"""v005 reference-first Study 與低重複 runtime 的契約測試。"""

from pathlib import Path

import pytest
from operations.lifecycle import development
from operations.preflight import synthetic_csv
from repair_helpers import prepared_service
from test_operations import write
from validator.canonical_yaml import canonical_digest, load_canonical
from validator.errors import IntegrityError
from validator.study import validate_study


def test_study_reference_is_immutable_and_runtime_has_no_workflow_copy(tmp_path: Path):
    service, study_id, research, _ = prepared_service(tmp_path, eligible=True)
    contract = load_canonical(research / "runner-contract.yml")
    inputs = load_canonical(research / "development-trial-inputs.yml")
    data = synthetic_csv(contract["cases"][0])
    data_path = research / "development.csv"
    data_path.write_bytes(data)
    plan = {
        "actor": "fixture-owner",
        "trial_inputs": inputs,
        "data_path": f"research/{study_id}/development.csv",
        "data_digest": canonical_digest(data),
    }

    result = development(service, study_id, plan)

    study_root = service.study_root(study_id)
    reference_path = study_root / "manifests/workflow-reference.yml"
    reference = load_canonical(reference_path)
    assert reference == service.workflow_reference
    assert canonical_digest(reference_path.read_bytes()) == service.workflow_reference_digest
    state = validate_study(study_root, service.rules)
    assert state.bindings["workflow_reference_path"] == "manifests/workflow-reference.yml"
    assert state.bindings["workflow_reference_digest"] == service.workflow_reference_digest

    operation = study_root / "operations" / result["operation_id"]
    runtime_manifest = load_canonical(operation / "runtime/runtime-manifest.yml")
    assert runtime_manifest["execution_workspace"] == "temporary"
    assert runtime_manifest["workflow_reference"]["digest"] == service.workflow_reference_digest
    assert runtime_manifest["source_bundle"]["path"] == "manifests/source-bundle.yml"
    assert not (operation / "runtime/workflow").exists()
    assert not any(path.name == "bars.csv" for path in operation.rglob("*"))
    assert not any(path.name == "source-bundle.yml" for path in operation.rglob("*"))


def test_reference_drift_is_rejected_before_development_can_read_data(tmp_path: Path):
    service, study_id, _, _ = prepared_service(tmp_path, eligible=True)
    workflow_path = service.workflow_root / "workflow.yml"
    workflow = load_canonical(workflow_path)
    workflow["title"] = "被竄改的測試 Workflow"
    write(workflow_path, workflow)

    with pytest.raises(IntegrityError, match="digest"):
        validate_study(service.study_root(study_id), service.rules)
