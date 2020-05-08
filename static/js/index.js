function load_posts() {
  let resp = $.ajax({
    url: "/",
    method: "post",
    data: {
      offset: $(".post").length ? $('.post').last()[0].id.slice(5) : null
    },
    success: function (resp) {
      $('#posts').append(resp);

    }
  });
}

$(document).ready(function () {
  load_posts();
  $(document).on('scroll', function () {
    if ($(document).height() - $(window).scrollTop() - $(window).height() < 100 && last_post <= $(".post").length) {
      last_post += 20;
      load_posts();
    }
  });
})
