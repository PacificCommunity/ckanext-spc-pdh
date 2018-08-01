/* Module for handling the spatial querying
 */
this.ckan.module('spatial-select', function ($, _) {

  return {
    options: {
      i18n: {
      },
      style: {
        color: '#F06F64',
        weight: 2,
        opacity: 1,
        fillColor: '#F06F64',
        fillOpacity: 0.1,
        clickable: false
      },
      default_extent: [[90, 180], [-90, -180]]
    },

    initialize: function () {
      var module = this;
      $.proxyAll(this, /_on/);

      var user_default_extent = this.el.data('default_extent');
      if (user_default_extent ){
	if (user_default_extent instanceof Array) {
          // Assume it's a pair of coords like [[90, 180], [-90, -180]]
          this.options.default_extent = user_default_extent;
	} else if (user_default_extent instanceof Object) {
          // Assume it's a GeoJSON bbox
          this.options.default_extent = new L.GeoJSON(user_default_extent).getBounds();
	}
      }
      this.el.ready(this._onReady);
    },


    _drawExtentFromCoords: function(xmin, ymin, xmax, ymax) {
      if ($.isArray(xmin)) {
	var coords = xmin;
	xmin = coords[0]; ymin = coords[1]; xmax = coords[2]; ymax = coords[3];
      }
      return new L.Rectangle([[ymin, xmin], [ymax, xmax]],
                             this.options.style);
    },

    _drawExtentFromGeoJSON: function(geom) {
      return new L.GeoJSON(geom, {style: this.options.style});
    },

    _onReady: function() {

      var module = this;
      var map;
      var extentLayer;
      var spatialField = $('#field-spatial');
      // OK map time
      map = ckan.commonLeafletMap(
	'dataset-map-container',
	this.options.map_config,
	{
          attributionControl: false,
          drawControlTooltips: false
	}
      );

      // Initialize the draw control
      map.addControl(new L.Control.Draw({
	position: 'topright',
	draw: {
          polyline: false,
          polygon: false,
          circle: false,
          marker: false,
          rectangle: {shapeOptions: module.options.style}
	}
      }));


      // When user finishes drawing the box, record it and add it to the map
      map.on('draw:created', function (e) {
	if (extentLayer) {
          map.removeLayer(extentLayer);
	}
	extentLayer = e.layer;
	ckan.pubsub.publish('inner_layer_change', extentLayer);
	map.addLayer(extentLayer);

        // $('body').removeClass('dataset-map-expanded');
        resetMap();
        // Eugh, hacky hack.
        requestAnimationFrame(function() {
	  map.fitBounds(extentLayer.getBounds());
	  spatialField.val(JSON.stringify(extentLayer.toGeoJSON().geometry));
	});

      });

      ckan.pubsub.subscribe('outer_layer_change', function (coords) {
          setBBBox([coords[1], coords[0], coords[3], coords[2]]);

      });
      map.fitBounds(this.options.default_extent);

      setExistingBBBox();

      function setExistingBBBox() {
	var val = spatialField.val();
	if (!val) {
	  return;
	}
	var geoJSON = JSON.parse(val);
	extentLayer = module._drawExtentFromGeoJSON(geoJSON);
        map.addLayer(extentLayer);
	map.fitBounds(extentLayer.getBounds());
	ckan.pubsub.publish('inner_layer_change', extentLayer);
      }

      function setBBBox(bbox) {
	map.removeLayer(extentLayer);
        extentLayer = module._drawExtentFromCoords(bbox);
        map.addLayer(extentLayer);
	map.fitBounds(extentLayer.getBounds());
	spatialField.val(JSON.stringify(extentLayer.toGeoJSON().geometry));
      }

      // Reset map view
      function resetMap() {
	L.Util.requestAnimFrame(map.invalidateSize, map, !1, map._container);
      }
    }
  };
});
