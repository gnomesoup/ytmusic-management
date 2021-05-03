from os import sep
from ytmusicapi import YTMusic
from datetime import timedelta, datetime
import pickle
import re
from time import time, sleep
from secretsFile import mongoString, homeassistantToken, homeassistantUrl
from pymongo import MongoClient
from requests import get

def GetLatestHistory(updatedHistory, history, scrobblerUser):
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
            if newHistory[i]['videoId'] == history[currentIndex]['videoId']:
                if currentId != lastId:
                    # print(i, newHistory[i]['title'],
                    #       "==",
                    #       history[currentIndex]['title'])
                    currentIndex = currentIndex + 1
                    lastId = currentId
                    break
            else:
                matchStartIndex = i + 1
                # print(i, newHistory[i]['title'],
                #       "!=",
                #       history[currentIndex]['title'])
    regex = re.compile(r"(?P<minutes>\d+):(?P<seconds>\d+)")
    now = datetime.now()
    songDurations = timedelta(seconds=0)
    postCount = 0
    newRequests = []
    try:
        homeassistantResult = get(homeassistantUrl\
            + "/api/states/person.michael",
                    headers={
                        "Authorization": "Bearer " + homeassistantToken,
                        "Content-Type": "application/json"
                    })
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

ytmusic = YTMusic("headers_auth.json")
mongoClient = MongoClient(mongoString)
db = mongoClient['scrobble']
scrobblerId = '607f962eeafb5500062a4a68'
scrobblerUser = "michael"
queuedRequests = []
requestAttempts = 0

print("ytmusicScrobble to MongoDB")

while True:
    history = {}
    updatedHistory = {}
    

    try:
        # with open("ytmusicHistory.p", "rb") as file:
        #     history = pickle.load(file)
        scrobblerInfo = db['scrobblers'].find_one(
            {
                "name": "ytmusic history scrobbler",
                "user": scrobblerUser
            })
        print(scrobblerInfo)
        history = scrobblerInfo['videoIds']
        print("history=", history)
        exit()
    except:
        print("Initializing data")

    if history:
        try:
            requestsReady = False
            setVariables = {}
            while not requestsReady:
                updatedHistory = ytmusic.get_history()
                updatedHistory, newRequests = GetLatestHistory(
                                                            updatedHistory,
                                                            history,
                                                            scrobblerUser
                                                            )
                if len(newRequests) > 2 and requestAttempts < 4:
                    print(datetime.now().isoformat())
                    # print("<<< Too many requests! DUMP")
                    print("Too many requests!")
                    print("history:", len(history))
                    # print([x['videoId'] for x in history])
                    print("updatedHistory:", len(updatedHistory))
                    # print([x['videoId'] for x in updatedHistory])
                    # print("end DUMP >>>")
                    requestAttempts = requestAttempts + 1
                    print("requestAttempt:", requestAttempts)
                else:
                    requestAttempts = 0
                    requestsReady = True
            if requestsReady:
                if queuedRequests:
                    queuedRequests = queuedRequests + newRequests
                else:
                    queuedRequests = newRequests
                if queuedRequests:
                    print("Queued requests:", len(queuedRequests))
                    queuedRequests = [request for request in queuedRequests\
                        if not PostScrobble(db['songs'], request)]
                if updatedHistory:
                    # with open("ytmusicHistory.p", "wb") as file:
                    #     pickle.dump(updatedHistory, file)
                    videoIds = [item['videoId'] for item in updatedHistory]
                    setVariables["videoIds"] = videoIds
            setVariables["lastUpdate"] = datetime.utcnow()
            results = db['scrobblers'].update_one(
                {
                    "name": "ytmusic history scrobbler",
                    "user": scrobblerUser
                },
                {
                    "$set": setVariables
                }
            )
            # print(results.modified_count)
        except Exception as e:
            print("While loop error:", e)
    sleep(60.0 - (time() % 60.0))