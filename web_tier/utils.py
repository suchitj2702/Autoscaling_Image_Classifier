import boto3
import io
import constants


def get_s3_client():
    s3_client = boto3.client(
        's3',
        region_name=constants.REGION_NAME,
        aws_access_key_id=constants.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=constants.AWS_SECRET_ACCESS_KEY
    )
    return s3_client

def save_input(filename, stream):
    s3_client = get_s3_client()

    s3_client.upload_fileobj(
        stream,
        constants.INPUT_BUCKET_NAME,
        filename
    )

def get_sqs_client():
    sqs_client = boto3.client(
        'sqs',
        region_name = constants.REGION_NAME,
        aws_access_key_id = constants.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = constants.AWS_SECRET_ACCESS_KEY
    )

    return sqs_client

def get_sqs_resource():
    sqs_resource = boto3.resource(
        'sqs',
        region_name = constants.REGION_NAME,
        aws_access_key_id = constants.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = constants.AWS_SECRET_ACCESS_KEY
    )

    return sqs_resource

def get_s3_resources():
    s3_resource = boto3.resource(
        's3',
        region_name = constants.REGION_NAME,
        aws_access_key_id = constants.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = constants.AWS_SECRET_ACCESS_KEY
    )
    return s3_resource

def get_num_messages_in_queue(queue_url):
    sqs_client = get_sqs_client()
    response = sqs_client.get_queue_attributes(QueueUrl = queue_url, AttributeNames = ['ApproximateNumberOfMessages'])
    return response['Attributes']['ApproximateNumberOfMessages']

def enqueue_request(image_name):
    sqs = boto3.client('sqs', region_name=constants.REGION_NAME)
    sqs.send_message(
        QueueUrl=constants.REQUEST_QUEUE_URL,
        MessageBody=image_name,
        DelaySeconds=0
    )

# Clear the input and output buckets
def clear_buckets():
    s3_resource = get_s3_resources()

    bucket = s3_resource.Bucket(constants.INPUT_BUCKET_NAME)
    bucket.object_versions.delete()

    bucket = s3_resource.Bucket(constants.OUTPUT_BUCKET_NAME)
    bucket.object_versions.delete()

# Clears SQS response queue
def clear_response_queue():
    sqs_resource = get_sqs_resource()
    queue = sqs_resource.Queue(url=constants.RESPONSE_QUEUE_URL)
    try:
        queue.purge()
    except:
        pass
