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
        if "john c mellencamp" in song.lower():
            song = song.lower().replace("john c mellencamp", "john mellencamp")
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
                if "album" in firstSong:
                    albumId = firstSong['album']['id']
                    albumInfo = ytmSession.get_album(albumId)
                    if "releaseDate" in albumInfo:
                        yearReleased = albumInfo["releaseDate"]["year"]
                        if yearReleased in years:
                            years[yearReleased] = years[yearReleased] + 1
                        else:
                            years[yearReleased] = 1
            if ExcludeDislike:
                likeStatus = getLikeStatus(ytmSession, firstSong)
            else:
                likeStatus = "INDIFFERENT"
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
    
    videoResults = getSongVideoIds(ytmusic, songsToAdd)

    return UpdatePlaylist(ytmusic, playlistId, videoResults)

def UpdateWKLQYesterday(ytmusic, playlistId):
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

    videoResults = getSongVideoIds(ytmusic, songsToAdd)

    return UpdatePlaylist(ytmusic, playlistId, videoResults)