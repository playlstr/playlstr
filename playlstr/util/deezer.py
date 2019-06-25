from .playlist import *

import json

DEEZER_API_URL = 'https://api.deezer.com/'


def deezer_single_track_search(query: str) -> dict:
    result = requests.get('{}/search/track/?q={}&output=json'.format(DEEZER_API_URL, query))
    if result.status_code != 200:
        return {}
    return json.loads(result.text)['data']
