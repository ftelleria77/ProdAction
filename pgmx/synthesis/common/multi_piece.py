"""XML manipulation helpers for multi-piece PGMX synthesis.

These helpers operate directly on the XML tree and are namespace-agnostic.
They are intentionally free of PieceSpec to avoid circular imports with program.py.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from contextlib import contextmanager
from copy import deepcopy
from typing import Generator

from .xml import (
    PARAMETRIC_NS,
    XSD_NS,
    XSI_NS,
    _append_key,
    _append_node,
    _compact_number,
    _qname,
    _reserve_ids,
    _set_text,
    _set_xmlns,
    _text,
)

__all__ = [
    "_active_workpiece_ctx",
    "_add_piece_to_xml",
    "_plane_suffix_name",
]

_CANONICAL_PLANES = ("Top", "Right", "Left", "Front", "Back", "Bottom")


def _plane_suffix_name(canonical_name: str, piece_index: int) -> str:
    """Nombre de display del plano para pieza N (1-based).

    Piece 1 → 'Top', piece 2 → 'Top(1)', piece 3 → 'Top(2)', etc.
    """
    return canonical_name if piece_index == 1 else f"{canonical_name}({piece_index - 1})"


def _plane_placement_spec(
    plane_type: str, length: float, width: float, depth: float
) -> tuple[float, float, float, float, float]:
    """Returns (x_dim, y_dim, x_origin, y_origin, z_origin) for the given plane type."""
    specs = {
        "Top":    (length, width,  0.0,    0.0,   depth),
        "Bottom": (length, width,  0.0,    width,  0.0),
        "Right":  (width,  depth,  length, 0.0,   0.0),
        "Left":   (width,  depth,  0.0,    width,  0.0),
        "Front":  (length, depth,  0.0,    0.0,   0.0),
        "Back":   (length, depth,  length, width,  0.0),
    }
    return specs[plane_type]


@contextmanager
def _active_workpiece_ctx(
    root: ET.Element,
    workpiece_id: str,
) -> Generator[None, None, None]:
    """Temporarily moves the target WorkPiece and its Planes to the front.

    This allows all existing _append_* functions — which call _workpiece_ref(root)
    and _find_plane_ref(root, ...) on the first matching element — to correctly
    target the given piece without modification.
    """
    workpieces_node = root.find("./{*}Workpieces")
    planes_node = root.find("./{*}Planes")

    original_workpieces = list(workpieces_node) if workpieces_node is not None else []
    original_planes = list(planes_node) if planes_node is not None else []

    target_wp = next(
        (wp for wp in original_workpieces if _text(wp, "./{*}Key/{*}ID") == workpiece_id),
        None,
    )
    needs_wp_reorder = (
        target_wp is not None
        and bool(original_workpieces)
        and original_workpieces[0] is not target_wp
    )
    if needs_wp_reorder and workpieces_node is not None:
        for child in list(workpieces_node):
            workpieces_node.remove(child)
        workpieces_node.append(target_wp)
        for child in original_workpieces:
            if child is not target_wp:
                workpieces_node.append(child)

    target_planes = [
        p for p in original_planes if _text(p, "./{*}WorkpieceID/{*}ID") == workpiece_id
    ]
    other_planes = [p for p in original_planes if p not in target_planes]
    needs_plane_reorder = bool(target_planes) and (
        not original_planes or original_planes[0] not in target_planes
    )
    if needs_plane_reorder and planes_node is not None:
        for child in list(planes_node):
            planes_node.remove(child)
        for plane in target_planes:
            planes_node.append(plane)
        for plane in other_planes:
            planes_node.append(plane)

    try:
        yield
    finally:
        if needs_wp_reorder and workpieces_node is not None:
            for child in list(workpieces_node):
                workpieces_node.remove(child)
            for child in original_workpieces:
                workpieces_node.append(child)
        if needs_plane_reorder and planes_node is not None:
            for child in list(planes_node):
                planes_node.remove(child)
            for child in original_planes:
                planes_node.append(child)


def _clone_workpiece(
    root: ET.Element,
    piece_index: int,
    name: str,
    length: float,
    width: float,
    depth: float,
) -> tuple[str, str]:
    """Clones the first WorkPiece for piece N (1-based index >= 2).

    Returns (workpiece_id, object_type) of the newly added WorkPiece.
    """
    workpieces_node = root.find("./{*}Workpieces")
    if workpieces_node is None:
        raise ValueError("La plantilla no contiene Workpieces.")
    original_wp = workpieces_node.find("./{*}WorkPiece")
    if original_wp is None:
        raise ValueError("La plantilla no contiene WorkPiece.")

    [new_id] = _reserve_ids(root, 1)
    new_wp = deepcopy(original_wp)

    object_type = _text(original_wp, "./{*}Key/{*}ObjectType")

    _set_text(new_wp.find("./{*}Key/{*}ID"), new_id)
    _set_text(new_wp.find("./{*}Name"), name)
    _set_text(new_wp.find("./{*}Length"), _compact_number(length))
    _set_text(new_wp.find("./{*}Width"), _compact_number(width))
    _set_text(new_wp.find("./{*}Depth"), _compact_number(depth))
    _set_text(new_wp.find("./{*}LengthName"), f"dx{piece_index}")
    _set_text(new_wp.find("./{*}WidthName"), f"dy{piece_index}")
    _set_text(new_wp.find("./{*}DepthName"), f"dz{piece_index}")

    geometry = new_wp.find("./{*}Geometry")
    if geometry is not None:
        _set_text(geometry.find("./{*}Length"), _compact_number(length))
        _set_text(geometry.find("./{*}Width"), _compact_number(width))
        _set_text(geometry.find("./{*}Depth"), _compact_number(depth))

    workpieces_node.append(new_wp)
    return new_id, object_type


def _add_dim_variables(
    root: ET.Element,
    piece_index: int,
    length: float,
    width: float,
    depth: float,
) -> None:
    """Adds dxN, dyN, dzN variables for piece N to the Variables block.

    Clones the dx1/dy1/dz1 templates to guarantee identical XML structure.
    """
    variables_node = root.find("./{*}Variables")
    if variables_node is None:
        raise ValueError("La plantilla no contiene Variables.")

    templates: dict[str, ET.Element] = {}
    for var in list(variables_node):
        name_lower = _text(var, "./{*}Name").lower()
        if name_lower in ("dx1", "dy1", "dz1"):
            templates[name_lower] = var

    if len(templates) < 3:
        raise ValueError("La plantilla no contiene variables dx1/dy1/dz1 como plantillas.")

    [id_dx, id_dy, id_dz] = _reserve_ids(root, 3)

    for template_key, new_name, description, value, new_id in (
        ("dx1", f"dx{piece_index}", "Length", length, id_dx),
        ("dy1", f"dy{piece_index}", "Width",  width,  id_dy),
        ("dz1", f"dz{piece_index}", "Depth",  depth,  id_dz),
    ):
        new_var = deepcopy(templates[template_key])
        _set_text(new_var.find("./{*}Key/{*}ID"), new_id)
        _set_text(new_var.find("./{*}Name"), new_name)
        _set_text(new_var.find("./{*}Description"), description)
        value_node = new_var.find("./{*}Value")
        if value_node is not None:
            value_node.text = _compact_number(value)
        variables_node.append(new_var)


def _add_dim_expressions(
    root: ET.Element,
    workpiece_id: str,
    workpiece_object_type: str,
    piece_index: int,
) -> None:
    """Adds Length/Width/Depth expressions binding dxN/dyN/dzN to the new WorkPiece."""
    expressions_node = root.find("./{*}Expressions")
    if expressions_node is None:
        raise ValueError("La plantilla no contiene Expressions.")

    first_expr = expressions_node.find("./{*}Expression")
    if first_expr is None:
        raise ValueError("La plantilla no contiene ninguna Expression como plantilla.")

    [id_len, id_wid, id_dep] = _reserve_ids(root, 3)

    for expr_id, prop_name, var_name in (
        (id_len, "Length", f"dx{piece_index}"),
        (id_wid, "Width",  f"dy{piece_index}"),
        (id_dep, "Depth",  f"dz{piece_index}"),
    ):
        new_expr = deepcopy(first_expr)
        _set_text(new_expr.find("./{*}Key/{*}ID"), expr_id)
        _set_text(new_expr.find("./{*}Property/{*}Name"), prop_name)
        _set_text(new_expr.find("./{*}ReferencedObject/{*}ID"), workpiece_id)
        _set_text(new_expr.find("./{*}ReferencedObject/{*}ObjectType"), workpiece_object_type)
        _set_text(new_expr.find("./{*}Value"), var_name)
        expressions_node.append(new_expr)


def _clone_planes_for_piece(
    root: ET.Element,
    workpiece_id: str,
    workpiece_object_type: str,
    piece_index: int,
    length: float,
    width: float,
    depth: float,
) -> None:
    """Clones the 6 canonical planes from piece 1 for piece N (piece_index >= 2)."""
    planes_node = root.find("./{*}Planes")
    if planes_node is None:
        raise ValueError("La plantilla no contiene Planes.")

    piece1_wp = root.find("./{*}Workpieces/{*}WorkPiece")
    if piece1_wp is None:
        raise ValueError("La plantilla no contiene WorkPiece.")
    piece1_id = _text(piece1_wp, "./{*}Key/{*}ID")

    piece1_planes: dict[str, ET.Element] = {}
    for plane in list(planes_node):
        ptype = _text(plane, "./{*}Type")
        pwp_id = _text(plane, "./{*}WorkpieceID/{*}ID")
        if ptype in _CANONICAL_PLANES and pwp_id == piece1_id:
            piece1_planes[ptype] = plane

    [id1, id2, id3, id4, id5, id6] = _reserve_ids(root, 6)
    new_ids = dict(zip(_CANONICAL_PLANES, (id1, id2, id3, id4, id5, id6)))

    for plane_type in _CANONICAL_PLANES:
        source_plane = piece1_planes.get(plane_type)
        if source_plane is None:
            continue

        new_plane = deepcopy(source_plane)
        _set_text(new_plane.find("./{*}Key/{*}ID"), new_ids[plane_type])
        _set_text(new_plane.find("./{*}Name"), _plane_suffix_name(plane_type, piece_index))
        _set_text(new_plane.find("./{*}GeneratorKey/{*}ID"), workpiece_id)
        _set_text(new_plane.find("./{*}GeneratorKey/{*}ObjectType"), workpiece_object_type)
        _set_text(new_plane.find("./{*}WorkpieceID/{*}ID"), workpiece_id)
        _set_text(new_plane.find("./{*}WorkpieceID/{*}ObjectType"), workpiece_object_type)

        x_dim, y_dim, x_origin, y_origin, z_origin = _plane_placement_spec(
            plane_type, length, width, depth
        )
        _set_text(new_plane.find("./{*}XDimension"), _compact_number(x_dim))
        _set_text(new_plane.find("./{*}YDimension"), _compact_number(y_dim))
        placement = new_plane.find("./{*}Placement")
        if placement is not None:
            _set_text(placement.find("./{*}_xP"), _compact_number(x_origin))
            _set_text(placement.find("./{*}_yP"), _compact_number(y_origin))
            _set_text(placement.find("./{*}_zP"), _compact_number(z_origin))

        planes_node.append(new_plane)


def _add_workpiece_setup(
    root: ET.Element,
    workpiece_id: str,
    workpiece_object_type: str,
    origin_x: float,
    origin_y: float,
    origin_z: float,
) -> None:
    """Adds a WorkpieceSetup for the new piece to the MainWorkplan's Setup."""
    setups_node = root.find(
        "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups"
    )
    if setups_node is None:
        raise ValueError("La plantilla no contiene Setup/WorkpieceSetups.")
    first_setup = setups_node.find("./{*}WorkpieceSetup")
    if first_setup is None:
        raise ValueError("La plantilla no contiene WorkpieceSetup como plantilla.")

    new_setup = deepcopy(first_setup)
    placement = new_setup.find("./{*}Placement")
    if placement is not None:
        _set_text(placement.find("./{*}_xP"), _compact_number(origin_x))
        _set_text(placement.find("./{*}_yP"), _compact_number(origin_y))
        _set_text(placement.find("./{*}_zP"), _compact_number(origin_z))

    _set_text(new_setup.find("./{*}WorkpieceID/{*}ID"), workpiece_id)
    _set_text(new_setup.find("./{*}WorkpieceID/{*}ObjectType"), workpiece_object_type)
    setups_node.append(new_setup)


def _add_piece_to_xml(
    root: ET.Element,
    piece_index: int,
    name: str,
    length: float,
    width: float,
    depth: float,
    origin_x: float,
    origin_y: float,
    origin_z: float,
) -> tuple[str, str]:
    """Adds all XML elements for piece N (piece_index >= 2, 1-based).

    Returns (workpiece_id, workpiece_object_type) of the newly created WorkPiece.
    """
    workpiece_id, object_type = _clone_workpiece(
        root, piece_index, name, length, width, depth
    )
    _add_dim_variables(root, piece_index, length, width, depth)
    _add_dim_expressions(root, workpiece_id, object_type, piece_index)
    _clone_planes_for_piece(root, workpiece_id, object_type, piece_index, length, width, depth)
    _add_workpiece_setup(root, workpiece_id, object_type, origin_x, origin_y, origin_z)
    return workpiece_id, object_type
