function load_posts() {
  let resp = $.ajax({
    url: window.location.pathname,
    method: "post",
    data: {
      offset: $(".post").length ? $('.post').last()[0].id.slice(5) : null,
    },
    success: function (resp) {
      $('#posts').append(resp);
    },
    error: function (e) {
      console.log(e);
    }
  });
}

function change_subscribe_button() {
  $("#content-info button").toggleClass('d-none');
}

$(document).ready(function () {
  load_posts();
  $(document).on('scroll', function () {
    if ($(document).height() - $(window).scrollTop() - $(window).height() < 100 && last_post <= $(".post").length) {
      last_post += 20;
      load_posts();
    }
  });
});
