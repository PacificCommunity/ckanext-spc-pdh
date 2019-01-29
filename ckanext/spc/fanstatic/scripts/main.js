(function ($) {
  $('.json-data').map((i, item) => {
    $(item).jsonBrowse($(item).data().json, {
      collapsed: true
    });
  })
})(jQuery);
