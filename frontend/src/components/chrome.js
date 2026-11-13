import { $ } from "../utils/dom.js";
import { t } from "../i18n/index.js";
import { state } from "../state.js";

export function applyChrome(onRender) {
  const text = t(state.lang);
  document.documentElement.lang = state.lang === "pt" ? "pt-BR" : "en";
  document.documentElement.dataset.theme = state.theme;
  document.title = text.pageTitle;
  $("skip").textContent = text.skip;
  $("eyebrow").textContent = text.eyebrow;
  $("label-category").textContent = text.category;
  $("label-origin").textContent = text.origin;
  $("label-destination").textContent = text.destination;
  $("label-regime").textContent = text.regime;
  $("label-price").textContent = text.price;
  $("price-hint").textContent = text.priceHint;
  $("submit").textContent = text.submit;
  const waiting = $("waiting");
  if (waiting) waiting.textContent = state.result ? "" : text.waiting;
  $("theme").textContent = state.theme === "dark" ? text.themeDark : text.themeLight;
  $("theme").setAttribute("aria-pressed", state.theme === "dark" ? "true" : "false");
  renderLangSwitch(onRender);
}

function renderLangSwitch(onRender) {
  const text = t(state.lang);
  $("lang-switch").setAttribute("aria-label", text.lang);
  $("lang-switch").replaceChildren(
    ...["en", "pt"].map((code) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = code.toUpperCase();
      button.setAttribute("aria-pressed", state.lang === code ? "true" : "false");
      button.addEventListener("click", () => {
        state.lang = code;
        localStorage.setItem("iva-lang", code);
        onRender();
      });
      return button;
    }),
  );
}

export function initThemeToggle(onRender) {
  $("theme").addEventListener("click", () => {
    state.theme = state.theme === "dark" ? "light" : "dark";
    localStorage.setItem("iva-theme", state.theme);
    onRender();
  });
}
