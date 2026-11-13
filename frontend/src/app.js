import { $ } from "./utils/dom.js";
import { t } from "./i18n/index.js";
import { state } from "./state.js";
import { fetchRules, calculate } from "./api/client.js";
import { applyChrome, initThemeToggle } from "./components/chrome.js";
import { fillSelects, setDefaultValues, initCategoryHint, getFormValues, showFormError, hideFormError } from "./components/form.js";
import { renderNotice } from "./components/notice.js";
import { renderUpdated } from "./components/updated.js";
import { renderResult } from "./components/results.js";

function render() {
  applyChrome(render);
  if (state.catalogue) fillSelects();
  if (state.catalogue) renderUpdated();
  if (state.catalogue) renderNotice();
  if (state.result) renderResult();
}

async function loadCatalogue() {
  state.catalogue = await fetchRules();
  const firstLoad = !$("origin").options.length;
  fillSelects();
  if (firstLoad) {
    setDefaultValues();
  }
  renderUpdated();
  renderNotice();
}

async function submit(event) {
  event?.preventDefault();
  hideFormError();
  const { ok, body } = await calculate(getFormValues());
  if (!ok) {
    const detail = body.detail;
    const message = detail && detail[state.lang === "pt" ? "message_pt" : "message_en"];
    const fallback = state.lang === "pt" ? "Não foi possível calcular." : "The comparison could not be calculated.";
    showFormError(message || fallback);
    return;
  }
  state.result = body;
  renderResult();
}

initThemeToggle(render);
initCategoryHint();
$("calc").addEventListener("submit", submit);

render();
loadCatalogue()
  .then(() => submit())
  .catch(() => {
    $("waiting").textContent = state.lang === "pt"
      ? "Não foi possível carregar as regras."
      : "The rules did not load.";
  });
