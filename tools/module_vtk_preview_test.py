"""Standalone VTK module preview test window.

This prototype uses the same renderer-independent ModulePreviewModel as the
Qt3D test, but draws it with VTK actors. It is intentionally outside the main
application flow.
"""

from __future__ import annotations

import argparse
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


def _import_vtk():
    try:
        import vtk
    except ModuleNotFoundError:
        print("VTK no esta instalado. Para probar este visualizador:")
        print("python -m pip install vtk")
        return None
    return vtk


def _hex_to_rgb(color: str) -> tuple[float, float, float]:
    raw = str(color or "#cccccc").strip().lstrip("#")
    if len(raw) != 6:
        return 0.8, 0.8, 0.8
    try:
        red = int(raw[0:2], 16) / 255.0
        green = int(raw[2:4], 16) / 255.0
        blue = int(raw[4:6], 16) / 255.0
    except ValueError:
        return 0.8, 0.8, 0.8
    return red, green, blue


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
        opacity=0.26,
    )


def _add_box_actor(vtk, renderer, box: PreviewBox) -> None:
    source = vtk.vtkCubeSource()
    source.SetXLength(float(box.size_x))
    source.SetYLength(float(box.size_y))
    source.SetZLength(float(box.size_z))
    source.SetCenter(float(box.center_x), float(box.center_y), float(box.center_z))

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*_hex_to_rgb(box.color))
    actor.GetProperty().SetOpacity(float(box.opacity))
    actor.GetProperty().SetSpecular(0.18)
    actor.GetProperty().SetSpecularPower(18.0)
    actor.GetProperty().EdgeVisibilityOn()
    actor.GetProperty().SetEdgeColor(0.22, 0.26, 0.30)
    actor.GetProperty().SetLineWidth(1.0)
    renderer.AddActor(actor)


def _add_axes(vtk, renderer, model: ModulePreviewModel) -> None:
    axes = vtk.vtkAxesActor()
    axes.SetTotalLength(160.0, 160.0, 160.0)
    axes.SetShaftTypeToCylinder()
    axes.SetCylinderRadius(0.018)
    axes.AxisLabelsOff()
    axes.SetPosition(-model.width / 2 - 85.0, 0.0, -model.depth / 2 - 85.0)
    renderer.AddActor(axes)


def _add_info_text(vtk, renderer, model: ModulePreviewModel) -> None:
    display_boxes = [box for box in model.boxes if box.name != "Floor"]
    internal_count = sum(1 for box in display_boxes if box.is_internal)
    source = str(model.source_path) if model.source_path else "muestra interna"

    text = vtk.vtkTextActor()
    text.SetInput(
        f"{model.name}\n"
        f"{format_mm(model.width)} x {format_mm(model.height)} x {format_mm(model.depth)} mm\n"
        f"Piezas CSV: {model.pieces_count} | reglas 3D: {len(model.represented_piece_keys)} | "
        f"omitidas: {len(model.omitted_pieces)}\n"
        f"Cajas VTK: {len(display_boxes)} ({internal_count} internas)\n"
        f"Fuente: {source}"
    )
    text.SetDisplayPosition(14, 14)
    text.GetTextProperty().SetFontSize(18)
    text.GetTextProperty().SetFontFamilyToArial()
    text.GetTextProperty().SetColor(0.08, 0.10, 0.12)
    renderer.AddViewProp(text)


def _configure_camera(renderer, model: ModulePreviewModel) -> None:
    camera = renderer.GetActiveCamera()
    camera.SetViewAngle(34.0)
    camera.SetPosition(model.width * 1.35, model.height * 1.05, -model.depth * 2.45)
    camera.SetFocalPoint(0.0, model.height / 2, 0.0)
    camera.SetViewUp(0.0, 1.0, 0.0)
    renderer.ResetCameraClippingRange()


def _write_screenshot(vtk, render_window, screenshot_path: Path) -> None:
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    image_filter = vtk.vtkWindowToImageFilter()
    image_filter.SetInput(render_window)
    image_filter.SetScale(1)
    image_filter.SetInputBufferTypeToRGB()
    image_filter.ReadFrontBufferOff()
    image_filter.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(screenshot_path))
    writer.SetInputConnection(image_filter.GetOutputPort())
    writer.Write()


def show_vtk_preview(
    model: ModulePreviewModel,
    *,
    show_axes: bool = True,
    screenshot_path: Path | None = None,
) -> int:
    vtk = _import_vtk()
    if vtk is None:
        return 2

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.93, 0.95, 0.97)

    render_window = vtk.vtkRenderWindow()
    render_window.SetWindowName("Prueba visualizacion 3D de modulos - VTK")
    render_window.SetSize(1240, 760)
    render_window.AddRenderer(renderer)
    if screenshot_path is not None:
        render_window.SetOffScreenRendering(1)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    _add_box_actor(vtk, renderer, _make_floor(model))
    for box in model.boxes:
        _add_box_actor(vtk, renderer, box)
    if show_axes:
        _add_axes(vtk, renderer, model)
    _add_info_text(vtk, renderer, model)
    _configure_camera(renderer, model)

    render_window.Render()
    if screenshot_path is not None:
        _write_screenshot(vtk, render_window, screenshot_path)
        print(f"screenshot={screenshot_path}")
        return 0

    interactor.Initialize()
    interactor.Start()
    return 0


def run_self_test(module_paths: list[Path], requested_csv: Path | None, *, show_internal: bool = True) -> int:
    selected_csv = choose_initial_csv(module_paths, requested_csv)
    model = build_model_from_source(csv_path=selected_csv, show_internal=show_internal)
    return print_model_self_test(model)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open a standalone VTK module preview test window.")
    parser.add_argument("--root", type=Path, default=DEFAULT_LIBRARY_ROOT, help="Maestro library root to scan.")
    parser.add_argument("--csv", type=Path, default=None, help="Specific module CSV to open.")
    parser.add_argument("--self-test", action="store_true", help="Build a preview model without opening the UI.")
    parser.add_argument("--scan-summary", action="store_true", help="Print a library scan summary without opening the UI.")
    parser.add_argument("--limit", type=int, default=0, help="Limit modules printed by --scan-summary.")
    parser.add_argument("--hide-internal", action="store_true", help="Hide internal preview boxes.")
    parser.add_argument("--no-axes", action="store_true", help="Hide the VTK axes actor.")
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
    return show_vtk_preview(model, show_axes=not args.no_axes, screenshot_path=args.screenshot)


if __name__ == "__main__":
    raise SystemExit(main())
