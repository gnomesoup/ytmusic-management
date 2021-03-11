def getLikeStatus(ytmSession, songInfo):
    likeStatus = None
    try:
        album = ytmSession.get_album(songInfo['album']['id'])
        if album:
            for track in album['tracks']:
                if track['videoId'] == songInfo['videoId']:
                    likeStatus = track['likeStatus']
    except Exception as e:
        print("Error getting like status:", e)
    return likeStatus

def getSongVideoIds(ytmSession, SongNameArtistList, RemoveDuplicates = True, Verbose=False):
    songList = []
    if RemoveDuplicates:
        for song in SongNameArtistList:
            if song not in songList:
                songList.append(song)
    else:
        songList = SongNameArtistList
    
    videoIds = []
    for song in songList:
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
            likeStatus = getLikeStatus(ytmSession, firstSong)
            if likeStatus != "DISLIKE":
                videoIds.append(videoId)
                if Verbose:
                    print("   Returned:", firstSong['artists'][0]['name'],\
                        "-", firstSong['title'], "\n")
            elif Verbose:
                print("    Dislike: Song will not be included in playlist\n")

    return {"videoIds":videoIds,
            "searchCount": len(SongNameArtistList),
            "uniqueCount": len(songList),
            "matchedCount": len(videoIds)}  