# Looping program that reads from SQS request queue

# This script will be run when the instance is launched

import boto3
import time
import uuid

import json

import os
import sys


ID = sys.argv[1]


REGION_NAME = 'us-east-1'

REQUEST_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-request-queue'
RESPONSE_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-response-queue'

SHUTDOWN_REQUEST_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-shutdown-requests.fifo'
SHUTDOWN_CONFIRMED_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-shutdown-confirmed.fifo'


INPUT_BUCKET = 'cse546project1-inputs'
OUTPUT_BUCKET = 'cse546project1-outputs'


IMAGE_FOLDER = '/home/ubuntu/images'
CLASSIFIER_FOLDER = '/home/ubuntu/classifier'


# Save (key, value) result pair to S3
def save_result(key, value):
    s3 = boto3.client('s3', region_name=REGION_NAME)
    pair = f'({key}, {value})'
    s3.put_object(Key=key, Bucket=OUTPUT_BUCKET, Body=pair)


# Download image from S3 input bucket
def download_image(image_name):
    s3 = boto3.client('s3', region_name=REGION_NAME)
    save_path = f'{IMAGE_FOLDER}/{image_name}'
    s3.download_file(INPUT_BUCKET, image_name, save_path)
    return save_path


# Classify image by invoking classification script
def classify_image(img_path):
    stdout = os.popen(f'cd {CLASSIFIER_FOLDER}; python3 image_classification.py "{img_path}"')
    result = stdout.read().strip()
    return result


# Send response to response queue
def send_response(key, value):
    sqs = boto3.client('sqs', region_name=REGION_NAME)
    pair = f'({key}, {value})'
    sqs.send_message(
        QueueUrl=RESPONSE_QUEUE_URL,
        MessageBody=json.dumps({
            'app_tier_id': ID,
            'result': pair
        }),
        DelaySeconds=0
    )


def check_for_shutdown_request():
    sqs = boto3.client('sqs', region_name=REGION_NAME)
    response = sqs.receive_message(QueueUrl=SHUTDOWN_REQUEST_QUEUE_URL, MaxNumberOfMessages=1)
    messages = response.get('Messages', [])
    return messages[0] if len(messages) > 0 else None


def send_shutdown_notification():
    sqs = boto3.client('sqs', region_name=REGION_NAME)
    sqs.send_message(
        QueueUrl=SHUTDOWN_CONFIRMED_QUEUE_URL,
        MessageBody=ID,
        DelaySeconds=0,
        MessageDeduplicationId=str(uuid.uuid4()),
        MessageGroupId='2'
    )


# Continue polling SQS queue
while True:
    # Create client (if we don't instantiate a new client, then
    # there is a message delay)
    sqs = boto3.client('sqs', region_name=REGION_NAME)

    # Dequeue a message from request queue
    response = sqs.receive_message(QueueUrl=REQUEST_QUEUE_URL, MaxNumberOfMessages=1)

    # IN PROGRESS - DONT TERMINATE THIS INSTANCE YET

    #print(json.dumps(response, indent=4))

    messages = response.get('Messages', [])
    print(json.dumps(messages, indent=4))

    for message in messages:
        receipt_handle = message['ReceiptHandle']  # Needed for message deletion
        image_name = message['Body']

        # Download img from S3
        img_path = download_image(image_name)

        # Do machine learning
        result = classify_image(img_path)

        print(result)

        # Save result to S3
        key = image_name.split('.')[0]
        save_result(key, result)

        # Enqueue response in response queue (if needed)
        send_response(key, result)

        # Remove image from local machine
        os.remove(img_path)

        print('Deleting message...')
        sqs.delete_message(QueueUrl=REQUEST_QUEUE_URL, ReceiptHandle=receipt_handle)
        print('Message deleted.')

    shutdown_request = check_for_shutdown_request()

    if shutdown_request is not None:
        print('Shutting down...')
        receipt_handle = shutdown_request['ReceiptHandle']
        sqs.delete_message(QueueUrl=SHUTDOWN_REQUEST_QUEUE_URL, ReceiptHandle=receipt_handle)
        send_shutdown_notification()  # Send message to shutdown confirmed queue
        break  # Exit from loop

    time.sleep(5) # Wait for 5 seconds before polling again
