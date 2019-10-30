# encoding: utf-8

import logging

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model

from ckan.common import g, _, request

from ckanext.spc.model.search_query import SearchQuery

log = logging.getLogger(__name__)
render = base.render
abort = base.abort

PER_PAGE = 20


class SearchQueryController(base.BaseController):

    def index(self):
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
            model.Session.query(SearchQuery).filter(SearchQuery.query == query_name).delete()
            model.Session.commit()

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
