from ytmusicapi import YTMusic
from ytmusicFunctions import YesterdayPlaylistsUpdate
from secretsFile import mongoString
from pymongo import MongoClient
from pymongo.database import Database
from datetime import date, timedelta
import requests
from lxml import html

def UpdateWXRTYesterday(
    ytmusic:YTMusic, playlistId:str, db:Database=None
) -> bool:
    """
    Collect playlist data on WXRT from yesterday and import it to
    a YouTube Music playlist. Returns true if successful. Returns
    False if playlist could not be updated.
    """

    yesterday = date.today() - timedelta(days=1)
    yesterdayFormatted = "{dt.month}%2F{dt.day}%2F{dt.year}" \
        .format(dt = yesterday)

    url = "http://www.mediabase.com/whatsong/whatsong.asp?var_s=087088082084045070077&MONDTE="\
        + yesterdayFormatted

    page = requests.get(url)
    doc = html.fromstring(page.content)
    trs = doc.xpath('//tr')

    songsToAdd = []
    for tr in trs[5:]:
        if len(tr) == 6:
            songsToAdd.append(tr[2].text_content().lower() + " " + tr[4].text_content().lower())

    songsToAdd.reverse()
    return YesterdayPlaylistsUpdate(ytmusic, db, playlistId, songsToAdd)


if __name__ == "__main__":
    print("Updating WXRT Yesterday playlist")

    playlistId = "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw"
    ytmusic = YTMusic("headers_auth.json")
    mongoClient = MongoClient(mongoString)
    db = mongoClient['scrobble']

    UpdateWXRTYesterday(ytmusic, playlistId, db)
    #     print("Playlist update successful")
    # else:
    #     print("Error updating playlist")