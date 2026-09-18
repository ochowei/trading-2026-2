from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))


@pytest.fixture
def workflow_root(tmp_path: Path) -> Path:
    destination = tmp_path / "workflow"
    shutil.copytree(
        WORKFLOW_ROOT,
        destination,
        ignore=shutil.ignore_patterns(
            "studies", "__pycache__", "*.pyc", "release-manifest.yml", "release-test-report.yml"
        ),
    )
    from validator.canonical_yaml import canonical_bytes, canonical_digest
    from validator.release import build_release_manifest

    manifest = build_release_manifest(destination)
    report = {
        "schema_version": 1,
        "workflow": "strategy-forward-replication-research",
        "workflow_version": "v002",
        "generated_at": "2000-01-01T00:00:00.000000Z",
        "status": "release-candidate",
        "release_record_created": False,
        "checks": [{"command": "isolated fixture", "result": "passed", "summary": "僅測試用"}],
    }
    (destination / "release-manifest.yml").write_bytes(canonical_bytes(manifest))
    (destination / "release-test-report.yml").write_bytes(canonical_bytes(report))
    release = {
        "schema_version": 1,
        "workflow": report["workflow"],
        "workflow_version": "v002",
        "approved_at": report["generated_at"],
        "approved_by": "fixture-only",
        "workflow_digest": manifest["workflow_digest"],
        "release_manifest_digest": canonical_digest(manifest),
        "test_report_path": "release-test-report.yml",
        "test_report_digest": canonical_digest(report),
    }
    (destination / "release.yml").write_bytes(canonical_bytes(release))
    return destination


@pytest.fixture(autouse=True)
def legacy_transition_fixture(request, monkeypatch):
    """舊 transition 單元案例使用明示合成佐證；入口整合測試完全不套用。"""
    if request.node.path.name in {"test_operations.py", "test_repairs.py"}:
        return
    from copy import deepcopy

    from helpers import development_inputs, preregistration
    from validator.canonical_yaml import canonical_digest, load_canonical
    from validator.study import validate_study
    from writer.service import StudyService

    original_create, original_append = StudyService.create_study, StudyService.append_event
    # 只隔離耗時 runner 的 freshness；歷史佐證／核准／evidence 仍走真正 validator。
    monkeypatch.setattr(StudyService, "_verify_prepared", lambda *args: None)

    def create(self, study_id, actor_id, **kwargs):
        bundle = kwargs["source_bundle"]
        record = {
            "schema_version": 1,
            "status": "passed",
            "prepare_checks": "passed",
            "binding": {
                "study_id": study_id,
                "repository": str(self.repository_root),
                "authority_root": str(self.authority.root),
                "settings": {
                    "preregistration.yml": canonical_digest(preregistration()),
                    "candidate-definition.yml": "b" * 64,
                    "qualification-spec.yml": "c" * 64,
                    "development-trial-inputs.yml": canonical_digest(
                        development_inputs(
                            canonical_digest(preregistration()), canonical_digest(bundle)
                        )
                    ),
                },
                "source_bundle": bundle,
                "environment": {"fixture": True},
                "workflow_digest": self.workflow_digest,
            },
            "cases": [
                {
                    "case": i,
                    "stage": stage,
                    "expect": expect,
                    "data_digest": "a" * 64,
                    "request_digest": "b" * 64,
                    "evidence_digest": "c" * 64,
                    "validation": {"fixture": True},
                }
                for i, (stage, expect) in enumerate(
                    (
                        ("development", "trades"),
                        ("development", "no-trades"),
                        ("historical-evaluation", "trades"),
                        ("historical-evaluation", "no-trades"),
                    )
                )
            ],
        }
        kwargs.setdefault("prepare_report", record)
        return original_create(self, study_id, actor_id, **kwargs)

    def append(self, study_id, kind, actor, payload, **kwargs):
        if kind in {"preregistration-approved", "development-authorized", "trial-recorded"}:
            projection = validate_study(
                self.study_root(study_id), self.rules, check_projection=False
            )
            if kind != "trial-recorded":
                prereg_digest = payload.get(
                    "preregistration_digest", projection.preregistration_digest
                )
                proof = {
                    "decision": "approved",
                    "actor_id": actor,
                    "role": "trusted-approver",
                    "approved_at": "2000-01-01T00:00:00Z",
                    "basis": "隔離 transition fixture",
                    "scope": "preregistration"
                    if kind == "preregistration-approved"
                    else "development-only",
                    "bindings": {
                        "study_id": study_id,
                        "workflow_version": "v002",
                        "source_bundle_digest": projection.bindings["source_bundle_digest"],
                        "preregistration_digest": prereg_digest,
                    },
                }
                path, digest = self.publish_artifact(
                    study_id, f"evidence/fixture-{kind}.yml", proof
                )
                prefix = "approval" if kind == "preregistration-approved" else "evidence"
                payload.update({f"{prefix}_path": path, f"{prefix}_digest": digest})
            elif "development_evidence_path" in payload:
                evidence = load_canonical(
                    self.study_root(study_id) / payload["development_evidence_path"]
                )
                baseline = deepcopy(evidence)
                baseline["candidate_id"] = projection.preregistration["baseline_definition"][
                    "baseline_id"
                ]
                bp, bd = self.publish_artifact(study_id, "evidence/fixture-baseline.yml", baseline)
                manifest = {
                    "schema_version": 1,
                    "study_id": study_id,
                    "trial_id": payload["trial_id"],
                    "source_bundle_digest": projection.bindings["source_bundle_digest"],
                    "preregistration_digest": projection.preregistration_digest,
                    "envelope_digest": canonical_digest(
                        {"candidate": evidence, "baseline": baseline}
                    ),
                    "artifacts": {
                        "candidate": {
                            "path": payload["development_evidence_path"],
                            "digest": payload["development_evidence_digest"],
                        },
                        "baseline": {"path": bp, "digest": bd},
                        "inputs": {
                            "path": payload["inputs_path"],
                            "digest": payload["inputs_digest"],
                        },
                    },
                }
                pp, pd = self.publish_artifact(
                    study_id, "evidence/fixture-publication.yml", manifest
                )
                payload.update(publication_path=pp, publication_digest=pd)
                # registry 原始測試使用原 payload；將新增必要引用同步至 caller。
        return original_append(self, study_id, kind, actor, payload, **kwargs)

    monkeypatch.setattr(StudyService, "create_study", create)
    monkeypatch.setattr(StudyService, "append_event", append)
