from bibtexparser import load

import ckan.plugins.toolkit as tk
from ckan.lib.munge import munge_title_to_name, munge_tag
import ckan.model as model


class MendeleyBib(object):

    def __str__(self):
        return tk.config.get(
            'ckanext.ingestor.label.mendeley_bib', 'IAEA Mendeley Bibtext'
        )

    def extract(self, source):
        return load(source).entries

    def process(self, record):
        data_dict = {
            'id': record['ID'],
            'title': record['title'].strip('{}'),
            'name': munge_title_to_name(record['ID'] + record['title']),
            'notes': record['abstract'],
            'harvest_source': 'MENDELEY',
            'creator': record['author'].split(','),
            'tag_string': ','.join(
                munge_tag(tag) for tag in record['keywords'].split(',')
            ),
            'owner_org': 'mendeley',
            'type': 'publications'
        }
        identifiers = []
        if 'doi' in record:
            identifiers.append('doi:' + record['doi'])
        if 'isbn' in record:
            identifiers.append('isbn:' + record['isbn'])
        if 'pmid' in record:
            identifiers.append('pmid:' + record['pmid'])
        data_dict['identifier'] = identifiers

        if 'editor' in record:
            data_dict['contributor'] = [record['editor']]
        if 'publisher' in record:
            data_dict['publisher'] = [record['publisher']]
        if 'language' in record:
            data_dict['language'] = [record['language']]

        data_dict['source'] = record.get('url')

        user = tk.get_action('get_site_user')({'ignore_auth': True})
        existing = model.Package.get(data_dict['id'])
        action = tk.get_action(
            'package_update' if existing else 'package_create'
        )
        action({'ignore_auth': True, 'user': user['name']}, data_dict)


[
    u'address', u'annote', u'booktitle', u'journal', u'mendeley-tags',
    u'number', u'pages'
    u'volume', u'year'
]
