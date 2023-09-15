import boto3
import json
import os

def lambda_handler(event, context):
    try:
        s3=boto3.resource('s3')
        
        #get data from step function input
        bucketname = event['bucket']
        key = event['key']
        itemId = event['itemId']
        runId = event['runId']
        
        print("RunId: "+runId)
        #load the sentences from the s3 object
        bucket = s3.Bucket(bucketname)
        dialogObject = bucket.Object(key).get()['Body'].read().decode('utf-8')
        dialogObject_json = json.loads(dialogObject)
        print("Loading dialog file: " + key)
        #iterate over each sentence and send to Polly for synthesis
        polly_client = boto3.client('polly')
        for sentence in dialogObject_json:
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
        print('Uploading mp3 file to s3: ' + runId + '/topic_audio/'+itemId+'.mp3')
        s3.meta.client.upload_file('/tmp/output.mp3',bucket.name,runId + '/topic_audio/'+itemId+'.mp3')
        #cleanup
        os.remove("/tmp/output.mp3")
        
        #prepare output for step function
        manifestObject = {
            "id": itemId,
            "runId": runId,
            "inputObject":  key,
            "outputBucket": bucket.name,
            "audioObjectKey": 'topic_audio/'+itemId+'.mp3'
            
        }
    
        print("done")
        return manifestObject
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        return 'Error occurred'