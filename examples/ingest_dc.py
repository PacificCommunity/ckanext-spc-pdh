import sys
import json
import re
from collections import defaultdict

import requests
from lxml.etree import parse, QName

root = parse(sys.argv[3])
data = defaultdict(list)
for i in root.findall('*'):
    data[QName(i).localname].append(i.text)
data = {
    re.sub('[A-Z]', lambda match: '_' + match.group().lower(), key):
    ', '.join(value)
    for key, value in data.items()
}

data['type'] = 'publications'
data['name'] = re.sub('[^\w_-]', '-', data['title'].lower())[:99] # put hyphens instead of incorrect symbols
data['owner_org'] = 'test-organization' # name or id of organization

data.pop('coverage', None) # unless it's valid geoJSON, remove it
if 'spatial' in data:
    data['spatial_coverage'] = data.pop('spatial')

requests.post(
    sys.argv[1] + '/api/action/package_create',
    data=json.dumps(data.copy()),
    headers={
        'content-type': 'application/json',
        'Authorization': sys.argv[2]
    }
)
