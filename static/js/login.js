var token = /access_token=([^&]+)/.exec(document.location.hash)[1];
var expires_in = /expires_in=([^&]+)/.exec(document.location.hash)[1];
window.location.replace("http://127.0.0.1/login/redirect/?token=" + token + "&expires_in=" + expires_in);
