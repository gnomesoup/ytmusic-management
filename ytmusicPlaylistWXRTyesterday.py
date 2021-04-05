from requests import get

import lxml.html
from ytmusicapi import YTMusic
from ytmusicFunctions import getSongVideoIds
from datetime import date, datetime, timedelta

playlistId = "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw"

print("Updating playlist", playlistId)

ytmusic = YTMusic("headers_auth.json")
try:
    currentSongCount = ytmusic.get_playlist(playlistId, limit=1)["trackCount"]
except Exception as e:
    print("Error accessing playlist: ", e)
    exit()

yesterday = date.today() - timedelta(days=1)
yesterdayFormatted = "{dt.month}%2F{dt.day}%2F{dt.year}".format(dt = yesterday)

url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
    + yesterdayFormatted

page = get(url)
doc = lxml.html.fromstring(page.content)
trs = doc.xpath('//tr')

songsToAdd = []
for tr in trs[5:]:
    if len(tr) == 6:
        songsToAdd.append(tr[2].text_content().lower() + " " + tr[4].text_content().lower())

songsToAdd.reverse()
videoResults = getSongVideoIds(ytmusic, songsToAdd)

if currentSongCount > 0:
    currentPlaylist = ytmusic.get_playlist(playlistId, limit=currentSongCount)
    # currentSongs = [x['setVideoId'] for x in currentPlaylist['tracks']]
    ytmusic.remove_playlist_items(playlistId, currentPlaylist['tracks'])

addedVideos = False
for videoId in videoResults['videoIds']:
    status = ytmusic.add_playlist_items(playlistId, videoIds=[videoId])
    if status['status'] == "STATUS_SUCCEEDED":
        addedVideos = True
    else:
        print(status)

if addedVideos:
    nowFormatted = datetime.now().strftime("%Y-%m-%d at %H:%M")
    description = (
        f"Last updated {nowFormatted}.\n"
        f"Station played {videoResults['searchCount']} songs.\n"
        f"{videoResults['uniqueCount']} songs were unique.\n"
        f"YTMusic match {videoResults['matchedCount']} songs.\n\n"
        f"Note: Songs I've marked as \"dislike\" were not included in the playlist."
        )
    ytmusic.edit_playlist(playlistId, description=description)
    print("Playlist update successful")
else:
    print("There was an error adding songs to the playist.")
