import requests
from ytmusicapi import YTMusic
from ytmusicFunctions import getSongVideoIds

date = "2021-01-29"
url = "http://wklq.tunegenie.com/api/v1/brand/nowplaying/?" +\
    "hour=0&since=" +\
    date + "T00%3A00%3A00-05%3A00&until=" +\
    date + "T23%3A59%3A59-05%3A00"
headers = {
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "http://wklq.tunegenie.com/onair/" + date + "/",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9,fil;q=0.8"
}

r = requests.get(url, headers=headers)
rJson = r.json()
songList = rJson['response']

ytmusic = YTMusic("headers_auth.json")
playlistTitle = "WKLQ Playlist from " + date
playlistDescription = ""
playlistPrivacyStatus = "PUBLIC"

songsToAdd = []
for song in songList:
    searchTerm = (song['artist'] + " " + song['song'])
    songsToAdd.append(searchTerm)

videoResults = getSongVideoIds(ytmusic, songsToAdd)

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoResults['videoIds'])

print("playlistId:", newPlaylist)
print("Found", videoResults['searchCount'], "songs")
print(videoResults['uniqueCount'], "songs were unique")
print("YTMusic matched", videoResults['matchedCount'], "songs")