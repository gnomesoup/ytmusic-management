# from secretsFile import mongoString
from datetime import date, datetime, timedelta
import json
from os import path
from pymongo import MongoClient
from secretsFile import mongoString
from ytmusicapi import YTMusic
from ytmusicFunctions import YesterdayPlaylistsUpdate


def UpdateWDVXYesterday(
    ytmusic: YTMusic, playlistId: str, dbConnectionString: str = None
) -> bool:
    """Collect playlist data on WDVX from yesterday and import it to a YouTube
    Music playlist.

    Args:
        ytmusic (YTMusic): YouTube Music Session
        playlistId (str): YouTube music id for the playlist to be updated
        dbConnectionString (str, optional): Connection string for the Mongo
            database used for song caching to speed up searches. If no string
            is provided, all searches will happen directly on YouTube music.
            Defaults to None.

    Returns:
        bool: Returns true if successful. Returns false if the playlist
            could not be updated.
    """

    if dbConnectionString is not None:
        mongoClient = MongoClient(dbConnectionString)
        db = mongoClient['scrobble']

    filePath = "WDVX-Playlist.json"
    if path.exists(filePath):
        with open(filePath, mode="r") as fp:
            allTracks = json.load(fp)
    else:
        print(f"Unable to find playlist data for WDVX at {filePath}")
        return

    yesterday = date.today() - timedelta(days=1)
    # todayTracks = [allTracks[key] for key in allTracks if key ]
    todayTracks = []
    for key in allTracks:
        trackDateTime = datetime.strptime(key, "%b %d, %Y %H:%M %p")
        trackDate = date(trackDateTime.year, trackDateTime.month, trackDateTime.day)
        # print(f"{yesterday} == {trackDate}: {trackDate == yesterday}")
        if trackDate == yesterday:
            todayTracks.append(allTracks[key])
    
    YesterdayPlaylistsUpdate(
        ytmusic=ytmusic,
        db=None,
        playlistId=playlistId,
        SongArtistSearch=todayTracks,
    )
    return


if __name__ == "__main__":
    print("Updating WDVX Yesterday playlist")
    ytmusic = YTMusic("headers_auth.json")
    playlistId = "PLJpUfuX6t6dTz7hGKVztERi0YnE_azCg1"
    if UpdateWDVXYesterday(
        ytmusic=ytmusic,
        playlistId=playlistId,
        dbConnectionString=mongoString,
    ):
        print("Playlist update successful")
    else:
        print("Error updating playlist")
