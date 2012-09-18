from gmusicapi.api import Api

PREFIX = '/music/googlemusic'

NAME = "Google Music"

ART = 'art-default.jpg'
ICON = 'icon-default.png'

################################################################################

def Start():
    Log.Debug("This is a test")
    # Init
    Plugin.AddPrefixHandler(PREFIX, MainMenu, NAME, ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode = "List", mediaType = "items")

    # Plugin artwork setup
    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    MediaContainer.viewGroup = "List"
    DirectoryItem.thumb = R(ICON)

def ValidatePrefs():
    return

def MainMenu():
    dir = MediaContainer(viewGroup="InfoList")

    if 'GMusicConnection' not in Dict:
        Dict['GMusicConnection'] = {}

    if not Prefs['gmusic_user'] or not Prefs['gmusic_pass']:
        dir.Append(PrefsItem(title=L("Prefs Title")))
        return dir
    elif 'authed' in Dict['GMusicConnection']:
        if Dict['GMusicConnection']['authed']:
            authed = Dict['GMusicConnection']['authed']
        else:
            authed = GMusic_Authenticate()
    else:
        authed = GMusic_Authenticate()

    if not authed:
        dir.Append(PrefsItem(title=L("Prefs Title"), summary=L("Bad Password")))
    else:
        dir.Append(
            Function(
                DirectoryItem(
                    PlaylistList,
                    title=L("Playlists")
                )
            )
        )
        dir.Append(Function(DirectoryItem(ArtistList, title=L("Artists"))))
        dir.Append(Function(DirectoryItem(AlbumList, title=L("Albums"))))
        dir.Append(Function(DirectoryItem(SongList, title=L("Songs"))))
        dir.Append(Function(InputDirectoryItem(Search, title=L("Search"))))
        dir.Append(PrefsItem(title=L("Prefs Title Change")))

    return dir

def GMusic_Authenticate():
    api = Api()
    authed = api.login(Prefs['gmusic_user'], Prefs['gmusic_pass'])

    if authed:
        return True
    else:
        return False

def PlaylistList(sender):
    return

def AristList(sender):
    return

def AlbumList(sender):
    return

def SongList(sender):
    return

def Search(sender, query=None):
    return
