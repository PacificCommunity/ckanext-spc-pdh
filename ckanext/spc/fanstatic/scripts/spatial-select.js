/* Module for handling the spatial querying
 */
this.ckan.module("spatial-select", function($, _) {
  if (window.L) {
    window.L.Browser.touch = false;
  }
  return {
    options: {
      i18n: {},
      style: {
        color: "#F06F64",
        weight: 2,
        opacity: 1,
        fillColor: "#F06F64",
        fillOpacity: 0.1,
        clickable: false
      },
      default_extent: [[90, 180], [-90, -180]]
    },

    initialize: function() {
      var module = this;
      $.proxyAll(this, /_on/);

      var user_default_extent = this.el.data("default_extent");
      if (user_default_extent) {
        if (user_default_extent instanceof Array) {
          // Assume it's a pair of coords like [[90, 180], [-90, -180]]
          this.options.default_extent = user_default_extent;
        } else if (user_default_extent instanceof Object) {
          // Assume it's a GeoJSON bbox
          this.options.default_extent = new L.GeoJSON(
            user_default_extent
          ).getBounds();
        }
      }
      this.el.ready(this._onReady);
    },

    _drawExtentFromCoords: function(xmin, ymin, xmax, ymax) {
      if ($.isArray(xmin)) {
        var coords = xmin;
        xmin = coords[0];
        ymin = coords[1];
        xmax = coords[2];
        ymax = coords[3];
      }
      return new L.Rectangle([[ymin, xmin], [ymax, xmax]], this.options.style);
    },

    _drawExtentFromGeoJSON: function(geom) {
      return new L.GeoJSON(geom, { style: this.options.style });
    },

    flattenToCoordinates: function(geoJSON) {
      var features = geoJSON.features;
      var result = [];
      for (var i = 0; i < features.length; i++) {
        if (features[i].geometry.coordinates) {
          result.push(features[i].geometry.coordinates);
        } else {
          features[i].geometry.features.forEach(function(f) {
            features.push(f);
          });
        }
      }
      return result;
    },
    _onReady: function() {
      var module = this;
      var map;
      var spatialField = $("#field-spatial");

      // spatialField.on('change', setExistingBBBox);
      spatialField.on("input", function(e) {
        e.target.value = e.target.value.split("\n").join("");
        try {
          $("#formatted-spatial").text(
            JSON.stringify(JSON.parse(e.target.value), null, 2)
          );
          setExistingBBBox();
        } catch (e) {}
      });
      spatialField.trigger("input");

      $("#predefined_areas").on("change", function(event) {
        var val = { type: "MultiPolygon", coordinates: [] };
        if (event.val === "all") {
          Array.prototype.slice
            .apply(event.target.options, [0])
            .forEach(function(option) {
              var item = option.value;
              if (!item || item === "all") {
                return;
              }
              var geoJson = JSON.parse(item);
              var coord =
                geoJson.type === "MultiPolygon"
                  ? geoJson.coordinates
                  : [geoJson.coordinates];
              val.coordinates = val.coordinates.concat(coord);
            });
        } else {
          val.coordinates = val.coordinates.concat(
            event.val.map(function(item) {
              var geoJson = JSON.parse(item);
              return geoJson.type === "MultiPolygon"
                ? geoJson.coordinates[0]
                : geoJson.coordinates;
            })
          );
        }
        val = val.coordinates.length ? JSON.stringify(val) : "";

        spatialField.val(val).trigger("input");
      });
      // OK map time
      map = ckan.commonLeafletMap(
        "dataset-map-container",
        module.options.map_config,
        {
          attributionControl: false,
          drawControlTooltips: false
        }
      );
      L.drawLocal.edit.toolbar.buttons.remove = "Delete last layer.";

      var editableLayers = new L.FeatureGroup();
      map.addLayer(editableLayers);
      // Initialize the draw control
      map.addControl(
        new L.Control.Draw({
          position: "topright",
          draw: {
            undo: true,
            polyline: false,
            polygon: {
              shapeOptions: module.options.style,
              allowIntersection: false
            },
            circle: false,
            marker: false,
            rectangle: { shapeOptions: module.options.style }
          },
          edit: {
            featureGroup: editableLayers,
            edit: false,
            remove: true
          }
        })
      );

      // When user finishes drawing the box, record it and add it to the map
      map.on("draw:created", function(e) {
        var extentLayer = e.layer;
        ckan.pubsub.publish("inner_layer_change", extentLayer);
        editableLayers.addLayer(extentLayer);

        resetMap();
        // Eugh, hacky hack.
        requestAnimationFrame(function() {
          map.fitBounds(extentLayer.getBounds());
          updateSpatialField();
        });
      });

      $(".leaflet-draw-edit-remove").on("click", function() {
        removeLastLayer();
        updateSpatialField();
        var extentLayer = editableLayers.getLayers().shift();
        if (extentLayer) {
          map.fitBounds(extentLayer.getBounds());
          ckan.pubsub.publish("inner_layer_change", extentLayer);
        }
      });

      ckan.pubsub.subscribe("outer_layer_change", function(coords) {
        setBBBox([coords[1], coords[0], coords[3], coords[2]]);
      });
      map.fitBounds(module.options.default_extent);

      setExistingBBBox();

      function updateSpatialField() {
        var coordinates = module.flattenToCoordinates(
          editableLayers.toGeoJSON()
        );

        spatialField.val(
          coordinates.length
            ? JSON.stringify({
                type: coordinates.length > 1 ? "MultiPolygon" : "Polygon",
                coordinates:
                  coordinates.length > 1 ? coordinates : coordinates[0]
              })
            : ""
        );
        // spatialField.trigger('change');
        spatialField.trigger("input");
      }
      function removeLastLayer() {
        var layers = editableLayers.getLayers();
        var last = layers.shift();
        if (last) {
          editableLayers.removeLayer(last);
        }
      }

      function setExistingBBBox() {
        var val = spatialField.val();
        if (!val) {
          return;
        }
        try {
          new L.GeoJSON(JSON.parse(val));
        } catch (e) {
          spatialField.closest(".control-group").addClass("error");
          return;
        }
        spatialField.closest(".control-group").removeClass("error");

        editableLayers.clearLayers();
        var geoJSON = JSON.parse(val);
        var extentLayer;
        if (geoJSON.type === "MultiPolygon") {
          for (var i = 0; i < geoJSON.coordinates.length; i++) {
            coord = geoJSON.coordinates[i];
            extentLayer = module._drawExtentFromGeoJSON({
              type: "Polygon",
              coordinates: coord
            });
            editableLayers.addLayer(extentLayer);
          }
        } else {
          extentLayer = module._drawExtentFromGeoJSON(geoJSON);
          editableLayers.addLayer(extentLayer);
        }
        map.fitBounds(extentLayer.getBounds());
        ckan.pubsub.publish("inner_layer_change", extentLayer);
      }

      function setBBBox(bbox) {
        removeLastLayer();

        var extentLayer = module._drawExtentFromCoords(bbox);
        editableLayers.addLayer(extentLayer);
        map.fitBounds(extentLayer.getBounds());
        updateSpatialField();
      }

      // Reset map view
      function resetMap() {
        L.Util.requestAnimFrame(map.invalidateSize, map, !1, map._container);
      }
    }
  };
});
