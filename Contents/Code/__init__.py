from gmusicapi import Webclient
from gmusicapi.exceptions import AlreadyLoggedIn, NotLoggedIn

ART = 'art-default.jpg'
ICON = 'icon-default.png'

################################################################################

class GMusic(object):
    def __init__(self):
        self.webclient = Webclient()
        self.email = None
        self.password = None
        self.authenticated = False
        self.all_songs = list()
        self.playlists = list()

    def authenticate(self, email=None, password=None):
        if email:
            self.email = email
        if password:
            self.password = password

        try:
            Log("AUTHENTICATING!!!!111 : " + self.email + "," + self.password)
            self.authenticated = self.webclient.login(self.email, self.password)
        except AlreadyLoggedIn:
            self.authenticated = True


        return self.authenticated

    def get_all_songs(self):
        try:
            self.all_songs = self.webclient.get_all_songs()
        except NotLoggedIn:
            if self.authenticate():
                self.all_songs = self.webclient.get_all_songs()
            else:
                Log("LOGIN FAILURE")
                return

        return self.all_songs

    def get_all_playlists(self):
        try:
            self.playlists = self.webclient.get_all_playlist_ids()
        except NotLoggedIn:
            if self.authenticate():
                self.playlists = self.webclient.get_all_playlist_ids()
            else:
                Log("LOGIN FAILURE")
                return

        return self.playlists

    def get_stream_url(self, song_id):
        try:
            stream_url = self.webclient.get_stream_url(song_id)
        except NotLoggedIn:
            if self.authenticate():
                stream_url = self.webclient.get_stream_url(song_id)
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
    if not gmusic:
        oc.add(PrefsObject(title=L('Prefs Title'), summary=L('Bad Password')))
    else:
        oc.add(DirectoryObject(key=Callback(PlaylistList), title=L('Playlists')))
        oc.add(DirectoryObject(key=Callback(ArtistList), title=L('Artists')))
        oc.add(DirectoryObject(key=Callback(AlbumList), title=L('Albums')))
#        oc.add(DirectoryObject(key=Callback(SongList), title=L('Songs')))
#        oc.add(InputDirectoryObject(key=Callback(SearchResults), title=L('Search'), prompt=L('Search Prompt')))
        oc.add(PrefsObject(title=L('Prefs Title')))

    return oc

def GMusicObject():
    gmusic = GMusic()
    authed = gmusic.authenticate(Prefs['email'], Prefs['password'])
    if authed:
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

@route('/music/googlemusic/playlists')
def PlaylistList():
    oc = ObjectContainer()

    for name, id in myclient.get_all_playlists().iteritems():
        oc.add(DirectoryObject(key=Callback(GetTrackList, playlist_id=id), title=name))

    return oc

@route('/music/googlemusic/gettracklist', playlist_id=str, artist=str, album=str, query=str)
def GetTrackList(playlist_id=None, artist=None, album=None, query=None):
    gmusic = GMusicObject()
    oc = ObjectContainer()

    if playlist_id:
        songs = gmusic.webclient.get_playlist_songs(playlist_id)
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
    oc = ObjectContainer()

    songs = gmusic.get_all_songs()

    artists = list()

    for song in songs:
        found = False
        for artist in artists:
            if song['artist'] == '' or song['artistNorm'] in artist.itervalues():
                found = True
                break
        if not found:
            artists.append({
                'name_norm': song['artistNorm']	,
                'name': song['artist'],
            })

    for artist in artists:
        oc.add(ArtistObject(
            key = Callback(ShowArtistOptions, artist=artist['name_norm']),
            rating_key = artist['name_norm'],
            title = artist['name']
            # number of tracks by artist
            # art?
            # number of albums?
        ))

    oc.objects.sort(key=lambda obj: obj.title)

    return oc

@route('/music/googlemusic/artists/options', artist=str)
def ShowArtistOptions(artist):
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(PlayArtistTracks, artist=artist), title=L('All Songs')))
    oc.add(DirectoryObject(key=Callback(AlbumList, artist=artist), title=L('Albums')))
    oc.add(DirectoryObject(key=Callback(GetTrackList, artist=artist), title=L('Songs')))

    return oc

@route('/music/googlemusic/albums', artist=str)
def AlbumList(artist=None):
    gmusic = GMusicObject()
    oc = ObjectContainer()

    songs = gmusic.get_all_songs() # TODO: Consider returning filtered list from GMusic class

    albums = list()

    for song in songs:
        if artist and song['artistNorm'] != artist:
            continue
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

@route('/music/googlemusic/artists/playall', artist=str)
def PlayArtistTracks(artist):
    return

@route('/music/googlemusic/songs')
def SongList():
    return

@route('/music/googlemusic/search', query=str)
def SearchResults(query=None):
    return

@route('/music/googlemusic/songs/play', song=dict)
def PlayAudio(song=None):
    gmusic = GMusicObject()
    song_url = gmusic.get_stream_url(song['id'])

    return Redirect(song_url)
