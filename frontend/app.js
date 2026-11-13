const copy = {
  en: {
    eyebrow: "Brazil · EC 132/2023 · LC 214/2025",
    pageTitle: "ICMS, PIS, COFINS → IVA",
    skip: "Skip to the result",
    lang: "Language",
    themeLight: "Dark",
    themeDark: "Light",
    category: "Category",
    origin: "Origin",
    destination: "Destination",
    regime: "Tax regime",
    price: "Net price",
    priceHint: "What the supplier keeps before consumption taxes, in reais.",
    submit: "Compare",
    waiting: "Set a supply and compare.",
    today: "Today",
    customer: "Customer pays",
    nominal: "Nominal CBS + IBS",
    effective: "Effective on the price paid",
    ofWhich: "of which is tax",
    higher: "higher than today",
    lower: "lower than today",
    same: "the same burden as today",
    delta: (year, direction, points) =>
      `In ${year} the effective rate is ${points} percentage points ${direction}.`,
    tax: "Tax",
    rate: "Rate",
    amount: "Amount",
    total: "Total tax",
    estimate: "estimate",
    how: "How this number was built",
    docs: "OpenAPI",
    footer: "A comparison, not a filing. Rules are versioned YAML with a citation on each figure.",
    regimes: {
      lucro_real: "Lucro Real",
      lucro_presumido: "Lucro Presumido",
      simples: "Simples Nacional — not in this version",
    },
    lines: {
      icms: "ICMS",
      icms_interstate: "ICMS, interstate share",
      icms_difal: "ICMS, destination share (DIFAL)",
      fcp: "State surcharge",
      iss: "ISS",
      pis: "PIS",
      cofins: "COFINS",
      ipi: "IPI",
      cbs: "CBS",
      ibs: "IBS",
      ibs_state: "IBS, state",
      ibs_municipal: "IBS, municipal",
      selective: "Selective tax",
      offset_2026: "2026 offset against PIS/COFINS",
    },
    assumptions: {
      price_is_net: "The price is the supplier's net, before consumption taxes. Inside taxes are grossed up; CBS, IBS and the selective tax are added on top.",
      final_consumer: "The buyer is a final consumer. An interstate sale of goods therefore bears the destination state's modal ICMS: the interstate rate stays with the origin, and the difference is the DIFAL.",
      no_input_credits: "This is the tax debited on a single supply. It does not net off credits on purchases, under either the old non-cumulative PIS/COFINS or the new VAT.",
      domestic_goods: "Goods are treated as domestic. The 4% interstate rate for imported goods is not applied.",
      reference_rates_are_estimates: "From 2027 the CBS rate, and from 2029 the IBS rate, use the reference-rate estimate. The 2026 rates and the 2027–2028 IBS rates are the statutory test rates.",
      tcu_rate_not_used: "The TCU's CBS reference is disclosed and is not the rate used in the arithmetic.",
      ibs_phase_in_is_a_projection: "The IBS slices of 10%, 20%, 30% and 40% are the statute's revenue-replacement fractions, applied to one estimated full rate. The Senate fixes each year's real reference rate only in the year before.",
      ipi_not_by_ncm: "No IPI rate is applied. TIPI rates depend on an NCM code, and these categories are not NCM codes.",
      ipi_zfm_not_modelled: "IPI ends in 2027 except for goods that compete with the Manaus Free Zone. That residue is not modelled.",
      modal_icms: "ICMS is the state's modal internal rate, not the rate of a product, fuel or utility.",
      fcp_only_when_general: "The state poverty-fund surcharge is added only where it belongs to the general rule: Rio de Janeiro and Sergipe.",
      icms_excluded: "ICMS is excluded from the PIS/COFINS base, following STF Topic 69 (RE 574.706).",
      iss_scenario: "ISS is a 5% scenario rate, the top of the 2% to 5% municipal band. It is not the rate of a named city.",
      iss_excluded: "ISS is excluded from the PIS/COFINS base, following STF Topic 118 (RE 592.616), judged on 21 October 2026.",
      iss_modulation_open: "The Supreme Court had not modulated the effects of that ISS judgment when these rules were written. PIS and COFINS themselves end in 2027.",
      states_do_not_change_services: "For a service, the two states do not change the figure. ISS here is the scenario rate, not a municipal table.",
      basic_basket_keeps_modal_icms: "The national basic basket is zero-rated for CBS and IBS. State ICMS reductions on food are product-specific and are not applied, so today's column still uses the modal rate.",
      selective_holding_after_2027: "Provisional Measure 1.399/2026 fixes selective-tax rates for calendar year 2027. Later years keep that rate as a holding assumption. The statute still requires a further escalation, from 2029 to 2033, for drinks and tobacco, and that escalation has no number yet.",
      vehicle_adjustments_not_applied: "The car rate is the 6.3% base times the 1.21 conversion factor, before the sustainability adjustments, which depend on the vehicle.",
    },
  },
  pt: {
    eyebrow: "Brasil · EC 132/2023 · LC 214/2025",
    pageTitle: "ICMS, PIS, COFINS → IVA",
    skip: "Ir para o resultado",
    lang: "Idioma",
    themeLight: "Escuro",
    themeDark: "Claro",
    category: "Categoria",
    origin: "Origem",
    destination: "Destino",
    regime: "Regime tributário",
    price: "Valor líquido",
    priceHint: "O que fica com o fornecedor, antes dos tributos sobre o consumo.",
    submit: "Comparar",
    waiting: "Informe a operação e compare.",
    today: "Hoje",
    customer: "O adquirente paga",
    nominal: "Alíquota nominal de CBS + IBS",
    effective: "Carga efetiva sobre o preço pago",
    ofWhich: "em tributos",
    higher: "acima da de hoje",
    lower: "abaixo da de hoje",
    same: "igual à de hoje",
    delta: (year, direction, points) =>
      `Em ${year}, a carga efetiva fica ${points} pontos percentuais ${direction}.`,
    tax: "Tributo",
    rate: "Alíquota",
    amount: "Valor",
    total: "Total dos tributos",
    estimate: "estimativa",
    how: "Como o número foi calculado",
    docs: "OpenAPI",
    footer: "Comparação, não apuração. As regras estão em YAML versionado, com a fonte de cada número.",
    regimes: {
      lucro_real: "Lucro Real",
      lucro_presumido: "Lucro Presumido",
      simples: "Simples Nacional — fora desta versão",
    },
    lines: {
      icms: "ICMS",
      icms_interstate: "ICMS interestadual",
      icms_difal: "DIFAL",
      fcp: "FCP",
      iss: "ISS",
      pis: "PIS",
      cofins: "COFINS",
      ipi: "IPI",
      cbs: "CBS",
      ibs: "IBS",
      ibs_state: "IBS estadual",
      ibs_municipal: "IBS municipal",
      selective: "Imposto Seletivo",
      offset_2026: "Compensação de 2026 com PIS/COFINS",
    },
    assumptions: {
      price_is_net: "O valor informado é o que fica com o fornecedor, antes dos tributos sobre o consumo. ICMS, ISS, PIS e COFINS são calculados por dentro; CBS, IBS e Imposto Seletivo, por fora.",
      final_consumer: "O adquirente é consumidor final. Na venda interestadual de mercadoria, o ICMS é o da alíquota interna do destino: a interestadual fica na origem e a diferença é o DIFAL.",
      no_input_credits: "É o débito de uma única operação. Não se aproveitam créditos das entradas, nem no PIS/COFINS não cumulativo nem na CBS e no IBS.",
      domestic_goods: "A mercadoria é tratada como nacional. A alíquota interestadual de 4% dos produtos importados não se aplica.",
      reference_rates_are_estimates: "De 2027 em diante, a CBS usa a estimativa de alíquota de referência; o IBS, a partir de 2029. Em 2026, e no IBS de 2027 e 2028, valem as alíquotas de teste da lei.",
      tcu_rate_not_used: "A alíquota de referência da CBS calculada pelo TCU aparece na nota e não entra no cálculo.",
      ibs_phase_in_is_a_projection: "Os 10%, 20%, 30% e 40% do IBS são as frações da transição previstas na lei, aplicadas sobre uma única alíquota cheia estimada. O Senado só fixa a referência de cada ano no ano anterior.",
      ipi_not_by_ncm: "Não há IPI nesta conta. A alíquota da TIPI depende do NCM, e estas categorias não são códigos NCM.",
      ipi_zfm_not_modelled: "O IPI se extingue em 2027, exceto para os bens que concorrem com a Zona Franca de Manaus. Esse resíduo não entra nesta versão.",
      modal_icms: "O ICMS usado é a alíquota interna geral do Estado, não a de um produto, de combustível ou de energia.",
      fcp_only_when_general: "O adicional do fundo de combate à pobreza entra só onde integra a regra geral: Rio de Janeiro e Sergipe.",
      icms_excluded: "O ICMS é excluído da base de cálculo do PIS e da COFINS, conforme o Tema 69 do STF (RE 574.706).",
      iss_scenario: "O ISS entra como premissa de 5%, o teto da faixa municipal de 2% a 5%. Não é a alíquota de um município específico.",
      iss_excluded: "O ISS é excluído da base de cálculo do PIS e da COFINS, conforme o Tema 118 do STF (RE 592.616), julgado em 21 de outubro de 2026.",
      iss_modulation_open: "Na data desta versão, o STF ainda não havia modulado os efeitos desse julgamento. O PIS e a COFINS se extinguem em 2027.",
      states_do_not_change_services: "Em serviço, a UF de origem e a de destino não mudam o resultado. O ISS aqui é a premissa de 5%, não a tabela de um município.",
      basic_basket_keeps_modal_icms: "A cesta básica nacional tem alíquota zero de CBS e de IBS. Redução de ICMS sobre alimentos depende do produto e não entra nesta versão, então a coluna de hoje segue a alíquota interna geral.",
      selective_holding_after_2027: "A MP nº 1.399/2026 fixa o Imposto Seletivo para o ano-calendário de 2027. Os anos seguintes mantêm essa alíquota. O escalonamento de 2029 a 2033, para bebidas e tabaco, ainda não tem número publicado.",
      vehicle_adjustments_not_applied: "A alíquota do automóvel é a base de 6,3% multiplicada pelo fator 1,21, antes dos ajustes de sustentabilidade, que dependem de cada veículo.",
    },
  },
};

const state = {
  lang: localStorage.getItem("iva-lang") || "en",
  theme: localStorage.getItem("iva-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"),
  catalogue: null,
  result: null,
  selected: 2033,
};

const $ = (id) => document.getElementById(id);

function t() {
  return copy[state.lang];
}

function locale() {
  return state.lang === "pt" ? "pt-BR" : "en-GB";
}

function money(value) {
  const formatted = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
  return `R$\u00a0${formatted}`;
}

function pct(value, digits = 2) {
  if (value === null || value === undefined) return "—";
  return `${new Intl.NumberFormat(locale(), {
    minimumFractionDigits: digits,
    maximumFractionDigits: 3,
  }).format(Number(value) * 100)}%`;
}

function points(delta) {
  return new Intl.NumberFormat(locale(), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(delta) * 100);
}

function formatDate(iso) {
  const [year, month, day] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat(locale(), { day: "numeric", month: "long", year: "numeric" }).format(
    new Date(year, month - 1, day),
  );
}

function applyChrome() {
  const text = t();
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
  $("docs-link").textContent = text.docs;
  $("footer-copy").textContent = text.footer;
  $("theme").textContent = state.theme === "dark" ? text.themeDark : text.themeLight;
  $("theme").setAttribute("aria-pressed", state.theme === "dark" ? "true" : "false");
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
        render();
      });
      return button;
    }),
  );
  if (state.catalogue) fillSelects();
  if (state.catalogue) renderNotice();
  if (state.result) renderResult();
}

function fillSelects() {
  const text = t();
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

function renderNotice() {
  const estimates = state.catalogue.estimates;
  const asOf = formatDate(estimates.as_of);
  const cbs = pct(estimates.cbs_reference);
  const ibs = pct(estimates.ibs_reference);
  const combined = pct(estimates.combined_reference);
  const tcu = pct(estimates.tcu_cbs_reference);
  const cap = pct(estimates.statutory_review_cap);
  const link = document.createElement("a");
  link.href = estimates.source_url;
  link.textContent = state.lang === "pt" ? "fonte" : "source";
  const tcuLink = document.createElement("a");
  tcuLink.href = estimates.tcu_source_url;
  tcuLink.textContent = "TCU";
  const notice = $("notice");
  notice.replaceChildren();
  if (state.lang === "pt") {
    notice.append(
      `As alíquotas de referência da CBS e do IBS são estimativas. Nesta versão, de ${asOf}: CBS ${cbs} e IBS ${ibs}, somadas ${combined}. `,
    );
    notice.append(link);
    notice.append(". O ");
    notice.append(tcuLink);
    notice.append(
      ` calculou ${tcu} de CBS em 28 de outubro de 2026. O Senado ainda não a havia fixado, e esse percentual não entra no cálculo. O teto de revisão de ${cap} também não é a alíquota adotada.`,
    );
  } else {
    notice.append(
      `CBS and IBS reference rates are estimates, as of ${asOf} in this ruleset: CBS ${cbs} and IBS ${ibs}, combined ${combined}. `,
    );
    notice.append(link);
    notice.append(". The ");
    notice.append(tcuLink);
    notice.append(` calculated a CBS reference of ${tcu} on 28 October 2026. The Senate had not fixed it, and that figure is not used in the arithmetic. The statutory review cap of ${cap} is not the rate either.`);
  }
}

function lineLabel(line) {
  const text = t();
  const base = text.lines[line.code] || line.code;
  return line.detail ? `${base} (${line.detail})` : base;
}

function renderResult() {
  const text = t();
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
    ? text.delta(selected.year, direction, points(0)).replace(`${points(0)} percentage points `, "").replace(`${points(0)} pontos percentuais `, "")
    : text.delta(selected.year, direction, points(delta));
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
    rate.textContent = pct(year.effective_rate);
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
  const text = t();
  const node = document.createElement("article");
  node.className = selected ? "card selected" : "card";
  const label = document.createElement("p");
  label.className = "kicker";
  label.textContent = kicker;
  const figure = document.createElement("p");
  figure.className = "figure";
  figure.textContent = pct(year.effective_rate);
  const sub = document.createElement("p");
  sub.textContent = `${text.customer} ${money(year.customer_price)} · ${money(year.total_tax)} ${text.ofWhich}`;
  const nominal = document.createElement("p");
  nominal.textContent = `${text.nominal} ${pct(year.nominal_cbs_ibs_rate)}`;
  node.append(label, figure, sub, nominal);
  return node;
}

function tableFor(year) {
  const text = t();
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
    rate.textContent = line.rate === null ? "—" : pct(line.rate);
    const amount = document.createElement("td");
    amount.className = "num";
    amount.textContent = money(line.amount);
    row.append(name, rate, amount);
    body.append(row);
  }
  const total = document.createElement("tr");
  total.className = "total";
  total.innerHTML = `<td>${text.total}</td><td class="num">${pct(year.effective_rate)}</td><td class="num">${money(year.total_tax)}</td>`;
  body.append(total);
  table.append(head, body);
  wrap.append(table);
  return wrap;
}

async function loadCatalogue() {
  const response = await fetch("/api/rules");
  if (!response.ok) throw new Error("rules");
  state.catalogue = await response.json();
  const firstLoad = !$("origin").options.length;
  fillSelects();
  if (firstLoad) {
    $("origin").value = "SP";
    $("destination").value = "SP";
    $("regime").value = "lucro_real";
    $("category").value = "standard_goods";
  }
  renderNotice();
}

async function submit(event) {
  event?.preventDefault();
  const error = $("form-error");
  error.hidden = true;
  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      category_id: $("category").value,
      origin_uf: $("origin").value,
      destination_uf: $("destination").value,
      regime: $("regime").value,
      price: $("price").value,
    }),
  });
  const body = await response.json();
  if (!response.ok) {
    const detail = body.detail;
    const message = detail && detail[state.lang === "pt" ? "message_pt" : "message_en"];
    error.hidden = false;
    error.textContent = message || (state.lang === "pt" ? "Não foi possível calcular." : "The comparison could not be calculated.");
    return;
  }
  state.result = body;
  renderResult();
}

function render() {
  applyChrome();
}

$("theme").addEventListener("click", () => {
  state.theme = state.theme === "dark" ? "light" : "dark";
  localStorage.setItem("iva-theme", state.theme);
  applyChrome();
});

$("category").addEventListener("change", () => {
  if (!state.catalogue) return;
  const summary = state.lang === "pt" ? "summary_pt" : "summary_en";
  const current = state.catalogue.categories.find((item) => item.id === $("category").value);
  $("category-hint").textContent = current ? current[summary] : "";
});

$("calc").addEventListener("submit", submit);

applyChrome();
loadCatalogue()
  .then(() => submit())
  .catch(() => {
    $("waiting").textContent = state.lang === "pt"
      ? "Não foi possível carregar as regras."
      : "The rules did not load.";
  });
