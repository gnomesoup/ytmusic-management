from requests import get
from lxml import html
from datetime import date, datetime, timedelta
import re

def getLikeStatus(ytmSession, songInfo, verbose=False):
    likeStatus = None
    try:
        album = ytmSession.get_album(songInfo['album']['id'])
        if album:
            for track in album['tracks']:
                if track['videoId'] == songInfo['videoId']:
                    likeStatus = track['likeStatus']
    except Exception as e:
        if verbose:
            print("Error getting like status:", e)
    return likeStatus

def getSongVideoIds(
    ytmSession,
    SongNameArtistList,
    RemoveDuplicates=True,
    ExcludeDislike=True,
    CollectPrimaryYear=False,
    Verbose=False
):
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
                songInfo = ytmSession.get_song(firstSong['videoId'])
                matchResult = re.search(r"^\d{4}", songInfo['release'])
                if matchResult is not None:
                    yearReleased = matchResult.group()
                    if yearReleased in years:
                        years[yearReleased] = years[yearReleased] + 1
                    else:
                        years[yearReleased] = 1
            if ExcludeDislike:
                likeStatus = "INDIFFERENT"
            else:
                likeStatus = getLikeStatus(ytmSession, firstSong)
            if likeStatus != "DISLIKE":
                videoIds.append(videoId)
                if Verbose:
                    print("   Returned:", firstSong['artists'][0]['name'],\
                        "-", firstSong['title'], "\n")
            elif Verbose:
                print("    Dislike: Song will not be included in playlist\n")

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
        if status == "STATUS_SUCCEEDED":
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
    videoResults = getSongVideoIds(ytmusic, songsToAdd)

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
    
    searchResults = getSongVideoIds(
        ytmusic, songsToAdd,
        ExcludeDislike=False,
        CollectPrimaryYear=True
    )

    playlistYear = searchResults['primaryYear']
    playlistTitle = "WXRT Saturday Morning Flashback " + playlistYear
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
