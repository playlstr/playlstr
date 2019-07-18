function clearLinkedAccounts() {
    $.ajax({
        type: 'GET',
        url: 'http://' + window.location.host.toString() + '/clear-links',
        headers: {'X-CSRFToken': csrfToken},
        cache: false,
        timeout: 30000,
        error: function () {
            $('#clearFailed').fadeIn().delay(4000).fadeOut();
        },
        success: function () {
            $('#clearSuccess').fadeIn().delay(4000).fadeOut();
        },
        dataType: 'text'
    });
}

function initLinkPage() {
    setInterval(function () {
        let timeLocation = document.getElementById('timeUntilRefresh');
        if (timeLocation.textContent === "0") {
            window.location.reload(true);
            return;
        }
        timeLocation.textContent = (timeLocation.textContent - 1).toString();
    }, 1000);

}
