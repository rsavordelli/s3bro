import click
import boto3
import logging
from pool_map import multi_process
from ratelimit import *
from botocore.exceptions import ClientError


@rate_limited(50)
def restore_versions(x):
    s3 = boto3.client('s3')
    s3r = boto3.resource('s3')
    bucket, key, v_id, days, type, update_restore_date = x[0], x[1], x[2], x[3], x[4], x[5]
    obj = s3r.ObjectVersion( bucket, key, v_id )
    try:
        data = obj.head()
        try:
            if data['ResponseMetadata']['HTTPHeaders']['x-amz-storage-class'] == 'GLACIER':
                header = data['ResponseMetadata']['HTTPHeaders']
                if 'x-amz-restore' not in header:
                    click.echo('Submitting restoration request: %s for %s days' % (key, days))
                    response = s3.restore_object(
                        Bucket=bucket,
                        Key=key,
                        VersionId=v_id,
                        RestoreRequest={
                            'Days': days,
                            'GlacierJobParameters': {'Tier': type}
                        }
                    )
                elif 'ongoing-request="true"' in header.values():
                    click.echo('Restoration in-progress: %s VersionID: %s' % (key, v_id))
                elif any( 'ongoing-request="false"' in x for x in header.values() ):
                    if update_restore_date:
                        click.echo('[Updating date] - Restoration complete: %s VersionID: %s for %s days from now' % (key, v_id, days) )
                        response = s3.restore_object(
                            Bucket=bucket,
                            Key=key,
                            VersionId=v_id,
                            RestoreRequest={
                                'Days': days,
                                'GlacierJobParameters':
                                    {'Tier': type}
                            }
                        )
                    else:
                        date = ''.join( data['ResponseMetadata']['HTTPHeaders']['x-amz-restore'].split( ',' )[1:] )
                        click.echo('Restoration completed: %s VersionID: %s until %s' % (key, v_id, date))

        except KeyError as e:
            # that's for the keys without x-amz-storage-class header
            logging.warning( '[Key not in glacier] - Key: %s/%s VersionID: %s' % (bucket, key, v_id) )
            pass

    except ClientError as e:
        # print(e.response)
        if e.response['ResponseMetadata']['HTTPStatusCode'] == 503:
            err = {
                'key': key,
                'error': e.response['Error']
            }
            click.echo('ERROR: %s' % err)
            pass
        elif e.response['ResponseMetadata']['HTTPStatusCode'] == 405:
            logging.warning( '[Delete Marker Found] - Ignoring key %s/%s VersionID: %s' % (bucket, key, v_id) )
            pass
        else:
            click.log(e.response)
            pass
    except Exception as e:
        print(e)


@rate_limited(50)
def restore_default(x):
    s3r = boto3.resource( 's3' )
    bucket, key, days, type, update_restore_date = x[0], x[1], x[2], x[3], x[4]
    obj = s3r.Object(bucket, key)
    try:
        if obj.storage_class == 'GLACIER':
            if obj.restore is None:
                click.echo('Submitting restoration request: %s' % obj.key)
                obj.restore_object( RestoreRequest={'Days': days, 'GlacierJobParameters': {'Tier': type}} )
            # Print out objects whose restoration is on-going
            elif 'ongoing-request="true"' in obj.restore:
                click.echo('Restoration in-progress: %s' % obj.key)
            # Print out objects whose restoration is complete
            elif 'ongoing-request="false"' in obj.restore:
                date = obj.restore.split('expiry-date=')[1]
                if update_restore_date:
                    click.echo('[Updating date] - Restoration complete: %s for %s days from now' % (obj.key, days))
                    obj.restore_object( RestoreRequest={'Days': days, 'GlacierJobParameters': {'Tier': type}} )
                else:
                    click.echo('Restoration completed: %s until %s' % (obj.key, date))
        else:
            logging.warning('[Key not in glacier] - Key: %s' % obj.key)
    except ClientError as e:
        err = {'key': key, 'error': e.response['Error']}
        if e.response['ResponseMetadata']['HTTPStatusCode'] == 503:
            click.echo('ERROR: %s' % err)
            pass
        else:
            click.echo(err)
    except KeyError as e:
        click.echo(e.response)
    except Exception as e:
        click.echo(e)


def collect_keys(restore, bucket, prefix, days, type, versions, update_restore_date, workers, include, exclude):
    s3r = boto3.resource( 's3' )
    startTime = time.time()
    bkt = s3r.Bucket(bucket)
    objects = []
    keys_proccessed = 0
    click.echo('Initiating %s restore for %s/%s...\nRestoring keys for %s days\n' %(type, bucket, prefix, days) + 30*'=')
    if versions:
        iterator = bkt.object_versions.filter(Prefix=prefix)
        click.echo('All versions: True\n' + 30*'=')
    else:
        click.echo('All versions: False\n' + 30*'=')
        iterator = bkt.objects.filter( Prefix=prefix )
    processed = False
    for obj in iterator:
        keys_proccessed += 1
        processed = False
        if len(objects) < 1000:
            if versions:
                data = [bucket, obj.key, obj.id, days, type, update_restore_date]
                if include:
                    # if obj.key.endswith(include):
                    if any( x in obj.key for x in include ):
                        objects.append(data)
                    else:
                        logging.warning( 'Not included because of filter (--include) to the key %s | Keys to include %s ' % ( obj.key, include) )
                elif exclude:
                    if not any( x in obj.key for x in exclude ):
                        objects.append(data)
                    else:
                        logging.warning('filter applied (exclude) to the key %s | Keys to exclude %s ' % ( obj.key, exclude) )
                else:
                    objects.append( data )
            else:
                data = [bucket, obj.key, days, type, update_restore_date]
                if include:
                    if any( x in obj.key for x in include ):
                        objects.append(data)
                    else:
                        logging.warning( ' Not included because of filter (--include) to the key %s | Keys to include %s ' % (obj.key, include) )
                elif exclude:
                    if not any( x in obj.key for x in exclude ):
                        objects.append(data)
                    else:
                        logging.warning( 'filter applied (exclude) to the key %s | Keys to exclude %s ' % (obj.key, exclude) )
                else:
                    objects.append( data )
        else:
            if versions:
                multi_process(restore_versions, objects, workers)
            else:
                multi_process(restore_default, objects, workers)
            # click.echo('cleaning objects')
            del objects[:]
            processed = True

    if not processed:
        # click.echo('There is only %s keys, running it in a single batch\n'%(len(objects)) + 30*'=')
        if versions:
            multi_process(restore_versions, objects, workers)
        else:
            multi_process(restore_default, objects, workers)
    elapsed = time.time() - startTime
    end = round(elapsed, 2)
    click.echo('Total keys proccessed: %s in %ss' %(keys_proccessed, end))