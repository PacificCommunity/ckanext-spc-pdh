# -*- coding: utf-8 -*-
import os
import datetime as dt
from functools import partial
from dateutil import parser
from flask import Blueprint, jsonify
from flask.views import MethodView

import ckan.model as model
import ckan.lib.helpers as h
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.logic as logic

import ckan.plugins.toolkit as tk

from ckan.plugins.toolkit import ObjectNotFound
from ckan.lib.base import abort, render
from ckan.common import _, g, request, config
import ckan.views.resource as resource_view
import ckanext.spc.utils as utils

spc_access_request = Blueprint('spc_access_request', __name__)


@spc_access_request.route('/dataset/request_for_access', methods=['POST'])
def request_for_access():
    context = {'user': g.user}

    pkg_id = request.form.get('package-id')
    data_dict = {
        'id': pkg_id,
        'user': g.user,
        'reason': request.form.get('request-reason'),
        'user_org': request.form.get('request-org')
    }

    try:
        req = logic.get_action('get_access_request')(context, data_dict)
    except ObjectNotFound:
        # if access request doesn't exist - create it
        pass
    except logic.NotAuthorized:
        abort(403, _('You must be authorized'))
    except logic.ValidationError as e:
        abort(403, e)

    # if request was previously rejected
    if req and req.get('state') == 'rejected':
        request_timeout = int(config.get(
            'spc.access_request.request_timeout', 3))
        data_modified = parser.isoparse(req.get('data_modified'))
        days_passed = (dt.datetime.utcnow() - data_modified).days

        if days_passed >= request_timeout:
            logic.get_action('update_access')({'ignore_auth': True}, data_dict)
        else:
            message = _('Your request was recently rejected. Try again in {} day(s)'.format(
                request_timeout - days_passed
            ))
            return jsonify(message=message)

    # if request already created
    elif req:
        message = _('Your request is in a pending state already')
        return jsonify(message=message)
    elif not req:
        req = logic.get_action('create_access_request')(context, data_dict)

    message = _('Request has been sent. You\'ll be noticed via email')
    return jsonify(message=message)


class BulkRequest(MethodView):
    def __init__(self):
        self.context = {
            'user': g.user,
            'model': model,
            'session': model.Session
        }

    def _prepare_entity_dict(self, _id, package=False):
        data_dict = {'id': _id}
        if package:
            package = model.Package.get(_id)
            package_dict = model_dictize.package_dictize(package, self.context)
            package_dict['num_followers'] = logic.get_action('dataset_follower_count')(
                self.context, data_dict)
            return package_dict
        group = model.Group.get(_id)
        group_dict = model_dictize.group_dictize(group, self.context)
        group_dict['num_followers'] = logic.get_action('group_follower_count')(
            self.context, data_dict)
        return group_dict


class OrganizationRequests(BulkRequest):
    def __init__(self):
        super().__init__()
        self.messages = {
            'approve': '{number} access request(s) have been approved',
            'reject': '{number} access request(s) have been rejected',
        }

    def get(self, org_id):
        try:
            res = logic.get_action('get_access_requests_for_org')(
                context=self.context,
                data_dict={'id': org_id, 'state': 'pending'}
            )
        except logic.NotAuthorized:
            abort(403, _('You need to be sysadmin or data custodian'))

        group_dict = self._prepare_entity_dict(org_id)

        return render('access/org_requests_list.html',
                      extra_vars={'requests': res,
                                  'group_dict': group_dict,
                                  'group_type': 'organization'})

    @staticmethod
    def _redirect(org_id):
        return h.redirect_to('spc_access_request.org_requests', org_id=org_id)

    @staticmethod
    def _get_request_ids(form):
        # they are prefixed by req_ in the form data
        return [
            i.replace('req_', '')
            for i in form.keys()
            if i.startswith('req_')
        ]

    def post(self, org_id):
        actions = {
            'approve': 'approve_access',
            'reject': 'reject_access'
        }
        act = request.form.get('bulk_action', '')
        reject_reason = request.form.get('reject-reason')

        request_ids = self._get_request_ids(request.form)

        if not request_ids:
            h.flash_error(_('Select at least one to proceed.'))
            return self._redirect(org_id)

        action = actions.get(act)

        if not action:
            h.flash_error(_('Action not implemented.'))
            return self._redirect(org_id)

        if action == 'reject_access' and not reject_reason:
            h.flash_error(_('Reject reason isn\'t provided'))
            return self._redirect(org_id)

        for _id in request_ids:
            try:
                logic.get_action(action)(self.context, {
                    'request_id': _id,
                    'user': g.user,
                    'reject_reason': reject_reason
                })
            except logic.NotFound:
                abort(404, _('User or pkg not found'))
            except logic.NotAuthorized:
                abort(403, _('You need to be sysadmin or data custodian'))

        h.flash_success(_(self.messages[act].format(number=len(request_ids))))

        return self._redirect(org_id)


class PackageRequests(BulkRequest):
    def get(self, pkg_id):
        try:
            res = logic.get_action('get_access_requests_for_pkg')(
                context=self.context,
                data_dict={'id': pkg_id, 'state': 'approved'}
            )
        except logic.NotAuthorized:
            abort(403, _('You need to be sysadmin or data custodian'))

        pkg_dict = self._prepare_entity_dict(pkg_id, package=True)

        return render('access/pkg_requests_list.html',
                      extra_vars={'requests': res, 'pkg_dict': pkg_dict})

    def post(self, pkg_id):
        if request.form.get('bulk_action') != 'reject':
            h.flash_error(_('Action not implemented.'))
            return self._redirect(pkg_id)

        reject_reason = request.form.get('reject-reason')
        if not reject_reason:
            h.flash_error(_('Reject reason isn\'t provided'))
            return self._redirect(pkg_id)

        request_ids = [
            i.replace('req_', '')
            for i in request.form.keys()
            if i.startswith('req_')
        ]

        if not request_ids:
            h.flash_error(_('Select at least one to proceed.'))
            return self._redirect(pkg_id)

        for _id in request_ids:
            try:
                logic.get_action('reject_access')(self.context, {
                    'request_id': _id,
                    'reject_reason': reject_reason,
                    'user': g.user
                })
            except logic.NotFound:
                abort(404, _('Access request not found'))
            except logic.NotAuthorized:
                abort(403, _('You need to be sysadmin or data custodian'))

        h.flash_success(
            _('{} access request(s) have been rejected'.format(len(request_ids))))
        return self._redirect(pkg_id)

    @staticmethod
    def _redirect(pkg_id):
        return h.redirect_to('spc_access_request.pkg_requests', pkg_id=pkg_id)


@spc_access_request.route("/<package_type>/<id>/resource/<resource_id>/download")
@spc_access_request.route("/<package_type>/<id>/resource/<resource_id>/download/<filename>")
def download(id, resource_id, filename=None, package_type="dataset"):
    context = {
        "model": model,
        "session": model.Session,
        "user": tk.c.user,
        "auth_user_obj": tk.c.userobj,
    }

    try:
        rsc = tk.get_action("resource_show")(context, {"id": resource_id})
        pkg = tk.get_action("package_show")(context, {"id": id})
        # Possible NotAuthorized from listeners

        if tk.h.spc_is_restricted(pkg) and context['user']:
            utils.track_resource_download(context['user'], rsc['id'])
    except (tk.ObjectNotFound, tk.NotAuthorized):
        return tk.abort(404, tk._("Resource not found"))

    return resource_view.download(package_type, id, resource_id, filename)


@spc_access_request.route("/<package_type>/<id>/download-tracking", defaults={'package_type': 'dataset'})
def package_download_tracking(id, package_type):
    context = {"user": tk.c.user}
    try:
        pkg_dict = tk.get_action('package_show')(context.copy(), {'id': id})
        tk.check_access('spc_download_tracking_list', context, pkg_dict.copy())
    except tk.NotAuthorized:
        return tk.abort(403, tk._("Not authorized to read reports"))
    except tk.ObjectNotFound:
        return tk.abort(404, tk._("Dataset not found"))
    limit = 20
    page = tk.h.get_page_number(tk.request.args)
    resp = tk.get_action('spc_download_tracking_list')(context.copy(), {
        'id': id, 'limit': limit, 'offset': page * limit - limit
    })
    params_nopage = dict(
        [(k, v) for k, v in tk.request.args.items() if k != "page"]
        + [(k, v) for k, v in tk.request.view_args.items()]
    )

    pager = h.Page(
        resp['results'],
        page=page,
        item_count=resp['count'],
        url=partial(tk.h.pager_url, **params_nopage),
        items_per_page=limit,
        presliced_list=True
    )

    extra_vars = {
        'pkg_dict': pkg_dict,
        'pager': pager,
        'records': resp['results']
    }
    return tk.render('package/spc_download_tracking.html', extra_vars)


spc_access_request.add_url_rule('/dataset/<pkg_id>/request_access',
                                'request',
                                view_func=request_for_access,
                                methods=('POST', ))

spc_access_request.add_url_rule('/organization/<org_id>/access_requests',
                                'org_requests',
                                view_func=OrganizationRequests.as_view(
                                    str('org_bulk_process')),
                                methods=('GET', 'POST'))

spc_access_request.add_url_rule('/dataset/<pkg_id>/access_requests/',
                                'pkg_requests',
                                view_func=PackageRequests.as_view(
                                    str('pkg_bulk_process')),
                                methods=('GET', 'POST'))
