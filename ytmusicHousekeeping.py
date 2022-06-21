from bson.objectid import ObjectId
from datetime import datetime
from os import chdir
from pymongo.collection import Collection, ReturnDocument
from pymongo.database import Database
from pymongo import DESCENDING
from pymongo import MongoClient
import requests
import schedule
from secretsFile import mongoString, homeassistantToken, homeassistantUrl
from threading import Thread
import time
from types import FunctionType
from ytmusicapi import YTMusic
from ytmusicFunctions import GetSongId
from ytmusicPlaylistDoubleYouMixAreShe import MixChicagoRadioStations
from ytmusicPlaylistWDVX import UpdateWDVXYesterday
from ytmusicPlaylistWXRTSaturdayMorningFlashback import CreateWXRTFlashback
from ytmusicPlaylistCKPKyesterday import UpdateCKPKYesterday
from ytmusicPlaylistWKLQyesterday import UpdateWKLQYesterday
from ytmusicPlaylistWXRTyesterday import UpdateWXRTYesterday
from ytmusicPlaylistWSHEyesterday import UpdateWSHEYesterday
from ytmusicPlaylistWTMXyesterday import UpdateWTMXYesterday
from WDVXCollectPlaylist import WDVXCollectPlaylistData


def runThreaded(function: FunctionType, name: str):
    # print(f"{datetime.now().isoformat()}  " f"Running: {name}")
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


def BuildRequest(
    ytmusicHistoryItem: dict, user: str, scrobbleTime: datetime = None
) -> dict:
    if scrobbleTime is None:
        scrobbleTime = datetime.utcnow()
    artists = [artist["name"] for artist in ytmusicHistoryItem["artists"]]
    if "duration" in ytmusicHistoryItem:
        duration = ytmusicHistoryItem["duration"]
    elif "length" in ytmusicHistoryItem:
        duration = ytmusicHistoryItem["length"]
    else:
        duration = None
    try:
        album = ytmusicHistoryItem["album"]["name"]
    except Exception:
        album = None
    return {
        "time": scrobbleTime,
        "videoId": ytmusicHistoryItem["videoId"],
        "title": ytmusicHistoryItem["title"],
        "artists": artists,
        "album": album,
        "duration": duration,
        "user": user,
    }


def PostScrobble(db: Database, request: dict) -> dict:
    result = db["scrobbles"].insert_one(request)
    return result.inserted_id


def LinkScrobblerSong(ytmusic: YTMusic, db: Database, scrobbleId: ObjectId) -> ObjectId:
    scrobbleDocument = db["scrobbles"].find_one({"_id": scrobbleId})
    songId = GetSongId(ytmusic, db, scrobbleDocument["videoId"])
    if songId:
        db["scrobbles"].update_one(
            {"_id": scrobbleDocument["_id"]}, {"$set": {"songId": songId}}
        )
    return songId


def GetLocationFromHomeAssistant(
    homeassistantUrl: str,
    homeassistantToken: str,
    locationEntity: str,
    timePoint: datetime = None,
) -> dict:
    location = {}
    if timePoint is None:
        url = f"{homeassistantUrl}/api/states/{locationEntity}"
    else:
        homeassistantTime = timePoint.strftime("%Y-%m-%dT%H:%M:%S")
        url = (
            f"{homeassistantUrl}/api/history/period/{homeassistantTime}"
            f"?filter_entity_id={locationEntity}&minimal_response"
        )
    try:
        homeassistantResult = requests.get(
            url,
            headers={
                "Authorization": "Bearer " + homeassistantToken,
                "Content-Type": "application/json",
            },
        )
        homeassistantData = homeassistantResult.json()
        if timePoint is not None:
            homeassistantData = homeassistantData[0][0]
        location = {
            "type": "Point",
            "coordinates": [
                homeassistantData["attributes"]["longitude"],
                homeassistantData["attributes"]["latitude"],
            ],
        }
    except Exception:
        location = None
    return location


def ScrobbleAddLocation(
    dbCollection: Collection, scrobbleId: str, location: dict
) -> ReturnDocument:
    return dbCollection.update_one(
        {"_id": scrobbleId}, {"$set": {"location": location}}
    )


def YTMusicScrobble(ytmusic: YTMusic, connectionString: str, user: str) -> None:
    mongoClient = MongoClient(connectionString)
    db = mongoClient["scrobble"]
    scrobblerData = {
        "scrobblerId": "607f962eeafb5500062a4a68",
        "scrobblerUser": "michael",
        "queuedRequests": [],
        "requestAttempts": 0,
    }

    lastScrobbles = (
        db["scrobbles"]
        .find({"user": scrobblerData["scrobblerUser"]}, projection={"videoId": 1})
        .sort("time", DESCENDING)
        .limit(1)
    )
    lastScrobbleIds = [scrobble["videoId"] for scrobble in lastScrobbles]
    for i in range(4):
        ytmusicHistory = ytmusic.get_history()
        if len(ytmusicHistory) == 0:
            return
        historyVideoIds = [track["videoId"] for track in ytmusicHistory]
        matchStartIndex = len(historyVideoIds)
        endIndex = len(lastScrobbleIds)
        for i in range(len(historyVideoIds)):
            historySublist = historyVideoIds[i : i + endIndex]
            lastScrobbleSublist = lastScrobbleIds[0 : len(historySublist)]
            if historySublist == lastScrobbleSublist:
                matchStartIndex = i
                break
        if matchStartIndex < 1:
            return
        elif matchStartIndex < 2:
            break
        else:
            print(f"Large number of scrobbles: {matchStartIndex}")
    # because ytmusic is so inconsistent with how they report history,
    # sometimes songs just disappear and we get the whole 200 songs in the
    # history at onces. So, if the length equals 200, just get the last song
    matchStartIndex = 1 if matchStartIndex == 200 else matchStartIndex
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
            ScrobbleAddLocation(db["scrobbles"], scrobbleId, location)
            LinkScrobblerSong(ytmusic, db, scrobbleId)
            print(f"{datetime.now().isoformat()}  Posted Scrobble")
    return


if __name__ == "__main__":
    print("YouTube Music Housekeeping")
    chdir("/ytmusic")
    ytmusic = YTMusic("headers_auth.json")
    user = "michael"
    schedule.every().day.at("00:00").do(
        runThreaded,
        lambda: UpdateWSHEYesterday(
            ytmusic, "PLJpUfuX6t6dTyEfFJmvVlIGzcXR1dKFt5", mongoString
        ),
        "WSHE_Yesterday",
    )
    schedule.every().day.at("00:15").do(
        runThreaded,
        lambda: UpdateWTMXYesterday(
            ytmusic, "PLJpUfuX6t6dS__5F2qgcopS26s5MbO8Yd", mongoString
        ),
        "WSHE_Yesterday",
    )
    schedule.every().day.at("00:30").do(
        runThreaded,
        lambda: UpdateWXRTYesterday(
            ytmusic, "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw", mongoString
        ),
        "WXRT_Yesterday",
    )
    schedule.every().day.at("00:45").do(
        runThreaded,
        lambda: UpdateWKLQYesterday(
            ytmusic, "PLJpUfuX6t6dRg0mxM5fEufwZOd5eu_DmU", mongoString
        ),
        "WKLQ_Yesterday",
    )
    schedule.every().day.at("01:30").do(
        runThreaded,
        lambda: UpdateWDVXYesterday(
            ytmusic=ytmusic,
            playlistId="PLJpUfuX6t6dTz7hGKVztERi0YnE_azCg1",
            dbConnectionString=mongoString,
        ),
        "WDVX Yesterday",
    )
    schedule.every().day.at("01:00").do(
        runThreaded,
        lambda: MixChicagoRadioStations(ytmusic=ytmusic),
        "Double_You_Mix_Are_She_Playlist",
    )
    schedule.every().minute.at(":00").do(
        runThreaded,
        lambda: YTMusicScrobble(ytmusic, mongoString, user),
        "Scrobble YTMusic",
    )
    schedule.every().hour.at("00:30").do(
        runThreaded,
        lambda: WDVXCollectPlaylistData(
            "https://wdvx.com/listen/playlist/", "WDVX-Playlist.json"
        ),
        "Collect WDVX Data",
    )
    schedule.every().hour.at("30:30").do(
        runThreaded,
        lambda: WDVXCollectPlaylistData(
            "https://wdvx.com/listen/playlist/", "WDVX-Playlist.json"
        ),
        "Collect WDVX Data",
    )
    YTMusicScrobble(ytmusic, mongoString, user)
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"{datetime.now().isoformat()}  " f"Schedule error: {e}")
        time.sleep(1)
