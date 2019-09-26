# -*- coding: utf-8 -*-
import urllib
import urlparse
import logging
import json
import os
import requests
import traceback

import ckan.model as model
import requests
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.model import HarvestObjectExtra as HOExtra
from ckanext.ddi.harvesters.ddiharvester import NadaHarvester
from ckanext.ddi.importer.metadata import DdiCkanMetadata
from ckanext.spatial.validation import Validators

from pylons import config

log = logging.getLogger(__name__)

class SpcNadaHarvester(NadaHarvester):
    '''
    Nada Harvester for PDH Microdata Library
    '''
    def info(self):
        return {
            'name': 'nada',
            'title': 'Nada',
            'description': 'Harvester for Nada Microdata Library'
        }
    def import_stage(self, harvest_object):
        log.debug('In NadaHarvester import_stage')
        self._set_config(harvest_object.job.source.config)

        if not harvest_object:
            log.error('No harvest object received')
            self._save_object_error('No harvest object received',harvest_object)
            return False

        try:
            base_url = harvest_object.source.url.rstrip('/')
            ckan_metadata = DdiCkanMetadata()
            pkg_dict = ckan_metadata.load(harvest_object.content)
            pkg_dict = self._convert_to_extras(pkg_dict)

            # update URL with NADA catalog link
            catalog_path = self._get_catalog_path(harvest_object.guid)
            pkg_dict['url'] = base_url + catalog_path

            # set license from harvester config or use CKAN instance default
            if 'license' in self.config:
                pkg_dict['license_id'] = self.config['license']
            else:
                pkg_dict['license_id'] = config.get('ckanext.ddi.default_license','')
            tags = []
            for tag in pkg_dict['tags']:
                if isinstance(tag, basestring):
                    tags.append(munge_tag(tag[:100]))
            pkg_dict['tags'] = tags
            pkg_dict['version'] = pkg_dict['version'][:100]
            
            # Adding a default owner_org
            pkg_dict['owner_org'] = 'my_org'

            # add resources
            resources = [
                {
                    'url': base_url + self._get_ddi_api(harvest_object.guid),
                    'name': 'DDI XML of %s' % pkg_dict['title'],
                    'format': 'xml'
                },
                {
                    'url': pkg_dict['url'],
                    'name': 'NADA catalog entry',
                    'format': 'html'
                },
            ]
            pkg_dict['resources'] = resources

            log.debug('package dict: %s' % pkg_dict)
            # To avoid calling 'package_create_rest', we pass the parameter
            # package_dict_form='package_show'
            return self._create_or_update_package(pkg_dict, harvest_object,
                package_dict_form='package_show')
        
        except Exception, e:
            self._save_object_error(
                (
                    'Exception in import stage: %r / %s'
                    % (e, traceback.format_exc())
                ),
                harvest_object
            )
            return False
