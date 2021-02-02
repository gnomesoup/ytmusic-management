from requests import get
import lxml.html
from ytmusicapi import YTMusic

year = "2021"
month = "1"
day = "31"
url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
    + month + "%2F" + day + "%2F" + year
ytmusic = YTMusic("headers_auth.json")
playlistTitle = "WXRT Playlist from " + year + "-" + month.zfill(2) + "-" + day.zfill(2)
playlistDescription = ""
playlistPrivacyStatus = "PUBLIC"

page = get(url)
doc = lxml.html.fromstring(page.content)
trs = doc.xpath('//tr')

songsToAdd = []
for tr in trs[5:]:
    if len(tr) == 6:
        songsToAdd.append(tr[2].text_content().lower() + " " + tr[4].text_content().lower())

uniqueSongsToAdd = []
for song in reversed(songsToAdd):
    if song not in uniqueSongsToAdd:
        uniqueSongsToAdd.append(song)

uniqueSongsToAdd = uniqueSongsToAdd[160:165]
videoIds = []
for song in reversed(uniqueSongsToAdd):
    songSearch = ytmusic.search(song, "songs")
    print("Search Term:", song)
    if not songSearch:
        print("   Returned: None\n")
    else:
        firstSong = songSearch[0]
        videoId = firstSong['videoId']
        dislike = False
        try:
            album = ytmusic.get_album(firstSong['album']['id'])
            for track in album['tracks']:
                if track['videoId'] == videoId:
                    if track['likeStatus'] == 'DISLIKE':
                        dislike = True
        except:
            pass
        if not dislike:
            videoIds.append(videoId)
            print("   Returned:", firstSong['artists'][0]['name'], "-", firstSong['title'], "\n")
        else:
            print("Dislike: Will not be included in playlist\n")

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print("playlistId:", newPlaylist)
print("Found", len(songsToAdd), "songs")
print(len(uniqueSongsToAdd), "songs were unique")
print("YTMusic matched", len(videoIds), "songs")