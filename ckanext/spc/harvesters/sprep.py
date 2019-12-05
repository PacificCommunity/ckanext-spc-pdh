import uuid
import json
import logging
import re
import urllib2
import shapely

import urlparse
from bs4 import BeautifulSoup
import requests
from ckan.lib.helpers import markdown_extract
from ckan.lib.munge import munge_title_to_name, munge_tag
import ckan.plugins.toolkit as tk
from ckan.logic import get_action
from ckan.model import Session
from ckanext.harvest.harvesters.base import HarvesterBase
from ckanext.harvest.model import HarvestObject
from dateutil.parser import parse
import ckan.model as model
from ckan.lib.munge import munge_title_to_name

logger = logging.getLogger(__name__)
RE_SWITCH_CASE = re.compile('_(?P<letter>\\w)')
RE_SPATIAL = re.compile(r'POLYGON \(\((.*)\)\)')

country_mapping = {
    "palau": "PW",
    "fsm": "FM",
    "png": "PG",
    "vanuatu": "VU",
    "solomonislands": "SB",
    "nauru": "NR",
    "rmi": "MH",
    "tuvalu": "TV",
    "fiji": "FJ",
    "tonga": "TO",
    "samoa": "WS",
    "niue": "NU",
    "cookislands": "CK",
    "kiribati": "KI",
    None: "Regional",
}


class SpcSprepHarvester(HarvesterBase):
    '''
    SPREP Harvester
    '''

    def info(self):
        '''
        Return information about this harvester.
        '''
        return {
            'name': 'SPREP',
            'title': 'SPREP',
            'description': 'Harvester for SPREP ODP'
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

            skip_licenses = {
                'c12c3333-1ad7-4a3a-a629-ed51fcb636ac',
                'a270745d-07d5-4e93-94fc-ba6e0afc97fb',
            }

            # TODO: switch
            # with open('/tmp/data.json', 'wb') as file:
                # file.write(requests.get(
                    # urlparse.urljoin(harvest_job.source.url, 'data.json')
                # ).content)
            # for record in json.loads(open('/tmp/data.json').read())['dataset']:

            for record in requests.get(
                urlparse.urljoin(harvest_job.source.url, 'data.json')
            ).json()['dataset']:
                license_id = record.get('license',
                                        'cc-by').strip('/').split('/')[-1]
                if license_id in skip_licenses:
                    continue
                if 'hub.pacificdata' == record.get('isPartOf'):
                    continue
                if 'Info' in record.get('theme', []):
                    continue
                harvest_obj = HarvestObject(
                    guid=record['identifier'],
                    content=json.dumps(record),
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
        except Exception as e:
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

    def _set_config(self, source_config):
        try:
            config_json = json.loads(source_config)
            # logger.debug('config_json: %s' % config_json)
            self.config = config_json
            self.user = 'harvest'
            self._mapping = config_json.get('topic_mapping', False)

        except ValueError:
            pass

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
            content_dict = json.loads(harvest_object.content)
            content_dict['id'] = content_dict['identifier']

            content_dict['name'] = (
                munge_title_to_name(content_dict['title']) + content_dict['id']
            )[:99]
            try:
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

            package_dict = json.loads(harvest_object.content)
            data_dict = {}
            data_dict['id'] = package_dict['id']
            data_dict['title'] = package_dict['title']
            data_dict['name'] = munge_title_to_name(package_dict['name'])

            data_dict['notes'] = markdown_extract(
                package_dict.get('description')
            )

            tags = package_dict.get('keyword', [])
            data_dict['tag_string'] = ', '.join([
                munge_tag(tag) for tag in tags
            ])

            data_dict['private'] = False

            license_id = package_dict.get('license',
                                          'cc-by').strip('/').split('/')[-1]

            if license_id == 'de2a56f5-a565-481a-8589-406dc40b5588':
                license_id = 'sprep-public-license'
            data_dict['license_id'] = license_id or 'notspecified'

            data_dict['created'] = _parse_drupal_date(package_dict['issued'])
            data_dict['modified'] = _parse_drupal_date(
                package_dict['modified']
            )

            c_point, c_email = package_dict['contactPoint']['fn'], package_dict['contactPoint'][
                'hasEmail'].split(':')[-1]
            if c_email != 'noemailprovided@usa.gov':
                data_dict['contact_uri'] = c_point
                data_dict['contact_email'] = c_email
            data_dict['resources'] = []
            for res in package_dict.get('distribution', []):

                # res['issued'] = _parse_drupal_date(res.pop('created'))
                # res['modified'] = _parse_drupal_date(
                #     res.pop('last_modified').replace('Date changed ', '')
                # )
                res['url'] = res.get('downloadURL') or res.get('accessURL')
                res['name'] = res['title']
                res['description'] = markdown_extract(res.get('description'))
                data_dict['resources'].append(res)
            if 'spatial' in package_dict:
                data_dict['spatial'] = package_dict.pop('spatial')

                try:
                    geometry = {
                        "type": "Polygon",
                        "coordinates": [[[
                            float(c) for c in pair.split()
                        ] for pair in RE_SPATIAL.match(data_dict['spatial']).
                                         group(1).split(', ')]]
                    }
                    shape = shapely.geometry.asShape(geometry)
                    if shape.is_valid and shape.is_closed:
                        data_dict['spatial'] = json.dumps(geometry)
                    else:
                        del data_dict['spatial']

                except KeyError:
                    pass
                except (AttributeError, ValueError):
                    del data_dict['spatial']
                    # logger.warn('-' * 80)
                    #
                    # logger.warn('Failed parsing of spatial field: %s', data_dict['spatial'])

                # package_dict.pop('type')
            # add owner_org
            source_dataset = get_action('package_show')({
                'ignore_auth': True
            }, {
                'id': harvest_object.source.id
            })

            owner_org = source_dataset.get('owner_org')
            data_dict['owner_org'] = owner_org
            data_dict['member_countries'] = country_mapping[None]
            if 'isPartOf' in package_dict:
                country = package_dict['isPartOf'].split('.')[0]
                data_dict['member_countries'] = country_mapping.get(
                    country, country_mapping[None]
                )
                org = model.Session.query(
                    model.Group
                ).filter_by(name=country + '-data').first()
                if org:
                    data_dict['owner_org'] = org.id

            data_dict['source'] = package_dict.get('landingPage')

            data_dict['theme'] = package_dict.get('theme', [])
            data_dict['theme'] = package_dict.get('theme', [])

            data_dict['thematic_area_string'] = _map_theme_to_topic(data_dict['theme'])

            data_dict['harvest_source'] = 'SPREP'

            self._create_or_update_package(
                data_dict, harvest_object, 'package_show'
            )

            # import ipdb; ipdb.set_trace()
            Session.commit()
            stored_package = get_action('package_show')({
                'ignore_auth': True
            }, {
                'id': data_dict['id']
            })
            for res in stored_package.get('resources', []):
                get_action('resource_create_default_resource_views')(
                    {'ignore_auth': True},
                    {'package': stored_package, 'resource': res}
                )

            logger.debug("Finished record")
        except:
            logger.exception('Something went wrong!')
            self._save_object_error(
                'Exception in import stage', harvest_object
            )
            return False
        return True


def _parse_drupal_date(date_str):

    return parse(date_str, dayfirst=True)

def _map_theme_to_topic(themes):
    topics = set()
    if len(themes) >= 3:
        topics.add('Environment')
    if 'Atmosphere and Climate' in themes:
        topics.add('Climate Change')
    if 'Biodiversity' in themes:
        topics.add('Land Resources')
        if any(t in themes for t in ('Atmosphere and Climate', 'Inland Waters')):
            topics.add('Fisheries')
    if 'Land' in themes:
        topics.add('Land Resources')
    if 'Built Environment' in themes:
        topics.add('Environment')
        topics.add('Economic Development')
    if 'Coastal and Marine' in themes:
        topics.add('Fisheries')
    if 'Culture and Heritage' in themes:
        topics.add('Gender and Youth')
    if 'Inland Waters' in themes:
        topics.add('Geoscience')
    return list(topics)
