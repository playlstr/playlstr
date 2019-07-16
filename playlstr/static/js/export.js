let excludedArtists = [];
let excludedAlbums = [];

function excludeSelectedAlbum() {
    let option = $('#albumExcludeSelect').children('option:selected');
    if (option === $('#albumExcludeSelect:first-child')) return; // Default 'Choose...' element isn't an album
    excludedAlbums.push(option.val());
    option.remove();
    let id = option.val().replace(' ', '_');
    $('#excludedAlbums').append('<div id="{0}" class="form-inline">{1}<button onclick="removeExcludedAlbum(\'{1}\');" type="button" class="btn btn-outline-danger">X</button></div>'.format(id, option.val()));
}

function removeExcludedAlbum(album) {
    let index = excludedAlbums.indexOf(album);
    if (index === -1) return;
    $('#' + album.replace(' ', '_')).remove();
    excludedAlbums.splice(index, 1);
    $('#albumExcludeSelect').append($(new Option(album, album)).html(album));
}

function excludeSelectedArtist() {
    let option = $('#artistExcludeSelect').children('option:selected');
    if (option === $('#artistExcludeSelect:first-child')) return; // Default 'Choose...' element isn't an artist
    excludedArtists.push(option.val());
    option.remove();
    let id = option.val().replace(' ', '_');
    $('#excludedArtists').append('<div id="{0}" class="form-inline">{1}<button onclick="removeExcludedArtist(\'{1}\');" type="button" class="btn btn-outline-danger">X</button></div>'.format(id, option.val()));
}

function removeExcludedArtist(artist) {
    let index = excludedArtists.indexOf(artist);
    if (index === -1) return;
    $('#' + artist.replace(' ', '_')).remove();
    excludedArtists.splice(index, 1);
    $('#artistExcludeSelect').append($(new Option(artist, artist)).html(artist));
}

function exportAsText() {
    let criteria = JSON.stringify({
        'excluded_genres': getExcludedGenres(),
        'explicit': $('#explicitCheck').is(':checked'),
        'excluded_artists': excludedArtists,
        'excluded_albums': excludedAlbums
    });
    $.ajax({
        type: 'POST',
        url: 'http://' + window.location.host + '/file-export/',
        data: {'playlist_id': playlist_id, 'filetype': 'text', 'criteria': criteria},
        headers: {'X-CSRFToken': csrfToken},
        success: function (result) {
            console.log('success');
            console.log(result);
            let blob = new Blob([result], {type: 'text/plain'});
            window.location = URL.createObjectURL(blob);
        },
        error: function () {
            exportFail();
        }
    });
}

function getExcludedGenres() {
    // TODO
    return [];
}

function exportToSpotify() {
    let criteria = JSON.stringify({
        'excluded_genres': getExcludedGenres(),
        'explicit': $('#explicitCheck').is(':checked'),
        'excluded_artists': excludedArtists,
        'excluded_albums': excludedAlbums
    });
    $.ajax({
        type: 'POST',
        url: 'http://' + window.location.host + '/spotify-export/',
        data: {'playlist_id': playlist_id, 'criteria': criteria},
        headers: {'X-CSRFToken': csrfToken},
        success: function (result) {
            window.location = result;
        },
        error: exportFail
    });
}

function exportFail(data) {
    $('#exportError').text('Unable to export playlist (' + data.responseText + ')').fadeIn().delay(4000).fadeOut();
}


