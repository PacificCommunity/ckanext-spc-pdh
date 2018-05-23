#!/usr/bin/env bash

echo unset PYTHON_INSTALL_LAYOUT variable
unset $PYTHON_INSTALL_LAYOUT

echo uninstall old versions libs
pip uninstall -y ckanext-viewhelpers ckanext-geoview ckanext-c3charts

echo install new versions
pip install -e git+https://github.com/ckan/ckanext-viewhelpers.git@master#egg=ckanext-viewhelpers
pip install -e git+https://github.com/ckan/ckanext-geoview@master#egg=ckanext-geoview
pip install -e git+https://github.com/ViderumGlobal/ckanext-c3charts@master#egg=ckanext-c3charts



echo
echo --------------------------------------------------------------------------------
echo Add \'viewhelpers resource_proxy geojson_view c3charts\'
echo to ckan.plugins directive of your CKAN config plugin
echo --------------------------------------------------------------------------------
echo
