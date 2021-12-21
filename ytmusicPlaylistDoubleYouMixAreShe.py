import random
from ytmusicapi import YTMusic
from ytmusicFunctions import AddToPlaylist, ClearPlaylist
from ytmusicFunctions import GetPlaylistTrackCount

def MixChicagoRadioStations(ytmusic:YTMusic) -> bool:
    shePlaylistId = "PLJpUfuX6t6dTyEfFJmvVlIGzcXR1dKFt5"
    xrtPlaylistId = "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw"
    mixPlaylistId = "PLJpUfuX6t6dS__5F2qgcopS26s5MbO8Yd"
    wmrsPlaylistId = "PLJpUfuX6t6dSQDudst4PXxL_vo3T1uOd4"

    playlistTrackCount = {
        xrtPlaylistId: 64,
        shePlaylistId: 48,
        mixPlaylistId: 16,
    }

    collectedVideoIds = []
    for playlistId, count in playlistTrackCount.items():
        playlistData = ytmusic.get_playlist(
            playlistId=playlistId,
            limit=GetPlaylistTrackCount(
                ytmusic=ytmusic,
                playlistId=playlistId
            )
        )
        songIds = [
            track['videoId'] for track in playlistData['tracks']
        ]
        random.shuffle(songIds)
        addCount = 0
        for songId in songIds:
            if addCount >= count:
                break
            if songId in collectedVideoIds:
                continue
            collectedVideoIds.append(songId)
            addCount += 1

    ClearPlaylist(ytmusic=ytmusic, playlistId=wmrsPlaylistId)
    random.shuffle(collectedVideoIds)
    results = [
        AddToPlaylist(
            ytmusic=ytmusic,
            playlistId=wmrsPlaylistId,
            videoId=videoId
        ) for videoId in collectedVideoIds
    ]
    return sum(results) > 0

if __name__ == "__main__":
    
    ytmusic = YTMusic("headers_auth.json")
    print("Updating Double You Mix Are She playlist")

    if MixChicagoRadioStations(ytmusic=ytmusic):
        print("Playlist update successful")
    else:
        print("Error updating playlist")
