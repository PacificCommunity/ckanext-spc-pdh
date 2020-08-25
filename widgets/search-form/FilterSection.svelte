<script>
  import {createEventDispatcher} from 'svelte'
  import Icons from '../svg'
  import Select from './Select'

  import {advancedMode, filters} from './store'
  import {Filter } from './Filter'
  import InputText from './InputText'
  import InputDropdown from './InputDropdown'
  export let filter = new Filter()
  const dispatch = createEventDispatcher()
  const types = {
    text: InputText,
    dropdown: InputDropdown,
  }
</script>

<svelte:component this={types[Filter.getWidgetType(filter.type)] || InputText } filterType={filter.type} bind:value={filter.value}/>

<div class="filter-select--wrapper filter-type">
  <Select options={Filter.filterTypeOptions} bind:value={filter.type} on:change={() => filter.value = ''}/>
</div>
{#if $advancedMode}
  <div class="filter-select--wrapper filter-operator">
    <Select options={Filter.operatorOptions} bind:value={filter.operator}/>
  </div>
{/if}
{#if $advancedMode}
  <div class="remove-btn" on:click={() => filters.remove(filter)}>
    <Icons.Close/>
  </div>
{:else}
  <div class="search-btn" on:click={() => dispatch('search')}>
    <button class='unstyled-button' type="submit">
      <Icons.Search/>
    </button>
  </div>
{/if}

<input name="ext_advanced_value" type="hidden" value={filter.value||''}/>
<input name="ext_advanced_type" type="hidden" value={filter.type}/>
<input name="ext_advanced_operator" type="hidden" value={filter.operator}/>
