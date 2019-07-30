## [playlstr](http://playlstr.me)
### Features
- Create and share playlists online for free
- Import existing playlists from Spotify or Google Play
- Import local playlists using local audio file metadata with the [desktop client](http://github.com/git-uname/playlstr-client)
- Upload local playlist files to import (using filenames to try to find matching tracks)
- Export playlists as list of tracks
- Export playlists to Spotify
- Easily add entire albums to playlists
- Granular playlist exporting
    - Exclude specific genres, albums, or artists or explicit tracks
### Planned features
Ordered approximately by expected implementation date (soonest first)
- Support for more streaming services
- Build up playlists from other playlists ("sublists")
- Export to local files with the [desktop client](http://github.com/git-uname/playlstr-client)
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

