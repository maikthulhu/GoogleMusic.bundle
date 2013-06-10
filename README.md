GoogleMusic.bundle
==================

Plex Google Music Plugin

This is the Google Music plugin for Plex.  There are a couple of things to note.

The version of gmusicapi I'm currently using is quite outdated.  An attempt was made to update to 1.2.0, but it is Python 2.5-incompatible.  Plex Media Server for Mac currently runs with Python 2.5, but Linux and Windows are 2.6+.

There are rumors of unifying the PMS plugin framework to 2.7+ across the board, but there is no ETA other than "soonish".

Thus, the goals for this project as of now are thus:
Focus on Windows and Linux development with the latest gmusicapi
Hash out the plugin layout and core functionality
Add Mac support using an older version of gmusicapi and attempt to make the differences transparent
Once Plex unifies the plugin framework I will do the same with the plugin

Current plugin status: *WORKING*
