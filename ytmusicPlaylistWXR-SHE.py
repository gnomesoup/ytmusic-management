from ytmusicapi import YTMusic
from ytmusicFunctions import MixPlaylists

if __name__ == "__main__":
    
    shePlaylistId = "PLJpUfuX6t6dTyEfFJmvVlIGzcXR1dKFt5"
    xrtPlaylistId = "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw"
    wxrShePlaylistId = "PLJpUfuX6t6dSbJr2-k5ItAMFr7-DNszDJ"

    ytmusic = YTMusic("headers_auth.json")

    print("Updating WXR-SHE Mix playlist")

    if MixPlaylists(
        ytmusic=ytmusic,
        playlistId1=xrtPlaylistId,
        playlistId2=shePlaylistId,
        finalPlaylistId=wxrShePlaylistId
    ):
        print("Playlist update successful")
    else:
        print("Error updating playlist")
