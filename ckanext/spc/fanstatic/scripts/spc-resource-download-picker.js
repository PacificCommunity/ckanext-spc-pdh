ckan.module("spc-resource-download-picker", function ($) {
  "use strict";

  return {
    options: {},
    _ids: [],
    initialize: function () {
      this._bulkDownload = this._bulkDownload.bind(this);
      this._enable = this._enable.bind(this);
      this._disable = this._disable.bind(this);
      this._onCheck = this._onCheck.bind(this);
      this.el.on("click", this._bulkDownload);

      this.sandbox.subscribe(ckan.TOPICS.FPX_TICKET_AVAILABLE, this._enable);
      this.sandbox.subscribe(ckan.TOPICS.FPX_CANCEL_DOWNLOAD, this._enable);

      $("#dataset-resources .resource-picker :checkbox").on(
        "change",
        this._onCheck
      );
    },
    _onCheck: function (e) {
      var id = e.target.dataset.id;
      if (e.target.checked) {
        this._ids.push(id);
      } else {
        this._ids = this._ids.filter(function (i) {
          return i !== id;
        });
      }
      this.el.find(".picked-counter").attr("data-count", this._ids.length);
    },
    teardown: function () {
      this.sandbox.unsubscribe(ckan.TOPICS.FPX_CANCEL_DOWNLOAD, this._enable);
      this.sandbox.unsubscribe(ckan.TOPICS.FPX_TICKET_AVAILABLE, this._enable);

      this.el.off("click", this._bulkDownload);
    },
    _bulkDownload: function () {
      var sandbox = this.sandbox;
      if (!this._ids.length) {
        return;
      }
      sandbox.publish(
        ckan.TOPICS.FPX_ORDER_TICKET,
        "resource",
        this._ids.map(function (id) {
          return { id: id };
        })
      );
      this.el.attr("disabled", true);
    },
    _disable: function () {
      this.el.attr("disabled", true);
    },

    _enable: function () {
      this.el.attr("disabled", false);
    },
  };
});
