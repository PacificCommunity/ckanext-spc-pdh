#!/usr/bin/env bash
function skip() {
    echo
}
function install-deps() {
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
}
function clear-sources() {
    names="pacgeo sprep sprep-gbif spc-gbif spc-sdd spc-sdp spc-phd spc-lrd spc-gem spc-fame spc-cces"
    for name in $names; do
        paster --plugin=ckanext-harvest harvester clearsource "$name" -c $1
    done
}
function create-sources() {
    # echo Creating user for harvesting
    # paster --plugin=ckan user add harvest email=harvest@example.com password=$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c12) -c $1

    # echo Creating harvest sources
    # url=$LIB_URL

    name='spc-cces'
    title='Climate Change and Environmental Sustainability'
    org='spc-cces'
    config='{"set": "CCES_PDH", "topic": "Climate Change"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1
    fi

    name='spc-fame'
    title='Fisheries, Aquaculture & Marine Ecosystems'
    org='spc-fame'
    config='{"set": "FAME_PDH", "topic": "Fisheries"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1
    fi

    name='spc-gem'
    title='Geoscience, Energy and Maritime'
    org='spc-gem'
    config='{"set": "GEM_PDH", "topic": "Geoscience"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1
    fi

    name='spc-lrd'
    title='Land Resources Division'
    org='spc-lrd'
    config='{"set": "LRD_PDH", "topic": "Land Resources"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1
    fi

    name='spc-phd'
    title='Public Health Division'
    org='spc-phd'
    config='{"set": "PHD_PDH", "topic": "Health"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1
    fi

    name='spc-sdp'
    title='Social Development Program'
    org='spc-sdp'
    config='{"set": "SDP_PDH", "topic": "Social"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1
    fi

    name='spc-sdd'
    title='Statistics for Development Division'
    org='spc-sdd'
    config='{"set": "SDD_PDH", "topic": "Statistics"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" OAI-PMH "$title" true "$org" DAILY "$config" -c $1
    fi

    # GBIF
    url='http://api.gbif.org'
    name='spc-gbif'
    title='GBIF SPC published'
    org='spc-fame'
    config='{"topic": "Fisheries", "hosting_org": "cd3512e7-886c-4873-b629-740abe8ae74e", "q": "+spc"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" GBIF "$title" true "$org" DAILY "$config" -c $1
    fi

    name='sprep-gbif'
    title='GBIF SPREP published'
    org='sprep'
    config='{"topic": "Fisheries", "hosting_org": "cd3512e7-886c-4873-b629-740abe8ae74e", "q": "-spc"}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" GBIF "$title" true "$org" DAILY "$config" -c $1
    fi

    # SPREP
    url='https://pacific-data.sprep.org'
    name='sprep'
    title='Inform Regional Data Portal '
    org='sprep'
    config='{"topic_mapping": {"Atmosphere and Climate": "Climate Change", "Info": null, "Land": "Land Resources", "Biodiversity": "Fisheries", "Build Environment": "Economic Development", "Coastal and Marine": "Fisheries", "Culture and Heritage": "Social", "Inland Waters": "Geoscience"}}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" SPREP "$title" true "$org" DAILY "$config" -c $1
    fi

    # PacGeo
    url='http://www.pacgeo.org/catalogue/csw'
    name='pacgeo'
    title='PacGeo'
    org='spc-gem'
    config='{"keywords": ["maritimeboundaries", "boundaries-administrative"]}'
    if ! paster --plugin=ckanext-harvest harvester source "$name" -c $1 2>/dev/null; then
        paster --plugin=ckanext-harvest harvester source "$name" "$url" pacgeo "$title" true "$org" DAILY "$config" -c $1
    fi
}

LIB_URL=http://www.spc.int/DigitalLibrary/SPC/OAI

if [[ ! -f "$1" ]]; then
    echo You must specify path to existing config as first argument to this script
    exit 1
fi
CONFIG=$1
shift

if [ ! -d 'ckanext-spc' ]
then
    echo Switch to folder containing CKAN extensions
    exit
fi

read -p "Have you updated ckanext-spc source?(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo You need to do it manually
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
fi

select operation in install-deps clear-sources create-sources skip; do
    if [[ -n "$operation" ]]; then
        break
    fi
    echo "Incorrect choice"
done

$operation $CONFIG

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
