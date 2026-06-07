# Auditoria Del Subsistema `cnc_traceability/`

Estado: bloque auditado con cobertura focal, 2026-06-07.

Este documento registra el corte actual del visor de trazabilidad CNC. El
subsistema es una herramienta auxiliar standalone para la PC del CNC; no forma
parte del stack PySide6 de la aplicacion principal ni reemplaza el flujo
productivo de ProdAction.

## Alcance

`cnc_traceability/` acompana la ejecucion real de programas ya generados:

- abre un indice publicado o una carpeta CNC manual;
- lista archivos `.iso` en la estructura de salida;
- intenta resolver pieza, modulo, local, dimensiones y observaciones desde
  `module_config.json`;
- guarda avance operativo en `cnc_progress.json`;
- prepara un unico `.iso` en `USBMIX`;
- muestra una vista previa simple cuando el runtime Tkinter puede cargarla.

No debe generar PGMX, postprocesar ISO, modificar datos productivos del
proyecto ni borrar archivos fuera de la carpeta `USBMIX` configurada.

## Mapa Actual

| Ruta | Responsabilidad |
| --- | --- |
| `cnc_traceability/viewer_xp.py` | Aplicacion Tkinter/stdlib compatible con Windows XP 32 bits. Contiene helpers puros, ventana principal, ventana de proyecto y preview de pieza. |
| `cnc_traceability/config/cnc_project_viewer_settings.json` | Configuracion local inicial para desarrollo. En runtime portable se espera junto al ejecutable. |
| `cnc_traceability/docs/contract.md` | Contrato estable de responsabilidades, entradas, salidas y seguridad `USBMIX`. |
| `cnc_traceability/memory/current-state.md` | Memoria historica del frente y decisiones de diseno. |

## Procesos Donde Interviene

| Proceso | Entrada | Salida | Codigo |
| --- | --- | --- | --- |
| Apertura de cola | `cnc_project_viewer_index.json` o `prodaction_cnc_queue.json` | Lista normalizada de proyectos | `normalize_index`, `normalize_project`, `CncProjectViewerApp.load_index`. |
| Apertura manual | Carpeta CNC seleccionada | Proyecto manual normalizado | `open_manual_root_dialog`. |
| Escaneo de programas | Arbol CNC con `.iso` | Filas por local/modulo/pieza | `scan_iso_files`, `build_project_rows`. |
| Resolucion de pieza | `module_config.json` de carpeta origen | Nombre, dimensiones y observaciones | `read_module_config_for_iso`, `resolve_piece_for_iso`. |
| Avance operativo | Acciones del operador | `cnc_progress.json` | `progress_template`, `update_item_status`, `ProjectWindow.save_progress`. |
| Preparacion USBMIX | `.iso` seleccionado + carpeta configurada | Unico `.iso` copiado; estado `copiado_a_usbmix` | `ProjectWindow.prepare_usbmix`. |
| Preview | Imagen asociada si existe | Dibujo Tkinter o mensaje de fallback | `preview_candidates`, `find_preview`, `PiecePreviewWindow.draw_preview`. |

## Lectura De Codigo

`viewer_xp.py` esta organizado en tres capas:

- helpers puros y de filesystem al comienzo;
- `CncProjectViewerApp`, que maneja configuracion, indice y ventana principal;
- `ProjectWindow` y `PiecePreviewWindow`, que manejan el proyecto abierto,
  avance, observaciones, `USBMIX` y preview.

La restriccion XP esta respetada en el codigo auditado: no hay PySide6,
`pathlib`, `dataclasses`, f-strings ni dependencias externas. El modulo usa
compatibilidad `Tkinter`/`tkinter` para Python 2/3 y solo libreria estandar.

## Comentarios Y Documentacion

El modulo tiene un docstring de frontera correcto y documentos de entrada
propios (`README.md`, `docs/contract.md`, `memory/current-state.md`). Los
comentarios internos son escasos, pero el codigo es auditable por bloques si se
lee junto con este documento. No aparecen `TODO`/`FIXME` activos.

## Acciones Aplicadas

- Se agrego `tests/test_cnc_traceability.py` para cubrir helpers puros sin
  iniciar la UI Tkinter.
- La cobertura fija normalizacion de indices, escaneo de `.iso`,
  preservacion local/modulo, resolucion de pieza desde `module_config.json`,
  dimensiones, observaciones y estado de progreso.

## Deuda Residual Aceptada

- No hay test automatizado de UI Tkinter ni de dialogos. Para este subsistema
  eso queda aceptado porque el runtime objetivo es XP 32 bits y requiere
  validacion manual en la PC real.
- `viewer_xp.py` sigue siendo un archivo grande. Separarlo ahora podria
  complicar el empaquetado XP; conviene hacerlo solo si el flujo crece o si se
  define un build portable estable.
- Falta validar en la PC del CNC permisos de escritura, resolucion de pantalla,
  acceso a unidades compartidas y comportamiento real de `USBMIX`.
- La aplicacion principal todavia debe publicar o estabilizar la cola CNC si se
  quiere usar `cnc_project_viewer_index.json` como entrada operativa diaria.

## Validacion Del Bloque

Comandos esperados:

```powershell
py -3 -m unittest tests.test_cnc_traceability
py -3 -m compileall -q cnc_traceability
py -3 -m compileall -q main.py app core pgmx iso_state_synthesis cnc_traceability tools tests
py -3 -m unittest discover -s tests -p "test*.py"
```
