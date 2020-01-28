# -*- coding: utf-8 -*-
import os
import logging
from datetime import datetime
from flask import Blueprint, send_file

import ckan.lib.jobs as jobs
import ckan.model as model
from ckan.common import _, g, request
from ckan.plugins import toolkit
import ckan.lib.helpers as h
import ckan.lib.plugins
import ckan.lib.base as base

from ckanext.spc.jobs import broken_links_report
import ckanext.scheming.helpers as scheming_helpers


log = logging.getLogger(__name__)
render = base.render
abort = base.abort


def switch_admin_state(id):
    if not toolkit.check_access('sysadmin', {'user': g.user}):
        return toolkit.abort(403, _('Not authorized'))

    user = model.User.get(id)
    if not user:
        return toolkit.abort(404, _('User does not exist'))
    if g.user == user.name:
        return toolkit.abort(403, _('Not authorized'))
    user.sysadmin = not user.sysadmin
    user.save()

    return toolkit.redirect_to('user.read', id=id)


def broken_links():
    QUEUE_NAME = 'default'
    queue = jobs.get_queue(QUEUE_NAME)
    queue._default_timeout = 3600 * 24
    try:
        toolkit.check_access('sysadmin', {'user': g.user, model: model})
    except toolkit.NotAuthorized:
        return toolkit.abort(403)
    filepath = toolkit.config['spc.report.broken_links_filepath']
    try:
        last_check = datetime.fromtimestamp(os.stat(filepath).st_mtime)
    except OSError:
        last_check = None
    active_jobs_count = jobs.get_queue(QUEUE_NAME).count
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'download' and last_check:
            return send_file(
                filepath,
                as_attachment=True,
                attachment_filename='SPC-BrokenLinks-{:%Y-%m-%d}.csv'.format(
                    last_check))

        elif action == 'start':
            jobs.enqueue(broken_links_report,
                         kwargs={'recepients': [g.user]},
                         queue=QUEUE_NAME)
            h.flash_notice('Report generation in progress. '
                           'You will recieve email notification '
                           'as soon as report finished')
            return h.redirect_to('spc_admin.broken_links')
    if active_jobs_count:
        h.flash_error('There are unfinished '
                      'report generation processes in progress. '
                      'You will not be able to manually start checker '
                      'until they are finished.')
    extra_vars = {
        'last_check': last_check,
        'active_jobs_count': active_jobs_count
    }
    return toolkit.render('admin/broken_links.html', extra_vars)


def choose_type():
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
                key.title(): value[0]
                for key, value in errors.items()
            }
        else:
            return h.redirect_to(
                'spc_dataset.new', package_type=dataset_type
            )

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


spc_user = Blueprint('spc_user', __name__)
spc_admin = Blueprint('spc_admin', __name__)
spc_package = Blueprint('spc_package', __name__)

spc_user.add_url_rule(u'/user/switch_admin_state/<id>',
                      view_func=switch_admin_state,
                      methods=(u'POST', ))

spc_admin.add_url_rule(u'/ckan-admin/broken-links',
                       view_func=broken_links,
                       methods=(u'GET', u'POST'))


spc_package.add_url_rule(
    "/dataset/new/choose_type", view_func=choose_type
)

blueprints = [spc_user, spc_admin, spc_package]