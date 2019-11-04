# -*- coding: utf-8 -*-
import logging
import requests
import traceback
from bs4 import BeautifulSoup
from ckanext.ddi.harvesters.ddiharvester import NadaHarvester
from ckanext.ddi.importer.metadata import DdiCkanMetadata
from ckan.logic import get_action
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

'''
   Harvester uses NadaHarvester class from ckanext-ddi
   
   Note on metadata: ckanext.ddi.importer.metadata contains the mapping from
    ddi standard to ckan standard metadata.
'''
            

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
    
    '''
    Necessary changes made in import stage
    '''

    def import_stage(self, harvest_object):
        log.debug('In NadaHarvester import_stage')
        self._set_config(harvest_object.job.source.config)

        if not harvest_object:
            log.error('No harvest object received')
            self._save_object_error('No harvest object received',harvest_object)
            return False

        try:
            base_url = harvest_object.source.url.rstrip('/')
            # Mapping DDI metadata to CKAN equivalents
            ckan_metadata = DdiCkanMetadata()
            pkg_dict = ckan_metadata.load(harvest_object.content)
        
            # Alterations to pkg_dict
            # All NADA resources fal under Official Statistics theme

            pkg_dict['thematic_area_string'] = ["Statistics"]

            # Update URL with NADA catalog link
            catalog_path = self._get_catalog_path(harvest_object.guid)
            pkg_dict['url'] = base_url + catalog_path

            # Find country DDI abbreviation
            # Use the mapping of codes to return the right value
            if pkg_dict['member_countries'] not in list(country_mapping.values()):
                pkg_dict['member_countries'] = country_mapping[(pkg_dict['member_countries'])]   
            # Adjust title to include country
            pkg_dict['title'] = pkg_dict['country'] + ' ' + pkg_dict['title']
               
            # set license from harvester config or use CKAN instance default
            if 'license' in self.config:
                pkg_dict['license_id'] = self.config['license']
            else:
                pkg_dict['license_id'] = config.get('ckanext.ddi.default_license','')
          
            # Get owner_org from harvester
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
            # Here we find resources related to the study and scrape the relevant information
            if rsc_page:
                html_cont = BeautifulSoup(rsc_page.content, 'html5lib')
                for i, rsc in enumerate(html_cont.findAll('a', attrs={'class': 'download', 'target': '_blank'})):
                    resources.append({})
                    if rsc['href']:
                        resources[i]['url'] = rsc['href']
                    if rsc['data-extension']:
                        resources[i]['format'] = rsc['data-extension']
                    resources[i]['description'] = (rsc.find_previous('legend').text)[2:].strip()[:-1]
                    resources[i]['name'] = rsc.find_previous('span').contents[-1][2:].strip()
            
            # Put the list of dictionaries in 'resources' field
            pkg_dict['resources'] = resources

            log.debug('package dict: %s' % pkg_dict)

            # To avoid calling 'package_create_rest', we pass the parameter
            # package_dict_form='package_show'
            
            # If "M_DEVELOPMENT" is at end of id_number, the file is under
            #   development, and should not show up in front end
            # So we skip it
            # Otherwise we create/update as necessary
            if pkg_dict['id'][-13:] != "M_DEVELOPMENT":
                #p.toolkit.get_action('package_delete')(context, pkg_dict)
                return self._create_or_update_package(pkg_dict, harvest_object,
                package_dict_form='package_show')
            else:
                return False
        
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
