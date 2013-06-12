from gmusicapi import Webclient, AlreadyLoggedIn

MUSIC_PREFIX = '/music/googlemusic'

NAME = L('Title')

ART = 'art-default.jpg'
ICON = 'icon-default.png'

api = Webclient()
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
#        oc.add(DirectoryObject(key=Callback(SongList), title=L('Songs')))
#        oc.add(InputDirectoryObject(key=Callback(SearchResults), title=L('Search'), prompt=L('Search Prompt')))
        oc.add(PrefsObject(title=L('Prefs Title')))

    return oc

#def authenticated(func):
#    def wrapper():
#	try:
#	    func()
#	except:
#	    if GMusic_Authenticate():
#		func()
#	    else:
#		Log("RE-LOGIN FAILURE")
#    return wrapper

def GMusic_Authenticate():
    global api

    try:
        authed = api.login(Prefs['email'], Prefs['password'])
    except AlreadyLoggedIn:
	authed = True

    return authed

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
        #disc = song.get('disc', 0),
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

    try:
        playlists = api.get_all_playlist_ids()
    except:
        if GMusic_Authenticate():
            playlists = api.get_all_playlist_ids()
        else:
            Log("LOGIN FAILURE")
            return

    for name, id in playlists['user'].iteritems():
        oc.add(DirectoryObject(key=Callback(GetTrackList, playlist_id=id), title=name))

    return oc

def GetTrackList(playlist_id=None, artist=None, album=None, query=None):
    oc = ObjectContainer()

    if playlist_id:
        try:
            songs = api.get_playlist_songs(playlist_id)
        except:
            if GMusic_Authenticate():
                songs = api.get_playlist_songs(playlist_id)
            else:
                Log("LOGIN FAILURE")
                return
    else:
        try:
            songs = api.get_all_songs()
        except:
            if GMusic_Authenticate():
                songs = api.get_all_songs()
            else:
                Log("LOGIN FAILURE")
                return

    for song in songs:
        if artist and song['artist'].lower() != artist:
            continue
        if album and song['album'].lower() != album:
            continue
        track = GetTrack(song)
        oc.add(track)

#    oc.objects.sort(key=lambda obj: (obj.album, obj.disc, obj.index))
    oc.objects.sort(key=lambda obj: (obj.album, obj.index))

    return oc

def ArtistList():
    oc = ObjectContainer()

    try:
        songs = api.get_all_songs()
    except:
        if GMusic_Authenticate():
            songs = api.get_all_songs()
        else:
            Log("LOGIN FAILURE")
            return

    artists = list()

    for song in songs:
        found = False
        for artist in artists:
            if song['artist'] == '' or song['artistNorm'] in artist.itervalues():
                found = True
                break
        if not found:
            artists.append({
                'name_norm': song['artistNorm'],
                'name': song['artist'],
            })

    for artist in artists:
        oc.add(ArtistObject(
            key = Callback(GetTrackList, artist=artist['name_norm']),
            rating_key = artist['name_norm'],
            title = artist['name']
            # number of tracks by artist
            # art?
            # number of albums?
        ))

    oc.objects.sort(key=lambda obj: obj.title)

    return oc

def AlbumList():
    oc = ObjectContainer()

    try:
        songs = api.get_all_songs()
    except:
        if GMusic_Authenticate():
            songs = api.get_all_songs()
        else:
            Log("LOGIN FAILURE")
            return

    albums = list()

    for song in songs:
        found = False
        for album in albums:
            if song['album'] == '' or song['albumNorm'] in album.itervalues():
                found = True
                break
        if not found:
            album = {
                'title_norm': song['albumNorm'],
                'title': song['album'],
                'artist': song['artist'],
                'thumb': song.get('albumArtUrl', None)
            }
            if album['thumb'] is not None:
                album['thumb'] = "http:%s" % album['thumb']
            albums.append(album)

    Log(len(albums))
    for album in albums:
        oc.add(AlbumObject(
            key = Callback(GetTrackList, album=album['title_norm']),
            rating_key = album['title_norm'],
            title = album['title'],
            artist = album['artist'],
            thumb = Resource.ContentsOfURLWithFallback(album['thumb'], R(ICON))
	))

    oc.objects.sort(key=lambda obj: obj.title)

    return oc

def SongList():
    return

def SearchResults(query=None):
    return

def PlayAudio(song=None):
    song_url = api.get_stream_url(song['id'])

    return Redirect(song_url)
