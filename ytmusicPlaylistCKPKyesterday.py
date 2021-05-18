from ytmusicapi import YTMusic
from ytmusicFunctions import UpdateCKPKYesterday

playlistId = "PLJpUfuX6t6dR9DeM0gOH3rLt99Sl3SDVG"

print("Updating playlist", playlistId)

ytmusic = YTMusic("headers_auth.json")

if UpdateCKPKYesterday(ytmusic, playlistId):
    print("Playlist update successful")
else:
    print("There was an error adding songs to the playlist.")