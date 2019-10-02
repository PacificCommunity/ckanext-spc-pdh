ckan.module('spc-sortable-facets', function($, _) {
  'use strict';
  return {
    options: {
      selector: '.nav-facet .nav-item'
    },
    initialize: function() {
      this._enumerateFacets(this._findFacets());
      this.el.on('click', this._onHeadingClick.bind(this));
    },

    _findFacets: function() {
      return this.el.parent().find(this.options.selector);
    },
    _enumerateFacets: function(facets) {
      facets.each(function(idx, el) {
        el.style.order = idx;
      });
    },

    _onHeadingClick: function(event) {
      var btn = $(event.target);
      if (btn.is('i')) {
        btn = btn.parent();
      }
      var sortType = btn.data('sortType');
      if (!sortType) {
        return;
      }

      this.el
        .find('.facet-sorter')
        .not(btn)
        .removeClass('active reverse');
      btn.hasClass('active')
        ? btn.toggleClass('reverse')
        : btn.addClass('active');

      var reverse = btn.hasClass('reverse');

      this._rearrangeFacets(
        this._findFacets(),
        this._comparators[sortType],
        reverse
      );
    },

    _rearrangeFacets: function(facets, comparator, reverse = false) {
      var parent = facets.parent();
      facets
        .sort(function(l, r) {
          return comparator(l, r) * (reverse ? -1 : 1);
        })
        .each(function(idx, item) {
          item.style.order = idx;
        });
    },

    _comparators: {
      'data-name': function(l, r) {
        return l.dataset.name.localeCompare(r.dataset.name);
      },
      'data-number': function(l, r) {
        return l.dataset.number - r.dataset.number;
      }
    }
  };
});
