let searchHovered = false;

String.prototype.format = String.prototype.f = function () {
    let s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};

function getPathUrl(path) {
    let url = window.location.protocol.toString() + '//' + window.location.host.toString() + (path[0] === '/' ? path : '/' + path);
    if (url[url.length - 1] !== '/') {
        console.log('adding / to url');
        console.log(url);
        url += '/';
    }
    return url;
}

function createPlaylist() {
    $('#createPlaylistFail').hide();
    let playlistName = $('#newPlaylistName').val();
    $.ajax({
        type: 'POST',
        url: getPathUrl('create'),
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
    window.location.href = '/list/{0}/'.format(data);
}

function searchClicked() {
    let query = document.getElementById('playlistSearch').value;
    if (query.length === 0) {
        return;
    }
    window.location.href = '/search?q=' + query;
}

