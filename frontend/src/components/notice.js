import { $ } from "../utils/dom.js";
import { pct } from "../utils/format.js";
import { state } from "../state.js";

export function renderNotice() {
  const estimates = state.catalogue.estimates;
  const cbs = pct(estimates.cbs_reference, state.lang);
  const ibs = pct(estimates.ibs_reference, state.lang);
  const combined = pct(estimates.combined_reference, state.lang);
  const tcu = pct(estimates.tcu_cbs_reference, state.lang);
  const cap = pct(estimates.statutory_review_cap, state.lang);
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
      `As alíquotas de referência da CBS e do IBS ainda são estimativas. Esta simulação usa CBS de ${cbs} e IBS de ${ibs}, totalizando ${combined} (`,
    );
    notice.append(link);
    notice.append("). Em 28 de outubro de 2026, o ");
    notice.append(tcuLink);
    notice.append(
      ` calculou a CBS em ${tcu}, mas, como o Senado ainda não fixou a alíquota, esse percentual não foi incorporado ao cálculo. O teto de ${cap} previsto para a revisão das alíquotas também não corresponde à alíquota aplicada.`,
    );
  } else {
    notice.append(
      `The CBS and IBS reference rates are still estimates. This simulation uses a CBS rate of ${cbs} and an IBS rate of ${ibs}, totaling ${combined} (`,
    );
    notice.append(link);
    notice.append("). On 28 October 2026, the ");
    notice.append(tcuLink);
    notice.append(
      ` calculated the CBS rate at ${tcu}, but the Senate has not set the rate, so that figure is not included in the calculation. The ${cap} cap provided for the rate review is not the rate applied here either.`,
    );
  }
}
