import { locale } from "../i18n/index.js";

export function money(value) {
  const formatted = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
  return `R$\u00a0${formatted}`;
}

export function pct(value, lang, digits = 2) {
  if (value === null || value === undefined) return "—";
  return `${new Intl.NumberFormat(locale(lang), {
    minimumFractionDigits: digits,
    maximumFractionDigits: 3,
  }).format(Number(value) * 100)}%`;
}

export function points(delta, lang) {
  return new Intl.NumberFormat(locale(lang), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(delta) * 100);
}

export function rulesAsOf(iso, lang) {
  const [year, month, day] = iso.split("-").map(Number);
  if (lang === "pt") {
    const dd = String(day).padStart(2, "0");
    const mm = String(month).padStart(2, "0");
    return `${dd}/${mm}/${year}`;
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(year, month - 1, day));
}
