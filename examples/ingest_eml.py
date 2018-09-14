import sys

import json
import re
from collections import defaultdict

import requests
from lxml.etree import parse, QName

MULTI_PROPS = (
    'creator', 'alternate_identifier', 'keyword_set', 'para',
    'taxonomic_classification', 'personnel', 'metadata_provider', 'contact',
    'associated_party'
)


def default_value(key):
    if key in MULTI_PROPS:
        return []
    return {}


def dictize(root):
    data = dict()
    for tag in root:
        tag_name = re.sub(
            '[A-Z]', lambda match: '_' + match.group().lower(), tag.tag
        )
        default = default_value(tag_name)
        if tag_name == 'ulink':
            data['para'] = [tag.find('citetitle').text.strip() + tag.tail]
            break
        elif len(tag):
            child = dictize(tag)
            if tag_name == 'keyword_set':
                child = child['keyword']
            elif tag_name == 'taxonomic_coverage':
                child = [
                    item['taxon_rank_value']
                    for item in child['taxonomic_classification']
                ]
        else:
            child = (tag.text or '').strip()
        if isinstance(default, list):
            child = [child]

        if isinstance(default, list):
            data.setdefault(tag_name, default).extend(child)
        else:
            data[tag_name] = child
    if 'para' in data:
        data = '\n\n'.join(data['para']).strip()
    return data


root = parse(sys.argv[3]).find('dataset')
data = defaultdict(list)
data = dictize(root)

data['type'] = 'biodiversity_data'
data['name'] = re.sub('[^\w_-]', '-', data['title'].lower())
data['owner_org'] = 'test-organization'

r = requests.post(
    sys.argv[1] + '/api/action/package_create',
    data=json.dumps(data.copy()),
    headers={
        'content-type': 'application/json',
        'Authorization': sys.argv[2]
    }
)
