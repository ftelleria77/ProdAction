"""Extraction of individual pieces from a multi-piece PGMX file.

`split_pgmx_pieces` does native XML slicing: it creates one PGMX per WorkPiece,
keeping only that piece's features, geometry, operations, expressions, planes,
variables and WorkpieceSetup.  Variables are renamed so dxN/dyN/dzN become
dx1/dy1/dz1 in every extracted file; cross-piece dimension references become
_dxM/_dyM/_dzM with a snapshot of the original value.
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from typing import Optional

from .output import (
    _write_pgmx_zip,
    _finalize_synthesized_pgmx_xml_bytes,
    _build_itype_ns_map,
    _fix_itype_namespaces,
)
from .xml import _compact_number, _safe_float, _set_text, _text, register_pgmx_namespaces

__all__ = ["split_pgmx_pieces", "merge_pgmx_pieces"]

# Regex to identify dimensional variable names like dx1, dy2, dz12
_DIM_VAR_RE = re.compile(r"^d[xyz]\d+$")


def _tokenize_vars(formula: str, known_vars: frozenset[str]) -> set[str]:
    """Returns the variable names from *known_vars* that appear in the formula."""
    return {tok for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula) if tok in known_vars}


def _apply_rename(formula: str, rename: dict[str, str]) -> str:
    """Word-boundary-safe substitution of variable names in a formula."""
    if not rename:
        return formula
    pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in rename) + r")\b")
    return pattern.sub(lambda m: rename[m.group(0)], formula)


def _build_id_map(root: ET.Element) -> dict[str, ET.Element]:
    """Returns a map of Key/ID → element for every element in the tree."""
    result: dict[str, ET.Element] = {}
    for elem in root.iter():
        eid = (elem.findtext(".//{*}Key/{*}ID") or "").strip()
        if eid and eid not in result:
            result[eid] = elem
    return result


def _piece_index_from_wp(wp_element: ET.Element) -> int:
    """Extracts the piece index from the WorkPiece's LengthName (dx1→1, dx2→2, …)."""
    length_name = (_text(wp_element, "./{*}LengthName") or "dx1").strip()
    m = re.match(r"dx(\d+)$", length_name)
    return int(m.group(1)) if m else 1


_CANONICAL_PLANE_NAMES = frozenset(("Top", "Right", "Left", "Front", "Back", "Bottom"))


def _max_numeric_id(root: ET.Element) -> int:
    max_id = 0
    for elem in root.iter():
        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local == "ID":
            text = (elem.text or "").strip()
            if text.isdigit():
                max_id = max(max_id, int(text))
    return max_id


def _offset_numeric_ids(subtree: ET.Element, offset: int) -> None:
    for elem in subtree.iter():
        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local == "ID":
            text = (elem.text or "").strip()
            if text.isdigit():
                elem.text = str(int(text) + offset)


def _rename_piece_dim_vars(subtree: ET.Element, piece_index: int) -> None:
    """Renames dx1/dy1/dz1 → dxN/dyN/dzN throughout text content (word-boundary safe)."""
    rename = {"dx1": f"dx{piece_index}", "dy1": f"dy{piece_index}", "dz1": f"dz{piece_index}"}
    pattern = re.compile(r"\b(dx1|dy1|dz1)\b")
    for elem in subtree.iter():
        if elem.text and any(k in elem.text for k in rename):
            elem.text = pattern.sub(lambda m: rename[m.group(0)], elem.text)


def _rename_planes_for_merge(subtree: ET.Element, piece_index: int) -> None:
    """Renames canonical plane Names: 'Top' → 'Top(N-1)' for piece N >= 2."""
    suffix = f"({piece_index - 1})"
    for plane in subtree.findall(".//{*}Plane"):
        name_node = plane.find("./{*}Name")
        if name_node is not None:
            canonical = (name_node.text or "").strip()
            if canonical in _CANONICAL_PLANE_NAMES:
                name_node.text = canonical + suffix


def _merge_children(dest: Optional[ET.Element], src: Optional[ET.Element]) -> None:
    if dest is not None and src is not None:
        for child in src:
            dest.append(deepcopy(child))


def _merge_variables_dedup(base_root: ET.Element, piece_copy: ET.Element) -> None:
    """Merges Variables from piece_copy into base_root, skipping names already present."""
    dest = base_root.find("./{*}Variables")
    src = piece_copy.find("./{*}Variables")
    if dest is None or src is None:
        return
    existing_names = {
        (_text(v, "./{*}Name") or "").strip()
        for v in dest
    }
    for var in src:
        name = (_text(var, "./{*}Name") or "").strip()
        if name not in existing_names:
            dest.append(deepcopy(var))
            existing_names.add(name)


def _resolve_snapshots(root: ET.Element) -> None:
    """Replaces _dxN/_dyN/_dzN snapshot variables with their live counterparts when present."""
    variables_node = root.find("./{*}Variables")
    if variables_node is None:
        return

    live_vars: set[str] = set()
    snapshots: list[tuple[ET.Element, str, str]] = []

    for var in list(variables_node):
        name = (_text(var, "./{*}Name") or "").strip()
        if re.match(r"^_d[xyz]\d+$", name):
            snapshots.append((var, name, name[1:]))  # (elem, "_dz2", "dz2")
        elif re.match(r"^d[xyz]\d+$", name):
            live_vars.add(name)

    expressions_node = root.find("./{*}Expressions")
    for var_elem, snap_name, live_name in snapshots:
        if live_name in live_vars:
            variables_node.remove(var_elem)
            if expressions_node is not None:
                pat = re.compile(r"\b" + re.escape(snap_name) + r"\b")
                for expr in expressions_node:
                    val_node = expr.find(".//{*}Value")
                    if val_node is not None and val_node.text:
                        val_node.text = pat.sub(live_name, val_node.text)


def merge_pgmx_pieces(
    piece_paths: list[Path],
    output_path: Path,
) -> Path:
    """Merges N single-piece PGMX files into a multi-piece PGMX file.

    Args:
        piece_paths:  Ordered list of single-piece .pgmx files. The first file
                      is used as the base; subsequent pieces are renumbered.
        output_path:  Destination path for the merged .pgmx file.

    Returns:
        Path of the written file (same as output_path).
    """
    register_pgmx_namespaces()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not piece_paths:
        raise ValueError("Se requiere al menos una pieza para combinar.")

    # Load all pieces
    pieces_roots: list[ET.Element] = []
    template_entries: dict[str, bytes] = {}
    itype_ns_map: dict[tuple[str, str], str] = {}

    for i, path in enumerate(piece_paths):
        with zipfile.ZipFile(path) as zf:
            entries = {name: zf.read(name) for name in zf.namelist()}
        if i == 0:
            template_entries = entries
        xml_name = next(n for n in entries if n.lower().endswith(".xml"))
        xml_text = entries[xml_name].decode("utf-8", errors="ignore")
        itype_ns_map.update(_build_itype_ns_map(xml_text))
        pieces_roots.append(ET.fromstring(xml_text))

    # Base = deep copy of piece 1 (dx1/dy1/dz1 already correct)
    base_root = deepcopy(pieces_roots[0])

    for piece_idx, piece_root in enumerate(pieces_roots[1:], start=2):
        piece_copy = deepcopy(piece_root)

        # 1. Remap IDs to avoid collisions with existing base IDs
        id_offset = _max_numeric_id(base_root) + 1
        _offset_numeric_ids(piece_copy, id_offset)

        # 2. Rename dx1/dy1/dz1 → dxN/dyN/dzN (own dimensions)
        _rename_piece_dim_vars(piece_copy, piece_idx)

        # 3. Rename plane display names: "Top" → "Top(N-1)"
        _rename_planes_for_merge(piece_copy, piece_idx)

        # 4. Merge XML blocks into base
        for block_path in (
            "./{*}Workpieces",
            "./{*}Expressions",
            "./{*}Features",
            "./{*}Geometries",
            "./{*}Operations",
            "./{*}Planes",
        ):
            _merge_children(base_root.find(block_path), piece_copy.find(block_path))

        # Variables: deduplicate by name (user vars shared across pieces must not repeat)
        _merge_variables_dedup(base_root, piece_copy)

        _merge_children(
            base_root.find("./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups"),
            piece_copy.find("./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups"),
        )
        _merge_children(
            base_root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements"),
            piece_copy.find("./{*}Workplans/{*}MainWorkplan/{*}Elements"),
        )

    # 5. Resolve snapshot variables (_dz2 → dz2) now that all live vars are present
    _resolve_snapshots(base_root)

    xml_bytes = _finalize_synthesized_pgmx_xml_bytes(
        ET.tostring(base_root, encoding="utf-8", xml_declaration=True)
    )
    xml_bytes = _fix_itype_namespaces(xml_bytes.decode("utf-8"), itype_ns_map).encode("utf-8")
    xml_entry_name = output_path.stem + ".xml"
    _write_pgmx_zip(output_path, xml_bytes, template_entries, xml_entry_name)
    return output_path


def split_pgmx_pieces(
    source_path: Path,
    output_dir: Path,
    *,
    baseline_path: Optional[Path] = None,
) -> list[Path]:
    """Extracts each WorkPiece from a multi-piece PGMX into individual PGMX files.

    Args:
        source_path: Path to the multi-piece .pgmx file.
        output_dir:  Directory where the extracted files will be written.
        baseline_path: Unused — kept for API compatibility. Extraction uses the
                       source file as its own baseline.

    Returns:
        List of paths to the written PGMX files, one per WorkPiece, in order.
    """
    register_pgmx_namespaces()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source_path) as zf:
        archive_entries = {name: zf.read(name) for name in zf.namelist()}
    xml_entry_name = next(name for name in archive_entries if name.lower().endswith(".xml"))
    xml_source_text = archive_entries[xml_entry_name].decode("utf-8", errors="ignore")
    itype_ns_map = _build_itype_ns_map(xml_source_text)
    root = ET.fromstring(xml_source_text)

    workpieces = list(root.findall("./{*}Workpieces/{*}WorkPiece"))
    if not workpieces:
        raise ValueError(f"El archivo '{source_path}' no contiene WorkPieces.")

    # ---------- Build global object-ID → workpiece-ID maps ----------

    # Features: ManufacturingFeature.WorkpieceID
    feature_to_wp: dict[str, str] = {}
    geom_to_wp: dict[str, str] = {}
    op_to_wp: dict[str, str] = {}
    features_node = root.find("./{*}Features")
    if features_node is not None:
        for feat in features_node:
            fid = (_text(feat, "./{*}Key/{*}ID") or "").strip()
            wp_id = (_text(feat, "./{*}WorkpieceID/{*}ID") or "").strip()
            geom_id = (_text(feat, "./{*}GeometryID/{*}ID") or "").strip()
            op_ids = [
                (ref.findtext(".//{*}ID") or "").strip()
                for ref in feat.findall(".//{*}OperationIDs/{*}ReferenceKey")
            ]
            feature_to_wp[fid] = wp_id
            if geom_id:
                geom_to_wp[geom_id] = wp_id
            for oid in op_ids:
                if oid:
                    op_to_wp[oid] = wp_id

    # Steps: MachiningWorkingStep → ManufacturingFeatureID → feature → wp
    step_to_wp: dict[str, str] = {}
    elements_node = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    if elements_node is not None:
        for step in elements_node:
            step_id = (_text(step, "./{*}Key/{*}ID") or "").strip()
            mfid = (_text(step, "./{*}ManufacturingFeatureID/{*}ID") or "").strip()
            step_to_wp[step_id] = feature_to_wp.get(mfid, "")

    # All variable names and their IDs/values
    all_var_names: frozenset[str] = frozenset(
        (_text(var, "./{*}Name") or "").strip()
        for var in root.findall("./{*}Variables/{*}Variable")
    )
    var_value: dict[str, float] = {}
    dim_var_name_to_id: dict[str, str] = {}
    all_var_ids: set[str] = set()
    for var in root.findall("./{*}Variables/{*}Variable"):
        vname = (_text(var, "./{*}Name") or "").strip()
        val = _safe_float((_text(var, "./{*}Value") or "0").strip(), 0.0)
        var_value[vname] = val
        vid = (_text(var, "./{*}Key/{*}ID") or "").strip()
        if vid:
            all_var_ids.add(vid)
        if _DIM_VAR_RE.match(vname) and vid:
            dim_var_name_to_id[vname] = vid

    # Per-workpiece object ID sets (features, geoms, ops, steps, workpiece — NOT variables)
    wp_id_to_objects: dict[str, set[str]] = {}
    # Per-workpiece own dimensional variable IDs (dx/dy/dz for this piece's index)
    wp_id_to_dim_var_ids: dict[str, set[str]] = {}
    for wp in workpieces:
        wid = (_text(wp, "./{*}Key/{*}ID") or "").strip()
        pidx = _piece_index_from_wp(wp)
        s: set[str] = {wid}
        s |= {fid for fid, w in feature_to_wp.items() if w == wid}
        s |= {gid for gid, w in geom_to_wp.items() if w == wid}
        s |= {oid for oid, w in op_to_wp.items() if w == wid}
        s |= {sid for sid, w in step_to_wp.items() if w == wid}
        wp_id_to_objects[wid] = s
        dim_ids: set[str] = set()
        for axis in ("dx", "dy", "dz"):
            vid = dim_var_name_to_id.get(f"{axis}{pidx}")
            if vid:
                dim_ids.add(vid)
        wp_id_to_dim_var_ids[wid] = dim_ids

    # ---------- Extract one file per WorkPiece ----------
    output_paths: list[Path] = []

    for wp in workpieces:
        wp_id = (_text(wp, "./{*}Key/{*}ID") or "").strip()
        wp_name = (_text(wp, "./{*}Name") or wp_id).strip()
        piece_index = _piece_index_from_wp(wp)

        # ── Determine which variables this piece uses ──────────────────────────
        piece_objects = wp_id_to_objects[wp_id]
        piece_dim_var_ids = wp_id_to_dim_var_ids[wp_id]

        piece_used_vars: set[str] = set()
        for expr in root.findall("./{*}Expressions/{*}Expression"):
            ref_id = (_text(expr, "./{*}ReferencedObject/{*}ID") or "").strip()
            if ref_id in piece_objects or ref_id in piece_dim_var_ids:
                value = (_text(expr, "./{*}Value") or "").strip()
                piece_used_vars |= _tokenize_vars(value, all_var_names)

        # ── Build rename map ───────────────────────────────────────────────────
        own_dx = f"dx{piece_index}"
        own_dy = f"dy{piece_index}"
        own_dz = f"dz{piece_index}"

        rename: dict[str, str] = {}
        if own_dx != "dx1":
            rename[own_dx] = "dx1"
        if own_dy != "dy1":
            rename[own_dy] = "dy1"
        if own_dz != "dz1":
            rename[own_dz] = "dz1"

        # Foreign dimension variable references
        foreign_dims: dict[str, str] = {}  # original_name → snapshot_name
        for var_name in piece_used_vars:
            if _DIM_VAR_RE.match(var_name) and var_name not in (own_dx, own_dy, own_dz):
                snapshot_name = f"_{var_name}"
                rename[var_name] = snapshot_name
                foreign_dims[var_name] = snapshot_name

        # ── Deep-copy and slice the XML ────────────────────────────────────────
        copy_root = deepcopy(root)

        # --- Variables ---
        variables_node = copy_root.find("./{*}Variables")
        if variables_node is not None:
            to_remove = []
            for var in list(variables_node):
                vname = (_text(var, "./{*}Name") or "").strip()
                if _DIM_VAR_RE.match(vname):
                    if vname in (own_dx, own_dy, own_dz):
                        # Keep and rename to dx1/dy1/dz1
                        _set_text(var.find(".//{*}Name"), rename.get(vname, vname))
                    elif vname in foreign_dims:
                        # Keep as snapshot with _ prefix
                        _set_text(var.find(".//{*}Name"), foreign_dims[vname])
                        val_node = var.find(".//{*}Value")
                        if val_node is not None:
                            val_node.text = _compact_number(var_value.get(vname, 0.0))
                    else:
                        to_remove.append(var)
                else:
                    # User variable: keep only if used by this piece
                    if vname not in piece_used_vars:
                        to_remove.append(var)
            for v in to_remove:
                variables_node.remove(v)

            # Update WorkPiece dim variable name attributes
            for var in list(variables_node):
                vname = (_text(var, "./{*}Name") or "").strip()
                # Ensure dx1/dy1/dz1 variables have the right LengthName in workpiece
                pass  # handled below in WorkPiece block

        # --- WorkPieces ---
        workpieces_node = copy_root.find("./{*}Workpieces")
        if workpieces_node is not None:
            for other_wp in list(workpieces_node):
                other_id = (_text(other_wp, "./{*}Key/{*}ID") or "").strip()
                if other_id != wp_id:
                    workpieces_node.remove(other_wp)
                else:
                    # Fix LengthName/WidthName/DepthName
                    _set_text(other_wp.find("./{*}LengthName"), "dx1")
                    _set_text(other_wp.find("./{*}WidthName"), "dy1")
                    _set_text(other_wp.find("./{*}DepthName"), "dz1")

        # --- Expressions ---
        expressions_node = copy_root.find("./{*}Expressions")
        if expressions_node is not None:
            to_remove = []
            for expr in list(expressions_node):
                ref_id = (_text(expr, "./{*}ReferencedObject/{*}ID") or "").strip()
                # Variable formula expressions: keep only for this piece's own dim vars.
                # Using all_var_ids to distinguish variable formulas from feature/geom/op
                # formulas avoids false positives when the same numeric ID appears as both
                # a variable ID and a feature ID in different pieces.
                if ref_id in all_var_ids:
                    if ref_id not in piece_dim_var_ids:
                        to_remove.append(expr)
                    else:
                        value_node = expr.find(".//{*}Value")
                        if value_node is not None and value_node.text:
                            value_node.text = _apply_rename(value_node.text, rename)
                elif ref_id not in piece_objects:
                    to_remove.append(expr)
                else:
                    # Feature / operation / workpiece parametric expression
                    value_node = expr.find(".//{*}Value")
                    if value_node is not None and value_node.text:
                        value_node.text = _apply_rename(value_node.text, rename)
            for e in to_remove:
                expressions_node.remove(e)

        # --- Features ---
        features_copy = copy_root.find("./{*}Features")
        if features_copy is not None:
            for feat in list(features_copy):
                fid = (_text(feat, "./{*}Key/{*}ID") or "").strip()
                if feature_to_wp.get(fid, "") != wp_id:
                    features_copy.remove(feat)

        # --- Operations ---
        operations_node = copy_root.find("./{*}Operations")
        if operations_node is not None:
            for op in list(operations_node):
                oid = (_text(op, "./{*}Key/{*}ID") or "").strip()
                if op_to_wp.get(oid, "") != wp_id:
                    operations_node.remove(op)

        # --- Geometries ---
        geometries_node = copy_root.find("./{*}Geometries")
        if geometries_node is not None:
            for geom in list(geometries_node):
                gid = (_text(geom, "./{*}Key/{*}ID") or "").strip()
                if geom_to_wp.get(gid, "") != wp_id:
                    geometries_node.remove(geom)

        # --- Planes ---
        planes_node = copy_root.find("./{*}Planes")
        if planes_node is not None:
            for plane in list(planes_node):
                plane_wp_id = (_text(plane, "./{*}WorkpieceID/{*}ID") or "").strip()
                if plane_wp_id != wp_id:
                    planes_node.remove(plane)
                else:
                    # Normalize plane Name to remove the (N-1) suffix
                    canonical = _text(plane, "./{*}Type") or ""
                    if canonical:
                        name_node = plane.find(".//{*}Name")
                        if name_node is not None:
                            name_node.text = canonical

        # --- WorkpieceSetups ---
        setups_node = copy_root.find(
            "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups"
        )
        if setups_node is not None:
            for setup in list(setups_node):
                setup_wp_id = (_text(setup, "./{*}WorkpieceID/{*}ID") or "").strip()
                if setup_wp_id != wp_id:
                    setups_node.remove(setup)

        # --- MainWorkplan Elements ---
        elements_copy = copy_root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
        if elements_copy is not None:
            for step in list(elements_copy):
                step_id = (_text(step, "./{*}Key/{*}ID") or "").strip()
                if step_to_wp.get(step_id, "") != wp_id:
                    elements_copy.remove(step)

        # --- Serialize and write ---
        xml_bytes = _finalize_synthesized_pgmx_xml_bytes(
            ET.tostring(copy_root, encoding="utf-8", xml_declaration=True)
        )
        xml_bytes = _fix_itype_namespaces(xml_bytes.decode("utf-8"), itype_ns_map).encode("utf-8")
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", wp_name)
        output_path = output_dir / f"{safe_name}.pgmx"
        _write_pgmx_zip(
            output_path=output_path,
            xml_bytes=xml_bytes,
            template_entries=archive_entries,
            xml_entry_name=f"{safe_name}.xml",
        )
        output_paths.append(output_path)

    return output_paths
