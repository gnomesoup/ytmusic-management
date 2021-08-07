from ytmusicFunctions import AddToPlaylist, ClearPlaylist
from bson.objectid import ObjectId
from pymongo.database import Database
from ytmusicapi import YTMusic
from pymongo import MongoClient
from secretsFile import mongoString
from datetime import datetime
import cProfile

def UpdateLikeSongsSorted(databaseConnectionString:str):
    ytmusic = YTMusic("headers_auth.json")
    mongoClient = MongoClient(databaseConnectionString)
    db = mongoClient['scrobble']
    playlistId = "PLJpUfuX6t6dScH3Ua2f2EsmRC4PolZp8I"
    likedSongs = db['scrobbleCount'].find(
        {"likeStatus": 1},
        sort=[("time", 1)],
        limit=100
    )
    videoIds = [
        song['ytmusicId'] for song in likedSongs
    ]
    ClearPlaylist(ytmusic=ytmusic, playlistId=playlistId)
    results = [
        AddToPlaylist(
            ytmusic=ytmusic,
            playlistId=playlistId,
            videoId=videoId
        ) for videoId in videoIds
    ]
    if results:
        nowFormatted = datetime.now().strftime(
            "%Y-%m-%d at %H:%M"
        )
        ytmusic.edit_playlist(
            playlistId=playlistId,
            description=f"Updated on {nowFormatted}"
        )
    return

if __name__ == "__main__":

    # cProfile.run("UpdateLikeSongsSorted(db)")
    UpdateLikeSongsSorted(
        databaseConnectionString=mongoString
    )
    


    