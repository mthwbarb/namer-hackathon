# namer-hackathon
# Generate a Podcast from an RSS feed

This repo contains an AWS SAM definition and a sample streamlit app to play your podcast.

## Pre-Reqs
1. Sagemaker Endpoint running Llama-2-7b-chat
2. AWS CLI
3. AWS SAM CLI   see https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
4. Note: If you use AWS Cloud9, 2 and 3 above are already preinstalled.

## Instructions

1. Navigate to the SAM folder `cd SAM`
2. Build the SAM package `sam build --use-container`
3. Deploy the package.`sam deploy --guided`  Give your stack a name, and use the region where your SageMaker Endpoint is deployed.  Use the defaults for the rest of the options.

