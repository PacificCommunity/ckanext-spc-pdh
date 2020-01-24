import logging
import os

from time import sleep
import ckan.model as model
from ckanext.harvest import model as harvest_model
import ckan.plugins.toolkit as tk
import paste.script
import sqlalchemy
from alembic import command
from alembic.config import Config

from ckan.common import config
from ckan.lib.cli import CkanCommand
from ckanext.spc.jobs import broken_links_report
import ckan.lib.jobs as jobs
import ckan.lib.search as search

_select = sqlalchemy.sql.select
_func = sqlalchemy.func
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_

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
        broken_links_report
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

    def broken_links_report(self):
        jobs.enqueue(broken_links_report)

    def fix_harvester_duplications(self):
        # paster spc fix_harvester_duplications 'SOURCE_TYPE_TO_DROP' -c /etc/ckan/default/production.ini
        # paster spc fix_harvester_duplications 'SPREP' -c /etc/ckan/default/production.ini

        # Prepare HarvestObject to have munged ids for search
        formatted_harvest_objects = model.Session.query(
            harvest_model.HarvestObject,
            _func.replace(_func.replace(harvest_model.HarvestObject.guid, ':', '-'), '.', '-').label('possible_id')
            ).subquery()

        # Find packages with duplications
        subquery_packages = model.Session.query(
            model.Package.id.label('pkg_id'),
            harvest_model.HarvestSource.id.label('hs_id'),
            harvest_model.HarvestSource.type.label('hs_type'),
        )\
        .distinct()\
        .join(
            formatted_harvest_objects,
            _or_(
                formatted_harvest_objects.c.guid == model.Package.id,
                formatted_harvest_objects.c.possible_id == model.Package.id,
                formatted_harvest_objects.c.package_id == model.Package.id
            )
        ).join(
            harvest_model.HarvestSource,
            formatted_harvest_objects.c.harvest_source_id == harvest_model.HarvestSource.id
        ).group_by(
            model.Package.id,
            formatted_harvest_objects.c.id,
            harvest_model.HarvestSource.id
        ).subquery()
            
        subquery_count = model.Session.query(
            subquery_packages.c.pkg_id.label('pkg_id'),
            _func.count(subquery_packages.c.pkg_id).label('hs_count'),
            _func.array_agg(subquery_packages.c.hs_id).label('hs_ids'),
            _func.array_agg(subquery_packages.c.hs_type).label('hs_types')
        ).group_by(subquery_packages.c.pkg_id).subquery()

        q = model.Session.query(
            subquery_count.c.pkg_id, 
            subquery_count.c.hs_ids,
            subquery_count.c.hs_types)\
        .filter(subquery_count.c.hs_count > 1) 

        res = q.all()

        package_ids = []
        harvest_sources_types = []
        harvest_sources_ids = []
        for pkg_id, hs_ids, hs_types in res:
            package_ids.append(pkg_id)
            harvest_sources_types.extend(x for x in hs_types if x not in harvest_sources_types)
            harvest_sources_ids.extend(x for x in hs_ids if x not in harvest_sources_ids)

        try:
            source_type_to_drop = self.args[1]
            if len(res) == 0 or len(harvest_sources_types) < 2:
                raise ValueError
        except IndexError:
            print('Source type to drop is not defined')
            print('paster spc fix_harvester_duplications \'SOURCE_TYPE_TO_DROP\' -c /etc/ckan/default/production.ini')
            return
        except ValueError:
            print('No duplications found')
            return

        print('{} duplications found'.format(len(res)))    
        print('Duplications found for source types: {}'.format(', '.join(harvest_sources_types)))
        print('Harvest Sources IDs: {}'.format(', '.join(harvest_sources_ids)))

        # Filter by Source
        harvest_objects_ids = model.Session.query(formatted_harvest_objects.c.id)\
        .join(
            harvest_model.HarvestSource,
            harvest_model.HarvestSource.id == formatted_harvest_objects.c.harvest_source_id
            
        ).filter(harvest_model.HarvestSource.type == source_type_to_drop)\
        .join(
            model.Package,
            _or_(
                model.Package.id == formatted_harvest_objects.c.guid,
                model.Package.id == formatted_harvest_objects.c.possible_id,
                model.Package.id == formatted_harvest_objects.c.package_id
            )
        ).filter(model.Package.id.in_(package_ids)).all()

        # Delete Harvest Object Errors
        if harvest_objects_ids:
            model.Session.query(harvest_model.HarvestObjectError)\
            .filter(harvest_model.HarvestObjectError.harvest_object_id.in_(harvest_objects_ids))\
            .delete(synchronize_session='fetch')

            # Delete Harvest Objects
            model.Session.query(harvest_model.HarvestObject)\
            .filter(harvest_model.HarvestObject.id.in_(harvest_objects_ids))\
            .delete(synchronize_session='fetch')

        model.Session.commit()

        print 'Done'

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
