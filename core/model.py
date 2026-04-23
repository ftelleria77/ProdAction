"""Definiciones de modelo de datos para piezas, locales, módulos y proyectos."""

from dataclasses import dataclass, field
from typing import List, Optional


PIECE_TYPE_ORDER: list = [
    "F1", "F2", "T", "B", "R", "A1", "A2", "D1", "D2", "S", "H", "Q", "G", "C1", "C2", "E",
]

PIECE_GRAIN_CODE_NONE = "0"
PIECE_GRAIN_CODE_HEIGHT = "1"
PIECE_GRAIN_CODE_WIDTH = "2"

PIECE_GRAIN_CODE_LABELS = {
    PIECE_GRAIN_CODE_NONE: "Sin veta",
    PIECE_GRAIN_CODE_HEIGHT: "Alto",
    PIECE_GRAIN_CODE_WIDTH: "Ancho",
}
PIECE_EN_JUEGO_OBSERVATION = "En-Juego"


def normalize_piece_grain_direction(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"0", "0 - sin veta", "sin veta", "no veta"}:
        return PIECE_GRAIN_CODE_NONE
    if raw in {"1", "1 - longitudinal", "a lo largo", "longitudinal", "alto"}:
        return PIECE_GRAIN_CODE_HEIGHT
    if raw in {"2", "2 - transversal", "a lo ancho", "transversal", "ancho"}:
        return PIECE_GRAIN_CODE_WIDTH
    if "sin veta" in raw or "no veta" in raw:
        return PIECE_GRAIN_CODE_NONE
    if "a lo largo" in raw or "longitudinal" in raw:
        return PIECE_GRAIN_CODE_HEIGHT
    if "a lo ancho" in raw or "transversal" in raw:
        return PIECE_GRAIN_CODE_WIDTH
    return PIECE_GRAIN_CODE_NONE


def piece_grain_direction_label(value) -> str:
    normalized = normalize_piece_grain_direction(value)
    return PIECE_GRAIN_CODE_LABELS.get(normalized, PIECE_GRAIN_CODE_LABELS[PIECE_GRAIN_CODE_NONE])


def normalize_piece_observations(value) -> str:
    raw_text = str(value or "").replace("\r", "\n")
    parts: list[str] = []
    seen: set[str] = set()
    for raw_part in raw_text.replace("|", "\n").split("\n"):
        cleaned = raw_part.strip()
        if not cleaned:
            continue
        normalized_key = cleaned.casefold()
        if normalized_key in seen:
            continue
        seen.add(normalized_key)
        parts.append(cleaned)
    return " | ".join(parts)


def set_piece_en_juego_observation(observations, enabled: bool) -> str:
    normalized = normalize_piece_observations(observations)
    entries = [entry.strip() for entry in normalized.split("|") if entry.strip()]
    entries = [entry for entry in entries if entry.casefold() != PIECE_EN_JUEGO_OBSERVATION.casefold()]
    if enabled:
        entries.append(PIECE_EN_JUEGO_OBSERVATION)
    return normalize_piece_observations(" | ".join(entries))


def build_piece_observations_display(observations, program_note=None) -> str:
    values = []
    normalized_observations = normalize_piece_observations(observations)
    normalized_program_note = str(program_note or "").strip()
    if normalized_observations:
        values.append(normalized_observations)
    if normalized_program_note:
        values.append(normalized_program_note)
    return " | ".join(values)


@dataclass
class Piece:
    id: str
    width: float
    height: float
    thickness: Optional[float] = None
    quantity: int = 1
    color: Optional[str] = None
    grain_direction: Optional[str] = None
    name: Optional[str] = None
    module_name: str = ""
    cnc_source: Optional[str] = None
    f6_source: Optional[str] = None
    piece_type: Optional[str] = None
    program_width: Optional[float] = None
    program_height: Optional[float] = None
    program_thickness: Optional[float] = None


@dataclass
class ModuleData:
    name: str
    path: str
    locale_name: str = ""
    relative_path: str = ""
    quantity: int = 1
    pieces: List[Piece] = field(default_factory=list)
    is_manual: bool = False


@dataclass
class LocaleData:
    name: str
    path: str
    modules_count: int = 0


@dataclass
class Project:
    name: str
    root_directory: str
    project_data_file: str = "project.json"
    client: str = ""
    created_at: str = ""
    locales: List[LocaleData] = field(default_factory=list)
    modules: List[ModuleData] = field(default_factory=list)
    output_directory: Optional[str] = None

    @property
    def local(self) -> str:
        return self.locales[0].name if self.locales else ""

    @property
    def locales_count(self) -> int:
        return len(self.locales)

    def to_dict(self):
        """Convierte el proyecto al formato persistido en disco."""
        return {
            "project_name": self.name,
            "client_name": self.client,
            "created_at": self.created_at,
            "locales": [
                {
                    "name": locale.name,
                    "path": locale.path,
                    "modules_count": locale.modules_count,
                }
                for locale in self.locales
            ],
        }
