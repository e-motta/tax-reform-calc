import { $ } from "../utils/dom.js";
import { t } from "../i18n/index.js";
import { money, pct, points } from "../utils/format.js";
import { state } from "../state.js";

export function renderResult() {
  const text = t(state.lang);
  const result = state.result;
  const selected = result.years.find((year) => year.year === state.selected) || result.years.at(-1);
  state.selected = selected.year;
  const root = $("result");
  root.replaceChildren();

  const cards = document.createElement("div");
  cards.className = "cards";
  cards.append(card(text.today, result.baseline, false), card(String(selected.year), selected, true));
  root.append(cards);

  const delta = Number(selected.effective_rate) - Number(result.baseline.effective_rate);
  const sentence = document.createElement("p");
  sentence.className = "delta";
  const direction = delta > 0.00005 ? text.higher : delta < -0.00005 ? text.lower : text.same;
  sentence.textContent = Math.abs(delta) < 0.00005
    ? text.delta(selected.year, direction, points(0, state.lang)).replace(`${points(0, state.lang)} percentage points `, "").replace(`${points(0, state.lang)} pontos percentuais `, "")
    : text.delta(selected.year, direction, points(delta, state.lang));
  if (Math.abs(delta) < 0.00005) {
    sentence.textContent = state.lang === "pt"
      ? `Em ${selected.year}, a carga efetiva é a mesma de hoje.`
      : `In ${selected.year} the effective burden is the same as today.`;
  }
  root.append(sentence);

  const max = Math.max(
    ...[result.baseline, ...result.years].map((year) => Number(year.effective_rate)),
    0.01,
  );
  const timeline = document.createElement("div");
  timeline.className = "timeline";
  timeline.setAttribute("role", "group");
  timeline.setAttribute("aria-label", state.lang === "pt" ? "Anos da transição" : "Transition years");
  for (const year of result.years) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "year";
    button.setAttribute("aria-pressed", year.year === selected.year ? "true" : "false");
    const track = document.createElement("span");
    track.className = "track";
    const fill = document.createElement("span");
    fill.className = "fill";
    fill.style.height = `${Math.max(2, (Number(year.effective_rate) / max) * 100)}%`;
    track.append(fill);
    const meta = document.createElement("span");
    meta.className = "meta";
    const y = document.createElement("span");
    y.className = "y";
    y.textContent = String(year.year);
    const rate = document.createElement("span");
    rate.className = "pct";
    rate.textContent = pct(year.effective_rate, state.lang);
    meta.append(y, rate);
    button.append(track, meta);
    button.addEventListener("click", () => {
      state.selected = year.year;
      renderResult();
    });
    timeline.append(button);
  }
  root.append(timeline);
  root.append(tableFor(selected));

  const source = document.createElement("p");
  source.className = "source";
  source.textContent = state.lang === "pt" ? selected.source_pt : selected.source;
  root.append(source);

  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = text.how;
  const list = document.createElement("ul");
  for (const code of result.assumptions) {
    const item = document.createElement("li");
    item.textContent = text.assumptions[code] || code;
    list.append(item);
  }
  details.append(summary, list);
  root.append(details);
}

function card(kicker, year, selected) {
  const text = t(state.lang);
  const node = document.createElement("article");
  node.className = selected ? "card selected" : "card";
  const label = document.createElement("p");
  label.className = "kicker";
  label.textContent = kicker;
  const figure = document.createElement("p");
  figure.className = "figure";
  figure.textContent = pct(year.effective_rate, state.lang);
  const sub = document.createElement("p");
  sub.textContent = `${text.customer} ${money(year.customer_price)} · ${money(year.total_tax)} ${text.ofWhich}`;
  const nominal = document.createElement("p");
  nominal.textContent = `${text.nominal} ${pct(year.nominal_cbs_ibs_rate, state.lang)}`;
  node.append(label, figure, sub, nominal);
  return node;
}

function lineLabel(line) {
  const text = t(state.lang);
  const base = text.lines[line.code] || line.code;
  return line.detail ? `${base} (${line.detail})` : base;
}

function tableFor(year) {
  const text = t(state.lang);
  const wrap = document.createElement("div");
  wrap.className = "breakdown";
  const table = document.createElement("table");
  const head = document.createElement("thead");
  head.innerHTML = `<tr><th>${text.tax}</th><th class="num">${text.rate}</th><th class="num">${text.amount}</th></tr>`;
  const body = document.createElement("tbody");
  for (const line of year.lines) {
    const row = document.createElement("tr");
    const name = document.createElement("td");
    name.textContent = lineLabel(line);
    if (line.estimated) {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = text.estimate;
      name.append(tag);
    }
    const rate = document.createElement("td");
    rate.className = "num";
    rate.textContent = line.rate === null ? "—" : pct(line.rate, state.lang);
    const amount = document.createElement("td");
    amount.className = "num";
    amount.textContent = money(line.amount);
    row.append(name, rate, amount);
    body.append(row);
  }
  const total = document.createElement("tr");
  total.className = "total";
  total.innerHTML = `<td>${text.total}</td><td class="num">${pct(year.effective_rate, state.lang)}</td><td class="num">${money(year.total_tax)}</td>`;
  body.append(total);
  table.append(head, body);
  wrap.append(table);
  return wrap;
}
