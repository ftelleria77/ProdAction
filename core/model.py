"""Definiciones de modelo de datos para piezas, módulos y proyectos."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


PIECE_TYPE_ORDER: list = [
    "F1", "F2", "T", "B", "R", "A1", "A2", "D1", "D2", "S", "H", "Q", "G", "C1", "C2", "E",
]


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
    pieces: List[Piece] = field(default_factory=list)
    is_manual: bool = False


@dataclass
class Project:
    name: str
    root_directory: str
    client: str = ""
    local: str = ""
    created_at: str = ""
    modules: List[ModuleData] = field(default_factory=list)
    output_directory: Optional[str] = None

    def to_dict(self):
        """Convertir objeto de proyecto a diccionario.

        Este método es usado para serializar y guardar en JSON.
        """
        return {
            "name": self.name,
            "root_directory": self.root_directory,
            "client": self.client,
            "local": self.local,
            "created_at": self.created_at,
            "output_directory": self.output_directory,
            "modules": [
                {
                    "name": m.name,
                    "path": m.path,
                    "pieces": [p.__dict__ for p in m.pieces],
                }
                for m in self.modules
            ],
        }
