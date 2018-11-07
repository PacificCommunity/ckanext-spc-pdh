ckan.module("clonable-fieldset", function($, _) {
  "use strict";
  return {
    options: {
      wildcard: null,
      i: 0,
      buttonTpl:
        '<button type="button" class="btn btn-success btn-add-fieldset"><i class="fa fa-plus"/> Add</button>',
      wildcardedProps: ["id", "data-target", "name", "for"]
    },
    initialize: function() {
      $.proxyAll(this, /_on/);
      var addButton = $(this.options.buttonTpl).on("click", this._onAddClick);

      this.el.after(addButton);
    },
    _onAddClick: function() {
      this.el.find(".select2-container").remove();
      this.el.find(".select2-offscreen").removeClass("select2-offscreen");
      var clone = this.el.clone();
      clone.find(".btn-add-fieldset").remove();
      var propNames = this.options.wildcardedProps;
      var wildcard = this.options.wildcard;
      var idx = this.options.i;
      clone.prop("disabled", false).attr("data-module", null);
      for (var i = 0; i < propNames.length; i++) {
        $("[" + propNames[i] + '*="' + wildcard + '"]', clone).each(function() {
          $(this).attr(
            propNames[i],
            $(this)
              .attr(propNames[i])
              .replace(wildcard, idx)
          );
        });
      }

      ++this.options.i;
      this.el.before(clone);
      clone.show(400);
      clone.find("[data-module]").each(function() {
        ckan.module.initializeElement(this);
      });
    }
  };
});
