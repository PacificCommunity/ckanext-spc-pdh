import re
import logging
import json
from urlparse import urljoin
import requests
import lxml.etree as et
from ckan.logic import check_access, get_action
from ckan.lib.munge import munge_title_to_name

from ckanext.oaipmh.harvester import OaipmhHarvester
from ckanext.scheming.helpers import (
    scheming_get_dataset_schema, scheming_field_by_name, scheming_field_choices
)
from ckanext.spc.utils import eez

import urllib2

from ckan.model import Session
from ckan import model

from ckanext.harvest.harvesters.base import HarvesterBase
from ckan.lib.munge import munge_tag
from ckanext.harvest.model import HarvestObject

import oaipmh.client
from oaipmh.metadata import MetadataRegistry

logger = logging.getLogger(__name__)
RE_SWITCH_CASE = re.compile('_(?P<letter>\w)')


class SpcGbifHarvester(HarvesterBase):
    '''
    GBIF Harvester
    '''

    def info(self):
        '''
        Return information about this harvester.
        '''
        return {
            'name': 'GBIF',
            'title': 'GBIF',
            'description': 'Harvester for GBIF data sources'
        }

    def gather_stage(self, harvest_job):
        '''
        The gather stage will recieve a HarvestJob object and will be
        responsible for:
            - gathering all the necessary objects to fetch on a later.
              stage (e.g. for a CSW server, perform a GetRecords request)
            - creating the necessary HarvestObjects in the database, specifying
              the guid and a reference to its source and job.
            - creating and storing any suitable HarvestGatherErrors that may
              occur.
            - returning a list with all the ids of the created HarvestObjects.

        :param harvest_job: HarvestJob object
        :returns: A list of HarvestObject ids
        '''
        logger.debug("in gather stage: %s" % harvest_job.source.url)
        try:
            harvest_obj_ids = []
            self._set_config(harvest_job.source.config)
            url = urljoin(harvest_job.source.url, '/v1/dataset/search')

            for record in self._fetch_record_outline(url):
                harvest_obj = HarvestObject(
                    guid=record['key'],
                    content=record['country'],
                    job=harvest_job
                )
                harvest_obj.save()
                harvest_obj_ids.append(harvest_obj.id)
        except urllib2.HTTPError, e:
            logger.exception(
                'Gather stage failed on %s (%s): %s, %s' %
                (harvest_job.source.url, e.fp.read(), e.reason, e.hdrs)
            )
            self._save_gather_error(
                'Could not gather anything from %s' % harvest_job.source.url,
                harvest_job
            )
            return None
        except Exception, e:
            logger.exception(
                'Gather stage failed on %s: %s' % (
                    harvest_job.source.url,
                    str(e),
                )
            )
            self._save_gather_error(
                'Could not gather anything from %s' % harvest_job.source.url,
                harvest_job
            )
            return None
        return harvest_obj_ids

    def _fetch_record_outline(self, url):
        params = {'offset': 0, 'hosting_org': self._hosting_org, 'q': self._q}
        while True:
            resp = requests.get(url, params)
            resp.raise_for_status()
            data = resp.json()
            for record in data['results']:

                yield {
                    'key': record['key'],
                    'country': record['publishingCountry']
                }
            logger.debug(
                'Fetched {:d} of {:d} records'.format(
                    params['offset'] + data['limit'], data['count']
                )
            )
            if data['endOfRecords']:
                break
            params['offset'] += data['limit']

    def _set_config(self, source_config):
        try:
            config_json = json.loads(source_config)
            logger.debug('config_json: %s' % config_json)
            try:
                username = config_json['username']
                password = config_json['password']
                self.credentials = (username, password)
            except (IndexError, KeyError):
                self.credentials = None

            self.user = 'harvest'
            self._hosting_org = config_json.get('hosting_org', None)
            self._q = config_json.get('q', 'oai_dc')
            self._topic = config_json.get('topic', False)

        except ValueError:
            pass

    def _fetch_record(self, url, key):

        root = et.parse(
            url + '?verb=GetRecord&metadataPrefix=eml&identifier=' + key
        ).getroot()
        nsmap = root.nsmap
        nsmap['oai'] = nsmap.pop(None)
        id = root.find('*//oai:identifier', namespaces=nsmap).text
        dataset = root.find('*//dataset')
        return id, dataset

    def _eml_to_dict(self, record):
        data = {}
        data['type'] = 'biodiversity_data'
        data['license_id'] = 'cc-nc'
        data['thematic_area_string'] = self._topic

        data['title'] = record.find('title').text.strip()
        data['name'] = munge_title_to_name(data['title'])
        data['pub_date'] = record.find('pubDate').text.strip()

        data['alternate_identifier'] = [
            e.text.strip() for e in record.findall('alternateIdentifier')
        ]
        data['language'] = [e.text.strip() for e in record.findall('language')]

        data['creator'] = [_parse_agent(e) for e in record.findall('creator')]
        data['metadata_provider'] = [
            _parse_agent(e) for e in record.findall('metadataProvider')
        ]
        data['associated_party'] = [
            _parse_agent(e) for e in record.findall('associatedParty')
        ]
        data['contact'] = [_parse_agent(e) for e in record.findall('contact')]

        data['notes'] = '\n\n'.join(record.xpath('abstract/para/text()'))
        data['additional_info'] = '\n\n'.join(
            record.xpath('additionalInfo/para/text()')
        )
        data['intellectual_rights'] = '\n\n'.join(
            record.xpath('intellectualRights/para/text()')
        )
        data['purpose'] = '\n\n'.join(record.xpath('purpose/para/text()'))

        data['keyword_set'] = [
            _parse_keyword_set(e) for e in record.findall('keywordSet')
        ]
        data['coverage'] = [
            _parse_coverage(e) for e in record.findall('coverage')
        ]
        data['maintenance'] = [
            _parse_maintenance(e) for e in record.findall('maintenance')
        ]
        data['methods'] = [
            _parse_methods(e) for e in record.findall('methods')
        ]
        data['project'] = [
            _parse_project(e) for e in record.findall('project')
        ]
        data['resources'] = [
            _parse_distribution(e) for e in record.findall('distribution')
        ]

        return data

    def fetch_stage(self, harvest_object):
        '''
        The fetch stage will receive a HarvestObject object and will be
        responsible for:
            - getting the contents of the remote object (e.g. for a CSW server,
              perform a GetRecordById request).
            - saving the content in the provided HarvestObject.
            - creating and storing any suitable HarvestObjectErrors that may
              occur.
            - returning True if everything went as expected, False otherwise.

        :param harvest_object: HarvestObject object
        :returns: True if everything went right, False if errors were found
        '''
        logger.debug("in fetch stage: %s" % harvest_object.guid)
        try:
            self._set_config(harvest_object.job.source.config)

            record = None
            try:
                logger.debug(
                    "Load %s with metadata prefix '%s'" %
                    (harvest_object.guid, 'eml')
                )

                id, record = self._fetch_record(
                    urljoin(
                        harvest_object.job.source.url, '/v1/oai-pmh/registry'
                    ), harvest_object.guid
                )

                logger.debug('record found!')
            except Exception:
                logger.exception('fetch_record failed')
                self._save_object_error('Fetch record failed!', harvest_object)
                return False

            try:

                content_dict = self._eml_to_dict(record)
                content_dict['id'] = id
                content = json.dumps(content_dict)
            except Exception:
                logger.exception('Dumping the metadata failed!')
                self._save_object_error(
                    'Dumping the metadata failed!', harvest_object
                )
                return False

            harvest_object.content = content
            harvest_object.save()
        except Exception:
            logger.exception('Something went wrong!')
            self._save_object_error('Exception in fetch stage', harvest_object)
            return False

        return True

    def import_stage(self, harvest_object):
        '''
        The import stage will receive a HarvestObject object and will be
        responsible for:
            - performing any necessary action with the fetched object (e.g
              create a CKAN package).
              Note: if this stage creates or updates a package, a reference
              to the package must be added to the HarvestObject.
              Additionally, the HarvestObject must be flagged as current.
            - creating the HarvestObject - Package relation (if necessary)
            - creating and storing any suitable HarvestObjectErrors that may
              occur.
            - returning True if everything went as expected, False otherwise.

        :param harvest_object: HarvestObject object
        :returns: True if everything went right, False if errors were found
        '''
        logger.debug("in import stage: %s" % harvest_object.guid)
        if not harvest_object:
            logger.error('No harvest object received')
            self._save_object_error('No harvest object received')
            return False

        try:
            self._set_config(harvest_object.job.source.config)
            context = {'model': model, 'session': Session, 'user': self.user}

            package_dict = json.loads(harvest_object.content)

            package_dict['id'] = munge_title_to_name(harvest_object.guid)
            package_dict['name'] = package_dict['id']

            # add owner_org
            source_dataset = get_action('package_show')({
                'ignore_auth': True
            }, {
                'id': harvest_object.source.id
            })
            owner_org = source_dataset.get('owner_org')
            package_dict['owner_org'] = owner_org

            # logger.debug('Create/update package using dict: %s' % package_dict)
            self._create_or_update_package(package_dict, harvest_object)

            Session.commit()

            logger.debug("Finished record")
        except:
            logger.exception('Something went wrong!')
            self._save_object_error(
                'Exception in import stage', harvest_object
            )
            return False
        return True


def _text(e):
    if e is not None:
        return e.text.strip()


def _dumb_parse(e, keys, with_empty=False):
    data = {}
    for key in keys:
        fetch_text = False
        if key.startswith('@'):
            key = key[1:]
            fetch_text = True
        selector = RE_SWITCH_CASE.sub(
            lambda match: match.group(1).upper(), key
        )
        if fetch_text:
            value = [
                t.strip() for t in e.xpath(selector + '/text()') +
                e.xpath(selector + '/para/text()')
            ]
            value = filter(None, value)
        else:
            value = _text(e.find(selector)) or '\n\n'.join(
                e.xpath(selector + '//para/text()') or []
            ).strip()
            if not value and selector.endswith(('Date', 'Time')):
                value = _text(e.find(selector + '/calendarDate'))
        if not with_empty and not value:
            continue
        position = data
        steps = key.split('/')
        for step in steps[:-1]:
            position = position.setdefault(step, {})
        position[steps[-1]] = value
    return data


def _parse_agent(e):
    keys = (
        'organization_name', 'individual_name/given_name',
        'individual_name/sur_name', 'position_name', 'address/delivery_point',
        'address/city', 'address/administrative_area', 'address/postal_code',
        'address/country', 'phone', 'electronic_mail_address', 'online_url',
        'role', '@user_id'
    )
    return _dumb_parse(e, keys)


def _parse_keyword_set(e):
    keys = ('keyword_thesaurus', '@keyword')
    return _dumb_parse(e, keys)


def _parse_coverage(e):
    keys = (
        'geographic_coverage/geographic_description',
        'geographic_coverage/bounding_coordinates/west_bounding_coordinate',
        'geographic_coverage/bounding_coordinates/east_bounding_coordinate',
        'geographic_coverage/bounding_coordinates/north_bounding_coordinate',
        'geographic_coverage/bounding_coordinates/south_bounding_coordinate',
        'temporal_coverage/range_of_dates/begin_date',
        'temporal_coverage/range_of_dates/end_date',
        'temporal_coverage/single_date_time',
        'taxonomic_coverage/general_taxonomic_coverage',
    )
    data = _dumb_parse(e, keys)
    data.setdefault('taxonomic_coverage', {})['taxonomic_classification'] = [
        _parse_taxon_class(el)
        for el in e.findall('taxonomic_coverage/taxonomic_classification')
    ]

    return data


def _parse_taxon_class(e):
    keys = (
        'taxon_rank_name',
        'taxon_rank_value',
        'common_name',
    )
    return _dumb_parse(e, keys)


def _parse_maintenance(e):
    keys = (
        'description',
        'maintenance_update_frequency',
    )
    return _dumb_parse(e, keys)


def _parse_methods(e):
    keys = (
        'method_step',
        'sampling/study_extent',
        'sampling/sampling_description',
        'quality_control',
    )
    return _dumb_parse(e, keys)


def _parse_project(e):
    keys = (
        'title', 'abstract', 'funding',
        'study_area_description/descriptor_value',
        'study_area_description/citable_classification_system',
        'study_area_description/name', 'design_description', 'id'
    )
    data = _dumb_parse(e, keys)
    data['personnel'] = [_parse_agent(el) for el in e.findall('personnel')]

    return data


def _parse_distribution(e):
    url = _text(e.find('online/url'))
    return {'url': url}
