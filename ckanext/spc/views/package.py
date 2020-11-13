import datetime
import logging
import enum
import io
import os
import urllib
import uuid
import magic
import requests
import json

import funcy as F
from werkzeug.datastructures import FileStorage
from flask import Blueprint, jsonify
from ckan.plugins import toolkit as tk
from ckan.common import g, request, streaming_response, config
import ckan.logic as logic
import ckan.model as model
import ckan.lib.jobs as jobs

from ckanext.spc.utils.xlsx import Exporter, Importer


spc_package = Blueprint("spc_package", __name__)
log = logging.getLogger(__name__)


class ImportState(enum.Enum):
    FAIL = "failed"
    SKIP = "skipped"
    CREATE = "created"
    UPDATE = "updated"


def _get_search_args():
    ignore = {"page", "sort", "q"}
    extras = {}
    fq = ""
    for k, v in request.args.items(multi=True):
        if k in ignore:
            continue
        if k.startswith("ext_"):
            extras[k] = v
        else:
            fq += ' %s:"%s"' % (k, v)
    context = {
        "model": model,
        "session": model.Session,
        "user": g.user,
        "for_view": True,
        "auth_user_obj": g.userobj,
    }
    data_dict = {
        "q": request.args.get("q", "*:*"),
        "fq": fq.strip(),
        "extras": extras,
        "include_private": True,
    }

    return context, data_dict


def list_ids():
    context, data_dict = _get_search_args()
    data_dict["fl"] = "id"
    data_dict["rows"] = 1000
    query = tk.get_action("package_search")(context, data_dict)
    ids = [r["id"] for r in query["results"]]
    return jsonify(ids)


def _exhaustive_search(context, data_dict):
    count = 1000
    offset = 0
    data_dict["rows"] = 100
    while offset < count:
        data_dict["start"] = offset
        query = tk.get_action("package_search")(context, data_dict)
        for pkg in query["results"]:
            yield pkg
        offset += len(query["results"])
        count = query["count"]


def export_datasets(id):
    context, data_dict = _get_search_args()
    data_dict["fq"] += f' owner_org:"{id}"'
    try:
        tk.check_access("spc_export_datasets", context, {"id": id})
    except tk.NotAuthorized:
        return tk.abort(403, tk._("Not authorized to export datasets"))

    exporter = Exporter(_exhaustive_search(context, data_dict))
    resp = streaming_response(exporter.get_stream(), with_context=True)
    resp.headers[
        "content-disposition"
    ] = 'attachment; filename="data_export.xlsx"'
    resp.headers["Last-Modified"] = datetime.datetime.now()
    resp.headers[
        "Cache-Control"
    ] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "-1"
    return resp


def _import_dataset(context, dataset, action="package_update"):
    try:
        if dataset.get('spatial', None):
            dataset['spatial'] = json.dumps(dataset['spatial'])
        pkg = tk.get_action(action)(context, dataset)
        if action == "package_update":
            return ImportState.UPDATE, pkg
        return ImportState.CREATE, pkg
    except tk.ValidationError as e:
        msg = f'Validation error during {dataset.get("id")} import: {e}'
        log.error(msg)
        return ImportState.FAIL, {"error": e, "dataset": dataset}


def _handle_imported_dataset(context, dataset):
    dataset = F.select_values(F.notnone, dataset)
    try:
        pkg = tk.get_action("package_show")(context.copy(), dataset)
    except (tk.ObjectNotFound, tk.ValidationError):
        return _import_dataset(context.copy(), dataset, "package_create")

    old_fields = F.project(pkg, dataset)
    new_fields = F.omit(dataset, old_fields)
    for field in new_fields:
        if dataset[field] is None:
            del dataset[field]

    if any(new_fields.values()):
        return _import_dataset(context.copy(), dataset)
    new_fields = F.project(dataset, old_fields)

    new_resources = dataset.setdefault('resources', [])
    old_resources = pkg.setdefault('resources', [])
    for idx, (new, old) in enumerate(zip(new_resources, old_resources)):
        old_resources[idx] = F.project(old, new)
        diff = F.omit(new, old)
        if not any(diff.values()):
            new_resources[idx] = F.omit(new, diff)
    if new_fields == old_fields:
        return ImportState.SKIP, dataset
    return _import_dataset(context.copy(), dataset)


def _get_format(c_type):
    if c_type:
        ct = c_type.split(';')[0]
        ft = ct.split('/')[-1]
        return {'content_type': ct, 'format': ft}
    return {}


def _get_action(upload, extra):
    action = None
    extra_dict = {}
    frm = _get_format(extra.get('content-type', None))
    if upload.get('id', None):
        action = 'resource_update'
        for key, _ in upload.items():
            if key == 'format':
                upload[key] = frm.get('format', '')
            if key == 'mimetype':
                upload[key] = frm.get('content_type', '')
        extra_dict = upload
    else:
        action = 'resource_create'
        extra_dict = {key: value for (key, value) in upload.items() if key not in (
                     'id', 'url', 'format', 'mimetype', 'modified', 'download_location')}
    return action, extra_dict


def _upload_resources(context, resources):

    context.update({"model": model})
    total_uploaded = 0
    for upload in resources:
        package_id = upload['package_id']
        pkg = model.Package.get(package_id)
        if not pkg:
            log.error(f"* Was trying to upload a resource to a dataset which doesn't exist (id: {package_id}). Skipping.")
            continue
        resource_location = upload['download_location'].strip()
        log.info(f"* Uploading {resource_location} to {pkg.name}")
        filename = os.path.basename(resource_location)
        local_file = os.path.isfile(resource_location)
        stream, extra = None, None
        if local_file:
            with open(resource_location, 'rb') as f:
                data = f.read()
                stream = io.BytesIO(data)
                mime = magic.Magic(mime=True)
                extra = {'content-type': mime.from_file(resource_location)}
        else:
            try:
                req = requests.get(resource_location, stream=True)
                extra = req.headers
            except:
                log.error(f"Invalid location provided: {resource_location}. Skipping.")
                continue
            stream = io.BytesIO(req.content)
                
        data_dict = dict(upload=FileStorage(stream, filename, name='file'))
        action, extra_dict = _get_action(upload, extra)
        data_dict.update(extra_dict)

        try:
            m = {'resource_create': 'created', 'resource_update': 'updated'}
            message = f"Resource {resource_location} was successfuly {m[action]} on {pkg.name}"
            logic.get_action(action)(context, data_dict)
            log.info(message)
            total_uploaded += 1
        except Exception as e:
            log.error(e)
            continue

    log.info(f"Total uploaded {total_uploaded} of {len(resources)}.")


def import_datasets(id):
    context = {
        "model": model,
        "user": g.user,
    }
    try:
        tk.check_access("spc_import_datasets", context.copy(), {"id": id})
    except tk.NotAuthorized:
        return tk.abort(403, tk._("Not authorized to import datasets"))
    org = model.Group.get(id)
    if not org:
        return tk.abort(404, tk._("Organization not found"))
    snapshot = tk.request.files.get("snapshot")
    if snapshot is None:
        return tk.abort(409, tk._("Data snapshot must be provided"))
    importer = Importer(snapshot)

    datasets = importer.get_datasets()

    results = F.group_by(
        F.first,
        [
            _handle_imported_dataset(context.copy(), dataset)
            for dataset in datasets
        ],
    )

    status_msg = "Import finished: " + ", ".join(
        [f"{state.value}: {len(results[state])}" for state in ImportState]
    )
    tk.h.flash_notice(status_msg)
    res_to_upload = len(importer.resources_to_upload)
    if res_to_upload:
        jobs.enqueue(_upload_resources, kwargs={
            'context': { "user": g.user },
            'resources': importer.resources_to_upload},
            queue='default'
        )
        tk.h.flash_notice(f"Uploading {res_to_upload} resources. This can take some time. Please check default worker log file for details.")
    failed = results[ImportState.FAIL]
    if failed:
        fail_msg = '<br/>'.join([
            f"{fail['dataset'].get('name', 'Unnamed')}: {fail['error'].error_summary}"
            for fail in map(F.second, failed)
        ])
        tk.h.flash_error(fail_msg, True)
    return tk.redirect_to("organization.read", id=org.name)


spc_package.add_url_rule("/dataset/ids/list", view_func=list_ids)
spc_package.add_url_rule(
    "/organization/<id>/export/datasets", view_func=export_datasets
)
spc_package.add_url_rule(
    "/organization/<id>/import/datasets",
    view_func=import_datasets,
    methods=("POST",),
)
