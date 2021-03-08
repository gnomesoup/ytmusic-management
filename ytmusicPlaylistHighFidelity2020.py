from ytmusicapi import YTMusic

ytmusic = YTMusic("headers_auth.json")
playlistId = "PLJpUfuX6t6dSlyTg9M4CGzk8GVJEnkJ7w"
playlist = ytmusic.get_playlist(playlistId, 500)
songs = playlist['tracks']
print("Playlist:", playlist['title'])
print("Songs: ", len(songs))
print("Length: ", playlist['duration'])
lastSong = playlist['tracks'][-1]
print("\n")

toAdd = [
"Holiday in Cambodia Dead Kennedys",
"Inspired Blackalicious",
"Automatic The Pointer Sisters",
"It's All Coming Back to Me Now Celine Dion",
"Le Premier Bonheur du Jour Os Mutantes",
"I Want You to Want Me Cheap Trick",
"When I Get Home The Innocents",
"Memorabilia Soft Cell",
"Whereyougonnago? Jitwam",
"Rock-n-roll Victim Death",
"You Make Me Feel (Mighty Real) Sylvester",
"I Don't Wanna Hear It Minor Threat",
"Anxious Holy Ghost!",
"Give Me Fire GBH",
"I'm a Nobody US 69",
"Dry the Rain The Beta Band",
"In Search of Balance Reginald Omas Mamode IV",
"Justify the Way Dexter Lee Moore",
"Door of the Cosmos Sun Ra",
"La Pongo El Freaky Colectivo",
"Try Me Witch",
"Don't Depend on Me Direct Drive",
"Blaze - Digital Lab Remix Sandro Silva",
"Anime Blossom feat. Outlaw the Artist",
"Guess What Luciana",
"I Got It Carly and Martina",
"Perfect Night Fergie DJ & Evil Twin",
"Get Loud Tia P feat. Redwood",
"Juanita Moon Boots",
"Amateurs feat. Lights Sleepy Tom",
"875 Dollars De Lux",
"Nikes Frank Ocean",
"You Got Me The Roots",
"Make a Smile for Me Bill Withers",
"Pains Silk Rhodes",
"I Believe (When I Fall in Love It Will Be Forever) Stevie Wonder",
"Don't Let Me Be Misunderstood Nina Simone",
"Not Today Ronnie D'addario",
"Pains Silk Rhodes",
"Unsatisfied Woman Barbara Stant",
"Feel So Good Denise Darlington",
"I Get Lonely Janet Jackson",
"Everybody Dies (feat. Sean Nicholas Savage) World Brain",
"Come Home Rollee McGill",
"Another Night The Men",
"Baby Where You Are Ted Lucas",
"Ram Dancehall Double Tiger",
"Can You Get to That Funkadelic"
]

toAddVideoIds = []
for song in toAdd:
    songSearch = ytmusic.search(song, "songs")
    firstSong = songSearch[0]
    toAddVideoIds.append(firstSong['videoId'])
    print("Search Term:", song, "\nReturn:", firstSong['title'], "-", firstSong['artists'][0]['name'], "\n")

print(toAddVideoIds)
status = ytmusic.add_playlist_items(playlistId, toAddVideoIds, None, True)
print(status)
