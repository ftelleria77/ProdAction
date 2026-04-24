"""Transformaciones geometricas para la composicion En-Juego.

Este modulo no lee ni escribe `.pgmx`: solo mueve specs ya adaptadas desde el
sistema local de una pieza al sistema local de la composicion En-Juego.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Union

from tools import synthesize_pgmx as sp


TransformableSpec = Union[
    sp.LineMillingSpec,
    sp.PolylineMillingSpec,
    sp.CircleMillingSpec,
    sp.DrillingSpec,
]


@dataclass(frozen=True)
class EnJuegoTransform:
    """Transforma coordenadas CAM locales hacia la composicion.

    `origin_x_mm` y `origin_y_mm` son la ubicacion, ya rotada y normalizada, del
    punto `(0, 0)` de la pieza original dentro del sistema local En-Juego.
    """

    origin_x_mm: float
    origin_y_mm: float
    rotation_deg: float = 0.0

    def point(self, x_value: float, y_value: float) -> tuple[float, float]:
        radians = math.radians(float(self.rotation_deg))
        cos_value = math.cos(radians)
        sin_value = math.sin(radians)
        x_float = float(x_value)
        y_float = float(y_value)
        return (
            float(self.origin_x_mm) + (x_float * cos_value) + (y_float * sin_value),
            float(self.origin_y_mm) - (x_float * sin_value) + (y_float * cos_value),
        )


def prefixed_feature_name(feature_name: str, prefix: str = "") -> str:
    cleaned_name = str(feature_name or "").strip() or "Fresado"
    cleaned_prefix = str(prefix or "").strip()
    if not cleaned_prefix:
        return cleaned_name
    return f"{cleaned_prefix} - {cleaned_name}"


def transform_line_milling_spec(
    spec: sp.LineMillingSpec,
    transform: EnJuegoTransform,
    *,
    feature_name_prefix: str = "",
) -> sp.LineMillingSpec:
    start_x, start_y = transform.point(spec.start_x, spec.start_y)
    end_x, end_y = transform.point(spec.end_x, spec.end_y)
    return replace(
        spec,
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
        feature_name=prefixed_feature_name(spec.feature_name, feature_name_prefix),
    )


def transform_polyline_milling_spec(
    spec: sp.PolylineMillingSpec,
    transform: EnJuegoTransform,
    *,
    feature_name_prefix: str = "",
) -> sp.PolylineMillingSpec:
    return replace(
        spec,
        points=tuple(transform.point(point_x, point_y) for point_x, point_y in spec.points),
        feature_name=prefixed_feature_name(spec.feature_name, feature_name_prefix),
    )


def transform_circle_milling_spec(
    spec: sp.CircleMillingSpec,
    transform: EnJuegoTransform,
    *,
    feature_name_prefix: str = "",
) -> sp.CircleMillingSpec:
    center_x, center_y = transform.point(spec.center_x, spec.center_y)
    return replace(
        spec,
        center_x=center_x,
        center_y=center_y,
        feature_name=prefixed_feature_name(spec.feature_name, feature_name_prefix),
    )


def transform_drilling_spec(
    spec: sp.DrillingSpec,
    transform: EnJuegoTransform,
    *,
    feature_name_prefix: str = "",
) -> sp.DrillingSpec:
    center_x, center_y = transform.point(spec.center_x, spec.center_y)
    return replace(
        spec,
        center_x=center_x,
        center_y=center_y,
        feature_name=prefixed_feature_name(spec.feature_name, feature_name_prefix),
    )


def transform_supported_spec(
    spec: TransformableSpec,
    transform: EnJuegoTransform,
    *,
    feature_name_prefix: str = "",
) -> TransformableSpec:
    if isinstance(spec, sp.LineMillingSpec):
        return transform_line_milling_spec(
            spec,
            transform,
            feature_name_prefix=feature_name_prefix,
        )
    if isinstance(spec, sp.PolylineMillingSpec):
        return transform_polyline_milling_spec(
            spec,
            transform,
            feature_name_prefix=feature_name_prefix,
        )
    if isinstance(spec, sp.CircleMillingSpec):
        return transform_circle_milling_spec(
            spec,
            transform,
            feature_name_prefix=feature_name_prefix,
        )
    if isinstance(spec, sp.DrillingSpec):
        return transform_drilling_spec(
            spec,
            transform,
            feature_name_prefix=feature_name_prefix,
        )
    raise TypeError(f"Spec no soportado para transformacion En-Juego: {type(spec).__name__}")
