import ckan.lib.helpers as h
from ckanext.ga_report.ga_model import GA_Url
import ckan.model as model

def _normalize_res(res):
    return {
        'title': res.get('name'),
        'description': res.get('description'),
        'format': res.get('format'),
        'byteSize': res.get('size'),
        'accessURL': res.get('url')
    }


def normalize_to_dcat(pkg_dict):
    pkg_dict['identifier'] = pkg_dict.pop('id')
    pkg_dict['description'] = pkg_dict.pop('notes', '')
    pkg_dict['landingPage'] = h.url_for(
        'dataset_read', id=pkg_dict['name'], qualified=True
    )
    pkg_dict['keyword'] = [tag['name'] for tag in pkg_dict.pop('tags', [])]

    pkg_dict['distribution'] = [
        _normalize_res(res) for res in pkg_dict.pop('resources', [])
    ]

    pkg_dict['publisher'] = dict(
        name=pkg_dict.pop('publisher', ''),
        mbox=pkg_dict.pop('publisher_email', '')
    )

    pkg_dict['contactPoint'] = pkg_dict.get('contact', '')
    if pkg_dict.get('contact_email'):
        pkg_dict['contactPoint'] += '<' + pkg_dict['contact_email'] + '>'

    pkg_dict['temporal'] = [
        pkg_dict.get('temporal_from'),
        pkg_dict.get('temporal_to')
    ]

    pkg_dict['accrualPeriodicity'] = pkg_dict.pop('frequency', '')
    pkg_dict['issued'] = pkg_dict.pop('metadata_created')
    pkg_dict['modified'] = pkg_dict.pop('metadata_modified')
    return pkg_dict


def ga_view_count(name):
    return model.Session.query(GA_Url.pageviews).filter(
        GA_Url.period_name == 'All',
        GA_Url.package_id == name
    ).scalar() or 0


class _EEZ:
    def __init__(self, collection):
        self.collection = collection

    def update(self, collection):
        self.collection = collection

    def __iter__(self):
        return iter(self.collection)


eez = _EEZ([])
