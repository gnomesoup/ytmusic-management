from ytmusicapi import YTMusic
from ytmusicFunctions import YesterdayPlaylistsUpdate
from pymongo import MongoClient
import requests
from secretsFile import mongoString

def UpdateCKPKYesterday(ytmusic, playlistId, dbConnectionString:str) -> bool:
    """
    Collect playlist data on CKPK from yesterday and import it to
    a YouTube Music playlist. Returns true if successful. Returns
    False if playlist could not be updated.
    """

    if dbConnectionString is not None:
        mongoClient = MongoClient(dbConnectionString)
        db = mongoClient['scrobble']

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

    r = requests.get(url, headers=headers)
    rJson = r.json()
    songList = rJson['data']['songs']

    songsToAdd = []
    for song in songList:
        searchTerm = (song['artist_name'] + " " + song['song_name'])
        songsToAdd.append(searchTerm)
    
    return YesterdayPlaylistsUpdate(ytmusic, db, playlistId, songsToAdd)

if __name__ == "__main__":
    playlistId = "PLJpUfuX6t6dR9DeM0gOH3rLt99Sl3SDVG"
    print("Updating CKPK Yesterday playlist")
    ytmusic = YTMusic("oauth.json")

    if UpdateCKPKYesterday(ytmusic, playlistId, mongoString):
        print("Playlist update successful")
    else:
        print("There was an error adding songs to the playlist.")