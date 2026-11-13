"""HTTP contract: health, the rules catalogue, calculation, and the Simples refusal."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_the_rules_version():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rules_version"] == "2026-11-13"
    assert body["rules_as_of"] == "2026-11-13"


def test_rules_catalogue_is_bilingual_and_marks_simples():
    response = client.get("/api/rules")
    assert response.status_code == 200
    body = response.json()
    assert body["estimates"]["tcu_used_in_calculation"] is False
    assert body["estimates"]["cbs_reference"] == "0.0921"
    categories = {item["id"]: item for item in body["categories"]}
    assert categories["standard_goods"]["name_en"]
    assert categories["standard_goods"]["name_pt"]
    assert len(body["states"]) == 27
    regimes = {item["id"]: item for item in body["regimes"]}
    assert regimes["lucro_real"]["supported"] is True
    assert regimes["simples"]["supported"] is False


def test_calculate_returns_the_transition(rules_payload=None):
    response = client.post(
        "/api/calculate",
        json={
            "category_id": "standard_goods",
            "origin_uf": "sp",
            "destination_uf": "SP",
            "regime": "lucro_real",
            "price": "1000",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["origin_uf"] == "SP"
    assert [year["year"] for year in body["years"]] == list(range(2026, 2034))
    assert body["baseline"]["kind"] == "baseline"
    assert body["years"][-1]["customer_price"] == "1279.10"


def test_simples_is_a_structured_rejection():
    response = client.post(
        "/api/calculate",
        json={
            "category_id": "general_services",
            "origin_uf": "SP",
            "destination_uf": "RJ",
            "regime": "simples",
            "price": "250.50",
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "regime_not_supported"
    assert "Simples" in detail["message_en"]
    assert "Simples" in detail["message_pt"]


def test_openapi_is_exposed():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert "/api/calculate" in spec["paths"]
    assert "/api/rules" in spec["paths"]


def test_ui_is_served_from_the_same_origin():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "IVA" in response.text


def test_custom_iss_rate_minimum():
    """Custom ISS rate of 2% (the minimum) should work for services."""
    response = client.post(
        "/api/calculate",
        json={
            "category_id": "general_services",
            "origin_uf": "SP",
            "destination_uf": "SP",
            "regime": "lucro_real",
            "price": "1000",
            "iss_rate": "0.02",
        },
    )
    assert response.status_code == 200
    body = response.json()
    baseline_iss = next(
        line for line in body["baseline"]["lines"] if line["code"] == "iss"
    )
    assert baseline_iss["rate"] == "0.02"
    assert "iss_custom" in body["assumptions"]
    assert "iss_scenario" not in body["assumptions"]


def test_custom_iss_rate_mid_range():
    """Custom ISS rate of 3.5% should work for services."""
    response = client.post(
        "/api/calculate",
        json={
            "category_id": "general_services",
            "origin_uf": "SP",
            "destination_uf": "SP",
            "regime": "lucro_real",
            "price": "1000",
            "iss_rate": "0.035",
        },
    )
    assert response.status_code == 200
    body = response.json()
    baseline_iss = next(
        line for line in body["baseline"]["lines"] if line["code"] == "iss"
    )
    assert baseline_iss["rate"] == "0.035"


def test_iss_rate_below_minimum_rejected():
    """ISS rate below 2% should be rejected with 422."""
    response = client.post(
        "/api/calculate",
        json={
            "category_id": "general_services",
            "origin_uf": "SP",
            "destination_uf": "SP",
            "regime": "lucro_real",
            "price": "1000",
            "iss_rate": "0.01",
        },
    )
    assert response.status_code == 422


def test_iss_rate_above_maximum_rejected():
    """ISS rate above 5% should be rejected with 422."""
    response = client.post(
        "/api/calculate",
        json={
            "category_id": "general_services",
            "origin_uf": "SP",
            "destination_uf": "SP",
            "regime": "lucro_real",
            "price": "1000",
            "iss_rate": "0.06",
        },
    )
    assert response.status_code == 422


def test_default_iss_rate_unchanged():
    """When no iss_rate is provided, the default 5% scenario rate is used."""
    response = client.post(
        "/api/calculate",
        json={
            "category_id": "general_services",
            "origin_uf": "SP",
            "destination_uf": "SP",
            "regime": "lucro_real",
            "price": "1000",
        },
    )
    assert response.status_code == 200
    body = response.json()
    baseline_iss = next(
        line for line in body["baseline"]["lines"] if line["code"] == "iss"
    )
    assert baseline_iss["rate"] == "0.05"
    assert "iss_scenario" in body["assumptions"]
    assert "iss_custom" not in body["assumptions"]


def test_iss_rate_ignored_for_goods():
    """ISS rate should be ignored for goods categories."""
    response = client.post(
        "/api/calculate",
        json={
            "category_id": "standard_goods",
            "origin_uf": "SP",
            "destination_uf": "SP",
            "regime": "lucro_real",
            "price": "1000",
            "iss_rate": "0.03",
        },
    )
    assert response.status_code == 200
    body = response.json()
    iss_lines = [line for line in body["baseline"]["lines"] if line["code"] == "iss"]
    assert len(iss_lines) == 0
    assert "iss_scenario" not in body["assumptions"]
    assert "iss_custom" not in body["assumptions"]
