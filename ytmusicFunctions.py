from enum import Enum
from scrobbleFunctions import GetSongId
from pymongo.database import Database
from pymongo.mongo_client import MongoClient
from requests import get
from lxml import html
from datetime import date, datetime, timedelta
import re
from ytmusicapi import YTMusic
from ytmusicapi.parsers import watch

def GetDetailedSongData(ytmusic:YTMusic, videoId:str) -> dict:
    songData = None
    watchPlaylist = ytmusic.get_watch_playlist(videoId)
    if watchPlaylist:
        songData = watchPlaylist['tracks'][0]
    return songData

class LikeStatus(Enum):
    LIKE = 1
    DISLIKE = -1 
    INDIFFERENT = 0

def GetLikeStatus(
    ytmusic:YTMusic,
    videoId:str,
    browseId:str=None,
    db:Database=None,
    verbose:bool=False
) -> LikeStatus:
    likeStatus = None
    try:
        if db:
            songDocument = db['songs'].find_one(
                {"ytmusicId": videoId},
                projection={"likeStatus": 1}
            )
            if "likeStatus" in songDocument:
                likeStatus = LikeStatus(songDocument['likeStatus'])
                if verbose:
                    print(f"GetLikeStatus: Scrobble likeStatus {likeStatus}")
        if likeStatus is None:
            if browseId is None:
                songData = GetDetailedSongData(ytmusic, videoId)
                if "album" in songData:
                    browseId = songData['album']['id']
                elif "likeStatus" in songData:
                    likeStatus = LikeStatus[songData['likeStatus']]
                    if verbose:
                        print(f"GetLikeStatus: YTMusic likeStatus {likeStatus}")
            if browseId:
                albumData = ytmusic.get_album(browseId)
                tracks = [
                    track for track in albumData['tracks']
                    if track['videoId'] == videoId
                ]
                likeStatus = LikeStatus[tracks[0]['likeStatus']]
            if db and likeStatus:
                result = db['songs'].find_one_and_update(
                    {"ytmusicId": videoId},
                    {"$set": {"likeStatus": likeStatus.value}}
                )
                if verbose:
                    if result: 
                        print(
                            f"GetLikeStatus: Updated song {result['_id']}"
                            f" like status"
                        )
                    else:
                        print(
                            f"GetLikeStatus: Could not update song. Not found."
                        )
    except Exception as e:
        if verbose:
            print("GetLikeStatus Error: ", e)
        return
    return likeStatus

def GetSongVideoId(
    ytmusic:YTMusic,
    songSearchString:str,
    db:Database=None,
    verbose:bool=False
) -> list[str, str, str]:
    if not songSearchString:
        if verbose:
            print(
                f"GetSongVideoId: Search string is empty. {songSearchString=}"
            )
        return
    if verbose:
        print("Search Term:", songSearchString)
    searchStringLower = songSearchString.lower()
    videoId = None
    browseId = None
    songId = None
    if db:
        songDocument = db['songs'].find_one(
            {"searchString": {"$regex": searchStringLower, "$options": "i"}},
            projection={"ytmusicId": 1}
        ) 
        if songDocument:
            if "ytmusicId" in songDocument:
                videoId = songDocument['ytmusicId']
            songId = songDocument['_id']
            if verbose:
                print(f"    Scrobble result: {videoId}")
    if videoId is None:
        ytmSearch = ytmusic.search(searchStringLower, "songs")
        if not ytmSearch:
            if verbose:
                print("   YTMusic result: Not found\n")
            return
        else:
            firstSong = ytmSearch[0]
            videoId = firstSong['videoId']
            browseId = firstSong['album']['id']
            if verbose:
                print(f"    YTMusic result: {videoId}")
        if db:
            songId = GetSongId(ytmusic, db, videoId)
            result = db['songs'].find_one_and_update(
                {"_id": songId},
                {"$push": {"searchString": searchStringLower}}
            )
            if result:
                print(f"    Scrobble: Added search string to {songId}")
            else:
                print(f"    Scrobble: Error adding search string to {songId}")
    return videoId, browseId, songId

def GetSongVideoIds(
    ytmSession:YTMusic,
    SongNameArtistList:list,
    RemoveDuplicates:bool=True,
    ExcludeDislike:bool=True,
    CollectPrimaryYear:bool=False,
    Verbose:bool=False,
    mongodb=None
):
    if not SongNameArtistList:
        return
    
    songList = []
    years = {}
    if RemoveDuplicates:
        for song in SongNameArtistList:
            if song not in songList:
                songList.append(song)
    else:
        songList = SongNameArtistList
    
    videoIds = []
    for song in songList:
        videoId = None
        likeStatus = None
        year = None
        if "john c mellencamp" in song.lower():
            song = song.lower().replace("john c mellencamp", "john mellencamp")
        if mongodb:
            songDocument = mongodb.songs.find_one(
                {"searchStrings": song},
                projection={"ytmusicId": 1, "likeStatus": 1, "year": 1}
            )
            if songDocument:
                videoId = songDocument['ytmusicId']
                if "likeStatus" in songDocument:
                    likeStatus = "DISLIKE" if songDocument['likeStatus'] < 0\
                        else "INDIFFERENT"
                if "year" in songDocument:
                    year = songDocument['year']
        if not videoId:
            songSearch = ytmSession.search(song, "songs")
            if Verbose:
                print("Search Term:", song)
            if not songSearch:
                if Verbose:
                    print("   Returned: No results found\n")
                continue
            else:
                firstSong = songSearch[0]
                videoId = firstSong['videoId']
        if CollectPrimaryYear:
            if year is None:
                songInfo = GetDetailedSongData(ytmSession)
                if "year" in songInfo:
                    year = songInfo["year"]
                if year in years:
                    years[year] = years[year] + 1
                else:
                    years[year] = 1
        if ExcludeDislike and likeStatus is None:
            likeStatus = GetLikeStatus(ytmSession, videoId)
        else:
            likeStatus = "INDIFFERENT"
        if likeStatus != "DISLIKE":
            videoIds.append(videoId)
            if Verbose:
                print("   Returned:", firstSong['artists'][0]['name'],\
                    "-", firstSong['title'], "\n")
        elif Verbose:
            print("    Dislike: Song will not be included in playlist\n")
        if mongodb:
            songDocument = mongodb.songs.find_one_and_update(
                {"ytmusicId": videoId},
                {"$push": {"searchStrings": song}}
            )
            if songDocument is None:
                documentData = {
                        "title": firstSong['title'],
                        "artists": [
                            artist['name']
                            for artist in firstSong['artists']
                        ],
                        "ytmusicId": videoId,
                        "searchStrings": [song],
                    }
                if "album" in firstSong:
                    documentData['album'] = firstSong['album']['name']
                mongodb.songs.insert_one(documentData)

    if CollectPrimaryYear:
        primaryYear = max(years, key=lambda k: years[k])
    else:
        primaryYear = None

    return {"videoIds":videoIds,
            "searchCount": len(SongNameArtistList),
            "uniqueCount": len(songList),
            "matchedCount": len(videoIds),
            "primaryYear": primaryYear}

def UpdatePlaylist(
    ytmusic,
    playlistId,
    videoResults,
    description=None,
    excludeDisliked=True,
    clearPlaylist=True
):
    try:
        currentSongCount = ytmusic.get_playlist(
            playlistId, limit=1
        )["trackCount"]
    except Exception as e:
        return e

    if currentSongCount > 0 and clearPlaylist:
        currentPlaylist = ytmusic.get_playlist(
            playlistId, limit=currentSongCount
        )
        ytmusic.remove_playlist_items(
            playlistId, currentPlaylist['tracks']
        )

    addedVideos = False
    for videoId in videoResults['videoIds']:
        status = ytmusic.add_playlist_items(
            playlistId, videoIds=[videoId]
        )
        if status['status'] == "STATUS_SUCCEEDED":
            addedVideos = True
        else:
            print(status)

    if addedVideos:
        if description is None:
            nowFormatted = datetime.now().strftime(
                "%Y-%m-%d at %H:%M"
            )
            description = (
                f"Last updated {nowFormatted}.\nStation played "
                f"{videoResults['searchCount']} songs.\n"
                f"{videoResults['uniqueCount']} songs were unique.\n"
                f"YTMusic match {videoResults['matchedCount']} songs."
            )
            if excludeDisliked:
                description = (
                    f"{description}\n\nNote: Songs I've marked as "
                    f"\"dislike\" were not included in the playlist."
                )
        ytmusic.edit_playlist(playlistId, description=description)
        return True
    else:
        print("There was an error adding songs to the playlist.")
        return False

def UpdateWXRTYesterday(ytmusic, playlistId):
    """
    Collect playlist data on WXRT from yesterday and import it to
    a YouTube Music playlist. Returns true if successful. Returns
    False if playlist could not be updated.
    """

    yesterday = date.today() - timedelta(days=1)
    yesterdayFormatted = "{dt.month}%2F{dt.day}%2F{dt.year}" \
        .format(dt = yesterday)

    url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
        + yesterdayFormatted

    page = get(url)
    doc = html.fromstring(page.content)
    trs = doc.xpath('//tr')

    songsToAdd = []
    for tr in trs[5:]:
        if len(tr) == 6:
            songsToAdd.append(tr[2].text_content().lower() + " " + tr[4].text_content().lower())

    songsToAdd.reverse()
    videoResults = GetSongVideoIds(ytmusic, songsToAdd)

    return UpdatePlaylist(ytmusic, playlistId, videoResults)

def CreateWXRTFlashback(ytmusic, playlistDate=None):
    if playlistDate is None:
        today = datetime.now() - timedelta(hours=12)
    else:
        today = playlistDate
    lastSaturday = today - timedelta(days=(7 - (5 - today.weekday())) % 7)
    lastSaturdayFormatted = "{dt.month}%2F{dt.day}%2F{dt.year}".format(dt = lastSaturday)

    url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
    + lastSaturdayFormatted

    page = get(url)
    doc = html.fromstring(page.content)
    trs = doc.xpath('//tr')

    songList = []
    for tr in reversed(trs[5:]):
        if len(tr) == 6:
            songList.append(
                [tr[0].text_content(), tr[2].text_content().lower() +
                " " + tr[4].text_content().lower()]
            )

    songsToAdd = []
    for song in songList:
        if re.match("(9|10|11):\d\d\sAM",song[0]):
            songsToAdd.append(song[1])
    
    searchResults = GetSongVideoIds(
        ytmusic, songsToAdd,
        ExcludeDislike=False,
        CollectPrimaryYear=True
    )

    playlistYear = searchResults['primaryYear']
    playlistTitle = f"WXRT Saturday Morning Flashback {playlistYear}"
    playlistDescription = "Air date " + lastSaturday.strftime("%Y-%m-%d")
    newPlaylist = ytmusic.create_playlist(
        playlistTitle,
        description="",
        privacy_status="PUBLIC"
    )
    return UpdatePlaylist(
        ytmusic,
        newPlaylist,
        searchResults,
        description=playlistDescription
    )

def UpdateCKPKYesterday(ytmusic, playlistId):
    """
    Collect playlist data on CKPK from yesterday and import it to
    a YouTube Music playlist. Returns true if successful. Returns
    False if playlist could not be updated.
    """
    url = "https://www.thepeak.fm/api/v1/music/broadcastHistory?day=-1&playerID=757"
    headers = {
        "Host": "www.thepeak.fm",
        "Connection": "keep-alive",
        "sec-ch-ua": "\"Google Chrome\";v=\"89\", \"Chromium\";v=\"89\", \";Not A Brand\";v=\"99\"",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.thepeak.fm/recentlyplayed/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,fil;q=0.8",
        "Cookie": "SERVERID=v1; _gcl_au=1.1.152033816.1616085086; _gid=GA1.2.1046217361.1616085087; _ga_L8XJ1TXSJ7=GS1.1.1616085086.1.0.1616085086.0; _ga=GA1.1.341213110.1616085087; __atuvc=1%7C11; __atuvs=6053805e328b1b57000; __atssc=google%3B1; PHPSESSID=8b88a5b0a76043cb13a2943e82bdcb62; sc_device_id=web%3Ac8c07bc4-4fee-4a92-a41b-d4e21ea85fbf; _fbp=fb.1.1616085087326.385418690"
    }

    r = get(url, headers=headers)
    rJson = r.json()
    songList = rJson['data']['scrobbles']

    songsToAdd = []
    for song in songList:
        searchTerm = (song['artist_name'] + " " + song['song_name'])
        songsToAdd.append(searchTerm)
    
    videoResults = GetSongVideoIds(ytmusic, songsToAdd)

    return UpdatePlaylist(ytmusic, playlistId, videoResults)
