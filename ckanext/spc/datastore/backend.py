"""Datastore Backend implementations.

DotstatDatastoreBackend itercepts requests to datastore and makes
direct requests to Dotstat API in order to return most accurate
information. For all non-dotstat resources, default CKAN's PostgreSQL
backend is used.

"""
import os
import csv
import tempfile
import requests_cache
import requests
import pandas
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.datastore.backend.postgres import DatastorePostgresqlBackend

import ckanext.spc.utils as utils

CONFIG_DOTSTAT_CACHE_AGE = "spc.dotstat.cache.seconds"
CACHE_PATH = os.path.join(tempfile.gettempdir(), "spc_dotstat_cache")

CONFIG_DOTSTAT_FAST_SEARCH = "spc.dotstat.fast_search"


def _get_csv_reader(id: str):
    res = model.Resource.get(id)
    if res and utils.is_dotstat_url(res.url):
        with requests_cache.enabled(
            CACHE_PATH,
            expire_after=tk.asint(tk.config.get(CONFIG_DOTSTAT_CACHE_AGE, 60)),
        ):

            resp = requests.get(res.url, stream=True)
            if resp.ok:
                return csv.DictReader(resp.iter_lines(decode_unicode=True))


class DotstatDatastoreBackend(DatastorePostgresqlBackend):
    def resource_id_from_alias(self, res_id):
        if _get_csv_reader(res_id):
            return True, res_id

        return super(DotstatDatastoreBackend, self).resource_id_from_alias(res_id)


    def resource_fields(self, id):
        reader = _get_csv_reader(id)
        if reader:
            for _ in reader:
                pass
            info = {
                "schema": {field: "text" for field in reader.fieldnames},
                "meta": {"count": reader.line_num},
            }

            return info

        return super().resource_fields(id)

    def search(self, context, data_dict):
        reader = _get_csv_reader(data_dict.get("resource_id"))
        if reader:
            data_dict["records"] = []
            data_dict["fields"] = []
            include_total = data_dict.get("include_total")
            limit = data_dict.get("limit", 100)
            offset = data_dict.get("offset", 0)

            fast_search = tk.asbool(tk.config.get(CONFIG_DOTSTAT_FAST_SEARCH, True))
            if not limit and not include_total and fast_search:
                return data_dict

            data_dict["fields"] = [
                {"id": id, "type": "text"} for id in reader.fieldnames
            ]
            dataframe = pandas.DataFrame(reader)

            if limit:
                sort = data_dict.get("sort")
                if sort:
                    sort_column, sort_direction = (
                        sort.rsplit(maxsplit=1) + ["asc"]
                    )[:2]
                    dataframe = dataframe.sort_values(
                        sort_column, ascending=sort_direction == "asc"
                    )
                # dataframe = dataframe.fillna("").applymap(str)
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

                if include_total:
                    data_dict["total"] = len(dataframe)

                dataframe = dataframe[offset : offset + limit]
                records = dataframe.to_dict("records")

                # dataflow_id = f"{data.structure.maintainer.id}:{data.structure.id}(data.structure.version)"
                # for record in records:
                # record["DATAFLOW"] = dataflow_id
                data_dict["records"] = records
            return data_dict

        return super(DotstatDatastoreBackend, self).search(context, data_dict)
