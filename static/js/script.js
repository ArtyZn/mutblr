var post = {
  list: {
    get: async function (args) {
      try {
        if (!args) args = {};
        r = {
          url: "/api/posts",
          data: args,
        }
        r.data.token = cur_user.token;
        return await $.ajax(r);
      } catch (e) {
        console.error(e);
      }
    },
  },
  get: async function (post_id) {
    try {
      r = {
        url: "/api/posts/" + post_id,
        data: {
          token: cur_user.token
        },
      }
      return await $.ajax(r);
    } catch (e) {
      console.error(e);
    }
  },
  create: async function (args) {
    try {
      if (!args) args = {};
      r = {
        url: "/api/posts",
        method: "post",
        data: args
      }
      r.args.token = cur_user.token;
      await $.ajax(r);
    } catch (e) {
      console.error(e);
    }
  },
  delete: async function (post_id) {
    return await $.ajax({
      url: "/api/posts/" + post_id,
      method: "delete",
      data: {
        token: cur_user.token,
      }
    });
  }
}

var cur_user = {
  username: null,
  id: null,
  api_token: null
}

var load_posts_args = {
  offset: 0,
  limit: 20,
  feed: false
}

function login_prompt() {
  $('#loginModal').modal('toggle');
}

function login_check(ondiscard) {
  if (!cur_user.id) {
    login_prompt();
  }
}

async function load_posts(args) {
  let resp = await post.list.get(args)
  console.log(resp)
  resp.posts.forEach((post, i) => {
    $('#posts').append('<div class="post"><div class="post-author rounded-circle"><img src="/uploads/' + post.user.pfp + '"></div><div class="post-content rounded text-break">' + post.content + '</div></div>');
  });
}

$(document).ready(function () {
  $('#loginModal').on('hidden.bs.modal', function (e) {
    window.location.replace('/');
  });
  load_posts(load_posts_args);
  $(document).on('scroll', function () {
    if ($(document).height() - $(window).scrollTop() - $(window).height() < 100 && load_posts_args.offset < $('.post').length) {
      load_posts_args.offset += load_posts_args.limit;
      load_posts(load_posts_args);
    }
  })
})
