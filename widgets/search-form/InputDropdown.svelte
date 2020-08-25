<script>
  import PerfectScrollbar from 'perfect-scrollbar';
  import {onMount, afterUpdate, tick} from 'svelte'
  import Icons from '../svg'
  import {Filter} from './Filter'
  import { facets$ } from './store'
  export let value = ''

  export let filterType = 'any';

  let open = false
  let dropdownOptionsEl = undefined

  const scrollDropdown = async () => {
    await tick()
    dropdownOptionsEl.scrollTop = 0
  }
  let ps = undefined

  onMount(() => {
    ps = new PerfectScrollbar(dropdownOptionsEl, {
      suppressScrollX: true
    })
    return () => ps.destroy()
  })
  $: if (open) {
    scrollDropdown()
  }

  $: placeholder = Filter.getPlaceholder(filterType)
</script>

<div class="filter-input-dropdown" tabIndex=-1 class:open
     on:blur={() => open=false}
  >
  <div class="dropdown-handle" on:click={() => open = !open}>
    {placeholder}
    <span class="blue-stroke">
      <Icons.Chevron fill={null}/>
    </span>
  </div>
  <div class="dropdown-options--wrapper" on:mouseleave={() => open=false}>
    <ul bind:this={dropdownOptionsEl} class="dropdown-options">
      {#await $facets$}
      <li class="empty">
        Loading...
      </li>
      {:then facets}
      {#each facets[filterType].items as option}
        <li class="option-item" class:active={option.name === value} on:click={() => value = option.name}>
          {option.display_name}
        </li>
      {:else}
      <li class="empty">
        No options available
      </li>
    {/each}
  {/await}
</ul>
  </div>
  {#await $facets$ then facets}
  {#if value}
    <div class="dropdown-value">
      {(facets[filterType].items.find(option => option.name == value)||{}).display_name}
      <span class="remove-icon" on:click={() => value = undefined}>
        <Icons.Close fill={null}/>
      </span>
    </div>
  {/if}
  {/await}
</div>
