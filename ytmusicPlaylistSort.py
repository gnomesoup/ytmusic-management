from ytmusicapi import YTMusic

ytmusic = YTMusic("headers_auth.json")
# libraryPlaylists = ytmusic.get_library_playlists()
# for playlist in libraryPlaylists:
#     print(playlist['title'], playlist['playlistId'])
playlistId = "PLJpUfuX6t6dQdLW_mPfm69Ar-cOmkq2Wq"

playlistTrackCount = ytmusic.get_playlist(playlistId,)['trackCount']
playlistTrackCount = 10
playlist = ytmusic.get_playlist(playlistId, limit=(playlistTrackCount+1))
tracks = playlist['tracks']
print(len(tracks))
trackDict = {}
for track in tracks:
    song = track['title'] + " " + track['artists'][0]['name']
    trackDict[song] = track['videoId']

videoIds = [trackDict[track] for track in sorted(trackDict)]
print(trackDict.keys())

# status = ytmusic.edit_playlist(playlistId, moveItem=videoIds)

# status = ytmusic.create_playlist("Christmas Sorted", "Test", video_ids=videoIds)
# print(status)