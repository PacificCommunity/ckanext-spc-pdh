import json
import logging
from datetime import datetime
from dateutil.parser import parse as parse_date
from ckantoolkit import missing, Invalid, StopOnError
from six import string_types
from ckan.lib.navl.dictization_functions import unflatten, flatten_dict

logger = logging.getLogger(__name__)


def get_validators():
    return dict(
        copy_from=copy_from,
        spc_normalize_date=spc_normalize_date,
        spc_from_json=spc_from_json,
        spc_to_json=spc_to_json,
        construct_sub_schema=construct_sub_schema,
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
    data[key] = json.dumps(value)


def spc_from_json(value):
    if isinstance(value, string_types):
        try:
            value = json.loads(value)
        except Exception as e:
            logger.warn('spc_from_json: {}'.format(e))
    return value


def construct_sub_schema(name):
    def converter(key, data, errors, context):
        junk_key = ('__junk', )
        junk = unflatten(data.get(junk_key, {}))

        sub_data = junk.pop(name, None)
        if not sub_data:
            return
        data[key] = sub_data
        data[junk_key] = flatten_dict(junk)

    return converter
