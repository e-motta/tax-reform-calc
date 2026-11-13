"""Seam for a future batch recalculation. Not wired to a queue in v1.

The tax function in ``calculate`` has no database and no I/O. When a batch
feature is needed, an OCI Queue worker (not Kafka) should pull a message of
the shape below and call ``apply``. Publishing, consuming, and storing the
result are intentionally left out: there is no queue client in this version.
"""

from pydantic import BaseModel

from app.engine.rules import RuleSet
from app.schemas import CalculationRequest, CalculationResult

from .calculate import calculate


class RecalculationCommand(BaseModel):
    """One OCI Queue message. ``schema_version`` is here so a later worker can
    reject a payload it does not understand instead of guessing."""

    schema_version: int = 1
    request: CalculationRequest
    rules_version: str | None = None


class RulesVersionMismatch(Exception):
    def __init__(self, requested: str, loaded: str) -> None:
        self.requested = requested
        self.loaded = loaded
        super().__init__(f"requested {requested}, loaded {loaded}")


def apply(command: RecalculationCommand, rules: RuleSet) -> CalculationResult:
    if command.schema_version != 1:
        raise ValueError(f"unsupported command schema {command.schema_version}")
    if command.rules_version is not None and command.rules_version != rules.version:
        raise RulesVersionMismatch(command.rules_version, rules.version)
    return calculate(command.request, rules)
