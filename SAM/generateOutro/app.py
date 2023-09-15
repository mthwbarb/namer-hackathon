import boto3
import json
import os
from datetime import date
import re

s3=boto3.resource('s3')
sagemaker = boto3.client('sagemaker')

runtime = boto3.client('runtime.sagemaker')


def generatePayload(date):
    #construct the prompt
    payload = {
        "inputs": [
            [
                {
                    "role": "system",
                    "content": "You are writing a script for your AWS podcast called 'The AWS Factor' which is focused on the latest news and announcements. You are the host named Li.  There is a co-host named Richard.",
                },
                {
                    "role": "user", 
                    "content": "Write an outro for the podcast focused on the latest announcements from AWS from the past week.  Remind audience to check out the AWS news Blog. End with something similar to 'See you next week'."
                }
            ]
        ],
        "parameters": {"max_new_tokens": 1500, "top_p": 0.9, "temperature": 0.72},
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
    sentences_list = [y for y in (x.strip() for x in output.splitlines()) if y]
    dialog=[]
    i=1
    print("Generating Sentence List")
    for sentence in sentences_list:
        try:
            sentence_voice = sentence.rsplit(': ', 1)[0]
            sentence_content = sentence.rsplit(': ', 1)[1]
            #Strip out non-verbal words like *chuckles* since the LLM wont omit them no matter how hard i try
            sentence_content = re.sub('\*.*?\*', '', sentence_content)
            dialog.append({"seq":i, "voice":sentence_voice, "content":sentence_content})
            i=i+1
        except:
            print("Skipping sentence")
    return dialog

def generateAudio(payload,run_id,bucket,s3Client):
    #load the sentences from the s3 object
    s3=s3Client
    #iterate over each sentence and send to Polly for synthesis
    polly_client = boto3.client('polly')
    for sentence in payload:
        if sentence["voice"] == "Richard":
            print('Generating audio snippet for sequence #: ' + str(sentence["seq"]) + '.  Sentence: ' + sentence["content"])
            response = polly_client.synthesize_speech(VoiceId='Stephen',
                            OutputFormat='mp3', 
                            Text = sentence["content"],
                            Engine = 'neural')
            
            #append the bits to existing mp3
            file = open('/tmp/output.mp3', 'ab+')
            file.write(response['AudioStream'].read())
            file.close()
        else:
            print('Generating audio snippet for sequence #: ' + str(sentence["seq"]) + '.  Sentence: ' + sentence["content"])
            response = polly_client.synthesize_speech(VoiceId='Ruth',
                            OutputFormat='mp3', 
                            Text = sentence["content"],
                            Engine = 'neural')
            
            #append the bits to existing mp3
            file = open('/tmp/output.mp3', 'ab+')
            file.write(response['AudioStream'].read())
            file.close()
    #upload the mp3 object to s3
    print('Uploading mp3 file to s3: ' + run_id + '/other_audio/outro.mp3')
    s3.meta.client.upload_file('/tmp/output.mp3',bucket,run_id + '/other_audio/outro.mp3')
    #cleanup
    os.remove("/tmp/output.mp3")

    return 

def lambda_handler(event, context):
    try:
        print("Starting...")
        print(event)
        s3=boto3.resource('s3')
        bucketName = event['bucket']
        bucket = s3.Bucket(bucketName)
        runId = event['uuid']
        endpoint = event['llmEndpoint']
        numDays = event['numDays']
        
        print("runId: " +runId)
        print("Bucket: "+bucketName)
        
        manifestObject = bucket.Object(runId + '/manifest.json').get()['Body'].read().decode('utf-8')
        manifestObject_json = json.loads(manifestObject)
        
        anyItem = manifestObject_json[0]
        anyItemMetadata = anyItem.get('metadata')
        week = anyItemMetadata.get('week')
        year = anyItemMetadata.get('year')
        today = date.today()
        todayDate = today.strftime("%B %d, %Y")
        
        print("Generating Payload for LLM")
        payload = generatePayload(todayDate)
        print(payload)
        print("Sending Payload to LLM and generating the dialog")
        dialog = createDialog(payload,endpoint)
        print(dialog)
        print("Generating audio file")
        generateAudio(dialog,runId,bucketName,s3)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        return 'Error occurred'