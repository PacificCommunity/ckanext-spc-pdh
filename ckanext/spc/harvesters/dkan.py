from ckanext.harvest.harvesters.ckanharvester import CKANHarvester
import json
from ckan import model
import ckan.lib.munge as munge
import logging

log = logging.getLogger(__name__)

MIMETYPE_FORMATS = {
    'text/html': 'HTML',
    'text/csv': 'CSV',
    'text/xml': 'XML',
    'application/pdf': 'PDF',
    'application/zip': 'ZIP',
    'application/rdf+xml': 'RDF',
    'application/json': 'JSON',
    'application/vnd.ms-excel': 'XLS',
    'application/vnd.google-earth.kml+xml': 'KML',
    'application/msword': 'DOC',
}


class PackageDictError(Exception):
    pass


class DKANHarvester(CKANHarvester):

    ckan_revision_api_works = False

    def info(self):
        return {
            'name': 'dkan',
            'title': 'DKAN',
            'description': 'Harvests remote DKAN instances',
            'form_config_interface': 'Text'
        }

    def _get_all_packages(self, base_url, harvest_job):
        # Request all remote packages
        url = base_url + '/api/3/action/package_list'
        log.debug('Getting all DKAN packages: %s', url)
        try:
            content = self._get_content(url)
        except Exception, e:
            self._save_gather_error(
                'Unable to get content for URL: %s - %s' % (url, e),
                harvest_job
            )
            return None

        packages = json.loads(content)['result']

        return packages

    def _get_package(self, base_url, harvest_object):
        url = base_url + '/api/3/action/package_show/' + harvest_object.guid
        log.debug('Getting DKAN package: %s', url)

        # Get contents
        try:
            content = self._get_content(url)
        except Exception, e:
            self._save_object_error(
                'Unable to get content for package: %s - %r' % (url, e),
                harvest_object
            )
            return None, None

        package = json.loads(content)['result'][0]
        return url, json.dumps(package)

    @classmethod
    def get_harvested_package_dict(cls, harvest_object):
        package = CKANHarvester.get_harvested_package_dict(harvest_object)
        # change the DKAN-isms into CKAN-style
        try:
            if 'extras' not in package:
                package['extras'] = {}

            if 'name' not in package:
                package['name'] = munge.munge_title_to_name(package['title'])

            if 'description' in package:
                package['notes'] = package['description']

            for license in model.Package.get_license_register().values():
                if license.title == package['license_title']:
                    package['license_id'] = license.id
                    break
            else:
                package['license_id'] = 'notspecified'

            if 'resources' not in package:
                raise PackageDictError('Dataset has no resources')
            for resource in package['resources']:
                resource['description'] = resource['title']

                if 'revision_id' in resource:
                    del resource['revision_id']

                if 'format' not in resource:
                    resource['format'] = MIMETYPE_FORMATS.get(
                        resource.get('mimetype'), ''
                    )

            if 'private' in package:
                # DKAN appears to have datasets with private=True which are
                # still public: https://github.com/NuCivic/dkan/issues/950. If
                # they were really private then we'd not get be able to access
                # them, so assume they are not private.
                package['private'] = False

            return package
        except Exception, e:
            cls._save_object_error(
                'Unable to get convert DKAN to CKAN package: %s' % e,
                harvest_object
            )
            return None

    def _fix_tags(self, package_dict):
        pass
