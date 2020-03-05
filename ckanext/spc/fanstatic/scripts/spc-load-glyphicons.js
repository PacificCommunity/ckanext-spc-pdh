ckan.module("spc-load-glyphicons", function($, _) {
  "use strict";
  return {
    initialize: function() {
      $.proxyAll(this, /_on/);
      this._onLoad();
    },
    _onLoad: function(event) {
      // Lets append right fonts to IFRAME
      $('.resource-view iframe').each(function(idx, item){
        var iframe = $(this);          
          var fonts = '<style type="text/css" rel="stylesheet">' +
            '@font-face {' +
            'font-family: "Glyphicons Halflings";' +
            // 'src: url("'+ ckan.url('/base/fonts/glyphicons-halflings-regular.eot') +'");' +
            // 'src: url("'+ ckan.url('/base/fonts/glyphicons-halflings-regular.eot?#iefix') +') format("embedded-opentype"),' +
              'src: url("'+ ckan.url('/base/fonts/glyphicons-halflings-regular.woff')+'") format("woff"),' + 
              'url("'+ ckan.url('/base/fonts/glyphicons-halflings-regular.ttf') +'") format("truetype"),' +
              'url("'+ ckan.url('/base/fonts/glyphicons-halflings-regular.svg#glyphicons_halflingsregular') + '") format("svg");' +
            '}' +
            '</style>';
          iframe.contents().find('body').append(fonts);
      })
    }
  };
});
