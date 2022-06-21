from datetime import date, datetime, timedelta
import json
from lxml import html
from os import path
import requests


def WDVXCollectPlaylistData(url: str, filePath: str) -> None:
    r = requests.get(url)
    doc = html.fromstring(r.content)

    selectorXPath = (
        './/*[contains(concat(" ",normalize-space(@class)," ")," playlist-table ")]'
    )
    tables = doc.xpath(selectorXPath)

    if tables:
        trs = tables[0].xpath("//tr")
    else:
        print("No tables found")
        return
    if path.exists(filePath):
        with open(filePath, mode="r") as fp:
            allTracks = json.load(fp)
    else:
        allTracks = {}
    newTracks = {
        tr[0].text_content(): tr[1].text_content() for tr in trs if len(tr) == 2
    }
    twoWeeksAgo = date.today() - timedelta(days=14)
    addCount = 0
    for track in newTracks:
        if track not in allTracks:
            allTracks[track] = newTracks[track]
            addCount += 1
        else:
            trackDate = datetime.strptime(track, "%b %d, %Y %H:%M %p")
            if date(trackDate.year, trackDate.month, trackDate.day) < twoWeeksAgo:
                allTracks.pop(track)
    if addCount:
        plural = "" if addCount == 1 else "s"
        print(f"WDVX Collect: Adding {addCount} track{plural}")
    with open(filePath, mode="w") as fp:
        json.dump(allTracks, fp)
    plural = "" if len(allTracks) == 1 else "s"
    print(f"WDVX Collect: {len(allTracks)} total track{plural}")
    return


if __name__ == "__main__":
    WDVXCollectPlaylistData("https://wdvx.com/listen/playlist/", "WDVX-Playlist.json")
