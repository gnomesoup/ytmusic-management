from requests import get
import lxml.html
import re
from ytmusicapi import YTMusic
import datetime

today = datetime.datetime.now() - datetime.timedelta(hours=12)
weekday = today.weekday()
lastSaturday = today - datetime.timedelta(days=(7 - (5 - today.weekday())) % 7)
lastSaturdayFormatted = "{dt.month}%2F{dt.day}%2F{dt.year}".format(dt = lastSaturday)

url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
    + lastSaturdayFormatted
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
    if re.match("(9|10|11):\d\d\sAM",song[0]):
        songsToAdd.append(song[1])

videoIds = []
years = {}
for song in songsToAdd:
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
playlistDescription = "Air date " + lastSaturday.strftime("%Y-%m-%d")
newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print(playlistTitle)
print("playlistId:", newPlaylist)
print("Found", len(songsToAdd), "songs")
print("YTMusic matched", len(videoIds), "songs")