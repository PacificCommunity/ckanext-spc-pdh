import sdmx

import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckan.exceptions import CkanConfigurationException

from ckanext.datastore.interfaces import IDatastoreBackend

from .backend import DotstatDatastoreBackend
from ckanext.spc.utils import dotstat_api_url, CONFIG_DOTSTAT_RESTAPI


class DotstatDatastorePlugin(p.SingletonPlugin):
    p.implements(IDatastoreBackend)
    p.implements(p.IConfigurer)

    # IDatastoreBackend

    def register_backends(self):
        return {
            "postgresql": DotstatDatastoreBackend,
            "postgres": DotstatDatastoreBackend,
        }

    # IConfigurer

    def update_config(self, config):
        api = dotstat_api_url()
        if not api:
            raise CkanConfigurationException(
                f"{CONFIG_DOTSTAT_RESTAPI} config option is missing"
            )

        if "SPC" not in sdmx.list_sources():
            sdmx.add_source(
                {
                    "id": "SPC",
                    "documentation": "https://stats.pacificdata.org/?locale=en",
                    "url": dotstat_api_url(),
                    "name": "Pacific Data Hub DotStat",
                }
            )
