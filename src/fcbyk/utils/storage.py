import json
import os
import tempfile
from typing import Any, TypeVar

_DEFAULT_APP_NAME = "fcbyk"


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def get_path(filename: str, *, app_name: str = _DEFAULT_APP_NAME, subdir: str | None = None) -> str:
    base = os.path.join(os.path.expanduser("~"), f".{app_name}")
    if subdir:
        base = os.path.join(base, subdir)
    return os.path.join(base, filename)


T = TypeVar("T")


def load_json(
    path: str,
    *,
    default: T | None = None,
    create_if_missing: bool = False,
    strict: bool = True,
) -> T:
    _ensure_dir(path)

    if not os.path.exists(path):
        if create_if_missing and default is not None:
            save_json(path, default)
        return default  # type: ignore[return-value]

    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)  # type: ignore[return-value]
        except Exception:
            if strict:
                raise
            return default  # type: ignore[return-value]


def save_json(path: str, data: Any, *, indent: int = 2, ensure_ascii: bool = False, atomic: bool = True) -> None:
    _ensure_dir(path)

    if atomic:
        dir_name = os.path.dirname(path)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tf:
            json.dump(data, tf, indent=indent, ensure_ascii=ensure_ascii)
            temp_name = tf.name
        os.replace(temp_name, path)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def load_section(filename: str, section: str, *, default: T | None = None, app_name: str = _DEFAULT_APP_NAME) -> T:
    path = get_path(filename, app_name=app_name)
    root = load_json(path, default={}, create_if_missing=True, strict=True)
    assert isinstance(root, dict), "Root of JSON must be an object for section operations"

    section_data = root.get(section)
    updated = False

    if section_data is None:
        if default is not None:
            root[section] = default
            updated = True
            section_data = default
    elif isinstance(section_data, dict) and isinstance(default, dict):
        for k, v in default.items():
            if k not in section_data:
                section_data[k] = v
                updated = True

    if updated:
        save_json(path, root)

    return section_data if section_data is not None else default  # type: ignore[return-value]


def save_section(filename: str, section: str, data: Any, *, app_name: str = _DEFAULT_APP_NAME) -> None:
    path = get_path(filename, app_name=app_name)
    root = load_json(path, default={}, create_if_missing=True, strict=True)
    assert isinstance(root, dict), "Root of JSON must be object"
    root[section] = data
    save_json(path, root)


def read_text(path: str, *, default: str | None = None) -> str | None:
    _ensure_dir(path)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return default


def write_text(path: str, content: str, *, atomic: bool = True) -> None:
    _ensure_dir(path)
    if atomic:
        dir_name = os.path.dirname(path)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tf:
            tf.write(content)
            temp_name = tf.name
        os.replace(temp_name, path)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
