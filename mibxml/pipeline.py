from __future__ import annotations

import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

from .classify import java_class_name
from .gen_java import write_java_entities
from .strip import load_xml, strip_tree, write_xml

# parser/mibxml/pipeline.py → parser → model-ntcip
MODEL_NTCIP_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = MODEL_NTCIP_ROOT / "mib-xml"
DEFAULT_ENTITIES_DIR = MODEL_NTCIP_ROOT / "entities"


def stem_of(input_path: Path) -> str:
    if input_path.suffix.lower() != ".xml":
        raise ValueError(f"source must be a .xml file: {input_path}")
    return input_path.stem


def default_parse_xml_name(input_path: Path) -> str:
    return f"{stem_of(input_path)}-parse.xml"


def default_java_entities_dir(input_path: Path) -> Path:
    """Generated Java lives under model-ntcip/entities/{stem}/."""
    return DEFAULT_ENTITIES_DIR / stem_of(input_path)


def is_parse_xml_name(name: str) -> bool:
    return name.lower().endswith("-parse.xml")


def list_mib_xml_files(input_dir: Path) -> list[Path]:
    """*.xml in the input folder, skipping already-slim *-parse.xml."""
    input_dir = input_dir.resolve()
    if not input_dir.is_dir():
        raise FileNotFoundError(f"input dir not found: {input_dir}")
    files = []
    for path in sorted(input_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".xml":
            continue
        if is_parse_xml_name(path.name):
            continue
        files.append(path)
    return files


def package_leaf_from_root(slim_root: ET.Element) -> str:
    if slim_root.tag.lower() == "root":
        children = list(slim_root)
        if children:
            return children[0].tag
    return slim_root.tag or "mib"


def parse_mib_xml(input_path: Path, output_dir: Path | None = None) -> dict[str, Path]:
    """Generic: any mib-xml → slim xml + Java entities."""
    input_path = input_path.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"input xml not found: {input_path}")
    if input_path.suffix.lower() != ".xml":
        raise ValueError(f"source must be a .xml file: {input_path}")

    stem = stem_of(input_path)
    if output_dir is not None:
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        parse_xml_dir = output_dir
        entities_dir = output_dir / "entities" / stem
    else:
        parse_xml_dir = input_path.parent
        entities_dir = default_java_entities_dir(input_path)

    parse_xml_dir.mkdir(parents=True, exist_ok=True)
    raw_root = load_xml(str(input_path))
    slim_root = strip_tree(raw_root)

    parse_xml_path = parse_xml_dir / default_parse_xml_name(input_path)
    write_xml(slim_root, str(parse_xml_path))

    if entities_dir.exists():
        shutil.rmtree(entities_dir)
    entities_dir.mkdir(parents=True, exist_ok=True)

    leaf = java_class_name(package_leaf_from_root(slim_root))
    leaf = leaf[0].lower() + leaf[1:] if leaf else "mib"
    write_java_entities(slim_root, entities_dir, leaf)

    return {
        "parse_xml": parse_xml_path,
        "entities": entities_dir,
    }
