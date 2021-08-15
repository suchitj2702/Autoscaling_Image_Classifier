import boto3
import time
import uuid

from AppTierInstancePool import AppTierInstancePool


REGION_NAME = 'us-east-1'
REQUEST_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-request-queue'


sqs_client = boto3.client('sqs', region_name=REGION_NAME)


def get_request_queue_length():
    # Count # of requests in the queue
    response = sqs_client.get_queue_attributes(
        QueueUrl=REQUEST_QUEUE_URL,
        AttributeNames=[
            'ApproximateNumberOfMessages',
            'ApproximateNumberOfMessagesNotVisible'
        ]
    )
    num_visible_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
    num_invisible_messages = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
    num_requests = num_visible_messages + num_invisible_messages
    print(f'# of requests: {num_visible_messages} + {num_invisible_messages} = {num_requests} ')
    return num_requests


def run():
    # Create a pool of EC2 instances, with max of 19 instances
    pool = AppTierInstancePool()

    while True:
        num_requests = get_request_queue_length()

        print('# of instances running:', pool.num_instances_running)

        # Number of instances that we will have available assuming all pending shutdown requests
        # will be processed successfully
        num_projected_instances = pool.num_instances_running - pool.num_shutdown_requests_sent

        # Number of new instances we will need to launch
        # e.g. If there are 19 requests in the queue, 19 currently running, and 4 pending shutdown requests
        # then we will need to launch 19 - (19 - 4) = 19 - 15 = 4 new instances.
        num_create = num_requests - num_projected_instances

        if num_create > 0:  # We need to scale up
            # First try to obtain instances by cancelling shutdown requests
            num_successfully_cancelled = pool.cancel_shutdown_requests(num_create)

            print(f'Successfully cancelled {num_successfully_cancelled} requests.')

            num_launch = num_create - num_successfully_cancelled

            pool.launch_instances(num_launch)

        elif num_create < 0: # We need to scale down
            num_delete = abs(num_create)

            # Send num_shutdown_requests additional graceful shutdown requests
            pool.send_shutdown_requests(num_delete)

        # Check for any shutdown confirmed messages and terminate instances accordingly.
        pool.check_shutdown_confirmed()

        time.sleep(5)

if __name__ == '__main__':
    run()
