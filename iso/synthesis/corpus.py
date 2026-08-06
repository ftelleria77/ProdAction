"""Corrida de corpus: convierte un árbol de `.pgmx` y clasifica cada uno contra su ISO.

Es la herramienta del «ensayo general» y del set de control final del plan de cierre
(`iso/docs/plan_cierre_converter.md`): recorre un árbol de `.pgmx`, convierte cada uno con
`iso.synthesis.convert`, busca su ISO de referencia (postprocesado por Maestro) y clasifica
con `compare.classify_iso_diff`. Los rechazos fail-loud NO son errores: son la guarda
diciendo qué fixture falta — el resumen los agrupa por guarda para priorizar lotes.

Veredictos por archivo:

- ``byte_identico`` / ``funcionalmente_identico`` / ``diferente`` — de `compare.py`.
- ``fail_loud`` — el converter rechazó con `UnsupportedOperationError` (guarda con nombre).
- ``error`` — cualquier otra excepción (eso SÍ es un bug nuestro).
- ``sin_iso`` — no hay ISO de referencia para ese `.pgmx`.
- ``ambiguo`` — más de un ISO candidato con el mismo nombre y ninguno en la ruta espejo.

Apareo `.pgmx` ↔ `.iso`: primero por RUTA ESPEJO (misma ruta relativa bajo la raíz de ISOs,
la convención de los lotes N en S:/P:); si no, por nombre único en todo el árbol de ISOs.

Uso CLI::

    py -m iso.synthesis.corpus <raiz_pgmx> <raiz_iso> [--out reporte.jsonl] [--tolerance F]

El detalle por archivo va al JSONL (`--out`); el resumen agrupado, a stdout.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .compare import DEFAULT_TOLERANCE, classify_iso_diff
from ._validation import UnsupportedOperationError

__all__ = ["CorpusResult", "CorpusReport", "run_corpus"]

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


@dataclass(frozen=True)
class CorpusResult:
    pgmx: Path
    iso: Path | None
    verdict: str
    detail: str = ""          # mensaje de guarda / issue estructural / resumen de deltas
    group_key: str = ""       # detalle con números normalizados, para agrupar en el resumen

    def to_json(self) -> str:
        return json.dumps({
            "pgmx": str(self.pgmx), "iso": None if self.iso is None else str(self.iso),
            "verdict": self.verdict, "detail": self.detail,
        }, ensure_ascii=False)


@dataclass
class CorpusReport:
    results: list[CorpusResult] = field(default_factory=list)
    elapsed_s: float = 0.0

    def counts(self) -> Counter:
        return Counter(r.verdict for r in self.results)

    def grouped(self, verdict: str, top: int = 15) -> list[tuple[int, str]]:
        counter = Counter(r.group_key or r.detail for r in self.results
                          if r.verdict == verdict and (r.group_key or r.detail))
        return [(n, key) for key, n in counter.most_common(top)]

    def summary(self) -> str:
        counts = self.counts()
        total = len(self.results)
        lines = [f"corpus: {total} .pgmx en {self.elapsed_s:.0f}s"]
        for verdict in ("byte_identico", "funcionalmente_identico", "diferente",
                        "fail_loud", "error", "sin_iso", "ambiguo"):
            if counts.get(verdict):
                lines.append(f"  {verdict}: {counts[verdict]}")
        for verdict, title in (("fail_loud", "guardas golpeadas"),
                               ("diferente", "diferencias"),
                               ("error", "errores")):
            grouped = self.grouped(verdict)
            if grouped:
                lines.append(f"-- {title} (top {len(grouped)}) --")
                lines.extend(f"  {n:4d}× {key}" for n, key in grouped)
        return "\n".join(lines)


def _group_key(detail: str) -> str:
    """Detalle con números y rutas normalizados: agrupa '3 operaciones' con '5 operaciones'."""
    head = detail.splitlines()[0] if detail else ""
    return _NUM_RE.sub("#", head)[:160]


def _index_isos(iso_root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in iso_root.rglob("*.iso"):
        index.setdefault(path.stem.lower(), []).append(path)
    return index


def _find_reference(pgmx: Path, pgmx_root: Path, iso_root: Path,
                    index: dict[str, list[Path]]) -> tuple[Path | None, str]:
    mirror = iso_root / pgmx.relative_to(pgmx_root).with_suffix(".iso")
    if mirror.exists():
        return mirror, ""
    candidates = index.get(pgmx.stem.lower(), [])
    if len(candidates) == 1:
        return candidates[0], ""
    if not candidates:
        return None, "sin_iso"
    return None, "ambiguo"


def run_corpus(pgmx_root: Path, iso_root: Path,
               tolerance: float = DEFAULT_TOLERANCE,
               progress=None) -> CorpusReport:
    from . import convert  # import tardío: convert carga machine config/catálogo

    started = time.monotonic()
    report = CorpusReport()
    index = _index_isos(iso_root)
    pgmx_files = sorted(pgmx_root.rglob("*.pgmx"))
    for i, pgmx in enumerate(pgmx_files, start=1):
        if progress is not None and i % 25 == 0:
            progress(f"{i}/{len(pgmx_files)}")
        reference, missing = _find_reference(pgmx, pgmx_root, iso_root, index)
        if reference is None:
            report.results.append(CorpusResult(pgmx, None, missing))
            continue
        try:
            generated = convert(pgmx)
        except UnsupportedOperationError as guard:
            detail = str(guard)
            report.results.append(CorpusResult(
                pgmx, reference, "fail_loud", detail, _group_key(detail)))
            continue
        except Exception as error:  # noqa: BLE001 — un bug nuestro: se reporta, no se corta
            detail = f"{type(error).__name__}: {error}"
            report.results.append(CorpusResult(
                pgmx, reference, "error", detail, _group_key(detail)))
            continue
        comparison = classify_iso_diff(
            generated, reference.read_text(encoding="cp1252"), tolerance=tolerance)
        if comparison.verdict == "diferente":
            issue = (comparison.structural_issues[0] if comparison.structural_issues
                     else f"deltas numéricos: {len(comparison.numeric_diffs)} "
                          f"(máx {comparison.max_delta:.4f})")
            report.results.append(CorpusResult(
                pgmx, reference, "diferente", issue, _group_key(issue)))
        else:
            detail = ""
            if comparison.verdict == "funcionalmente_identico":
                detail = (f"deltas: {len(comparison.numeric_diffs)} "
                          f"(máx {comparison.max_delta:.4f}); "
                          f"omisiones deliberadas: {len(comparison.deliberate_omissions)}")
            report.results.append(CorpusResult(pgmx, reference, comparison.verdict, detail))
    report.elapsed_s = time.monotonic() - started
    return report


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pgmx_root", type=Path)
    parser.add_argument("iso_root", type=Path)
    parser.add_argument("--out", type=Path, default=None,
                        help="JSONL con el detalle por archivo")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    args = parser.parse_args(argv)

    report = run_corpus(args.pgmx_root, args.iso_root, tolerance=args.tolerance,
                        progress=lambda msg: print(msg, file=sys.stderr, flush=True))
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8") as handle:
            for result in report.results:
                handle.write(result.to_json() + "\n")
    print(report.summary())
    counts = report.counts()
    return 1 if counts.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
