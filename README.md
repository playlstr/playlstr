## [playlstr](http://playlstr.me)
### Features
- Create and share playlists online for free
- Import existing playlists from Spotify
### Planned features
Ordered approximately by expected implementation date (soonest first)
- Easily add/remove tracks, albums, and artists to/from playlists
- Import and export playlists to and from popular streaming services like Spotify, Google Play Music, Deezer, and YouTube
- Export playlists as text files of tracks
- Sync the same playlist across different streaming services
- Granular playlist exporting
    - Exclude specific genres, albums, or artists or explicit tracks
- Build up playlists from other playlists ("sublists")
    - For example, you may have a Hip Hop sublist which is included in your Fav Tracks playlist. You want to share your Fav Tracks playlist with a friend who doesn't like hip-hop, so simply deselect Hip Hop when exporting to get a playlist of Fav Tracks without Hip Hop
- Play playlists in your browser for free with YouTube or Deezer
- Upload local playlist files to import (using filenames to try to find matching tracks)
- Local library support via standalone client or beets plugin
    - Use existing metadata for matching tracks when importing a local playlist file
    - Export playlists using local music files
### Development
- Install Python 3.6+ and PostgreSQL 11.2+
- `pip install -r requirements.txt`
- Create a psql database for playlstr and update DATABASES in `playlstr/settings.py` accordingly
- `python manage.py makemigrations playlstr` and `python manage.py migrate`
