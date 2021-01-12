"""Datastore Backend implementations.

DotstatDatastoreBackend itercepts requests to datastore and makes
direct requests to Dotstat API in order to return most accurate
information. For all non-dotstat resources, default CKAN's PostgreSQL
backend is used.

"""
import os
import tempfile
import sdmx
from sdmx.model import AttributeValue
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.datastore.backend.postgres import DatastorePostgresqlBackend

import ckanext.spc.utils as utils

CONFIG_DOTSTAT_CACHE_AGE = "spc.dotstat.cache.seconds"


def _as_dataframe(data):
    return (
        sdmx.to_pandas(data, attributes="o")
        .reset_index()
        .rename(columns={"value": "OBS_VALUE"})
    )


def _stat_id_by_res_id(id):
    res = model.Resource.get(id)
    if res and utils.is_dotstat_url(res.url):
        key = res.url[len(utils.dotstat_api_url() + "/data/") :]
        key = key.replace("format=csv", "format=structure")
        return key


def _request():
    return sdmx.Request(
        "SPC",
        backend="sqlite",
        fast_save=True,
        expire_after=tk.asint(tk.config.get(CONFIG_DOTSTAT_CACHE_AGE, 60)),
        cache_name=os.path.join(tempfile.gettempdir(), 'spc_dotstat_cache')
    )


def _get_data(id):
    req = _request()
    data = req.data(id)
    return data


def _get_fields(data):
    fields = {field: "text" for field in _as_dataframe(data).keys()}
    fields["DATAFLOW"] = "text"
    fields["OBS_VALUE"] = fields.pop("value", "text")
    return fields


def sdmx_serializer(obj):
    if isinstance(obj, AttributeValue):
        return obj.value
    return obj


class DotstatDatastoreBackend(DatastorePostgresqlBackend):
    def resource_fields(self, id):
        stat_id = _stat_id_by_res_id(id)
        if stat_id:
            data = _get_data(stat_id)
            info = {
                "schema": _get_fields(data),
                "meta": {"count": len(data.data[0].obs)},
            }

            return info

        return super().resource_fields(id)

    def search(self, context, data_dict):
        stat_id = _stat_id_by_res_id(data_dict.get("resource_id"))
        if stat_id:
            data_dict["records"] = []
            limit = data_dict.get("limit", 100)
            offset = data_dict.get("offset", 0)
            data = _get_data(stat_id)
            fields = _get_fields(data)
            data_dict["fields"] = [
                #    {"id": "_id", "type": "int"}
            ] + [{"id": id, "type": type} for id, type in fields.items()]
            if limit:
                dataframe = _as_dataframe(data).applymap(sdmx_serializer)
                sort = data_dict.get("sort")
                if sort:
                    sort_column, sort_direction = (
                        sort.rsplit(maxsplit=1) + ["asc"]
                    )[:2]
                    dataframe = dataframe.sort_values(
                        sort_column, ascending=sort_direction == "asc"
                    )
                dataframe = dataframe.fillna("").applymap(str)
                q = str(data_dict.get("q"))
                for fkey, fvalue in data_dict.get("filters", {}).items():
                    dataframe = dataframe[dataframe[fkey] == fvalue]
                if q:
                    dataframe = dataframe[
                        dataframe.apply(
                            lambda row: row.astype(str)
                            .str.contains(q, case=False)
                            .any(),
                            axis=1,
                        )
                    ]

                if data_dict.get("include_total"):
                    data_dict["total"] = len(dataframe)

                dataframe = dataframe[offset : offset + limit]
                records = dataframe.to_dict("records")

                dataflow_id = f"{data.structure.maintainer.id}:{data.structure.id}(data.structure.version)"
                for record in records:
                    record["DATAFLOW"] = dataflow_id
                data_dict["records"] = records
            return data_dict

        return super(DotstatDatastoreBackend, self).search(context, data_dict)
