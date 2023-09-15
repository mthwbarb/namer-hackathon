import boto3
import streamlit as st
import json
import time
import base64

#Replace these variables
####################################################
bucketName = '<YOUR BUCKET NAME'
runId = '<YOUR UUID>'
####################################################

def startPodcast():
    st.title('The AWS Factor Podcast')
    s3=boto3.resource('s3')
    bucket = s3.Bucket(bucketName)
    playlistObject_json = bucket.Object(runId+'/playlist.json').get()['Body'].read().decode()
    playlistObject = json.loads(playlistObject_json)
    sortedList = sorted(playlistObject, key=lambda x: x['seq'])
    audio = bucket.Object(runId + '/podcast.mp3').get()
    audioStream = audio['Body'].read()
    
    #st.audio(audioStream, format='audio/mp3')
    b64 = base64.b64encode(audioStream).decode()
    md = f"""
        <audio controls autoplay="true">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(
        md,
        unsafe_allow_html=True,
    )
    time.sleep(10)
    
    t = st.empty()
    u = st.empty()
    for i in sortedList:
        #print(i.get("metadata", {}).get("title"))
        t.markdown("## Segment Title: " + str(i.get("title")))
        u.markdown("## Link: " + str(i.get("url")))
        time.sleep(i.get("length"))


st.title('The AWS Factor Podcast')
st.button('Start', on_click=startPodcast)