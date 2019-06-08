import argparse
from json import dumps

import importer
from requests import post

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import playlist to playlstr')
    parser.add_argument('playlist', type=str, nargs='+', help='A playlist to import')
    parser.add_argument('-am', '--add-missing', action='store_true', help='Add tracks whose local file doesn\'t exist')
    parser.add_argument('-hash', '--hash', action='store_true', help='Use file hashes for track matching')
    parser.add_argument('-u', '--user', type=int, action='store', default=-1,
                        help='User id to associate imported playlists with')
    parser.add_argument('-xt', '--m3u-ext', action='store_true',
                        help='Use duration, artist, and track information from extended m3u instead of file metadata')
    parser.add_argument('--url', action='store', default='http://127.0.0.1:8000/', help='Website url')
    args = parser.parse_args().__dict__
    # Ensure trailing slash
    if args['url'][-1] == '/':
        args['url'] = args['url'][:-1]
    for playlist in args['playlist']:
        split_dot = playlist.split('.')
        filetype = split_dot[-1]
        name = split_dot[0]
        try:
            parse_method = getattr(importer, 'import_{}'.format(filetype))
        except AttributeError:
            print('Invalid filetype {}'.format(filetype))
            continue
        with open(playlist) as file:
            tracks = parse_method(file, args)
        response = post('{}/client-import/'.format(args['url']), data={'playlist_name': name, 'tracks': dumps(tracks)})
        if response.status_code != 200:
            print('Error adding {}: {}'.format(playlist, response.reason))
        else:
            print('Imported {}: {}/list/{}/'.format(playlist, args['url'], response.text))
