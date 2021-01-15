from ytmusicapi import YTMusic

ytmusic = YTMusic("headers_auth.json")
playlistTitle = "TITLE"
playlistDescription = ""
playlistPrivacyStatus = "PUBLIC"

songsToAdd = ["artist song title"]

videoIds = []
for song in songsToAdd:
    songSearch = ytmusic.search(song, "songs")
    print("Search Term:", song)
    if not songSearch:
        print("Return: None\n")
    else:
        firstSong = songSearch[0]
        videoIds.append(firstSong['videoId'])
        print("Return:", firstSong['title'], "-", firstSong['artists'][0]['name'], "\n")

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print(newPlaylist)