from ytmusicapi import YTMusic
from ytmusicFunctions import UpdateWXRTYesterday

print("Updating WXRT Yesterday playlist")

playlistId = "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw"
ytmusic = YTMusic("headers_auth.json")

if UpdateWXRTYesterday(ytmusic, playlistId):
    print("Playlist update successful")
else:
    print("Error updating playlist")