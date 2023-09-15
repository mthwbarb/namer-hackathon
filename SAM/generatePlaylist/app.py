import boto3
import json
import os
from mutagen.mp3 import MP3


def lambda_handler(event, context):
    try:
        bucketName = event['bucket']
        runId = event['uuid']
        
        s3=boto3.resource('s3')
        bucket = s3.Bucket(bucketName)
        manifestObject_json = bucket.Object(runId+'/manifest.json').get()['Body'].read().decode()
        manifestObject = json.loads(manifestObject_json)
        uniqueCategories = ( set(d['category'] for d in manifestObject) )
        #print(uniqueCategories)
        playList = []
        #Intro
        introItem={}
        introItem["seq"] = 0
        introItem["type"] = "intro"
        introItem["category"] = "none"
        introItem["objectKey"] = "other_audio/intro.mp3"
        introItem["url"] = ""
        introItem["title"] = "Introduction"
        playList.append(introItem)
        i=0
        
        for category in uniqueCategories:
            i=i+1
            itemList = [item for item in manifestObject if item['category'] == category]
            catItem={}
            catItem['seq'] = i
            catItem["type"] = "transition"
            catItem["category"] = category
            catItem["objectKey"] = "transition_audio/"+category+".mp3"
            catItem["url"] = "none"
            catItem["title"] = category
            playList.append(catItem)
            for item in itemList:
                i=i+1
                sortedItem = {}
                sortedItem['seq'] = i
                sortedItem["type"] = "topic"
                sortedItem["category"] = item.get("category")
                sortedItem["objectKey"] = "topic_audio/"+item.get("id")+".mp3"
                sortedItem["url"] = item.get("metadata", {}).get("url")
                sortedItem["title"] = item.get("metadata", {}).get("title")
                playList.append(sortedItem)
        
        #outro
        outroItem={}
        outroItem["seq"] = i+1
        outroItem["type"] = "outro"
        outroItem["category"] = "none"
        outroItem["objectKey"] = "other_audio/outro.mp3"
        outroItem["url"] = ""
        outroItem["title"] = "Outro"
        playList.append(outroItem)
        print("Uploading playlist to s3")
    
        
        
        #Create the final mp3 file
        sortedList = sorted(playList, key=lambda x: x['seq'])
        playlist2=[]
        for item in sortedList:
            
            print(item)
            objectKey = item['objectKey']
            print(runId + '/' + objectKey)
            #Get the obect and read it
            audio = bucket.Object(runId + '/' + objectKey).get()
            audioStream = audio['Body'].read()
            
            #download the object so we can get the length
            clip = s3.Bucket(bucketName).download_file(runId + '/' + objectKey, '/tmp/clip.mp3')
            mp3 = MP3('/tmp/clip.mp3')
            mp3Info = mp3.info    
            length_in_secs = int(mp3Info.length)
            os.remove("/tmp/clip.mp3")
            
            #add the length to the playlist
            item["length"] = length_in_secs
            playlist2.append(item)
           
            #append this audio to the output
            file = open('/tmp/output.mp3', 'ab+')
            file.write(audioStream)
            file.close()
        #upload the mp3 object to s3
        print('Uploading mp3 file to s3: ' + runId + '/podcast.mp3')
        s3Client=boto3.client('s3')
        s3Client.upload_file('/tmp/output.mp3',bucketName,runId + '/podcast.mp3')
        #cleanup
        print("Cleaning Up temp file")
        os.remove("/tmp/output.mp3")
        #return runId + '/playlist.json'
        
        #write playlist to s3
        s3object = s3.Object(bucketName, runId + '/playlist.json')
        response = s3object.put(Body=json.dumps(playlist2))
        print("Playlist saved to s3 bucket: "+bucketName+".  runId is: "+runId)
        return "Playlist saved to s3 bucket: "+bucketName+".  runId is: "+runId
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        return 'Error occurred'