import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.spc.helpers as spc_helpers
import ckanext.spc.utils as spc_utils
import ckanext.spc.logic.action as spc_action
import ckanext.spc.logic.auth as spc_auth
import ckanext.spc.validators as spc_validators


class SpcPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'spc')

    # ITemplateHelpers

    def get_helpers(self):
        return spc_helpers.get_helpers()

    # IActions

    def get_actions(self):
        return spc_action.get_actions()

    # IAuthFunctions

    def get_auth_functions(self):
        return spc_auth.get_auth_functions()

    # IValidators

    def get_validators(self):
        return spc_validators.get_validators()
