# App Tier

## Running the app
Set up a Python virtual environment, activate the virtual environment, and then install the application dependencies into the virtual environment using `pip install -r requirements.txt`

Set the following environment variables:

```
REGION_NAME=<aws-region-name>
AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
INPUT_BUCKET_NAME=<input-s3-bucket-name>
OUTPUT_BUCKET_NAME=<output-s3-bucket-name>
FLASK_APP="app.py"
```

Run `flask run` to start the server.
