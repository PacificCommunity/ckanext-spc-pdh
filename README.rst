
=============
ckanext-spc
=============

.. Put a description of your extension here:
   What does it do? What features does it have?
   Consider including some screenshots or embedding a video!


------------
Requirements
------------

- `ckanext-scheming <https://github.com/ckan/ckanext-scheming>`_


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-spc:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-spc and its requirements into your virtual environment::

     pip install ckanext-spc
     pip install -r dev-requirements.txt

3. Add ``spc`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Update SOLR schema::

     <field name="topic" type="string" indexed="true" stored="true" multiValued="true"/>

5. Update DB schema::

     paster spc db-upgrade -c config.ini


6. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config Settings
---------------

Config options::

    scheming.dataset_schemas = ckanext.spc.schemas:dataset.json

------------------------
Development Installation
------------------------

To install ckanext-spc for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/DataShades/ckanext-spc.git
    cd ckanext-spc
    python setup.py develop
    pip install -r dev-requirements.txt
    paster spc db-upgrade -c config.ini

---------------
Template macros
---------------

This extension provides new template macro _nested_field_ which is
used for rendering fields in nested schemas. It can be easily added to
any page that have access to dataset metadata via next snippet::

  {{ nested_field(parent_field_name, index_of_current_field_amoung_other_siblings, current_field_name, parent_data_dict, parent_errors_dict) }}

More examples can be found in `templates/macro/spc.html`.

---------------------
SPC specific examples
---------------------

Recently updated dataset(within thematic area)::
  http://ckan.url/api/action/package_search?q=extras_thematic_area_string:%22Climate%20Change%22&sort=metadata_modified+desc

Most popular dataset(within thematic area)::
  http://site.url/api/action/package_search?q=extras_thematic_area_string:%22Climate%20Change%22&sort=extras_ga_view_count+desc

-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.spc --cover-inclusive --cover-erase --cover-tests

-------------------
General Information
-------------------


Harvesters
##########

OAI-PMH
*******

* Name used in config: **spc\_oaipmh\_harvester**
* Dataset type: **publications**
* Sources:

+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| Url                                       | Title                           | Settings                                       | Organization |
+===========================================+=================================+================================================+==============+
| http://www.spc.int/DigitalLibrary/SPC/OAI | Social Development Program      | {"set": "SDP_PDH", "topic": "Gender and Youth"}          | spc-sdp      |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| http://www.spc.int/DigitalLibrary/SPC/OAI | Climate Change and              | {"set": "CCES_PDH", "topic": "Climate Change"} | spc-cces     |
|                                           | Environmental Sustainability    |                                                |              |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| http://www.spc.int/DigitalLibrary/SPC/OAI | Fisheries, Aquaculture &        | {"set": "FAME_PDH", "topic": "Fisheries"}      | spc-fame     |
|                                           | Marine Ecosystems               |                                                |              |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| http://www.spc.int/DigitalLibrary/SPC/OAI | Geoscience, Energy and Maritime | {"set": "GEM_PDH", "topic": "Geoscience"}      | spc-gem      |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| http://www.spc.int/DigitalLibrary/SPC/OAI | Land Resources Division         | {"set": "LRD_PDH", "topic": "Land Resources"}  | spc-lrd      |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| http://www.spc.int/DigitalLibrary/SPC/OAI | Public Health Division          | {"set": "PHD_PDH", "topic": "Health"}          | spc-phd      |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| http://www.spc.int/DigitalLibrary/SPC/OAI | Statistics for Development      | {"set": "SDD_PDH", "topic": "Official Statistics"}      | spc-sdd      |
|                                           | Division                        |                                                |              |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+

DKAN
****

* Name used in config: **spc\_dkan\_harvester**
* Dataset type: **dataset**
* Sources:

+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| Url                                       | Title                           | Settings                                       | Organization |
+===========================================+=================================+================================================+==============+
|                                           |                                 |                                                |              |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+

GBIF
****

* Name used in config: **spc\_gbif\_harvester**
* Dataset type: **biodiversity\_data**
* Sources:

+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| Url                                       | Title                           | Settings                                       | Organization |
+===========================================+=================================+================================================+==============+
| http://api.gbif.org                       | GBIF SPREP published            | {"topic": "Fisheries", "hosting_org":          | sprep        |
|                                           |                                 | "cd3512e7-886c-4873-b629-740abe8ae74e",        |              |
|                                           |                                 | "q": "-spc"}                                   |              |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| http://api.gbif.org                       | GBIF SPC published              | {"topic": "Fisheries", "hosting_org":          | spc-fame     |
|                                           |                                 | "cd3512e7-886c-4873-b629-740abe8ae74e",        |              |
|                                           |                                 | "q": "+spc"}                                   |              |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+

PRDR Publications Harvester
***************************

* Name used in config: **spc\_prdr\_publications\_harvester**
* Dataset type: **publications**
* Sources:

+--------------------------------------------------------------------+-----------------------+---------------------+--------------+
| Url                                                                | Title                 | Settings            | Organization |
+====================================================================+=======================+=====================+==============+
| https://prdr-dev.spc.links.com.au/api/action/publications_list     | SPC PRDR Publications | {"topic": "Energy"} | spc-gem      |
+--------------------------------------------------------------------+-----------------------+---------------------+--------------+

PRDR Data(energy-resource) Harvester
************************************

* Name used in config: **spc\_prdr\_res\_energy\_harvester**
* Dataset type: **dataset**
* Sources:

+--------------------------------------------------------------------+-----------------------+---------------------+--------------+
| Url                                                                | Title                 | Settings            | Organization |
+====================================================================+=======================+=====================+==============+
| https://prdr-dev.spc.links.com.au/api/action/energy_resources_list | SPC PRDR Data         | {"topic": "Energy"} | spc-gem      |
+--------------------------------------------------------------------+-----------------------+---------------------+--------------+

SPREP
*****

* Name used in config: **spc\_sprep\_harvester**
* Dataset type: **dataset**
* Sources:

+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+
| Url                                       | Title                           | Settings                                       | Organization |
+===========================================+=================================+================================================+==============+
|  https://pacific-data.sprep.org           | Inform Regional Data Portal     | {"topic_mapping": {"Atmosphere and Climate":   | sprep        |
|                                           |                                 | "Climate Change", "Info": null,                |              |
|                                           |                                 | "Land": "Land Resources",                      |              |
|                                           |                                 | "Biodiversity": "Fisheries",                   |              |
|                                           |                                 | "Build Environment": "Economic Development",   |              |
|                                           |                                 | "Coastal and Marine": "Fisheries",             |              |
|                                           |                                 | "Culture and Heritage": "Gender and Youth",              |              |
|                                           |                                 | "Inland Waters": "Geoscience"}}                |              |
+-------------------------------------------+---------------------------------+------------------------------------------------+--------------+


Datasets types
##############

* **Biodiversity data** - EML schema

This Dataset type has multiple fields which includes subfields:
	- Creator
	- Metadata Provider
	- Associated Party
	- Keyword Set
	- Coverage
	- Maintenance
	- Contact
	- Methods
	- Project

* **Dataset** - DCAT schema
* **Geographic data** - ANZLIC schema
* **Publications** - Dublin Core schema
