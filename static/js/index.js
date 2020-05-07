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
