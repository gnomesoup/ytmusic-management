from ytmusicapi import YTMusic


ytmusic = YTMusic('headers_auth.json')
playlists = ytmusic.get_library_playlists(50)
for i in playlists:
    print(i['title'], i['playlistId'])