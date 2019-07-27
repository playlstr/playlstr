let changes = {};

function enterProfileEditMode() {
    $('#enterProfileEdit').hide();
    $('#exitProfileEdit').show();
    let email = $('#userEmail').hide();
    $('#userEmailInput').val(email.text()).show();
    let username = $('#username').hide();
    $('#usernameInput').val(username.text()).show();
    $('#userFullname').hide();
    $('#userFirstnameInput').val($('#userFirstname').text()).show();
    $('#userLastnameInput').val($('#userLastname').text()).show();
}

function exitProfileEditMode(save = true) {
    $('#enterProfileEdit').show();
    $('#exitProfileEdit').hide();
    $('#userEmail').show();
    let newEmail = $('#userEmailInput').hide().val();
    $('#username').show();
    let newUsername = $('#usernameInput').hide().val();
    $('#userFullname').show();
    let newFirstname = $('#userFirstnameInput').hide().val();
    let newLastname = $('#userLastnameInput').hide().val();
    if (save) {
        if ($('#userEmail').text() !== newEmail) {
            changes['email'] = newEmail;
        }
        if ($('#username').text() !== newUsername) {
            changes['username'] = newUsername;
        }
        if ($('#userFirstname').text() !== newFirstname) {
            changes['firstname'] = newFirstname;
        }
        if ($('#userLastname').text() !== newLastname) {
            changes['lastname'] = newLastname;
        }
        sendUpdatedProfile();
    }
}

function sendUpdatedProfile() {
    $.ajax({
        type: 'POST',
        url: getPathUrl('/profile-update/'),
        data: {'changes': JSON.stringify(changes)},
        headers: {'X-CSRFToken': csrfToken},
        success: profileUpdateSuccess,
        error: profileUpdateFail
    });
}

function profileUpdateSuccess() {
    if ('firstname' in changes) {
        $('#userFirstname').text(changes['firstname']);
    }
    if ('lastname' in changes) {
        $('#userLastname').text(changes['lastname']);
    }
    if ('email' in changes) {
        $('#userEmail').text(changes['email']);
    }
    if ('username' in changes) {
        $('#username').text(changes['username']);
    }
}

function profileUpdateFail() {
    // TODO
    console.log('profile update failed');
}