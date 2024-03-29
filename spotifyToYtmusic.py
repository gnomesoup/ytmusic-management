from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from secretsFile import spotifyClientID, spotifyClientSecret
from ytmusicapi import YTMusic
from ytmusicFunctions import GetSongVideoIds, UpdatePlaylist

# Sex Education Soundtrack
# https://open.spotify.com/playlist/0SmKzbbBAmspl0GCiETzYp

spotifyPlayistId = "0SmKzbbBAmspl0GCiETzYp"

print("Creating a YouTube Music Playlist from a Spotify Playlist")
ytmusic = YTMusic("oauth.json")

scc = SpotifyClientCredentials(spotifyClientID, spotifyClientSecret)
sp = spotipy.Spotify(client_credentials_manager=scc)

spotifyPlaylist = sp.playlist(spotifyPlayistId)
tracks = spotifyPlaylist['tracks']
trackResults = tracks['items']
while tracks['next']:
    tracks = sp.next(tracks)
    trackResults.extend(tracks['items'])
songArtistSearchList = []
for track in trackResults:
    trackInfo = track['track']
    title = trackInfo['name']
    artist = trackInfo['artists'][0]['name']
    songArtistSearchList.append(f"{title} {artist}")

songsToAdd = GetSongVideoIds(ytmusic, songArtistSearchList)
playlistTitle = spotifyPlaylist['name']
playlistDescription = "Imported from a spotify playlist"
newPlaylist = ytmusic.create_playlist(
    playlistTitle,
    description="",
    privacy_status="PUBLIC"
)
if UpdatePlaylist(
    ytmusic,
    newPlaylist,
    songsToAdd,
    description=playlistDescription
):
    print(f"Successfully created {playlistTitle} playlist.")
else:
    print("There was an error creating the playlist.")