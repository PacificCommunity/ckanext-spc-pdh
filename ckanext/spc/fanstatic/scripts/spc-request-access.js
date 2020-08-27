ckan.module("spc-request-access", function ($) {
  "use strict";
  return {
    initialize: function () {
      this.el.on("submit", this._onSubmit.bind(this));

      $('#request-reason').prop('required', true);
    },
    teardown: function () {
      this.el.off("submit");
    },

    _onSubmit: function (e) {
      var self = this;
      e.preventDefault();
      this.sandbox.ajax(ckan.url("/dataset/request_for_access"), {
        method: "POST",
        data: this.el.serialize(),
        success: function (resp) {
          if (resp['message']) {
            self._afterRequest(resp['message']);
          }
        },
        error: function (err) {
          console.warn(err);
          self._afterRequest();
        },
      });
    },
    _afterRequest: function (message = null) {
      this.el.closest(".modal").modal("hide");
      const successModal = $("#request-access-modal-success");

      successModal.modal();
      if (message) (
        successModal.find('.modal-title').text(message)
      )
      setTimeout(function () {
        successModal.modal("hide")
      }, 10000)
    },
  };
});
