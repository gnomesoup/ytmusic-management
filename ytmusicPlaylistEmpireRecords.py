from ytmusicapi import YTMusic

ytmusic = YTMusic("headers_auth.json")
playlistTitle = "Empire Records (1995)"
playlistDescription = "All songs from the movie Empire Records"
playlistPrivacyStatus = "PUBLIC"

songsToAdd = [
"The Honeymoon Is Over The Cruel Sea",
"Can't Stop Losing Myself The Dirt Clods",
"I Don't Want to Live Today Ape Hangers",
"Hey Joe The Dirt Clods",
"Til I Hear It from You Gin Blossoms",
"Seems Queen Sarah Saturday",
"Say No More (Mon Amour) Maxwell Caulfield",
"She Walks Poster Children",
"Free The Martinis",
"I Shot the Devil Suicidal Tendencies",
"Money (That's What I Want) Flying Lizards",
"Video Killed the Radio Star The Buggles",
"Ready, Steady, Go The Meices",
"Thorn in My Side Quicksand",
"Little Bastard Ass Ponies",
"I Don't Know Why Sacrilocious",
"Real Real",
"Infinity Mouth Music",
"If You Want Blood (You've Got It) AC/DC",
"Crazy Life Toad the Wet Sprocket",
"The Ballad of El Goodo Evan Dando",
"Snakeface Throwing Muses",
"Romeo and Juliet Dire Straits",
"What You Are Drill",
"How The Cranberries",
"A Girl Like You Edwyn Collins",
"Liar The Cranberries",
"Power Shack Fitz of Depression",
"Bright As Yellow The Innocence Mission",
"Saddam a Go-Go Gwar",
"Rock 'N' Roll / EGA Daniel Johnston",
"Here It Comes Again Please",
"Plowed Sponge",
"Sugarhigh Coyote Shivers",
"This Is the Day The The",
"Vinyl Advice Dead Hot Workshop",
"Dark and Brooding Noah Stone",
"Counting Blue Cars Dishwalla",
"Hardlight Peg Boy",
"Circle of Friends Better Than Ezra",
"Surround You Billy White Trio",
"Chew Toy Fig Dish",
"Back Down Blues Loose Diamonds",
"Nice Overalls Lustre",
"L.A. Girl Adolescents",
"Sorry Sybil Vane",
"Whole Lotta Trouble Cracker",
"Candy Full Tilt Gonzo",
"Tomorrow Mouth Music",
]

videoIds = []
for song in songsToAdd:
    songSearch = ytmusic.search(song, "songs")
    print("Search Term:", song)
    if not songSearch:
        print("   Returned: None\n")
    else:
        firstSong = songSearch[0]
        videoIds.append(firstSong['videoId'])
        print("   Returned:", firstSong['title'], "-", firstSong['artists'][0]['name'], "\n")

newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    playlistDescription,
    playlistPrivacyStatus,
    videoIds)

print("playlistId:", newPlaylist)
print("Searched", len(songsToAdd), "songs")
print("YTMusic matched", len(videoIds), "songs")