import json
from os import name
import re
from ytmusicapi import YTMusic
from datetime import datetime, timezone
from dateutil import parser
from secretsFile import malojaKey, malojaURL, mongoString
from requests import post
import pickle
from pymongo import MongoClient

def parseTakeoutItem(item, ytmusic):
    try:
        outDict = {}
        outDict["time"] = parser.parse(item["time"])
        titleUrl = item["titleUrl"]
        regexString = re.compile(r"\?v=(.*)$")
        result = regexString.search(titleUrl)
        song = ytmusic.get_song(result.group(1))
        outDict["title"] = song["title"]
        outDict["artists"] = [artist for artist in song["artists"]]
        outDict["source"] = "YouTube Music"
        outDict["user"] = "michael"
        outDict["videoId"] = song["videoId"]
        if "release" in song:
            outDict["release"] = song["release"]
        return outDict
    except Exception as e:
        print(item['title'], e)
        return

def PostScrobble(dbCollection, request):
    if request is not None:
        try:
            dbCollection.insert_one(request)
        except:
            pass
        return True
    else:
        print("Error posting scrobble", result)
        print("Queueing for next run")
        return False

takeoutFilePath = "/Users/mpfammatter/Downloads/Takeout/"\
    + "YouTube and YouTube Music/history/watch-history.json"

ytmusic = YTMusic("headers_auth.json")
mongoClient = MongoClient(mongoString)
db = mongoClient['scrobble']
# test = {"name": "test name", "artists": ["artist1", "artist2"],
#         "album": "test album",
#         "time": datetime.utcnow(), "user": "michael"}
# db['scrobbles'].insert_one(test,)

with open(takeoutFilePath) as takeoutFile:
    takeoutData = json.load(takeoutFile)

print("takeoutData count:", len(takeoutData))
currentData = [item for item in takeoutData\
    if (parser.parse(item['time']) < parser.parse("2020-10-01T00:00:00.000Z"))]
print("currentData:", len(currentData))

ytmusicData = [parseTakeoutItem(item, ytmusic) for item in currentData
               if (item["header"] == "YouTube Music" and "titleUrl" in item)]
            
with open("ytmusicData.p", "wb") as file:
    pickle.dump(ytmusicData, file)
# with open("ytmusicData.p", "rb") as file:
#     ytmusicData = pickle.load(file)

print("ytmusic count:", len(ytmusicData))

ytmusicData = [request for request in ytmusicData if request]

print("ytmusic count:", len(ytmusicData))

while ytmusicData:
    ytmusicData = [request for request in ytmusicData\
                    if not PostScrobble(db['scrobbles'], request)]