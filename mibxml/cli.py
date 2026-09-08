from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .pipeline import (
    DEFAULT_ENTITIES_DIR,
    DEFAULT_INPUT_DIR,
    list_mib_xml_files,
    parse_mib_xml,
)


def _resolve_inputs(input_arg: str | None) -> list[Path]:
    if input_arg is None:
        return list_mib_xml_files(DEFAULT_INPUT_DIR)
    path = Path(input_arg)
    if path.is_dir():
        return list_mib_xml_files(path)
    return [path]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generic mib-xml parser: slim XML + annotated Java entities.",
    )
    parser.add_argument(
        "-i",
        "--input",
        default=None,
        help=(
            "mib-xml file or folder. "
            f"Default folder: {DEFAULT_INPUT_DIR}"
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help=(
            "Override output (parse-xml + entities all go here). "
            f"Default Java folder: {DEFAULT_ENTITIES_DIR}/{{stem}}/; "
            "slim xml stays next to the input file."
        ),
    )
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else None
    try:
        inputs = _resolve_inputs(args.input)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    if not inputs:
        print(f"no mib-xml files in {args.input or DEFAULT_INPUT_DIR}", file=sys.stderr)
        return 1
    for input_path in inputs:
        try:
            result = parse_mib_xml(input_path, output_dir)
        except (FileNotFoundError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
        print(f"parse xml : {result['parse_xml']}")
        print(f"entities  : {result['entities']}")
    return 0
