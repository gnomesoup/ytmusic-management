from ytmusicapi import YTMusic
from ytmusicFunctions import UpdateWKLQYesterday

print("Updating WXRT Yesterday playlist")

playlistId = "PLJpUfuX6t6dRg0mxM5fEufwZOd5eu_DmU"
ytmusic = YTMusic("headers_auth.json")

if UpdateWKLQYesterday(ytmusic, playlistId):
    print("Playlist update successful")
else:
    print("Error updating playlist")