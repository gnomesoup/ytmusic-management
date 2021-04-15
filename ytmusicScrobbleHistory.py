from os import sep
from ytmusicapi import YTMusic
from datetime import timedelta, datetime
import pickle
import re
from time import time, sleep
from requests import post
from secretsFile import malojaKey

def GetLatestHistory(updatedHistory, history, queuedRequests):
    '''
    Compare the latest YouTube Music history with a previously pulled
    dictionary of history.
    '''

    newHistory = []
    for song in updatedHistory:
        artists = [artist['name'] for artist in song['artists']]
        if song['played'] in ["Today"]:
        # if song['played'] in ["Today", "Yesterday"]:
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
    if not queuedRequests:
        queuedRequests = []
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
        queuedRequests.append(requestData)

    return newHistory, queuedRequests

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

while True:
    history = {}
    updatedHistory = {}
    for item in ytmusic.get_watch_playlist():
        print(item)
    # try:
    #     with open("ytmusicHistory.p", "rb") as file:
    #         history = pickle.load(file)
    # except:
    #     print("Initializing data")

    # if history:
    #     try:
    #         updatedHistory = ytmusic.get_history()
    #         updatedHistory, queuedRequests = GetLatestHistory(
    #                                                     updatedHistory,
    #                                                     history,
    #                                                     queuedRequests
    #                                                     )
    #         if queuedRequests:
    #             if len(queuedRequests) > 3:
    #                 print("<<< Too many requests! DUMP")
    #                 print("history:")
    #                 print(history)
    #                 print("updatedHistory")
    #                 print(updatedHistory)
    #                 print("end DUMP >>>")
    #             print("Queued requests:", len(queuedRequests))
    #             queuedRequests = [request for request in queuedRequests\
    #                 if not PostScrobble(scrobblerURL, request)]
    #         if updatedHistory:
    #             with open("ytmusicHistory.p", "wb") as file:
    #                 pickle.dump(updatedHistory, file)
    #     except Exception as e:
    #         print(e)

    sleep(60.0 - (time() % 60.0))