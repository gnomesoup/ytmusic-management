from bson.objectid import ObjectId
from pymongo.database import Database
from ytmusicapi import YTMusic
from pymongo import MongoClient
from secretsFile import mongoString
from datetime import datetime
import cProfile

def songCount(db:Database, doc:dict):
    songCount = db['scrobbles'].count_documents(
        {"songId": doc['_id']}
    )
    lastPlayed = db['scrobbles'].find_one(
        {"songId": doc['_id']},
        sort=[('time', -1)]
    )
    if lastPlayed is not None and "time" in lastPlayed:
        lastPlayedTime = lastPlayed['time']
    else:
        lastPlayedTime = datetime(1979, 1, 14)
    # print(f"{doc['title']} - {', '.join(doc['artists'])}: {songCount} ({lastPlayed['time']})")
    return {
        "songId": doc['_id'],
        "videoId": doc['ytmusicId'],
        "lastPlayed": lastPlayedTime,
        "playCount": songCount
    }

def main(db):
    likedSongs = db['songs'].find(
        {"likeStatus": 1}
    )
    songData = [
        songCount(db=db, doc=doc) for doc in likedSongs
    ]
    sortedData = sorted(songData, key=lambda x: x['lastPlayed'], reverse=False)
    return

def main2(db:Database):
    likedSongs = db['songs'].find(
        {"likeStatus": 1}
    )
    songIds = [doc['_id'] for doc in likedSongs]
    db['songs'].aggregate()
    scrobbledSongs = db['songs'].find(
        {"songId": {"$in": songIds}},
        projection={"_id": 1, "time": -1},
        sort=[("time", 1)]
    )
    songData = {}
    for doc in likedSongs:

        


if __name__ == "__main__":
    ytmusic = YTMusic("headers_auth.json")
    mongoClient = MongoClient(mongoString)
    db = mongoClient['scrobble']

    cProfile.run("main(db)")
    


    