"""Lectura de la config de máquina (snapshot Xilog Plus) para el converter.

Las posiciones/limites de máquina que entran en las fórmulas de traza/recorrido NO deben
ser constantes internas: salen del snapshot real en `iso/data/machine_config/`. Este módulo
lee los `.cfg` con clave (INI-style: secciones `[name]`, `KEY = value`), p. ej. `Params.cfg`.

Nota: `spindles.cfg`/`oheads.cfg` son dumps posicionales sin clave (no INI) → no se parsean
acá todavía; sus offsets (shf) siguen medidos hasta tener un mapeo confiable.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_CFG_DIR = (
    Path(__file__).resolve().parents[1]
    / "data" / "machine_config" / "snapshot" / "xilog_plus" / "Cfg"
)


@lru_cache(maxsize=None)
def _ini(filename: str) -> dict[tuple[str, str], str]:
    """Parsea un .cfg INI-style → {(seccion, clave): valor}. Primer valor gana
    (hay secciones repetidas, p. ej. dos grupos [ax0..ax10])."""
    out: dict[tuple[str, str], str] = {}
    section = ""
    text = (_CFG_DIR / filename).read_text(encoding="latin-1", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif "=" in line:
            key, value = line.split("=", 1)
            out.setdefault((section, key.strip()), value.strip())
    return out


def param_float(filename: str, section: str, key: str) -> float:
    """Valor numérico de una clave de un .cfg de máquina."""
    raw = _ini(filename).get((section, key))
    if raw is None:
        raise KeyError(f"{filename}[{section}] {key} no está en el snapshot de config")
    return float(raw)


# spindles.cfg: dump posicional de los Mandriles del Grupo Taladradora (la GUI de Xilog Plus
# lo muestra como "xilog3.cfg → SPINDLES"). Estructura regular (verificada con la GUI para los
# mandriles 58-61): header de 44 líneas + un bloque de 42 líneas por mandril; dentro del bloque,
# 21 enteros (Habilitación..Cabeza, reservados) y luego los floats, con Offset X/Y/Z en los
# índices 21/22/23. El mandril N (1-based) = nº de husillo (para laterales coincide con ETK[6]).
_SPINDLE_HEADER = 44
_SPINDLE_BLOCK = 42
_SPINDLE_OFFXYZ = 21  # índice de OffsetX dentro del bloque (OffsetY/Z a +1/+2)


@lru_cache(maxsize=1)
def _spindle_lines() -> list[str]:
    return (_CFG_DIR / "spindles.cfg").read_text(encoding="latin-1", errors="replace").splitlines()


def spindle_offset(mandril: int) -> tuple[float, float, float]:
    """(OffsetX, OffsetY, OffsetZ) del mandril en spindles.cfg. El SHF de máquina es el opuesto:
    shf = -offset (verificado: shf_* = -(Offset X/Y/Z), mandril = ETK[6] en top 1-7 y side 58-61)."""
    lines = _spindle_lines()
    base = _SPINDLE_HEADER + (mandril - 1) * _SPINDLE_BLOCK + _SPINDLE_OFFXYZ
    return (float(lines[base]), float(lines[base + 1]), float(lines[base + 2]))


def spindle_shf(mandril: int) -> tuple[float, float, float]:
    """SHF de máquina del mandril = -(Offset X/Y/Z), con el cero normalizado (evita -0.0,
    que formatearía como '-0.000' y rompería el byte-match)."""
    return tuple(-v + 0.0 for v in spindle_offset(mandril))  # type: ignore[return-value]


# pheads.cfg: Cabezas Operadoras (PHEADS) — la cabeza del router/electromandril vive acá.
# Dump posicional regular (verificado con la GUI): bloque de 104 líneas/cabeza; dentro del
# bloque, "Configuración 0 (Eje X/Y/Z)" en los índices 0-based 136/137/138 de la 1ª cabeza
# (= header+ints). El SHF del router = -(Configuración 0) de su cabeza (mismo patrón que mandriles).
_PHEAD_BLOCK = 104
_PHEAD_CONFIG0 = 136  # índice 0-based de "Configuración 0 Eje X" para la Cabeza 1


@lru_cache(maxsize=1)
def _pheads_lines() -> list[str]:
    return (_CFG_DIR / "pheads.cfg").read_text(encoding="latin-1", errors="replace").splitlines()


def phead_float(cabeza: int, idx: int) -> float:
    """Float en el índice `idx` del bloque de la cabeza (0-based desde Configuración 0 Eje X).
    Orden: Config0 X/Y/Z = 0/1/2, Config1 = 3/4/5, Config2 = 6/7/8, Config3 = 9/10/11,
    ConfigL = 12/13/14, Carrera H1 = 15, H2 = 16, cota angular = 17, ..."""
    lines = _pheads_lines()
    return float(lines[_PHEAD_CONFIG0 + (cabeza - 1) * _PHEAD_BLOCK + idx])


def phead_shf(cabeza: int) -> tuple[float, float, float]:
    """SHF de una cabeza operadora = -(Configuración 0 Eje X/Y/Z) de pheads.cfg, cero normalizado."""
    return tuple(-phead_float(cabeza, i) + 0.0 for i in range(3))  # type: ignore[return-value]


# fields.cfg: Campos de trabajo (FIELDS) — la cama partida en áreas. Dump posicional regular:
# header de 30 líneas + un bloque de 30 líneas por campo (14 enteros + 15 floats + 1 letra de
# etiqueta). Dentro del bloque, el origen del campo (X, Y) son los 2 primeros floats (índices
# 14/15 del bloque) y la etiqueta (A..P) es la última línea (índice 29). Hay 16 campos (A-P);
# las áreas de trabajo se nombran por pares (AB/DC/EF/HG) y toman el origen del PRIMER campo del
# par. ⚠️ Solo HG está calibrado válido hoy (ver bitácora de la máquina); EF/AB/DC conservan la
# calibración inicial, invalidada por intervenciones técnicas → no usar sus orígenes aún.
_FIELDS_HEADER = 30
_FIELDS_BLOCK = 30
_FIELDS_ORIGIN = 14  # índice de OrigenX dentro del bloque (OrigenY a +1); etiqueta en +15


@lru_cache(maxsize=1)
def _fields_lines() -> list[str]:
    return (_CFG_DIR / "fields.cfg").read_text(encoding="latin-1", errors="replace").splitlines()


def field_origin(area: str) -> tuple[float, float]:
    """Origen (X, Y) en mm del área de trabajo, leído de fields.cfg. El área (AB/DC/EF/HG) toma
    el origen del PRIMER campo del par (su 1ª letra: HG→H, EF→E, AB→A, DC→D)."""
    field = area[0].upper()
    idx = ord(field) - ord("A")  # A=0 .. P=15
    lines = _fields_lines()
    base = _FIELDS_HEADER + idx * _FIELDS_BLOCK
    # La etiqueta viene rellenada con \x03 (ETX): "H\x03\x03..." → quedarse con la 1ª letra.
    label = lines[base + _FIELDS_ORIGIN + 15].replace("\x03", "").strip()
    if label != field:
        raise ValueError(
            f"fields.cfg: esperaba el campo '{field}' en el bloque {idx}, encontré '{label}'")
    return (float(lines[base + _FIELDS_ORIGIN]), float(lines[base + _FIELDS_ORIGIN + 1]))
