"""CLI for the experimental ISO generation subsystem."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .comparator import (
    IsoComparisonOptions,
    compare_iso_files,
    unified_diff,
)
from .emitter import emit_header_only
from .model import to_jsonable
from .pgmx_source import load_pgmx_iso_source


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Herramientas experimentales para traduccion PGMX -> ISO."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect-pgmx",
        help="Lee un .pgmx y muestra el resumen de adaptacion para ISO.",
    )
    inspect_parser.add_argument("pgmx_path")
    inspect_parser.add_argument("--json", action="store_true", help="Imprime JSON.")

    header_parser = subparsers.add_parser(
        "emit-header",
        help="Emite solo la cabecera ISO validada para un .pgmx.",
    )
    header_parser.add_argument("pgmx_path")
    header_parser.add_argument("--program-name", help="Nombre del programa ISO.")
    header_parser.add_argument("--output", help="Archivo de salida.")
    header_parser.add_argument(
        "--warnings-json",
        action="store_true",
        help="Imprime advertencias como JSON despues de escribir la cabecera.",
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compara un ISO Maestro contra otro ISO normalizado.",
    )
    compare_parser.add_argument("expected_iso")
    compare_parser.add_argument("actual_iso")
    compare_parser.add_argument("--json", action="store_true", help="Imprime JSON.")
    compare_parser.add_argument("--diff", action="store_true", help="Imprime diff.")
    compare_parser.add_argument(
        "--keep-program-name",
        action="store_true",
        help="No normaliza la primera linea con nombre de programa.",
    )
    compare_parser.add_argument(
        "--keep-blank-lines",
        action="store_true",
        help="No descarta lineas vacias.",
    )
    compare_parser.add_argument(
        "--keep-whitespace",
        action="store_true",
        help="No normaliza espacios internos.",
    )
    compare_parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="Compara sin distinguir mayusculas/minusculas.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if args.command == "inspect-pgmx":
        return _inspect_pgmx(args)
    if args.command == "emit-header":
        return _emit_header(args)
    if args.command == "compare":
        return _compare(args)
    parser.error(f"Comando no soportado: {args.command}")
    return 2


def _inspect_pgmx(args: argparse.Namespace) -> int:
    source = load_pgmx_iso_source(Path(args.pgmx_path))
    if args.json:
        print(json.dumps(source.summary(), indent=2, ensure_ascii=False))
        return 0

    piece = source.state
    print(f"PGMX: {source.path}")
    print(
        "Pieza: "
        f"{piece.piece_name} "
        f"({piece.length} x {piece.width} x {piece.depth}, area {piece.execution_fields})"
    )
    print(
        "Entradas: "
        f"adapted={source.adapted_count}, "
        f"unsupported={source.unsupported_count}, "
        f"ignored={source.ignored_count}"
    )
    if source.warnings:
        print("Advertencias:")
        for warning in source.warnings:
            print(f"- {warning.code}: {warning.source}: {warning.message}")
    return 0


def _emit_header(args: argparse.Namespace) -> int:
    source = load_pgmx_iso_source(Path(args.pgmx_path))
    program = emit_header_only(source, program_name=args.program_name)
    if args.output:
        program.write_text(Path(args.output))
    else:
        print(program.text(), end="")
    if args.warnings_json:
        print(json.dumps(to_jsonable(program.warnings), indent=2, ensure_ascii=False))
    return 0


def _compare(args: argparse.Namespace) -> int:
    options = IsoComparisonOptions(
        normalize_program_name=not args.keep_program_name,
        strip_blank_lines=not args.keep_blank_lines,
        normalize_whitespace=not args.keep_whitespace,
        ignore_case=bool(args.ignore_case),
    )
    expected_path = Path(args.expected_iso)
    actual_path = Path(args.actual_iso)
    result = compare_iso_files(expected_path, actual_path, options)
    if args.json:
        print(json.dumps(to_jsonable(result), indent=2, ensure_ascii=False))
    else:
        status = "igual" if result.equal else "distinto"
        print(
            f"Resultado: {status} "
            f"({result.expected_line_count} vs {result.actual_line_count} lineas, "
            f"{result.difference_count} diferencias)"
        )
        for difference in result.differences[:20]:
            print(
                f"- linea {difference.line_number}: "
                f"Maestro={difference.expected!r} / candidato={difference.actual!r}"
            )
    if args.diff:
        expected_text = expected_path.read_text(encoding="utf-8", errors="replace")
        actual_text = actual_path.read_text(encoding="utf-8", errors="replace")
        diff = unified_diff(
            expected_text,
            actual_text,
            options,
            expected_label=str(expected_path),
            actual_label=str(actual_path),
        )
        if diff:
            print(diff)
    return 0 if result.equal else 1


if __name__ == "__main__":
    raise SystemExit(main())
