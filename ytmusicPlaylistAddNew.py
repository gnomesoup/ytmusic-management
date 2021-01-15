from ytmusicapi import YTMusic

ytmusic = YTMusic("headers_auth.json")
playlistTitle = "Songs from High Fidelity (2000)"
playlistDescription = "Songs from the original movie with John Cusak"
playlistPrivacyStatus = "PUBLIC"

songsToAdd = [
"Crocodile Rock Elton John",
"Seymour Stein Belle and Sebastian",
"Walking On Sunshine Katrina and the Waves",
"Baby Got Going Liz Phair",
"The River Bruce Springsteen",
"Baby, I Love Your Way Peter Frampton",
"Hyena 1 Goldie",
"I'm Gonna Love You Just A Little More, Babe Barry White",
"Always See Your Face Love",
"Soaring and Boaring Plush",
"Four to the Floor John Etkin-Bell",
"Leave Home The Chemical Brothers",
"Oh! Sweet Nuthin' The Velvet Underground",
"You're Gonna Miss Me The Thirteenth Floor Elevators",
"Little Did I Know Brother JT 3",
"Jacob's Ladder Neil Peart, Geddy Lee and Alex Lifeson",
"I'm Wrong About Everything John Wesley Harding",
"I Can't Stand The Rain Ann Peebles",
"Jesus Doesn't Want Me For A Sunbeam The Vaselines",
"Cold Blooded Old Times Smog",
"On Hold Edith Frost",
"Loopfest Toby Bricheno and Jan Cryka",
"Suspect Device Stiff Little Fingers",
"Robbin's Nest Illinois Jacket",
"Who Loves the Sun The Velvet Underground",
"Dry The Rain The Beta Band",
"Rock Steady Aretha Franklin",
"Shipbuilding Elvis Costello and The Attractions",
"Your Friend and Mine Love",
"Get It Together Grand Funk Railroad",
"Juice (Know the Ledge) Eric B. and Rakim",
"Tonight I'll Be Staying Here With You Johnny Cash with Bob Dylan",
"This India Harbhajhn Singh and Navinder Pal Singh",
"I'm Glad You're Mine Al Green",
"Fallen For You Sheila Nicholls",
"Tread Water De La Soul",
"What's On Your Mind Eric B. and Rakim",
"Doing It Anyway Apartment 26",
"The Inside Game Royal Trux",
"Lo Boob Oscillator Stereolab",
"Good and Strong Sy Smith",
"Chapel of Rest Dick Walter & Diane Nalini",
"The Moonbeam Song Harry Nilsson",
"The Night Chicago Died Mitch Murray and Peter Callander",
"I Get The Sweetest Feeling Jackie Wilson",
"Everybody's Gonna Be Happy The Kinks",
"Mendocino Sie Douglas Quintet",
"The Anti-Circle The Roots & Erykah Badu",
"Homespin Rerun High Llamas",
"Most of the Time Johnny Cash with Bob Dylan",
"Hit the Street Rupert Gregson-Williams & Lorne Balfe",
"I Believe (When I Fall In Love It Will Be Forever) Stevie Wonder",
"My Little Red Book Love",
"We Are the Champions Queen",
"Crimson and Clover Joan Jett & The Blackhearts",
"Let's Get It On Jack Black",
"I Want Candy Bow Wow Wow"
]

videoIds = []
for song in songsToAdd:
    songSearch = ytmusic.search(song, "songs")
    print("Search Term:", song)
    if not songSearch:
        print("Return: None\n")
    else:
        firstSong = songSearch[0]
        videoIds.append(firstSong['videoId'])
        print("Return:", firstSong['title'], "-", firstSong['artists'][0]['name'], "\n")

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print(newPlaylist)