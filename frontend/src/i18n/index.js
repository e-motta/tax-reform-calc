import { en } from "./en.js";
import { pt } from "./pt.js";

const copy = { en, pt };

export function t(lang) {
  return copy[lang];
}

export function locale(lang) {
  return lang === "pt" ? "pt-BR" : "en-GB";
}
