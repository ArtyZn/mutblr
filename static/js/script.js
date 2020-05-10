updInterval = setInterval(update, 200);

var users_info = {}

var last_post = 0;

function login_prompt() {
  $('#login-modal').modal('toggle');
}

function subscribe(user_id) {
  $.ajax({
    url: "/action/",
    method: "post",
    data: {
      action: "subscribe",
      user_id: user_id
    }
  });
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
  login_check();
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

function reply(post_id) {
  $('#post-modal').modal('show');
  $('#post-iframe')[0].contentWindow.document.getElementById('reply_to').value = post_id;
}

function new_post() {
  $('#post-modal').modal('show');
  $('#post-iframe')[0].contentWindow.document.getElementById('reply_to').value = null;
}

function delete_post(post_id) {
  $.ajax({
    url: "/post/" + post_id + "/delete",
    method: "post"
  });
}

function update() {
  $('.username').on('mouseover', function(e) {
    username = $($(e)[0].target)[0].innerHTML;
    console.log(username);
  });
  $('#post-iframe')[0].style.height = $($('#post-iframe')[0].contentWindow).height() + 'px';
}

$(document).ready(function () {
  $('#login-modal').on('hidden.bs.modal', function (e) {
    window.location.replace('/');
  });
  $('#search-input').on('input', function (e) {
    $.ajax({
      url: "/action/",
      method: "post",
      data: {
        action: 'search',
        keyword: e.target.value
      },
      success: function (e) {
        console.log(e);
        $('#search-panel')[0].innerHTML = e;
      },
      error: function (e) {
        console.log(e);
      }
    });
  });
});
