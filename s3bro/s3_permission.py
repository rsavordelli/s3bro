import boto3
import click
from pool_map import multi_process
import logging
from termcolor import colored
from botocore.exceptions import ClientError

public_perms = "http://acs.amazonaws.com/groups/global/AllUsers"


def get_bucket_permission(bucket):
    s3 = boto3.resource('s3')
    bkt = s3.Bucket(bucket)
    failed = False
    try:
        bucket_acl = bkt.Acl().grants
        owner = bkt.Acl().owner['ID']
    except ClientError as e:
        if e.response['Error']['Message'] == "Access Denied":
            click.echo('Failed to retrieve Bucket ACLs for %s with error Access Denied\n' %bucket)
            failed = True
        else:
            print(e.response['Error']['Message'])
            failed = True
    if not failed:
        perms = {'Public': [], 'Canonical': [], 'Owner': []}
        for p in bucket_acl:
            if p['Grantee']['Type'] == "Group":
                if p['Grantee']['URI'] == public_perms:
                    perms['Public'].append(p['Permission'])
            if p['Grantee']['Type'] == "CanonicalUser":
                o = p['Grantee']['ID']
                if owner != o:
                    data = {
                        'CanonicalID': o,
                        'Permission': p['Permission']
                    }
                    perms['Canonical'].append(data)
                if owner == o:
                    perms['Owner'].append( p['Permission'] )
        print('Bucket: %s' % bucket)
        print("        Owner ID: %s" % owner)
        if perms['Public']:
            print(colored('        Public Access: %s', 'red')) % perms['Public']
        if perms['Canonical']:
            for i in perms['Canonical']:
                print(colored("        AWS Account: %s %s", 'yellow') % (i['CanonicalID'], i['Permission']))
        print(colored('        Bucket Owner: %s', 'green')) % ', '.join(perms['Owner'])
        print('\n')


def get_permission(x):
    s3 = boto3.resource( 's3' )
    bucket, key, owner = x[0], x[1], x[2]
    obj = s3.Object(bucket, key)
    failed = False
    try:
        obj_acl = obj.Acl().grants
    except ClientError as e:
        if e.response['Error']['Message'] == "Access Denied":
            click.echo('Failed to retrieve ACLs for %s with error Access Denied' %key)
            failed = True
            pass
    perms = {'Public': [], 'Canonical': [], 'Owner': []}
    if not failed:
        for p in obj_acl:
            if p['Grantee']['Type'] == "Group":
                if p['Grantee']['URI'] == public_perms:
                    perms['Public'].append( p['Permission'] )
            if p['Grantee']['Type'] == "CanonicalUser":
                o = p['Grantee']['ID']
                if owner != o:
                    perms['Canonical'].append(p['Permission'])
                if owner == o:
                    perms['Owner'].append( p['Permission'] )

        if perms['Public']:
            out = {'Key': key, "Public": perms['Public'], "Canonical": perms['Canonical'], "Owner": perms['Owner']}
            print("{} | {} | {} | {}".format(", ".join(out['Public']).ljust(25), ", ".join(out['Canonical']).ljust(25), ", ".join(out['Owner']).ljust(25), out['Key'].ljust(50)))
        else:
            logging.warning('Key is Safe: %s' % key)


def scan_key_perms(scanperms, bucket, prefix, workers):
    s3 = boto3.resource( 's3' )
    bkt = s3.Bucket( bucket )
    owner = bkt.Acl().owner['ID']
    click.echo( '>> Scanning bucket ACL' )
    click.echo(30*'=')
    click.echo('>> Scanning objects with PUBLIC ACL')
    print(150 * "-")
    print("Public {} | Other AWS Accounts {} | Owner {}| Key {}").format("".ljust(18), "".ljust(6), "".ljust(20), "".ljust(60))
    print(150*"-")
    objects = []
    iterator = bkt.objects.filter(Prefix=prefix)
    processed = False
    for k in iterator:
        processed = False
        if len(objects) < 1000:
            objects.append( [bucket, k.key, owner] )
        else:
            multi_process(get_permission, objects, workers)
            del objects[:]
            processed = True
    if not processed:
        multi_process(get_permission, objects, workers)
