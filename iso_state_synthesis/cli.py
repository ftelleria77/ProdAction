"""CLI for the state-based ISO synthesis experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .differential import evaluate_pgmx_state_plan
from .emitter import (
    IsoCandidateEmissionError,
    compare_candidate_to_iso,
    emit_candidate_for_pgmx,
)
from .model import IsoStateEvaluation, IsoStatePlan, StageDifferential, StateStage, to_jsonable
from .pgmx_source import build_state_plan_from_pgmx


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Herramientas experimentales para sintesis ISO por estado."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect-pgmx",
        help="Lee un .pgmx y muestra el plan interno de estados.",
    )
    inspect_parser.add_argument("pgmx_path")
    inspect_parser.add_argument("--json", action="store_true", help="Imprime JSON completo.")
    inspect_parser.add_argument("--summary", action="store_true", help="Imprime solo resumen JSON.")
    inspect_parser.add_argument("--output", help="Archivo de salida JSON.")

    eval_parser = subparsers.add_parser(
        "evaluate-pgmx",
        help="Calcula diferenciales entre estado activo y estado objetivo.",
    )
    eval_parser.add_argument("pgmx_path")
    eval_parser.add_argument("--json", action="store_true", help="Imprime JSON completo.")
    eval_parser.add_argument("--summary", action="store_true", help="Imprime solo resumen JSON.")
    eval_parser.add_argument("--output", help="Archivo de salida JSON.")

    emit_parser = subparsers.add_parser(
        "emit-candidate",
        help="Emite ISO candidato explicado para el subset soportado.",
    )
    emit_parser.add_argument("pgmx_path")
    emit_parser.add_argument("--program-name", help="Nombre ISO sin extension.")
    emit_parser.add_argument("--json", action="store_true", help="Imprime lineas con explicacion.")
    emit_parser.add_argument("--output", help="Archivo de salida.")

    compare_parser = subparsers.add_parser(
        "compare-candidate",
        help="Compara el ISO candidato contra un ISO Maestro.",
    )
    compare_parser.add_argument("pgmx_path")
    compare_parser.add_argument("expected_iso")
    compare_parser.add_argument("--program-name", help="Nombre ISO sin extension.")
    compare_parser.add_argument("--json", action="store_true", help="Imprime JSON.")
    compare_parser.add_argument("--diff", action="store_true", help="Incluye diff normalizado.")
    compare_parser.add_argument("--candidate-output", help="Guarda el ISO candidato.")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if args.command == "inspect-pgmx":
        return _inspect_pgmx(args)
    if args.command == "evaluate-pgmx":
        return _evaluate_pgmx(args)
    if args.command == "emit-candidate":
        return _emit_candidate(args)
    if args.command == "compare-candidate":
        return _compare_candidate(args)
    parser.error(f"Comando no soportado: {args.command}")
    return 2


def _inspect_pgmx(args: argparse.Namespace) -> int:
    plan = build_state_plan_from_pgmx(Path(args.pgmx_path))
    if args.summary:
        payload = plan.summary()
    elif args.json or args.output:
        payload = to_jsonable(plan)
    else:
        _print_text_summary(plan)
        return 0

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def _evaluate_pgmx(args: argparse.Namespace) -> int:
    evaluation = evaluate_pgmx_state_plan(Path(args.pgmx_path))
    if args.summary:
        payload = evaluation.summary()
    elif args.json or args.output:
        payload = to_jsonable(evaluation)
    else:
        _print_evaluation_summary(evaluation)
        return 0

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def _emit_candidate(args: argparse.Namespace) -> int:
    try:
        program = emit_candidate_for_pgmx(
            Path(args.pgmx_path),
            program_name=args.program_name,
        )
    except IsoCandidateEmissionError as exc:
        if args.json:
            print(json.dumps({"error": "unsupported_candidate", "message": str(exc)}, ensure_ascii=False))
        else:
            print(f"Sin candidato: {exc}")
        return 2
    if args.json:
        text = json.dumps(to_jsonable(program), indent=2, ensure_ascii=False)
    else:
        text = program.text()
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0


def _compare_candidate(args: argparse.Namespace) -> int:
    try:
        program = emit_candidate_for_pgmx(
            Path(args.pgmx_path),
            program_name=args.program_name,
        )
    except IsoCandidateEmissionError as exc:
        if args.json:
            print(json.dumps({"error": "unsupported_candidate", "message": str(exc)}, ensure_ascii=False))
        else:
            print(f"Sin candidato: {exc}")
        return 2
    if args.candidate_output:
        program.write_text(Path(args.candidate_output))
    result = compare_candidate_to_iso(
        Path(args.expected_iso),
        program,
        include_diff=bool(args.diff),
    )
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
        if args.diff and result.diff:
            print(result.diff)
    return 0 if result.equal else 1


def _print_text_summary(plan: IsoStatePlan) -> None:
    print(f"PGMX: {plan.source_path}")
    print(f"Proyecto: {plan.project_name}")
    print(f"Estado inicial: {len(plan.initial_state.values)} valores")
    print(f"Etapas: {len(plan.stages)}")
    for stage in plan.stages:
        _print_stage(stage)
    if plan.warnings:
        print("Advertencias:")
        for warning in plan.warnings:
            print(f"- {warning.code}: {warning.source}: {warning.message}")


def _print_stage(stage: StateStage) -> None:
    xiso = f", XISO={stage.xiso_statement}" if stage.xiso_statement else ""
    print(f"- {stage.order_index:03d} {stage.key} [{stage.family}{xiso}]")
    if stage.target_state.values:
        keys = ", ".join(value.address for value in stage.target_state.values[:6])
        suffix = "..." if len(stage.target_state.values) > 6 else ""
        print(f"  target: {keys}{suffix}")
    if stage.trace:
        print(f"  trace: {len(stage.trace)} bloques")
    if stage.reset_state.values:
        keys = ", ".join(value.address for value in stage.reset_state.values)
        print(f"  reset: {keys}")


def _print_evaluation_summary(evaluation: IsoStateEvaluation) -> None:
    print(f"PGMX: {evaluation.source_path}")
    print(f"Proyecto: {evaluation.project_name}")
    print(f"Estado inicial: {len(evaluation.initial_state.values)} valores")
    print(f"Estado final: {len(evaluation.final_state.values)} valores")
    print(f"Diferenciales: {len(evaluation.differentials)}")
    for differential in evaluation.differentials:
        _print_differential(differential)
    if evaluation.warnings:
        print("Advertencias:")
        for warning in evaluation.warnings:
            print(f"- {warning.code}: {warning.source}: {warning.message}")


def _print_differential(differential: StageDifferential) -> None:
    print(
        f"- {differential.order_index:03d} {differential.stage_key} "
        f"[{differential.family}] cambios={differential.change_count}"
    )
    if differential.target_changes:
        keys = ", ".join(change.address for change in differential.target_changes[:8])
        suffix = "..." if len(differential.target_changes) > 8 else ""
        print(f"  set: {keys}{suffix}")
    if differential.forced_values:
        keys = ", ".join(change.address for change in differential.forced_values[:8])
        suffix = "..." if len(differential.forced_values) > 8 else ""
        print(f"  force: {keys}{suffix}")
    if differential.reset_changes:
        keys = ", ".join(change.address for change in differential.reset_changes)
        print(f"  reset: {keys}")
    if differential.trace:
        print(f"  trace: {len(differential.trace)} bloques")


if __name__ == "__main__":
    raise SystemExit(main())
