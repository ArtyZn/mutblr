var cur_user = {
  username: null,
  id: null
}

var last_post = 0;

function login_prompt() {
  $('#loginModal').modal('toggle');
}

function login_check(ondiscard) {
  if (!cur_user.id) {
    login_prompt();
  }
}

$(document).ready(function () {
  $('#loginModal').on('hidden.bs.modal', function (e) {
    window.location.replace('/');
  });
  load_posts();
  $(document).on('scroll', function () {
    if ($(document).height() - $(window).scrollTop() - $(window).height() < 100 && last_post <= $(".post").length) {
      last_post += 20;
      load_posts();
    }
  })
})
