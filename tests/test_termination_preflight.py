from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPOSITORY_ROOT / "workflows" / "strategy-forward-replication-research--v001"
CHECKER = (
    REPOSITORY_ROOT
    / ".agents"
    / "skills"
    / "build-strategy-study-to-freeze"
    / "scripts"
    / "check_authority_root.py"
)

if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from validator.canonical_yaml import canonical_bytes, canonical_digest  # noqa: E402
from validator.study import _expected_terminal_bindings, validate_study  # noqa: E402
from writer.service import StudyService  # noqa: E402

from research.tools.termination_preflight import run_preflight  # noqa: E402


def _temporary_study(tmp_path: Path) -> tuple[Path, Path, StudyService, str]:
    root = tmp_path / "repo"
    workflow = root / "workflows" / "strategy-forward-replication-research--v001"
    shutil.copytree(WORKFLOW_ROOT, workflow)
    checker = root / ".agents" / "skills" / "build-strategy-study-to-freeze" / "scripts"
    checker.mkdir(parents=True)
    shutil.copyfile(CHECKER, checker / "check_authority_root.py")
    authority = root / ".authority"
    authority.mkdir()
    (authority / "README.md").write_text("repository-local authority\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)

    study_id = "termination-preflight-v001"
    service = StudyService(
        workflow,
        authority,
        repository_root=root,
        allow_draft=True,
    )
    service.create_study(
        study_id,
        "owner",
        research_round_id="round-1",
        experiment_family="family-1",
        research_owner="owner",
        historical_evaluation_operator="owner",
        source_bundle={
            "schema_version": 1,
            "files": [
                {
                    "path": "runner.py",
                    "digest": hashlib.sha256(b"runner\n").hexdigest(),
                }
            ],
        },
    )
    return root, authority, service, study_id


def _write_payload(path: Path, value: dict[str, object]) -> None:
    path.write_bytes(canonical_bytes(value))


def test_termination_preflight_checks_canonical_path_and_authority(tmp_path: Path) -> None:
    root, authority, _, study_id = _temporary_study(tmp_path)
    payload = root / "payloads" / "evidence-unavailable.yml"
    payload.parent.mkdir()
    _write_payload(
        payload,
        {
            "stage": "development",
            "unavailable_path": "evidence/missing-development.yml",
            "reason": "synthetic setup evidence is unavailable",
        },
    )

    passed = run_preflight(
        root,
        study_id,
        "evidence-unavailable",
        payload,
        authority,
    )

    assert passed["status"] == "passed"
    assert passed["details"]["authority_preflight"]["status"] == "passed"
    assert passed["details"]["unavailable_path"]["exists"] is False
    assert passed["details"]["writer_handoff"]["atomic"] is False

    missing_path = (
        root
        / "workflows"
        / "strategy-forward-replication-research--v001"
        / "studies"
        / study_id
        / "evidence"
        / "missing-development.yml"
    )
    missing_path.parent.mkdir()
    missing_path.write_bytes(b"reserved\n")
    occupied = run_preflight(
        root,
        study_id,
        "evidence-unavailable",
        payload,
        authority,
    )
    assert occupied["status"] == "failed"
    assert any(item["code"] == "unavailable-path-exists" for item in occupied["errors"])

    noncanonical = root / "payloads" / "noncanonical.yml"
    noncanonical.write_text(
        "stage: development\nunavailable_path: evidence/other.yml\nreason: bad\n",
        encoding="utf-8",
    )
    rejected = run_preflight(
        root,
        study_id,
        "evidence-unavailable",
        noncanonical,
        authority,
    )
    assert any(item["code"] == "non-canonical-payload" for item in rejected["errors"])

    wrong_authority = run_preflight(
        root,
        study_id,
        "evidence-unavailable",
        payload,
        tmp_path / "different-authority",
    )
    assert any(
        item["code"] == "authority-root-must-be-repository-local"
        for item in wrong_authority["errors"]
    )


def test_termination_preflight_checks_terminal_evidence_digest_and_bindings(
    tmp_path: Path,
) -> None:
    root, authority, service, study_id = _temporary_study(tmp_path)
    study_root = service.study_root(study_id)
    unavailable_payload = {
        "stage": "development",
        "unavailable_path": "evidence/missing.yml",
        "reason": "development evidence cannot be produced",
    }
    service.append_event(study_id, "evidence-unavailable", "owner", unavailable_payload)
    projection = validate_study(study_root, service.rules)
    terminal = {
        "schema_version": 1,
        "outcome": "indeterminate",
        "authority": "none",
        "recomputed": True,
        "bindings": _expected_terminal_bindings(projection),
        "reasons": ["development evidence cannot be produced"],
    }
    evidence_path, evidence_digest = service.publish_artifact(
        study_id,
        "evidence/terminal-evidence.yml",
        terminal,
    )
    payload = root / "payloads" / "study-terminal.yml"
    payload.parent.mkdir()
    _write_payload(
        payload,
        {
            "outcome": "indeterminate",
            "authority": "none",
            "terminal_evidence_path": evidence_path,
            "terminal_evidence_digest": evidence_digest,
        },
    )

    result = run_preflight(root, study_id, "study-terminal", payload, authority)

    assert result["status"] == "passed"
    assert result["details"]["terminal_evidence"]["expected_digest"] == evidence_digest
    assert result["details"]["terminal_evidence"]["actual_digest"] == canonical_digest(terminal)

    tampered_payload = root / "payloads" / "tampered-terminal.yml"
    _write_payload(
        tampered_payload,
        {
            "outcome": "indeterminate",
            "authority": "none",
            "terminal_evidence_path": evidence_path,
            "terminal_evidence_digest": "0" * 64,
        },
    )
    tampered = run_preflight(
        root,
        study_id,
        "study-terminal",
        tampered_payload,
        authority,
    )
    assert any(
        item["code"] == "terminal-evidence-digest-mismatch"
        for item in tampered["errors"]
    )
