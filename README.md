## [playlstr](http://playlstr.me)
### Features
- Create and share playlists online for free
- Import existing playlists from Spotify
- Import local playlists using local audio file metadata with the desktop client
- Upload local playlist files to import (using filenames to try to find matching tracks)
- Export playlists as text files of tracks
- Easily add entire albums to playlists
- Granular playlist exporting
    - Exclude specific genres, albums, or artists or explicit tracks
### Planned features
Ordered approximately by expected implementation date (soonest first)
- Export playlists to streaming services
- Import playlists from other streaming services
- Build up playlists from other playlists ("sublists")
    - For example, you may have a Downtempo sublist which is included in your Fav Tracks playlist. You want to share your Fav Tracks playlist with a friend but keep it upbeat, so simply deselect Downtempo when exporting to get all tracks in Fav Tracks that aren't in Downtempo.
- Export playlists using local music files
- Play tracks in your browser for free with YouTube
- Download tracks for free from Deezer
### Development
- Install Python 3.6+ and PostgreSQL 11.2+ (other PostgreSQL versions may work but are unsupported)
- `pip install -r requirements.txt`
- Create a PostgreSQL user and database for playlstr and update DATABASES in `playlstr/settings.py` accordingly
    - To use default DATABASES:
        - `CREATE DATABASE playlstr;`
        - `CREATE USER playlstruser WITH PASSWORD "playlstrpassword";`
        - `GRANT ALL PRIVILEGES ON DATABASE playlstr TO playlstruser;`
    - Note that in order to run tests you will need to `ALTER USER [username] CREATEDB;` so the testing database can be created
- `python manage.py makemigrations playlstr` and `python manage.py migrate`
- Set up API keys and add them to `playlstr/apikeys.py`
    - [Spotify](https://developer.spotify.com/dashboard/)
        - Add `[domain]/spotify-redirect/` to Redirect URIs in the Spotify API dashboard, then
        
        - ```python
          SPOTIFY_CLIENT_ID = '[your Spotify client id]'
          SPOTIFY_CLIENT_SECRET = '[your Spotify client secret]'
          ```
           
    - [ Google API](https://console.developers.google.com/apis/)
        - ```python 
          SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '[your Google oauth api key]'
          SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '[your Google oauth api secret]'
          ```

