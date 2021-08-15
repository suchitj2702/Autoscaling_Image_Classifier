import boto3
from AppTierInstance import AppTierInstance

import uuid


REGION_NAME = 'us-east-1'

REQUEST_QUEUE_URL='https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-request-queue'
SHUTDOWN_REQUEST_QUEUE_URL='https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-shutdown-requests.fifo'
SHUTDOWN_CONFIRMED_QUEUE_URL='https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-shutdown-confirmed.fifo'


ec2 = boto3.client('ec2', region_name=REGION_NAME)


class AppTierInstancePool:

    def __init__(self, max_instances=19, AMI='ami-09f75b0501c68aa85'):
        self.max_instances = max_instances
        self.instances = [None] * max_instances  # Array of instance objects, indexed by (App Tier ID - 1)
        self.available_ids = list(range(max_instances, 0, -1))  # Available App Tier IDs
        self.AMI = AMI
        self.num_shutdown_requests_sent = 0  # Keeping track of how many shutdown requests have already been sent

    # Number of additional instances to launch
    def launch_instances(self, number_of_instances):
        for _ in range(number_of_instances):
            # Break from loop if we've hit limit
            if len(self.available_ids) == 0:
                break
            self._launch_instance()

    def terminate_instance(self, app_tier_id: int):
        if app_tier_id < 1 or app_tier_id > self.max_instances:
            return
        instance = self.instances[app_tier_id - 1]
        if instance is not None:
            instance.terminate()
            self.instances[app_tier_id - 1] = None
            self.available_ids.append(app_tier_id)

    def send_shutdown_requests(self, num_shutdown_requests):
        for _ in range(num_shutdown_requests):
            self._send_shutdown_request()

    def _send_shutdown_request(self):
        sqs = boto3.client('sqs', region_name=REGION_NAME)
        sqs.send_message(
            QueueUrl=SHUTDOWN_REQUEST_QUEUE_URL,
            MessageBody='shutdown',
            DelaySeconds=0,
            MessageDeduplicationId=str(uuid.uuid4()),
            MessageGroupId='1'
        )
        self.num_shutdown_requests_sent += 1

    # Attempt to cancel at most num_cancel shutdown requests (10 max)
    def cancel_shutdown_requests(self, num_cancel):
        sqs = boto3.client('sqs', region_name=REGION_NAME)
        response = sqs.receive_message(QueueUrl=SHUTDOWN_REQUEST_QUEUE_URL, MaxNumberOfMessages=min(num_cancel, 10))
        messages = response.get('Messages', [])
        print('Cancelling', len(messages), 'shutdown requests.')
        for message in messages:
            receipt_handle = message['ReceiptHandle']
            sqs.delete_message(QueueUrl=SHUTDOWN_REQUEST_QUEUE_URL, ReceiptHandle=receipt_handle)
            self.num_shutdown_requests_sent -= 1
        return len(messages)  # Returned number of successfully cancelled shutdown requests

    # Checks shutdown confirmed queue for new confirmed messages
    # then terminates the corresponding instances.
    # Can only respond to 10 shutdown confirmed messages at a time as per boto3 limits
    def check_shutdown_confirmed(self):
        sqs = boto3.client('sqs', region_name=REGION_NAME)
        response = sqs.receive_message(QueueUrl=SHUTDOWN_CONFIRMED_QUEUE_URL, MaxNumberOfMessages=10)
        messages = response.get('Messages', [])
        print('Found', len(messages), 'shutdown confirmed messages.')
        # Respond to each shutdown confirmed message
        for message in messages:
            receipt_handle = message['ReceiptHandle']
            app_tier_id = int(message['Body'])
            self.terminate_instance(app_tier_id)
            sqs.delete_message(QueueUrl=SHUTDOWN_CONFIRMED_QUEUE_URL, ReceiptHandle=receipt_handle)
            self.num_shutdown_requests_sent -= 1

    # Launch EC2 app tier instance
    def _launch_instance(self) -> AppTierInstance:
        if len(self.available_ids) == 0:
            return None
        app_tier_id = self.available_ids.pop()
        # Startup script
        user_data = f"""#!/bin/bash
touch /home/ubuntu/test;
runuser -l ubuntu -c 'screen -dm bash -c "python3 /home/ubuntu/app_tier.py {app_tier_id}; exec sh"'
"""
        print(user_data)
        ami_image_id = self.AMI  # Project 1 Custom AMI
        result = ec2.run_instances(
            ImageId=ami_image_id,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            KeyName='cse546project1',
            SecurityGroupIds=[
                'sg-037ea264983489c67' # Project 1 EC2 Security Group ID
            ],
            IamInstanceProfile={  # Assign IAM role to give the app tier EC2 instances access to S3, Simple DB, etc.
                'Name': 'cse546project1app_tier_role'
            },
            UserData=user_data,
            TagSpecifications=[{  # Give instance name based on App Tier ID
                'ResourceType': 'instance',
                'Tags': [{
                    'Key': 'Name',
                    'Value': f'app-instance{app_tier_id}'
                }]
            }]
        )
        instance_id = result['Instances'][0]['InstanceId']
        instance = AppTierInstance(instance_id=instance_id, app_tier_id=app_tier_id)
        self.instances[app_tier_id - 1] = instance
        return instance

    @property
    def num_instances_running(self):
        return self.max_instances - len(self.available_ids)
