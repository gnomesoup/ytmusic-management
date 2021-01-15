from requests import get
import lxml.html
from ytmusicapi import YTMusic

year = "2021"
month = "1"
day = "14"
url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
    + month + "%2F" + day + "%2F" + year
ytmusic = YTMusic("headers_auth.json")
playlistTitle = "WXRT Playlist from " + year + "-" + month + "-" + day
playlistDescription = ""
playlistPrivacyStatus = "PUBLIC"

page = get(url)
doc = lxml.html.fromstring(page.content)
trs = doc.xpath('//tr')

songsToAdd = []
for tr in trs[5:]:
    if len(tr) == 6:
        songsToAdd.append(tr[2].text_content().lower() + " " + tr[4].text_content().lower())

uniqueSongsToAdd = list(set(songsToAdd))

videoIds = []
for song in reversed(uniqueSongsToAdd):
    songSearch = ytmusic.search(song, "songs")
    print("Search Term:", song)
    if not songSearch:
        print("   Returned: None\n")
    else:
        firstSong = songSearch[0]
        videoIds.append(firstSong['videoId'])
        print("   Returned:", firstSong['artists'][0]['name'], "-", firstSong['title'], "\n")

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print("playlistId:", newPlaylist)
print("Found", len(songsToAdd), "songs")
print(len(uniqueSongsToAdd), "songs were unique")
print("YTMusic matched", len(videoIds), "songs")