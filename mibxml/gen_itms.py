"""Emit ITMS-handoff Java (GBT2017Packet + @Label). Not compiled by CCU."""

from __future__ import annotations

from datetime import datetime
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
    java_group_class_name,
    java_type,
    kind,
    syntax,
)
from .gen_java import _access, _entry_child
from .strip import parse_indexes

ITMS_PACKAGE = "com.maxvision.itms.ntcip"
ITMS_LABEL_TYPE = "com.maxvision.itms.ann.Label"
ITMS_PACKET_TYPE = "com.maxvision.itms.protocol.GBT2017Packet"

README_NAME = "README.md"


def _label_simple() -> str:
    return ITMS_LABEL_TYPE.rsplit(".", 1)[-1]


def _packet_simple() -> str:
    return ITMS_PACKET_TYPE.rsplit(".", 1)[-1]


def _modify(access: str, *, index: bool = False, table: bool = False) -> str:
    if table:
        return "true"
    if index:
        return "false"
    return "true" if "write" in (access or "").lower() else "false"


def _header() -> str:
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    return (
        "/*\n"
        " * AUTO-GENERATED for ITMS handoff. Do not compile in CCU.\n"
        " * Copy into the ITMS repo, fix package / Label / GBT2017Packet imports, then DELETE this folder.\n"
        f" * Generated at: {stamp}\n"
        " */\n"
        "\n"
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_header() + text, encoding="utf-8")


def _emit_inner_entry(elem: ET.Element, object_id: int) -> list[str]:
    class_name = java_class_name(elem.tag)
    indexes = set(parse_indexes(elem.get("indexes")))
    label = _label_simple()
    lines = [
        f"    public static class {class_name} {{",
        "",
    ]
    attr = 0
    for col in elem:
        attr += 1
        syn = syntax(col) or "INTEGER"
        field = java_field_name(col.tag)
        is_index = col.tag in indexes
        modify = _modify(_access(col), index=is_index)
        lines.append(
            f"        @{label}(Object = {object_id}, Attribute = {attr}, Modify = {modify})"
        )
        lines.append(f"        public {java_type(syn)} {field};")
        lines.append("")
    lines.append("    }")
    lines.append("")
    return lines


def _group_members(elem: ET.Element) -> tuple[list[str], list[str]]:
    label = _label_simple()
    fields: list[str] = []
    inners: list[str] = []
    object_id = 0
    for child in elem:
        child_kind = kind(child, KIND_GROUP)
        field = java_field_name(child.tag)
        object_id += 1
        if child_kind == KIND_GROUP:
            nested = java_group_class_name(child.tag)
            fields.append(f"    @{label}(Object = {object_id}, Modify = true)")
            fields.append(f"    public {nested} {field};")
            fields.append("")
        elif child_kind == KIND_SCALAR:
            syn = syntax(child) or "INTEGER"
            modify = _modify(_access(child))
            fields.append(f"    @{label}(Object = {object_id}, Modify = {modify})")
            fields.append(f"    public {java_type(syn)} {field};")
            fields.append("")
        elif child_kind == KIND_TABLE:
            entry = _entry_child(child)
            entry_name = java_class_name(
                entry.tag if entry is not None else child.tag + "Entry"
            )
            fields.append(f"    @{label}(Object = {object_id}, Modify = true)")
            fields.append(f"    public List<{entry_name}> {field};")
            fields.append("")
            if entry is not None:
                inners.extend(_emit_inner_entry(entry, object_id))
        elif child_kind == KIND_ENTRY:
            nested = java_class_name(child.tag)
            fields.append(f"    @{label}(Object = {object_id}, Modify = true)")
            fields.append(f"    public {nested} {field};")
            fields.append("")
        elif child_kind == KIND_COLUMN:
            syn = syntax(child) or "INTEGER"
            modify = _modify(_access(child))
            fields.append(f"    @{label}(Object = {object_id}, Modify = {modify})")
            fields.append(f"    public {java_type(syn)} {field};")
            fields.append("")
    return fields, inners


def _emit_root_group(elem: ET.Element) -> str:
    class_name = java_group_class_name(elem.tag)
    packet = _packet_simple()
    field_lines, inner_lines = _group_members(elem)
    lines = [
        f"package {ITMS_PACKAGE};",
        "",
        "import java.util.List;",
        "",
        f"import {ITMS_LABEL_TYPE};",
        f"import {ITMS_PACKET_TYPE};",
        "",
        f"public class {class_name} extends {packet}<{class_name}> {{",
        "",
    ]
    lines.extend(field_lines)
    lines.extend(inner_lines)
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _walk_itms_group(elem: ET.Element, out_dir: Path) -> None:
    _write(out_dir / f"{java_group_class_name(elem.tag)}.java", _emit_root_group(elem))


def _readme(class_names: list[str]) -> str:
    listing = "\n".join(f"- `{n}`" for n in class_names) or "- (none)"
    return f"""# itms-model-temp（发给 ITMS 后删除）

本目录是 **临时交接包**，给 ITMS 协议开发者用，**不要**编进 CCU。

拷贝到 ITMS 工程后 **删除整个 `itms-model-temp` 目录**（含本 README）。

每个 MIB **组**一个 `.java`（与 CCU 的 `Ntcip*` 组根类对应）。表行是该文件里的 `public static` 内部类。嵌套组是独立文件，父类里只留字段引用。

## 本目录 Java

{listing}

type 号由 ITMS 开发者自己登记，生成器不写。

## ITMS 开发者要做的

1. 把 `package {ITMS_PACKAGE}` 改成 ITMS 工程包名。
2. 把 `import {ITMS_LABEL_TYPE}` / `{ITMS_PACKET_TYPE}` 改成 ITMS 里 `@Label`、`GBT2017Packet` 的真实包。
3. 在 ITMS 把要用的根类登记到 type（不要占用国标已有 type，如 `Phase` / 4）。
4. 字段顺序、camelCase、`@Label(Object, Attribute, Modify)` 不要改；不要加 `Element`。
5. GET 只发信封 `type/objectId/attributeIds/elementIds`，不带 payload。

规则全文：`device-signal-ntcip-snmp/docs/REQ-01-itms.md` §3.2。

再生成：在 `model-ntcip/parser/` 执行 `py -3 parse_mib_xml.py --itms`。
"""


def write_itms_entities(slim_root: ET.Element, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    def visit(elem: ET.Element, parent_kind: str | None) -> None:
        this_kind = kind(elem, parent_kind)
        if this_kind == KIND_GROUP:
            _walk_itms_group(elem, out_dir)
            for child in elem:
                visit(child, KIND_GROUP)
        elif this_kind == KIND_TABLE:
            entry = _entry_child(elem)
            if entry is not None:
                visit(entry, KIND_TABLE)

    targets = list(slim_root) if slim_root.tag.lower() == "root" else [slim_root]
    for child in targets:
        visit(child, KIND_GROUP)

    class_names = sorted(p.stem for p in out_dir.glob("*.java"))
    (out_dir / README_NAME).write_text(_readme(class_names), encoding="utf-8")
    return out_dir
