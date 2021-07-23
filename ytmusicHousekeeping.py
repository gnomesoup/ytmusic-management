from ytmusicapi import YTMusic
from datetime import datetime
from time import time, sleep
from pymongo import MongoClient
from secretsFile import mongoString, homeassistantToken, homeassistantUrl
from scrobbleFunctions import ScrobbleCheck
from scrobbleFunctions import GetLocationFromHomeAssistant
from scrobbleFunctions import ScrobbleAddLocation
from scrobbleFunctions import LinkScrobblerSong
from ytmusicFunctions import UpdateWXRTYesterday, CreateWXRTFlashback
from ytmusicFunctions import UpdateCKPKYesterday
from ytmusicPlaylistWKLQyesterday import UpdateWKLQYesterday
import schedule
from threading import Thread

ytmusic = YTMusic("headers_auth.json")
mongoClient = MongoClient(mongoString)
db = mongoClient['scrobble']
scrobblerData = {
    "scrobblerId": '607f962eeafb5500062a4a68',
    "scrobblerUser": "michael",
    "queuedRequests": [],
    "requestAttempts": 0
}

def runThreaded(function, name):
    print(
        f"{datetime.now().isoformat()}  "
        f"Running: {name}"
    )
    job = Thread(target=function, name=name)
    job.start()

print("YouTube Music Housekeeping")

schedule.every().day.at("00:00").do(
    runThreaded,
    lambda: UpdateWXRTYesterday(ytmusic, "PLJpUfuX6t6dSaHuu1oeQHWhmMTM6G_hKw"),
    "WXRT_Yesterday"
)
schedule.every().day.at("00:30").do(
    runThreaded,
    lambda: UpdateWKLQYesterday(ytmusic, "PLJpUfuX6t6dRg0mxM5fEufwZOd5eu_DmU"),
    "WKLQ_Yesterday"
)
schedule.every().day.at("02:05").do(
    runThreaded,
    lambda: UpdateCKPKYesterday(ytmusic, "PLJpUfuX6t6dR9DeM0gOH3rLt99Sl3SDVG"),
    "CKPK_Yesterday"
)
schedule.every().saturday.at("12:15").do(
    runThreaded,
    lambda: CreateWXRTFlashback(ytmusic),
    "WXRT_Saturday_Morning_Flashback"
)

while True:
    try:
        scrobbleIds = ScrobbleCheck(ytmusic, db, scrobblerData['scrobblerUser'])
        if scrobbleIds:
            location = GetLocationFromHomeAssistant(
                homeassistantUrl,
                homeassistantToken,
                "person.michael",
            )
            for scrobbleId in scrobbleIds:
                ScrobbleAddLocation(
                    db['scrobbles'],
                    scrobbleId,
                    location
                )
                LinkScrobblerSong(ytmusic, db, scrobbleId)

            if len(scrobbleIds) == 1:
                suffix = ""
            else:
                suffix = "s"
            print(
                f"{datetime.now().isoformat()}  "
                f"Posted {len(scrobbleIds)} scrobble{suffix}"
            )
    except Exception as e:
        print(
            f"{datetime.now().isoformat()}  "
            f"Scrobble error: {e}"
        )
    
    try:
        schedule.run_pending()
    except Exception as e:
        print( 
            f"{datetime.now().isoformat()}  "
            f"Schedule error: {e}"
        )

    sleep(60.0 - (time() % 60.0))