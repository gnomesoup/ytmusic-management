from ytmusicapi import YTMusic
from ytmusicFunctions import CreateWXRTFlashback

print("Creating WXRT Saturday Morning Flashback Playlist")
ytmusic = YTMusic("headers_auth.json")

result = CreateWXRTFlashback(ytmusic)

if result:
    print("Playlist created successfully")
else:
    print("Error creating playlist")