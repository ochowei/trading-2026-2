"""兩個 v002 補充技能的隔離讀取與證據驗證反例。"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPOSITORY = Path(__file__).resolve().parents[1]
PACKAGE = REPOSITORY / "workflows/strategy-forward-replication-research--v002"
SKILLS = ["blind-review-strategy-study-v002", "study-development-note-authoring-v002"]


@pytest.fixture
def repository(tmp_path):
    repo = tmp_path / "repo"
    package = repo / "workflows" / PACKAGE.name
    shutil.copytree(PACKAGE, package, ignore=shutil.ignore_patterns("studies", "__pycache__"))
    program = r"""
import sys
from pathlib import Path
from copy import deepcopy
package=Path(sys.argv[1]); sys.path[:0]=[str(package),str(package/'tests')]
from helpers import preregistration,development_inputs,development_evidence
from validator.canonical_yaml import canonical_bytes,canonical_digest
study=package/'studies/review-fixture'
def write(relative,value):
    path=study/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(canonical_bytes(value))
prereg=preregistration()
bundle={'schema_version':1,'files':[{'path':'src/fixture.py','digest':'a'*64}]}
inputs=development_inputs(canonical_digest(prereg),canonical_digest(bundle))
candidate=development_evidence(canonical_digest(prereg),canonical_digest(bundle),canonical_digest(inputs))
baseline=deepcopy(candidate);baseline['candidate_id']=prereg['baseline_definition']['baseline_id']
write('manifests/preregistration.yml',prereg);write('manifests/source-bundle.yml',bundle)
artifacts={}
for kind,value in {'candidate':candidate,'baseline':baseline,'inputs':inputs}.items():
    path=f'evidence/trials/trial-1/{kind}.yml';write(path,value);artifacts[kind]={'path':path,'digest':canonical_digest(value)}
write('evidence/trials/trial-1/publication.yml',{'schema_version':1,'study_id':'review-fixture','trial_id':'trial-1','source_bundle_digest':canonical_digest(bundle),'preregistration_digest':canonical_digest(prereg),'envelope_digest':canonical_digest({'candidate':candidate,'baseline':baseline}),'artifacts':artifacts})
"""
    subprocess.run([sys.executable, "-c", program, str(package)], check=True, capture_output=True)
    study = package / "studies/review-fixture"
    for relative in (
        "study.yml",
        "events/result.yml",
        "journals/result.yml",
        "operations/result.yml",
    ):
        path = study / relative
        path.parent.mkdir(exist_ok=True)
        path.write_text("不得讀取的合成 sentinel")
    (repo / "historical-evaluation-artifacts").mkdir()
    (repo / "historical-evaluation-artifacts/result.yml").write_text("不得讀取的合成 sentinel")
    return repo


def run(skill, repo, reference="review-fixture", *flags):
    script = REPOSITORY / ".agents/skills" / skill / "scripts/check_development.py"
    # 即使 helper 捕捉例外，也不能掩蓋曾嘗試讀正式结果區的行為。
    guard = r"""
import os,sys,runpy
from pathlib import Path
script,repo=sys.argv[1:3];sys.argv=[script,*sys.argv[3:]]
violations=[]
def audit(event,args):
    if event=='open' and not isinstance(args[0],int):
        path=Path(os.fsdecode(args[0]))
        if any(part in path.parts for part in ('historical-evaluation-artifacts','events','journals','operations')) and str(path).startswith(repo) and '/studies/' in str(path) or str(path).startswith(repo+'/historical-evaluation-artifacts') or path.name=='study.yml':
            violations.append(str(path));raise AssertionError('forbidden read')
sys.addaudithook(audit)
try:runpy.run_path(script,run_name='__main__')
except SystemExit:
    if violations:sys.exit(99)
    raise
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            guard,
            str(script),
            str(repo),
            reference,
            "--repository-root",
            str(repo),
            "--role",
            "study 開發者",
            *flags,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 99, result.stdout + result.stderr
    return result.returncode, json.loads(result.stdout)


@pytest.mark.parametrize("skill", SKILLS)
def test_valid_artifacts_without_reading_events_or_formal_results(repository, skill):
    code, result = run(skill, repository)
    assert code == 0
    assert result["development_evidence_validity"] == "valid"
    assert result["trials"]["trial-1"]["assessment"]["candidate_freeze_eligibility"]["eligible"]
    assert result["candidate_freeze_status"] == "尚不能判斷"
    assert result["full_chain_validated"] is False


@pytest.mark.parametrize("skill", SKILLS)
@pytest.mark.parametrize(
    "fault", ["missing-candidate", "missing-baseline", "tampered", "redirect", "symlink"]
)
def test_missing_or_unsafe_evidence_limits_analysis_without_rejecting_review(
    repository, skill, fault
):
    trial = (
        repository / "workflows" / PACKAGE.name / "studies/review-fixture/evidence/trials/trial-1"
    )
    if fault.startswith("missing-"):
        (trial / f"{fault.removeprefix('missing-')}.yml").unlink()
    elif fault == "symlink":
        (trial / "candidate.yml").unlink()
        (trial / "candidate.yml").symlink_to(
            repository / "historical-evaluation-artifacts/result.yml"
        )
    elif fault == "tampered":
        path = trial / "candidate.yml"
        path.write_text(path.read_text().replace("candidate_id: trial-1", "candidate_id: wrong"))
    else:
        path = trial / "publication.yml"
        value = yaml.safe_load(path.read_text())
        value["artifacts"]["candidate"]["path"] = "historical-evaluation-artifacts/result.yml"
        path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=True, indent=2))
    code, result = run(skill, repository)
    assert code == 0
    assert result["blind_review_status"] == "eligible-with-development-evidence-unavailable"
    assert "assessment" not in result["trials"]["trial-1"]
    if fault == "redirect":
        assert "白名單" in result["trials"]["trial-1"]["reason"]
    elif fault == "symlink":
        assert "symlink" in result["trials"]["trial-1"]["reason"]
    elif fault == "tampered":
        assert "digest" in result["trials"]["trial-1"]["reason"]


@pytest.mark.parametrize("skill", SKILLS)
def test_exposure_rejected_before_access_even_when_repository_missing(tmp_path, skill):
    code, result = run(skill, tmp_path / "missing", "review-fixture", "--outcome-exposed")
    assert code == 2
    assert result["blind_review_status"] == "blocked-by-exposed-outcome"
    assert result["read_files"] == []


@pytest.mark.parametrize("skill", SKILLS)
@pytest.mark.parametrize(
    "reference",
    [
        "research/review-fixture",
        "workflows/strategy-forward-replication-research--v001/studies/review-fixture",
        "../elsewhere",
        "workflows/strategy-forward-replication-research--v002/studies/review-fixture/study.yml",
    ],
)
def test_wrong_scope_is_rejected(repository, skill, reference):
    code, result = run(skill, repository, reference)
    assert code == 2
    assert result["read_files"] == []
