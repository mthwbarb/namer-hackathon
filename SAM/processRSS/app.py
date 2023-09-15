import feedparser
from datetime import datetime, timedelta
import json
import boto3
import os
import requests
from bs4 import BeautifulSoup


def generateManifest(manifest,prefix,run_id,bucket):
    s3=boto3.resource('s3')
    bucket = s3.Bucket(bucket)
    #categroy to friendly name map pulled from website
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
    "networking":"Networking and Content Delivery",
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
    #append friendly category names to manifest.  If it doesnt exist in the map, tag it as Other AWS Services
    manifest=manifest
    manifest2 = []
    for item in manifest:
        try:
            item['category-friendly-name'] = category_map.get(item['category'])
            item['runId'] = run_id
        except:
            item['category-friendly-name'] = "Other AWS Services"
            item['runId'] = run_id
        #print(item)
        manifest2.append(item)


    #write the manifest json object to s3
    s3object = s3.Object(bucket.name, run_id+'/manifest.json')
    response = s3object.put(Body=json.dumps(manifest2))
    print("Manifest generated. Key: " + s3object.key)
    return manifest2

def parseFeed(url,run_id,num_days,bucket):
    feed = feedparser.parse(url)
    s3=boto3.resource('s3')
    bucket = s3.Bucket(bucket)
    manifest = []
    
    # Define the time range (e.g., the last 7 days)
    now = datetime.utcnow()
    time_range = timedelta(days=int(num_days))
    print("Parsing RSS Feed for the last "+num_days+' days')
    # Iterate through entries and filter by the time range
    for entry in feed.entries:
        entry_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
        if now - entry_date.replace(tzinfo=None) <= time_range:
            
            #Some feed items have multiple categories, just get the first one.  We only want the "marketing" tag.  If it doesnt exist, tag as "general"
            tags = entry.tags[0]["term"]
            tagslist = (tags.split(","))
            try:
                result = list(filter(lambda x: x.startswith('marketing'),tagslist))
                category = result[0].rsplit("/", 1)[1]
            except:
                category = "general"
            
            #get the year and week #
            week = datetime.date(entry_date).isocalendar()[1]
            year = datetime.date(entry_date).isocalendar()[0]
            
            #scrape the post for the content
            scrapedtext = ''
            r = requests.get(entry.link)
            soup = BeautifulSoup(r.content, 'html.parser')
            divs = soup.find_all('div', class_='aws-text-box')
            for div in divs:
                lines = div.find_all('p')
                for line in lines:
                    scrapedtext += line.text
            
            #create the post object
            post = {
                "id": entry.id,
                "category": category,
                "title": entry.title,
                "url": entry.link,
                "date": entry.published,
                "week": datetime.date(entry_date).isocalendar()[1],
                "text": scrapedtext
            }
            
            #write the feed metadata json object to s3
            print('Post Title: ' + post['title'])
            s3object = s3.Object(bucket.name, run_id + '/processed/' + entry.id + '.json')
            response = s3object.put(Body=json.dumps(post))
            
            #Generate the manifest
            manifestObject = {}
            manifestObject['id'] = entry.id
            manifestObject['category'] = category           
            manifestObject['metadata'] = {
                "bucket": s3object.bucket_name,
                "key": s3object.key,
                "title": entry.title,
                "url": entry.link,
                "date": entry.published,
                "week": datetime.date(entry_date).isocalendar()[1],
                "year": year
            }
            manifest.append(manifestObject)
            prefix = str(year)+'/'+str(week)
            
    return manifest,prefix

def lambda_handler(event, context):
    print(event)
    runId = event['uuid']
    feed_url = event['feedUrl']
    num_days = event['numDays']
    bucket = event['bucket']
    try:
        print("RunId is "+runId)
        print("Bucket: "+bucket+"Feed URL: "+feed_url+"Number of days to parse: "+num_days)
        result = parseFeed(feed_url,runId,num_days,bucket)
        print("Generating Manifest")
        result2 = generateManifest(result[0],result[1],runId,bucket)
        return result2
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        return 'Error occurred'