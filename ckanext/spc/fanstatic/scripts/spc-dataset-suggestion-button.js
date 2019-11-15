ckan.module("spc-dataset-suggestion-button", function($, _) {
  "use strict";
  return {
    initialize: function() {
      this.el.on("click", this._onExpand.bind(this));
      this._block = $(".suggestion-block");
      this._block
        .find(".btn-suggestion-close")
        .on("click", this._onReject.bind(this));
      // console.log(this.block, this.block.find(".btn-suggestion-close"));
    },
    _onExpand: function(event) {
      if (this.el.hasClass("active")) {
        return;
      }
      event.preventDefault();
      this.el.addClass("active");
      this._block.addClass("active");
    },
    _onReject: function(event) {
      this.el.removeClass("active");
      this._block.removeClass("active");
    }
  };
});
