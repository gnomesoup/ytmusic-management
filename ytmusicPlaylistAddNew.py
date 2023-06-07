from ytmusicapi import YTMusic

ytmusic = YTMusic("oauth.json")
playlistTitle = "TITLE"
playlistDescription = ""
playlistPrivacyStatus = "PUBLIC"

songsToAdd = [
"Artist Song Name"
]

videoIds = []
for song in songsToAdd:
    songSearch = ytmusic.search(song, "songs")
    print("Search Term:", song)
    if not songSearch:
        print("   Returned: None\n")
    else:
        firstSong = songSearch[0]
        videoIds.append(firstSong['videoId'])
        print("   Returned:", firstSong['title'], "-", firstSong['artists'][0]['name'], "\n")

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print("playlistId:", newPlaylist)
print("Searched", len(songsToAdd), "songs")
print("YTMusic matched", len(videoIds), "songs")