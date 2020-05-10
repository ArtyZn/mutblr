function load_blogs() {
  let resp = $.ajax({
    url: "/blogs/",
    method: "post",
    data: {
      offset: $(".blog").length ? $(".blog").length : null
    },
    success: function (resp) {
      $("#blogs").append(resp);
    }
  });
}

$(document).ready(function () {
  login_check();
  load_blogs();
  $(document).on('scroll', function () {
    if ($(document).height() - $(window).scrollTop() - $(window).height() < 100 && last_post <= $(".blog").length) {
      last_post += 20;
      load_blogs();
    }
  });
});
