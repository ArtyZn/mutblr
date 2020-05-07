function load_posts() {
  let resp = $.ajax({
    url: "/feed/",
    method: "post",
    data: {
      offset: $(".post").length ? $('.post').last()[0].id.slice(5) : null,
      show_privates : $("#show_privates_switch").is(':checked') ? 1 : null
    },
    success: function (resp) {
      $('#posts').append(resp);

    }
  });
}

function reload_posts() {
  $("#posts").empty();
  load_posts();
  var last_post = 0;
}

$(document).ready(function () {
  login_check();
});
