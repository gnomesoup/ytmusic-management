import json
from os import name
import re
from ytmusicFunctions import GetDetailedSongData, GetSongId
from ytmusicapi import YTMusic
from datetime import datetime, timezone
from dateutil import parser
from secretsFile import malojaKey, malojaURL, mongoString
from requests import post
import pickle
from pymongo import MongoClient

def parseTakeoutItem(item:dict) -> dict:
    # try:
    outDict = {}
    outDict["time"] = parser.parse(item["time"])
    titleUrl = item["titleUrl"]
    regexString = re.compile(r"\?v=(.*)$")
    result = regexString.search(titleUrl)
    outDict["videoId"] = result.group(1)
    return outDict

def songDocumentfromYTMusicData(ytMusic:YTMusic, takeoutData:dict) -> dict:
    outDict = {}
    song = GetDetailedSongData(ytMusic, takeoutData['videoId'])
    outDict["time"] = takeoutData['time']
    outDict["title"] = song["title"]
    outDict["artists"] = [artist for artist in song["artists"]]
    outDict["source"] = "YouTube Music"
    outDict["user"] = "michael"
    outDict["videoId"] = song["videoId"]
    return outDict

def PostScrobble(dbCollection, request):
    if request is not None:
        request['songId'] = GetSongId(ytmusic, db=db, videoId=request['videoId'])
        dbCollection.insert_one(request)
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

# with open(takeoutFilePath) as takeoutFile:
#     allTakeoutData = json.load(takeoutFile)

# print("allTakeoutData count:", len(allTakeoutData))
# currentData = [item for item in allTakeoutData\
#     if (parser.parse(item['time']) > parser.parse("2021-07-24T00:00:00.000Z"))]
# print("currentData:", len(currentData))


# takeoutData = [parseTakeoutItem(item) for item in currentData
#                if (item["header"] == "YouTube Music" and "titleUrl" in item)]
            
# with open("takeoutData.p", "wb") as file:
#     pickle.dump(takeoutData, file)
with open("takeoutData.p", "rb") as file:
    takeoutData = pickle.load(file)

print("ytmusic count:", len(takeoutData))

# songDocuments = [
#     songDocumentfromYTMusicData(ytmusic, takeout) for takeout in takeoutData
# ]
# with open("songDocuments.p", "wb") as file:
#     pickle.dump(songDocuments, file)
with open("songDocuments.p", "rb") as file:
    songDocuments = pickle.load(file)

print("ytmusic count:", len(songDocuments))

while songDocuments:
    songDocuments = [request for request in songDocuments\
                    if not PostScrobble(db['scrobbles'], request)]