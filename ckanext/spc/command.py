import logging
import os

import ckan.model as model
import paste.script
from alembic import command
from alembic.config import Config

from ckan.common import config
from ckan.lib.cli import CkanCommand
import ckan.lib.search as search

logger = logging.getLogger(__name__)


class SPCCommand(CkanCommand):
    """
    ckanext-spc management commands.

    Usage::
    paster spc [command]

    Commands::
        db-upgrade    Upgrade database to the state of the latest migration
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

        alembic_ini = os.path.normpath(
            os.path.join(__file__, '../../../alembic.ini')
        )
        self.alembic_cfg = Config(alembic_ini)
        self.alembic_cfg.set_section_option(
            'alembic', 'sqlalchemy.url', config.get('sqlalchemy.url')
        )

        cmd_name = (self.args[0] if self.args else '').replace('-', '_')
        cmd = getattr(self, cmd_name, None)
        if cmd is None:
            return self.usage

        return cmd()

    def db_upgrade(self):
        command.upgrade(self.alembic_cfg, 'head')
        return 'Success'

    def db_downgrade(self):
        command.downgrade(self.alembic_cfg, 'base')
        return 'Success'

    def fix_missed_licenses(self):
        q = model.Session.query(model.Package).filter_by(license_id=None)
        ids = [pkg.id for pkg in q]
        if not ids:
            print('There are no packages with missed license_id')
            return
        broken_count = q.update({'license_id': 'notspecified'})
        model.Session.commit()
        print('{} packages were updated:'.format(broken_count))
        for id in ids:
            search.rebuild(id)
            print('\t' + id)
