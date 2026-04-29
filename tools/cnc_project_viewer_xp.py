# -*- coding: utf-8 -*-
"""ProdAction CNC project viewer, XP-compatible prototype.

This module intentionally avoids the main PySide6 application stack.  The
target runtime is a 32-bit Windows XP executable, so the UI is built with the
standard Tkinter toolkit and only Python standard-library modules.
"""

from __future__ import print_function

import codecs
import json
import os
import shutil
import sys
import time

try:
    import Tkinter as tk
    import ttk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
except ImportError:  # pragma: no cover - Python 3 path
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
    from tkinter import messagebox


APP_TITLE = "ProdAction CNC - Visualizador"
SETTINGS_FILENAME = "cnc_project_viewer_settings.json"
INDEX_FILENAMES = ("cnc_project_viewer_index.json", "prodaction_cnc_queue.json")
PROGRESS_FILENAME = "cnc_progress.json"
ISO_EXT = ".iso"
PREVIEW_EXTENSIONS = (".gif", ".png", ".ppm", ".pgm", ".svg")


def now_stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def read_json(path):
    with codecs.open(path, "r", "utf-8-sig") as handle:
        return json.load(handle)


def write_json(path, data):
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    temp_path = path + ".tmp"
    with codecs.open(temp_path, "w", "utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    if os.path.exists(path):
        os.remove(path)
    os.rename(temp_path, path)


def normalize_path(path):
    if not path:
        return ""
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))


def relpath_safe(path, root):
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path


def split_relpath(path):
    if not path:
        return []
    parts = []
    head = os.path.normpath(path)
    while head and head not in (os.curdir, os.pardir):
        new_head, tail = os.path.split(head)
        if tail:
            parts.insert(0, tail)
        if not new_head or new_head == head:
            break
        head = new_head
    return parts


def is_iso_path(path):
    return path.lower().endswith(ISO_EXT)


def safe_project_id(project, fallback_index):
    for key in ("project_id", "id", "key"):
        value = project.get(key)
        if value:
            return str(value)
    raw = "%s|%s|%s" % (
        project.get("project_name", ""),
        project.get("client_name", ""),
        project.get("cnc_output_root", project.get("source_folder", "")),
    )
    if raw.strip("|"):
        return raw
    return "project-%s" % fallback_index


def normalize_project(project, fallback_index):
    result = dict(project)
    result["project_name"] = result.get("project_name") or result.get("name") or "Proyecto"
    result["client_name"] = result.get("client_name") or result.get("client") or ""
    result["source_folder"] = normalize_path(result.get("source_folder", ""))
    result["project_data_file"] = result.get("project_data_file") or "project.json"
    result["cnc_output_root"] = normalize_path(
        result.get("cnc_output_root")
        or result.get("output_root")
        or result.get("cnc_folder")
        or result.get("iso_root")
        or ""
    )
    result["project_id"] = safe_project_id(result, fallback_index)
    result["locales"] = result.get("locales") or []
    result["modules"] = result.get("modules") or []
    return result


def normalize_index(data):
    if isinstance(data, list):
        raw_projects = data
    elif isinstance(data, dict):
        raw_projects = data.get("projects") or []
    else:
        raw_projects = []

    projects = []
    for index, project in enumerate(raw_projects):
        if isinstance(project, dict):
            projects.append(normalize_project(project, index))
    return projects


def scan_iso_files(root):
    root = normalize_path(root)
    items = []
    if not root or not os.path.isdir(root):
        return items

    for current_root, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for filename in sorted(filenames):
            if not is_iso_path(filename):
                continue
            full_path = os.path.join(current_root, filename)
            rel_path = relpath_safe(full_path, root)
            rel_dir = os.path.dirname(rel_path)
            parts = split_relpath(rel_dir)
            local_name = parts[0] if len(parts) >= 1 else ""
            module_name = parts[1] if len(parts) >= 2 else ""
            items.append(
                {
                    "name": filename,
                    "path": full_path,
                    "rel_path": rel_path,
                    "rel_dir": rel_dir,
                    "local_name": local_name,
                    "module_name": module_name,
                }
            )
    return items


def progress_template(project):
    return {
        "format_version": 1,
        "updated_at": now_stamp(),
        "project": {
            "project_id": project.get("project_id", ""),
            "project_name": project.get("project_name", ""),
            "client_name": project.get("client_name", ""),
            "source_folder": project.get("source_folder", ""),
            "cnc_output_root": project.get("cnc_output_root", ""),
        },
        "items": {},
    }


def status_for(progress, rel_path):
    item = progress.get("items", {}).get(rel_path, {})
    return item.get("state") or "pendiente"


def update_item_status(progress, rel_path, iso_name, state, extra):
    items = progress.setdefault("items", {})
    item = items.setdefault(rel_path, {})
    item["iso_name"] = iso_name
    item["state"] = state
    item["updated_at"] = now_stamp()
    for key, value in extra.items():
        item[key] = value
    progress["updated_at"] = now_stamp()
    return item


def preview_candidates(project, iso_item):
    source_root = project.get("source_folder", "")
    if not source_root:
        return []

    rel_dir = iso_item.get("rel_dir", "")
    parts = split_relpath(rel_dir)
    candidate_dirs = []
    if rel_dir:
        candidate_dirs.append(os.path.join(source_root, rel_dir))
    if len(parts) > 1:
        candidate_dirs.append(os.path.join(source_root, *parts[1:]))
    candidate_dirs.append(source_root)

    base = os.path.splitext(iso_item.get("name", ""))[0]
    candidates = []
    seen = set()
    for folder in candidate_dirs:
        folder = normalize_path(folder)
        if not folder or folder in seen:
            continue
        seen.add(folder)
        if not os.path.isdir(folder):
            continue
        for ext in PREVIEW_EXTENSIONS:
            candidates.append(os.path.join(folder, base + ext))
        try:
            filenames = os.listdir(folder)
        except OSError:
            filenames = []
        lower_base = base.lower()
        for filename in filenames:
            name_root, ext = os.path.splitext(filename)
            if ext.lower() not in PREVIEW_EXTENSIONS:
                continue
            if name_root.lower() == lower_base:
                candidates.append(os.path.join(folder, filename))
    return candidates


def find_preview(project, iso_item):
    for candidate in preview_candidates(project, iso_item):
        if os.path.isfile(candidate):
            return candidate
    return ""


try:
    text_type = unicode
except NameError:  # pragma: no cover - Python 3 path
    text_type = str


def as_text(value):
    if value is None:
        return text_type("")
    if isinstance(value, text_type):
        return value
    try:
        return text_type(value)
    except Exception:
        return text_type("")


def project_label(project):
    name = as_text(project.get("project_name", "") or "Proyecto")
    client = as_text(project.get("client_name", ""))
    if client:
        return "%s - %s" % (name, client)
    return name


def compact_number(value):
    if value in (None, ""):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return as_text(value)
    if abs(number - int(number)) < 0.001:
        return str(int(number))
    return ("%.2f" % number).rstrip("0").rstrip(".")


def piece_dimensions_text(piece):
    if not piece:
        return ""
    width = piece.get("program_width") or piece.get("width")
    height = piece.get("program_height") or piece.get("height")
    thickness = piece.get("program_thickness") or piece.get("thickness")
    values = [compact_number(width), compact_number(height), compact_number(thickness)]
    values = [value for value in values if value]
    return " x ".join(values)


def simple_match_key(value):
    raw = as_text(value).strip()
    if not raw:
        return ""
    raw = raw.replace("\\", "/")
    raw = os.path.basename(raw)
    raw = os.path.splitext(raw)[0] or raw
    return "".join([char.lower() for char in raw if char.isalnum()])


def module_source_dirs(project, iso_item):
    source_root = project.get("source_folder", "")
    if not source_root:
        return []

    rel_dir = iso_item.get("rel_dir", "")
    parts = split_relpath(rel_dir)
    candidates = []
    if rel_dir:
        candidates.append(os.path.join(source_root, rel_dir))
    if len(parts) > 1:
        candidates.append(os.path.join(source_root, *parts[1:]))
    candidates.append(source_root)

    result = []
    seen = set()
    for folder in candidates:
        folder = normalize_path(folder)
        if not folder or folder in seen:
            continue
        seen.add(folder)
        result.append(folder)
    return result


def read_module_config_for_iso(project, iso_item):
    for folder in module_source_dirs(project, iso_item):
        config_path = os.path.join(folder, "module_config.json")
        if os.path.isfile(config_path):
            try:
                data = read_json(config_path)
            except Exception:
                data = {}
            if isinstance(data, dict):
                return data
    return {}


def piece_keys(piece):
    values = [
        piece.get("id"),
        piece.get("name"),
        piece.get("source"),
        piece.get("cnc_source"),
        piece.get("f6_source"),
    ]
    return [simple_match_key(value) for value in values if simple_match_key(value)]


def resolve_piece_for_iso(project, iso_item):
    config = read_module_config_for_iso(project, iso_item)
    pieces = config.get("pieces", []) if isinstance(config, dict) else []
    pieces = [piece for piece in pieces if isinstance(piece, dict)]
    if not pieces:
        return {}

    iso_key = simple_match_key(iso_item.get("name", ""))
    for piece in pieces:
        if iso_key and iso_key in piece_keys(piece):
            return piece

    for piece in pieces:
        for key in piece_keys(piece):
            if iso_key and key and (iso_key in key or key in iso_key):
                return piece

    if len(pieces) == 1:
        return pieces[0]
    return {}


def piece_name_for_row(iso_item, piece):
    if piece:
        return as_text(piece.get("name") or piece.get("id") or "").strip()
    base = os.path.splitext(iso_item.get("name", ""))[0]
    return base or iso_item.get("name", "")


def build_project_rows(project, progress):
    root = project.get("cnc_output_root", "")
    iso_items = scan_iso_files(root)
    rows = []
    for iso_item in iso_items:
        piece = resolve_piece_for_iso(project, iso_item)
        rel_path = iso_item.get("rel_path", "")
        progress_item = progress.get("items", {}).get(rel_path, {})
        observations = progress_item.get("observations")
        if observations is None and piece:
            observations = piece.get("observations", "")
        state = status_for(progress, rel_path)
        row = {
            "key": rel_path,
            "local_name": iso_item.get("local_name") or "(sin local)",
            "module_name": iso_item.get("module_name") or "(sin modulo)",
            "piece_name": piece_name_for_row(iso_item, piece),
            "dimensions": piece_dimensions_text(piece),
            "observations": observations or "",
            "state": state,
            "completed": state == "mecanizado",
            "iso_item": iso_item,
            "piece": piece,
            "preview_path": find_preview(project, iso_item),
        }
        rows.append(row)
    rows.sort(key=lambda item: (
        as_text(item.get("local_name", "")).lower(),
        as_text(item.get("module_name", "")).lower(),
        as_text(item.get("piece_name", "")).lower(),
        as_text(item.get("key", "")).lower(),
    ))
    return rows


class ScrollableFrame(object):
    def __init__(self, parent):
        self.outer = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.outer, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.outer, orient=tk.VERTICAL, command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas)
        self.body_id = self.canvas.create_window((0, 0), window=self.body, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.body.bind("<Configure>", self.on_body_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

    def pack(self, **kwargs):
        self.outer.pack(**kwargs)

    def on_body_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.body_id, width=event.width)


class CncProjectViewerApp(object):
    def __init__(self, root):
        self.root = root
        self.settings_path = os.path.join(app_dir(), SETTINGS_FILENAME)
        self.settings = self.load_settings()
        self.projects = []
        self.project_windows = []

        self.root.title("Proyectos")
        self.root.minsize(520, 520)
        self.build_ui()
        self.autoload_index()

    def load_settings(self):
        if os.path.isfile(self.settings_path):
            try:
                return read_json(self.settings_path)
            except Exception:
                return {}
        return {}

    def save_settings(self):
        try:
            write_json(self.settings_path, self.settings)
        except Exception as exc:
            self.set_status("No se pudo guardar configuracion: %s" % exc)

    def build_ui(self):
        toolbar = ttk.Frame(self.root, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Abrir indice", command=self.open_index_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Abrir estructura CNC", command=self.open_manual_root_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Configurar USBMIX", command=self.configure_usbmix).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Recargar", command=self.autoload_index).pack(side=tk.LEFT, padx=2)

        body = ttk.Frame(self.root, padding=8)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        ttk.Label(body, text="Proyectos").pack(anchor=tk.W)
        self.project_list = tk.Listbox(body, exportselection=False, height=18)
        self.project_list.pack(fill=tk.BOTH, expand=True, pady=(4, 6))
        self.project_list.bind("<Double-Button-1>", self.open_selected_project)
        self.project_list.bind("<<ListboxSelect>>", self.on_project_selected)

        button_bar = ttk.Frame(body)
        button_bar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(button_bar, text="Abrir proyecto", command=self.open_selected_project).pack(side=tk.LEFT, padx=2)

        self.project_info = tk.Text(body, height=7, wrap=tk.WORD)
        self.project_info.pack(fill=tk.X)
        self.project_info.configure(state=tk.DISABLED)

        self.usbmix_var = tk.StringVar()
        self.usbmix_var.set(self.settings.get("usbmix_path", "USBMIX sin configurar"))
        ttk.Label(self.root, textvariable=self.usbmix_var, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar()
        self.status_var.set("Listo.")
        ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, text):
        self.status_var.set(text)

    def autoload_index(self):
        paths = []
        configured = self.settings.get("index_path", "")
        if configured:
            paths.append(configured)
        for folder in (os.getcwd(), app_dir()):
            for filename in INDEX_FILENAMES:
                paths.append(os.path.join(folder, filename))

        for path in paths:
            if path and os.path.isfile(path):
                try:
                    self.load_index(path)
                    return
                except Exception as exc:
                    self.set_status("No se pudo leer indice %s: %s" % (path, exc))

        self.populate_projects()
        self.set_status("Sin indice cargado. Use 'Abrir indice' o 'Abrir estructura CNC'.")

    def open_index_dialog(self):
        path = filedialog.askopenfilename(
            title="Abrir indice CNC",
            filetypes=[("Indice CNC", "*.json"), ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            self.load_index(path)
            self.settings["index_path"] = path
            self.save_settings()
        except Exception as exc:
            messagebox.showerror(APP_TITLE, "No se pudo abrir el indice:\n%s" % exc)

    def load_index(self, path):
        data = read_json(path)
        projects = normalize_index(data)
        if not projects:
            raise ValueError("El indice no contiene proyectos.")
        self.projects = projects
        self.populate_projects()
        self.set_status("Indice cargado: %s" % path)

    def populate_projects(self):
        self.project_list.delete(0, tk.END)
        for project in self.projects:
            self.project_list.insert(tk.END, project_label(project))
        if self.projects:
            self.project_list.selection_set(0)
            self.show_project_info(self.projects[0])
        else:
            self.show_project_info({})

    def show_project_info(self, project):
        if not project:
            text = "No hay proyectos cargados."
        else:
            text = "\n".join(
                [
                    "Proyecto: %s" % project.get("project_name", ""),
                    "Cliente: %s" % project.get("client_name", ""),
                    "Origen: %s" % project.get("source_folder", ""),
                    "Salida CNC: %s" % project.get("cnc_output_root", ""),
                ]
            )
        self.project_info.configure(state=tk.NORMAL)
        self.project_info.delete("1.0", tk.END)
        self.project_info.insert(tk.END, text)
        self.project_info.configure(state=tk.DISABLED)

    def on_project_selected(self, event):
        selection = self.project_list.curselection()
        if not selection:
            return
        self.show_project_info(self.projects[int(selection[0])])

    def open_selected_project(self, event=None):
        selection = self.project_list.curselection()
        if not selection:
            messagebox.showwarning(APP_TITLE, "Seleccione un proyecto.")
            return
        project = self.projects[int(selection[0])]
        window = ProjectWindow(self, project)
        self.project_windows.append(window)

    def open_manual_root_dialog(self):
        root = filedialog.askdirectory(title="Abrir estructura CNC")
        if not root:
            return
        root = normalize_path(root)
        project = normalize_project(
            {
                "project_id": "manual:%s" % root,
                "project_name": os.path.basename(root) or root,
                "client_name": "Manual",
                "source_folder": "",
                "cnc_output_root": root,
            },
            len(self.projects),
        )
        self.projects.append(project)
        self.populate_projects()
        index = len(self.projects) - 1
        self.project_list.selection_clear(0, tk.END)
        self.project_list.selection_set(index)
        self.show_project_info(project)
        self.open_selected_project()

    def configure_usbmix(self):
        initial = self.settings.get("usbmix_path", "") or os.getcwd()
        path = filedialog.askdirectory(title="Configurar carpeta USBMIX", initialdir=initial)
        if not path:
            return
        path = normalize_path(path)
        self.settings["usbmix_path"] = path
        self.usbmix_var.set(path)
        self.save_settings()
        self.set_status("USBMIX configurado: %s" % path)


class ProjectWindow(object):
    def __init__(self, app, project):
        self.app = app
        self.project = project
        self.window = tk.Toplevel(app.root)
        self.window.title("Proyecto: %s" % project_label(project))
        self.window.minsize(1020, 620)
        self.progress_path = self.get_progress_path()
        self.progress = self.load_progress()
        self.rows = []
        self.observation_vars = {}
        self.build_ui()
        self.reload()

    def get_progress_path(self):
        root = self.project.get("cnc_output_root", "")
        if root:
            return os.path.join(root, PROGRESS_FILENAME)
        source = self.project.get("source_folder", "")
        if source:
            return os.path.join(source, PROGRESS_FILENAME)
        return ""

    def load_progress(self):
        if self.progress_path and os.path.isfile(self.progress_path):
            try:
                progress = read_json(self.progress_path)
                if isinstance(progress, dict):
                    progress.setdefault("items", {})
                    return progress
            except Exception as exc:
                self.set_status("No se pudo leer avance: %s" % exc)
        return progress_template(self.project)

    def save_progress(self):
        if not self.progress_path:
            messagebox.showwarning(APP_TITLE, "No hay ruta para guardar cnc_progress.json.")
            return False
        try:
            write_json(self.progress_path, self.progress)
            self.set_status("Avance guardado: %s" % self.progress_path)
            return True
        except Exception as exc:
            messagebox.showerror(APP_TITLE, "No se pudo guardar avance:\n%s" % exc)
            return False

    def build_ui(self):
        top = ttk.Frame(self.window, padding=6)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Proyecto: %s" % project_label(self.project)).pack(side=tk.LEFT)
        ttk.Button(top, text="Recargar", command=self.reload).pack(side=tk.RIGHT, padx=2)
        ttk.Button(top, text="Configurar USBMIX", command=self.app.configure_usbmix).pack(side=tk.RIGHT, padx=2)

        info = ttk.Frame(self.window, padding=(6, 0, 6, 4))
        info.pack(side=tk.TOP, fill=tk.X)
        self.summary_var = tk.StringVar()
        ttk.Label(info, textvariable=self.summary_var, anchor=tk.W).pack(fill=tk.X)

        self.sheet = ScrollableFrame(self.window)
        self.sheet.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.status_var = tk.StringVar()
        self.status_var.set("Listo.")
        ttk.Label(self.window, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, text):
        self.status_var.set(text)
        self.app.set_status(text)

    def reload(self):
        self.progress = self.load_progress()
        self.rows = build_project_rows(self.project, self.progress)
        self.draw_sheet()
        self.update_summary()

    def update_summary(self):
        total = len(self.rows)
        done = len([row for row in self.rows if row.get("state") == "mecanizado"])
        problems = len([row for row in self.rows if row.get("state") == "con_problema"])
        self.summary_var.set(
            "Salida CNC: %s    |    Programas: %s    |    Mecanizados: %s    |    Con problema: %s"
            % (self.project.get("cnc_output_root", ""), total, done, problems)
        )

    def clear_sheet(self):
        for child in self.sheet.body.winfo_children():
            child.destroy()

    def draw_sheet(self):
        self.clear_sheet()
        body = self.sheet.body
        for column in range(5):
            body.grid_columnconfigure(column, weight=0)
        body.grid_columnconfigure(4, weight=1)

        headers = ["", "Pieza", "Dimensiones", "Archivo ISO", "Observaciones"]
        widths = [4, 32, 18, 28, 52]
        for column, header in enumerate(headers):
            label = tk.Label(body, text=header, bg="#c8c8c8", anchor=tk.W, padx=4)
            label.grid(row=0, column=column, sticky="ew", padx=1, pady=1)
            label.configure(width=widths[column])

        if not self.project.get("cnc_output_root", ""):
            self.draw_message(1, "Proyecto sin carpeta CNC configurada.")
            return
        if not os.path.isdir(self.project.get("cnc_output_root", "")):
            self.draw_message(1, "No existe la carpeta CNC: %s" % self.project.get("cnc_output_root", ""))
            return
        if not self.rows:
            self.draw_message(1, "No se encontraron archivos .iso.")
            return

        current_local = None
        current_module = None
        row_index = 1
        self.observation_vars = {}
        for row in self.rows:
            local_name = row.get("local_name", "(sin local)")
            module_name = row.get("module_name", "(sin modulo)")
            if local_name != current_local:
                current_local = local_name
                current_module = None
                local_label = tk.Label(
                    body,
                    text=local_name,
                    bg="#9f9f9f",
                    fg="white",
                    anchor=tk.W,
                    padx=6,
                    font=("Arial", 10, "bold"),
                )
                local_label.grid(row=row_index, column=0, columnspan=5, sticky="ew", pady=(8, 1))
                row_index += 1
            if module_name != current_module:
                current_module = module_name
                module_label = tk.Label(body, text=module_name, bg="#e6e6e6", anchor=tk.W, padx=12)
                module_label.grid(row=row_index, column=0, columnspan=5, sticky="ew", pady=(2, 1))
                row_index += 1
            self.draw_piece_row(body, row_index, row)
            row_index += 1

    def draw_message(self, row_index, text):
        label = tk.Label(self.sheet.body, text=text, anchor=tk.W, padx=8, pady=10)
        label.grid(row=row_index, column=0, columnspan=5, sticky="ew")

    def draw_piece_row(self, body, row_index, row):
        bg = "#ffffff" if row_index % 2 == 0 else "#f5f5f5"
        if row.get("state") == "con_problema":
            bg = "#ffd9d9"
        elif row.get("state") == "copiado_a_usbmix":
            bg = "#fff2c2"
        elif row.get("state") == "mecanizado":
            bg = "#dff0d8"

        completed = tk.IntVar()
        completed.set(1 if row.get("state") == "mecanizado" else 0)
        check = tk.Checkbutton(
            body,
            variable=completed,
            bg=bg,
            command=lambda r=row, var=completed: self.on_completed_changed(r, var),
        )
        check.grid(row=row_index, column=0, sticky="nsew", padx=1, pady=1)

        piece_label = tk.Label(body, text=row.get("piece_name", ""), anchor=tk.W, bg=bg, padx=4)
        piece_label.grid(row=row_index, column=1, sticky="ew", padx=1, pady=1)

        dim_label = tk.Label(body, text=row.get("dimensions", ""), anchor=tk.W, bg=bg, padx=4)
        dim_label.grid(row=row_index, column=2, sticky="ew", padx=1, pady=1)

        iso_button = tk.Button(
            body,
            text=row.get("iso_item", {}).get("name", ""),
            anchor=tk.W,
            relief=tk.FLAT,
            fg="blue",
            bg=bg,
            activebackground=bg,
            command=lambda r=row: self.open_preview(r),
        )
        iso_button.grid(row=row_index, column=3, sticky="ew", padx=1, pady=1)

        obs_var = tk.StringVar()
        obs_var.set(row.get("observations", ""))
        self.observation_vars[row.get("key", "")] = obs_var
        obs_entry = tk.Entry(body, textvariable=obs_var, relief=tk.SOLID, bd=1)
        obs_entry.grid(row=row_index, column=4, sticky="ew", padx=1, pady=1)
        obs_entry.bind("<FocusOut>", lambda event, r=row, var=obs_var: self.save_observation(r, var.get()))
        obs_entry.bind("<Return>", lambda event, r=row, var=obs_var: self.save_observation(r, var.get()))

    def on_completed_changed(self, row, var):
        if var.get():
            self.set_row_state(row, "mecanizado", redraw=True)
        else:
            self.set_row_state(row, "pendiente", redraw=True)

    def save_observation(self, row, value):
        rel_path = row.get("key", "")
        item = self.progress.setdefault("items", {}).setdefault(rel_path, {})
        item["iso_name"] = row.get("iso_item", {}).get("name", "")
        item.setdefault("state", status_for(self.progress, rel_path))
        item["observations"] = value
        item["updated_at"] = now_stamp()
        self.progress["updated_at"] = now_stamp()
        row["observations"] = value
        self.save_progress()

    def set_row_state(self, row, state, redraw=False):
        extra = {}
        if state == "en_proceso":
            extra["started_at"] = now_stamp()
        elif state == "mecanizado":
            extra["machined_at"] = now_stamp()
        elif state == "con_problema":
            extra["problem_at"] = now_stamp()
        rel_path = row.get("key", "")
        update_item_status(self.progress, rel_path, row.get("iso_item", {}).get("name", ""), state, extra)
        row["state"] = state
        row["completed"] = state == "mecanizado"
        if self.save_progress() and redraw:
            self.reload()

    def open_preview(self, row):
        PiecePreviewWindow(self, row)

    def prepare_usbmix(self, row):
        iso_item = row.get("iso_item", {})
        usbmix = normalize_path(self.app.settings.get("usbmix_path", ""))
        if not usbmix:
            messagebox.showwarning(APP_TITLE, "Configure primero la carpeta USBMIX.")
            return False
        if not os.path.isdir(usbmix):
            messagebox.showerror(APP_TITLE, "La carpeta USBMIX no existe:\n%s" % usbmix)
            return False

        source = iso_item.get("path", "")
        if not os.path.isfile(source):
            messagebox.showerror(APP_TITLE, "No existe el ISO fuente:\n%s" % source)
            return False

        try:
            entries = [
                os.path.join(usbmix, name)
                for name in os.listdir(usbmix)
                if os.path.isfile(os.path.join(usbmix, name))
            ]
        except OSError as exc:
            messagebox.showerror(APP_TITLE, "No se pudo leer USBMIX:\n%s" % exc)
            return False

        iso_entries = [path for path in entries if is_iso_path(path)]
        non_iso_entries = [path for path in entries if not is_iso_path(path)]
        if non_iso_entries:
            messagebox.showerror(
                APP_TITLE,
                "USBMIX contiene archivos no ISO.\n"
                "Por seguridad no se borran automaticamente:\n\n%s"
                % "\n".join(non_iso_entries),
            )
            return False

        message = (
            "Se preparara USBMIX para una unica ejecucion.\n\n"
            "Carpeta USBMIX:\n%s\n\n"
            "Se borraran %s archivo(s) ISO existentes y se copiara:\n%s"
            % (usbmix, len(iso_entries), source)
        )
        if not messagebox.askyesno(APP_TITLE, message):
            return False

        try:
            for old_path in iso_entries:
                os.remove(old_path)
            destination = os.path.join(usbmix, os.path.basename(source))
            shutil.copy2(source, destination)
            final_entries = [
                name
                for name in os.listdir(usbmix)
                if os.path.isfile(os.path.join(usbmix, name))
            ]
        except Exception as exc:
            messagebox.showerror(APP_TITLE, "No se pudo preparar USBMIX:\n%s" % exc)
            return False

        if len(final_entries) != 1 or final_entries[0] != os.path.basename(source):
            messagebox.showerror(
                APP_TITLE,
                "USBMIX no quedo con un unico archivo esperado.\nRevise la carpeta:\n%s" % usbmix,
            )
            return False

        update_item_status(
            self.progress,
            row.get("key", ""),
            iso_item.get("name", ""),
            "copiado_a_usbmix",
            {"copied_at": now_stamp(), "usbmix_path": usbmix, "copied_name": os.path.basename(source)},
        )
        self.save_progress()
        self.reload()
        messagebox.showinfo(APP_TITLE, "USBMIX preparado con:\n%s" % os.path.basename(source))
        return True


class PiecePreviewWindow(object):
    def __init__(self, project_window, row):
        self.project_window = project_window
        self.row = row
        self.window = tk.Toplevel(project_window.window)
        self.window.title("Pieza: %s" % row.get("piece_name", ""))
        self.window.minsize(760, 520)
        self.preview_image = None
        self.build_ui()
        self.refresh()

    def build_ui(self):
        self.canvas = tk.Canvas(self.window, height=300, background="white", borderwidth=1, relief=tk.SUNKEN)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.detail_text = tk.Text(self.window, height=10, wrap=tk.WORD)
        self.detail_text.pack(side=tk.TOP, fill=tk.X, padx=8)
        self.detail_text.configure(state=tk.DISABLED)

        buttons = ttk.Frame(self.window, padding=8)
        buttons.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(buttons, text="Preparar en USBMIX", command=self.prepare_usbmix).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons, text="Marcar mecanizado", command=self.mark_machined).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons, text="Problema", command=self.mark_problem).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons, text="Cerrar", command=self.window.destroy).pack(side=tk.RIGHT, padx=2)

    def refresh(self):
        preview_path = self.row.get("preview_path") or find_preview(
            self.project_window.project,
            self.row.get("iso_item", {}),
        )
        self.row["preview_path"] = preview_path
        self.draw_preview(preview_path)
        self.set_detail_text(self.details_text(preview_path))

    def details_text(self, preview_path):
        iso_item = self.row.get("iso_item", {})
        lines = [
            "Pieza: %s" % self.row.get("piece_name", ""),
            "Dimensiones: %s" % self.row.get("dimensions", ""),
            "Local: %s" % self.row.get("local_name", ""),
            "Modulo: %s" % self.row.get("module_name", ""),
            "ISO: %s" % iso_item.get("name", ""),
            "Ruta ISO: %s" % iso_item.get("path", ""),
            "Vista previa: %s" % (preview_path or "No encontrada"),
            "Estado: %s" % status_for(self.project_window.progress, self.row.get("key", "")),
            "Observaciones: %s" % self.row.get("observations", ""),
        ]
        return "\n".join(lines)

    def set_detail_text(self, text):
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, text)
        self.detail_text.configure(state=tk.DISABLED)

    def draw_preview(self, preview_path):
        self.canvas.delete("all")
        self.preview_image = None
        if not preview_path:
            self.canvas.create_text(
                20,
                20,
                anchor=tk.NW,
                text="Sin imagen de vista previa.",
                fill="black",
                width=620,
            )
            return

        ext = os.path.splitext(preview_path)[1].lower()
        if ext in (".gif", ".png", ".ppm", ".pgm"):
            try:
                self.preview_image = tk.PhotoImage(file=preview_path)
                self.canvas.create_image(10, 10, anchor=tk.NW, image=self.preview_image)
                return
            except Exception:
                pass

        self.canvas.create_text(
            20,
            20,
            anchor=tk.NW,
            text="Vista previa disponible pero no renderizada en este runtime XP:\n\n%s" % preview_path,
            fill="black",
            width=620,
        )

    def prepare_usbmix(self):
        if self.project_window.prepare_usbmix(self.row):
            self.refresh()

    def mark_machined(self):
        self.project_window.set_row_state(self.row, "mecanizado", redraw=True)
        self.refresh()

    def mark_problem(self):
        self.project_window.set_row_state(self.row, "con_problema", redraw=True)
        self.refresh()


def main():
    root = tk.Tk()
    CncProjectViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
