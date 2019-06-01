function createPlaylist() {
    $('#createPlaylistFail').hide();
    var location = window.location.toString();
    if (document.cookie.length === 0) createPlaylistFail();
    var playlistName = $('#newPlaylistName').val();
    $.ajax({
        type: 'POST',
        url: location + 'create/',
        headers: {'X-CSRFToken': csrfToken},
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

