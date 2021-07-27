from types import FunctionType
import dataclasses
from bson.objectid import ObjectId
from pymongo.collection import Collection, ReturnDocument
from pymongo.database import Database
from pymongo import DESCENDING
from ytmusicapi import YTMusic
from datetime import datetime
import time
from pymongo import MongoClient
from secretsFile import mongoString, homeassistantToken, homeassistantUrl
from ytmusicFunctions import CreateWXRTFlashback
from ytmusicFunctions import UpdateCKPKYesterday
from ytmusicPlaylistWKLQyesterday import UpdateWKLQYesterday
from ytmusicPlaylistWXRTyesterday import UpdateWXRTYesterday
import schedule
from threading import Thread
import re

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

def GetLatestHistory(
    updatedHistory:list, history:list, scrobblerUser:str
) -> list:
    '''
    Compare the latest YouTube Music history with a previously pulled
    dictionary of history.
    '''

    newHistory = []
    for song in updatedHistory:
        # if song['played'] in ["Today"]:
        if "release" in song:
            release = song['release']
        if song['played'] in ["Today", "Yesterday"]:
            artists = [artist['name'] for artist in song['artists']]
            try:
                album = song['album']['name']
            except Exception:
                album = None
            newHistory.append({
                "videoId": song['videoId'],
                "title": song['title'],
                "artists": artists,
                "album": album,
                "played": song['played'],
                "duration": song['duration']
            })

    if history:
        currentIndex = 0
        matchStartIndex = 0
        lastId = None
        for i in range(len(newHistory)):
            currentId = newHistory[i]['videoId']
            if newHistory[i]['videoId'] == history[currentIndex]:
                if currentId != lastId:
                    currentIndex = currentIndex + 1
                    lastId = currentId
                    break
            else:
                matchStartIndex = i + 1
    regex = re.compile(r"(?P<minutes>\d+):(?P<seconds>\d+)")
    now = datetime.now()
    songDurations = timedelta(seconds=0)
    postCount = 0
    newRequests = []
    for song in reversed(newHistory[0:matchStartIndex]):
        requestData = {
            "artists": song['artists'],
            "title": song['title'],
            "album": song['album'],
            "source": "YouTube Music",
            "time": datetime.utcnow(),
            "user": scrobblerUser,
            "videoId": song['videoId']
            }
        newRequests.append(requestData)

    return newHistory, newRequests

def PostScrobble(db:Database, request:dict) -> dict:
    result = db['scrobbles'].insert_one(request)
    return {"scrobbleId": result.inserted_id, "videoId": request['videoId']}

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

def ScrobbleCheck(ytmusic:YTMusic, db:Database, scrobblerUser:str) -> list:
    if not hasattr(ScrobbleCheck, "queuedRequests"):
        ScrobbleCheck.queuedRequests = []
    if not hasattr(ScrobbleCheck, "requestAttempts"):
        ScrobbleCheck.requestAttempts = 0
    updatedHistory = {}
    setVariables = {}
    scrobbleIds = {}

    # Get previous scrobble history
    history = GetScrobblerHistory(db['scrobblers'], scrobblerUser)
    if not history:
        updatedHistory = ytmusic.get_history()
        setVariables['videoIds'] = [item['videoId'] for item in updatedHistory]
    else:
        requestsReady = False
        while not requestsReady:
            updatedHistory = ytmusic.get_history()
            updatedHistory, newRequests = GetLatestHistory(
                updatedHistory,
                history,
                scrobblerUser
            )
            if len(newRequests) > 2 and ScrobbleCheck.requestAttempts < 4:
                print(
                    f"{datetime.now().isoformat()}  Too many requests!"
                    f"history: {len(history)} "
                    f"updatedHistory: {len(updatedHistory)} "
                    f"attempts: {ScrobbleCheck.requestAttempts}"
                )
                ScrobbleCheck.requestAttempts += 1
                print("requestAttempt:", ScrobbleCheck.requestAttempts)
            else:
                ScrobbleCheck.requestAttempts = 0
                requestsReady = True
        if requestsReady:
            if ScrobbleCheck.queuedRequests:
                ScrobbleCheck.queuedRequests += newRequests
            else:
                ScrobbleCheck.queuedRequests = newRequests
            if ScrobbleCheck.queuedRequests:
                postResult = [
                    PostScrobble(db, request)
                    for request in ScrobbleCheck.queuedRequests
                ]
                postedVideoIds = [
                    request['videoId'] for request in postResult
                ]
                scrobbleIds = [
                    request['scrobbleId'] for request in postResult
                ]
                ScrobbleCheck.queuedRequests = [
                    request for request in ScrobbleCheck.queuedRequests
                    if request['videoId'] not in postedVideoIds
                ]
            if updatedHistory:
                videoIds = [item['videoId'] for item in updatedHistory]
                setVariables["videoIds"] = videoIds
    setVariables["lastUpdate"] = datetime.utcnow()
    db['scrobblers'].update_one(
        {
            "name": "ytmusic history scrobbler",
            "user": scrobblerUser
        },
        {
            "$set": setVariables
        }
    )
    return scrobbleIds

def YTMusicScrobble(ytmusic:YTMusic, connectionString:str):
    print("YTMusicScrobble")
    mongoClient = MongoClient(connectionString)
    db = mongoClient['scrobble']
    scrobblerData = {
        "scrobblerId": '607f962eeafb5500062a4a68',
        "scrobblerUser": "michael",
        "queuedRequests": [],
        "requestAttempts": 0
    }

    last200Scrobbles = db['scrobbles'].find(
        {
            "user": scrobblerData['scrobblerUser']
        },
        projection={"videoId": 1}
    ).sort("_id", DESCENDING).limit(200)
    last200videoIds = [scrobble['videoId'] for scrobble in last200Scrobbles]
    scrobblerHistory = GetScrobblerHistory(
        db['scrobblers'], scrobblerData['scrobblerUser']
    )
    ytmusicHistory = None
    while ytmusicHistory is None:
        print("Trying to get history")
        ytmusicHistory = ytmusic.get_history()
    historyVideoIds = [track['videoId'] for track in ytmusicHistory]
    print(len(historyVideoIds))
    unscrobbled = []
    matchStartIndex = 0
    for i, videoId in enumerate(historyVideoIds):
        if scrobblerHistory[matchStartIndex] != videoId:
            matchStartIndex += 1
            unscrobbled.append(videoId)

    return

    try:
        scrobbleIds = ScrobbleCheck(ytmusic, db, scrobblerData['scrobblerUser'])
        if scrobbleIds:
            location = GetLocationFromHomeAssistant(
                homeassistantUrl,
                homeassistantToken,
                "person.michael",
            )
            for scrobbleId in scrobbleIds:
                ScrobbleAddLocation(
                    db['scrobbles'],
                    scrobbleId,
                    location
                )
                LinkScrobblerSong(ytmusic, db, scrobbleId)

            if len(scrobbleIds) == 1:
                suffix = ""
            else:
                suffix = "s"
            print(
                f"{datetime.now().isoformat()}  "
                f"Posted {len(scrobbleIds)} scrobble{suffix}"
            )
    except Exception as e:
        print(
            f"{datetime.now().isoformat()}  "
            f"Scrobble error: {e}"
        )
    
    try:
        schedule.run_pending()
    except Exception as e:
        print( 
            f"{datetime.now().isoformat()}  "
            f"Schedule error: {e}"
        )



if __name__ == "__main__":
    print("YouTube Music Housekeeping")
    ytmusic = YTMusic("headers_auth.json")
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
        lambda: YTMusicScrobble(ytmusic, mongoString),
        "Check for and add ytmusic scrobbles"
    )

    YTMusicScrobble(ytmusic, mongoString)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)