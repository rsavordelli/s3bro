import boto3
import click
import random
import string
import json
import time
import os
from termcolor import colored


s3 = boto3.client('s3')


def create_queue(bucket, bucket_location):
    click.echo('[ Preparing services ]')
    print(50*'=')
    click.echo('Creating a SQS in %s ...' % bucket_location)
    sqs = boto3.client('sqs', region_name=bucket_location)
    char_set = string.ascii_uppercase + string.digits

    response = sqs.create_queue(
        QueueName=bucket.replace('.', '_') + "_" + bucket_location + "_" + ''.join(random.sample(char_set*6, 6)),
        Attributes={
            'MessageRetentionPeriod': '60'
    })
    url = response['QueueUrl']
    data = response['QueueUrl'].split('/')
    account = data[3]
    q_name = data[4]
    arn = "arn:aws:sqs:%s:%s:%s" % (bucket_location, account, q_name)
    data = {'arn': arn, 'url': url, 'account_id': account}
    click.echo("Queue: %s" % data['arn'])
    return data


def add_queue_permission(q_url, q_arn, bucket_location):
    sqs = boto3.client('sqs', region_name=bucket_location)
    policy = {
        "Version": "2012-10-17",
        "Id": q_arn + "/SQSDefaultPolicy",
        "Statement": [{
            "Sid": "Sid1522338529054",
            "Effect": "Allow",
            "Principal": {
                "Service": "s3.amazonaws.com"
            },
            "Action": "SQS:*",
            "Resource": q_arn
        }]
    }

    sqs.set_queue_attributes(QueueUrl=q_url, Attributes={'Policy': json.dumps(policy), })


# def get_s3_notification(bucket):
#     response = s3.get_bucket_notification_configuration(Bucket=bucket)
#     print(response)


def enable_s3_notification(bucket, queue):
    # get_s3_notification(bucket)
    click.echo('Enabling s3 event (s3tail-Event) notification on %s ...' % bucket)
    response = s3.put_bucket_notification_configuration(
        Bucket=bucket,
        NotificationConfiguration={
            'QueueConfigurations': [
                {
                    'Id': 's3tail-Event',
                    'QueueArn': queue,
                    'Events': ['s3:ObjectCreated:*', 's3:ObjectRemoved:*']

                }
            ]
        }
    )
    print(50*'=')
    return response


def delete_resources(q_url, bucket, bucket_location):
    sqs = boto3.client('sqs', region_name=bucket_location)
    print( 30 * '-' )
    click.echo( 'Time is over, deleting resources' )
    click.echo( 'Deleting queue' )
    response = sqs.delete_queue( QueueUrl=q_url )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        click.echo( 'Failed to delete the Queue, please manually delete it to avoid extra-cost' )
    click.echo( 'Disabling Event on S3' )
    response = s3.put_bucket_notification_configuration( Bucket=bucket, NotificationConfiguration={} )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        click.echo( 'Failed to delete s3 notification, please manually disable to avoid extra-cost' )


def parsed_output(msg):
    event_time = msg.get('eventTime')
    event_name = msg.get('eventName')
    user_identity = msg.get('userIdentity').get('principalId')
    ip_address = msg.get('requestParameters').get('sourceIPAddress')
    x_amz_id = msg.get('responseElements').get('x-amz-request-id')
    host_id = msg.get('responseElements').get('x-amz-id-2')
    key = msg.get('s3').get('object').get('key')
    size = msg.get('s3').get('object').get('size')
    v_id = msg.get('s3').get('object').get('versionId')
    return [ip_address, event_time, key, str(size), str(v_id), event_name, user_identity, x_amz_id, host_id]


def s3tail(q_url, min, bucket, bucket_location):
    sqs = boto3.client('sqs', region_name=bucket_location)

    timeout = time.time() + 60 * min
    try:
        while True:
            if time.time() > timeout:
                delete_resources(q_url, bucket, bucket_location)
                break

            response = sqs.receive_message(
                QueueUrl=q_url,
                MaxNumberOfMessages=10,
                VisibilityTimeout=65,
            )
            try:
                raw_msg = response['Messages']
                for m in raw_msg:
                    msg = json.loads( m.get('Body'))
                    if msg.get('Records') is not None:
                        notification = msg.get('Records')[0]
                        print(' '.join(parsed_output(notification)))
            except KeyError as e:
                pass

    except (KeyboardInterrupt, SystemExit):
        print("Caught KeyboardInterrupt, terminating workers")
        delete_resources(q_url, bucket, bucket_location)


def resource_confirmation():
    print(colored("s3bro will create an SQS and enable Event notification in your S3 bucket\n"
                  "After the script is done it will delete the resources automatically.\n"
                  "If you cancel or interrupt the script, the resource deletion may fail.\n"
                  "In that case, you have to manually delete the resources, ok?\n"
                  "To prove you've read the message, type 'agreed' in the confirmation below", 'yellow'))
    res = raw_input('confirmation: ')
    if res != 'agreed':
        print('Read the above message entirely')
        resource_confirmation()
    else:
        os.system( 'cls' if os.name == 'nt' else 'clear' )


def get_bucket_location(bucket):
    get_location = s3.get_bucket_location(Bucket=bucket)
    if get_location['LocationConstraint'] is None:
        bucket_location = 'us-east-1'
    else:
        bucket_location = get_location['LocationConstraint']
    return bucket_location


def tail_init(bucket, timeout):
    bucket_location = get_bucket_location(bucket)
    resource_confirmation()
    queue = create_queue(bucket, bucket_location)
    add_queue_permission(queue['url'], queue['arn'], bucket_location)
    enable_s3_notification(bucket, queue['arn'])
    s3tail(queue['url'], timeout, bucket, bucket_location)





