import "regenerator-runtime/runtime.js";

// import "simplebar";
// import "simplebar/dist/simplebar.css";

import "perfect-scrollbar/css/perfect-scrollbar.css";

import "./search-form/style.less";
import { filters, facets$ } from "./search-form/store";
import SearchForm from "./search-form/SearchForm";

SearchForm.filters = filters;
SearchForm.facets$ = facets$;

window.SPCWidgets = {
  SearchForm,
};
