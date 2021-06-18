<script>
  import { createEventDispatcher } from 'svelte'
  import {advancedMode, solrMode} from './store'
  import Icons from '../svg'

  function checkMode() {
    if ($advancedMode) {
      $solrMode = false;
    }
  }

  const dispatch = createEventDispatcher()
</script>

<div class="advanced-form-control">
  <div class="enable-advanced-search">
    <input id="enable-advance-search-checkbox" type="checkbox" on:change={checkMode} bind:checked={$advancedMode}/>
    <label for="enable-advance-search-checkbox">
      Advanced search
    </label>
  </div>
  {#if $advancedMode}
    <div class="enable-advanced-search">
        <input id="toggle-enable-solr" type="checkbox" bind:checked={$solrMode} />
        <label for="toggle-enable-solr">Add query syntax to search</label>
        <div class="data-quality-tooltip">
          <i class="info-icon"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="8" cy="8" r="8" fill="#001E73"/><rect x="7" y="2" width="2" height="2" fill="white"/><rect x="6" y="6" width="1" height="2" fill="white"/><rect x="6" y="12" width="4" height="2" fill="white"/><rect x="7" y="6" width="2" height="6" fill="white"/></svg></i>
          <span class="tooltiptext tooltiptext-above data-quality-tooltip-inner info-tooltip">Search using SOLR query language. For more information, click  <a href="https://docs.pacificdata.org/catalogue/advanced-search/solr-search" target="_blank">here</a></span>
        </div>
    </div>
    <button type=submit class="btn search-btn {$solrMode ? 'hdn' : ''}" on:click={() => dispatch('search')}>
      <Icons.Search fill="#ffffff"/>
      Search
    </button>
  {/if}
</div>
