import { $ } from "../utils/dom.js";
import { t } from "../i18n/index.js";
import { state } from "../state.js";

export function renderIntro() {
  const text = t(state.lang);
  $("intro").textContent = text.intro;
}
