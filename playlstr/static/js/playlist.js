var newTracks = [];
var deletedTracks = [];
var advancedSearch = false;
var lastTrackSearchTime = new Date();

function deleteTrack(track_id) {
    // TODO
    console.log("delete " + track_id);
}

function enterEditMode() {
    $('#addTrackContainer').show();
    $('#editButton').hide();
    $('#saveButton').show();
    $('#cancelButton').show();
    $('.rm-btn-container').show();
}

function exitEditMode(save = false) {
    $('#addTrackContainer').hide();
    $('#editButton').show();
    $('#saveButton').hide();
    $('#cancelButton').hide();
    $('.rm-btn-container').hide();
    if (save) {
        if (document.cookie.length === 0) return;
        let csrf_cookie_start = document.cookie.indexOf('csrftoken=') + 10;
        let csrf_cookie_end = document.cookie.indexOf(';', csrf_cookie_start);
        if (csrf_cookie_end === -1) csrf_cookie_end = document.cookie.length;
        let csrf = unescape(document.cookie.substring(csrf_cookie_start, csrf_cookie_end));
        $.ajax({
            type: 'POST',
            url: 'http://' + window.location.host + '/update-playlist/',
            headers: {'X-CSRFToken': csrf},
            data: {'added': newTracks, 'deleted': deletedTracks},
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
        let new_row = '<tr class="track-search-results" id="' + track.id + '"><td>' +
            track.title + '</td>' + '<td>' + track.artist + '</td>' + '<td>' + track.album + '</td>' +
            '<td><button class="btn btn-primary" onclick="addTrackById(' + track.id + ')">+</button> </td>' + '</tr>';
        $(search_results_div).append(new_row);
    }
}

function addTrackById(track_id) {
    console.log("add " + track_id);
    newTracks.push(track_id);
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

function savePlaylist() {

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