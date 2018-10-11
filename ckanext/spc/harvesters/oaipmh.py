from ckanext.oaipmh.harvester import OaipmhHarvester


class SpcOaipmhHarvester(OaipmhHarvester):
    def _extract_additional_fields(self, content, package_dict):
        skip_keys = {
            'set_spec', 'description'
        }
        for key, value in content.items():
            if key in package_dict or key in skip_keys:
                continue
            if key == 'type':
                key = 'publication_type'
            package_dict[key] = value
        package_dict.pop('extras', None)
        package_dict['type'] = 'publications'
        package_dict.pop('maintainer_email', None)

        # TODO: map coverage(list of countries) to spatial
        package_dict.pop('coverage', None)

        return package_dict
