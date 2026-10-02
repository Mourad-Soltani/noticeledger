"""Minimal YAML subset parser for NoticeLedger vendor files.

Signature: Mourad.Soltani

Supports mappings, lists of mappings, and scalar strings. No anchors.
"""

from __future__ import annotations


def parse_simple_yaml(text: str) -> dict:
    root: dict = {}
    # stack entries: (indent, container)
    stack: list[tuple[int, object]] = [(-1, root)]

    lines = text.splitlines()
    for index, raw in enumerate(lines):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, root)]
        parent = stack[-1][1]

        if line.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"list item outside a list: {line}")
            item: dict = {}
            parent.append(item)
            rest = line[2:].strip()
            if rest:
                key, value = _split_kv(rest)
                if value == "" and _next_is_list(lines, index, indent + 2):
                    item[key] = []
                    stack.append((indent, item))
                    stack.append((indent + 2, item[key]))
                else:
                    item[key] = value
                    stack.append((indent, item))
            else:
                stack.append((indent, item))
            continue

        if not isinstance(parent, dict):
            raise ValueError(f"key outside a mapping: {line}")
        key, value = _split_kv(line)
        if value == "":
            if _next_is_list(lines, index, indent):
                parent[key] = []
            else:
                parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            parent[key] = value
    return root


def _next_is_list(lines: list[str], index: int, indent: int) -> bool:
    for nxt in lines[index + 1 :]:
        if not nxt.strip() or nxt.lstrip().startswith("#"):
            continue
        nindent = len(nxt) - len(nxt.lstrip(" "))
        if nindent <= indent:
            return False
        return nxt.strip().startswith("- ")
    return False


def _split_kv(line: str) -> tuple[str, object]:
    if ":" not in line:
        raise ValueError(f"expected key: value, got {line}")
    key, value = line.split(":", 1)
    return key.strip(), _coerce(value.strip())


def _coerce(value: str):
    if value == "":
        return ""
    if value.isdigit():
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value
