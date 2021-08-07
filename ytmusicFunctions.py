from enum import Enum
from bson.objectid import ObjectId
from pymongo.database import Database
from datetime import datetime
import re
from ytmusicapi import YTMusic

def GetDetailedSongData(ytmusic:YTMusic, videoId:str) -> dict:
    songData = None
    watchPlaylist = ytmusic.get_watch_playlist(videoId)
    if watchPlaylist:
        songData = watchPlaylist['tracks'][0]
    return songData

def GetSongId(ytmusic:YTMusic, db:Database, videoId:str) -> ObjectId:
    try:
        songDocument = db['songs'].find_one(
            {"ytmusicId": videoId},
            {"ytmusicId": 1}
        )
        if songDocument is None:
            watchPlaylist = ytmusic.get_watch_playlist(videoId)
            browseId = None
            songInfo = watchPlaylist['tracks'][0]
            documentData = {
                    "title": songInfo['title'],
                    "artists": [
                        artist['name'] for artist in songInfo['artists']
                    ],
                    "ytmusicId": songInfo['videoId']
                }
            if "album" in songInfo:
                documentData['album'] = songInfo['album']['name']
                browseId = songInfo['album']['id']
            likeStatus = GetLikeStatus(ytmusic, videoId, browseId, db)
            if likeStatus:
                documentData['likeStatus'] = likeStatus.value
            result = db['songs'].insert_one(documentData)
            songId = result.inserted_id
        else:
            songId = songDocument['_id']
        return songId
    except Exception as e:
        print(f"GetSongId Error: {e}")
        return None

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
):
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
            {
                "searchString": {
                    "$regex": re.escape(searchStringLower),
                    "$options": "i"
                }
            },
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
    db=None
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
        if db:
            songDocument = db.songs.find_one(
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
        if db:
            songDocument = db.songs.find_one_and_update(
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
                db.songs.insert_one(documentData)

    if CollectPrimaryYear:
        primaryYear = max(years, key=lambda k: years[k])
    else:
        primaryYear = None

    return {"videoIds":videoIds,
            "searchCount": len(SongNameArtistList),
            "uniqueCount": len(songList),
            "matchedCount": len(videoIds),
            "primaryYear": primaryYear}

def GetPlaylistTrackCount(ytmusic:YTMusic, playlistId:str) -> int:
    currentPlaylist = ytmusic.get_playlist(playlistId, limit=10)
    if "trackCount" in currentPlaylist:
        return currentPlaylist['trackCount']
    else:
        return False

def ClearPlaylist(ytmusic:YTMusic, playlistId:str) -> str:
    trackCount = GetPlaylistTrackCount(ytmusic, playlistId=playlistId)
    if trackCount and trackCount > 0:
        currentPlaylist = ytmusic.get_playlist(playlistId, limit=trackCount)
        return ytmusic.remove_playlist_items(
            playlistId, currentPlaylist['tracks']
        )
    else:
        return

def AddToPlaylist(
    ytmusic:YTMusic, playlistId:str, videoId:str, duplicates:bool=False
) -> bool:
    status = ytmusic.add_playlist_items(
        playlistId, videoIds=[videoId], duplicates=duplicates
    )
    if status['status'] == "STATUS_SUCCEEDED":
        return True
    else:
        print(f"AddtoPlaylist Error: Could not add {videoId}")
        return False

def YesterdayPlaylistsUpdate(
    ytmusic:YTMusic, db:Database, playlistId:str, SongArtistSearch:list
) -> None:
    originalSongCount = len(SongArtistSearch)
    uniqueSongs = list(dict.fromkeys(SongArtistSearch))

    videoIds = []
    for song in uniqueSongs:
        videoId, browseId, songId = GetSongVideoId(
            ytmusic, song, db=db
        )
        if GetLikeStatus(
            ytmusic, videoId, browseId, db
        ) is not LikeStatus.DISLIKE:
            videoIds.append(videoId)
    ClearPlaylist(ytmusic, playlistId)
    results = [
        AddToPlaylist(ytmusic, playlistId, videoId) 
        for videoId in videoIds
    ]
    YesterdayPlaylistsDescription(
        ytmusic,
        playlistId,
        originalSongCount,
        len(uniqueSongs),
        sum(results)
    )
    if GetPlaylistTrackCount(ytmusic, playlistId=playlistId) == sum(results):
        return True
    else:
        return False

def YesterdayPlaylistsDescription(
    ytmusic:YTMusic,
    playlistId:str,
    searchCount:int,
    uniqueCount:int, 
    matchedCount:int
) -> str:
    nowFormatted = datetime.now().strftime(
        "%Y-%m-%d at %H:%M"
    )
    description = (
        f"Last updated {nowFormatted}.\nStation played "
        f"{searchCount} songs.\n"
        f"{uniqueCount} songs were unique.\n"
        f"YTMusic match {matchedCount} songs."
        f"\n\nNote: Songs I've marked as "
        f"\"dislike\" were not included in the playlist."
    )
    return ytmusic.edit_playlist(playlistId, description=description)

def UpdatePlaylist(
    ytmusic:YTMusic,
    playlistId:str,
    videoResults,
    description=str,
    excludeDisliked=bool,
    clearPlaylist=bool
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
