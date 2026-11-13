export async function fetchRules() {
  const response = await fetch("/api/rules");
  if (!response.ok) throw new Error("rules");
  return response.json();
}

export async function calculate(params) {
  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(params),
  });
  const body = await response.json();
  return { ok: response.ok, body };
}
