from __future__ import annotations

from pathlib import Path

import pytest
from validator.canonical_yaml import canonical_bytes, load_canonical, parse_yaml
from validator.errors import IntegrityError, ValidationError


def test_canonical_round_trip(tmp_path: Path) -> None:
    value = {"z": ["二", "一"], "a": {"decimal": "1.10", "enabled": True}}
    path = tmp_path / "value.yml"
    path.write_bytes(canonical_bytes(value))
    assert load_canonical(path) == value
    assert path.read_text() == "a:\n  decimal: '1.10'\n  enabled: true\nz:\n  - 二\n  - 一\n"


def test_noncanonical_comments_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "comment.yml"
    path.write_text("# comment\na: 1\n")
    with pytest.raises(IntegrityError):
        load_canonical(path)


@pytest.mark.parametrize(
    "source",
    [
        b"a: &anchor value\nb: *anchor\n",
        b"a: 1.25\n",
        b"a: 1\na: 2\n",
    ],
)
def test_ambiguous_yaml_is_rejected(source: bytes) -> None:
    with pytest.raises(ValidationError):
        parse_yaml(source)
