<script>
  import {createEventDispatcher} from 'svelte'
  import Icons from '../svg'
  const dispatch = createEventDispatcher()

  export let options = []
  export let value = undefined
  let open = false
  const setValue = (v) => {
    if(value === v) { return; }
    open=false;
    value = v;
    dispatch('change', {value: v})
  }
  $: alter = options.length && value !== options[0].value
</script>


<div class="filter-select" tabIndex=-1 class:open
     on:click|capture={() => open=true}
  on:blur={() => open=false}
  class:alter>
  {#each options as option, idx}
    <div class="filter-select--option" on:click={() => setValue(option.value)}
      class:selected={value===option.value} >
      <span class="option-label">{option.label}</span>
      <span class="caret-icon">
        <Icons.Chevron fill={null}/>
      </span>
    </div>
  {/each}
</div>
