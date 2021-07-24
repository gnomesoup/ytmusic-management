import re
from ytmusicFunctions import GetLikeStatus
import requests
from datetime import datetime, timedelta

def GetLatestHistory(updatedHistory, history, scrobblerUser):
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

def PostScrobble(db, request):
    result = db['scrobbles'].insert_one(request)
    return {"scrobbleId": result.inserted_id, "videoId": request['videoId']}

def LinkScrobblerSong(ytmusic, db, _id):
    scrobbleDocument = db['scrobbles'].find_one(
        {"_id": _id}
    )
    songId = GetSongId(ytmusic, db, scrobbleDocument['videoId'])
    if songId:
        db['scrobbles'].update_one(
            {"_id": scrobbleDocument["_id"]},
            {"$set": {"songId": songId}}
        )
    return songId


def GetLocationFromHomeAssistant(
    homeassistantUrl,
    homeassistantToken,
    locationEntity
):
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

def GetScrobblerHistory(dbCollection, scrobblerUser):
    history = []
    scrobblerInfo = dbCollection.find_one(
        {
            "name": "ytmusic history scrobbler",
            "user": scrobblerUser
        })
    if "videoIds" in scrobblerInfo:
        history = scrobblerInfo['videoIds']
    return history

def ScrobbleAddLocation( dbCollection, scrobbleId, location):
    return dbCollection.update_one(
        {"_id": scrobbleId},
        {"$set": {"location": location}}
    )

def ScrobbleCheck(ytmusic, MongoDB, scrobblerUser):
    if not hasattr(ScrobbleCheck, "queuedRequests"):
        ScrobbleCheck.queuedRequests = []
    if not hasattr(ScrobbleCheck, "requestAttempts"):
        ScrobbleCheck.requestAttempts = 0
    updatedHistory = {}
    setVariables = {}
    scrobbleIds = {}

    # Get previous scrobble history
    history = GetScrobblerHistory(MongoDB['scrobblers'], scrobblerUser)
    if not history:
        updatedHistory = ytmusic.get_history()
        setVariables[videoIds] = [item['videoId'] for item in updatedHistory]
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
                    PostScrobble(MongoDB, request)
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
    MongoDB['scrobblers'].update_one(
        {
            "name": "ytmusic history scrobbler",
            "user": scrobblerUser
        },
        {
            "$set": setVariables
        }
    )
    return scrobbleIds