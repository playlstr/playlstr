let spotifyAccessToken = null;

function loadSpotifyAccessToken(state = '') {
    parseSpotifyAccessTokenFromLocation();
    let savedToken = getCookieValue('spotify-token');
    if (savedToken === '') return;
    spotifyAccessToken = savedToken;
}

function parseSpotifyAccessTokenFromLocation() {
    let location = document.location.toString();
    var access_token_start = location.indexOf('#access_token=') + 14;
    if (access_token_start === 13 /* -1 + 14 */) {
        return null;
    }
    var access_token_end = location.indexOf('&', access_token_start);
    let token = location.substring(access_token_start, access_token_end);
    let expiry_start = location.indexOf('expires_in=') + 11;
    let expiry_end = location.indexOf('&', expiry_start);
    if (expiry_end === -1) expiry_end = location.length;
    let expiryDate = new Date();
    expiryDate.setSeconds(expiryDate.getSeconds() + parseInt(location.substring(expiry_start, expiry_end)) - 5);
    document.cookie = 'spotify-token=' + token + '; expires=' + expiryDate.toString() + '; path=/';
    document.location.hash = '';
}

function newSpotifyAccessToken(state = '') {
    window.location.href = 'https://accounts.spotify.com/authorize?client_id=c39c475f390546a1832482a02c4aa36a&response_type=token&scope=playlist-modify-public%20playlist-read-private%20playlist-read%20playlist-read-collaborative&redirect_uri=' + location + (state === '' ? '' : '&state=' + state);
}

// https://stackoverflow.com/questions/5639346/what-is-the-shortest-function-for-reading-a-cookie-by-name-in-javascript/25490531#25490531
function getCookieValue(a) {
    var b = document.cookie.match('(^|[^;]+)\\s*' + a + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}