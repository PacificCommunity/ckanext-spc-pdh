<script>
  import {Filter} from './Filter'
  export let value = ""
  export let filterType = 'any';

  $: placeholder = Filter.getPlaceholder(filterType)
</script>

<input class="filter-input-text" type="text" {placeholder} bind:value/>
