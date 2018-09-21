import os
import sys
import json
import re
from collections import defaultdict

import requests
from lxml.etree import parse, QName

try:
    skip = int(sys.argv[4])
except IndexError:
    skip = 0

skipped = 0


def eject_data(root, defaults={}):
    data = defaultdict(list)
    for i in root.findall('*'):
        data[QName(i).localname].append(i.text)
    data = {
        re.sub('[A-Z]', lambda match: '_' + match.group().lower(), key):
        value[0] if 1 == len(value) else value
        for key, value in data.items()
    }

    if 'subject' in data:
        if isinstance(data['subject'], basestring):
            data['subject'] = [data['subject']]
        data['subject'] = [
            re.sub('[^\w_.-]', '-', term) for term in data['subject']
        ]
    data['type'] = 'publications'
    if data['title'] is None:
        data['title'] = defaults['title']
    data['name'] = re.sub('[^\w_-]', '-', data['title'].lower()
                          )[:99]  # put hyphens instead of incorrect symbols
    data['owner_org'] = 'test-organization'  # name or id of organization

    data.pop('coverage', None)  # unless it's valid geoJSON, remove it
    if 'spatial' in data:
        data['spatial_coverage'] = data.pop('spatial')
    return data


def post_data(data):
    return requests.post(
        sys.argv[1] + '/api/action/package_create',
        data=json.dumps(data.copy()),
        headers={
            'content-type': 'application/json',
            'Authorization': sys.argv[2]
        }
    )


def parse_single(root):
    data = eject_data(root)
    post_data(data)


def parse_multiple(root):
    global skipped
    i = 0
    list_keys = set()
    root = root.getroot()
    records = root.findall('ListRecords/record', namespaces=root.nsmap)
    for record in records:
        i += 1
        if skipped < skip:
            skipped += 1
            continue
        id = record.find('header/identifier', namespaces=root.nsmap).text
        dc = record.find('metadata', namespaces=root.nsmap)[0]
        data = eject_data(dc, {'title': id})
        response = post_data(data)
        if not response.ok:
            err = response.json()['error']
            if 'name' not in err:
                raise
            print(
                '[{:05}]Not Posted {}. CKAN error: {}'.format(i, id, err)
            )
        else:
            print(
                '[{:05}]Posted {}. CKAN dataset id: {}'.format(
                    i, id,
                    response.json()['result']['id']
                )
            )

    return list_keys


def main():
    path = sys.argv[3]
    if os.path.isdir(path):
        for filename in sorted(os.listdir(path)):
            full_path = os.path.join(path, filename)
            parse_multiple(parse(full_path))
            print('Completed {}'.format(full_path))
    else:
        root = parse(path)
        parse_single(root)


if __name__ == '__main__':
    main()
