from ytmusicFunctions import GetDetailedSongData
from pymongo import MongoClient
from pymongo.database import Database
from secretsFile import mongoString
from ytmusicapi import YTMusic, ytmusic

def GetPlayability(
    ytmusic:YTMusic,
    dbDocument:dict,
) -> dict:
    playable = True
    ytmusicId = dbDocument['ytmusicId']
    songData = ytmusic.get_song(ytmusicId)
    if songData['playabilityStatus']['status'] != 'OK':
        statusMessage = (
            f"{ytmusicId} playablilityStatus="
            f"{songData['playabilityStatus']['status']}: "
            f"{songData['playabilityStatus']['reason']}"
        )
        titleArtist = f"{dbDocument['title']} {dbDocument['artists'][0]}"
        ytmSearch = ytmusic.search(titleArtist, "songs")
        firstSong = ytmSearch[0]
        firstSongArtists = [
            artist['name'] for artist in firstSong['artists']
        ]
        if (
            (dbDocument['title']).lower() == (firstSong['title']).lower() and
            dbDocument['artists'][0] in firstSongArtists
        ):
            db['songs'].find_one_and_update(
                {"_id": dbDocument['_id']},
                {"$set": {"ytmusicId": firstSong['videoId']}}
            )
            print(f"{statusMessage} <- {firstSong['videoId']}")
        else:
            db['songs'].find_one_and_update(
                {"_id": dbDocument['_id']},
                {"$set": {"ytmusicPlayable": False}}
            )
            print(f"{statusMessage} != {firstSong['videoId']}")
            print(
                f"old: {titleArtist} | "
                f"{dbDocument['album'] if 'album' in dbDocument else ''}"
            )
            print(
                f"new: {firstSong['title']} "
                f"{', '.join(firstSongArtists)} | "
                f"{firstSong['album']['name'] if 'album' in firstSong else ''}"
            )
            playable = False
    else:
        db['songs'].find_one_and_update(
            {"_id": dbDocument['_id']},
            {"$set": {"ytmusicPlayable": True}}
        )
    return playable

def VideoIdCheck(
    ytmusic:YTMusic,
    db:Database,
    skip:int=0,
    limit:int=None,
) -> None:
    if limit is None:
        limit = db['songs'].count_documents({})
    print(f"Video Id Cleanup. {skip=} {limit=}")
    lineEnd = "\r"
    for i, doc in enumerate(db['songs'].find({}, skip=skip, limit=limit)):
        print(f"song#: {i + skip + 1}", end=lineEnd)
        if not GetPlayability(ytmusic=ytmusic, dbDocument=doc):
            print(f"song#: {i + skip + 1}")
    print(f"song#: {i + skip + 1}")
    return

if __name__ == "__main__":
    mongoClient = MongoClient(mongoString)
    db = mongoClient['scrobble']
    ytmusic = YTMusic("headers_auth.json")
    VideoIdCheck(ytmusic=ytmusic, db=db, skip=100, limit=900)
