from pymongo import MongoClient
from pymongo.database import Database
from ytmusicapi import YTMusic
from secretsFile import mongoString
from ytmusicFunctions import GetSongId
from ytmusicFunctions import GetLikeStatus

if __name__ == "__main__":
    ytmusic = YTMusic("oauth.json")
    mongoClient = MongoClient(mongoString)
    db = mongoClient['scrobble']

    skipCount = 0
    n = skipCount 
    query = {}
    keysToUpdate = ["likeStatus"]
    songCount = db['songs'].count_documents(query)
    for song in db['songs'].find(query, skip=skipCount):
        # likeStatus = None
        # videoId = song['ytmusicId']
        # likeStatus = GetLikeStatus(ytmusic, videoId, None)
        # if likeStatus:
        #     songId = song['_id']
        #     db['songs'].update_one(
        #         {"_id": songId}, {"$set": {"likeStatus": likeStatus.value}}
        #     )
        # n += 1
        # if n % 100 == 0:
        #     print(f"{n}/{songCount}")

        watchPlaylist = ytmusic.get_watch_playlist(song['ytmusicId'])
        ytmusicSongInfo = watchPlaylist['tracks'][0]
        if ytmusicSongInfo:
            setData = {}
            if "likeStatus" in ytmusicSongInfo:
                likeStatus = ytmusicSongInfo['likeStatus']
                storedLikeStatus = 1 if likeStatus == "LIKE" \
                    else -1 if likeStatus == "DISLIKE" else 0
                setData['likeStatus'] = storedLikeStatus
            if setData:
                db['songs'].update_one({"_id": song["_id"]}, {"$set": setData})
        n += 1
        if (n % 100) == 0:
            print(f"{n}/{songCount}")