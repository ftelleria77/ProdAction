"""Command line interface for PGMX synthesis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional


def main(argv: Optional[list[str]] = None) -> int:
    from .core import (
        DEFAULT_BASELINE_DIR,
        _compact_number,
        build_circle_spec,
        build_line_spec,
        build_synthesis_request,
        synthesize_request,
    )

    parser = argparse.ArgumentParser(
        description="Sintetiza un PGMX base a partir de un baseline Maestro (.pgmx, Pieza.xml o carpeta)."
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE_DIR),
        help=(
            "Ruta al baseline Maestro: `.pgmx`, `Pieza.xml` o carpeta contenedora. "
            "Si no se indica, usa `pgmx/data/maestro_baselines`."
        ),
    )
    parser.add_argument("--output", required=True, help="Ruta del .pgmx sintetizado de salida.")
    parser.add_argument(
        "--source-pgmx",
        "--source-template",
        dest="source_pgmx",
        help=(
            "Ruta a una plantilla manual de Maestro (`.pgmx`, `Pieza.xml` o carpeta) "
            "desde la cual copiar serializacion ya validada."
        ),
    )
    parser.add_argument("--piece-name", help="Nombre interno de la pieza dentro del .pgmx.")
    parser.add_argument("--length", type=float, help="Largo final de la pieza (dx1).")
    parser.add_argument("--width", type=float, help="Ancho final de la pieza (dy1).")
    parser.add_argument("--depth", type=float, help="Espesor final de la pieza (dz1).")
    parser.add_argument("--origin-x", type=float, help="Origen de mecanizado X.")
    parser.add_argument("--origin-y", type=float, help="Origen de mecanizado Y.")
    parser.add_argument("--origin-z", type=float, help="Origen de mecanizado Z.")
    parser.add_argument(
        "--execution-fields",
        "--area",
        dest="execution_fields",
        help="Area de Parametros de Maquina. Valores observados: A, EF, HG. Si no se indica, la sintesis usa HG.",
    )
    parser.add_argument("--line-x1", type=float, help="Coordenada X inicial de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-y1", type=float, help="Coordenada Y inicial de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-x2", type=float, help="Coordenada X final de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-y2", type=float, help="Coordenada Y final de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-feature-name", help="Nombre del feature/working step del fresado lineal.")
    parser.add_argument("--line-side-of-feature", help="Correccion de herramienta del fresado lineal: Center, Right o Left.")
    parser.add_argument("--line-tool-id", help="ID de herramienta para el fresado lineal.")
    parser.add_argument("--line-tool-name", help="Nombre de herramienta para el fresado lineal.")
    parser.add_argument("--line-tool-width", type=float, help="Ancho del perfil barrido para el fresado lineal.")
    parser.add_argument("--line-security-plane", type=float, help="Plano de seguridad usado en approach/retract.")
    parser.add_argument(
        "--line-through",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Configura Pasante activado/desactivado del fresado lineal. Por defecto queda activado.",
    )
    parser.add_argument(
        "--line-target-depth",
        type=float,
        help="Profundidad fija del fresado lineal cuando Pasante esta desactivado.",
    )
    parser.add_argument(
        "--line-extra-depth",
        type=float,
        help="Extra del fresado lineal cuando Pasante esta activado.",
    )
    parser.add_argument(
        "--line-approach-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el approach del fresado lineal. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro: Line/Quote/radio 2/speed -1."
        ),
    )
    parser.add_argument("--line-approach-type", help="Tipo de approach. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--line-approach-mode",
        help="Modo de approach. Valores utiles: Down o Quote (UI Maestro: En Cota). Para Arc se valido Quote.",
    )
    parser.add_argument(
        "--line-approach-radius-multiplier",
        type=float,
        help="Multiplicador de radio del approach lineal.",
    )
    parser.add_argument(
        "--line-approach-speed",
        type=float,
        help="Velocidad del approach. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--line-approach-arc-side",
        help="Lado del arco del approach. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--line-retract-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el retract del fresado lineal. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro: Line/Quote/radio 2/speed -1/overlap 0."
        ),
    )
    parser.add_argument("--line-retract-type", help="Tipo de retract. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--line-retract-mode",
        help="Modo de retract. Valores utiles: Up o Quote (UI Maestro: En Cota). Para Arc se validaron Quote y Up.",
    )
    parser.add_argument(
        "--line-retract-radius-multiplier",
        type=float,
        help="Multiplicador de radio del retract lineal.",
    )
    parser.add_argument(
        "--line-retract-speed",
        type=float,
        help="Velocidad del retract. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--line-retract-arc-side",
        help="Lado del arco del retract. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--line-retract-overlap",
        type=float,
        help="Sobreposicion del retract lineal.",
    )
    parser.add_argument("--circle-center-x", type=float, help="Coordenada X del centro del circulo sobre Top.")
    parser.add_argument("--circle-center-y", type=float, help="Coordenada Y del centro del circulo sobre Top.")
    parser.add_argument("--circle-radius", type=float, help="Radio del circulo a fresar sobre Top.")
    parser.add_argument("--circle-winding", help="Sentido del circulo: CounterClockwise/Antihorario o Clockwise/Horario.")
    parser.add_argument("--circle-feature-name", help="Nombre del feature/working step del fresado circular.")
    parser.add_argument("--circle-side-of-feature", help="Correccion de herramienta del fresado circular: Center, Right o Left.")
    parser.add_argument("--circle-tool-id", help="ID de herramienta para el fresado circular.")
    parser.add_argument("--circle-tool-name", help="Nombre de herramienta para el fresado circular.")
    parser.add_argument("--circle-tool-width", type=float, help="Ancho del perfil barrido para el fresado circular.")
    parser.add_argument("--circle-security-plane", type=float, help="Plano de seguridad usado en approach/retract del circulo.")
    parser.add_argument(
        "--circle-through",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Configura Pasante activado/desactivado del fresado circular. Por defecto queda activado.",
    )
    parser.add_argument(
        "--circle-target-depth",
        type=float,
        help="Profundidad fija del fresado circular cuando Pasante esta desactivado.",
    )
    parser.add_argument(
        "--circle-extra-depth",
        type=float,
        help="Extra del fresado circular cuando Pasante esta activado.",
    )
    parser.add_argument(
        "--circle-approach-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el approach del fresado circular. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro."
        ),
    )
    parser.add_argument("--circle-approach-type", help="Tipo de approach del circulo. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--circle-approach-mode",
        help="Modo de approach del circulo. Valores utiles: Down o Quote (UI Maestro: En Cota).",
    )
    parser.add_argument(
        "--circle-approach-radius-multiplier",
        type=float,
        help="Multiplicador de radio del approach circular.",
    )
    parser.add_argument(
        "--circle-approach-speed",
        type=float,
        help="Velocidad del approach del circulo. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--circle-approach-arc-side",
        help="Lado del arco del approach circular. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--circle-retract-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el retract del fresado circular. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro."
        ),
    )
    parser.add_argument("--circle-retract-type", help="Tipo de retract del circulo. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--circle-retract-mode",
        help="Modo de retract del circulo. Valores utiles: Up o Quote (UI Maestro: En Cota).",
    )
    parser.add_argument(
        "--circle-retract-radius-multiplier",
        type=float,
        help="Multiplicador de radio del retract circular.",
    )
    parser.add_argument(
        "--circle-retract-speed",
        type=float,
        help="Velocidad del retract del circulo. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--circle-retract-arc-side",
        help="Lado del arco del retract circular. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--circle-retract-overlap",
        type=float,
        help="Sobreposicion del retract circular.",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output)
    line_milling = build_line_spec(
        line_x1=args.line_x1,
        line_y1=args.line_y1,
        line_x2=args.line_x2,
        line_y2=args.line_y2,
        line_feature_name=args.line_feature_name,
        line_side_of_feature=args.line_side_of_feature,
        line_tool_id=args.line_tool_id,
        line_tool_name=args.line_tool_name,
        line_tool_width=args.line_tool_width,
        line_security_plane=args.line_security_plane,
        line_is_through=args.line_through,
        line_target_depth=args.line_target_depth,
        line_extra_depth=args.line_extra_depth,
        line_approach_enabled=args.line_approach_enabled,
        line_approach_type=args.line_approach_type,
        line_approach_mode=args.line_approach_mode,
        line_approach_radius_multiplier=args.line_approach_radius_multiplier,
        line_approach_speed=args.line_approach_speed,
        line_approach_arc_side=args.line_approach_arc_side,
        line_retract_enabled=args.line_retract_enabled,
        line_retract_type=args.line_retract_type,
        line_retract_mode=args.line_retract_mode,
        line_retract_radius_multiplier=args.line_retract_radius_multiplier,
        line_retract_speed=args.line_retract_speed,
        line_retract_arc_side=args.line_retract_arc_side,
        line_retract_overlap=args.line_retract_overlap,
    )
    circle_args = (args.circle_center_x, args.circle_center_y, args.circle_radius)
    if all(value is None for value in circle_args):
        circle_milling = None
    elif any(value is None for value in circle_args):
        raise ValueError(
            "Para sintetizar el fresado circular hay que indicar center_x, center_y y radius."
        )
    else:
        circle_milling = build_circle_spec(
            center_x=float(args.circle_center_x),
            center_y=float(args.circle_center_y),
            radius=float(args.circle_radius),
            winding=args.circle_winding,
            feature_name=args.circle_feature_name,
            tool_id=args.circle_tool_id,
            tool_name=args.circle_tool_name,
            tool_width=args.circle_tool_width,
            security_plane=args.circle_security_plane,
            side_of_feature=args.circle_side_of_feature,
            is_through=args.circle_through,
            target_depth=args.circle_target_depth,
            extra_depth=args.circle_extra_depth,
            approach_enabled=args.circle_approach_enabled,
            approach_type=args.circle_approach_type,
            approach_mode=args.circle_approach_mode,
            approach_radius_multiplier=args.circle_approach_radius_multiplier,
            approach_speed=args.circle_approach_speed,
            approach_arc_side=args.circle_approach_arc_side,
            retract_enabled=args.circle_retract_enabled,
            retract_type=args.circle_retract_type,
            retract_mode=args.circle_retract_mode,
            retract_radius_multiplier=args.circle_retract_radius_multiplier,
            retract_speed=args.circle_retract_speed,
            retract_arc_side=args.circle_retract_arc_side,
            retract_overlap=args.circle_retract_overlap,
        )
    request = build_synthesis_request(
        baseline_path=Path(args.baseline),
        output_path=output_path,
        source_pgmx_path=Path(args.source_pgmx) if args.source_pgmx else None,
        piece_name=args.piece_name,
        length=args.length,
        width=args.width,
        depth=args.depth,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        origin_z=args.origin_z,
        execution_fields=args.execution_fields,
        line_millings=[line_milling] if line_milling is not None else (),
        circle_millings=[circle_milling] if circle_milling is not None else (),
    )
    result = synthesize_request(request)

    summary = {
        "output": str(output_path),
        "piece_name": result.piece.piece_name,
        "length": _compact_number(result.piece.length),
        "width": _compact_number(result.piece.width),
        "depth": _compact_number(result.piece.depth),
        "origin_x": _compact_number(result.piece.origin_x),
        "origin_y": _compact_number(result.piece.origin_y),
        "origin_z": _compact_number(result.piece.origin_z),
        "execution_fields": result.piece.execution_fields,
        "sha256": result.sha256,
    }
    if line_milling is not None:
        summary["line_milling"] = {
            "feature_name": line_milling.feature_name,
            "start": [_compact_number(line_milling.start_x), _compact_number(line_milling.start_y)],
            "end": [_compact_number(line_milling.end_x), _compact_number(line_milling.end_y)],
            "side_of_feature": line_milling.side_of_feature,
            "tool_id": line_milling.tool_id,
            "tool_name": line_milling.tool_name,
            "tool_width": _compact_number(line_milling.tool_width),
            "security_plane": _compact_number(line_milling.security_plane),
            "approach": {
                "is_enabled": line_milling.approach.is_enabled,
                "approach_type": line_milling.approach.approach_type,
                "mode": line_milling.approach.mode,
                "radius_multiplier": _compact_number(line_milling.approach.radius_multiplier),
                "speed": _compact_number(line_milling.approach.speed),
                "arc_side": line_milling.approach.arc_side,
            },
            "retract": {
                "is_enabled": line_milling.retract.is_enabled,
                "retract_type": line_milling.retract.retract_type,
                "mode": line_milling.retract.mode,
                "radius_multiplier": _compact_number(line_milling.retract.radius_multiplier),
                "speed": _compact_number(line_milling.retract.speed),
                "arc_side": line_milling.retract.arc_side,
                "overlap": _compact_number(line_milling.retract.overlap),
            },
        }
    if circle_milling is not None:
        summary["circle_milling"] = {
            "feature_name": circle_milling.feature_name,
            "center": [_compact_number(circle_milling.center_x), _compact_number(circle_milling.center_y)],
            "radius": _compact_number(circle_milling.radius),
            "winding": circle_milling.winding,
            "side_of_feature": circle_milling.side_of_feature,
            "tool_id": circle_milling.tool_id,
            "tool_name": circle_milling.tool_name,
            "tool_width": _compact_number(circle_milling.tool_width),
            "security_plane": _compact_number(circle_milling.security_plane),
            "approach": {
                "is_enabled": circle_milling.approach.is_enabled,
                "approach_type": circle_milling.approach.approach_type,
                "mode": circle_milling.approach.mode,
                "radius_multiplier": _compact_number(circle_milling.approach.radius_multiplier),
                "speed": _compact_number(circle_milling.approach.speed),
                "arc_side": circle_milling.approach.arc_side,
            },
            "retract": {
                "is_enabled": circle_milling.retract.is_enabled,
                "retract_type": circle_milling.retract.retract_type,
                "mode": circle_milling.retract.mode,
                "radius_multiplier": _compact_number(circle_milling.retract.radius_multiplier),
                "speed": _compact_number(circle_milling.retract.speed),
                "arc_side": circle_milling.retract.arc_side,
                "overlap": _compact_number(circle_milling.retract.overlap),
            },
        }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0

