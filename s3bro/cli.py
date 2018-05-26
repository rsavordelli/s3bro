import click
import boto3
from termcolor import colored
from s3_restore import *
from s3_purge import *
from s3_permission import *
from s3_tail import *
from s3_encryption import *
from __init__ import *

@click.group()
@click.version_option()
def cli():
    """This is your s3 friend(bro), that will help you with bucket iterations.
    Try:\n
    \b
    # s3bro restore --help
    # s3bro purge --help
    # s3tk --help
    
    For more help or detailed information please check:
    https://github.com/rsavordelli/s3bro
    https://pypi.org/project/s3bro/
    
    """
    global s3cli
    s3cli = boto3.client('s3')
    pass


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@cli.command()
@click.argument('restore', nargs=-1)
@click.option('--bucket', '-b', type=str, help='bucket name', required=True)
@click.option('--prefix','-p', type=str, help=' prefix', default='')
@click.option('--days', '-d', type=int, help='Days to keep the restore', required=True)
@click.option('--type', '-t', type=click.Choice(['Standard', 'Expedited', 'Bulk']), help='restore type (Tier)', required=True)
@click.option('--versions/--no-versions','-v', default=False, help='[--no-versions is DEFAULT] - this option will make the restore to include all versions excluding delete markers')
@click.option('--update-restore-date/--do-not-update-restore-date', '-urd', default=False, help='If passed, it will change the restore date for already restored key')
@click.option('--include', '-in', type=str, multiple=True, help='Only restore keys that matches with a given string, you can add multiples times by passing --include multiple times')
@click.option('--exclude', '-ex', type=str, multiple=True, help='Do not restore if key name matches with a given pattern,'
                                  'you can add multiple patterns by inputting')
@click.option('--workers', type=int, help='How many helpers to include in task, default is 10', default=10)
@click.option('--log-level', type=click.Choice(['INFO', 'ERROR', 'DEBUG', 'WARNING']), help='logging type', default='ERROR')
def restore(restore, bucket, prefix, days, type, versions, update_restore_date, workers, include, exclude, log_level):
    """
    restore glacier objects from s3
    """
    if type == "Expedited":
        print(colored('Note: ', 'yellow') + "Expedited requests will likely be throttled. If you want to avoid this please check: ")
        click.echo('https://docs.aws.amazon.com/AmazonS3/latest/dev/restoring-objects.html#restoring-objects-expedited-capacity')
        click.echo(30*'=')
    loglevel(log_level)
    collect_keys(restore, bucket, prefix, days, type, versions, update_restore_date, workers, include, exclude)


@cli.command()
@click.argument('purge', nargs=-1)
@click.option('--bucket','-b', type=str, help='Bucket name', required=True)
@click.option('--prefix', '-p', type=str, default='', help='prefix name - optional')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to continue with this deletion?', help="first confirmation")
@click.option('--log-level', type=click.Choice(['INFO', 'ERROR', 'DEBUG', 'WARNING']), help='logging type', default='ERROR')
def purge(purge, bucket, prefix, log_level):
    """ 
    delete all the bucket content
    """
    loglevel(log_level)
    # clean_bucket(bucket, prefix)
    delete_confirmation( bucket, prefix )


@cli.command('scan-objects')
@click.argument('scan-objects', nargs=-1)
@click.option('--bucket','-b', type=str, help='Bucket name', required=True)
@click.option('--prefix', '-p', type=str, default='', help='prefix name - optional')
@click.option('--workers', type=int, help='How many helpers to include in task, default is 10', default=10)
@click.option('--log-level', type=click.Choice(['INFO', 'ERROR', 'DEBUG', 'WARNING']), help='logging type', default='ERROR')
def scan_objects(scan_objects, bucket, prefix, workers, log_level):
    """
    scan object ACLs
    """
    loglevel(log_level)
    scan_key_perms(scan_objects, bucket, prefix, workers)


@cli.command('scan-bucket')
@click.argument('scan-bucket', nargs=-1)
@click.option('--bucket','-b', type=str, help='Bucket name')
@click.option('--all', '-A', is_flag=True, help="Scan permissions for all your buckets (don't combine -b with -A)")
@click.option('--log-level', type=click.Choice(['INFO', 'ERROR', 'DEBUG', 'WARNING']), help='logging type', default='ERROR')
def scan_bucket(scan_bucket, bucket, all, log_level):
    """
    scan bucket ACLs
    """
    if bucket is None and all is False:
        print('Either choose --bucket or --all option')
        quit()
    if bucket is not None and all is True:
        print('pick one dude, you want to scan one bucket (-b) or all (-A)?')
        quit()
    if all:
        bucket_list = [x['Name'] for x in s3cli.list_buckets()['Buckets']]
        for x in bucket_list:
            get_bucket_permission(x)
    elif bucket is not None:
        get_bucket_permission(bucket)


@cli.command()
@click.argument('tail', nargs=-1)
@click.option('--bucket','-b', type=str, help='Bucket name', required=True)
@click.option('--timeout', '-t', type=int, help='How much time (in minutes) to run, it will destroy '
                                                'the resources created after this time', required=True)
def tail(tail, bucket, timeout):
    """ 
    s3 logs in "real-time" through S3 Events (for puts and deletes only)
    """
    tail_init(bucket, timeout)


@cli.command('find-unencrypted')
@click.argument('find-unencrypted', nargs=-1)
@click.option('--bucket','-b', type=str, help='Bucket name', required=True)
@click.option('--prefix', '-p', type=str, default='', help='prefix name - optional')
@click.option('--versions/--no-versions','-v', default=False, help='[--no-versions is DEFAULT] - this option will make the restore to include all versions excluding delete markers')
@click.option('--workers', type=int, help='How many helpers to include in task, default is 10', default=10)
@click.option('--log-level', type=click.Choice(['INFO', 'ERROR', 'DEBUG', 'WARNING']), help='logging type', default='ERROR')
def find_unencrypted(find_unencrypted, bucket, prefix, versions, workers, log_level):
    """ 
    find unencrypted keys in a bucket (ServerSideEncryption)
    """
    loglevel(log_level)
    find_unencrypted_keys(bucket, prefix, versions, workers)
