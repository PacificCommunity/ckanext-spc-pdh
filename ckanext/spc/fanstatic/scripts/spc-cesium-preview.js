ckan.module("spc-cesium-preview", function () {
  return {
    initialize: function () {
      this._btn = $(
        '<button class="btn btn-default spc-open-on-pacific-map">' +
          '<i class="fa fa-clone"> </i> ' +
          "Open in PacificMap" +
          "</button>"
      );
      this._btn.on("click", this._onClick.bind(this));
      this.el.after(this._btn);
    },
    _onClick: function () {
      console.log(this.el);
    },
  };
});
