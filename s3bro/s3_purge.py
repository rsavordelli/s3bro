import boto3
import click
import logging
import time, sys
from termcolor import colored
from botocore.exceptions import ClientError


def check_tagging(bucket):
    has_confirmation = False
    s3 = boto3.client( 's3' )
    try:
        tag = s3.get_bucket_tagging(Bucket=bucket)
    except ClientError as e:
        if e.response['Error']['Code'] == "NoSuchTagSet":
            logging.warning('No tags found for {}'.format(bucket))
            return has_confirmation
        elif e.response['ResponseMetadata']['HTTPStatusCode'] == 403:
            logging.warning("GetBucketTagging {} failed with {}".format(bucket, e.response['Error']['Code']))
            return has_confirmation
        else:
            logging.warning(e.response)
    tags = tag.get('TagSet')
    for x in tags:
        if x.get('Key') == 's3bro_delete':
            if x.get('Value') == "yes":
                has_confirmation = True
    return has_confirmation


def delete_confirmation(bucket, prefix):
    avoid_confirmation = check_tagging(bucket)
    if avoid_confirmation is True:
        clean_bucket(bucket, prefix)
    else:
        if prefix is '':
            print_prefix = '/'
        else:
            print_prefix = prefix
        print(colored('[Warning] This action is not reversible', 'red'))
        print(30*'=')
        print('Bucket: %s' % bucket)
        print('Prefix: %s' % print_prefix)
        print(30*'=')
        r = raw_input("Confirm the bucket name if you want to wipe the bucket content: ")
        if r == bucket:
            clean_bucket(bucket, prefix)
        else:
            print('something is not right with the confirmation')


def clean_bucket(bucket, prefix):
    s3 = boto3.resource( 's3' )
    click.echo('I will start the deletion of %s/%s in 10 seconds, you still have the chance to stop' % (bucket, prefix))
    for remaining in range( 10, 0, -1 ):
        sys.stdout.write( "\r" )
        sys.stdout.write( "{:2d} seconds remaining.".format( remaining ) )
        sys.stdout.flush()
        time.sleep( 1 )
    click.echo('\nStart cleaning...')
    bkt = s3.Bucket(bucket)
    iterator = bkt.object_versions.filter( Prefix=prefix )
    objects = []
    for obj in iterator:
        objects.append( {'Key': obj.key, 'VersionId': obj.id} )
        logging.warning('Sending to deletion: %s %s' % (obj.key, obj.id))
        if len(objects) == 1000:
            response = bkt.delete_objects(Delete={'Objects': objects})
            objects = []
    if len(objects) > 0:
        click.echo('You have only %s keys, deleting'%len(objects))
        response = bkt.delete_objects( Delete={'Objects': objects} )
    else:
        print('it seem that you got no keys')

