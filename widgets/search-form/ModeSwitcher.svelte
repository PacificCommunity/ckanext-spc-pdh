<script>
  import { createEventDispatcher } from 'svelte'
  import {advancedMode} from './store'
  import Icons from '../svg'
  const dispatch = createEventDispatcher()
</script>

<div class="advanced-form-control">
  <div class="enable-advanced-search">
    <input id="enable-advance-search-checkbox" type="checkbox" bind:checked={$advancedMode}/>
    <label for="enable-advance-search-checkbox">
      Advanced search
    </label>
  </div>
  {#if $advancedMode}
    <button type=submit class="btn search-btn" on:click={() => dispatch('search')}>
      <Icons.Search fill="#ffffff"/>
      Search
    </button>
  {/if}
</div>
