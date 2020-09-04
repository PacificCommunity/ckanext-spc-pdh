import datetime
import logging

from flask import Blueprint, jsonify
from ckan.plugins import toolkit as tk
from ckan.common import g, request, streaming_response
import ckan.model as model

from ckanext.spc.utils.dataset_export import Exporter


spc_package = Blueprint("spc_package", __name__)
log = logging.getLogger(__name__)


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
        return tk.abort(403, tk._("Not authorized to read reports"))

    exporter = Exporter(_exhaustive_search(context, data_dict))
    resp = streaming_response(exporter.get_stream(), with_context=True)
    resp.headers[
        "content-disposition"
    ] = 'attachment; filename="data_export.xlsx"'
    resp.headers['Last-Modified'] = datetime.datetime.now()
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '-1'
    return resp


spc_package.add_url_rule("/dataset/ids/list", view_func=list_ids)
spc_package.add_url_rule(
    "/organization/<id>/export/datasets", view_func=export_datasets
)
