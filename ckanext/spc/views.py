# -*- coding: utf-8 -*-
import os
from datetime import datetime

from flask import Blueprint, send_file

import ckan.lib.jobs as jobs
import ckan.model as model
from ckan.common import _, g, request
from ckan.plugins import toolkit
import ckan.lib.helpers as h

from ckanext.spc.jobs import broken_links_report


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


spc_user = Blueprint('spc_user', __name__)
spc_admin = Blueprint('spc_admin', __name__)

spc_user.add_url_rule(u'/user/switch_admin_state/<id>',
                      view_func=switch_admin_state,
                      methods=(u'POST', ))
spc_admin.add_url_rule(u'/ckan-admin/broken-links',
                       view_func=broken_links,
                       methods=(u'GET', u'POST'))
blueprints = [spc_user, spc_admin]
