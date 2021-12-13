from ytmusicapi import YTMusic

from ytmusicFunctions import AddToPlaylist, ClearPlaylist
import random

if __name__ == "__main__":
    
    shePlaylistId = "PLJpUfuX6t6dTyEfFJmvVlIGzcXR1dKFt5"
    xrtPlaylistId = "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw"
    wxrShePlaylistId = "PLJpUfuX6t6dSbJr2-k5ItAMFr7-DNszDJ"

    ytmusic = YTMusic("headers_auth.json")

    shePlaylist = ytmusic.get_playlist(shePlaylistId)
    sheSongs = shePlaylist['tracks']
    xrtPlaylist = ytmusic.get_playlist(xrtPlaylistId)
    xrtSongs = xrtPlaylist['tracks']
    songIds = [
        track['videoId'] for track in
        sheSongs + xrtSongs
    ]

    ClearPlaylist(ytmusic=ytmusic, playlistId=wxrShePlaylistId)
    random.shuffle(songIds)
    for videoId in songIds:
        AddToPlaylist(
            ytmusic=ytmusic,
            playlistId=wxrShePlaylistId,
            videoId=videoId
        )