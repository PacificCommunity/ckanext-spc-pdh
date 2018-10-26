import json
import logging

from ckan.common import _
from datetime import datetime
from dateutil.parser import parse as parse_date
from ckantoolkit import missing, Invalid, navl_validate, StopOnError
from six import string_types
from ckan.lib.navl.dictization_functions import (
    unflatten, flatten_dict, MissingNullEncoder
)
import ckanext.spc.schemas.sub_schema as sub_schema

logger = logging.getLogger(__name__)

incorrectly_dictized_dict = (
    ('individual_name', ),
    ('address', ),
    ('geographic_coverage', ),
    ('temporal_coverage', ),
    ('taxonomic_coverage', ),
    ('range_of_dates', ),
    ('bounding_coordinates', ),
    ('sampling', ),
    ('study_area_description', ),
    ('personnel', ),

    ('metadata_extension_info', ),
)
incorrectly_dictized_sub_lists = {
    ('taxonomic_coverage', ): 'taxonomic_classification',
    ('personnel', ): 'person',

    ('metadata_extension_info', ): 'extended_element_information'
}

def get_validators():
    return dict(
        copy_from=copy_from,
        spc_normalize_date=spc_normalize_date,
        spc_from_json=spc_from_json,
        spc_to_json=spc_to_json,
        construct_sub_schema=construct_sub_schema,
        spc_ignore_missing_if_one_of=spc_ignore_missing_if_one_of,
        spc_float_validator=spc_float_validator,
    )


def copy_from(copy_key):
    def validator(key, data, errors, context):
        current_value = data.get(key)
        if current_value and current_value is not missing:
            return
        value = data.pop((copy_key, ), None)
        if not value:
            value = data.get(('__extras', ), {}).get(copy_key)
        if value is not missing:
            data[key] = value

    return validator


def spc_normalize_date(value):
    if not value or value is missing:
        return value
    try:
        return parse_date(
            value, dayfirst=True, default=datetime(2000, 1, 1)
        ).isoformat()
    except Exception as e:
        logger.warn('ValidationError[{}]: {}'.format(value, e))
        raise Invalid('cannot parse date')


def spc_to_json(key, data, errors, context):
    # ('__extras', ) - for package
    # ('resources', 0, '__extras') - for resource
    extras_key = key[:-1] + ('__extras', )
    string_value = data.get(extras_key, {}).pop(key[-1] + '_string', None)
    value = data.get(key)
    if string_value is not None:
        value = filter(None, string_value.split(','))

    if not isinstance(value, (list, dict)):
        value = [value]
    data[key] = MissingNullEncoder().encode(value)


def spc_from_json(value):
    if isinstance(value, string_types):
        try:
            value = json.loads(value)
        except Exception as e:
            logger.warn('spc_from_json: {}'.format(e))
    return value


def construct_sub_schema(name):
    def converter(key, data, errors, context):
        single_value = False
        junk_key = ('__junk', )
        junk = unflatten(data.get(junk_key, {}))
        # if key == ('metadata_extension_info', ):
            # import ipdb; ipdb.set_trace()
        # for multiple-valued fields, everything moved to junk
        sub_data = junk.pop(key[0], None) or data.get(key)

        if not sub_data or sub_data is missing:
            data[key] = missing
            return
        data[junk_key] = flatten_dict(junk)

        schema = getattr(sub_schema, 'get_default_{}_schema'.format(name))()

        if not isinstance(sub_data, (list, dict)):
            try:
                sub_data = json.loads(sub_data)
            except ValueError:
                raise Invalid(_('Plain values are not supported'))


        if key[-1:] in incorrectly_dictized_dict:
            try:
                sub_data = sub_data[0]
            except KeyError:
                pass

        if key in incorrectly_dictized_sub_lists:
            list_key = incorrectly_dictized_sub_lists[key]
            try:
                sub_data[list_key] = list(sub_data.get(list_key, {}).values())
            except AttributeError:
                pass
        if isinstance(sub_data, dict):
            single_value = True
            sub_data = [sub_data]

        validated_list = []
        errors_list = []
        for chunk in sub_data:
            validated_data, err = navl_validate(chunk, schema, context)
            validated_list.append(validated_data)
            errors_list.append(err)

        data[key] = validated_list[0] if single_value else validated_list
        if any(err for err in errors_list):
            errors.setdefault(key, []).extend(errors_list)
            raise StopOnError

    return converter


def spc_ignore_missing_if_one_of(*fields):
    def at_least_one_validator(key, data, errors, context):
        value = data.get(key)

        if value and value is not missing:
            return
        prefix = key[:-1]
        if any(
            data.get(prefix + (field, ), missing) is not missing
            for field in fields
        ):
            raise StopOnError
        raise Invalid(
            _('Cannot be empty if none of alternatives specified: {}')
            .format(fields)
        )

    return at_least_one_validator


def spc_float_validator(value):
    try:
        return float(value)
    except ValueError:
        raise Invalid(_('Must be a decimal number'))
