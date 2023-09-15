#generate a segment intro for each unique category

import boto3
import json
import os

def generatePayload(category):
    #grab the category friendly name
    catvalue = next(iter(category.values()))
    #construct the prompt
    payload = {
        "inputs": [
            [
                {
                    "role": "system",
                    "content": "You are writing a script for your AWS podcast called 'The AWS Factor' which is focused on new announcements. You are the host named Li.  There is a co-host named Richard",
                },
                {
                    "role": "user", 
                    "content": "You have just returned from a short commercial break.  Write a brief introduction for the next segment in the podcast with a topic of "+ catvalue + ". Mention the topic but do not go into details about the topic. Always end with something similar to either 'let's dive in' or 'let's get started'  Don't include the assistant response."
                }
            ]
        ],
        "parameters": {"max_new_tokens": 1500, "top_p": 0.9, "temperature": 1.0},
    }
    return payload

def createDialog(payload,endpoint):
    sagemaker = boto3.client('sagemaker')
    runtime = boto3.client('runtime.sagemaker')
    print("Invoking Endpoint")
    #feed the payload to our Sagemaker Endpoint
    response = runtime.invoke_endpoint(EndpointName=endpoint, ContentType='application/json', Body=json.dumps(payload), CustomAttributes="accept_eula=true")
    #format the result
    result = json.loads(response['Body'].read().decode())
    output = result[0]["generation"]["content"]
    dialog=output
    return dialog

def generateAudio(payload,run_id,category,bucket,s3Client):
    #grab the category id
    catkey = next(iter(category.keys()))
    #setup Polly client
    print("Payload: " + payload)
    print("initiating Polly session")
    polly_client = boto3.client('polly')
    #Syntesize audio from the input
    response = polly_client.synthesize_speech(VoiceId='Ruth',
                OutputFormat='mp3', 
                Text = payload,
                Engine = 'neural')
    #write temporary mp3 file
    print("Writing mp3 file to temp storage")
    file = open('/tmp/output.mp3', 'ab+')
    file.write(response['AudioStream'].read())
    file.close()
    
    #upload the mp3 object to s3
    print('Uploading mp3 file to s3: ' + run_id + '/transition_audio/'+catkey+'.mp3')
    s3=s3Client
    s3.meta.client.upload_file('/tmp/output.mp3',bucket,run_id + '/transition_audio/'+catkey+'.mp3')
    #cleanup
    print("Cleaning Up temp file")
    os.remove("/tmp/output.mp3")
    
    #prepare output for step function
    manifestObject = {"audioObjectKey": 'transition_audio/'+catkey+'.mp3'}
    return manifestObject
def lambda_handler(event, context):
    try:
        print("Starting...")
        print(event)
        s3=boto3.resource('s3')
        bucketName = event['bucket']
        bucket = s3.Bucket(bucketName)
        runId = event['uuid']
        endpoint = event['llmEndpoint']
        
        print("runId: " +runId)
        print("Bucket: "+bucketName)
        
        manifestObject = bucket.Object(runId + '/manifest.json').get()['Body'].read().decode('utf-8')
        manifestObject_json = json.loads(manifestObject)
        
        #Get list of unique categories from the manifest
        uniqueCategories = ( set(d['category'] for d in manifestObject_json) )
        #this is our mapping of category to Friendly category name
        category_map={
        "analytics":"Analytics",
        "application-services":"Application Integration",
        "blockchain":"Blockchain",
        "business-productivity":"Business Applications",
        "cost-management":"Cloud Financial Management",
        "compute":"Compute",
        "containers":"Containers",
        "customer-enablement":"Customer Enablement",
        "messaging":"Customer Engagement",
        "databases":"Database",
        "developer-tools":"Developer Tools",
        "desktop-and-app-streaming":"End User Computing",
        "mobile-services":"Front End Web and Mobile",
        "game-development":"GameTech",
        "internet-of-things":"Internet of Things",
        "artificial-intelligence":"Machine Learning",
        "management-and-governance":"Management and Governance",
        "media-services":"Media Services",
        "migration":"Migration and Transfer",
        "networking-and-content-delivery":"Networking and Content Delivery",
        "networking": "Networking and Content Delivery",
        "aws-marketplace-and-partners":"Partners",
        "quantum-technologies":"Quantum Technologies",
        "robotics":"Robotics",
        "satellite":"Satellite",
        "security-identity-and-compliance":"Security, Identity, and Compliance",
        "serverless":"Serverless",
        "storage":"Storage",
        "training-and-certification":"Training and Certification",
        "partner-network":"Partners",
        "general":"Other AWS Services"
        }
        uniqueCategoriesMap = []
        for category in uniqueCategories:
            item={}
            item[category] = category_map.get(category)
            uniqueCategoriesMap.append(item)
        #iterate through each category pair
        print(uniqueCategoriesMap)
        for category in uniqueCategoriesMap:
            print("Generating Payload for LLM")
            payload = generatePayload(category)
            print("Sending Payload to LLM and generating the dialog")
            dialog = createDialog(payload,endpoint)
            print(dialog)
            print("Generating audio file")
            audio = generateAudio(dialog,runId,category,bucketName,s3)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        return 'Error occurred:'
