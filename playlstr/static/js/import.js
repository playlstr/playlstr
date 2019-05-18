function deleteTrack(track_id) {

}


function importSpotifyUrl() {
    var location = window.location.toString();
    var access_token_start = location.indexOf('#access_token=') + 14;
    import_url = document.getElementById('spotifyImportInput').value;
    if (access_token_start === 13 /* -1 + 14 */) {
        window.location.href = 'https://accounts.spotify.com/authorize?client_id=c39c475f390546a1832482a02c4aa36a&response_type=token&scope=playlist-modify-public%20playlist-read-private%20playlist-read%20playlist-read-collaborative&redirect_uri=' + location + '&state=' + import_url;
        return;
    }
    if (import_url.match('^http(s?):\\/\\/open\\.spotify\\.com\\/playlist\\/.{22}\\/?')) {
        $('#invalidSpotifyUrl').hide();
    } else {
        $('#invalidSpotifyUrl').show();
        return;
    }
    var access_token_end = location.indexOf('&', access_token_start);
    if (access_token_end === -1) access_token_end = location.length;
    var access_token = location.substring(access_token_start, access_token_end);
    $('#spotifyImportRequestSent').show();
    if (document.cookie.length === 0) spotifyImportFail();
    var csrf_cookie_start = document.cookie.indexOf('csrftoken=') + 10;
    var csrf_cookie_end = document.cookie.indexOf(';', csrf_cookie_start);
    if (csrf_cookie_end === -1) csrf_cookie_end = document.cookie.length;
    var csrf = unescape(document.cookie.substring(csrf_cookie_start, csrf_cookie_end));
    console.log(csrf);
    console.log(location.substring(0, location.indexOf('/import/') + 8) + 'spotify/');
    $.ajax({
        type: 'POST',
        url: location.substring(0, location.indexOf('/import/') + 8) + 'spotify/',
        headers: {'X-CSRFToken': csrf},
        cache: false,
        timeout: 30000,
        data: {'playlist_url' : import_url, 'access_token': access_token},
        error: spotifyImportFail,
        success: spotifyImportComplete,
        dataType: 'text'
    });
}

function spotifyImportComplete(data) {
    url = 'http://' + window.location.host + '/list/' + data;
    window.location = url;
}

function spotifyImportFail(data) {
    $('spotifyImportFailed').show();
}

