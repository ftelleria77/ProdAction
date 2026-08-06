r"""Ciclo de refresco de la configuración de máquina (F0.7 del plan de cierre).

REQUISITO (Fermín, 2026-08-04): el converter lee la config de máquina y de herramientas
SIEMPRE de los archivos extraídos de la PC del CNC. Tras una calibración, un cambio de
configuración o el alta de una herramienta, esos archivos cambian: se re-extraen y se
sobreescriben. Sobreescribir = converter actualizado, sin tocar código.

Las fuentes en la PC del CNC se ven desde esta máquina como los shares `S:` (VPN
`fabrica.somosmobile.com.ar`). Este módulo automatiza el ciclo completo:

    py -m iso.machine_config check     ¿cambió algo en S: respecto del snapshot?
    py -m iso.machine_config refresh   copia S: → snapshot, regenera manifest.csv y
                                       pgmx/data/tool_catalog.csv

`tool_catalog.csv` era la ÚNICA pieza derivada A MANO del ciclo (auditoría 2026-08-04):
sus 17 columnas numéricas se regeneran del `def.tlgx` del snapshot (verificado 0
diferencias contra el CSV curado, 19/19 herramientas). Las columnas `type` y
`description` NO existen en el def.tlgx — son vocabulario de Fermín (regla 3; `type`
alimenta la validación «Sierra Vertical X» del canal): se PRESERVAN del CSV existente,
y una herramienta NUEVA sale con esas columnas vacías + un aviso para que Fermín las
complete (fail-loud suave: el canal rechaza una sierra sin tipo).

El manifest (SHA256 por archivo) FECHA cada estado de config: los ISO de referencia
valen para la config con la que se postprocesaron (riesgo 7 del plan).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parent / "data" / "machine_config" / "snapshot"
MANIFEST = SNAPSHOT / "manifest.csv"
TOOL_CATALOG = Path(__file__).resolve().parents[1] / "pgmx" / "data" / "tool_catalog.csv"
DEF_TLGX = SNAPSHOT / "maestro" / "Tlgx" / "def.tlgx"

#: (raíz en la PC del CNC vía S:, subcarpeta del snapshot, subrutas cubiertas)
SCOPE: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (r"S:\Maestro\Cfgx", "maestro/Cfgx", ("",)),
    (r"S:\Maestro\Tlgx", "maestro/Tlgx", ("",)),
    (r"S:\Xilog Plus", "xilog_plus", ("axis.ini", "Cfg", "Job")),
)

CSV_COLUMNS = (
    "tool_id", "name", "description", "type", "holder_key",
    "overall_assembly_diameter", "overall_assembly_length", "diameter", "pilot_length",
    "sinking_length", "tool_offset_length",
    "descent_speed_min", "descent_speed_std", "descent_speed_max",
    "feed_rate_min", "feed_rate_std", "feed_rate_max",
    "spindle_speed_min", "spindle_speed_std", "spindle_speed_max",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _scope_files(root: Path, subpaths: tuple[str, ...]):
    for sub in subpaths:
        target = root / sub if sub else root
        if target.is_file():
            yield target
        elif target.is_dir():
            files = (p for p in target.rglob("*") if p.is_file()) if sub else (
                p for p in target.iterdir() if p.is_file())
            yield from sorted(files)


def check(source_side: bool = True) -> list[str]:
    """Compara los archivos (de S: si `source_side`, si no del snapshot local) contra el
    manifest. Devuelve las diferencias como líneas de reporte."""
    manifest = {str(Path(row["snapshot_root"]) / row["relative_path"]).replace("/", "\\"): row
                for row in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))}
    report: list[str] = []
    seen: set[str] = set()
    for source_root, snap_sub, subpaths in SCOPE:
        base = Path(source_root) if source_side else (SNAPSHOT / snap_sub)
        if not base.exists():
            report.append(f"FALTA la raíz {base} (¿VPN caída?)" if source_side
                          else f"FALTA {base} en el snapshot")
            continue
        for path in _scope_files(base, subpaths):
            rel_manifest = _manifest_key(snap_sub, path.relative_to(base))
            seen.add(rel_manifest)
            row = manifest.get(rel_manifest)
            if row is None:
                report.append(f"NUEVO: {rel_manifest}")
            elif _sha256(path) != row["sha256"].upper():
                report.append(f"CAMBIÓ: {rel_manifest}")
    for rel in sorted(set(manifest) - seen):
        report.append(f"DESAPARECIÓ: {rel}")
    return report


def _manifest_key(snap_sub: str, rel: Path) -> str:
    # El manifest histórico usa snapshot_root maestro_cfgx/maestro_tlgx/xilog_plus con
    # relative_path estilo Windows. Se mapea el layout REAL (maestro/Cfgx…) a esas claves.
    legacy = {"maestro/Cfgx": "maestro_cfgx", "maestro/Tlgx": "maestro_tlgx",
              "xilog_plus": "xilog_plus"}[snap_sub]
    del legacy  # la clave nueva es directamente la ruta relativa al snapshot:
    return str(Path(snap_sub) / rel).replace("/", "\\")


def refresh() -> int:
    """Copia S: → snapshot (sobreescribe), regenera manifest y tool_catalog.csv."""
    copied = 0
    rows = []
    for source_root, snap_sub, subpaths in SCOPE:
        base = Path(source_root)
        if not base.exists():
            print(f"ERROR: no existe {base} — ¿VPN '{'fabrica.somosmobile.com.ar'}' caída?")
            return 1
        for path in _scope_files(base, subpaths):
            rel = path.relative_to(base)
            dest = SNAPSHOT / snap_sub / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            copied += 1
            rows.append({
                "source_root": source_root,
                "snapshot_root": snap_sub,
                "relative_path": str(rel).replace("/", "\\"),
                "bytes": dest.stat().st_size,
                "sha256": _sha256(dest),
            })
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "source_root", "snapshot_root", "relative_path", "bytes", "sha256"),
            quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    print(f"snapshot: {copied} archivos copiados; manifest regenerado")
    avisos = regenerate_tool_catalog()
    for aviso in avisos:
        print(aviso)
    return 0


def tool_rows_from_tlgx(tlgx_path: Path = DEF_TLGX) -> dict[str, dict[str, str]]:
    """Columnas NUMÉRICAS del catálogo, por herramienta, desde el def.tlgx (0 diferencias
    contra el CSV curado — verificado 2026-08-05, 19/19)."""
    root = ET.fromstring(tlgx_path.read_text(encoding="utf-8-sig"))
    result: dict[str, dict[str, str]] = {}
    for tool in root:
        obj = tool.find(".//{*}ObjectType")
        if obj is None or not (obj.text or "").endswith("CuttingTool"):
            continue
        def leaf(name: str) -> str:
            node = tool.find(f".//{{*}}{name}")
            return "" if node is None or node.text is None else node.text.strip()
        tech = tool.find(".//{*}ToolTechnology")
        def rango(grupo: str, campo: str) -> str:
            node = tech.find(f".//{{*}}{grupo}/{{*}}{campo}")
            return "" if node is None or node.text is None else node.text.strip()
        name = leaf("Name")
        result[name] = {
            "tool_id": leaf("ID"),
            "name": name,
            "holder_key": tool.find(".//{*}ToolKey/{*}Key").text.strip(),
            "overall_assembly_diameter": leaf("OverallAssemblyDiameter"),
            "overall_assembly_length": leaf("OverallAssemblyLength"),
            "diameter": leaf("Diameter"),
            "pilot_length": leaf("PilotLength"),
            "sinking_length": leaf("SinkingLength"),
            "tool_offset_length": leaf("ToolOffsetLength"),
            "descent_speed_min": rango("DescentSpeed", "Minimum"),
            "descent_speed_std": rango("DescentSpeed", "Standard"),
            "descent_speed_max": rango("DescentSpeed", "Maximum"),
            "feed_rate_min": rango("FeedRate", "Minimum"),
            "feed_rate_std": rango("FeedRate", "Standard"),
            "feed_rate_max": rango("FeedRate", "Maximum"),
            "spindle_speed_min": rango("SpindleSpeed", "Minimum"),
            "spindle_speed_std": rango("SpindleSpeed", "Standard"),
            "spindle_speed_max": rango("SpindleSpeed", "Maximum"),
        }
    return result


def regenerate_tool_catalog(tlgx_path: Path = DEF_TLGX,
                            catalog_path: Path = TOOL_CATALOG) -> list[str]:
    """Reescribe el catálogo: numéricos del def.tlgx + type/description PRESERVADOS del
    CSV existente (vocabulario de Fermín, no derivable del XML). Devuelve avisos."""
    xml_rows = tool_rows_from_tlgx(tlgx_path)
    curated: dict[str, dict[str, str]] = {}
    if catalog_path.exists():
        curated = {row["name"]: row for row in
                   csv.DictReader(catalog_path.open(encoding="utf-8-sig"))}
    avisos: list[str] = []
    out_rows = []
    for name, numeric in xml_rows.items():
        prev = curated.get(name, {})
        row = dict(numeric)
        row["description"] = prev.get("description", "")
        row["type"] = prev.get("type", "")
        if not prev:
            avisos.append(f"AVISO: herramienta NUEVA '{name}' sin type/description — "
                          f"completarlos en {catalog_path.name} (vocabulario de la UI, "
                          f"regla 3; el canal exige type='Sierra Vertical X').")
        out_rows.append(row)
    for name in set(curated) - set(xml_rows):
        avisos.append(f"AVISO: la herramienta '{name}' del catálogo ya NO está en "
                      f"def.tlgx — se quita del CSV.")
    # utf-8 SIN BOM: el archivo curado original no lo lleva (el lector usa utf-8-sig,
    # que tolera ambos) — así la regeneración sin cambios es byte-idéntica y git queda mudo.
    with catalog_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(out_rows)
    avisos.append(f"tool_catalog.csv regenerado: {len(out_rows)} herramientas")
    return avisos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="reporta drift entre S: y el snapshot (no toca nada)")
    sub.add_parser("refresh", help="copia S: -> snapshot y regenera manifest + catálogo")
    args = parser.parse_args(argv)
    if args.cmd == "check":
        report = check(source_side=True)
        if not report:
            print("sin drift: S: coincide con el snapshot")
            return 0
        print("\n".join(report))
        return 1
    return refresh()


if __name__ == "__main__":
    raise SystemExit(main())
