###############################################################################
#                             requirements: start                             #
###############################################################################
ckan_tag = ckan-2.9.0
ext_list = c3charts cesiumpreview ddi discovery drupal_menu_sync ga-report \
	geoview harvest hierarchy hierarchy_search metaexport metatags \
	oaipmh pdfview spatial xloader zippreview

remote-c3charts = https://github.com/DataShades/ckanext-c3charts.git branch py3
remote-cesiumpreview = https://github.com/DataShades/ckanext-cesiumpreview.git branch py3
remote-ddi = https://github.com/DataShades/ckanext-ddi.git branch py3
remote-discovery = https://github.com/DataShades/ckanext-discovery.git branch py3
remote-drupal_menu_sync = https://github.com/DataShades/ckanext-drupal_menu_sync.git branch d9
remote-ga-report = https://github.com/DataShades/ckanext-ga-report.git branch py3
remote-geoview = https://github.com/DataShades/ckanext-geoview.git branch py3
remote-harvest = https://github.com/DataShades/ckanext-harvest.git branch fix_clearsource_history_command
remote-hierarchy = https://github.com/DataShades/ckanext-hierarchy.git branch py3
remote-hierarchy_search = https://github.com/DataShades/ckanext-hierarchy_search.git branch master
remote-metaexport = https://github.com/DataShades/ckanext-metaexport.git branch py3
remote-metatags = https://github.com/DataShades/ckanext-metatags.git branch master
remote-oaipmh = https://github.com/DataShades/ckanext-oaipmh.git branch py3
remote-spatial = https://github.com/DataShades/ckanext-spatial.git branch py3
remote-zippreview = https://github.com/DataShades/ckanext-zippreview.git branch py3
remote-pdfview = https://github.com/ckan/ckanext-pdfview.git branch master
remote-xloader = https://github.com/ckan/ckanext-xloader.git branch master

###############################################################################
#                              requirements: end                              #
###############################################################################
_version = master

-include deps.mk

prepare:
	curl -O https://raw.githubusercontent.com/DataShades/ckan-deps-installer/$(_version)/deps.mk
