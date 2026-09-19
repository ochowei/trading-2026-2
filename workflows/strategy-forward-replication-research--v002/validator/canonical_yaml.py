"""Repository-canonical YAML v1。

正式檔案只接受可穩定重新序列化的 YAML 子集。Digest 一律計算 exact bytes。
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.tokens import AliasToken, AnchorToken, TagToken

from .errors import IntegrityError, ValidationError


class CanonicalLoader(yaml.SafeLoader):
    """拒絕重複 key，且不把日期字串隱式轉成 datetime。"""


CanonicalLoader.yaml_implicit_resolvers = deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for resolver_key, resolver_values in list(CanonicalLoader.yaml_implicit_resolvers.items()):
    CanonicalLoader.yaml_implicit_resolvers[resolver_key] = [
        value for value in resolver_values if value[0] != "tag:yaml.org,2002:timestamp"
    ]


def _construct_mapping(loader: CanonicalLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    loader.flatten_mapping(node)
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ConstructorError(
                "mapping key", key_node.start_mark, "key 必須是字串", key_node.start_mark
            )
        if key in result:
            raise ConstructorError(
                "mapping key", key_node.start_mark, f"重複 key: {key}", key_node.start_mark
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


CanonicalLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


class CanonicalDumper(yaml.SafeDumper):
    """固定 list indentation，且不產生 aliases。"""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        return super().increase_indent(flow, False)

    def ignore_aliases(self, data: Any) -> bool:
        return True


def _validate_value(value: Any, location: str = "$") -> None:
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        raise ValidationError(f"{location}: 正式 YAML 禁止 float，請用十進位字串")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{location}: mapping key 必須是字串")
            _validate_value(item, f"{location}.{key}")
        return
    raise ValidationError(f"{location}: 不支援的 YAML 型別 {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """將支援的資料結構轉成唯一的 YAML bytes。"""

    _validate_value(value)
    text = yaml.dump(
        value,
        Dumper=CanonicalDumper,
        allow_unicode=True,
        default_flow_style=False,
        explicit_end=False,
        explicit_start=False,
        indent=2,
        line_break="\n",
        sort_keys=True,
        width=10_000,
    )
    return text.rstrip("\n").encode("utf-8") + b"\n"


def canonical_digest(value_or_bytes: Any) -> str:
    data = value_or_bytes if isinstance(value_or_bytes, bytes) else canonical_bytes(value_or_bytes)
    return hashlib.sha256(data).hexdigest()


def parse_yaml(data: bytes) -> Any:
    """安全解析 YAML；anchors、aliases 與 tags 一律拒絕。"""

    try:
        for token in yaml.scan(data.decode("utf-8")):
            if isinstance(token, (AnchorToken, AliasToken, TagToken)):
                raise ValidationError("正式 YAML 禁止 anchors、aliases 與自訂 tags")
        value = yaml.load(data, Loader=CanonicalLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValidationError(f"無法解析 YAML: {exc}") from exc
    _validate_value(value)
    return value


def load_yaml(path: Path | str, *, require_canonical: bool = False) -> Any:
    source = Path(path)
    data = source.read_bytes()
    value = parse_yaml(data)
    if require_canonical and canonical_bytes(value) != data:
        raise IntegrityError(f"{source}: 不是 repository-canonical YAML")
    return value


def load_canonical(path: Path | str) -> Any:
    return load_yaml(path, require_canonical=True)


def atomic_create(path: Path | str, data: bytes) -> None:
    """在相同 filesystem 以不可覆寫方式原子建立檔案。"""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp_path, destination)
        except FileExistsError as exc:
            if destination.read_bytes() == data:
                return
            raise IntegrityError(f"拒絕覆寫不同內容: {destination}") from exc
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temp_path.unlink(missing_ok=True)


def write_canonical(path: Path | str, value: Any) -> None:
    atomic_create(path, canonical_bytes(value))


def atomic_replace(path: Path | str, data: bytes) -> None:
    """原子替換可重建 projection；不可用於 authority artifacts。"""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temp_path.unlink(missing_ok=True)
