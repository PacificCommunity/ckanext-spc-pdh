/**
 * Listen to `data-module-events` and every time the event is fired,
 * search for element, specified by `data-edit-destination` attribute
 * of the event.target and update it's value using textContent of the
 * event.target
 */
ckan.module("spc-editable-container", function ($) {
  "use strict";
  return {
    options: {
      events: [],
      destinationAttribute: "editDestination",
    },
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.el.on(this.options.events.join(" "), this._onEdit);
    },
    _onEdit: function (e) {
      var dest = e.target.dataset[this.options.destinationAttribute];
      if (!dest) {
        console.warn("Missing edit destination", e.target);
      }
      $(dest).val(e.target.textContent);
    },
  };
});
