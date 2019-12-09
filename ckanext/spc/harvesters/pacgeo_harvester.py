# -*- coding: utf-8 -*-
import urllib
import urlparse
import logging
import json
import StringIO
import requests

import ckan.model as model

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.model import HarvestObjectExtra as HOExtra
from ckanext.spatial.harvesters.csw import CSWHarvester
from ckanext.spatial.validation import Validators
from ckanext.spatial.lib.csw_client import CswService

from owslib.csw import CatalogueServiceWeb
from owslib.etree import etree
from owslib import util
from owslib.namespaces import Namespaces
from urllib2 import Request, urlopen

logger = logging.getLogger(__name__)


def get_namespaces():
    n = Namespaces()
    return n.get_namespaces()
namespaces = get_namespaces()


class _Implementation(CatalogueServiceWeb, object):
    __metaclass__ = type
    def __init__(self, url, headers, lang='en-US', version='2.0.2', timeout=10, skip_caps=False):
        self.headers = headers
        super(_Implementation, self).__init__(url,
                                              lang='en-US',
                                              version='2.0.2',
                                              timeout=10,
                                              skip_caps=False)

    def _invoke(self):
        self.request = Request(self.request,
                               headers={'User-Agent': self.headers})

        # do HTTP request
        self.response = urlopen(self.request, timeout=self.timeout).read()

        # parse result see if it's XML
        self._exml = etree.parse(StringIO.StringIO(self.response))

        # it's XML.  Attempt to decipher whether the XML response is CSW-ish """
        valid_xpaths = [
            util.nspath_eval('ows:ExceptionReport', namespaces),
            util.nspath_eval('csw:Capabilities', namespaces),
            util.nspath_eval('csw:DescribeRecordResponse', namespaces),
            util.nspath_eval('csw:GetDomainResponse', namespaces),
            util.nspath_eval('csw:GetRecordsResponse', namespaces),
            util.nspath_eval('csw:GetRecordByIdResponse', namespaces),
            util.nspath_eval('csw:HarvestResponse', namespaces),
            util.nspath_eval('csw:TransactionResponse', namespaces)
        ]

        if self._exml.getroot().tag not in valid_xpaths:
            raise RuntimeError, 'Document is XML, but not CSW-ish'

        # check if it's an OGC Exception
        val = self._exml.find(util.nspath_eval('ows:Exception', namespaces))
        if val is not None:
            raise ows.ExceptionReport(self._exml, self.owscommon.namespace)
        else:
            self.exceptionreport = None


class CustomCswService(CswService):
    _Implementation = _Implementation

    def __init__(self, url, headers):
        self.headers = headers
        super(CustomCswService, self).__init__(url)

    def _ows(self, endpoint=None, **kw):
        if not hasattr(self, "_Implementation"):
            raise NotImplementedError("Needs an Implementation")
        if not hasattr(self, "__ows_obj__"):
            if endpoint is None:
                raise ValueError("Must specify a service endpoint")
            self.__ows_obj__ = self._Implementation(endpoint, self.headers)

        return self.__ows_obj__


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
    
    def _setup_csw_client(self, url):
        headers = self.config_json['user_agent']
        self.csw = CustomCswService(url, headers)

    def _set_source_config(self, source_config):
        super(CSWHarvester, self)._set_source_config(source_config)
        try:
            self.config_json = json.loads(source_config)
        except ValueError:
            self.config_json = {}

        self.keywords = self.config_json.get('keywords', [])
        self.user_agent = self.config_json.get('user_agent', '')

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

    def fetch_stage(self, harvest_object):
        self._set_source_config(harvest_object.source.config)
        super(PacGeoHarvester, self).fetch_stage(harvest_object)
        return True

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
