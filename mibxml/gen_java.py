"""Emit Java annotations + NTCIP entity sources from a stripped mib-xml tree."""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from .classify import (
    KIND_COLUMN,
    KIND_ENTRY,
    KIND_GROUP,
    KIND_SCALAR,
    KIND_TABLE,
    java_class_name,
    java_field_name,
    java_type,
    kind,
    syntax,
)
from .strip import parse_indexes

ANN_PACKAGE = "com.maxvision.ccu.base.model.ntcip.ann"
GEN_PACKAGE_PREFIX = "com.maxvision.ccu.base.model.ntcip.gen"

ANNOTATION_SOURCES = {
    "NtcipNode.java": '''package com.maxvision.ccu.base.model.ntcip.ann;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface NtcipNode {
    String name();
    String oid();
}
''',
    "NtcipScalar.java": '''package com.maxvision.ccu.base.model.ntcip.ann;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface NtcipScalar {
    String oid();
    String syntax();
    String access() default "";
}
''',
    "NtcipTable.java": '''package com.maxvision.ccu.base.model.ntcip.ann;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface NtcipTable {
    String oid();
    Class<?> entry();
    String access() default "";
}
''',
    "NtcipEntry.java": '''package com.maxvision.ccu.base.model.ntcip.ann;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface NtcipEntry {
    String oid();
    String[] indexes();
    String access() default "";
}
''',
    "NtcipColumn.java": '''package com.maxvision.ccu.base.model.ntcip.ann;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface NtcipColumn {
    String oid();
    String syntax();
    String access() default "";
    boolean index() default false;
}
''',
}


def _oid(elem: ET.Element) -> str:
    return elem.get("oid") or ""


def _access(elem: ET.Element) -> str:
    return elem.get("access") or ""


def _java_string_array(values: list[str]) -> str:
    inner = ", ".join(f'"{v}"' for v in values)
    return "{" + inner + "}"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _entry_child(table: ET.Element) -> ET.Element | None:
    for child in table:
        if kind(child, KIND_TABLE) == KIND_ENTRY:
            return child
    children = list(table)
    return children[0] if children else None


def _emit_entry(elem: ET.Element, package: str) -> str:
    class_name = java_class_name(elem.tag)
    indexes = parse_indexes(elem.get("indexes"))
    lines = [
        f"package {package};",
        "",
        f"import {ANN_PACKAGE}.NtcipColumn;",
        f"import {ANN_PACKAGE}.NtcipEntry;",
        "",
        f'@NtcipEntry(oid = "{_oid(elem)}", indexes = {_java_string_array(indexes)}, access = "{_access(elem)}")',
        f"public class {class_name} {{",
        "",
    ]
    for col in elem:
        syn = syntax(col) or "INTEGER"
        field = java_field_name(col.tag)
        is_index = col.tag in indexes
        lines.append(
            f'    @NtcipColumn(oid = "{_oid(col)}", syntax = "{syn}", '
            f'access = "{_access(col)}", index = {"true" if is_index else "false"})'
        )
        lines.append(f"    public {java_type(syn)} {field};")
        lines.append("")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _emit_group(elem: ET.Element, package: str) -> str:
    class_name = java_class_name(elem.tag)
    lines = [
        f"package {package};",
        "",
        "import java.util.List;",
        "",
        f"import {ANN_PACKAGE}.NtcipNode;",
        f"import {ANN_PACKAGE}.NtcipScalar;",
        f"import {ANN_PACKAGE}.NtcipTable;",
        "",
        f'@NtcipNode(name = "{elem.tag}", oid = "{_oid(elem)}")',
        f"public class {class_name} {{",
        "",
    ]
    parent_kind = KIND_GROUP
    for child in elem:
        child_kind = kind(child, parent_kind)
        field = java_field_name(child.tag)
        if child_kind == KIND_GROUP:
            nested = java_class_name(child.tag)
            lines.append(f"    public {nested} {field};")
            lines.append("")
        elif child_kind == KIND_SCALAR:
            syn = syntax(child) or "INTEGER"
            lines.append(
                f'    @NtcipScalar(oid = "{_oid(child)}", syntax = "{syn}", access = "{_access(child)}")'
            )
            lines.append(f"    public {java_type(syn)} {field};")
            lines.append("")
        elif child_kind == KIND_TABLE:
            entry = _entry_child(child)
            entry_name = java_class_name(entry.tag if entry is not None else child.tag + "Entry")
            lines.append(
                f'    @NtcipTable(oid = "{_oid(child)}", entry = {entry_name}.class, access = "{_access(child)}")'
            )
            lines.append(f"    public List<{entry_name}> {field};")
            lines.append("")
        elif child_kind == KIND_ENTRY:
            nested = java_class_name(child.tag)
            lines.append(f"    public {nested} {field};")
            lines.append("")
        elif child_kind == KIND_COLUMN:
            syn = syntax(child) or "INTEGER"
            lines.append(
                f'    @NtcipScalar(oid = "{_oid(child)}", syntax = "{syn}", access = "{_access(child)}")'
            )
            lines.append(f"    public {java_type(syn)} {field};")
            lines.append("")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _walk_write(elem: ET.Element, package: str, gen_dir: Path, parent_kind: str | None) -> None:
    this_kind = kind(elem, parent_kind)
    if this_kind == KIND_GROUP:
        class_name = java_class_name(elem.tag)
        _write(gen_dir / f"{class_name}.java", _emit_group(elem, package))
        for child in elem:
            _walk_write(child, package, gen_dir, KIND_GROUP)
    elif this_kind == KIND_TABLE:
        entry = _entry_child(elem)
        if entry is not None:
            _walk_write(entry, package, gen_dir, KIND_TABLE)
    elif this_kind == KIND_ENTRY:
        class_name = java_class_name(elem.tag)
        _write(gen_dir / f"{class_name}.java", _emit_entry(elem, package))


def write_java_entities(slim_root: ET.Element, out_dir: Path, package_leaf: str) -> Path:
    ann_dir = out_dir / ANN_PACKAGE.replace(".", "/")
    for name, source in ANNOTATION_SOURCES.items():
        _write(ann_dir / name, source)
    package = f"{GEN_PACKAGE_PREFIX}.{package_leaf}"
    gen_dir = out_dir / package.replace(".", "/")
    targets = list(slim_root) if slim_root.tag.lower() == "root" else [slim_root]
    for child in targets:
        _walk_write(child, package, gen_dir, KIND_GROUP)
    return out_dir
