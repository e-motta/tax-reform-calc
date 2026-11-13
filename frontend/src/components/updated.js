import { $ } from "../utils/dom.js";
import { rulesAsOf } from "../utils/format.js";
import { state } from "../state.js";

export function renderUpdated() {
  const node = $("asof");
  const iso = state.catalogue.as_of;
  node.hidden = false;
  node.textContent = state.lang === "pt"
    ? `Regras atualizadas em ${rulesAsOf(iso, state.lang)}`
    : `Rules updated ${rulesAsOf(iso, state.lang)}`;
}
