# -*- coding: utf-8 -*-
import urllib
import urlparse
import logging
import json
import os
import requests
import traceback
from bs4 import BeautifulSoup

import ckan.model as model
import requests
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.model import HarvestObjectExtra as HOExtra
from ckanext.ddi.harvesters.ddiharvester import NadaHarvester
from ckanext.ddi.importer.metadata import ( 
    DdiCkanMetadata, XPathTextValue, XPathValue, ArrayTextValue, XPathMultiTextValue,
    FirstInOrderValue, DateCollectionValue, CombinedValue, ArrayDictNameValue
)
from ckan.logic import get_action
from ckanext.spatial.validation import Validators
from ckanext.scheming.helpers import (
    scheming_get_dataset_schema, scheming_field_by_name, scheming_field_choices
)

from pylons import config

log = logging.getLogger(__name__)

# Mapping DDI country abbreviations to CKAN equivalent
country_mapping = {
   "ASM": "AS",
   "MNP": "MP",
   "COK": "CK", 
   "FSM": "Micronesia",
   "FJI": "FJ",
   "PYF": "PF",
   "GUM": "GU",
   "KIR": "KI",
   "MHL": "MH",
   "NRU": "NR",
   "NCL": "NC",
   "NMI": "MP",
   "NIU": "NU",
   "PLW": "PW",
   "PNG": "PG",
   "PCN": "PN",
   "WSM": "WS",
   "SLB": "SB",
   "TKL": "TK",
   "TON": "TO",
   "TUV": "TV",
   "VAN": "VU",
   "VUT": "VU",
   "WLF": "WF",
   None: "Regional"
}

# Here we define an object to map ckan metadata to ddi metadata
# DdiCkanMetadata has some defaults, but we will add to them
#ckan_metadata = DdiCkanMetadata()
#print(ckan_metadata.get_mapping().keys())
# Try to get tags
#ckan_metadata.get_mapping()['tags'] = 
#ckan_metadata.get_mapping()['issued'] = XPathTextValue("//ddi:codeBook/ddi:docDscr//ddi:citation/ddi:prodStmt/ddi:prodDate/@date")
#ckan_metadata.get_mapping()['temporal_start'] = XPathTextValue("//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:SumDscr/ddi:collDate[@event='start']/@date")
#ckan_metadata.get_mapping()['temporal_end'] = XPathTextValue("//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:SumDscr/ddi:collDate[@event='end']/@date")

#print(ckan_metadata.get_mapping().keys())
            

class SpcNadaHarvester(NadaHarvester):
    '''
    Nada Harvester for PDH Microdata Library
    '''
    
    # Customize default attributes to use dataset.json
    #dataset_schema = scheming_get_dataset_schema("dataset")
    #print(dataset_schema)


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
            #print('HARVEST OBJECT:' + harvest_object.content + '\n')
            base_url = harvest_object.source.url.rstrip('/')
            ckan_metadata = DdiCkanMetadata()
            #maps = ckan_metadata.get_mapping()
            #print('Metadata keys! \n')
            #print(maps.keys())
            pkg_dict = ckan_metadata.load(harvest_object.content)
            #print(pkg_dict)
            # Alterations to pkg_dict
            # All NADA resources fal under Official Statistics
            pkg_dict['thematic_area_string'] = ["Official Statistics"]

            # update URL with NADA catalog link
            catalog_path = self._get_catalog_path(harvest_object.guid)
            pkg_dict['url'] = base_url + catalog_path

                      
            # Find country DDI abbreviation
            # Use the mapping of codes to return the right value
            if pkg_dict['member_countries'] not in list(country_mapping.values()):
                pkg_dict['member_countries'] = country_mapping[(pkg_dict['member_countries'])]   
            # Adjust title to include country
            pkg_dict['title'] = pkg_dict['title'] + ' ' + pkg_dict['country']
            # Here we make changes to get keys into right format
            
            # We won't use 'extras' field
            #pkg_dict = self._convert_to_extras(pkg_dict)

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
            
            # Get owner_org from harvester
            #pkg_dict['owner_org'] = self.content['owner_org']
            source_dataset = get_action('package_show')({
                'ignore_auth': True
            }, {
                'id': harvest_object.source.id
            })
            owner_org = source_dataset.get('owner_org')
            pkg_dict['owner_org'] = owner_org
                
            # Add url as source
            pkg_dict['source'] = pkg_dict['url']
        

            # Add resources
            # Gather the name and url of resources
            resources = []

            rsc_page = requests.get(pkg_dict['url'] + '/related_materials', verify=False)
            if rsc_page:
                html_cont = BeautifulSoup(rsc_page.content, 'html5lib')
                for i, rsc in enumerate(html_cont.findAll('a', attrs={'class': 'download', 'target': '_blank'})):
                    resources.append({})
                    resources[i]['url'] = rsc['href']
                    if rsc['title']:
                        resources[i]['name'] = rsc['title']
                    else:
                        resources[i]['name'] = 'Resource'
      
            pkg_dict['resources'] = resources

            log.debug('package dict: %s' % pkg_dict)
            # To avoid calling 'package_create_rest', we pass the parameter
            # package_dict_form='package_show'
            
            # If "M_DEVELOPMENT" is at end of id_number, the file is under
            #   development, and should not show up in front end
            # So we delete it
            # Otherwise we create/update as necessary
            if pkg_dict['id'][-13:] != "M_DEVELOPMENT":
                #p.toolkit.get_action('package_delete')(context, pkg_dict)
                return self._create_or_update_package(pkg_dict, harvest_object,
                package_dict_form='package_show')
            else:
                return "Skipped package 'under development'"
        
        except Exception, e:
            location = harvest_object.source.url.rstrip('/') + self._get_catalog_path(harvest_object.guid)
            self._save_object_error(
                (
                    'Exception in import stage for package at %s : %r / %s'
                    % (location, e, traceback.format_exc())
                ),
                harvest_object
            )
            return False
