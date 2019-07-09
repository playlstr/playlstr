let userPlaylistsOffset = 0;

function importSpotifyUrl(import_url = '') {
    if (import_url === '') import_url = document.getElementById('spotifyImportInput').value;
    console.log(import_url);
    let location = document.location.toString();
    if (spotifyAccessToken === null) {
        alert('Authenticate with Spotify first');
        return;
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
        data: {'playlist_url': import_url, 'access_token': spotifyAccessToken},
        error: spotifyImportFail,
        success: spotifyImportComplete,
        dataType: 'text'
    });
}

function spotifyImportComplete(data) {
    window.location = 'http://' + window.location.host + '/list/' + data;
}

function spotifyImportFail(data) {
    $('spotifyImportFailed').show();
}

function importPlaylistFile(fileInput) {
    let reader = new FileReader();
    if (!fileInput.files) return;
    let file = fileInput.files[0];
    reader.fileName = file.name;
    reader.addEventListener('load', sendPlaylistImportRequest);
    reader.readAsText(file);
}

function sendPlaylistImportRequest(callback) {
    $.ajax({
        type: 'POST',
        url: 'http://' + window.location.host + '/local-import/',
        headers: {'X-CSRFToken': csrfToken},
        cache: false,
        timeout: 30000,
        data: {'name': callback.target.fileName, 'playlist': callback.target.result},
        error: localImportFail,
        success: spotifyImportComplete,
        dataType: 'text'
    });
}

function localImportFail(error) {
    // TODO
    console.log(error);
}

function appendUserSpotifyPlaylists(playlists, more_button_exists = false, create_more_button = false) {
    let playlistsDiv = document.getElementById('spotifyPlaylists');
    if (more_button_exists) $('#spotifyPlaylists button:last-child').remove();
    for (let i = 0; i < playlists.length; i++) {
        $(playlistsDiv).append('<button class="list-group-item list-group-item-action" onclick="importSpotifyUrl(\'https://open.spotify.com/playlist/' + playlists[i].id + '\');">' + playlists[i].name + '</button>')
    }
    if (create_more_button) {
        $(playlistsDiv).append('<button class="list-group-item list-group-item-action" onclick="getUserSpotifyPlaylists();">More</button>')
    }
}