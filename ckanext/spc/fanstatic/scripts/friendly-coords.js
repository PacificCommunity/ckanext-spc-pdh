
ckan.module('friendly-coords', function($, _){
  "use strict";
  return {
    initialize: function(){
      $.proxyAll(this, /_on/);
      var prefix = '#' + this.el.prop('name');

      this._s = $(prefix + '-s').on('change.friendly-coord', this._onOneCoordChanged);
      this._w = $(prefix + '-w').on('change.friendly-coord', this._onOneCoordChanged);
      this._n = $(prefix + '-n').on('change.friendly-coord', this._onOneCoordChanged);
      this._e = $(prefix + '-e').on('change.friendly-coord', this._onOneCoordChanged);


      ckan.pubsub.subscribe('inner_layer_change', this._onMapChanged);
    },

    _onOneCoordChanged: function (event) {
      var duplicate = false;
      var values = [
	this._convertStrToFloat(this._s.val()),
	this._convertStrToFloat(this._w.val()),
	this._convertStrToFloat(this._n.val()),
	this._convertStrToFloat(this._e.val()),
      ];
      if (values.some(isNaN)) return;

      var invalid = $(':invalid').filter('[id^=spatial_coverage-]');
      var valid = $(':valid').filter('[id^=spatial_coverage-]');

      if (values[0] === values[2]) {
	invalid = invalid.add(this._n).add(this._s);
	invalid.tooltip({title: 'North and South boundaries can\'t match. Line and point extents are not supported.'});
      } else {
	this._n.add(this._s).tooltip('destroy');
      }

      if (values[1] === values[3]) {
	invalid = invalid.add(this._e).add(this._w);
	invalid.tooltip({title: 'East and West boundaries can\'t match. Line and point extents are not supported.'});
      } else {
	this._e.add(this._w).tooltip('destroy');
      }

      valid.closest('.control-group').removeClass('error');

      if (invalid.length) {
	$('[type=submit]').prop('disabled', true);
	invalid.closest('.control-group').addClass('error');
	return;
      }
      $('[type=submit]').prop('disabled', false);

      ckan.pubsub.publish('outer_layer_change', values);

    },

    _onMapChanged: function (rect) {
      var values = rect.getBounds().toBBoxString().split(',');
      this._w.val(this._convertStrToFloat(values[0]));
      this._s.val(this._convertStrToFloat(values[1]));
      this._e.val(this._convertStrToFloat(values[2]));
      this._n.val(this._convertStrToFloat(values[3]));
    },

    _convertStrToFloat: function (str) {
      return parseFloat(str).toFixed(5);
    }
  };
});
