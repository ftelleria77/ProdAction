"""Standalone Panda3D module preview test window.

This prototype uses the same renderer-independent ModulePreviewModel as the
Qt3D and VTK tests, but draws it with Panda3D procedural cuboids. It is
intentionally outside the main application flow.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

try:
    from .module_3d_preview_model import (
        DEFAULT_LIBRARY_ROOT,
        ModulePreviewModel,
        PreviewBox,
        build_model_from_source,
        choose_initial_csv,
        format_mm,
        print_model_self_test,
        print_scan_summary,
        scan_library_csvs,
    )
except ImportError:
    from module_3d_preview_model import (
        DEFAULT_LIBRARY_ROOT,
        ModulePreviewModel,
        PreviewBox,
        build_model_from_source,
        choose_initial_csv,
        format_mm,
        print_model_self_test,
        print_scan_summary,
        scan_library_csvs,
    )


def _import_panda3d():
    try:
        import panda3d.core as p3d
    except ModuleNotFoundError:
        print("Panda3D no esta instalado. Para probar este visualizador:")
        print("python -m pip install panda3d")
        return None, None, None

    try:
        from direct.gui.OnscreenText import OnscreenText
        from direct.showbase.ShowBase import ShowBase
    except ModuleNotFoundError:
        print("Panda3D esta incompleto o no puede importar direct.showbase.")
        return None, None, None

    return p3d, ShowBase, OnscreenText


def _hex_to_rgba(color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    raw = str(color or "#cccccc").strip().lstrip("#")
    if len(raw) != 6:
        return 0.8, 0.8, 0.8, alpha
    try:
        red = int(raw[0:2], 16) / 255.0
        green = int(raw[2:4], 16) / 255.0
        blue = int(raw[4:6], 16) / 255.0
    except ValueError:
        return 0.8, 0.8, 0.8, alpha
    return red, green, blue, alpha


def _make_floor(model: ModulePreviewModel) -> PreviewBox:
    return PreviewBox(
        name="Floor",
        piece_type="",
        size_x=max(model.width * 1.22, 500.0),
        size_y=4.0,
        size_z=max(model.depth * 1.22, 500.0),
        center_x=0,
        center_y=-4.0,
        center_z=0,
        color="#cfd6dd",
        opacity=0.34,
    )


def _box_bounds(box: PreviewBox) -> tuple[float, float, float, float, float, float]:
    half_x = float(box.size_x) / 2
    half_y = float(box.size_z) / 2
    half_z = float(box.size_y) / 2
    center_x = float(box.center_x)
    center_y = float(box.center_z)
    center_z = float(box.center_y)
    return (
        center_x - half_x,
        center_x + half_x,
        center_y - half_y,
        center_y + half_y,
        center_z - half_z,
        center_z + half_z,
    )


def _make_cuboid_node(p3d, box: PreviewBox):
    vertex_format = p3d.GeomVertexFormat.getV3n3()
    vertex_data = p3d.GeomVertexData(box.name, vertex_format, p3d.Geom.UHStatic)
    vertices = p3d.GeomVertexWriter(vertex_data, "vertex")
    normals = p3d.GeomVertexWriter(vertex_data, "normal")
    triangles = p3d.GeomTriangles(p3d.Geom.UHStatic)

    x0, x1, y0, y1, z0, z1 = _box_bounds(box)
    faces = [
        (((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)), (-1, 0, 0)),
        (((x1, y1, z0), (x1, y0, z0), (x1, y0, z1), (x1, y1, z1)), (1, 0, 0)),
        (((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)), (0, -1, 0)),
        (((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)), (0, 1, 0)),
        (((x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1)), (0, 0, 1)),
        (((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)), (0, 0, -1)),
    ]

    vertex_index = 0
    for face_vertices, normal in faces:
        for vertex in face_vertices:
            vertices.addData3f(*vertex)
            normals.addData3f(*normal)
        triangles.addVertices(vertex_index, vertex_index + 1, vertex_index + 2)
        triangles.addVertices(vertex_index, vertex_index + 2, vertex_index + 3)
        vertex_index += 4

    geom = p3d.Geom(vertex_data)
    geom.addPrimitive(triangles)

    node = p3d.GeomNode(box.name)
    node.addGeom(geom)
    return node


def _make_edge_node(p3d, box: PreviewBox):
    x0, x1, y0, y1, z0, z1 = _box_bounds(box)
    corners = [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]
    edges = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]

    lines = p3d.LineSegs(f"{box.name}_edges")
    lines.setThickness(1.0)
    lines.setColor(0.20, 0.23, 0.26, min(max(box.opacity, 0.25), 0.9))
    for start, end in edges:
        lines.moveTo(*corners[start])
        lines.drawTo(*corners[end])
    return lines.create()


def _add_box(p3d, render, box: PreviewBox) -> None:
    node_path = render.attachNewNode(_make_cuboid_node(p3d, box))
    node_path.setColor(*_hex_to_rgba(box.color, box.opacity))
    node_path.setTwoSided(True)
    if box.opacity < 0.98:
        node_path.setTransparency(p3d.TransparencyAttrib.MAlpha)
        node_path.setBin("transparent", 30)
        node_path.setDepthWrite(False)

    edge_path = render.attachNewNode(_make_edge_node(p3d, box))
    if box.opacity < 0.98:
        edge_path.setTransparency(p3d.TransparencyAttrib.MAlpha)


def _add_lights(p3d, render) -> None:
    ambient = p3d.AmbientLight("ambient")
    ambient.setColor((0.48, 0.50, 0.53, 1.0))
    ambient_np = render.attachNewNode(ambient)
    render.setLight(ambient_np)

    key = p3d.DirectionalLight("key")
    key.setColor((0.92, 0.90, 0.84, 1.0))
    key_np = render.attachNewNode(key)
    key_np.setHpr(-35, -48, 0)
    render.setLight(key_np)

    fill = p3d.DirectionalLight("fill")
    fill.setColor((0.42, 0.50, 0.62, 1.0))
    fill_np = render.attachNewNode(fill)
    fill_np.setHpr(130, -28, 0)
    render.setLight(fill_np)


def _add_info_text(OnscreenText, p3d, model: ModulePreviewModel) -> None:
    display_boxes = [box for box in model.boxes if box.name != "Floor"]
    internal_count = sum(1 for box in display_boxes if box.is_internal)
    source = str(model.source_path) if model.source_path else "muestra interna"
    OnscreenText(
        text=(
            f"{model.name}\n"
            f"{format_mm(model.width)} x {format_mm(model.height)} x {format_mm(model.depth)} mm\n"
            f"Piezas CSV: {model.pieces_count} | reglas 3D: {len(model.represented_piece_keys)} | "
            f"omitidas: {len(model.omitted_pieces)}\n"
            f"Cajas Panda3D: {len(display_boxes)} ({internal_count} internas)\n"
            f"Fuente: {source}"
        ),
        pos=(-1.32, -0.74),
        scale=0.040,
        align=p3d.TextNode.ALeft,
        fg=(0.08, 0.10, 0.12, 1),
        mayChange=False,
    )


def _add_axes(p3d, render, model: ModulePreviewModel) -> None:
    origin = (-model.width / 2 - 85.0, -model.depth / 2 - 85.0, 0.0)
    lines = p3d.LineSegs("axes")
    lines.setThickness(3.0)
    axes = [
        ((1.0, 0.12, 0.10, 1.0), (160.0, 0.0, 0.0)),
        ((0.12, 0.62, 0.18, 1.0), (0.0, 160.0, 0.0)),
        ((0.12, 0.26, 0.95, 1.0), (0.0, 0.0, 160.0)),
    ]
    for color, delta in axes:
        lines.setColor(*color)
        lines.moveTo(*origin)
        lines.drawTo(origin[0] + delta[0], origin[1] + delta[1], origin[2] + delta[2])
    render.attachNewNode(lines.create())


class PandaPreviewApp:
    def __init__(
        self,
        p3d,
        ShowBase,
        OnscreenText,
        model: ModulePreviewModel,
        *,
        show_axes: bool = True,
        screenshot_path: Path | None = None,
    ):
        self.p3d = p3d
        self.model = model
        self.screenshot_path = screenshot_path
        self.base = ShowBase()
        self.base.disableMouse()
        self.base.setBackgroundColor(0.93, 0.95, 0.97, 1.0)

        if self.base.win is not None:
            self.base.win.setClearColor((0.93, 0.95, 0.97, 1.0))

        _add_lights(p3d, self.base.render)
        _add_box(p3d, self.base.render, _make_floor(model))
        for box in model.boxes:
            _add_box(p3d, self.base.render, box)
        if show_axes:
            _add_axes(p3d, self.base.render, model)
        _add_info_text(OnscreenText, p3d, model)

        self.center = p3d.Point3(0.0, 0.0, model.height / 2)
        self.distance = max(model.width, model.height, model.depth) * 2.65
        self.yaw = math.radians(26.0)
        self.pitch = math.radians(18.0)
        self.last_mouse: tuple[float, float] | None = None
        self._update_camera()

        self.base.accept("wheel_up", self._zoom, [0.86])
        self.base.accept("wheel_down", self._zoom, [1.16])
        self.base.accept("r", self._reset_camera)
        self.base.accept("escape", self.base.userExit)
        self.base.taskMgr.add(self._mouse_orbit_task, "mouse_orbit_task")

        if screenshot_path is not None:
            self.base.taskMgr.doMethodLater(0.2, self._save_screenshot_and_exit, "save_screenshot")

    def run(self) -> int:
        self.base.run()
        return 0

    def _reset_camera(self) -> None:
        self.distance = max(self.model.width, self.model.height, self.model.depth) * 2.65
        self.yaw = math.radians(26.0)
        self.pitch = math.radians(18.0)
        self._update_camera()

    def _zoom(self, factor: float) -> None:
        self.distance = max(max(self.model.width, self.model.height, self.model.depth) * 0.75, self.distance * factor)
        self._update_camera()

    def _update_camera(self) -> None:
        x = self.distance * math.sin(self.yaw) * math.cos(self.pitch)
        y = -self.distance * math.cos(self.yaw) * math.cos(self.pitch)
        z = self.distance * math.sin(self.pitch)
        self.base.camera.setPos(self.center.x + x, self.center.y + y, self.center.z + z)
        self.base.camera.lookAt(self.center)

    def _mouse_orbit_task(self, task):
        watcher = self.base.mouseWatcherNode
        if watcher is None:
            return task.cont

        button_down = watcher.isButtonDown(self.p3d.MouseButton.one())
        if not watcher.hasMouse() or not button_down:
            self.last_mouse = None
            return task.cont

        mouse = watcher.getMouse()
        current = (mouse.x, mouse.y)
        if self.last_mouse is not None:
            delta_x = current[0] - self.last_mouse[0]
            delta_y = current[1] - self.last_mouse[1]
            self.yaw -= delta_x * 2.25
            self.pitch = min(math.radians(76.0), max(math.radians(-8.0), self.pitch + delta_y * 1.45))
            self._update_camera()
        self.last_mouse = current
        return task.cont

    def _save_screenshot_and_exit(self, task):
        if self.screenshot_path is None:
            self.base.userExit()
            return task.done

        self.screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.base.graphicsEngine.renderFrame()
        self.base.win.saveScreenshot(self.p3d.Filename.fromOsSpecific(str(self.screenshot_path)))
        print(f"screenshot={self.screenshot_path}")
        self.base.userExit()
        return task.done


def show_panda3d_preview(
    model: ModulePreviewModel,
    *,
    show_axes: bool = True,
    screenshot_path: Path | None = None,
) -> int:
    p3d, ShowBase, OnscreenText = _import_panda3d()
    if p3d is None or ShowBase is None or OnscreenText is None:
        return 2

    p3d.loadPrcFileData("", "window-title Prueba visualizacion 3D de modulos - Panda3D")
    p3d.loadPrcFileData("", "win-size 1240 760")
    p3d.loadPrcFileData("", "sync-video false")
    if screenshot_path is not None:
        p3d.loadPrcFileData("", "window-type offscreen")

    app = PandaPreviewApp(
        p3d,
        ShowBase,
        OnscreenText,
        model,
        show_axes=show_axes,
        screenshot_path=screenshot_path,
    )
    return app.run()


def run_self_test(module_paths: list[Path], requested_csv: Path | None, *, show_internal: bool = True) -> int:
    selected_csv = choose_initial_csv(module_paths, requested_csv)
    model = build_model_from_source(csv_path=selected_csv, show_internal=show_internal)
    return print_model_self_test(model)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open a standalone Panda3D module preview test window.")
    parser.add_argument("--root", type=Path, default=DEFAULT_LIBRARY_ROOT, help="Maestro library root to scan.")
    parser.add_argument("--csv", type=Path, default=None, help="Specific module CSV to open.")
    parser.add_argument("--self-test", action="store_true", help="Build a preview model without opening the UI.")
    parser.add_argument("--scan-summary", action="store_true", help="Print a library scan summary without opening the UI.")
    parser.add_argument("--limit", type=int, default=0, help="Limit modules printed by --scan-summary.")
    parser.add_argument("--hide-internal", action="store_true", help="Hide internal preview boxes.")
    parser.add_argument("--no-axes", action="store_true", help="Hide the Panda3D axes lines.")
    parser.add_argument("--screenshot", type=Path, default=None, help="Render a PNG screenshot and exit.")
    args = parser.parse_args(argv)

    module_paths = scan_library_csvs(args.root)
    initial_csv = choose_initial_csv(module_paths, args.csv)
    show_internal = not args.hide_internal

    if args.self_test:
        return run_self_test(module_paths, args.csv, show_internal=show_internal)
    if args.scan_summary:
        print_scan_summary(module_paths, limit=args.limit)
        return 0

    model = build_model_from_source(csv_path=initial_csv, show_internal=show_internal)
    return show_panda3d_preview(model, show_axes=not args.no_axes, screenshot_path=args.screenshot)


if __name__ == "__main__":
    raise SystemExit(main())
