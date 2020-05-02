var token = /access_token=([^&]+)/.exec(document.location.hash)[1];
var expires_in = /expires_in=([^&]+)/.exec(document.location.hash)[1];
let date = new Date(Date.now() + (1000 * parseInt(expires_in)));
date = date.toUTCString();
document.cookie = "SESSION_ID=" + token + "; path=/; expires=" + date;
window.location.replace("http://127.0.0.1/");
