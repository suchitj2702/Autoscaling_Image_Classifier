import boto3


ec2 = boto3.client('ec2', region_name='us-east-1')


class AppTierInstance:

    def __init__(self, instance_id, app_tier_id):
        self.instance_id = instance_id  # AWS generated ID
        self.app_tier_id = app_tier_id  # Our own ID

    # Terminate the S3 instance
    def terminate(self):
        ec2.terminate_instances(
            InstanceIds=[self.instance_id]
        )
