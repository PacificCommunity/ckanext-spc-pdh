#!/usr/bin/env bash


LIB_URL=http://www.spc.int/DigitalLibrary/SPC/OAI

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

echo Creating user for harvesting
paster --plugin=ckan user add harvest email=harvest@example.com password=$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c12) -c $1

echo Creating harvest sources
url=$LIB_URL

name='spc-cces'
title='Climate Change and Environmental Sustainability'
org='spc-cces'
config='{"set": "CCES_PDH", "topic": "Climate Change"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1

name='spc-fame'
title='Fisheries, Aquaculture & Marine Ecosystems'
org='spc-fame'
config='{"set": "FAME_PDH", "topic": "Fisheries"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1

name='spc-gem'
title='Geoscience, Energy and Maritime'
org='spc-gem'
config='{"set": "GEM_PDH", "topic": "Geoscience"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1

name='spc-lrd'
title='Land Resources Division'
org='spc-lrd'
config='{"set": "LRD_PDH", "topic": "Land Resources"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1

name='spc-phd'
title='Public Health Division'
org='spc-phd'
config='{"set": "PHD_PDH", "topic": "Health"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1

name='spc-sdp'
title='Social Development Program'
org='spc-sdp'
config='{"set": "SDP_PDH", "topic": "Social"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1

name='spc-sdd'
title='Statistics for Development Division'
org='spc-sdd'
config='{"set": "SDD_PDH", "topic": "Statistics"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1

# GBIF
url='http://api.gbif.org'
name='spc-gbif'
title='GBIF SPC published'
org='spc-fame'
config='{"topic": "Fisheries", "hosting_org": "cd3512e7-886c-4873-b629-740abe8ae74e", "q": "+spc"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" GBIF "$title" true "$org" DAILY "$config" -c $1

name='sprep-gbif'
title='GBIF SPREP published'
org='sprep'
config='{"topic": "Fisheries", "hosting_org": "cd3512e7-886c-4873-b629-740abe8ae74e", "q": "-spc"}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" GBIF "$title" true "$org" DAILY "$config" -c $1

# SPREP
url='https://pacific-data.sprep.org'
name='sprep'
title='Inform Regional Data Portal '
org='sprep'
config='{"topic_mapping": {"Atmosphere and Climate": "Climate Change", "Info": null, "Land": "Land Resources", "Biodiversity": "Fisheries", "Build Environment": "Economic Development", "Coastal and Marine": "Fisheries", "Culture and Heritage": "Social", "Inland Waters": "Geoscience"}}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" SPREP "$title" true "$org" DAILY "$config" -c $1


# PacGeo
url='http://www.pacgeo.org/catalogue/csw'
name='pacgeo'
title='PacGeo'
org='spc-gem'
config='{"keywords": ["maritimeboundaries", "boundaries-administrative"]}'
paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
paster --plugin=ckanext-harvest harvester source "$name" "$url" pacgeo "$title" true "$org" DAILY "$config" -c $1

echo
echo ________________________________________________________________________________
echo Done

echo
echo Make sure you have redis installed and it\'s automatically started during system boot.
echo Setup ckanext-harvest for production.
echo Reference: https://github.com/ckan/ckanext-harvest#setting-up-the-harvesters-on-a-production-server

echo
echo Update $1 with following changes:
echo -e '\t'ckan.auth.user_create_groups = true
echo -e '\t'ckan.harvest.mq.type = redis
echo -e '\t'ckan.plugins = ... harvest spc_oaipmh_harvester spc_dkan_harvester spc_gbif_harvester spc_pacgeo_harvester

echo
echo Restart server and create new harvest sources under /harvest:
echo -e '\t{"set": HARVEST_SET, "topic": DEFAULT_TOPIC}'
