var token = /access_token=([^&]+)/.exec(document.location.hash)[1];
window.location.replace("http://127.0.0.1/login/redirect/?token=" + token);
