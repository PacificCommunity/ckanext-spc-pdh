ckan.module("spc-import-datasets", function ($) {
  "use strict";
  return {
    initialize: function () {
      this.el.on("change", this._onChange.bind(this));
    },
    _onChange: function (e) {
      this.el.submit();
    },
  };
});
