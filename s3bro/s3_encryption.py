import boto3
import click
import logging
from pool_map import multi_process
from botocore.exceptions import ClientError


def is_encrypted(obj):
    enc = obj.get('ResponseMetadata').get('HTTPHeaders').get('x-amz-server-side-encryption')
    if not enc:
        return False
    else:
        return True


def get_encryption(obj):
    s3 = boto3.resource('s3')
    try:
        r = s3.ObjectVersion(obj.get('bucket'), obj.get('key'), obj.get('version')).head()
        if not is_encrypted(r):
            print('[Not Encrypted] %s | %s' % (obj.get('key'), obj.get('version')))
        else:
            logging.warning('[Encrypted] %s | %s' % (obj.get('key'), obj.get('version')))

    except ClientError as e:
        if e.response['ResponseMetadata']['HTTPStatusCode'] == 405:
            logging.warning('[Delete Marker Found] - Ignoring key %s/%s VersionID: %s' % (obj.get('bucket'), obj.get('key'), obj.get('version')))
        elif e.response['ResponseMetadata']['HTTPStatusCode'] == 403 or e.response['ResponseMetadata']['HTTPStatusCode'] == 404:
            print('Failed to retrieve encryption details %s %s (Access Denied)' % (obj.get('key'), obj.get('version')))
        elif e.response['ResponseMetadata']['HTTPStatusCode'] == 503:
            print('SlowDown - Too many requests. Failed to retrieve %s | %s' % (obj.get('bucket'), obj.get('key'), obj.get('version')))
        else:
            logging.warning(obj.get('bucket'), obj.get('key'), obj.get('version'), e.response)


def find_unencrypted_keys(bucket, prefix, versions, workers):
    s3 = boto3.resource( 's3' )
    bkt = s3.Bucket( bucket )
    objects = []
    if versions:
        iterator = bkt.object_versions.filter(Prefix=prefix)
    else:
        iterator = bkt.objects.filter( Prefix=prefix )

    processed = False
    for k in iterator:
        processed = False
        if len( objects ) < 1000:
            if not versions:
                data = {'bucket': bucket, 'key': k.key, 'version': 'null'}
            else :
                data = {'bucket': bucket, 'key': k.key, 'version': k.id}
            objects.append(data)
            # objects.append([bucket, k.key]) if not versions else objects.append([bucket, k.key, k.id])
        else:
            multi_process(get_encryption, objects, workers)
            del objects[:]
            processed = True
    if not processed:
        multi_process(get_encryption, objects, workers)
