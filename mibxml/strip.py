"""Strip description attributes from a mib-xml tree. Generic: no 1202 names."""

from __future__ import annotations

import copy
import xml.etree.ElementTree as ET

DROP_ATTRS = ("desc", "full")
KEEP_ATTRS = ("oid", "type", "access", "indexes")


def normalize_oid(oid: str | None) -> str | None:
    if oid is None:
        return None
    oid = oid.strip()
    while oid.startswith("."):
        oid = oid[1:]
    return oid or None


def parse_indexes(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def strip_element(src: ET.Element) -> ET.Element:
    dst = ET.Element(src.tag)
    for key in KEEP_ATTRS:
        value = src.get(key)
        if key == "oid":
            value = normalize_oid(value)
        if value:
            dst.set(key, value)
    for child in src:
        dst.append(strip_element(child))
    return dst


def strip_tree(root: ET.Element) -> ET.Element:
    slim = strip_element(root)
    module = root.get("module")
    if module:
        slim.set("module", module)
    return slim


def load_xml(path: str) -> ET.Element:
    tree = ET.parse(path)
    return tree.getroot()


def write_xml(root: ET.Element, path: str) -> None:
    out = copy.deepcopy(root)
    if hasattr(ET, "indent"):
        ET.indent(out, space="    ")
    tree = ET.ElementTree(out)
    tree.write(path, encoding="utf-8", xml_declaration=True)
