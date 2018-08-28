# encoding: utf-8

import logging

import ckan.logic as logic
import ckan.lib.base as base
import ckan.model as model
import ckan.lib.plugins
import ckan.lib.helpers as h
from ckan.common import g, _, request

import ckanext.scheming.helpers as scheming_helpers

log = logging.getLogger(__name__)
render = base.render
abort = base.abort


class PackageController(base.BaseController):
    def choose_type(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': g.user,
            'auth_user_obj': g.userobj
        }
        # Package needs to have a organization group in the call to
        # check_access and also to save it
        try:
            logic.check_access('package_create', context)
        except logic.NotAuthorized:
            abort(403, _('Unauthorized to create a package'))

        errors = {}
        error_summary = {}
        if 'POST' == request.method:
            try:
                dataset_type = request.params['type']
            except KeyError:
                errors = {'type': [_('Dataset type must be provided')]}
                error_summary = {
                    key.title(): value[0] for key, value in errors.items()
                }
            else:
                return h.redirect_to('/' + dataset_type + '/new')

        options = [
            {
                'text': schema['about'],
                'value': schema['dataset_type']
            } for schema in
            sorted(scheming_helpers.scheming_dataset_schemas().values())
        ]
        data = {
            'form_vars': {
                'options': options,
                'error_summary': error_summary,
                'errors': errors,
            },
            'form_snippet': 'package/snippets/choose_type_form.html'
        }
        return render('package/choose_type.html', data)
