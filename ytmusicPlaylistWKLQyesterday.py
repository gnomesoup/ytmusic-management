from ytmusicapi import YTMusic
from pymongo import MongoClient
from secretsFile import mongoString
from datetime import date, timedelta
from ytmusicFunctions import GetSongVideoId, UpdatePlaylist

def UpdateWKLQYesterday(
    ytmusic: YTMusic, playlistId:str, mongodb:MongoClient=None
):
    # Get data from the internet
    searchDate = date.today() - timedelta(days=1)
    searchDate = searchDate.strftime("%Y-%m-%d")
    url = "http://wklq.tunegenie.com/api/v1/brand/nowplaying/?" +\
        "hour=0&since=" +\
        searchDate + "T00%3A00%3A00-05%3A00&until=" +\
        searchDate + "T23%3A59%3A59-05%3A00"
    headers = {
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://wklq.tunegenie.com/onair/" + searchDate + "/",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,fil;q=0.8"
    }

    r = get(url, headers=headers)
    rJson = r.json()
    songList = rJson['response']

    songsToAdd = []
    for song in songList:
        searchTerm = (song['artist'] + " " + song['song'])
        songsToAdd.append(searchTerm)

    uniqueSongs = []
    uniqueSongs = [
        song for song in songsToAdd if song not in uniqueSongs
    ]

    for song in uniqueSongs:
        videoId, browseId, songId = GetSongVideoId(
            ytmusic, song, mongodb=mongodb
        )
        
    return UpdatePlaylist(ytmusic, playlistId, videoResults)

if __name__ == "__main__":

    print("Updating WKLQ Yesterday playlist")
    playlistId = "PLJpUfuX6t6dRg0mxM5fEufwZOd5eu_DmU"
    ytmusic = YTMusic("headers_auth.json")
    mongoClient = MongoClient(mongoString)
    db = mongoClient['scrobble']

    if UpdateWKLQYesterday(ytmusic, playlistId, mongodb=db):
        print("Playlist update successful")
    else:
        print("Error updating playlist")