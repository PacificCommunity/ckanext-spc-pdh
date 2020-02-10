(function($) {
  function makeShareLink(url, icon) {
    var link = document.createElement('a');
    link.href = url;

    var i = document.createElement('i');
    i.classList.add('fa');
    i.classList.add(icon);
    link.appendChild(i);
    link.addEventListener('click', function(e) {
      e.preventDefault();
      window.open(link.href, 'shareWindow', 'height=450, width=550, toolbar=0, menubar=0, top=200');
    });
    return link;
  }

  function currentUrl() {
    return encodeURIComponent(window.location.href);
  }
  function currentTitle() {
    return encodeURIComponent(document.head.querySelector('title').textContent);
  }

  function facebookShare(host) {
    var url = 'https://www.facebook.com/share.php?u=' + currentUrl();
    host.appendChild(makeShareLink(url, 'fa-facebook'));
    return host;
  }
  function twitterShare(host) {
    var url = 'https://twitter.com/share?text=' + currentTitle() + '&url=' + currentUrl();
    host.appendChild(makeShareLink(url, 'fa-twitter'));
    return host;
  }
  function linkedinShare(host) {
    var url = 'https://www.linkedin.com/shareArticle?mini=true&title=' + currentTitle() + '&summary=&url=' + currentUrl();
    host.appendChild(makeShareLink(url, 'fa-linkedin'));
    return host;
  }
  function mailShare(host) {
    var url = 'mailto:?subject=' + currentTitle() + '&body=You might want to check this out: ' + currentUrl();
    host.appendChild(makeShareLink(url, 'fa-envelope'));
    return host;
  }
  var sharePoints = [
    facebookShare,
    twitterShare,
    linkedinShare,
    mailShare
  ];
  $(document).ready(function() {
    var panel = document.createElement('ul');
    panel.classList.add('social-share--panel');
    sharePoints.forEach(function(point) {
      var tile = document.createElement('li');
      tile.classList.add('social-share--tile');
      panel.appendChild(point(tile));
    });
    if (window.parent == window) {
      document.body.appendChild(panel);
    }
  });
})(jQuery);
