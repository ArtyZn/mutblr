updInterval = setInterval(update, 500);

var users_info = {}

var last_post = 0;

function login_prompt() {
  $('#login-modal').modal('toggle');
}

function login_check() {
  $.ajax({
    url: "/action/",
    method: "post",
    data: {
      action: "getcuruserid"
    },
    success: function (resp, a, b) {
      console.log(resp);
      console.log(a);
      console.log(b);
    },
    error: function(e) {
      console.log(e);
      login_prompt();
    }
  })
}

function like(post_id) {
  $.ajax({
    url: "/action/",
    method: "post",
    data: {
      action: "like",
      post_id: post_id
    }
  })
  $('#post-' + post_id + ' .likebtn').toggleClass('liked');
}

function send_post(args) {
  data = args ? args : {};
  data.action = "post";
  data.content = $('#post-modal-form-content')[0].value;
  console.log(data);
  $.ajax({
    url: "/action/",
    method: "post",
    data: data,
    error: function (e) {
      console.log(e);
    }
  })
  $('#post-modal').modal('hide');
}

function update() {
  $('.username').on('mouseover', function(e) {
    username = $($(e)[0].target)[0].innerHTML;
    console.log(username);
  });
}

$(document).ready(function () {
  $('#login-modal').on('hidden.bs.modal', function (e) {
    window.location.replace('/');
  });
});
