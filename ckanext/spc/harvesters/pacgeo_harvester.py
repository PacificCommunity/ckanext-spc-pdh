# -*- coding: utf-8 -*-
import urllib
import urlparse
import logging
import json

import ckan.model as model
import requests
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.model import HarvestObjectExtra as HOExtra
from ckanext.spatial.harvesters.csw import CSWHarvester
from ckanext.spatial.validation import Validators
logger = logging.getLogger(__name__)


class PacGeoHarvester(CSWHarvester):
    _validator = Validators(profiles=[])

    def info(self):
        '''
        Return information about this harvester.
        '''
        return {
            'name': 'pacgeo',
            'title': 'PacGeo',
            'description': 'Harvester for PacGeo'
        }

    def _set_source_config(self, source_config):
        super(CSWHarvester, self)._set_source_config(source_config)
        try:
            config_json = json.loads(source_config)
            self.keywords = config_json['keywords']
        except (KeyError, ValueError):
            self.keywords = []

    def gather_stage(self, harvest_job):
        logger.debug('CswHarvester gather_stage for job: %r', harvest_job)
        # Get source URL
        url = harvest_job.source.url
        self._set_source_config(harvest_job.source.config)

        parts = urlparse.urlparse(url)

        params = {'keywords__slug__in': self.keywords, 'limit': 10000}

        url = urlparse.urlunparse((
            parts.scheme, parts.netloc, '/api/layers', None,
            urllib.urlencode(params, True), None
        ))

        query = model.Session.query(
            HarvestObject.guid, HarvestObject.package_id
        ).filter(HarvestObject.current == True).filter(
            HarvestObject.harvest_source_id == harvest_job.source.id
        )
        guid_to_package_id = {}

        for guid, package_id in query:
            guid_to_package_id[guid] = package_id

        guids_in_db = set(guid_to_package_id.keys())

        logger.debug('Starting gathering for %s' % url)
        guids_in_harvest = set()
        try:
            for obj in requests.get(url).json()['objects']:
                try:
                    uuid = obj['uuid']
                    logger.info('Got identifier %s from the PacGeo', uuid)
                    guids_in_harvest.add(uuid)
                except Exception, e:
                    self._save_gather_error(
                        'Error for the identifier from <%r>: %s' % (obj, e),
                        harvest_job
                    )
                    continue

        except Exception as e:
            logger.error('Exception: %s', e)
            self._save_gather_error(
                'Error gathering the identifiers from the PacGeo server [%s]' %
                str(e), harvest_job
            )
            return None

        new = guids_in_harvest - guids_in_db
        delete = guids_in_db - guids_in_harvest
        change = guids_in_db & guids_in_harvest

        ids = []
        for guid in new:
            obj = HarvestObject(
                guid=guid,
                job=harvest_job,
                extras=[HOExtra(key='status', value='new')]
            )
            obj.save()
            ids.append(obj.id)
        for guid in change:
            obj = HarvestObject(
                guid=guid,
                job=harvest_job,
                package_id=guid_to_package_id[guid],
                extras=[HOExtra(key='status', value='change')]
            )
            obj.save()
            ids.append(obj.id)
        for guid in delete:
            obj = HarvestObject(
                guid=guid,
                job=harvest_job,
                package_id=guid_to_package_id[guid],
                extras=[HOExtra(key='status', value='delete')]
            )
            model.Session.query(HarvestObject).filter_by(guid=guid).update({
                'current': False
            }, False)
            obj.save()
            ids.append(obj.id)

        if len(ids) == 0:
            self._save_gather_error(
                'No records received from the CSW server', harvest_job
            )
            return None

        return ids

    def get_package_dict(self, iso_values, harvest_object):
        data = super(PacGeoHarvester,
                     self).get_package_dict(iso_values, harvest_object)

        data['type'] = 'geographic_data'
        extras = data.pop('extras', [])
        for extra in extras:
            key, value = extra['key'], extra['value']
            if key == 'metadata-date':
                data['date_stamp'] = value.split('T')[0]
            elif key == 'spatial':
                data[key] = value
            elif key == 'responsible-party':
                for party in json.loads(value):
                    contact = {
                        'individual_name': party['name'] or 'Undefined',
                        'role': [
                            {'code_list_value': role, 'code_list': 'default'}
                            for role in party['roles']
                        ]
                    }
                    data.setdefault('contact', []).append(contact)

        harvest_source = model.Package.get(harvest_object.source.id)
        if harvest_source:
            data['owner_org'] = harvest_source.owner_org
        data['thematic_area_string'] = 'Geoscience'
        return data
