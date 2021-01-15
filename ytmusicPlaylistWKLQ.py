# from requests import Request, Session
import requests
import lxml.html
# import pandas
from ytmusicapi import YTMusic

date = "2021-01-14"
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

page = requests.get(url)
doc = lxml.html.fromstring(page.content)
lis = doc.xpath('//li[contains(@class, "slot lt")]')

songsToAdd = []
for song in songList:
    searchTerm = (song['artist'] + " " + song['song'])
    songsToAdd.append(searchTerm)

uniqueSongsToAdd = list(set(songsToAdd))

videoIds = []
for song in reversed(uniqueSongsToAdd):
    songSearch = ytmusic.search(song, "songs")
    print("Search Term:", song)
    if not songSearch:
        print("Return: None\n")
    else:
        firstSong = songSearch[0]
        videoIds.append(firstSong['videoId'])
        print("Return:", firstSong['artists'][0]['name'], "-", firstSong['title'], "\n")

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print(newPlaylist)