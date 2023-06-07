from pymongo import MongoClient
from pymongo.database import Database
from ytmusicapi import YTMusic
from secretsFile import mongoString
from ytmusicFunctions import GetSongId
from ytmusicFunctions import LikeStatus

def LikeSongByYTMusicId(db:Database, videoId:str, databaseUser:str):
    db = mongoClient['scrobble']
    songDocument = db['songs'].find_one_and_update(
        {"ytmusicId": videoId},
        {"$set": {"likeStatus": 1}}
    )
    if songDocument is None:
        songId = None
    else:
        songId = songDocument["_id"]
    return {"videoId": videoId, "songId": songId}

if __name__ == "__main__":
    ytmusic = YTMusic("oauth.json")
    mongoClient = MongoClient(mongoString)
    db = mongoClient['scrobble']
    databaseUser = "michael"
    

    print(
        f"Missing Like Status: "
        f"{db['songs'].count_documents( {'likeStatus': {'$exists': False}})}"
    )

    ytLikes = ytmusic.get_liked_songs(limit=2000)
    videoIds = [track['videoId'] for track in ytLikes['tracks']]
    updatedSongs = [
        LikeSongByYTMusicId(
            db=db,
            videoId=videoId,
            databaseUser=databaseUser
        ) for videoId in videoIds
    ]

    newSongs = [
        GetSongId(ytmusic=ytmusic, db=db, videoId=track['videoId'])
        for track in updatedSongs if track['songId'] is None
    ]
    if newSongs:
        print("Adding new songs to database")
    
    for songId in newSongs:
        ['songs'].find_one_and_update(
            {"_id": songId},
            {"$set": {"likeStatus": 1}}
        )