from __future__ import annotations

from validator.canonical_yaml import load_canonical
from validator.schema_validation import SchemaStore


def test_policy_values_and_safety(workflow_root) -> None:
    schema_store = SchemaStore(workflow_root / "schemas")
    market = load_canonical(workflow_root / "policies/us-equity-market--v002/policy.yml")
    execution = load_canonical(workflow_root / "policies/canonical-execution--v001/policy.yml")
    risk = load_canonical(workflow_root / "policies/portfolio-risk--v001/policy.yml")
    proposals = load_canonical(workflow_root / "policies/paper-proposal-orders--v001/policy.yml")
    for policy in (market, execution, risk, proposals):
        schema_store.validate("policy.schema.yml", policy)

    assert market["values"]["formal_run_provider_access_allowed"] is False
    assert market["values"]["primary_calendar"] == "XNYS"
    assert execution["values"]["intrabar_ambiguity"] == "adverse_stop_first"
    assert execution["values"]["stress_cost_bps"]["entry_slippage"] == "20"
    assert risk["values"]["pyramiding"] is False
    assert proposals["values"]["allowed_order_types"] == ["MARKET", "LIMIT", "STOP_MARKET"]
    assert proposals["values"]["broker_order_creation_allowed"] is False
