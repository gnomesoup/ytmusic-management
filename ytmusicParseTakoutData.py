import json
from os import name
import re
from ytmusicFunctions import GetDetailedSongData, GetSongId
from ytmusicapi import YTMusic
from datetime import datetime, timezone
from dateutil import parser
from secretsFile import malojaKey, malojaURL, mongoString
from requests import post
import pickle
from pymongo import MongoClient
header = """
POST /youtubei/v1/account/account_menu?alt=json&key=AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30 HTTP/1.1
Host: music.youtube.com
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0
Accept: */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Content-Type: application/json
X-Goog-Visitor-Id: CgtjSEx1VDNwZEF4TSjP9fyHBg%3D%3D
Authorization: SAPISIDHASH 1627339473_0079459e4304c47a5d2d7635623efb50cbdab87d
X-Goog-AuthUser: 0
X-Goog-PageId: undefined
x-origin: https://music.youtube.com
X-YouTube-Client-Name: 67
X-YouTube-Client-Version: 1.20210721.00.00
X-YouTube-Device: cbr=Firefox&cbrand=apple&cbrver=89.0&ceng=Gecko&cengver=89.0&cos=Macintosh&cosver=10.15&cplatform=DESKTOP&cyear=2013
X-Youtube-Identity-Token: QUFFLUhqbERVWm9MZUxHeEJOQ3VTeEliallJYTdQU0szQXw=
X-YouTube-Page-CL: 385780629
X-YouTube-Page-Label: youtube.music.web.client_20210721_00_RC00
X-YouTube-Utc-Offset: -300
X-YouTube-Time-Zone: America/Chicago
X-YouTube-Ad-Signals: dt=1627339472315&flash=0&frm&u_tz=-300&u_his=5&u_java&u_h=1440&u_w=2560&u_ah=1337&u_aw=2560&u_cd=24&u_nplug&u_nmime&bc=31&bih=592&biw=1897&brdim=510%2C23%2C510%2C23%2C2560%2C23%2C1897%2C1330%2C1897%2C592&vis=1&wgl=true&ca_type=image
Content-Length: 845
Origin: https://music.youtube.com
DNT: 1
Connection: keep-alive
Referer: https://music.youtube.com/
Cookie: YSC=60p7UmHUx70; VISITOR_INFO1_LIVE=cHLuT3pdAxM; _gcl_au=1.1.1858949286.1627339359; PREF=volume=100; SID=AAg_1LGBInDfPuV4ARaUDqtsF5G-NzBjj8SeAoWrwz5cC9ZgvmpPLK6qSNR6u1xrxlRzRQ.; __Secure-1PSID=AAg_1LGBInDfPuV4ARaUDqtsF5G-NzBjj8SeAoWrwz5cC9ZgUTUVfAomkO5on5txZfusog.; __Secure-3PSID=AAg_1LGBInDfPuV4ARaUDqtsF5G-NzBjj8SeAoWrwz5cC9ZgbPs2vxlq02viYUkdi6ntzg.; HSID=AnjLV-I3fleSdIloP; SSID=AMrgj852cSxHFPIgv; APISID=przvSJ3kHQplS2OA/Aehlh3JhDg7n4LbV0; SAPISID=LH4BGv3GREpZM6cP/AcGi5mWVL0GehQ5Tr; __Secure-1PAPISID=LH4BGv3GREpZM6cP/AcGi5mWVL0GehQ5Tr; __Secure-3PAPISID=LH4BGv3GREpZM6cP/AcGi5mWVL0GehQ5Tr; LOGIN_INFO=AFmmF2swRQIgczb_T-1eb74i5pfajYLo3PsfNrqGW6pREdxq0JNzUV8CIQCvpxX1DXgJS8ArKLEnC9fyK4sWmnYm9bCDP7wPGZrUbg:QUQ3MjNmeVRWSWxGMWR0U0J4emVYMFRaSzVPTmYxTDBhTi1tWDdIa1BrYkFHOUE4MVZBNVp6d08wZjdyUWNIbTBwLUJMbFV6eXM2bkNTUXFjZ3VSN3M1M1RFU3Y2dmpfRHkydlBUWDVtb2QxUnZlSlRPbkdhWV9LNkhsQzVSazhaYnpmaDlOSEFpcFJOUXlKNFVJVTBIVGZSdzl6dDMyNXJB; SIDCC=AJi4QfEYenGAKwrt9RsfqFabIHuiZfGYRu4wAV2cRgg7etuHBW_UtZC7PFeMIoQIwmFmhLNB; __Secure-3PSIDCC=AJi4QfHt3dS5Q1eh8_IIgjCKpQRGvedh4oE6ymzLKW1rDRguR3hJo1AFytyLASqn-3eMlvGWlw
Cache-Control: max-age=0
"""
# YTMusic.setup("headers_auth.json", headers_raw=header)

def parseTakeoutItem(item:dict) -> dict:
    # try:
    outDict = {}
    outDict["time"] = parser.parse(item["time"])
    titleUrl = item["titleUrl"]
    regexString = re.compile(r"\?v=(.*)$")
    result = regexString.search(titleUrl)
    outDict["videoId"] = result.group(1)
    return outDict

def songDocumentfromYTMusicData(ytMusic:YTMusic, takeoutData:dict) -> dict:
    outDict = {}
    song = GetDetailedSongData(ytMusic, takeoutData['videoId'])
    outDict["time"] = takeoutData['time']
    outDict["title"] = song["title"]
    outDict["artists"] = [artist for artist in song["artists"]]
    outDict["source"] = "YouTube Music"
    outDict["user"] = "michael"
    outDict["videoId"] = song["videoId"]
    return outDict

def PostScrobble(dbCollection, request):
    if request is not None:
        request['songId'] = GetSongId(ytmusic, db=db, videoId=request['videoId'])
        dbCollection.insert_one(request)
        return True
    else:
        print("Error posting scrobble", result)
        print("Queueing for next run")
        return False

takeoutFilePath = "/Users/mpfammatter/Downloads/Takeout/"\
    + "YouTube and YouTube Music/history/watch-history.json"

ytmusic = YTMusic("headers_auth.json")
mongoClient = MongoClient(mongoString)
db = mongoClient['scrobble']
# test = {"name": "test name", "artists": ["artist1", "artist2"],
#         "album": "test album",
#         "time": datetime.utcnow(), "user": "michael"}
# db['scrobbles'].insert_one(test,)

# with open(takeoutFilePath) as takeoutFile:
#     allTakeoutData = json.load(takeoutFile)

# print("allTakeoutData count:", len(allTakeoutData))
# currentData = [item for item in allTakeoutData\
#     if (parser.parse(item['time']) > parser.parse("2021-07-24T00:00:00.000Z"))]
# print("currentData:", len(currentData))


# takeoutData = [parseTakeoutItem(item) for item in currentData
#                if (item["header"] == "YouTube Music" and "titleUrl" in item)]
            
# with open("takeoutData.p", "wb") as file:
#     pickle.dump(takeoutData, file)
with open("takeoutData.p", "rb") as file:
    takeoutData = pickle.load(file)

print("ytmusic count:", len(takeoutData))

# songDocuments = [
#     songDocumentfromYTMusicData(ytmusic, takeout) for takeout in takeoutData
# ]
# with open("songDocuments.p", "wb") as file:
#     pickle.dump(songDocuments, file)
with open("songDocuments.p", "rb") as file:
    songDocuments = pickle.load(file)

print("ytmusic count:", len(songDocuments))

while songDocuments:
    songDocuments = [request for request in songDocuments\
                    if not PostScrobble(db['scrobbles'], request)]