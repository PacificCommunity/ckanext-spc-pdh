import "regenerator-runtime/runtime.js";
import "perfect-scrollbar/css/perfect-scrollbar.css";

import "./search-form/style.less";
import { filters, facets$, advancedMode } from "./search-form/store";
import SearchForm from "./search-form/SearchForm";

SearchForm.filters = filters;
SearchForm.facets$ = facets$;
SearchForm.advancedMode = advancedMode;

window.SPCWidgets = {
  SearchForm,
};
