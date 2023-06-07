from ytmusicapi import YTMusic
from datetime import datetime
from time import time, sleep
from secretsFile import mongoString, homeassistantToken, homeassistantUrl
from pymongo import MongoClient
from scrobbleFunctions import GetLatestHistory, GetLocationFromHomeAssistant, \
    PostScrobble

ytmusic = YTMusic("oauth.json")
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
    setVariables = {}

    try:
        scrobblerInfo = db['scrobblers'].find_one(
            {
                "name": "ytmusic history scrobbler",
                "user": scrobblerUser
            })
        history = scrobblerInfo['videoIds']
    except:
        print("Initializing data")

    if not history:
        updatedHistory = ytmusic.get_history()
        setVariables[videoIds] = [item['videoId'] for item in updatedHistory]

    else:
        try:
            requestsReady = False
            while not requestsReady:
                updatedHistory = ytmusic.get_history()
                updatedHistory, newRequests = GetLatestHistory(
                    updatedHistory,
                    history,
                    scrobblerUser,
                    GetLocationFromHomeAssistant(
                        homeassistantUrl,
                        homeassistantToken,
                        "person.michael"
                    )
                )
                if len(newRequests) > 2 and requestAttempts < 4:
                    print(datetime.now().isoformat())
                    # print("<<< Too many requests! DUMP")
                    print("Too many requests!")
                    print("history:", len(history))
                    # print([x['videoId'] for x in history])
                    print("updatedHistory:", len(updatedHistory))
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
                        if not PostScrobble(db['scrobbles'], request)]
                if updatedHistory:
                    videoIds = [item['videoId'] for item in updatedHistory]
                    setVariables["videoIds"] = videoIds
            # print(results.modified_count)
        except Exception as e:
            print("While loop error:", e)

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
    sleep(60.0 - (time() % 60.0))