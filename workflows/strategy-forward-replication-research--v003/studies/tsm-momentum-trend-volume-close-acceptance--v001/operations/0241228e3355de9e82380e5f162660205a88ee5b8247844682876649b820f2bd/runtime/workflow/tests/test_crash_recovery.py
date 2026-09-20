"""子程序 os._exit 硬中斷及並行；測試不攔截或降低正式驗證。"""

import os
import subprocess
import sys

import pytest
from operations.evaluation import historical_evaluation
from operations.service import create
from test_assignment_lifecycle import evaluation_fixture
from test_operations import (
    assignment_for,
    fixture_repository,
    make_service,
    passed_report,
    plan_for,
    write,
)
from validator.canonical_yaml import load_canonical
from validator.errors import WorkflowError


def process(package, code, *args):
    env = dict(os.environ, PYTHONPATH=str(package))
    return subprocess.run(
        [sys.executable, "-c", code, *map(str, args)], capture_output=True, text=True, env=env
    )


@pytest.mark.parametrize(
    "boundary",
    [
        "reservation",
        "started",
        "authority-marker",
        "marker",
        "output",
        "partial-output",
        "missing-output",
        "deleted-local-marker",
        "completed",
        "terminal",
        "started-event",
        "started-checkpoint",
        "completed-event",
        "completed-checkpoint",
        "terminal-event",
        "terminal-checkpoint",
    ],
)
def test_evaluation_hard_crash_resumes_without_second_launch(tmp_path, boundary):
    _, service, study_id, plan = evaluation_fixture(tmp_path)
    write(tmp_path / "plan.yml", plan)
    write(tmp_path / "assignment.yml", service.assignment)
    code = r"""
import os, sys
from pathlib import Path
import operations.evaluation as operation
from validator.canonical_yaml import load_canonical
from writer.service import StudyService
package, repo, authority, study, temp, boundary = sys.argv[1:]
service = StudyService(package, authority, repository_root=repo, allow_draft=True, actor="fixture-evaluator", role="Study 歷史評估執行者", assignment=load_canonical(Path(temp)/"assignment.yml"))
original_create = operation.atomic_create
original_append = service.append_event
original_launch = operation.launch
import writer.journal as journal
original_journal_create = journal.atomic_create

def journal_create(path, data):
    original_journal_create(path, data)
    if "-" not in boundary or boundary in {"authority-marker"}: return
    stage, phase = boundary.split("-", 1)
    number = {"started": 8, "completed": 9, "terminal": 10}.get(stage)
    if number and path.name.startswith(f"{number:06d}") and ((phase == "event" and path.parent.name == "events") or (phase == "checkpoint" and path.parent.name == "checkpoints")):
        os._exit(71)
journal.atomic_create = journal_create

def atomic(path, data):
    original_create(path, data)
    if (boundary == "reservation" and path.name == "evaluation-operation.yml") or (boundary == "authority-marker" and path.name == "evaluation-launch.yml") or (boundary == "marker" and path.name == "launch-marker.yml"):
        os._exit(71)

def append(study, kind, *args, **kwargs):
    result = original_append(study, kind, *args, **kwargs)
    if (boundary == "started" and kind == "historical-evaluation-started") or (boundary == "completed" and kind == "historical-evaluation-completed") or (boundary == "terminal" and kind == "study-terminal"):
        os._exit(71)
    return result

def launch(*args):
    count = Path(temp)/"launch-count"
    with count.open("a") as stream:
        stream.write("launch\n"); stream.flush(); os.fsync(stream.fileno())
    original_launch(*args)
    if boundary == "partial-output":
        Path(args[-1]).write_text("incomplete")
        os._exit(71)
    if boundary in {"missing-output", "deleted-local-marker"}:
        Path(args[-1]).unlink()
        if boundary == "deleted-local-marker":
            for marker in service.study_root(study).glob("operations/*/launch-marker.yml"):
                marker.unlink()
        os._exit(71)
    if boundary == "output": os._exit(71)
operation.atomic_create = atomic
operation.launch = launch
service.append_event = append
operation.historical_evaluation(service, study, load_canonical(Path(temp)/"plan.yml"))
"""
    result = process(
        service.workflow_root,
        code,
        service.workflow_root,
        service.repository_root,
        service.authority.root,
        study_id,
        tmp_path,
        boundary,
    )
    assert result.returncode == 71, result.stdout + result.stderr
    import operations.evaluation as operation

    original = operation.launch
    # A separate in-process invocation resumes the exact immutable inputs.
    from unittest.mock import patch

    def counted(*args):
        with (tmp_path / "launch-count").open("a") as stream:
            stream.write("launch\n")
        return original(*args)

    with patch.object(operation, "launch", counted):
        final = historical_evaluation(service, study_id, plan)
        assert historical_evaluation(service, study_id, plan) == final
    count = (
        (tmp_path / "launch-count").read_text().count("launch")
        if (tmp_path / "launch-count").exists()
        else 0
    )
    assert count == (0 if boundary in {"authority-marker", "marker"} else 1)
    assert final["outcome"] == (
        "indeterminate"
        if boundary
        in {
            "authority-marker",
            "marker",
            "partial-output",
            "missing-output",
            "deleted-local-marker",
        }
        else "fail"
    )
    events = [
        load_canonical(p)["event_type"]
        for p in (service.study_root(study_id) / "events").glob("*.yml")
    ]
    assert events.count("historical-evaluation-started") == 1
    assert events.count("study-terminal") == 1


@pytest.mark.parametrize("sequence", [1, 2, 3])
@pytest.mark.parametrize("phase", ["prepared", "event", "checkpoint"])
def test_create_hard_crash_same_inputs(tmp_path, sequence, phase):
    repo, package, study_id, authority, research = fixture_repository(tmp_path)
    report = passed_report(repo, package, study_id, authority)
    plan = plan_for(study_id, research)
    write(tmp_path / "report.yml", report)
    write(tmp_path / "plan.yml", plan)
    write(tmp_path / "assignment.yml", assignment_for(study_id))
    code = r"""
import os, sys
from pathlib import Path
import writer.journal as journal
from operations.service import create
from validator.canonical_yaml import load_canonical
from writer.service import StudyService
package, repo, authority, study, temp, sequence, phase = sys.argv[1:]
service = StudyService(package, authority, repository_root=repo, allow_draft=True, actor="fixture-owner", role="study 開發者", assignment=load_canonical(Path(temp)/"assignment.yml"))
original = journal.atomic_create
counter = 0

def atomic(path, data):
    global counter
    original(path, data)
    matches = (phase == "prepared" and path.name.endswith(".prepared.yml")) or (phase == "event" and path.parent.name == "events") or (phase == "checkpoint" and path.parent.name == "checkpoints")
    if matches:
        counter += 1
        if counter == int(sequence): os._exit(72)
journal.atomic_create = atomic
create(service, load_canonical(Path(temp)/"plan.yml"), load_canonical(Path(temp)/"report.yml"))
"""
    result = process(package, code, package, repo, authority, study_id, tmp_path, sequence, phase)
    assert result.returncode == 72, result.stdout + result.stderr
    service = make_service(package, authority, repo, study_id)
    create(service, plan, report)
    assert service.validate(study_id)["lifecycle"]["event_count"] == 3
    assert len(service.authority.checkpoints(study_id)) == 3


def test_parallel_evaluation_only_one_launch(tmp_path):
    _, service, study_id, plan = evaluation_fixture(tmp_path)
    write(tmp_path / "plan.yml", plan)
    write(tmp_path / "assignment.yml", service.assignment)
    code = r"""
import os, sys
from pathlib import Path
import operations.evaluation as operation
from validator.canonical_yaml import load_canonical
from writer.service import StudyService
package, repo, authority, study, temp = sys.argv[1:]
service = StudyService(package, authority, repository_root=repo, allow_draft=True, actor="fixture-evaluator", role="Study 歷史評估執行者", assignment=load_canonical(Path(temp)/"assignment.yml"))
original = operation.launch

def launch(*args):
    with (Path(temp)/"count").open("a") as stream:
        stream.write("launch\n"); stream.flush(); os.fsync(stream.fileno())
    return original(*args)
operation.launch = launch
operation.historical_evaluation(service, study, load_canonical(Path(temp)/"plan.yml"))
"""
    args = [
        sys.executable,
        "-c",
        code,
        str(service.workflow_root),
        str(service.repository_root),
        str(service.authority.root),
        study_id,
        str(tmp_path),
    ]
    env = dict(os.environ, PYTHONPATH=str(service.workflow_root))
    children = [
        subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        for _ in range(2)
    ]
    results = [child.communicate(timeout=90) for child in children]
    assert any(child.returncode == 0 for child in children), results
    assert all(
        child.returncode == 0 or "lock" in output[1]
        for child, output in zip(children, results, strict=True)
    ), results
    assert (tmp_path / "count").read_text() == "launch\n"
    with pytest.raises(WorkflowError):
        historical_evaluation(service, study_id, dict(plan, data_path="another.csv"))
