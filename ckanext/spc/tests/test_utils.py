import nose.tools as nt
import ckan.model as model
from ckan.tests.helpers import call_action, FunctionalTestBase
from ckan.tests.legacy.pylons_controller import PylonsTestCase
import ckanext.spc.utils as utils
from ckanext.spc.tests.test_helpers import cli
from nose.tools import eq_, assert_raises


def test_normalize_res():
    original = dict(name='a', description='b', format='c', size=1, url='d')
    expected = dict(
        title='a', description='b', format='c', byteSize=1, accessURL='d'
    )

    nt.assert_dict_equal(expected, utils._normalize_res(original))


def test_normalize_to_dcat():
    pkg = dict(
        id='a',
        notes='b',
        name='c',
        tags=[dict(name='x'), dict(name='y')],
        frequency='d',
        metadata_created='e',
        metadata_modified='f'
    )
    expected = dict(
        identifier='a',
        description='b',
        landingPage='http://test.ckan.net/dataset/c',
        keyword=['x', 'y'],
        accrualPeriodicity='d',
        issued='e',
        modified='f',
        contactPoint='',
        publisher={
            'name': '',
            'mbox': ''
        },
        distribution=[],
        temporal=[None, None],
        name='c',
    )

    nt.assert_dict_equal(expected, utils.normalize_to_dcat(pkg))


def test_normalize_search_query():
    eq_('a a', utils._normalize_search_query('A A'))
    eq_('a a', utils._normalize_search_query('a a'))
    eq_('a a', utils._normalize_search_query('      a            A    '))
