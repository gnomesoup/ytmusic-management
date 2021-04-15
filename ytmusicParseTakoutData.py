import json
from os import name
import re
from ytmusicapi import YTMusic
from datetime import datetime, timezone
from secretsFile import malojaKey, malojaURL
from requests import post

def parseTakeoutItem(item, ytmusic):
    try:
        outDict = {}
        utc_dt = datetime.strptime(item["time"], '%Y-%m-%dT%H:%M:%S.%fZ')
        local_dt = utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
        outDict["time"] = local_dt.timestamp()
        titleUrl = item["titleUrl"]
        regexString = re.compile(r"\?v=(.*)$")
        result = regexString.search(titleUrl)
        song = ytmusic.get_song(result.group(1))
        outDict["title"] = song["title"]
        outDict["artists"] = [artist for artist in song["artists"]]
        return outDict
    except Exception as e:
        print(item['title'], e)
        return

def PostScrobble(url, request, key):
    if request is not None:
        request["key"] = key
        result = post(
                url,
                json=request
        )
    if (result.status_code == 200 or requests is None):
        return True
    else:
        print("Error posting scrobble", result)
        print("Queueing for next run")
        return False

takeoutFilePath = "/Users/mpfammatter/downloads/takeout/"\
    + "YouTube and YouTube Music/history/watch-history.json"

ytmusic = YTMusic("headers_auth.json")

tz = datetime.utcnow().astimezone().tzinfo
print(tz)

with open(takeoutFilePath) as takeoutFile:
    takeoutData = json.load(takeoutFile)

print("takeoutData count:", len(takeoutData))

ytmusicData = [parseTakeoutItem(item, ytmusic) for item in takeoutData
               if (item["header"] == "YouTube Music" and "titleUrl" in item)]
            
print("ytmusic count:", len(ytmusicData))

while ytmusicData:
    ytmusicData = [request for request in ytmusicData\
                    if not PostScrobble(malojaURL, request, malojaKey)]