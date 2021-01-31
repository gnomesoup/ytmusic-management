from requests import get
import lxml.html
import re
from ytmusicapi import YTMusic

year = "2021"
month = "1"
day = "23"
url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
    + month + "%2F" + day + "%2F" + year
ytmusic = YTMusic("headers_auth.json")
playlistPrivacyStatus = "PUBLIC"

page = get(url)
doc = lxml.html.fromstring(page.content)
trs = doc.xpath('//tr')

songList = []
for tr in reversed(trs[5:]):
    if len(tr) == 6:
        songList.append([tr[0].text_content(), tr[2].text_content().lower() + " " + tr[4].text_content().lower()])

songsToAdd = []
for song in songList:
    if re.match("(9|10):\d\d\sAM",song[0]):
        songsToAdd.append(song[1])
uniqueSongsToAdd = list(set(songsToAdd))

videoIds = []
years = {}
for song in reversed(uniqueSongsToAdd):
    songSearch = ytmusic.search(song, "songs")
    print("Search Term:", song)
    if not songSearch:
        print("   Returned: None\n")
    else:
        firstSong = songSearch[0]
        songInfo = ytmusic.get_song(firstSong['videoId'])
        matchResult = re.search(r"^\d{4}", songInfo['release'])
        if matchResult is not None:
            yearReleased = matchResult.group()
            if yearReleased in years:
                years[yearReleased] = years[yearReleased] + 1
            else:
                years[yearReleased] = 1
        videoIds.append(firstSong['videoId'])
        print("   Returned:", firstSong['artists'][0]['name'], "-", firstSong['title'], "\n")


playlistYear = max(years, key=lambda k: years[k])
playlistTitle = "WXRT Saturday Morning Flashback " + playlistYear
playlistDescription = "Air date " + year + "-" + month.zfill(2) + "-" + day.zfill(2)
newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print(playlistTitle)
print("playlistId:", newPlaylist)
print("Found", len(songsToAdd), "songs")
print(len(uniqueSongsToAdd), "songs were unique")
print("YTMusic matched", len(videoIds), "songs")