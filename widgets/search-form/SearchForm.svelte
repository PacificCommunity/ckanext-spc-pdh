<script>
  // import PerfectScrollbar from 'perfect-scrollbar'
  import ModeSwitcher from './ModeSwitcher'
  import FilterSection from './FilterSection'
  import SolrInput from './SolrInput'
  import {advancedMode, solrMode, filters} from './store'

  $: if (!$advancedMode) filters.reset()

  const urlParams = new URLSearchParams(window.location.search);
  const extSolrQuery = urlParams.get('ext_solr_query', '');
  if (extSolrQuery) {
    $advancedMode = true;
    $solrMode = true;
  }

  const search = () => {
    const params = new URLSearchParams();

    $filters.forEach(filter => {
      params.append(`ext_advanced_type`, filter.type);
      params.append(`ext_advanced_operator`, filter.operator);
      params.append(`ext_advanced_value`, filter.value);
    })
    window.location.search = params.toString()
  }

</script>

<div class="advanced-filters">

  {#if !$solrMode}
    {#if $advancedMode}
      {#each $filters as filter }
        <div class="advanced-filter-row">
          <FilterSection {filter}/>
        </div>
      {/each}
        <div class="advanced-filter-row add-filter" on:click={() => filters.add()}>
          <span class="input-placeholder">Add search field</span>
        </div>
    {/if}
  {:else}
    <SolrInput query={extSolrQuery}/>
  {/if}
  <ModeSwitcher />
</div>
