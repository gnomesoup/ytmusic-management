from pymongo import MongoClient
from secretsFile import mongoString, homeassistantToken, homeassistantUrl
from pprint import pprint
from bson.objectid import ObjectId
from datetime import date, datetime, timedelta
from dateutil import parser, tz
from requests import get

def GrabTime(scrobble):
    scrobbleTime = scrobble['time']


fromTZ = tz.gettz("UTC")
toTZ = tz.gettz("America/Chicago")

mongoClient = MongoClient(mongoString)
db = mongoClient['scrobble']
songs = db['songs']

# homeassistantResult = get(homeassistantUrl + "/api/states/person.michael",
#                headers={
#                    "Authorization": "Bearer " + homeassistantToken,
#                    "Content-Type": "application/json"
#                })
# homeassistantData = homeassistantResult.json()
# print(homeassistantData['attributes']['latitude'],
#       homeassistantData['attributes']['longitude'])

# songCount = db['songs'].delete_many({'time': {
#     "$gte": parser.parse("2021-04-22T04:22:00.000Z"),
#     "$lt": parser.parse("2021-04-22T04:24:00.000Z")
#     }})
# print(songCount)

# exit()
# scrobbles with unformatted dates
songCount = songs.count_documents({'time': {"$not": {"$type": "date"}}})
print("scrobbles with unformatted dates:", songCount)

# dateless = songs.find({'time': {"$not": {"$type": "date"}}})

# for song in dateless:
#     newDate = parser.parse(song['time'])
#     result = db['songs'].update_one({"_id": song['_id']}, {"$set": {"time": newDate}})
#     print(result.modified_count)

# today's scrobbles
today = datetime.combine(date.today(), datetime.min.time())
todayUTC = today.astimezone()
print(todayUTC.isoformat())

songCount = songs.count_documents({"time": {"$gte": todayUTC}})
print("scrobbles from today:", songCount)

for scrobble in songs.find({"time": {"$gte": todayUTC,}})\
                           .sort("time", -1):
    scrobbleTimeUTC = scrobble['time'].replace(tzinfo=fromTZ)
    scrobbleTimeLocal = scrobbleTimeUTC.astimezone(toTZ)
    print(scrobbleTimeLocal.strftime("%Y-%m-%d %H:%M"),
        "    ",
        scrobble['title'],
        "-",
        ", ".join(scrobble['artists']))

# yesterday's scrobbles
yesterdayUTC = todayUTC - timedelta(days=1)
songCount = songs.count_documents(
    {"time": {"$lt": todayUTC, "$gte": yesterdayUTC}}
)
print("scrobbles from yesterday:", songCount)

# last 7 days scrobbles
last7UTC = todayUTC - timedelta(days=7)
songCount = songs.count_documents(
    {"time": {"$gte": last7UTC}}
)
print("scrobbles from last 7 days:", songCount)

# search by artist
artist = "U2"
artistQuery = {"artists": artist}
artistCount = songs.count_documents(artistQuery)
if artistCount == 1:
    descriptor = "once"
else:
    descriptor = str(artistCount) + " times"
print(artist, "played", descriptor)
firstPlayed = songs.find_one(artistQuery, sort=[("time", 1)])
lastPlayed = songs.find_one(artistQuery, sort=[("time", -1)])
print("first played", firstPlayed["title"], "on",
        firstPlayed["time"].strftime("%Y-%m-%d at %H:%M"))
print("last played", lastPlayed["title"], "on", 
        lastPlayed["time"].strftime("%Y-%m-%d at %H:%M"))