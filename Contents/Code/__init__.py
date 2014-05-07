import random

from gmusicapi import Webclient, Mobileclient
from gmusicapi.exceptions import AlreadyLoggedIn, NotLoggedIn

ART = 'art-default.jpg'
ICON = 'icon-default.png'

################################################################################

class GMusic(object):
    def __init__(self):
        self.webclient = Webclient(debug_logging=False)
        self.mobileclient = Mobileclient(debug_logging=False)
        self.email = None
        self.password = None
        self.mc_authenticated = False
        self.wc_authenticated = False
        self.authenticated = False
        self.device = None
        self.all_songs = list()
        self.playlists = list()

    def authenticate(self, email=None, password=None):
        if email:
            self.email = email
        if password:
            self.password = password

        try:
            Log("Authenticating mobileclient...")
            self.mc_authenticated = self.mobileclient.login(self.email, self.password)
        except AlreadyLoggedIn:
            self.mc_authenticated = True

        try:
            Log("Authenticating webclient...")
            self.wc_authenticated = self.webclient.login(self.email, self.password)
        except AlreadyLoggedIn:
            self.wc_authenticated = True

        self.authenticated = self.mc_authenticated and self.wc_authenticated

        return self.authenticated

    def get_all_songs(self):
        try:
            self.all_songs = self.mobileclient.get_all_songs()
        except NotLoggedIn:
            if self.authenticate():
                self.all_songs = self.mobileclient.get_all_songs()
            else:
                Log("LOGIN FAILURE")
                return

        return self.all_songs

    def get_all_playlists(self):
        try:
            self.playlists = self.mobileclient.get_all_playlist_ids()
        except NotLoggedIn:
            if self.authenticate():
                self.playlists = self.mobileclient.get_all_playlist_ids()
            else:
                Log("LOGIN FAILURE")
                return

        return self.playlists

    def get_stream_url(self, song_id):
        try:
            stream_url = self.mobileclient.get_stream_url(song_id)
        except NotLoggedIn:
            if self.authenticate():
                stream_url = self.mobileclient.get_stream_url(song_id)
            else:
                Log("LOGIN FAILURE")
                return

        return stream_url

def Start():
    Plugin.AddPrefixHandler('/music/googlemusic', MainMenu, L('Title'), ICON, ART)

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = L('Title')

    DirectoryObject.thumb = R(ICON)

def ValidatePrefs():
    return True

def MainMenu():
    oc = ObjectContainer()

    if not Prefs['email'] or not Prefs['password']:
        oc.add(PrefsObject(title=L('Prefs Title')))
        return oc

    gmusic = GMusicObject()
    if not gmusic and self.authenticated:       # No gmusic object but we did authenticated
        oc.add(PrefsObject(title=L('Prefs Title'), summary=L('No mobile devices registered (registration not yet implemented.)')))
    elif not gmusic:                            # No gmusic object (assume bad password)
        oc.add(PrefsObject(title=L('Prefs Title'), summary=L('Bad Password')))
    else:                                       # Gmusic object
        oc.add(DirectoryObject(key=Callback(PlaylistList), title=L('Playlists')))
        oc.add(DirectoryObject(key=Callback(SongList), title=L('Shuffle All')))
        oc.add(DirectoryObject(key=Callback(ArtistList), title=L('Artists')))
        oc.add(DirectoryObject(key=Callback(AlbumList), title=L('Albums')))
#        oc.add(InputDirectoryObject(key=Callback(SearchResults), title=L('Search'), prompt=L('Search Prompt')))
        oc.add(PrefsObject(title=L('Prefs Title')))

    return oc

def GMusicObject():
    gmusic = GMusic()
    authed = gmusic.authenticate(Prefs['email'], Prefs['password'])
    if authed:
        devices = gmusic.webclient.get_registered_devices()
        for dev in devices:
            if dev['type'] == 'PHONE':
                gmusic.device = dev['id'][2:]     # Chop off 0x part of ID
                break
        if not gmusic.device:
            return None
        return gmusic
    else:
        return None

@route('/music/googlemusic/gettrack', song=dict, gmusic=object)
def GetTrack(song, gmusic=None):
    if not gmusic:
        gmusic = GMusicObject()

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
        index = song.get('track', 0),
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

@route('/music/googlemusic/playlists')
def PlaylistList():
    gmusic = GMusicObject()
    oc = ObjectContainer(title2=L('Playlists'))

    for name, ids in gmusic.mobileclient.get_all_playlist_ids()['user'].iteritems():
        for id in ids:
            oc.add(DirectoryObject(key=Callback(GetTrackList, playlist_id=id, playlist_name=name), title=name))

    return oc

@route('/music/googlemusic/gettracklist', playlist_id=str, artist=str, album=str, query=str)
def GetTrackList(playlist_id=None, playlist_name=None, artist=None, album=None, query=None):
    gmusic = GMusicObject()

    t2 = L('Songs')
    if artist:
        t2 = artist.title()
        if album:
            t2 = t2 + ' - ' + album.title()
        t2 = t2 + ' - ' + L('Songs')
    elif album:
        t2 = album.title() + ' - ' + t2
    elif playlist_name:
       t2 = playlist_name.title() + ' - ' + t2

    oc = ObjectContainer(title2=t2)

    if playlist_id:
        Log('PLAYLIST_ID : ' + playlist_id)
        songs = gmusic.mobileclient.get_playlist_songs(playlist_id)
    else:
        songs = gmusic.get_all_songs()

    for song in songs:
        if artist and song['artist'].lower() != artist:
            continue
        if album and song['album'].lower() != album:
            continue
        track = GetTrack(song, gmusic)
        oc.add(track)

#    oc.objects.sort(key=lambda obj: (obj.album, obj.disc, obj.index))
    oc.objects.sort(key=lambda obj: (obj.album, obj.index))

    return oc

@route('/music/googlemusic/artists')
def ArtistList():
    gmusic = GMusicObject()
    oc = ObjectContainer(title2=L('Artists'))

    songs = gmusic.get_all_songs()

    artists = list()

    for song in songs:
        found = False
        for artist in artists:
            # TODO: Consider using artistId
            if song['artist'] == '' or song['artist'] in artist.itervalues():
                found = True
                break
        if not found:
            artists.append({
                #'name_norm': song['artistNorm']	,
                'id': song['artistId'],
                'name': song['artist'],
            })

    for artist in artists:
        oc.add(ArtistObject(
            #key = Callback(ShowArtistOptions, artist=artist['name_norm']),
            key = Callback(ShowArtistOptions, artist=artist['id']),
            #rating_key = artist['name_norm'],
            rating_key = artist['id'],
            title = artist['name']
            # number of tracks by artist
            # art?
            # number of albums?
        ))

    oc.objects.sort(key=lambda obj: obj.title)

    return oc

@route('/music/googlemusic/artists/options', artist=str)
def ShowArtistOptions(artist):
    oc = ObjectContainer(title2=artist.title())
    oc.add(DirectoryObject(key=Callback(AlbumList, artist=artist), title=L('Albums')))
    oc.add(DirectoryObject(key=Callback(GetTrackList, artist=artist), title=L('All Songs')))

    return oc

@route('/music/googlemusic/albums', artist=str)
def AlbumList(artist=None):
    gmusic = GMusicObject()
    t2 = L('Albums')

    if artist:
        t2 = artist.title() + ' - ' + t2

    oc = ObjectContainer(title2=t2)

    songs = gmusic.get_all_songs() # TODO: Consider returning filtered list from GMusic class

    albums = list()

    for song in songs:
        # TODO: Consider using artistId
        if artist and song['artist'] != artist:
            continue
        found = False
        for album in albums:
            # TODO: Consider using albumId
            if song['album'] == '' or song['album'] in album.itervalues():
                found = True
                break
        if not found:
            print song['title']
            album = {
                #'title_norm': song['albumNorm'],
                'id': song.get('albumId', song['album']),
                'title': song['album'],
                'artist': song['artist'],
                'thumb': song.get('albumArtUrl', None)
            }
            if album['thumb'] is not None:
                album['thumb'] = "http:%s" % album['thumb']
            albums.append(album)

    for album in albums:
        oc.add(AlbumObject(
            #key = Callback(GetTrackList, album=album['title_norm']),
            key = Callback(GetTrackList, album=album['id']),
            #rating_key = album['title_norm'],
            rating_key = album['id'],
            title = album['title'],
            artist = album['artist'],
            thumb = Resource.ContentsOfURLWithFallback(album['thumb'], R(ICON))
	))

    oc.objects.sort(key=lambda obj: obj.title)

    return oc

@route('/music/googlemusic/songs')
def SongList():
    oc = GetTrackList()

    random.shuffle(oc.objects)

    return oc

@route('/music/googlemusic/search', query=str)
def SearchResults(query=None):
    return

@route('/music/googlemusic/songs/play', song=dict)
def PlayAudio(song=None):
    gmusic = GMusicObject()
    song_url = gmusic.get_stream_url(song['id'], self.device)

    return Redirect(song_url)
