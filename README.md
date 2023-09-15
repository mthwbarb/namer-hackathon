# namer-hackathon
# Generate a Podcast from the AWS whats new RSS Feed

This repo contains an AWS SAM definition and a sample streamlit app to play your podcast.

## Pre-Reqs
1. Sagemaker Endpoint running Llama-2-7b-chat (tested on ml.g5.2xlarge)
2. AWS CLI
3. AWS SAM CLI   see https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
4. boto3 installed `pip install boto3`
5. Note: If you use AWS Cloud9, steps 2,3,and 4 above are already preinstalled.
6. Streamlit `pip install streamlit`

## Instructions

1. Navigate to the SAM folder `cd SAM`
2. Build the SAM package `sam build --use-container`
3. Deploy the package.`sam deploy --guided`  Give your stack a name, and use the region where your SageMaker Endpoint is deployed.  Use the defaults for the rest of the options.
4. The following resources will be deployed: AWS Step Functions State Machine, AWS S3 Bucket, 7 Lambda functions, various IAM roles and policies
5. Navigate to the deployed state machine and choose **New Execution**
6. Paste the json from `sampleStepFunctionInput` into the execution input field
7. Replace the `bucket` with the bucket name deployed by the SAM application
8. Replace `llmEndpoint` with your SageMaker Endpoint Name.
9. Replace `numDays` with the number of days from today that you want to process from the RSS feed.
9. Click Start Execution
10. Depending on the number of new announcements and your SageMaker Endpoint instance type, execution can take anywhere from 5-15 minutes or longer.
11. Grab the `UUID` by clicking on the **Generate UUID** task, choose the **Output** tab, and scroll down to the **Output** field.  Copy the `UUID` value.  You will need this if you want to run the Streamlit app below.

### Listen to your podcast
You have 2 options:
1. Download the **podcast.mp3** file from the s3 bucket
2. Run the included Streamlit app `sampleApp.py`

To run the Streamlit app, do the following:
1. In your terminal, open `sampleApp.py`
2. Replace `bucketName` with your s3 bucket
3. Replace `runId` with the `UUID` you copied earlier
4. Save and close
5. Run `streamlit run ./sampleApp.py`
6. Open the URL in your browser.  *If using Cloud9, you must have your EC2 instance in a public subnet with a public IP, and a Security Group rule allow traffic to the Streamlit port (usually 8501)*


##Cleanup

1.Empty the S3 bucket or you will get an error when you delete the SAM application
2. `aws sam delete --stack-name <your stack name here>`

