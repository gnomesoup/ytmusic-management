from ytmusicapi import YTMusic
from ytmusicFunctions import GetDetailedSongData, GetPlaylistTrackCount, UpdatePlaylist, GetSongVideoId, AddToPlaylist
from pymongo import MongoClient
import requests
from lxml import html
import re
from datetime import datetime, timedelta
from secretsFile import mongoString

def CreateWXRTFlashback(
    ytmusic, playlistDate=None, dbConnectionString:str=None
) -> bool:

    if dbConnectionString is not None:
        mongoClient = MongoClient(dbConnectionString)
        db = mongoClient['scrobble']

    if playlistDate is None:
        today = datetime.now() - timedelta(hours=12)
    else:
        today = playlistDate
    lastSaturday = today - timedelta(days=(7 - (5 - today.weekday())) % 7)
    lastSaturdayFormatted = "{dt.month}%2F{dt.day}%2F{dt.year}".format(
        dt = lastSaturday
    )

    url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
    + lastSaturdayFormatted

    page = requests.get(url)
    doc = html.fromstring(page.content)
    trs = doc.xpath('//tr')

    songList = []
    for tr in reversed(trs[5:]):
        if len(tr) == 6:
            songList.append(
                [tr[0].text_content(), tr[2].text_content().lower() +
                " " + tr[4].text_content().lower()]
            )

    songArtistSearch = []
    for song in songList:
        if re.match("(9|10|11):\d\d\sAM",song[0]):
            songArtistSearch.append(song[1])
    
    originalSongCount = len(songArtistSearch)

    years = {}
    videoIds = []
    for song in songArtistSearch:
        videoId, browseId, songId = GetSongVideoId(
            ytmusic=ytmusic, songSearchString=song, db=db
        )
        if db is not None:
            songDocument = db['songs'].find_one({"_id": songId})
        else:
            songDocument = {}
        if "year" not in songDocument:
            songDocument = GetDetailedSongData(ytmusic=ytmusic, videoId=videoId)
        if "year" in songDocument:
            year = songDocument['year']
            years[year] = 1 if year not in years else years[year] + 1
        videoIds.append(videoId)
    playlistYear = max(years, key=years.get)
    playlistTitle = f"WXRT Saturday Morning Flashback {playlistYear}"
    playlistDescription = "Air date " + lastSaturday.strftime("%Y-%m-%d")
    newPlaylist = ytmusic.create_playlist(
        playlistTitle,
        description=playlistDescription,
        privacy_status="PUBLIC"
    )
    results = [
        AddToPlaylist(
            ytmusic=ytmusic,
            playlistId=newPlaylist,
            videoId=videoId,
            duplicates=True
        ) for videoId in videoIds
    ]
    if GetPlaylistTrackCount(
        ytmusic=ytmusic,
        playlistId=newPlaylist
    ) == sum(results):
        return True
    else:
        return False
if __name__ == "__main__":
    print("Creating WXRT Saturday Morning Flashback Playlist")
    ytmusic = YTMusic("headers_auth.json")

    if CreateWXRTFlashback(ytmusic, dbConnectionString=mongoString):
        print("Playlist created successfully")
    else:
        print("Error creating playlist")