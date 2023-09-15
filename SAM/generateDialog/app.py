import boto3
import json

s3=boto3.resource('s3')
sagemaker = boto3.client('sagemaker')
runtime = boto3.client('runtime.sagemaker')

def generatePayload(feed_item):
    feed_item_json = json.loads(feed_item)
    text = feed_item_json['text']
    payload = {
        "inputs": [
            [
                {
                    "role": "system",
                    "content": "Discuss in the form of a 45 second casual podcast conversation between 2 hosts named Richard and Li.  Because this is one of many topics, do not close out the conversation and do not greet the other host.",
                },
                {
                    "role": "user", 
                    "content": text
                }
            ]
        ],
        "parameters": {"max_new_tokens": 1500, "top_p": 0.9, "temperature": 0.8},
    }
    return payload

def createDialog(payload,endpoint):
    print("Invoking Endpoint")
    response = runtime.invoke_endpoint(EndpointName=endpoint, ContentType='application/json', Body=json.dumps(payload), CustomAttributes="accept_eula=true")
    result = json.loads(response['Body'].read().decode())
    output = result[0]["generation"]["content"]
    print(result)
    sentences_list = [y for y in (x.strip() for x in output.splitlines()) if y]
    dialog=[]
    i=1
    print("Generating Sentence List")
    for sentence in sentences_list:
        print(sentence)
        #Skip over non-speech sentences
        try:
            sentence_voice = sentence.rsplit(': ', 1)[0]
            sentence_content = sentence.rsplit(': ', 1)[1]
            dialog.append({"seq":i, "voice":sentence_voice, "content":sentence_content})
            i=i+1
        except:
            print("There doesnt appear to be a voice indicator, skipping.")
    return dialog

def write_object(bucket,feeditem,dialog,run_id):
    feed_item_json = json.loads(feeditem)
    itemId = feed_item_json['id']
    s3object = s3.Object(bucket, run_id + '/dialogs/'+itemId+'.json')
    s3object.put(Body=json.dumps(dialog))
    manifestObject = {
    "itemId": itemId,
    "bucket": s3object.bucket_name,
    "key": s3object.key,
    "runId": run_id
    }
    return s3object,manifestObject

def lambda_handler(event, context):
    try:
        print("Event Data:")
        print(event)
        bucketname = event['Result']['metadata']['bucket']
        key = event['Result']['metadata']['key']
        runId = event['runId']
        endpoint = event['llmEndpoint']
        bucket = s3.Bucket(bucketname)
        feeditem = bucket.Object(key).get()['Body'].read().decode()
        print('runId is: ' + runId)
        payload = generatePayload(feeditem)
        dialog = createDialog(payload,endpoint)
        response = write_object(bucketname,feeditem,dialog,runId)
        #print(response)
        return response[1]
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        return 'Error occurred'
