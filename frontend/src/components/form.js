import { $ } from "../utils/dom.js";
import { t } from "../i18n/index.js";
import { state } from "../state.js";

export function fillSelects() {
  const text = t(state.lang);
  const name = state.lang === "pt" ? "name_pt" : "name_en";
  const summary = state.lang === "pt" ? "summary_pt" : "summary_en";
  keepSelect($("category"), state.catalogue.categories.map((item) => ({
    value: item.id,
    label: item[name],
  })));
  const states = state.catalogue.states.map((item) => ({
    value: item.uf,
    label: `${item.uf} — ${item[name]}`,
  }));
  keepSelect($("origin"), states);
  keepSelect($("destination"), states);
  keepSelect($("regime"), state.catalogue.regimes.map((item) => ({
    value: item.id,
    label: text.regimes[item.id] || item.id,
  })));
  const current = state.catalogue.categories.find((item) => item.id === $("category").value);
  $("category-hint").textContent = current ? current[summary] : "";
}

function keepSelect(select, options) {
  const previous = select.value;
  select.replaceChildren(
    ...options.map((option) => {
      const node = document.createElement("option");
      node.value = option.value;
      node.textContent = option.label;
      return node;
    }),
  );
  if (options.some((option) => option.value === previous)) select.value = previous;
}

export function setDefaultValues() {
  $("origin").value = "SP";
  $("destination").value = "SP";
  $("regime").value = "lucro_real";
  $("category").value = "standard_goods";
}

export function initCategoryHint() {
  $("category").addEventListener("change", () => {
    if (!state.catalogue) return;
    const summary = state.lang === "pt" ? "summary_pt" : "summary_en";
    const current = state.catalogue.categories.find((item) => item.id === $("category").value);
    $("category-hint").textContent = current ? current[summary] : "";
  });
}

export function getFormValues() {
  return {
    category_id: $("category").value,
    origin_uf: $("origin").value,
    destination_uf: $("destination").value,
    regime: $("regime").value,
    price: $("price").value,
  };
}

export function showFormError(message) {
  const error = $("form-error");
  error.hidden = false;
  error.textContent = message;
}

export function hideFormError() {
  $("form-error").hidden = true;
}
