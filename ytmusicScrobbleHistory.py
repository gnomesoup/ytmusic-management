from os import sep
from requests.api import request
from ytmusicapi import YTMusic
from datetime import timedelta, datetime
import pickle
import re
from time import time, sleep
from requests import post
from secretsFile import malojaKey

def GetLatestHistory(updatedHistory, history):
    '''
    Compare the latest YouTube Music history with a previously pulled
    dictionary of history.
    '''

    newHistory = []
    for song in updatedHistory:
        artists = [artist['name'] for artist in song['artists']]
        # if song['played'] in ["Today"]:
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
    for song in reversed(newHistory[0:matchStartIndex]):
        # matches = regex.match(song['duration'])
        # if matches:
        #     matchesDictionary = matches.groupdict()
        #     time_params = {}
        #     for (name, param) in matchesDictionary.items():
        #         if param:
        #             time_params[name] = int(param)
        #     songDurations = songDurations + timedelta(**time_params)
        requestData = {
            "artists": song['artists'],
            "title": song['title'],
            "key": malojaKey,
            "album": song['album'],
            "time": int(datetime.now().timestamp())
            # "time": int(datetime.utcnow().timestamp())
            }
        newRequests.append(requestData)

    return newHistory, newRequests

def PostScrobble(url, request):
    # result = post(
    #         url,
    #         json=request
    # )
    if True:
    # if result.status_code == 200:
        print(request['artists'], request['title'])
        return True
    else:
        print("Error posting scrobble", result)
        print("Queueing for next run")
        return False

ytmusic = YTMusic("headers_auth.json")
scrobblerURL = "https://maloja.mmjo.com/apis/mlj_1/newscrobble"
queuedRequests = []
requestAttempts = 0

while True:
    history = {}
    updatedHistory = {}

    try:
        with open("ytmusicHistory.p", "rb") as file:
            history = pickle.load(file)
    except:
        print("Initializing data")

    if history:
        try:
            updatedHistory = ytmusic.get_history()
            updatedHistory, newRequests = GetLatestHistory(
                                                        updatedHistory,
                                                        history
                                                        )
            if len(newRequests) > 2 and requestAttempts < 3:
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
                if queuedRequests:
                    queuedRequests = queuedRequests + newRequests
                else:
                    queuedRequests = newRequests
                if queuedRequests:
                    print("Queued requests:", len(queuedRequests))
                    queuedRequests = [request for request in queuedRequests\
                        if not PostScrobble(scrobblerURL, request)]
                if updatedHistory:
                    with open("ytmusicHistory.p", "wb") as file:
                        pickle.dump(updatedHistory, file)
        except Exception as e:
            print("While loop error:", e)

    sleep(60.0 - (time() % 60.0))