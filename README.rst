
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

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

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


---------------------------------
Registering ckanext-spc on PyPI
---------------------------------

ckanext-spc should be availabe on PyPI as
https://pypi.python.org/pypi/ckanext-spc. If that link doesn't work, then
you can register the project on PyPI for the first time by following these
steps:

1. Create a source distribution of the project::

     python setup.py sdist

2. Register the project::

     python setup.py register

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the first release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags


----------------------------------------
Releasing a New Version of ckanext-spc
----------------------------------------

ckanext-spc is availabe on PyPI as https://pypi.python.org/pypi/ckanext-spc.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag 0.0.2
       git push --tags
