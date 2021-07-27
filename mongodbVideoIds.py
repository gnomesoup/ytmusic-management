from pymongo import DESCENDING, MongoClient
from secretsFile import mongoString
from dateutil import parser, tz
from scrobbleFunctions import GetSongId
from ytmusicapi import YTMusic
from ytmusicFunctions import GetSongVideoIds, UpdatePlaylist, GetSongVideoId, GetLikeStatus
from ytmusicFunctions import LikeStatus
import datetime

def GetSongTitle(mongodatabase, videoId):
    document = mongodatabase.find_one(
        {"videoId": videoId},
        projection = {"title": 1, "artists": 1}
    )
    return f"{document['title']} - {document['artists'][0]}"

def KeyCheck(key, documentData, ytmusicData):
    if key not in documentData:
        if key in ytmusicData:
            return True
        else:
            return False
    else:
        return False

fromTZ = tz.gettz("UTC")
toTZ = tz.gettz("America/Detroit")

ytmusic = YTMusic("headers_auth.json")
mongoClient = MongoClient(mongoString)
db = mongoClient['scrobble']
scrobbles = db['scrobbles']
songs = db['songs']
keysToUpdate = ["artists", "likeStatus", "album", "year"]

query = {"time": {"$gt": datetime.datetime(2021, 7, 24)}}
skipCount = 0
songCount = scrobbles.count_documents(query)
print(f"{songCount=}")
# album = ytmusic.get_album('MPREb_eHkCHZP1e16')
# videoId, browseId, songId = GetSongVideoId(
#     ytmusic, "pretenders don't get me wrong", None, True
# )
# print(GetLikeStatus(ytmusic, videoId, None, db=None, verbose=True))
exit()
n = skipCount 
for song in songs.find(query, skip=skipCount):
    likeStatus = None
    videoId = song['ytmusicId']
    likeStatus = GetLikeStatus(ytmusic, videoId, None)
    if likeStatus:
        songId = song['_id']
        songs.update_one(
            {"_id": songId}, {"$set": {"likeStatus": likeStatus.value}}
        )
    n += 1
    if n % 100 == 0:
        print(f"{n}/{songCount}")

#     ytmusicSongInfo = None
#     for key in keysToUpdate:
#         if key not in song:
#             watchPlaylist = ytmusic.get_watch_playlist(song['ytmusicId'])
#             ytmusicSongInfo = watchPlaylist['tracks'][0]
#             break
#     if ytmusicSongInfo:
#         setData = {}
#         if KeyCheck("artists", song, ytmusicSongInfo):
#             setData['artists'] = [
#                 artist['name'] for artist in ytmusicSongInfo['artists']
#             ]
#         if KeyCheck("likeStatus", song, ytmusicSongInfo):
#             likeStatus = ytmusicSongInfo['likeStatus']
#             storedLikeStatus = 1 if likeStatus == "LIKE" \
#                 else -1 if likeStatus == "DISLIKE" else 0
#             setData['likeStatus'] = storedLikeStatus
#         if KeyCheck("album", song, ytmusicSongInfo):
#             setData['album'] = ytmusicSongInfo['album']['name']
#         if KeyCheck("year", song, ytmusicSongInfo):
#             setData['year'] = ytmusicSongInfo['year']
#         if setData:
#             songs.update_one({"_id": song["_id"]}, {"$set": setData})
#     songCount -= 1
#     if (songCount % 100) == 0:
#         print(f"Songs remaining: {songCount}")


            



# print(scrobbles.count_documents({"songId": {"$exists": False}}))
# for scrobble in scrobbles.find({"songId": {"$exists": False}}):
#     songId = GetSongId(ytmusic, db, scrobble['videoId'])
#     if songId: 
#         if 'songId' not in scrobble:
#             scrobbles.find_one_and_update(
#                 {"_id": scrobble['_id']},
#                 {"$set": {"songId": songId}}
#             )
#         else:
#             print(f"{scrobble['_id']}: songId already assigned")
#     else:
#         print(f"{scrobble['_id']}: Not a valid songId")

# distinctVideoIds = scrobbles.distinct("videoId")

# for videoId in distinctVideoIds:
#     songDocument = scrobbles.find_one(
#         {"videoId": videoId},
#         projection={"videoId": 1, "title": 1, "artists": 1, "album": 1}
#     )
#     if songs.count_documents({"ytmusicId": videoId}) > 0:
#         print(f"Already added {videoId}")
#         continue
#     song = {"ytmusicId": songDocument['videoId']}
#     for key in songDocument:
#         if key == 'title':
#             song['title'] = songDocument['title']
#         elif key == 'artists':
#             song['artists'] = songDocument['artists']
#         elif key == 'album':
#             song['album'] = songDocument['album']
#     songs.insert_one(song)