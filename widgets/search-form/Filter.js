let filterTypeOptions = [
  { value: "any", label: "Any attribute" },
  { value: "title", label: "Title" },
  { value: "type", label: "Dataset type", type: "dropdown" },
  { value: "topic", label: "Topic", type: "dropdown" },
  { value: "member_countries", label: "Country", type: "dropdown" },
  { value: "res_format", label: "Format", type: "dropdown" },
  { value: "organization", label: "Organisation", type: "dropdown" },
];
const operatorOptions = [
  { value: "or", label: "Or" },
  { value: "and", label: "And" },
];

const searchKeys = window.location.search
  .slice(1)
  .split("&")
  .map((val) => val.split("=")[0]);

filterTypeOptions = filterTypeOptions.filter(
  ({ value }) => !~searchKeys.indexOf(value)
);

export class Filter {
  static get filterTypeOptions() {
    return filterTypeOptions;
  }
  static get operatorOptions() {
    return operatorOptions;
  }

  static getWidgetType(filterType) {
    switch (filterType) {
      case "type":
      case "topic":
      case "member_countries":
      case "res_format":
      case "organization":
        return "dropdown";
      default:
        return "text";
    }
  }
  static getPlaceholder(filterType) {
    switch (filterType) {
      case "any":
        return "Search datasets...";
      case "title":
        return "Enter any title";
      case "type":
        return "Choose Dataset type";
      case "topic":
        return "Choose Topic";
      case "member_countries":
        return "Choose Country";
      case "res_format":
        return "Choose Format";
      case "organization":
        return "Choose Organisation";

      default:
        return "";
    }
  }
  constructor(initial = { operator: "or", type: "any", value: "" }) {
    Object.assign(this, initial);
  }
}
