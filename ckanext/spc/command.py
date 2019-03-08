import logging

import ckan.model as model
import paste.script
from ckan.lib.cli import CkanCommand
import ckan.lib.search as search

logger = logging.getLogger(__name__)


class SPCCommand(CkanCommand):
    """
    ckanext-spc management commands.

    Usage::
    paster spc [command]

    Commands::
    ...
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__

    parser = paste.script.command.Command.standard_parser(verbose=True)
    parser.add_option(
        '-c',
        '--config',
        dest='config',
        default='../spc.ini',
        help='Config file to use.'
    )

    def command(self):
        self._load_config()
        model.Session.commit()
        cmd_name = (self.args[0] if self.args else '').replace('-', '_')
        cmd = getattr(self, cmd_name, None)
        if cmd is None:
            return self.usage

        return cmd()

    def fix_missed_licenses(self):
        q = model.Session.query(model.Package).filter(
            model.Package.license_id.is_(None)
            | (model.Package.license_id == '')
        )
        ids = [pkg.id for pkg in q]
        if not ids:
            print('There are no packages with missed license_id')
            return
        broken_count = q.update({
            'license_id': 'notspecified'
        }, synchronize_session=False)
        model.Session.commit()
        print('{} packages were updated:'.format(broken_count))
        for id in ids:
            search.rebuild(id)
            print('\t' + id)
