function createPlaylist() {
    $('#createPlaylistFail').hide();
    let location = window.location.toString();
    if (document.cookie.length === 0) createPlaylistFail();
    let playlistName = $('#newPlaylistName').val();
    $.ajax({
        type: 'POST',
        url: location + 'create/',
        headers: {'X-CSRFToken': csrfToken},
        cache: false,
        timeout: 30000,
        data: {'name': playlistName},
        error: createPlaylistFail,
        success: createPlaylistSuccess,
        dataType: 'text'
    });
}

function createPlaylistFail() {
    $('#createPlaylistFail').show();
}

function createPlaylistSuccess(data) {
    window.location = 'http://' + window.location.host + '/list/' + data;
}

