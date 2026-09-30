"""runner envelope 的唯一消費與不可覆寫發布路徑。"""

from pathlib import Path

from validator.artifacts import validate_development_trial, verified_artifact
from validator.canonical_yaml import canonical_digest
from validator.errors import IntegrityError, ValidationError
from validator.schema_validation import SchemaStore


def validate_envelope(value, inputs, prereg, source_digest):
    SchemaStore(Path(__file__).resolve().parents[1] / "schemas").validate(
        "development-envelope.schema.yml", value
    )
    if not isinstance(value, dict) or set(value) != {"candidate", "baseline"}:
        raise ValidationError("Development 輸出必須同時包含 candidate 與 baseline")
    results = {}
    for name in ("candidate", "baseline"):
        model_id = (
            inputs["candidate_id"]
            if name == "candidate"
            else prereg["baseline_definition"]["baseline_id"]
        )
        failures = validate_development_trial(
            value[name],
            dict(inputs, candidate_id=model_id),
            prereg,
            trial_id=model_id,
            trial_inputs_digest=canonical_digest(inputs),
            preregistration_digest=canonical_digest(prereg),
            source_bundle_digest=source_digest,
        )
        results[name] = {"trades": len(value[name]["trades"]), "failed_gates": failures}
    return results


def consume(service, study_id, envelope, inputs, prereg, source_digest):
    validate_envelope(envelope, inputs, prereg, source_digest)
    trial_id = inputs["candidate_id"]
    if "/" in trial_id or ".." in trial_id:
        raise ValidationError("不安全的 trial_id")
    prefix = f"evidence/trials/{trial_id}"
    refs = {}
    for name, value in {
        "candidate": envelope["candidate"],
        "baseline": envelope["baseline"],
        "inputs": inputs,
    }.items():
        path, digest = service.publish_artifact(study_id, f"{prefix}/{name}.yml", value)
        refs[name] = {"path": path, "digest": digest}
    manifest = {
        "schema_version": 1,
        "study_id": study_id,
        "trial_id": trial_id,
        "source_bundle_digest": source_digest,
        "preregistration_digest": canonical_digest(prereg),
        "envelope_digest": canonical_digest(envelope),
        "artifacts": refs,
    }
    assets = inputs.get("data_bindings", {}).get("assets")
    if assets is not None:
        manifest["data_assets_digest"] = canonical_digest(assets)
    path, digest = service.publish_artifact(study_id, f"{prefix}/publication.yml", manifest)
    return {
        "trial_id": trial_id,
        "status": "completed",
        "inputs_path": refs["inputs"]["path"],
        "inputs_digest": refs["inputs"]["digest"],
        "development_evidence_path": refs["candidate"]["path"],
        "development_evidence_digest": refs["candidate"]["digest"],
        "publication_path": path,
        "publication_digest": digest,
    }


def validate_publication(root, rules, payload, projection):
    if not {"publication_path", "publication_digest"}.issubset(payload):
        raise ValidationError("Trial 缺少 candidate／baseline publication manifest")
    _, manifest = verified_artifact(
        root, payload["publication_path"], payload["publication_digest"]
    )
    rules.schema_store.validate("development-publication.schema.yml", manifest)
    if (
        manifest["study_id"] != projection.study_id
        or manifest["trial_id"] != payload["trial_id"]
        or manifest["source_bundle_digest"] != projection.bindings["source_bundle_digest"]
        or manifest["preregistration_digest"] != projection.preregistration_digest
    ):
        raise IntegrityError("Publication manifest 綁定不一致")
    values = {}
    for name, ref in manifest["artifacts"].items():
        _, values[name] = verified_artifact(root, ref["path"], ref["digest"])
    for name, path_key, digest_key in (
        ("candidate", "development_evidence_path", "development_evidence_digest"),
        ("inputs", "inputs_path", "inputs_digest"),
    ):
        if manifest["artifacts"][name] != {
            "path": payload[path_key],
            "digest": payload[digest_key],
        }:
            raise IntegrityError("Trial 與 publication artifact 不一致")
    envelope = {name: values[name] for name in ("candidate", "baseline")}
    assets = values["inputs"].get("data_bindings", {}).get("assets")
    expected_assets_digest = canonical_digest(assets) if assets is not None else None
    if manifest.get("data_assets_digest") != expected_assets_digest:
        raise IntegrityError("Publication 多資產資料綁定不一致")
    if canonical_digest(envelope) != manifest["envelope_digest"]:
        raise IntegrityError("Runner envelope digest 不一致")
    validate_envelope(
        envelope,
        values["inputs"],
        projection.preregistration,
        projection.bindings["source_bundle_digest"],
    )
