from lxml.etree import parse, QName, fromstring
from requests import get

url = 'http://www.spc.int/DigitalLibrary/OAI'

params = dict(verb='ListRecords', metadataPrefix='oai_dc')
i = 1

while True:
    resp = get(url, params)
    print('Downloaded {} page.'.format(i))
    root = fromstring(resp.content)
    records_list = root.find('ListRecords', namespaces=root.nsmap)
    if records_list is None:
        print('Done')
        return
    resumption_token = records_list.find(
        'resumptionToken', namespaces=root.nsmap
    ).text

    with open('archive/{:05}.xml'.format(i), 'w') as dest:
        dest.write(resp.content)
    print(' Stored {} page'.format(i))
    i += 1
    params.pop('metadataPrefix', None)
    params['resumptionToken'] = resumption_token
