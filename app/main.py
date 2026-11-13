"""FastAPI application. The UI and the API share this origin."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.engine.loader import load_rules

OPENAPI_DESCRIPTION = """
Compare today's Brazilian consumption taxes with the dual VAT introduced by
EC 132/2023 and regulated by Complementary Law 214/2025.

The calculator covers ICMS, PIS, COFINS and, where a ruleset sets a rate, IPI,
against CBS, IBS and the selective tax, for each year from 2026 to 2033.
Rates live in versioned YAML under `rules/`, with a citation and an as-of
date. CBS and IBS reference rates are estimates and are labelled as such.

This is one taxable supply, with no input credit. It is a comparison of the
tax debited on the operation, not a filing tool.
"""


def create_app() -> FastAPI:
    rules = load_rules()
    app = FastAPI(
        title="IVA transition",
        summary="Brazil's consumption taxes against the dual VAT, year by year.",
        description=OPENAPI_DESCRIPTION,
        version=rules.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.state.rules = rules
    app.include_router(router)

    static_dir = Path.cwd() / "frontend"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="ui")
    return app


app = create_app()
