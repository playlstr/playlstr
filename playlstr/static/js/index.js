function createPlaylist() {
    $('#createPlaylistFail').hide();
    var location = window.location.toString();
    if (document.cookie.length === 0) createPlaylistFail();
    var csrf_cookie_start = document.cookie.indexOf('csrftoken=') + 10;
    var csrf_cookie_end = document.cookie.indexOf(';', csrf_cookie_start);
    if (csrf_cookie_end === -1) csrf_cookie_end = document.cookie.length;
    var csrf = unescape(document.cookie.substring(csrf_cookie_start, csrf_cookie_end));
    var playlistName = $('#newPlaylistName').val();
    $.ajax({
        type: 'POST',
        url: location + 'create/',
        headers: {'X-CSRFToken': csrf},
        cache: false,
        timeout: 30000,
        data: {'name' : playlistName},
        error: createPlaylistFail,
        success: createPlaylistSuccess,
        dataType: 'text'
    });
}

function createPlaylistFail() {
    $('#createPlaylistFail').show();
}

function createPlaylistSuccess(data) {
    url = 'http://' + window.location.host + '/list/' + data;
    window.location = url;
}

