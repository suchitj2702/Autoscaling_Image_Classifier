import os

REGION_NAME = 'us-east-1'

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

INPUT_BUCKET_NAME = 'cse546project1-inputs'
OUTPUT_BUCKET_NAME = 'cse546project1-outputs'

REQUEST_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-request-queue'
RESPONSE_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/830749420193/cse546project1-response-queue'
