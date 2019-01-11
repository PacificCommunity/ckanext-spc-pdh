from nose.tools import eq_

from ckanext.spc.model import SearchQuery
import ckan.model as model


def test_update_or_create():
    model.Session.remove()

    q = SearchQuery.update_or_create('a')
    eq_(q.query, 'a')
    eq_(q.count, 1)

    model.Session.flush()

    q = SearchQuery.update_or_create('a')
    eq_(q.query, 'a')
    eq_(q.count, 2)

    model.Session.flush()

    q = SearchQuery.update_or_create('b')
    eq_(q.query, 'b')
    eq_(q.count, 1)

    model.Session.flush()

    total = model.Session.query(SearchQuery).count()
    eq_(2, total)
