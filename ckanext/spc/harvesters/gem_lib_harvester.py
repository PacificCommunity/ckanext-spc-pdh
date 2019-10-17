# -*- coding: utf-8 -*-

from sqlalchemy import func
import ckan.model as model
import json
import logging
import requests
import uuid
from operator import lt, itemgetter
import funcy as F

from ckanext.harvest.harvesters import HarvesterBase
from ckanext.harvest.model import HarvestObjectError, HarvestObject
from six.moves.urllib.parse import urljoin

log = logging.getLogger(__name__)


def _gl_url(base, resource):
    return urljoin(urljoin(base, 'libraryadmin/rest/'), resource)


def _map_gdl_to_publication(data_dict, obj):
    # thematic_area = data_dict.get('thematicArea', {}).get('area')

    dataset = {
        "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, str(data_dict['id']))),
        "type": "publications",
        "title": data_dict['title'],
        # "thematic_area_string": thematic_area,
        "creator": [a['name'] for a in data_dict['authors']],
        # "subject": data_dict,
        "notes": data_dict['description'],
        "publisher": data_dict.get('relatedOrganisation'),
        # "contributor": [a['name'] for a in data_dict['authors']],
        "date": data_dict.get('created'),
        "metadata_modified": data_dict.get('created'),
        # "publication_type": data_dict,
        # "format": data_dict,
        "identifier": data_dict['identifier'],
        "source": data_dict['source'],
        # "language": data_dict,
        # "relation": data_dict,
        # "spatial": data_dict,
        # "rights": data_dict,
        "license_id": 'notspecified',
        "member_countries": 'other',  # relatedCountry, optional
        "harvest_source": 'GDL'
    }
    if data_dict['file']:
        res_url = _gl_url(obj.source.url, 'download') + '?id=' + str(
            data_dict['id'])
        dataset['resources'] = [{'name': data_dict['file'], 'url': res_url}]
    return dataset


def must_be_ok(resp, exc, *exc_payload):
    if resp.ok:
        return resp
    log.debug('Fetch error<%s>: %d %s', resp.url, resp.status_code,
              resp.reason)
    raise exc(*exc_payload)


class GemLibHarvester(HarvesterBase):
    def info(self):
        return {
            'name': 'gem_lib',
            'title': 'GEM Digital Library',
            'description': 'Collect documents from GEM DL.'
        }

    def gather_stage(self, job):
        latest_url = _gl_url(job.source.url, 'latest')
        authors_url = _gl_url(job.source.url, 'authors')
        documents_url = _gl_url(job.source.url, 'document_author')
        latest_publication_date = model.Session.query(
            func.max(HarvestObject.metadata_modified_date)).filter(
                HarvestObject.source == job.source).scalar()

        if latest_publication_date:
            date_is_newer = F.partial(lt, latest_publication_date.isoformat())
            latest = must_be_ok(requests.get(latest_url),
                                self._save_gather_error,
                                'Cannot fetch latest list', job).json()

            fresh_publications = filter(
                F.compose(date_is_newer, itemgetter('created')), latest)
            if len(fresh_publications) < len(latest):
                return self._create_harvest_objects(
                    F.pluck('id', fresh_publications), job)
        authors = must_be_ok(requests.get(authors_url),
                             self._save_gather_error,
                             'Cannot fetch authors list', job).json()

        ids = set()
        log.debug("Collecting documents from %d authors", len(authors))
        for i, author in enumerate(authors, 1):
            log.debug('Fetching %d of %d record: %s', i, len(authors),
                      author['name'])
            documents = F.pluck(
                'id',
                must_be_ok(
                    requests.get(documents_url, params={'id': author['name']}),
                    self._save_gather_error,
                    'Cannot fetch documents for author <%s>' % author['name'],
                    job).json())

            for document in documents:
                ids.add(document)
        return self._create_harvest_objects(list(ids), job)

    def fetch_stage(self, obj):
        try:
            log.debug("Fetching document %s", obj.guid)
            obj.content = must_be_ok(
                requests.get(_gl_url(obj.source.url, 'document'),
                             params={'id': obj.guid}), self._save_object_error,
                'Cannot fetch document <%s>' % obj.guid, obj).content
        except HarvestObjectError as e:
            return False
        obj.save()
        return True

    def import_stage(self, obj):
        data_dict = json.loads(obj.content)
        package_dict = _map_gdl_to_publication(data_dict, obj)
        package_dict['owner_org'] = model.Package.get(obj.source.id).owner_org
        package_dict['tags'] = self._clean_tags({
            'name': tag,
            'display_name': tag
        } for tag in data_dict['keywords'].split(', '))

        result = self._create_or_update_package(package_dict, obj,
                                                'package_show')
        obj.metadata_modified_date = package_dict['metadata_modified']
        obj.save()
        return result
