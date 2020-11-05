# -*- coding: utf-8 -*-
import os
import logging
import csv
from io import StringIO
from werkzeug.wrappers import Response

from datetime import datetime
from flask import Blueprint, send_file
from flask.views import MethodView

import ckan.model as model
import ckan.views.api as api
import ckan.lib.jobs as jobs
import ckan.lib.helpers as h
import ckan.lib.plugins
import ckan.lib.base as base

from ckan.common import _, g, request
from ckan.plugins import toolkit

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


class IndexView(MethodView):
    def __init__(self):
        context= {
            'model': model,
            'session': model.Session,
            'user': g.user,
            'auth_user_obj': g.userobj
        }
        try:
            toolkit.check_access('sysadmin', context)
        except toolkit.NotAuthorized:
            base.abort(403, _('Need to be system administrator'))

    def post(self):
        action = request.form.get('action')
        query_name = request.form.get('q_name')
        if not action or not query_name:
            return base.abort(409, _('Missing request parameter'))
        query = model.Session.query(SearchQuery).filter(
            SearchQuery.query == query_name).first()
        if query is None:
            return base.abort(404, _('Search query not found'))
        if action == 'delete':
            model.Session.delete(query)
            h.flash_success(_('The query has been removed'))
        elif action == 'update':
            value = request.form.get('q_value')
            if value:
                query.query = value
                h.flash_success(_('The query has been updated'))
        model.Session.commit()
        return toolkit.redirect_to('search_queries.index')

    def get(self):
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


def download_search_queries():
    def generate():
        data = StringIO()
        w = csv.writer(data)
        queries = model.Session.query(SearchQuery).order_by(
            SearchQuery.count.desc())
        w.writerow(('Query', 'Counter'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        for item in queries:
            w.writerow((item.query, item.count))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="queries.csv")
    return response


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
    "/ckan-admin/search-queries", view_func=IndexView.as_view('index'), methods=(u'GET', u'POST')
)

search_queries.add_url_rule(
    "/ckan-admin/search-queries/download", view_func=download_search_queries, methods=(u'GET',)
)


blueprints = [spc_user, spc_admin, spc_package,
              search_queries, spc_access_request]
