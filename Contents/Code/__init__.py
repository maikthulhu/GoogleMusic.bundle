from gmusicapi.api import Api

MUSIC_PREFIX = '/music/googlemusic'

NAME = L('Title')

ART = 'art-default.jpg'
ICON = 'icon-default.png'

api = Api()
################################################################################

def Start():
    Plugin.AddPrefixHandler(MUSIC_PREFIX, MainMenu, NAME, ICON, ART)

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME

    DirectoryObject.thumb = R(ICON)
    
def ValidatePrefs():
    return True

def MainMenu():
    oc = ObjectContainer()

    # Borrowed menu display based on prefs/auth from Pandora plugin
    # https://github.com/plexinc-plugins/Pandora.bundle/
    if 'GMusicConnection' not in Dict:
        Dict['GMusicConnection'] = {}

    if not Prefs['email'] or not Prefs['password']:
        oc.add(PrefsObject(title=L('Prefs Title')))
        return oc
    elif 'authed' in Dict['GMusicConnection']:
        if Dict['GMusicConnection']['authed']:
            authed = Dict['GMusicConnection']['authed']
        else:
            authed = GMusic_Authenticate()
    else:
        authed = GMusic_Authenticate()

    if not authed:
        oc.add(PrefsObject(title=L('Prefs Title'), summary=L('Bad Password')))
    else:
        oc.add(DirectoryObject(key=Callback(PlaylistList), title=L('Playlists')))
        oc.add(DirectoryObject(key=Callback(ArtistList), title=L('Artists')))
        oc.add(DirectoryObject(key=Callback(AlbumList), title=L('Albums')))
        oc.add(DirectoryObject(key=Callback(SongList), title=L('Songs')))
        oc.add(InputDirectoryObject(key=Callback(SearchResults), title=L('Search'), prompt=L('Search Prompt')))
        oc.add(PrefsObject(title=L('Prefs Title Change')))

    return oc

def GMusic_Authenticate():
    global api
    authed = api.login(Prefs['email'], Prefs['password'])

    if authed:
        return True
    else:
        return False

def GetTrack(song):
    try:
	album_art_url = 'http:%s' % song['albumArtUrl']
    except:
	album_art_url = None

    track = TrackObject(
        key = song['id'],
        rating_key = song['id'],
        title = song['title'],
        album = song['album'],
	artist = song['artist'],
	duration = song['durationMillis'],
	index = song['track'],
	thumb = Resource.ContentsOfURLWithFallback(album_art_url, R(ICON)),
	items = [
	    MediaObject(
		parts = [PartObject(key=Callback(PlayAudio, song=song, ext='mp3'))], # ext='mp3' is apparently EXTREMELY CRITICAL
	        container = Container.MP3,
		audio_codec = AudioCodec.MP3
	    )
	]
    )

    return track

def PlaylistList():
    oc = ObjectContainer()

    playlists = api.get_all_playlist_ids()

    for name, id in playlists['user'].iteritems():
        oc.add(DirectoryObject(key=Callback(Playlist, id=id), title=name))

    return oc

def Playlist(id=None):
    oc = ObjectContainer()

    songs = api.get_playlist_songs(id)

    for song in songs:
        track = GetTrack(song)
	oc.add(track)

    return oc

def ArtistList():
    oc = ObjectContainer()

    songs = api.get_all_songs()
    artists = list()

    for song in songs:
        if song['artist'] not in artists:
            artists.append(song['artist'])
    
    artists.sort()

    for artist in artists:
	if artist != '':
	    oc.add(ArtistObject(
		key = Callback(ArtistSongs, artist=artist),
		rating_key = artist,
		title = artist
		# number of tracks by artist
		# art?
		# number of albums?
	        )
	    )
    
    return oc

def ArtistSongs(artist=None):
    oc = ObjectContainer()

    songs = api.get_all_songs()

    # sort songs by album
    # using the code below twice (except for artist check), make it generic
    for song in songs:
        if song['artist'] == artist:
	    track = GetTrack(song)
	    oc.add(track)

    return oc

def AlbumList():
    return

def SongList():
    return

def PlayAudio(song=None):
    song_url = api.get_stream_url(song['id'])

    return Redirect(song_url)

def SearchResults(query=None):
    return
