"""Comparación de ISOs: byte-idéntico / funcionalmente idéntico / diferente.

Dato de dominio (Fermín, 2026-07-31): **Maestro comete errores de cálculo del orden de las
MILÉSIMAS de milímetro** — suma o resta algunas milésimas a los parámetros sin razón
aparente (manejo de coma flotante de su emisor). La máquina tiene una precisión del orden
de la DÉCIMA de milímetro, así que ese ruido es invisible en el mecanizado. Primer caso
documentado: el `J150.001` del anillo circular (manual 2026-07-30), cuyo centro emitido NO
es equidistante de los endpoints redondeados — irreproducible desde los datos del `.pgmx`.

Este módulo clasifica la comparación entre un ISO generado y su referencia:

- ``byte_identico``: iguales línea a línea (módulo espacios finales, la convención de
  todos los e2e del converter).
- ``funcionalmente_identico``: la MISMA estructura (mismas líneas, mismas palabras, mismo
  esqueleto no numérico) con deltas numéricos ≤ `tolerance` — el ruido de milésimas de
  Maestro. Cada delta queda reportado: la clasificación IDENTIFICA la diferencia, no la
  esconde (regla 4: nunca aproximar en silencio).
- ``diferente``: cualquier otra cosa (estructura distinta o algún delta > tolerancia).

Además descuenta las **omisiones deliberadas** (`DELIBERATE_OMISSIONS`): líneas que Maestro
emite MAL FORMADAS y que el CNC rechaza, y que el converter deja de emitir a propósito. Se
reportan aparte —nunca se esconden— y no cuentan como diferencia.

La tolerancia por defecto (0.005 mm) está un orden y medio por debajo de la precisión de
la máquina (0.1 mm) y por encima del ruido observado (±0.001): discrimina el ruido del
emisor sin tragarse diferencias reales de geometría.

Uso programático: ``classify_iso_diff(generado, referencia)``.
Uso CLI (p. ej. para la validación masiva del corpus de control):
``py -m iso.synthesis.compare generado.iso referencia.iso``
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = ["DELIBERATE_OMISSIONS", "IsoComparison", "NumericDiff", "classify_iso_diff",
           "compare_iso_files"]

# Solo números CON decimales son "valores" tolerables (coordenadas, feeds): los enteros
# (G2/G3, T3, índices ETK, S18000) son parte del ESQUELETO — una diferencia ahí es
# estructural, nunca ruido de milésimas.
_FLOAT_RE = re.compile(r"-?\d+\.\d+")

#: Tolerancia por defecto para el ruido de milésimas del emisor de Maestro (mm).
DEFAULT_TOLERANCE = 0.005

#: Líneas que el converter OMITE a propósito porque Maestro las emite mal formadas y el
#: CNC las rechaza. Al comparar, se descuentan de la referencia y se reportan aparte: la
#: diferencia es deliberada, no un error nuestro.
#:
#: - ``%DONTCARESPEEDV=1``: Maestro la escribe cuando una op posterior tiene multipasada
#:   con conexión a cota de seguridad. El CNC aborta con «Alarma 67: Assegnazione a
#:   registro inesistente» (ejecución real 2026-08-03). El manual de Xilog documenta la
#:   instrucción como ``SET DONTCARE=1`` y ``DONTCARESPEEDV`` no existe en la
#:   configuración de la máquina ⇒ está mal formada. Decisión de Fermín: omitirla.
DELIBERATE_OMISSIONS: tuple[str, ...] = ("%DONTCARESPEEDV=1",)


@dataclass(frozen=True)
class NumericDiff:
    """Un valor numérico que difiere entre referencia y generado (dentro o no de tolerancia)."""

    line_number: int          # 1-based, sobre la referencia
    line_reference: str
    line_generated: str
    value_reference: float
    value_generated: float

    @property
    def delta(self) -> float:
        return abs(self.value_generated - self.value_reference)


@dataclass(frozen=True)
class IsoComparison:
    verdict: str              # "byte_identico" | "funcionalmente_identico" | "diferente"
    numeric_diffs: tuple[NumericDiff, ...] = ()
    structural_issues: tuple[str, ...] = ()
    tolerance: float = DEFAULT_TOLERANCE
    #: líneas de la referencia que el converter omite A PROPÓSITO (ver DELIBERATE_OMISSIONS)
    deliberate_omissions: tuple[str, ...] = ()
    #: comentarios (`% nombre.pgm`) que difieren SOLO en mayúsculas/minúsculas. Dato de
    #: dominio (Fermín, 2026-08-05): los archivos se crean en la PC de oficina técnica y se
    #: postprocesan en la PC del CNC; el case del comentario CAMBIÓ entre las salidas de
    #: producción (Cazaux 2026-01: `% Faja frontal.pgm`, preservado) y las actuales
    #: (2026-05+: `Galceado.pgmx` → `% galceado.pgm`, minusculizado). Ambas son Maestro
    #: real ⇒ es ruido del EMISOR, como las milésimas — no una regla derivable. El
    #: converter sigue al oráculo vivo (minusculiza); acá se clasifica como funcional y
    #: se REPORTA. Solo aplica a líneas de comentario (`% ` con espacio): las asignaciones
    #: de registro (`%Or`, `%ETK`, `%DONTCARESPEEDV`) no llevan espacio y NO se toleran.
    comment_case_diffs: tuple[str, ...] = ()

    @property
    def max_delta(self) -> float:
        return max((d.delta for d in self.numeric_diffs), default=0.0)

    def report(self) -> str:
        lines = [f"veredicto: {self.verdict}"]
        if self.deliberate_omissions:
            lines.append(f"omisiones deliberadas: {len(self.deliberate_omissions)} "
                         f"(línea inválida de Maestro que el CNC rechaza)")
            for omission in self.deliberate_omissions:
                lines.append(f"  omitida: {omission}")
        if self.comment_case_diffs:
            lines.append(f"comentarios con case distinto: {len(self.comment_case_diffs)} "
                         f"(ruido del emisor — ver docstring)")
            for diff in self.comment_case_diffs:
                lines.append(f"  case: {diff}")
        if self.numeric_diffs:
            lines.append(f"deltas numéricos: {len(self.numeric_diffs)} "
                         f"(máximo {self.max_delta:.4f} mm, tolerancia {self.tolerance})")
            for d in self.numeric_diffs:
                lines.append(f"  línea {d.line_number}: {d.value_reference} → "
                             f"{d.value_generated} (Δ{d.delta:.4f})  | {d.line_reference}")
        for issue in self.structural_issues:
            lines.append(f"  estructura: {issue}")
        return "\n".join(lines)


def _lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in text.replace("\r\n", "\n").splitlines()]


def classify_iso_diff(
    generated: str,
    reference: str,
    tolerance: float = DEFAULT_TOLERANCE,
) -> IsoComparison:
    """Clasifica la diferencia entre un ISO generado y su referencia (ver módulo)."""
    gen = _lines(generated)
    ref = _lines(reference)
    if gen == ref:
        return IsoComparison("byte_identico", tolerance=tolerance)

    # Divergencias DELIBERADAS: se descuentan de la referencia y se reportan aparte, para
    # que no contaminen la comparación (no son un error del converter — son líneas que
    # Maestro emite mal formadas y el CNC rechaza).
    omitted = tuple(line for line in ref if line in DELIBERATE_OMISSIONS)
    if omitted:
        ref = [line for line in ref if line not in DELIBERATE_OMISSIONS]
        if gen == ref:
            return IsoComparison("funcionalmente_identico", tolerance=tolerance,
                                 deliberate_omissions=omitted)

    issues: list[str] = []
    diffs: list[NumericDiff] = []
    case_diffs: list[str] = []
    if len(gen) != len(ref):
        issues.append(f"cantidad de líneas distinta (referencia {len(ref)}, "
                      f"generado {len(gen)})")
    for i, (r, g) in enumerate(zip(ref, gen), start=1):
        if r == g:
            continue
        # Comentario con case distinto (`% nombre.pgm`): ruido del emisor entre versiones
        # de Maestro (ver IsoComparison.comment_case_diffs). Solo comentarios reales
        # (`% ` con espacio); los registros `%...=` no llevan espacio y no entran acá.
        if r.startswith("% ") and g.startswith("% ") and r.lower() == g.lower():
            case_diffs.append(f"línea {i}: {r!r} → {g!r}")
            continue
        r_nums = _FLOAT_RE.findall(r)
        g_nums = _FLOAT_RE.findall(g)
        r_skeleton = _FLOAT_RE.sub("#", r)
        g_skeleton = _FLOAT_RE.sub("#", g)
        if r_skeleton != g_skeleton or len(r_nums) != len(g_nums):
            issues.append(f"línea {i}: esqueleto distinto | ref={r!r} gen={g!r}")
            continue
        for rv, gv in zip(r_nums, g_nums):
            if rv == gv:
                continue
            diffs.append(NumericDiff(i, r, g, float(rv), float(gv)))

    functional = (not issues
                  and (diffs or case_diffs)
                  and all(d.delta <= tolerance + 1e-9 for d in diffs))
    return IsoComparison(
        "funcionalmente_identico" if functional else "diferente",
        numeric_diffs=tuple(diffs),
        structural_issues=tuple(issues),
        tolerance=tolerance,
        deliberate_omissions=omitted,
        comment_case_diffs=tuple(case_diffs),
    )


def compare_iso_files(
    generated_path: Path,
    reference_path: Path,
    tolerance: float = DEFAULT_TOLERANCE,
) -> IsoComparison:
    """Compara dos archivos .iso (la referencia en cp1252, como escribe Maestro)."""
    return classify_iso_diff(
        Path(generated_path).read_text(encoding="cp1252"),
        Path(reference_path).read_text(encoding="cp1252"),
        tolerance=tolerance,
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("generated", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    args = parser.parse_args(argv)
    comparison = compare_iso_files(args.generated, args.reference, args.tolerance)
    print(comparison.report())
    return 0 if comparison.verdict != "diferente" else 1


if __name__ == "__main__":
    raise SystemExit(main())
