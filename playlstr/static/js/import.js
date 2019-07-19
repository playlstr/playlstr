let userPlaylistsOffset = 0;

function importSpotifyUrl(import_url = '') {
    if (import_url === '') import_url = document.getElementById('spotifyImportInput').value;
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
        url: getPathUrl('/import/spotify'),
        headers: {'X-CSRFToken': csrfToken},
        cache: false,
        timeout: 30000,
        data: {'playlist_url': import_url, 'access_token': spotifyAccessToken},
        error: spotifyImportFail,
        success: spotifyImportComplete,
    });
}

function spotifyImportComplete(data) {
    window.location.href = '/list/{0}'.format(data);
}

function spotifyImportFail() {
    $('spotifyImportFailed').fadeIn().delay(4000).fadeOut();
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
        url: getPathUrl('/local-import/'),
        headers: {'X-CSRFToken': csrfToken},
        cache: false,
        timeout: 30000,
        data: {'name': callback.target.fileName, 'playlist': callback.target.result},
        error: localImportFail,
        success: spotifyImportComplete,
    });
}

function localImportFail() {
    $('playlistFileImportFailed').fadeIn().delay(4000).fadeOut();
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