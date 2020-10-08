ckan.module("spc-advanced-search", function ($, _) {
  function searchKeys() {
    return window.location.search
      .slice(1)
      .split("&")
      .map(function (val) {
        return val.split("=")[0];
      });
  }
  function getUrlVars() {
    return window.location.search
      .slice(1)
      .split("&")
      .map(function (param) {
        var pair = param.split("=");
        if (pair[0].indexOf("ext_advanced_") === 0) {
          return [pair[0].slice(13), pair[1]];
        }
        return null;
      })
      .filter(Boolean);
  }
  return {
    options: {},
    initialize: function () {
      SPCWidgets.SearchForm.facets$.set(
        fetch(
          this.sandbox.client.url(
            "api/action/package_search?rows=0&facet.field=[%22type%22,%22topic%22,%22member_countries%22,%22res_format%22,%22organization%22]"
          )
        )
          .then((resp) => resp.json())
          .then((data) => data.result.search_facets)
      );

      var grouped = getUrlVars().reduce(
        function (result, next) {
          result[next[0]].push(next[1]);
          return result;
        },
        { operator: [], type: [], value: [] }
      );
      var filters = [];
      var keys = searchKeys();
      for (var i = 0; i < grouped.type.length; ++i) {
        if (~keys.indexOf(grouped.type[i])) {
          continue;
        }
        filters.push({
          operator: grouped.operator[i],
          type: grouped.type[i],
          value: decodeURIComponent(grouped.value[i]),
        });
      }

      if (filters.length) {
        SPCWidgets.SearchForm.filters.init(filters);
      }

      new SPCWidgets.SearchForm({
        target: this.el[0],
        props: {},
      });
    },
  };
});
