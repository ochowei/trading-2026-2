import pytest
from validator.errors import IntegrityError, ValidationError
from writer.service import StudyService


def test_freeze_readiness_uses_actual_transition_without_writing(
    workflow_root, tmp_path, monkeypatch
):
    from helpers import advance_to_candidate
    from operations.service import freeze_readiness

    # 此 fixture 只準備 Development 事件；runner/create 已由前面的完整入口測試涵蓋。
    service = StudyService(workflow_root, tmp_path / "authority", allow_draft=True)
    original = service.append_event
    frozen = {}

    def hold(study_id, event_type, actor, payload, **kwargs):
        if event_type == "candidate-frozen":
            frozen.update(payload)
            return "fixture-unpublished"
        return original(study_id, event_type, actor, payload, **kwargs)

    monkeypatch.setattr(service, "append_event", hold)
    advance_to_candidate(service)
    before = service.validate("study-1")
    assert freeze_readiness(service, "study-1", frozen, "same-person")["status"] == "passed"
    assert service.validate("study-1") == before
    bad = dict(frozen, selected_candidate_id="not-in-family")
    with pytest.raises((ValidationError, IntegrityError)):
        freeze_readiness(service, "study-1", bad, "same-person")
