import boto3
import click
import time
from pool_map import multi_process
import logging
from termcolor import colored
from botocore.exceptions import ClientError


public_perms = "http://acs.amazonaws.com/groups/global/AllUsers"

def get_permission(x):
    s3 = boto3.client('s3')
    bucket, key, ver, mk_private = x[0], x[1], x[2], x[3]
    got_acls = True
    grants = ''
    try:
        if ver:
            grants = s3.get_object_acl(Bucket=bucket, Key=key, VersionId=ver).get('Grants')
        else:
            grants = s3.get_object_acl(Bucket=bucket, Key=key).get('Grants')
    except ClientError as e:
        if e.response['Error']['Message'] == "Access Denied":
            print('Failed to retrieve ACLs for %s with error Access Denied' %key)
            logging.warning(e.response)
            got_acls = False
            pass
    pub_perms = []
    if got_acls:
        for g in grants:
            type = g.get('Grantee').get('Type')
            uri = g.get('Grantee').get('URI')
            if type == "Group" and uri == public_perms:
                pub_perms.append(g.get('Permission'))
            else:
                logging.warning('[Private  - {}/{} VersionId: {}]'.format(bucket, key, ver))
        if pub_perms:
            if mk_private:
                print("{}/{} VersionId: {} ".format(bucket, key, ver) + colored('public ', 'red') + "({})".format(','.join(pub_perms)) + " Reseting permissions to private")
                try:
                    if ver:
                        res = s3.put_object_acl(Bucket=bucket, Key=key, ACL='private', VersionId=ver)
                    else:
                        res = s3.put_object_acl(Bucket=bucket, Key=key, ACL='private')
                except ClientError as e:
                    if e.response['Error']['Message'] == "Access Denied":
                        print('Failed to set private acl for {}'.format(key))
                        pass
            else:
                print("{}/{} VersionId: {} ".format(bucket, key, ver) + colored('public ', 'red') + "({})".format(','.join(pub_perms)))
            

def scan_key_perms_v2(bucket, prefix, versions, make_private, workers):
    startTime = time.time()
    keys_proccessed = 0
    s3 = boto3.resource( 's3' )
    bkt = s3.Bucket( bucket )
    objects = []
    if not versions:
        iterator = bkt.objects.filter(Prefix=prefix)
    else:
        iterator = bkt.object_versions.filter(Prefix=prefix)
    processed = False
    for k in iterator:
        keys_proccessed += 1
        processed = False
        if versions:
            obj, ver = k.object_key, k.id
        else:
            obj, ver = k.key, None
        if len(objects) < 1000:
            objects.append( [bucket, obj, ver, make_private] )
        else:
            multi_process(get_permission, objects, workers)
            del objects[:]
            processed = True
    if not processed:
        multi_process(get_permission, objects, workers)
    elapsed = time.time() - startTime
    end = round(elapsed, 2)
    click.echo('\nTotal keys proccessed in total: %s in %ss' %(keys_proccessed, end))
