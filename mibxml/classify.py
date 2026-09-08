"""Classify stripped mib-xml nodes. Walks oid/type/indexes, never hardcodes table names."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .strip import parse_indexes

KIND_GROUP = "group"
KIND_SCALAR = "scalar"
KIND_TABLE = "table"
KIND_ENTRY = "entry"
KIND_COLUMN = "column"


def syntax(elem: ET.Element) -> str:
    return (elem.get("type") or "").strip()


def kind(elem: ET.Element, parent_kind: str | None = None) -> str:
    t = syntax(elem)
    indexes = parse_indexes(elem.get("indexes"))
    children = list(elem)
    if t.upper().startswith("SEQUENCE OF"):
        return KIND_TABLE
    if indexes:
        return KIND_ENTRY
    if not children:
        if parent_kind == KIND_ENTRY:
            return KIND_COLUMN
        return KIND_SCALAR
    return KIND_GROUP


def java_class_name(tag: str) -> str:
    if not tag:
        return "Node"
    return tag[0].upper() + tag[1:]


def java_type(syntax_name: str) -> str:
    upper = syntax_name.upper()
    if "OCTET STRING" in upper:
        return "byte[]"
    if upper in {"IPADDRESS", "DISPLAYSTRING", "OWNERSTRING", "OERSTRING"}:
        return "String"
    return "Integer"


def python_type(syntax_name: str) -> str:
    upper = syntax_name.upper()
    if "OCTET STRING" in upper:
        return "bytes"
    if upper in {"IPADDRESS", "DISPLAYSTRING", "OWNERSTRING", "OERSTRING"}:
        return "str"
    return "int"


JAVA_RESERVED = {
    "class", "package", "default", "int", "long", "public", "private", "static",
    "void", "boolean", "new", "this", "super", "import", "return", "if", "for",
}


def java_field_name(tag: str) -> str:
    if tag in JAVA_RESERVED:
        return tag + "_"
    return tag
