function deleteTrack(track_id) {

}


function importSpotifyUrl() {
    let import_url = document.getElementById('spotifyImportInput').value;
    if (spotifyAccessToken === null) {
        newSpotifyAccessToken(import_url);
    } else {
        console.log(spotifyAccessToken);
    }
    if (import_url.match('^http(s?):\\/\\/open\\.spotify\\.com\\/playlist\\/.{22}\\/?')) {
        $('#invalidSpotifyUrl').hide();
    } else {
        $('#invalidSpotifyUrl').show();
        return;
    }
    $('#spotifyImportRequestSent').show();
    if (spotifyAccessToken === null) spotifyImportFail();
    $.ajax({
        type: 'POST',
        url: location.substring(0, location.indexOf('/import/') + 8) + 'spotify/',
        headers: {'X-CSRFToken': csrfToken},
        cache: false,
        timeout: 30000,
        data: {'playlist_url' : import_url, 'access_token': spotifyAccessToken},
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

