from requests import get
import lxml.html
from ytmusicapi import YTMusic
from ytmusicFunctions import getSongVideoIds

year = "2021"
month = "3"
day = "6"
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

songsToAdd.reverse()
videoResults = getSongVideoIds(ytmusic, songsToAdd)

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoResults['videoIds'])

print("playlistId:", newPlaylist)
print("Found", videoResults['searchCount'], "songs")
print(videoResults['uniqueCount'], "songs were unique")
print("YTMusic matched", videoResults['matchedCount'], "songs")
