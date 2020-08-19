# index

## Requirements

* [ckanext-scheming](https://github.com/ckan/ckanext-scheming)

## Installation

To install ckanext-spc:

1. Activate your CKAN virtual environment, for example:

   ```text
   . /usr/lib/ckan/default/bin/activate
   ```

2. Install the ckanext-spc and its requirements into your virtual environment:

   ```text
   pip install ckanext-spc
   pip install -r dev-requirements.txt
   ```

3. Add `spc` to the `ckan.plugins` setting in your CKAN config file \(by default the config file is located at `/etc/ckan/default/production.ini`\).
4. For the SpcNadaHarvester to work, install this branch of ckanext-ddi: `github.com/roly97/ckanext-ddi/tree/nada_harvester`. Alternatively, install the original ckanext-ddi extension `github.com/liip/ckanext-ddi` and then replace the files `ddiharvester.py` and `metadata.py` with the changed files found in `ckanext-ddi_changes` directory in this repo.
5. Update SOLR schema:
6. Update DB schema:

   ```text
   paster spc db-upgrade -c config.ini
   ```

7. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

   ```text
   sudo service apache2 reload
   ```

## Config Settings

Config options:

```text
scheming.dataset_schemas = ckanext.spc.schemas:dataset.json
```

## Development Installation

To install ckanext-spc for development, activate your CKAN virtualenv and do:

```text
git clone https://github.com/DataShades/ckanext-spc.git
cd ckanext-spc
python setup.py develop
pip install -r dev-requirements.txt
paster spc db-upgrade -c config.ini
```

## Template macros

This extension provides new template macro \_\[nested\_field\]\[\] which is used for rendering fields in nested schemas. It can be easily added to any page that have access to dataset metadata via next snippet:

```text
{{ nested_field(parent_field_name, index_of_current_field_amoung_other_siblings, current_field_name, parent_data_dict, parent_errors_dict) }}
```

More examples can be found in templates/macro/spc.html.

## SPC specific examples

Recently updated dataset\(within thematic area\)::  
[http://ckan.url/api/action/package\_search?q=extras\_thematic\_area\_string:%22Climate%20Change%22&sort=metadata\_modified+desc](http://ckan.url/api/action/package_search?q=extras_thematic_area_string:%22Climate%20Change%22&sort=metadata_modified+desc)

Most popular dataset\(within thematic area\)::  
[http://site.url/api/action/package\_search?q=extras\_thematic\_area\_string:%22Climate%20Change%22&sort=extras\_ga\_view\_count+desc](http://site.url/api/action/package_search?q=extras_thematic_area_string:%22Climate%20Change%22&sort=extras_ga_view_count+desc)

-----------------Running the Tests ---------------

\[nested\_field\]:

