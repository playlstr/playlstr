let spotifyAccessToken = null;
let SPOTIFY_REDIRECT_URI = 'http://' + window.location.host.toString() + '/spotify-redirect/';

function hideSpotifyAuth() {
    $(document).ready(function () {
        $('#spotifyAuthButton').hide();
    });
}

function getNewAccessTokenLoggedIn() {
    $.ajax({
        type: 'GET',
        url: 'http://' + window.location.host + '/get-spotify-token/',
        headers: {'X-CSRFToken': csrfToken},
        success: parseUserSpotifyToken
    });
}

function parseUserSpotifyToken(data) {
    if (data.length < 20) {
        return;
    }
    data = JSON.parse(data);
    if (data['access_token'] === undefined) return;
    spotifyAccessToken = data['access_token'];
    let expiryDate = new Date();
    expiryDate.setSeconds(expiryDate.getSeconds() + parseInt(data['expires_in']));
    document.cookie = 'spotify-token=' + data['access_token'] + '; expires=' + expiryDate.toString() + '; path=/';
    hideSpotifyAuth();
}


function loadSpotifyAccessToken() {
    authenticated ? parseSpotifyAccessTokenFromLocationLoggedIn() : parseSpotifyAccessTokenFromLocationLoggedOut();
    let savedToken = getCookieValue('spotify-token');
    if (savedToken === '') {
        if (authenticated) {
            getNewAccessTokenLoggedIn();
        }
        return;
    }
    spotifyAccessToken = savedToken;
    hideSpotifyAuth();
}

function parseSpotifyAccessTokenFromLocationLoggedIn() {
    let location = document.location.toString();
    let access_token_start = location.indexOf('?code=') + 6;
    if (access_token_start === 5 /* -1 + 6 */) {
        return null;
    }
    let access_token_end = location.indexOf('&', access_token_start);
    if (access_token_end === -1) access_token_end = location.length;
    let token = location.substring(access_token_start, access_token_end);
    $.ajax({
        type: 'POST',
        url: 'http://' + window.location.host + '/spotify-auth-user/',
        headers: {'X-CSRFToken': csrfToken},
        data: {
            'code': token,
            'redirect_uri': location.substring(0, access_token_start - 6)
        },
        success: getNewAccessTokenLoggedIn(),
    });
    document.location.hash = '';
}

function parseSpotifyAccessTokenFromLocationLoggedOut() {
    let location = document.location.toString();
    let access_token_start = location.indexOf('#access_token=') + 14;
    if (access_token_start === 13 /* -1 + 14 */) {
        return null;
    }
    let access_token_end = location.indexOf('&', access_token_start);
    let token = location.substring(access_token_start, access_token_end);
    let expiry_start = location.indexOf('expires_in=') + 11;
    let expiry_end = location.indexOf('&', expiry_start);
    if (expiry_end === -1) expiry_end = location.length;
    let expiryDate = new Date();
    expiryDate.setSeconds(expiryDate.getSeconds() + parseInt(location.substring(expiry_start, expiry_end)) - 5);
    document.cookie = 'spotify-token=' + token + '; expires=' + expiryDate.toString() + '; path=/';
    document.location.hash = '';
    hideSpotifyAuth();
}

function redirectToPreauthUrl() {
    let location = document.location.toString();
    let state_start = location.indexOf('state=');
    if (state_start === -1) {
        console.log('No state, not redirecting');
        return;
    }
    state_start += 6;
    let state_end = location.indexOf('&', state_start);
    if (state_end === -1) state_end = location.length;
    let state = location.substring(state_start, state_end);
    let new_url_start = state.indexOf('_redirect_') + 10;
    if (new_url_start === -1 + 10) {
        console.log('No redirect url');
        return;
    }
    // Redirect URI should always be the last part of state
    let new_url = state.substring(new_url_start, state_end);
    console.log(new_url);
    location = location.replace(new_url, '');
    let hash = location.indexOf('#');
    if (hash === -1) {
        console.log('Passing no query string to redirect url');
        window.location.href = new_url;
        return;
    }
    let redirect = decodeURIComponent(new_url);
    if (redirect[redirect.length - 1] !== '/') {
        redirect += '/';
    }
    redirect += location.substring(hash, location.indexOf('_redirect_'));
    window.location.href = redirect;
}

function spotifyAuthLoggedOut() {
    state += '_redirect_' + window.location;
    window.location.href = 'https://accounts.spotify.com/authorize?client_id=c39c475f390546a1832482a02c4aa36a&response_type=token&scope=playlist-modify-public%20playlist-read-private%20playlist-read%20playlist-read-collaborative&redirect_uri=' + SPOTIFY_REDIRECT_URI + (state === '' ? '' : '&state=' + state);
}

function spotifyAuthLoggedIn() {
    state += '_redirect_' + window.location;
    window.location.href = 'https://accounts.spotify.com/authorize?client_id=c39c475f390546a1832482a02c4aa36a&response_type=code&scope=playlist-modify-public%20playlist-read-private%20playlist-read%20playlist-read-collaborative&redirect_uri=' + SPOTIFY_REDIRECT_URI + (state === '' ? '' : '&state=' + state);
}

// https://stackoverflow.com/questions/5639346/what-is-the-shortest-function-for-reading-a-cookie-by-name-in-javascript/25490531#25490531
function getCookieValue(a) {
    let b = document.cookie.match('(^|[^;]+)\\s*' + a + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}

