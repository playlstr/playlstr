let newTracks = [];
let deletedTracks = [];
let advancedSearch = false;
let trackSearch = false;
let lastTrackSearchTime = new Date();

String.prototype.format = String.prototype.f = function() {
    var s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};

function deleteTrack(track_id) {
    // TODO
    console.log("delete " + track_id);
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
        let csrf_cookie_start = document.cookie.indexOf('csrftoken=') + 10;
        let csrf_cookie_end = document.cookie.indexOf(';', csrf_cookie_start);
        if (csrf_cookie_end === -1) csrf_cookie_end = document.cookie.length;
        let csrf = unescape(document.cookie.substring(csrf_cookie_start, csrf_cookie_end));
        $.ajax({
            type: 'POST',
            url: 'http://' + window.location.host + '/playlist-update/',
            headers: {'X-CSRFToken': csrf},
            data: {'playlist': playlist_id, 'added': JSON.stringify(newTracks), 'deleted': JSON.stringify(deletedTracks), 'playlist_name': $('#playlistName').text()},
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
    if (document.cookie.length === 0) return;
    let csrf_cookie_start = document.cookie.indexOf('csrftoken=') + 10;
    let csrf_cookie_end = document.cookie.indexOf(';', csrf_cookie_start);
    if (csrf_cookie_end === -1) csrf_cookie_end = document.cookie.length;
    let csrf = unescape(document.cookie.substring(csrf_cookie_start, csrf_cookie_end));
    $.ajax({
        type: 'POST',
        url: 'http://' + window.location.host + '/track-autocomplete/',
        headers: {'X-CSRFToken': csrf},
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
        let new_row = '<tr class="track-search-results" id="{0}"><td>{1}</td><td>{2}</td><td>{3}</td><td><button class="btn btn-primary" onclick="addTrack({0}, \'{1}\', \'{2}\', \'{3}\')">+</button></td></tr>'.format(
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
    // TODO
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