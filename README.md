## [playlstr](http://playlstr.me)
### Features
- Create and share playlists online for free
- Import existing playlists from Spotify
- Import local playlists using local audio file metadata with the desktop client
### Planned features
Ordered approximately by expected implementation date (soonest first)
- Easily add/remove entire albums and artists to/from playlists
- Import playlists from other streaming services such as Google Play Music, Deezer, and YouTube
- Export playlists to streaming services
- Export playlists as text files of tracks
- Granular playlist exporting
    - Exclude specific genres, albums, or artists or explicit tracks
- Build up playlists from other playlists ("sublists")
    - For example, you may have a Downtempo sublist which is included in your Fav Tracks playlist. You want to share your Fav Tracks playlist with a friend but keep it upbeat, so simply deselect Downtempo when exporting to get all tracks in Fav Tracks that aren't in Downtempo.
- Play playlists in your browser for free with YouTube or Deezer
- Upload local playlist files to import (using filenames to try to find matching tracks)
- Export playlists using local music files
### Development
- Install Python 3.6+ and PostgreSQL 11.2+ (other PostgreSQL versions may work but are unsupported)
- `pip install -r requirements.txt`
- Create a PostgreSQL user and database for playlstr and update DATABASES in `playlstr/settings.py` accordingly
    - To use default DATABASES:
        - `CREATE DATABASE playlstr;`
        - `CREATE USER playlstruser WITH PASSWORD playlstrpassword;`
        - `GRANT ALL PRIVILEGES ON DATABASE playlstr TO playlstruser;`
    - Note that in order to run tests you will need to `ALTER USER [username] CREATEDB;` so the testing database can be created
- `python manage.py makemigrations playlstr` and `python manage.py migrate`

