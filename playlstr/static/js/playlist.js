let newTracks = [];
let spotifyResults = [];
let deletedTracks = [];
let newSpotifyTracks = [];
let advancedSearch = false;
let trackSearch = false;
let lastTrackSearchTime = new Date();
let spotifySearches = 0;
const spotifyResultsLimit = 20;

String.prototype.format = String.prototype.f = function () {
    let s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};

function deleteTrack(track_id) {
    let newIndex = newTracks.indexOf(track_id);
    if (newIndex === -1) {
        deletedTracks.push(track_id);
        $("#" + track_id + "track").hide();
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
            url: 'http://' + window.location.host + '/playlist-update/',
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
    } else {
        $('#editControlButtons').css('margin-bottom', '20px');
    }
}

function init() {
    initTrackAutocomplete();
    // Add listener for searching by pressing enter (see https://stackoverflow.com/a/45650898 for why this way)
    document.querySelector("#simpleTrackSearchText").addEventListener("keyup", event => {
        if (event.key !== "Enter") return;
        document.querySelector("#searchDropdownButton").click();
        event.preventDefault();
    });
}

function initTrackAutocomplete() {
    $('#simpleTrackSearchText').on('input', function () {
        let text = $('#simpleTrackSearchText').val();
        if (text.length <= 2 || Date() - lastTrackSearchTime < 1000) return;
        getTrackSearchResults(text);
        lastTrackSearchTime = Date();
    });
    $('#addSuccessDialog').hide();
}

function getTrackSearchResults(term, start = 0, count = 0) {
    $.ajax({
        type: 'POST',
        url: 'http://' + window.location.host + '/track-autocomplete/',
        headers: {'X-CSRFToken': csrfToken},
        data: {'term': term},
        success: function (unparsed) {
            let table_body = $('#trackSearchResultsTBody');
            table_body.empty();
            appendSearchResults(unparsed, table_body);
        },
        error: function () {
            getTrackResultsFail();
        }
    });
}

function appendSearchResults(unparsed_results, search_results_div) {
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

function searchSpotify() {
    let query = advancedSearch ? null : $('#simpleTrackSearchText').val();
    $.ajax({
        type: 'GET',
        url: 'https://api.spotify.com/v1/search',
        headers: {'Authorization': 'Bearer ' + spotifyAccessToken},
        data: {'q': query, 'type': 'track,artist', 'include_external': 'audio', 'limit': spotifyResultsLimit},
        success: function (data) {
            spotifySearches = 1;
            let table_body = $('#trackSearchResultsTBody');
            table_body.empty();
            appendSpotifySearchResults(advancedSearch ? null : data['tracks']['items'], table_body);
        },
        error: function () {
            getTrackResultsFail();
        }
    });
}

function searchSpotifyAgain() {
    let query = advancedSearch ? null : $('#simpleTrackSearchText').val();
    $.ajax({
        type: 'GET',
        url: 'https://api.spotify.com/v1/search',
        headers: {'Authorization': 'Bearer ' + spotifyAccessToken},
        data: {
            'q': query,
            'type': 'track,artist',
            'include_external': 'audio',
            'limit': spotifyResultsLimit,
            'offset': spotifySearches * spotifyResultsLimit
        },
        success: function (data) {
            let table_body = $('#trackSearchResultsTBody');
            appendSpotifySearchResults(advancedSearch ? null : data['tracks']['items'], table_body);
        },
        error: function () {
            getTrackResultsFail();
        }
    });
}

function appendSpotifySearchResults(tracks, table_body) {
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

function toggleTrackSearch() {
    if (trackSearch) {
        $('#addTrackContainer').hide();
        $('#enableTrackSearch').text('Add Tracks +').removeClass('btn-secondary').addClass('btn-primary');
        $('#editControlButtons').css('margin-bottom', '20px');
        trackSearch = false;
    } else {
        $('#addTrackContainer').show();
        $('#enableTrackSearch').text('Add Tracks -').removeClass('btn-primary').addClass('btn-secondary');
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
    } else {
        console.log(newTracks)
    }
}

function showNewTrackDialog() {
    // TODO
}

function exportAsText() {
    // TODO
}

function exportToSpotify() {
    // TODO
}

function downloadTrack(track) {
    // TODO
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
