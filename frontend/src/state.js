export const state = {
  lang: localStorage.getItem("iva-lang") || "en",
  theme: localStorage.getItem("iva-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"),
  catalogue: null,
  result: null,
  selected: 2033,
};
