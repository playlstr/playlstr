import requests
import lxml.html
import re
from playlstr.models import *

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
        result = requests.get(
            button[0].attrib['href'] if button[0].attrib['href'][0] == 'h' else 'http://play.google.com{}'.format(
                button[0].attrib['href']))
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


def xpath_with_class(el: str, cls: str, selector: str = ''):
    return "{}{}[contains(concat(' ', @class, ' '), ' {} ')]".format(selector, el, cls)


def duration_str_to_sec(duration: str) -> int:
    split = duration.split(':')
    return int(split[0]) * 60 + int(split[1])


def gplay_parse_playlist_track(html: lxml.html, fetch_album_name: bool = True) -> Track:
    title = html.xpath(xpath_with_class('td', 'title-col'))[0][0].text_content()
    artist = html.xpath(xpath_with_class('td', 'artist-col'))[0].text_content()
    duration = html.xpath(xpath_with_class('td', 'duration-col'))[0].text_content()
    buy_url = html.xpath("td/div/a")[0].attrib['href']
    ids = buy_url.split('?id=')[1]
    album_id = ids.split('&')[0]
    song_id = ids.split('song-')[1].split('&')[0]
    track = Track.objects.create(title=title, artist=artist, duration=duration_str_to_sec(duration),
                                 gplay_album_id=album_id, gplay_id=song_id)
    if fetch_album_name:
        album_response = requests.get('http://play.google.com/store/music/album?id={}'.format(album_id))
        if album_response.status_code == 200:
            html = lxml.html.fromstring(album_response.content)
            title = html.xpath(
                '/html/body/div[1]/div[4]/c-wiz/div/div[2]/div/div[1]/div/c-wiz[1]/div[1]/div[2]/div/div[1]/div[1]/h1/span')[
                0].text_content()
            if len(title) > 0:
                track.album = title
                track.save()
    return track


def import_gplay_playlist(html: lxml.html, owner_id: str = None) -> str:
    title = html.xpath(xpath_with_class('div', 'title', '//'))[0].text_content()
    tracks = html.xpath(xpath_with_class('tr', 'tracklist-entry', '//'))
    playlist = Playlist.objects.create(name=title)
    if owner_id is not None:
        playlist.owner = PlaylstrUser.objects.get(id=owner_id)
    from playlstr.util.playlist import playlist_add_track
    for track in tracks:
        playlist_add_track(playlist, gplay_parse_playlist_track(track))
    return playlist.playlist_id
