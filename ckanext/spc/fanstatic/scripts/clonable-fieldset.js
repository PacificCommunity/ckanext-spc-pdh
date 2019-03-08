ckan.module('clonable-fieldset', function($, _) {
  'use strict';
  return {
    options: {
      multiple: true,
      wildcard: null,
      i: 0,
      buttonTpl:
        '<button type="button" class="btn btn-success btn-add-fieldset"><i class="fa fa-plus"/> Add</button>',
      wildcardedProps: ['id', 'data-target', 'name', 'for', 'onclick']
    },
    initialize: function() {
      $.proxyAll(this, /_on/);

      this._addButton = $(this.options.buttonTpl);
      this._addButton.on('click', this._onAddClick);
      this.el.after(this._addButton);

      ckan.pubsub.subscribe('clonable-fieldset', this._onSubscription);
      this.updateAvailability();
    },

    updateAvailability() {
      if (!this.options.multiple && this.el.siblings('fieldset').length) {
        this._addButton.prop('disabled', true);
      } else {
        this._addButton.prop('disabled', false);
      }
    },

    _onSubscription: function(action, target) {
      var el;
      if ('remove' === action) {
        el = document.getElementById(target);
        console.log(arguments, el, target);
        if (!el) {
          return;
        }
        el.remove();
      }
      this.updateAvailability();
    },

    _onAddClick: function() {
      this.el.find('.select2-container').remove();
      this.el.find('.select2-offscreen').removeClass('select2-offscreen');
      var clone = this.el.clone();
      clone.find('.btn-add-fieldset').remove();
      var propNames = this.options.wildcardedProps;
      var wildcard = this.options.wildcard;
      var idx = this.options.i;
      clone.prop('disabled', false).attr('data-module', null);
      for (var i = 0; i < propNames.length; i++) {
        clone.attr(propNames[i]) && clone.attr(propNames[i], clone.attr(propNames[i]).replace(wildcard, idx));
        $('[' + propNames[i] + '*="' + wildcard + '"]', clone).each(function() {
          $(this).attr(
            propNames[i],
            $(this)
              .attr(propNames[i])
              .replace(wildcard, idx)
          );
        });
      }

      ++this.options.i;
      this.el.before(clone);
      clone.show(400);

      clone.find('[data-module]').each(function() {
        ckan.module.initializeElement(this);
      });

      clone.find('.select2-container').remove();
      clone.find('[data-module="autocomplete"]').each(function() {
        ckan.module.initializeElement(this);
      });

      this.updateAvailability();
    }
  };
});
