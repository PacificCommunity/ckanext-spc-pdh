import { writable } from "svelte/store";
import { Filter } from "./Filter";

export const solrMode = writable(false);

const makeAdvancedStore = () => {
  const { set, update, subscribe } = writable(false);

  const store = {
    subscribe,
    update,
    set,
    current: false,
  };

  subscribe(value => store.current = value);
  return store;
};

const makeFilters = (initial) => {
  const { set, update, subscribe } = writable(initial);

  return {
    subscribe,
    init: (items) => {
      advancedMode.set(true);
      set(items.map((item) => new Filter(item)));
    },
    reset: () => update((filters) => filters.slice(0, 1)),
    add: () => update((filters) => [...filters, new Filter()]),
    remove: (filter) =>
      update((filters) => {
        if (filters.length == 1) { return filters }
        let updated = filters.filter((f) => f !== filter);
        return updated.length ? updated : [new Filter()];
      }),
  };
};
export const filters = makeFilters([new Filter()]);
export const advancedMode = makeAdvancedStore();
export const facets$ = writable(new Promise(() => { }));
