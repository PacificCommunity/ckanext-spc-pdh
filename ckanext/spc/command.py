import logging
import os

from time import sleep
import ckan.model as model
import ckan.plugins.toolkit as tk
import paste.script
from alembic import command
from alembic.config import Config

from ckan.common import config
from ckan.lib.cli import CkanCommand
import ckan.lib.search as search

logger = logging.getLogger(__name__)
country_orgs = {
    "palau": "Palau Environment Data Portal",
    "fsm": "Federated States of Micronesia Environment Data Portal",
    "png": "Papua New Guinea Data Portal",
    "vanuatu": "Vanuatu Environment Data Portal",
    "solomonislands": "Solomon Islands Environment Data Portal",
    "nauru": "Nauru Environment Data Portal",
    "rmi": "Republic of Marshall Islands Environment Data Portal",
    "tuvalu": "Tuvalu Environment Data Portal",
    "fiji": "Fiji Environment Data Portal",
    "tonga": "Tonga Environment Data Portal",
    "samoa": "Samoa Environment Data Portal",
    "niue": "Niue Environment Data Portal",
    "cookislands": "Cook Islands Environment Data Portal",
    "kiribati": "Kiribati Environment Data Portal",
}


class SPCCommand(CkanCommand):
    """
    ckanext-spc management commands.

    Usage::
    paster spc [command]

    Commands::
        db-upgrade    Upgrade database to the state of the latest migration
        fix-missed-licenses
        drop-mendeley-publications
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
    parser.add_option(
        '-d',
        '--delay',
        type=int,
        default=1,
        help='Delay between pushes to datastore.'
    )
    parser.add_option(
        '-f',
        '--formats',
        type=str,
        default='xls,csv,xlsx',
        help='Delay between pushes to datastore.'
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

    def create_datastore(self):
        resources = model.Session.query(model.Resource)
        step = 20
        user = tk.get_action('get_site_user')({'ignore_auth': True})
        for offset in range(0, resources.count(), step):
            for res in resources.offset(offset).limit(step):
                if res.extras.get('datastore_active'):
                    continue
                if not res.format or res.format.lower() not in self.options.formats.split(','):
                    continue

                print('Pushing <{}> into datastore'.format(res.id))
                tk.get_action('datastore_create')(
                    {'ignore_auth': True, 'user': user['name']},
                    {'resource_id': res.id, 'force': True}
                )

                tk.get_action('datapusher_submit')(
                    {'ignore_auth': True, 'user': user['name']},
                    {'resource_id': res.id, 'force': True}
                )
                sleep(self.options.delay)

        return 'Success'

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
        },
                                synchronize_session=False)
        model.Session.commit()
        print('{} packages were updated:'.format(broken_count))
        for id in ids:
            search.rebuild(id)
            print('\t' + id)

    def update_topic_names(self):
        pairs = (
            ('"Social"', '"Gender and Youth"'),
            ('"Statistics"', '"Official Statistics"'),
        )
        model.repo.new_revision()
        for old_name, new_name in pairs:
            items = model.Session.query(
                model.PackageExtra
            ).filter_by(key='thematic_area_string').filter(
                model.PackageExtra.value != '[]',
                ~model.PackageExtra.value.is_(None),
                model.PackageExtra.value.contains(old_name)
            )
            for item in items:
                item.value = item.value.replace(old_name, new_name)
        model.repo.commit_and_remove()

    def create_country_orgs(self):
        site_user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
        for name, title in country_orgs.items():
            if model.Session.query(model.Group).filter_by(name=name + '-data'
                                                          ).count():
                continue
            tk.get_action('organization_create')({
                'ignore_auth': True,
                'user': site_user['name']
            }, {
                'name': name + '-data',
                'title': title
            })

    def drop_mendeley_publications(self):
        while True:
            results = tk.get_action('package_search')(
                None, {
                    'q': 'harvest_source:MENDELEY',
                    'rows': 100
                }
            )
            if not results['count']:
                break
            print('{} packages left'.format(results['count']))
            for pkg in results['results']:
                package = model.Package.get(pkg['id'])
                if package:
                    package.purge()
                    print('\tPurged package <{}>'.format(pkg['id']))
            model.Session.commit()
        print('Done')

    def update_dataset_coordinates(self):
        # EXAMPLE: paster spc update_dataset_coordinates 'COORDINATES_NEW' 'FIND_WITH_CURRENT' -c /etc/ckan/default/production.ini
        if self.args[1] and self.args[2]:
            new_coordinates = self.args[1]
            find_with_current = self.args[2]

            q = model.Session.query(model.PackageExtra)\
                .filter(model.PackageExtra.key == 'spatial')
            updated_items = []
            ds_list = [ds_extra for ds_extra in q.all() if find_with_current in ds_extra.value]
            if len(ds_list):
                print('There are items that match, will start to update')
                for ds in ds_list:
                    q = model.Session.query(model.PackageExtra)\
                        .filter(model.PackageExtra.id == ds.id)
                    if q:
                        q.update({
                            'value': new_coordinates
                            })
                        updated_items.append(ds.package_id)
                model.Session.commit()
                print('{0} items been updated. Here is the list of IDs:{1}'.format(
                    len(updated_items), updated_items))
            else:
                print('No items match found.')
        else:
            print('Please provide two arguments.')
