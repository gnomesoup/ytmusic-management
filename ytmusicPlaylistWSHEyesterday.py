from datetime import date, datetime, timedelta, timezone, time, tzinfo
from requests import get, post
from pymongo import MongoClient
from secretsFile import mongoString
from ytmusicapi import YTMusic
from ytmusicFunctions import YesterdayPlaylistsUpdate

def UpdateWSHEYesterday(
    ytmusic:YTMusic, playlistId:str, dbConnectionString:str=None
) -> bool:
    """Collect playlist data on WSHE from yesterday and import it to a YouTube
    Music playlist. 

    Args:
        ytmusic (YTMusic): YouTube Music Session
        playlistId (str): YouTube music id for the playlist to be updated
        dbConnectionString (str, optional): Connection string for the Mongo
            database used for song caching to speed up searches. If no string
            is provided, all searches will happen directly on YouTube music.
            Defaults to None.

    Returns:
        bool: Returns true if successfull. Returns false if the playlist
            could not be updated.
    """
    if dbConnectionString is not None:
        mongoClient = MongoClient(dbConnectionString)
        db = mongoClient['scrobble']

    searchEndDate = datetime.combine(date.today(), time())
    searchStartDate = searchEndDate - timedelta(days=1)
    searchEndTimestamp = searchEndDate.replace(tzinfo=timezone.utc).timestamp()
    searchStartTimestamp = searchStartDate.replace(tzinfo=timezone.utc).timestamp()
    # searchDate = searchDate.strftime("%Y-%m-%d")
    url = "https://live.wshechicago.com/" \
        "wp-content/plugins/hubbard-listen-live/api/hll_cues_get.php"
    headers = {
        "Host": "live.wshechicago.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Content-Length": "32",
        "Origin": "https://live.wshechicago.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://live.wshechicago.com/listen/",
        "Cookie": "hll-video-played=true; anonymousNotificationsChecksum=999999999; anonymousSeenAllNotifications=false; hll-registration-popup=true",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
    }
    r = post(url, data='{"limit":1"}',headers=headers)
    rJson = r.json()
    songList = rJson['data']['response']
    lastTimestamp = float(rJson['data']['response'][-1]['timestamp'])
    firstSongId = rJson['data']['response'][-1]['id']
    r = post(
        url,
        data=f'{{"limit":300, "offset":"{firstSongId}"}}',
        headers=headers
    )
    rJson = r.json()
    songList = songList + rJson['data']['response']
    songsToAdd = [
        f"{song['data']['artist']} {song['data']['description']}".lower()
        for song in songList
        if searchStartTimestamp < float(song['timestamp']) < searchEndTimestamp
    ]
    return YesterdayPlaylistsUpdate(
        ytmusic=ytmusic,
        db=None,
        playlistId=playlistId,
        SongArtistSearch=songsToAdd
    )

if __name__ == "__main__":
    # https://music.youtube.com/playlist?list=PLJpUfuX6t6dTyEfFJmvVlIGzcXR1dKFt5&feature=share
    ytmusic = YTMusic("headers_auth.json")
    playlistId = "PLJpUfuX6t6dTyEfFJmvVlIGzcXR1dKFt5"
    if UpdateWSHEYesterday(
        ytmusic=ytmusic,
        playlistId=playlistId,
        dbConnectionString=mongoString,
    ):
        print("Playlist update successful")
    else:
        print("Error updating playlist")