import re
from requests import get
from datetime import datetime, timedelta

def GetLatestHistory(
    updatedHistory,
    history,
    scrobblerUser,
    location={}
):
    '''
    Compare the latest YouTube Music history with a previously pulled
    dictionary of history.
    '''

    newHistory = []
    for song in updatedHistory:
        artists = [artist['name'] for artist in song['artists']]
        # if song['played'] in ["Today"]:
        if "release" in song:
            release = song['release']
        if song['played'] in ["Today", "Yesterday"]:
            newHistory.append({
                "videoId": song['videoId'],
                "title": song['title'],
                "artists": artists,
                "album": song['album']['name'],
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
            "videoId": song['videoId'],
            "location": location
            }
        newRequests.append(requestData)

    return newHistory, newRequests

def PostScrobble(dbCollection, request):
    try:
        result = dbCollection.insert_one(request)
        print(result.inserted_id)
        return True
    except Exception as e:
        print("Error posting scrobble:", e)
        print("Queueing for next run")
        return False

def GetLocationFromHomeAssistant(
    homeassistantUrl,
    homeassistantToken,
    locationEntity
):
    try:
        homeassistantResult = get(
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
    except Exception as e:
        print("location error:", e)
        location = {}
    return location
