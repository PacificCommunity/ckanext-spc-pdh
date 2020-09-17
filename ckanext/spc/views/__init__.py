# -*- coding: utf-8 -*-
import os
import logging

from datetime import datetime
from flask import Blueprint, send_file

import ckan.lib.jobs as jobs
import ckan.model as model
from ckan.common import _, g, request
from ckan.plugins import toolkit
import ckan.views.api as api

import ckan.lib.helpers as h
import ckan.lib.plugins
import ckan.lib.base as base

from ckan.common import _, g, request
from ckan.plugins import toolkit
from ckan.logic import NotAuthorized, check_access

import ckanext.scheming.helpers as scheming_helpers

from ckanext.spc.jobs import broken_links_report
from ckanext.spc.model.search_query import SearchQuery
from ckanext.spc.views.access_request import spc_access_request
from ckanext.spc.views.package import spc_package

log = logging.getLogger(__name__)
render = base.render
abort = base.abort

PER_PAGE = 20


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


def index():
    context = {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'auth_user_obj': g.userobj
    }
    # Package needs to have a organization group in the call to
    # check_access and also to save it
    try:
        logic.check_access('sysadmin', context, {})
    except logic.NotAuthorized:
        base.abort(403, _('Need to be system administrator'))

    if request.method == 'POST':
        query_name = request.POST['q_name']
        model.Session.query(SearchQuery).filter(
            SearchQuery.query == query_name).delete()
        model.Session.commit()
        h.flash_success(_('The query has been removed'))

    page = h.get_page_number(request.params)
    total = model.Session.query(SearchQuery).count()
    queries = model.Session.query(SearchQuery).order_by(
        SearchQuery.count.desc()
    ).limit(PER_PAGE).offset((page - 1) * PER_PAGE)
    pager = h.Page(
        collection=queries,
        page=page,
        url=lambda page: h.url_for('search_queries.index', page=page),
        item_count=total,
        items_per_page=PER_PAGE
    )

    return render(
        'search_queries/index.html', {
            'queries': queries,
            'pager': pager
        }
    )


spc_user = Blueprint('spc_user', __name__)
spc_admin = Blueprint('spc_admin', __name__)
search_queries = Blueprint('search_queries', __name__)

spc_user.add_url_rule(u'/user/switch_admin_state/<id>',
                      view_func=switch_admin_state,
                      methods=(u'POST', ))

spc_admin.add_url_rule(u'/ckan-admin/broken-links',
                       view_func=broken_links,
                       methods=(u'GET', u'POST'))

search_queries.add_url_rule(
    "/ckan-admin/search-queries", view_func=index, methods=(u'GET', u'POST')
)

blueprints = [spc_user, spc_admin, spc_package,
              search_queries, spc_access_request]
