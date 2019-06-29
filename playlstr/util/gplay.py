import requests
import lxml.html
import re

GPLAY_SEARCH_URL = 'https://play.google.com/store/search?c=music&q='
GPLAY_SEARCH_NO_RESULTS = 'We couldn\'t find anything for your search'


def gplay_search(query: str, search_type='track') -> list:
    """
    Get the results of type search_type from searching Google Play Music for query
    :param query: query to search for
    :param search_type: type of search. Should be one of 'track', 'album', or 'artist'
    :return: list of dicts of search results
    """
    # First get the base page that comes from searching the query
    result = requests.get(GPLAY_SEARCH_URL + query)
    if result.status_code != 200 or GPLAY_SEARCH_NO_RESULTS in result.text:
        return []
    html = lxml.html.fromstring(result.content)
    if search_type == 'track':
        if not html.xpath('.//h2[text()="Songs"]'):
            return []
        # Get the url of the button to go to the search results of type search_type
        button = html.xpath('.//h2[text()="Songs"]/../../following-sibling::div/a')
        # If there is no button to load more songs try to parse songs on the current page
        if not button or 'href' not in button[0].attrib or not button[0].attrib['href']:
            return gplay_parse_track_search(html)
        # Get results and parse them
        result = requests.get(button[0].attrib['href'])
        if result.status_code != 200:
            return []
        return gplay_parse_track_search(lxml.html.fromstring(result.content))
    elif search_type == 'album':
        if not html.xpath('.//h2[text()="Albums"]'):
            return []
        # Get the url of the button to go to the search results of type search_type
        button = html.xpath('.//h2[text()="Albums"]/../../following-sibling::div/a')
        if not button or 'href' not in button[0].attrib or not button[0].attrib['href']:
            return gplay_parse_album_search(html)
        # Get results and parse them
        result = requests.get(button[0].attrib['href'])
        if result.status_code != 200:
            return []
        return gplay_parse_album_search(lxml.html.fromstring(result.content))
    elif search_type == 'artist':
        if not html.xpath('.//h2[text()="Artists"]'):
            return []
        # Get the url of the button to go to the search results of type search_type
        button = html.xpath('.//h2[text()="Artists"]/../../following-sibling::div/a')
        if not button or 'href' not in button[0].attrib or not button[0].attrib['href']:
            return gplay_parse_artist_search(html)
        # Get results and parse them
        result = requests.get(button[0].attrib['href'])
        if result.status_code != 200:
            return []
        return gplay_parse_artist_search(lxml.html.fromstring(result.content))
    else:
        raise ValueError('Invalid search type {}'.format(search_type))


def gplay_parse_track_search(html: lxml.html) -> list:
    print('parsing track search')
    tracks = []
    for div in html.xpath('//div/c-wiz/c-wiz/c-wiz/div/div/div/c-wiz/div/div/div/div/div/div/div/div'):
        if not div[0].xpath('./a'):
            continue
        ids = div[0].xpath('./a')[0].attrib['href'].split('/')[3]
        matches = re.search(r'^album\?id=(.*)&tid=song-(.*)$', ids)  # Album and song ids
        tracks.append({'title': div[0].attrib['title'], 'artist': div[1][0][0].text, 'album_id': matches.group(1),
                       'id': matches.group(2)})
    return tracks


def gplay_parse_album_search(html: lxml.html) -> list:
    albums = []
    for div in html.xpath('//c-wiz/c-wiz/div/div/div/c-wiz/div/div/div/div/div/div/div/div'):
        if not div[0].xpath('./a'):
            continue
        id = div[0].xpath('./a')[0].attrib['href'].split('?id=')[1]
        albums.append({'name': div[0].attrib['title'], 'artist': div[1][0][0].text, 'album_id': id})
    return albums


def gplay_parse_artist_search(html: lxml.html) -> list:
    artists = []
    for div in html.xpath('//c-wiz/c-wiz/c-wiz/div/div/div/c-wiz'):
        a = div.xpath('./div/div/div/a')[0]
        artists.append({'name': a[0].text, 'id': a.attrib['href'].split('?id=')[1]})
    return artists
