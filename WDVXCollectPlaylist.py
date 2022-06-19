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
    print(f"len(allTracks) = {len(allTracks)}")
    print(f"len(newTracks) = {len(newTracks)}")
    for track in newTracks:
        if track not in allTracks:
            allTracks[track] = newTracks[track]
            print(f"Track Added: {newTracks[track]}")
    with open(filePath, mode="w") as fp:
        json.dump(allTracks, fp)
    print(f"len(allTracks) = {len(allTracks)}")
    return


if __name__ == "__main__":
    WDVXCollectPlaylistData("https://wdvx.com/listen/playlist/", "WDVX-Playlist.json")
