import traceback

from flask import Flask, request, render_template
import boto3
from botocore.config import Config

import utils
import constants
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():

    if 'img' not in request.files:
        return { 'message': 'missing required img param' }, 400

    # Get file
    img = request.files['img']

    # Save input to s3
    for img in request.files.getlist('img'):
        try:
            utils.save_input(img.filename, img.stream)
            utils.enqueue_request(img.filename)
        except:
            traceback.print_exc()
            return { 'message': 'Internal server error' }, 500
    
    return {'message' : 'Files uploaded successfully! Please wait a minute for results to be ready.'}, 200

@app.route('/results', methods=['GET'])
def fetchResults(): 
    output = ""

    sqs_resource = utils.get_sqs_resource()

    queue = sqs_resource.Queue(url=constants.RESPONSE_QUEUE_URL)

    count = 0

    # loop through queue until no more messages left
    while int(utils.get_num_messages_in_queue(constants.RESPONSE_QUEUE_URL)) > 0:
        for message in queue.receive_messages(MaxNumberOfMessages = 2):

            body = json.loads(message.body)

            count += 1

            output = output + f'{count} ' +  body['result'] + "<br/>"

            #message.delete()

    output = f'Total count: {count}<br/>{output}'

    return output

@app.route('/reset', methods=['POST'])
def reset():
    # Clear S3 buckets
    utils.clear_buckets()

    # Clear and response Queues
    utils.clear_response_queue()

    return { 'message': 'Successfully cleared S3 buckets and response queue!' }

'''
output queue expected schema:
    { 
        "app_tier_instance" : "ip_ex",
        "result" : "(imgName, prediction)"
    }
'''