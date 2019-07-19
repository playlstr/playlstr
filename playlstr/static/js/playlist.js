let spotifyResults = [];
let deletedTracks = [];
let newTracks = [];
let newSpotifyTracks = [];
let advancedSearch = false;
let trackSearch = false;
let lastTrackSearchTime = new Date();
let spotifySearches = 0;
const spotifyResultsLimit = 20;
let albumSearch = false;

/**
 * Remove track from playlist body and add it for deletion on save
 * @param track_id track id to delete
 */
function deleteTrack(track_id) {
    let newIndex = newTracks.indexOf(track_id);
    if (newIndex === -1) {
        deletedTracks.push(track_id);
        $('#{0}track'.format(track_id)).hide();
    } else {
        newTracks.splice(newIndex, 1);
        $('#newTrack' + track_id).remove();
        if (newTracks.length === 0 && newSpotifyTracks.length === 0) {
            $('#newTracksWarning').hide();
        }

    }
}

function enterEditMode() {
    $('#editButton').hide();
    $('#trackSearchButtons').show();
    $('.rm-btn-container').show();
    $('#playlistName').attr('contenteditable', true).addClass('editable-title');
    $('#trackSearchTitle').show();
}

function exitEditMode(save = false) {
    $('#newTracksWarning').hide();
    $('#trackSearchTitle').hide();
    $('#addTrackContainer').hide();
    trackSearch = false;
    $('#editButton').show();
    $('#trackSearchButtons').hide();
    $('#playlistName').attr('contenteditable', false).removeClass('editable-title');
    $('.rm-btn-container').hide();
    if (save) {
        if (document.cookie.length === 0) return;
        $.ajax({
            type: 'POST',
            url: getPathUrl('/playlist-update/'),
            headers: {'X-CSRFToken': csrfToken},
            data: {
                'playlist': playlist_id,
                'added': JSON.stringify(newTracks),
                'removed': JSON.stringify(deletedTracks),
                'spotify_new': JSON.stringify(newSpotifyTracks),
                'spotify_token': spotifyAccessToken,
                'playlist_name': $('#playlistName').text()
            },
            success: showUpdateSuccess,
            error: showUpdateFailure
        });
    }
    $('#editControlButtons').css('margin-bottom', '20px');
    $('#enableTrackSearch').text('Add +').removeClass('btn-secondary').addClass('btn-primary');
    trackSearch = false;
}

function init() {
    initTrackAutocomplete();
    // Add listener for searching by pressing enter (see https://stackoverflow.com/a/45650898 for why this way)
    document.querySelector("#simpleTrackSearchText").addEventListener("keyup", event => {
        if (event.key !== "Enter") return;
        document.querySelector("#searchDropdownButton").click();
        event.preventDefault();
    });
    $(document).ready(function () {
        setSearchTypeFromHtml();
    });
}

function initTrackAutocomplete() {
    $('#simpleTrackSearchText').on('input', function () {
        let text = $('#simpleTrackSearchText').val();
        if (text.length <= 2 || Date() - lastTrackSearchTime < 1000) return;
        if (!albumSearch) {
            getTrackSearchResults(text);
            lastTrackSearchTime = Date();
        }
    });
    $('#addSuccessDialog').hide();
}

/**
 * Get the tracks matching term from the server
 * @param term term to search for
 * @param start index into results from which to start
 * @param count how many tracks to return
 */
function getTrackSearchResults(term, start = 0, count = 0) {
    $.ajax({
        type: 'POST',
        url: getPathUrl('/track-autocomplete/'),
        headers: {'X-CSRFToken': csrfToken},
        data: {'term': term},
        success: function (unparsed) {
            let table_body = $('#trackSearchResultsTBody');
            table_body.empty();
            appendTrackSearchResults(unparsed, table_body);
        },
        error: getTrackResultsFail
    });
}

/**
 * Append results of server track search to track search results
 * @param unparsed_results unparsed json array of results
 * @param search_results_div div to append the tracks to
 */
function appendTrackSearchResults(unparsed_results, search_results_div) {
    let results = JSON.parse(unparsed_results);
    if (results.length === 0) {
        $('#noResultsInfo').show();
    } else {
        $('#noResultsInfo').hide();
        for (let i = 0; i < results.length; i++) {
            let track = results[i];
            let new_row = '<tr class="track-search-results" id="{0}search"><td>{1}</td><td>{2}</td><td>{3}</td><td><button class="btn btn-primary" onclick="addTrack({0}, \'{1}\', \'{2}\', \'{3}\')">+</button></td></tr>'.format(
                track.id, track.title, track.artist, track.album);
            $(search_results_div).append(new_row);
        }
    }
}


function addTrack(track_id, title, artist, album) {
    newTracks.push(track_id);
    $('#simpleTrackSearchText').val('');
    $('#simpleTrackSearchText').focus();
    $('#trackListTBody').append('<tr id="newTrack{0}"><td><a href="/track/{0}">{1}</a></td><td>{2}</td><td>{3}</td><td><i class="fa fa-certificate text-warning"></i></td><td class="rm-btn-container" style="display: block;"><button type="button" class="btn btn-outline-danger" onclick="deleteTrack({0});">&#10060;</button></td></tr>'.format(
        track_id, title, artist, album));
    showAddSuccess();
    $('#newTracksWarning').show();
}

function showAddSuccess() {
    $('#addSuccessDialog').fadeIn(1000).fadeOut(1000);
}

function toggleAdvancedTrackSearch() {
    if (advancedSearch) {
        $('#advancedTrackSearch').hide();
        $('#simpleTrackSearch').show();
        advancedSearch = false;
    } else {
        $('#advancedTrackSearch').show();
        $('#simpleTrackSearch').hide();
        advancedSearch = true;
    }
}

function showUpdateSuccess() {
    location.reload();
}

function showUpdateFailure(data) {
    // TODO
    console.log('Fail to update');
    console.log(data);
}

function getTrackResultsFail(data) {
    // TODO
    console.log('failed to get spotify results');
}

/**
 * Search for current search text on Spotify and update track search results accordingly
 * Should only be called once per search term
 */
function searchSpotify() {
    let query = advancedSearch ? null : $('#simpleTrackSearchText').val();
    $.ajax({
        type: 'GET',
        url: 'https://api.spotify.com/v1/search',
        headers: {'Authorization': 'Bearer ' + spotifyAccessToken},
        data: {
            'q': query,
            'type': albumSearch ? 'album' : 'track',
            'include_external': 'audio',
            'limit': spotifyResultsLimit
        },
        success: function (data) {
            spotifySearches = 1;
            let table_body = $('#trackSearchResultsTBody');
            table_body.empty();
            if (albumSearch) {
                appendSpotifyAlbumSearchResults(advancedSearch ? null : data['albums']['items'], table_body);
            } else {
                appendSpotifyTrackSearchResults(advancedSearch ? null : data['tracks']['items'], table_body);
            }
        },
        error: function () {
            getTrackResultsFail();
        }
    });
}

/**
 * Get more results from spotify and append them to the current track search results
 * Should only be called after searchSpotify() has been called once
 */
function searchSpotifyAgain() {
    let query = advancedSearch ? null : $('#simpleTrackSearchText').val();
    $.ajax({
        type: 'GET',
        url: 'https://api.spotify.com/v1/search',
        headers: {'Authorization': 'Bearer ' + spotifyAccessToken},
        data: {
            'q': query,
            'type': albumSearch ? 'album' : 'track',
            'include_external': 'audio',
            'limit': spotifyResultsLimit,
            'offset': spotifySearches * spotifyResultsLimit
        },
        success: function (data) {
            spotifySearches++;
            let table_body = $('#trackSearchResultsTBody');
            if (albumSearch) {
                appendSpotifyAlbumSearchResults(advancedSearch ? null : data['albums']['items'], table_body);
            } else {
                appendSpotifyTrackSearchResults(advancedSearch ? null : data['tracks']['items'], table_body);
            }
        },
        error: function () {
            getTrackResultsFail();
        }
    });
}

function appendSpotifyTrackSearchResults(tracks, table_body) {
    if (tracks.length === 0) {
        $('#noResultsInfo').show();
    } else {
        $('#noResultsInfo').hide();
        for (let i = 0; i < tracks.length; i++) {
            spotifyResults.push(tracks[i]);
            let track = tracks[i];
            let new_row = '<tr class="track-search-results" id="{0}search"><td>{1}</td><td>{2}</td><td>{3}</td><td><button class="btn btn-primary" onclick="addSpotifyTrack(\'{0}\', \'{1}\', \'{2}\', \'{3}\');">+</button></td></tr>'.format(
                track.id, track.name, track.artists[0].name, track.album.name);
            $(table_body).append(new_row);
        }
        $('#moreSpotifyResults').remove();
        $(table_body).append('<tr id="moreSpotifyResults"><td colspan="4"><center><a href="#" onclick="searchSpotifyAgain(); return false;">More...</a></center></td></tr>');
    }
}

function appendSpotifyAlbumSearchResults(albums, table_body) {
    if (albums.length === 0) {
        $('#noResultsInfo').show();
    } else {
        $('#noResultsInfo').hide();
        for (let i = 0; i < albums.length; i++) {
            spotifyResults.push(albums[i]);
            let album = albums[i];
            let new_row = '<tr class="track-search-results" id="{0}search"><td>{1}</td><td>{2}</td><td><button class="btn btn-primary" onclick="addSpotifyAlbum(\'{0}\');">+</button></td></tr>'.format(
                album.id, album.name, album.artists[0].name);
            $(table_body).append(new_row);
        }
        $('#moreSpotifyResults').remove();
        $(table_body).append('<tr id="moreSpotifyResults"><td colspan="3"><center><a href="#" onclick="searchSpotifyAgain(); return false;">More...</a></center></td></tr>');
    }

}

function toggleTrackSearch() {
    if (trackSearch) {
        $('#addTrackContainer').hide();
        $('#enableTrackSearch').text('Add +').removeClass('btn-secondary').addClass('btn-primary');
        $('#editControlButtons').css('margin-bottom', '20px');
        trackSearch = false;
    } else {
        $('#addTrackContainer').show();
        $('#enableTrackSearch').text('Add -').removeClass('btn-primary').addClass('btn-secondary');
        $('#editControlButtons').css('margin-bottom', '0px');
        trackSearch = true;
    }
}

function addSpotifyTrack(spotify_id, title, artist, album) {
    newSpotifyTracks.push(spotify_id);
    $('#newTracksWarning').show();
    let trackHtml = '<tr class="spotify-track" id="newTrack{0}"><td>{1}</td><td>{2}</td><td>{3}</td><td><i class="fa fa-certificate text-warning" ></i></td><td class="rm-btn-container" style="display: block;"><button type="button" class="btn btn-outline-danger" onclick="deleteNewSpotifyTrack(\'{0}\');">&#10060;</button></td></tr>'.format(spotify_id, title, artist, album);
    $('#trackListTBody').append(trackHtml);
    showAddSuccess();
}

function deleteNewSpotifyTrack(spotify_id) {
    console.log(spotify_id);
    $('#newTrack' + spotify_id).remove();
    let index = newSpotifyTracks.indexOf(spotify_id);
    if (index !== -1) newSpotifyTracks.splice(index, 1);
    if (newTracks.length === 0 && newSpotifyTracks.length === 0) {
        $('#newTracksWarning').hide();
    }
}


function searchDefault() {
    searchPlaylstr();
    if ($('#trackSearchResultsTBody > tr').length === 0) {
        searchSpotify();
    }
}

function searchPlaylstr() {
    // TODO
}

function setSearchTypeFromHtml() {
    let select = document.getElementById('searchTypeSelect');
    switch (select.options[select.selectedIndex].value) {
        case 'track':
            setSearchTypeTrack();
            break;
        case 'album':
            setSearchTypeAlbum();
            break;
        default:
            console.log('Invalid search type selected');
            return;
    }
}

function setSearchTypeTrack() {
    albumSearch = false;
    $('#searchTitleColumn').show();
}

function setSearchTypeAlbum() {
    albumSearch = true;
    $('#searchTitleColumn').hide();
}

function addSpotifyAlbum(spotify_id) {
    // TODO
    console.log(spotify_id);
    $.ajax({
        type: 'GET',
        url: 'https://api.spotify.com/v1/albums/' + spotify_id,
        headers: {'Authorization': 'Bearer ' + spotifyAccessToken},
        success: function (unparsed) {
            appendSpotifyAlbumTracks(unparsed);
        },
        error: function (data) {
            // TODO
            console.log('error adding album {}'.format(spotify_id));
        }
    });
}

function appendSpotifyAlbumTracks(unparsed_album) {
    let album = unparsed_album;
    if (album.tracks.items.length === 0) return;
    // TODO support multiple pages of tracks
    let trackHtml = '';
    for (let i = 0; i < album.tracks.items.length; i++) {
        let track = album.tracks.items[i];
        // Check if track is already in the playlist
        if (document.getElementById(track.id) !== null || document.getElementById(track.id + 'SpotifyButton') !== null) continue;
        newSpotifyTracks.push(track.id);
        trackHtml += '<tr class="spotify-track" id="newTrack{0}"><td>{1}</td><td>{2}</td><td>{3}</td><td><i class="fa fa-certificate text-warning" ></i></td><td class="rm-btn-container" style="display: block;"><button type="button" class="btn btn-outline-danger" onclick="deleteNewSpotifyTrack(\'{0}\');">&#10060;</button></td></tr>'.format(track.id, track.name, track.artists[0].name, album.name);
        $('#newTracksWarning').show();
    }
    $('#trackListTBody').append(trackHtml);
    showAddSuccess();
}

function createNewTrack() {
    let new_track = {'title': $('#newTrackTitle').val()};
    let buf = $('#newTrackArtist').val();
    if (!buf.empty) new_track['artist'] = buf;
    buf = $('#newTrackAlbum').val();
    if (!buf.empty) new_track['album'] = buf;
    buf = $('#newTrackYear');
    if (!buf.empty) new_track['release_date'] = buf;
    buf = $('#newTrackNumber');
    if (!buf.empty) new_track['track_number'] = buf;
    $.ajax({
        type: 'POST',
        url: getPathUrl('/create-track/'),
        headers: {'X-CSRFToken': csrfToken},
        data: new_track,
        success: newTrackCreateResponse,
        error: newTrackCreateFail
    });
}

function newTrackCreateResponse(response) {
    // If server returned a track id then show success message and add that new track
    let info = response.split('\n');
    if (info[0] === 'similar') {
        suggestSimilarTrack(info.slice(1));
    } else {
        $('#createTrackModal').modal('hide').find(':input').each(function () {
            $(this).val('');
        });
        addTrack(info[0], info[1], info[2], info[3]);
    }
}

function suggestSimilarTrack(info) {
    // TODO
}

function newTrackCreateFail() {
    // TODO
    console.log('Error creating track');
}

