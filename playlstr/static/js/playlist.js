let newTracks = [];
let spotifyResults = [];
let deletedTracks = [];
let newSpotifyTracks = [];
let advancedSearch = false;
let trackSearch = false;
let lastTrackSearchTime = new Date();

String.prototype.format = String.prototype.f = function () {
    var s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};

function deleteTrack(track_id) {
    deletedTracks.push(track_id);
    $("#" + track_id + "track").hide();
}

function enterEditMode() {
    $('#editButton').hide();
    $('#saveButton').show();
    $('#cancelButton').show();
    $('.rm-btn-container').show();
    $('#playlistName').attr('contenteditable', true).addClass('editable-title');
    $('#trackSearchTitle').show();
}

function exitEditMode(save = false) {
    $('#trackSearchTitle').hide();
    $('#addTrackContainer').hide();
    trackSearch = false;
    $('#editButton').show();
    $('#saveButton').hide();
    $('#cancelButton').hide();
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
    }
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
    for (let i = 0; i < results.length; i++) {
        let track = results[i];
        let new_row = '<tr class="track-search-results" id="{0}search"><td>{1}</td><td>{2}</td><td>{3}</td><td><button class="btn btn-primary" onclick="addTrack({0}, \'{1}\', \'{2}\', \'{3}\')">+</button></td></tr>'.format(
            track.id, track.title, track.artist, track.album);
        $(search_results_div).append(new_row);
    }
}

function addTrack(track_id, title, artist, album) {
    newTracks.push(track_id);
    $('#simpleTrackSearchText').val('');
    $('#simpleTrackSearchText').focus();
    $('#trackListTBody').append('<tr><td><a href="/track/{0}">{1}</a></td><td>{2}</td><td>{3}</td><td><button type="button" class="btn" style="border: 1px solid black;">&#9654; Play</button></td><td class="rm-btn-container" style="display: block;"><button type="button" class="btn" style="border: 1px solid red;" onclick="deleteTrack({0})">&#10060;</button></td></tr>'.format(
        track_id, title, artist, album));
    showAddSuccess();
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
    // TODO
}

function showUpdateFailure() {
    // TODO
}

function getTrackResultsFail() {
    // TODO
}

function getSpotifyResults() {
    let query = advancedSearch ? null : $('#simpleTrackSearchText').val();
    $.ajax({
        type: 'GET',
        url: 'https://api.spotify.com/v1/search',
        headers: {'Authorization': 'Bearer ' + spotifyAccessToken},
        data: {'q': query, 'type': 'track,artist,album', 'include_external': 'audio'},
        success: function (data) {
            let table_body = $('#trackSearchResultsTBody');
            table_body.empty();
            appendSpotifySearchResults(advancedSearch ? null : data['tracks']['items'], table_body);
        },
        error: function () {
            getTrackResultsFail();
        }
    });

}

function appendSpotifySearchResults(tracks, table_body) {
    for (let i = 0; i < tracks.length; i++) {
        spotifyResults.push(tracks[i]);
        let track = tracks[i];
        let new_row = '<tr class="track-search-results" id="{0}search"><td>{1}</td><td>{2}</td><td>{3}</td><td><button class="btn btn-primary" onclick="addSpotifyTrack({0}, \'{1}\', \'{2}\', \'{3}\')">+</button></td></tr>'.format(
            track.id, track.name, track.artists[0].name, track.album.name);
        $(table_body).append(new_row);
    }
}

function toggleTrackSearch() {
    if (trackSearch) {
        $('#addTrackContainer').hide();
        $('#enableTrackSearch').text('+');
        trackSearch = false;
    } else {
        $('#addTrackContainer').show();
        $('#enableTrackSearch').text('-');
        trackSearch = true;
    }
}

function addSpotifyTrack(spotify_id) {
    newSpotifyTracks.push(spotify_id);
    showAddSuccess();
}

function showNewTrackDialog() {
    // TODO
}

function exportAsText() {

}

function exportToSpotify() {

}