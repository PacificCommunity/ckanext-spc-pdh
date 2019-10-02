(function ($) {
  $('.json-data').map(function (i, item) {
    $(item).jsonBrowse($(item).data().json, {
      collapsed: true
    });
  })
})(jQuery);
