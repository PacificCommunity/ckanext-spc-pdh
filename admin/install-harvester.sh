#!/usr/bin/env bash

if [ ! -d 'ckanext-spc' ]
then
    echo Switch to folder containing CKAN extensions
fi

read -p "Have you updated ckanext-spc source?(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo You need to do it manually
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
fi

echo Downloading ckanext-harvest
git clone https://github.com/ckan/ckanext-harvest
cd ckanext-harvest

echo Installing dependencies
pip install -r pip-requirements.txt

echo Installing extension
pip install -e .

cd ..

echo Downloading ckanext-harvest
git clone https://github.com/openresearchdata/ckanext-oaipmh

cd ckanext-oaipmh

echo Installing dependencies
pip install -r requirements.txt

echo Installing extension
pip install -e .

cd ..

echo Reinstall ckanext-spc
pip install -e ckanext-spc

echo Initializing database
paster --plugin=ckanext-harvest harvester initdb --config=$1


echo
echo ________________________________________________________________________________
echo Done
echo
echo Make sure you have redis installed and it\'s automatically started during system boot.
echo Setup ckanext-harvest for production.
echo Reference: https://github.com/ckan/ckanext-harvest#setting-up-the-harvesters-on-a-production-server
echo
echo Update $1 with following changes:
echo -e '\t'ckan.harvest.mq.type = redis
echo -e '\t'ckan.plugins = ... harvest spc_oaipmh_harvester spc_dkan_harvester
echo
echo Restart server and create new harvest sources under /harvest:
echo -e '\t{"set": HARVEST_SET, "user": HARVEST_USER}'
