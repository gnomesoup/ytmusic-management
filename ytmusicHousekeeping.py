from types import FunctionType
import dataclasses
import time
from bson.objectid import ObjectId
from pymongo.collection import Collection, ReturnDocument
from pymongo.database import Database
from pymongo import DESCENDING
from ytmusicapi import YTMusic
from datetime import datetime
from pymongo import MongoClient
from secretsFile import mongoString, homeassistantToken, homeassistantUrl
from ytmusicFunctions import GetSongId
from ytmusicFunctions import CreateWXRTFlashback
from ytmusicFunctions import UpdateCKPKYesterday
from ytmusicPlaylistWKLQyesterday import UpdateWKLQYesterday
from ytmusicPlaylistWXRTyesterday import UpdateWXRTYesterday
import schedule
from threading import Thread
import requests

def runThreaded(function:FunctionType, name:str):
    print(
        f"{datetime.now().isoformat()}  "
        f"Running: {name}"
    )
    job = Thread(target=function, name=name)
    job.start()

# @dataclasses
# class scrobble:
#     videoId = str
#     title = str
#     artists = list
#     album = str

def KeyCheck(key, documentData, ytmusicData):
    if key not in documentData:
        if key in ytmusicData:
            return True
        else:
            return False
    else:
        return False

def GetScrobblerHistory(dbCollection:Collection, scrobblerUser:str) -> list:
    history = []
    scrobblerInfo = dbCollection.find_one(
        {
            "name": "ytmusic history scrobbler",
            "user": scrobblerUser
        })
    if "videoIds" in scrobblerInfo:
        history = scrobblerInfo['videoIds']
    return history

def BuildRequest(ytmusicHistoryItem:dict, user:str) -> dict:
    artists = [artist['name'] for artist in ytmusicHistoryItem['artists']]
    try:
        album = ytmusicHistoryItem['album']['name']
    except Exception:
        album = None
    return {
        "time": datetime.utcnow(),
        "videoId": ytmusicHistoryItem['videoId'],
        "title": ytmusicHistoryItem['title'],
        "artists": artists,
        "album": album,
        "played": ytmusicHistoryItem['played'],
        "duration": ytmusicHistoryItem['duration'],
        "user": user
    }

def PostScrobble(db:Database, request:dict) -> dict:
    result = db['scrobbles'].insert_one(request)
    return result.inserted_id

def LinkScrobblerSong(
    ytmusic:YTMusic, db:Database, scrobbleId:ObjectId
) -> ObjectId:
    scrobbleDocument = db['scrobbles'].find_one(
        {"_id": scrobbleId}
    )
    songId = GetSongId(ytmusic, db, scrobbleDocument['videoId'])
    if songId:
        db['scrobbles'].update_one(
            {"_id": scrobbleDocument["_id"]},
            {"$set": {"songId": songId}}
        )
    return songId

def GetLocationFromHomeAssistant(
    homeassistantUrl:str,
    homeassistantToken:str,
    locationEntity:str
) -> dict:
    location = {}
    homeassistantResult = requests.get(
        homeassistantUrl + "/api/states/" + locationEntity,
        headers={
            "Authorization": "Bearer " + homeassistantToken,
            "Content-Type": "application/json"
        }
    )
    homeassistantData = homeassistantResult.json()
    location = {
        "type": "Point",
        "coordinates": [
            homeassistantData["attributes"]["longitude"],
            homeassistantData["attributes"]["latitude"]
        ]
    }
    return location

def ScrobbleAddLocation(
    dbCollection:Collection, scrobbleId:str, location:dict
) -> ReturnDocument:
    return dbCollection.update_one(
        {"_id": scrobbleId},
        {"$set": {"location": location}}
    )

def YTMusicScrobble(ytmusic:YTMusic, connectionString:str, user:str):
    mongoClient = MongoClient(connectionString)
    db = mongoClient['scrobble']
    scrobblerData = {
        "scrobblerId": '607f962eeafb5500062a4a68',
        "scrobblerUser": "michael",
        "queuedRequests": [],
        "requestAttempts": 0
    }

    lastScrobbles = db['scrobbles'].find(
        {
            "user": scrobblerData['scrobblerUser']
        },
        projection={"videoId": 1}
    ).sort("time", DESCENDING).limit(5)
    lastScrobbleIds = [scrobble['videoId'] for scrobble in lastScrobbles]
    matchStartIndex = 0
    for i in range(4):
        ytmusicHistory = ytmusic.get_history()
        if len(ytmusicHistory) == 0:
            return
        historyVideoIds = [track['videoId'] for track in ytmusicHistory]
        endIndex = len(lastScrobbleIds)
        for i in range(len(historyVideoIds)):
            historySublist = historyVideoIds[i:i+endIndex]
            if historySublist == lastScrobbleIds:
                matchStartIndex = i
                break
        if matchStartIndex < 1:
            return
        elif matchStartIndex < 2:
            break
        else:
            print(f"Large number of scrobbles: {matchStartIndex}")
    location = None
    for i in reversed(range(matchStartIndex)):
        request = BuildRequest(ytmusicHistory[i], user)
        scrobbleId = PostScrobble(db, request)
        if scrobbleId:
            if location is None:
                location = GetLocationFromHomeAssistant(
                    homeassistantUrl,
                    homeassistantToken,
                    "person.michael",
                )
            ScrobbleAddLocation(
                db['scrobbles'],
                scrobbleId,
                location
            )
            LinkScrobblerSong(ytmusic, db, scrobbleId)
            print(f"{datetime.now().isoformat()}  Posted Scrobble")
    return

if __name__ == "__main__":
    print("YouTube Music Housekeeping")
    ytmusic = YTMusic("headers_auth.json")
    user = "michael"
    schedule.every().day.at("00:00").do(
        runThreaded,
        lambda: UpdateWXRTYesterday(ytmusic, "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw"),
        "WXRT_Yesterday"
    )
    schedule.every().day.at("00:30").do(
        runThreaded,
        lambda: UpdateWKLQYesterday(ytmusic, "PLJpUfuX6t6dRg0mxM5fEufwZOd5eu_DmU"),
        "WKLQ_Yesterday"
    )
    schedule.every().day.at("02:05").do(
        runThreaded,
        lambda: UpdateCKPKYesterday(ytmusic, "PLJpUfuX6t6dR9DeM0gOH3rLt99Sl3SDVG"),
        "CKPK_Yesterday"
    )
    schedule.every().saturday.at("12:15").do(
        runThreaded,
        lambda: CreateWXRTFlashback(ytmusic),
        "WXRT_Saturday_Morning_Flashback"
    )
    schedule.every().minute.do(
        runThreaded,
        lambda: YTMusicScrobble(ytmusic, mongoString, user),
        "Check for and add ytmusic scrobbles"
    )
    YTMusicScrobble(ytmusic, mongoString, user)
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print( 
                f"{datetime.now().isoformat()}  "
                f"Schedule error: {e}"
            )
        time.sleep(1)