# -*- coding: utf-8 -*-
import requests
import traceback
from bs4 import BeautifulSoup
from zlib import adler32
import ckan.model as model
from ckan.lib.helpers import json
from ckan.lib.munge import munge_tag
from ckanext.harvest.model import HarvestObject, HarvestObjectExtra
from ckanext.harvest.harvesters import HarvesterBase
from ckan.logic import get_action
from ckantoolkit import config

import logging
log = logging.getLogger(__name__)


class SpcDotStatHarvester(HarvesterBase):
    HARVEST_USER = 'harvest'

    ACCESS_TYPES = {
        '': '',
        'direct_access': 1,
        'public_use': 2,
        'licensed': 3,
        'data_enclave': 4,
        'data_external': 5,
        'no_data_available': 6,
        'open_data': 7,
    }

    def info(self):
        return {
            'name': 'dotstat',
            'title': '.Stat harvester for SDMX',
            'description': ('Harvests SDMX data from a .Stat instance '),
            'form_config_interface': 'Text'
        }

    def _set_config(self, config_str):
        if config_str:
            self.config = json.loads(config_str)
        else:
            self.config = {}

        if 'user' not in self.config:
            self.config['user'] = self.HARVEST_USER
        if 'agencyId' not in self.config:
            self.config['agencyId'] = 'SPC'

        log.debug('Using config: %r' % self.config)

    def get_endpoints(self, base_url):
        '''
        Finds all Dataflows under SPC
        Goes to dataflow endpoint and parses SDMX, finding dataflow IDs
        Returns a list of strings
        '''
        endpoints = []
        # https://stats-nsi-stable.pacificdata.org/rest/dataflow/SPC/all
        resources_url = "{}dataflow/{}/all".format(
            base_url,
            self.config['agencyId']
        )
        resp = requests.get(resources_url)
        soup = BeautifulSoup(resp.text, 'xml')

        for name in soup.findAll('Dataflow'):
            endpoints.append((name['agencyID'], name['id'], name['version']))
        return endpoints

    def gather_stage(self, harvest_job):
        log.debug('In DotStatHarvester gather_stage')

        # For each row of data, use its ID as the GUID and save a harvest object
        # Return a list of all these new harvest jobs
        try:
            harvest_obj_ids = []
            self._set_config(harvest_job.source.config)
            base_url = harvest_job.source.url

            try:
                # Get list of endpoint ids
                endpoints = self.get_endpoints(base_url)

            except (AccessTypeNotAvailableError, KeyError):
                log.debug('Endpoint function failed')

            # Make a harvest object for each dataset
            # Set the GUID to the dataset's ID (DF_SDG etc.)

            for agency_id, _id, version in endpoints:
                harvest_obj = HarvestObject(
                    guid="{}-{}".format(agency_id, _id),
                    job=harvest_job
                )

                harvest_obj.extras = [
                    HarvestObjectExtra(key='stats_guid',
                                       value=_id),
                    HarvestObjectExtra(key='version',
                                       value=version)
                ]
                harvest_obj.save()

                harvest_obj_ids.append(harvest_obj.id)

            log.debug('IDs: {}'.format(harvest_obj_ids))

            return harvest_obj_ids

        except Exception as e:
            self._save_gather_error(
                'Unable to get content for URL: %s: %s / %s' %
                (base_url, str(e), traceback.format_exc()), harvest_job)


    def _get_object_extra(self, harvest_object, key):
        '''
        Helper function for retrieving the value from a harvest object extra,
        given the key
        '''
        if harvest_object:
            for extra in harvest_object.extras:
                if extra.key == key:
                    return extra.value
        return None

    def fetch_stage(self, harvest_object):
        '''
        Get the SDMX formatted resource for the GUID
        Put this in harvest_object's 'content' as text
        '''
        log.debug('In DotStatHarvester fetch_stage')
        self._set_config(harvest_object.job.source.config)

        if not harvest_object:
            log.error('No harvest object received')
            self._save_object_error('No harvest object received',
                                    harvest_object)
            return False

        base_url = harvest_object.source.url
        # Build the url where we'll fetch basic metadata

        agency_id = self.config['agencyId']
        obj_guid = self._get_object_extra(harvest_object, 'stats_guid')
        version = self._get_object_extra(harvest_object, 'version')
        meta_suffix = '{}/?references=all&detail=referencepartial'.format(
            version)

        metadata_url = '{}dataflow/{}/{}/{}'.format(base_url,
                                                    agency_id,
                                                    obj_guid,
                                                    meta_suffix)

        try:
            log.debug('Fetching content from %s' % metadata_url)
            meta = requests.get(metadata_url)
            meta.encoding = 'utf-8'
            # Dump page contents into harvest object content
            harvest_object.content = meta.text
            harvest_object.save()
            log.debug('Successfully processed: {}'.format(harvest_object.guid))
            return True

        except Exception as e:
            self._save_object_error(
                ('Unable to get content for package: %s: %r / %s' %
                 (metadata_url, e, traceback.format_exc())), harvest_object)
            return False

    # Parse the SDMX text and assign to correct fields of package dict
    def import_stage(self, harvest_object):
        log.debug('In DotStatHarvester import_stage')
        self._set_config(harvest_object.job.source.config)

        if not harvest_object:
            log.error('No harvest object received')
            self._save_object_error('No harvest object received',
                                    harvest_object)
            return False

        try:
            base_url = harvest_object.source.url
            # Parse the SDMX as XML with bs4
            soup = BeautifulSoup(harvest_object.content, 'xml')

            # Make a package dict
            pkg_dict = {}
            pkg_dict['id'] = harvest_object.guid

            # Added thematic string
            pkg_dict['thematic_area_string'] = ["Official Statistics"]

            # Get owner_org if there is one
            source_dataset = get_action('package_show')(
                {
                    'ignore_auth': True
                }, {
                    'id': harvest_object.source.id
                })
            owner_org = source_dataset.get('owner_org')
            pkg_dict['owner_org'] = owner_org

            # Match other fields with tags in XML structure
            agency_id = self.config['agencyId']
            stats_guid = self._get_object_extra(harvest_object, 'stats_guid')

            structure = soup.find('Dataflow', attrs={'id': stats_guid})
            pkg_dict['title'] = structure.find('Name', {"xml:lang" : "en"}).text
            pkg_dict['publisher_name'] = structure['agencyID']
            pkg_dict['version'] = structure['version']

            # Need to change url to point to Data Explorer
            de_url = 'https://stats.pacificdata.org/vis?locale=en&dataflow[datasourceId]=SPC2&dataflow[agencyId]={}&dataflow[dataflowId]={}&dataflow[version]={}'.format(
                agency_id,
                stats_guid,
                structure['version']
            )
            pkg_dict['source'] = de_url

            # Set a default resource
            pkg_dict['resources'] = [{
                'url':
                'https://stats-nsi-stable.pacificdata.org/rest/data/{},{},{}/all/?format=csv'.format(
                    agency_id,
                    stats_guid,
                    structure['version']
                ),
                'format': 'CSV',
                'mimetype': 'CSV',
                'description': 'All data for {}'.format(pkg_dict['title']),
                'name': '{} Data CSV'.format(pkg_dict['title'])
            }]

            # Get notes/description if it exists
            try:
                pkg_dict['notes'] = structure.find(
                    'Description', {"xml:lang": "en"}).text
            except Exception as e:
                log.error("An error occured: {}".format(e))
                pkg_dict['notes'] = ''
            '''
            May need modifying when DF_SDG is broken into several DFs
            This gets the list of indicators for SDG-related dataflows
            Stores the list of strings in 'alternate_identifier' field
            '''
            if soup.find('Codelist', attrs={'id': 'CL_SDG_SERIES'
                                            }) is not None:
                pkg_dict['alternate_identifier'] = []
                codelist = soup.find('Codelist', attrs={'id': 'CL_SDG_SERIES'})
                for indic in codelist.findAll('Name', {"xml:lang" : "en"}):
                    if not indic or indic.text == 'SDG Indicator or Series':
                        continue
                    pkg_dict['alternate_identifier'].append(indic.text)
            '''
            When support for metadata endpoints arrives in .Stat, here is how more metadata may be found:
            # Use the metadata/flow endpoint
            metadata = requests.get('{}metadata/data/{}/all?detail=full'.format(base_url, harvest_object.guid))

            # Parse with bs4
            parsed = BeautifulSoup(metadata.text, 'xml')

            # Now search for tags which may be useful as metadata
            # example: getting the name and definition of metadata set
            # (may need tweaking depending on SPC's metadata setup)

            # We can get name from the metadata structure
            set = parsed.find('MetadataSet')
            pkg_dict['name'] = set.find('Name').text

            # Then we can go to the reported attribute structure for more details
            detail = set.find('ReportedAttribute', attrs={'id': 'DEF'})
            pkg_dict['notes'] = detail.find('StructuredText', attrs={'lang': 'en'})
            source_details = set.find('ReportedAttribute', attrs={'id': 'SOURCE_DEF'})
            pkg_dict['source'] = source_details.find('StructuredText', attrs={'lang': 'en'})
            '''

            log.debug('package dict: %s' % pkg_dict)
            content_hash = str(_hashify(pkg_dict))
            harvest_object.extras = [
                HarvestObjectExtra(key='content_hash',
                                   value=content_hash)
            ]

            harvest_object.save()

            prev_object = model.Session.query(HarvestObject).filter(
                HarvestObject.source == harvest_object.source,
                HarvestObject.guid == harvest_object.guid,
                ~HarvestObject.import_finished.is_(None)).order_by(
                    HarvestObject.import_finished.desc()).first()

            obj_hash = self._get_object_extra(prev_object, 'content_hash')
            if obj_hash and obj_hash == content_hash:
                log.debug('Content is not changed. Skip..')
                return True

            # Create or update the package
            return self._create_or_update_package(
                pkg_dict, harvest_object, package_dict_form='package_show')
        except Exception as e:
            self._save_object_error(('Exception in import stage: %r / %s' %
                                     (e, traceback.format_exc())),
                                    harvest_object)
            return False


class AccessTypeNotAvailableError(Exception):
    pass


def _hashify(data):
    checksum = 0
    if isinstance(data, (list, tuple)):
        for item in data:
            checksum ^= _hashify(item)
    elif isinstance(data, dict):
        checksum ^= _hashify(tuple(sorted(data.items())))
    else:
        data = data.encode(errors='ignore') if isinstance(data, str) else str(data)
        checksum ^= adler32(data)
    return checksum
