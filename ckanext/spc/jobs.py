import csv
import logging
import sys

import ckan.lib.helpers as h

import ckan.model as model
import requests
import requests.exceptions as exc
from ckan.common import config
from ckan.lib.mailer import mail_user
logger = logging.getLogger(__name__)


def broken_links_report(recepients=[]):
    broken_count = 0
    resources = model.Session.query(
        model.Resource
    ).join(model.Package,
           model.Package.id == model.Resource.package_id).outerjoin(
               model.PackageExtra,
               (model.Package.id == model.PackageExtra.package_id) &
               (model.PackageExtra.key == 'harvest_url')
           ).filter(
               model.Resource.state == 'active',
               model.PackageExtra.key.is_(None)
           )
    total = resources.count()
    file = open(config['spc.report.broken_links_filepath'], 'wb')
    report = csv.writer(file)
    report.writerow(['Page', 'Broken URL', 'HTTP Code', 'Reason'])
    for i, res in enumerate(resources, 1):
        logger.debug(
            'Processing %s of %s. Broken links: %s', i, total, broken_count
        )

        sys.stdout.flush()
        try:
            resp = requests.head(res.url, timeout=5)
            if resp.ok:
                continue
            code, reason = resp.status_code, resp.reason
            # it's likely incorrect request to service endpoint
            if 400 == code:
                continue
        except (exc.ConnectTimeout, exc.ReadTimeout):
            code, reason = 504, 'Request timeout'
        except exc.ConnectionError:
            code, reason = 520, 'Connection Error'
        except (exc.MissingSchema, exc.InvalidSchema):
            continue
        except exc.InvalidURL:
            code, reason = 520, 'Invalid URL'

        page = h.url_for(
            'resource.read',
            id=res.package_id,
            resource_id=res.id,
            qualified=True
        )

        report.writerow([page, res.url.encode('utf-8'), code, reason])
        broken_count += 1
    file.close()
    users = model.Session.query(
        model.User
    ).filter(model.User.name.in_(recepients), ~model.User.email.is_(None))
    url = h.url_for('spc_admin.broken_links', qualified=True)
    message = u'There is new report available at {}'.format(url)
    for user in users:
        mail_user(user, 'Broken links report', message)
