import logging
import json

from ckan.logic import check_access, get_action
from ckan.lib.munge import munge_title_to_name

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


    def _extract_additional_fields(self, content, package_dict):
        package_dict['thematic_area_string'] = self.topic
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
            data_dict = {
                'id': group_name,
                'name': munge_title_to_name(group_name),
                'title': group_name
            }
            try:
                check_access('group_show', context, data_dict)
                group = get_action('group_show')(context, data_dict)
                logger.info('found the group ' + group['id'])
            except:
                context['__auth_audit'] = []
                group = get_action('group_create')(context, data_dict)
                logger.info('created the group ' + group['id'])
            group_ids.append(group['id'])

        logger.debug('Group ids: %s' % group_ids)
        return group_ids
