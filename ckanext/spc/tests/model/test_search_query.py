import pytest
from ckanext.spc.model import SearchQuery
import ckan.model as model


@pytest.mark.usefixtures("clean_db")
def test_update_or_create():
    q = SearchQuery.update_or_create("a")
    assert q.query == "a"
    assert q.count == 1

    model.Session.flush()

    q = SearchQuery.update_or_create("a")
    assert q.query == "a"
    assert q.count == 2

    model.Session.flush()

    q = SearchQuery.update_or_create("b")
    assert q.query == "b"
    assert q.count == 1

    model.Session.flush()

    total = model.Session.query(SearchQuery).count()
    assert 2 == total
