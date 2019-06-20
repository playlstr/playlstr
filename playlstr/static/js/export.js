function exportAsText() {
    let criteria = JSON.stringify({'excluded_genres': getExcludedGenres(), 'explicit': $('#explicitCheck').is(':checked')});
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
    // TODO
}

function exportFail() {
    // TODO
    console.log('export failed');
}


