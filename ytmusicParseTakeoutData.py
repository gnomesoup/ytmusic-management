import json
from os import name
import re
from ytmusicFunctions import GetDetailedSongData, GetSongId
from ytmusicapi import YTMusic
from datetime import datetime, timezone
from dateutil import parser
from secretsFile import mongoString
from secretsFile import homeassistantToken, homeassistantUrl
from requests import post
import pickle
from pymongo import MongoClient
import ytmusicHousekeeping

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

if __name__ == "__main__":
    takeoutFilePath = "/Users/mpfammatter/Downloads/Takeout/"\
        + "YouTube and YouTube Music/history/watch-history.json"

    ytmusic = YTMusic("oauth.json")
    mongoClient = MongoClient(mongoString)
    db = mongoClient['scrobble']

    # with open(takeoutFilePath, encoding="UTF-8") as takeoutFile:
    #     allTakeoutData = json.load(takeoutFile)

    # print("allTakeoutData count:", len(allTakeoutData))
    # currentData = [item for item in allTakeoutData\
    #     if (parser.parse(item['time']) > parser.parse("2021-08-02T22:00:00.000Z"))]
    # print("currentData:", len(currentData))


    # takeoutData = [parseTakeoutItem(item) for item in currentData
    #                if (item["header"] == "YouTube Music" and "titleUrl" in item)]
                
    # with open("takeoutData.p", "wb") as file:
    #     pickle.dump(takeoutData, file)
    with open("takeoutData.p", "rb") as file:
        takeoutData = pickle.load(file)

    print("ytmusic count:", len(takeoutData))

    for track in takeoutData[38:]:
        videoData = GetDetailedSongData(
            ytmusic=ytmusic,
            videoId=track['videoId']
        )
        request = ytmusicHousekeeping.BuildRequest(
            ytmusicHistoryItem=videoData,
            user="michael",
            scrobbleTime=track['time']
        )
        scrobbleId = ytmusicHousekeeping.PostScrobble(
            db=db,
            request=request
        )
        location = ytmusicHousekeeping.GetLocationFromHomeAssistant(
            homeassistantUrl=homeassistantUrl,
            homeassistantToken=homeassistantToken,
            locationEntity="person.michael",
            timePoint=track['time']
        )
        if location:
            ytmusicHousekeeping.ScrobbleAddLocation(
                dbCollection=db['scrobbles'],
                scrobbleId=scrobbleId,
                location=location
            )
        ytmusicHousekeeping.LinkScrobblerSong(ytmusic, db, scrobbleId)
