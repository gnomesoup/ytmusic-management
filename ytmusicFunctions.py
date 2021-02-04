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

def getSongVideoIds(ytmSession, SongNameArtistList, RemoveDuplicates = True):
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
        print("Search Term:", song)
        if not songSearch:
            print("   Returned: No results found\n")
        else:
            firstSong = songSearch[0]
            videoId = firstSong['videoId']
            likeStatus = getLikeStatus(ytmSession, firstSong)
            if likeStatus != "DISLIKE":
                videoIds.append(videoId)
                print("   Returned:", firstSong['artists'][0]['name'],\
                      "-", firstSong['title'], "\n")
            else:
                print("    Dislike: Song will not be included in playlist\n")

    return {"videoIds":videoIds,
            "searchCount": len(SongNameArtistList),
            "uniqueCount": len(songList),
            "matchedCount": len(videoIds)}  