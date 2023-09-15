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
4. The following resources will be deployed: AWS Step Functions State Machine, AWS S3 Bucket, 7 Lambda functions, various IAM roles and policies.
5. Navigate to the deployed state machine and choose **New Execution**
6. Open the included `sampleStepFunctionInput.json` file, update the following fields, and save:
* Replace the `bucket` with the bucket name deployed by the SAM application
*  Replace `llmEndpoint` with your SageMaker Endpoint Name.
*  Replace `numDays` with the number of days from today that you want to process from the RSS feed.
7. Execute the Step Function from the command line: `aws stepfunctions start-execution --state-machine-arn <YOUR STATE MACHINE ARN> --input "$(jq -R . sampleStepFunctionInput.json --raw-output)"`
8. Depending on the number of new announcements in the time range that you specified in `numDays` and your SageMaker Endpoint instance type, execution can take anywhere from 5-15 minutes or longer.
9. Monitor the execution by running the command: `aws stepfunctions describe-execution --execution-arn <YOUR EXECUTION ARN>`.  Get the Execution ARN from the output of Step 7.
10. Once complete, grab the `runID` and `bucket name` from the output of Step 9.  You will need this if you want to run the Streamlit app below.

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



### What do the Lambdas Do?

* **processRSS** - Iterates through the RSS feed from today backward up to the number of days specified.  It takes the 