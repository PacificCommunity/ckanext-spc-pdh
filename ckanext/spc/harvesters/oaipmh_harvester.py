import logging
import json
import datetime
from uuid import uuid3, NAMESPACE_DNS

import ckan.model as model
from ckanext.harvest.model import HarvestObject
from ckan.logic import check_access, get_action
from ckan.lib.munge import munge_title_to_name, munge_tag
import ckan.plugins.toolkit as tk

from ckanext.oaipmh.harvester import OaipmhHarvester
from ckanext.scheming.helpers import (
    scheming_get_dataset_schema, scheming_field_by_name, scheming_field_choices
)
from ckanext.spc.utils import eez

logger = logging.getLogger(__name__)


class SpcOaipmhHarvester(OaipmhHarvester):
    def _set_config(self, source_config):
        super(SpcOaipmhHarvester, self)._set_config(source_config)
        try:
            config_json = json.loads(source_config)
            self.topic = config_json['topic']
        except KeyError:
            self.topic = None
        except ValueError:
            pass
        self.force_all = config_json.get('force_all', False)
        self.userobj = model.User.get(self.user)


    def _extract_additional_fields(self, content, package_dict):
        package_dict['thematic_area_string'] = self.topic

        if not package_dict.get('license_id'):
            package_dict['license_id'] = 'notspecified'

        skip_keys = {'set_spec', 'description'}

        for key, value in content.items():
            if key in package_dict or key in skip_keys:
                continue
            if key == 'type':
                key = 'publication_type'
            package_dict[key] = value

        package_dict.pop('extras', None)
        package_dict['type'] = 'publications'
        package_dict.pop('maintainer_email', None)

        coverage = package_dict.pop('coverage', None)
        if coverage:
            schema = scheming_get_dataset_schema('publications')
            field = scheming_field_by_name(
                schema['dataset_fields'], 'member_countries'
            )
            choices = scheming_field_choices(field)
            package_dict['member_countries'] = [
                choice['value'] for choice in choices
                if choice['label'] in coverage
            ] or ['other']
            polygons = [
                t['geometry'] for t in eez.collection if any(
                    country in t['properties']['GeoName']
                    for country in coverage
                )
            ]
            # TODO: for now we are taking first polygon from possible
            # list because of SOLR restriction of spatial field
            # size. In future we may add additional logic here
            if polygons:
                package_dict['coverage'] = json.dumps(polygons[0])

        return package_dict

    def _find_or_create_groups(self, groups, context):
        logger.debug('Group names: %s' % groups)
        group_ids = []
        for group_name in groups:
            munged_name = munge_title_to_name(group_name)
            existing = model.Group.get(munged_name)
            if existing:
                if 'organization' == existing.type:
                    munged_name += '_group'
                    existing = model.Group.get(munged_name)
            if existing:
                if existing.state != 'active':
                    existing.state = 'active'
                    model.Session.commit()
                group_ids.append({'id': existing.id})
            # else:
            #     data_dict = {
            #         'id': uuid3(NAMESPACE_DNS, munged_name),
            #         'name': munged_name,
            #         'title': group_name
            #     }
            #     context['__auth_audit'] = []
            #     group = get_action('group_create')(context, data_dict)
            #     logger.info('created the group ' + group['id'])
            #     group_ids.append({'id': group['id']})

        logger.debug('Group ids: %s' % group_ids)
        return group_ids

    def _extract_tags_and_extras(self, content):
        extras = []
        tags = []
        for key, value in content.items():
            if key in self._get_mapping().values():
                continue
            if key in ['type', 'subject']:
                if type(value) is list:
                    tags.extend(value)
                else:
                    tags.extend(value.split(';'))
                continue
            if value and type(value) is list:
                value = value[0]
            if not value:
                value = None
            if key.endswith('date') and value:
                # the ckan indexer can't handle timezone-aware datetime objects
                try:
                    from dateutil.parser import parse
                    date_value = parse(value)
                    date_without_tz = date_value.replace(tzinfo=None)
                    value = date_without_tz.isoformat()
                except (ValueError, TypeError):
                    continue

            extras.append((key, value))

        tags = [{'state': 'active', 'name': munge_tag(tag[:100])} for tag in tags]
        return (tags, extras)


    def _create_or_update_package(self, package_dict, harvest_object,
                                  package_dict_form='package_show'):
        
        previous_objects = model.Session.query(HarvestObject) \
            .filter(HarvestObject.guid == harvest_object.guid) \
            .filter(HarvestObject.current == True)

        # Mark previous object as not current anymore
        for previous_object in previous_objects:
            previous_object.current = False
            previous_object.add()

        try:
            existing_package_dict = self._find_existing_package(package_dict)
            if existing_package_dict.get('id'):
                harvest_object.package_id = munge_title_to_name(package_dict['id'])
        except:
            pass
        
        harvest_object.current = True
        harvest_object.save()

        if self.force_all:
            package_dict['metadata_modified'] = datetime.datetime.now().isoformat()

        super(SpcOaipmhHarvester, self)._create_or_update_package(package_dict, harvest_object,
                                          package_dict_form)
