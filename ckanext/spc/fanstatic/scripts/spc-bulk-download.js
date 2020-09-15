ckan.module("spc-bulk-download", function ($) {
  "use strict";

  return {
    options: {
      queryString: "",
    },
    initialize: function () {
      this._bulkDownload = this._bulkDownload.bind(this);
      this._enable = this._enable.bind(this);
      this.el.on("click", this._bulkDownload);

      this.sandbox.subscribe(ckan.TOPICS.FPX_TICKET_AVAILABLE, this._enable);
      this.sandbox.subscribe(ckan.TOPICS.FPX_CANCEL_DOWNLOAD, this._enable);
    },
    teardown: function () {
      this.sandbox.unsubscribe(ckan.TOPICS.FPX_CANCEL_DOWNLOAD, this._enable);
      this.sandbox.unsubscribe(ckan.TOPICS.FPX_TICKET_AVAILABLE, this._enable);

      this.el.off("click", this._bulkDownload);
    },
    _bulkDownload: function () {
      var sandbox = this.sandbox;
      sandbox.ajax(this.options.queryString).then(function (ids) {
        sandbox.publish(ckan.TOPICS.FPX_ORDER_TICKET, "package", ids);
      });
      this.el.attr("disabled", true);
    },
    _enable: function () {
      this.el.attr("disabled", false);
    },
  };
});
