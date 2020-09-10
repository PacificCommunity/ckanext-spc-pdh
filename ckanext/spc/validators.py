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
    ('character_set', ),
)


def get_validators():
    return dict(
        copy_from=copy_from,
        spc_normalize_date=spc_normalize_date,
        spc_from_json=spc_from_json,
        spc_to_json=spc_to_json,
        construct_sub_schema=construct_sub_schema,
        spc_ignore_missing_if_one_of=spc_ignore_missing_if_one_of,
        spc_float_validator=spc_float_validator,
        spc_list_of=spc_list_of,
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
        value = list(filter(None, string_value.split(',')))

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
        # for multiple-valued fields, everything moved to junk

        sub_data = data.get(key)
        if not sub_data or sub_data is missing:
            sub_data = junk
            try:
                for k in key[:-1]:
                    sub_data = sub_data[k]
                sub_data = sub_data.pop(key[-1], None)
            except (KeyError, IndexError):
                sub_data = None

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

        if isinstance(sub_data, dict):
            single_value = True
            sub_data = [sub_data]

        sub_data = [_listize(item) for item in sub_data]

        validated_list, errors_list = _validate_sub_data(
            sub_data, schema, context
        )

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
            data.get(prefix + (field, ), missing) not in [missing, None, '']
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


def spc_list_of(inner):
    def _spc_list_of(key, data, errors, context):
        ret = inner(key, data, errors, context)
        return ret

    return _spc_list_of


def _listize(data_dict):
    if not isinstance(data_dict, dict):
        return data_dict
    for k, v in data_dict.items():
        if isinstance(v, dict) and list(v.keys()) == list(range(len(v))):
            v = list(v.values())
        if isinstance(v, list):
            data_dict[k] = [_listize(item) for item in v]
    return data_dict


def _validate_sub_data(sub_data, schema, context):
    validated_list = []
    errors_list = []

    for chunk in sub_data:
        for k, v in schema.items():
            if not isinstance(v, list) or not isinstance(chunk.get(k), list):
                continue

            if chunk[k]:
                chunk[k] = chunk[k][0]
        validated_data, err = navl_validate(chunk, schema, context)
        validated_list.append(validated_data)
        errors_list.append(err)

    return validated_list, errors_list
