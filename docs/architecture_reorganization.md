# Reorganizacion De Arquitectura

Estado: 2026-05-31

Este documento fija el rumbo de reorganizacion del repo. Los frentes ISO por
estado y Vaciado quedan pausados como investigacion; la prioridad pasa a ordenar
el codigo productivo y reducir acoplamiento sin romper los comandos actuales.

## Objetivos

- Separar presentacion, persistencia, dominio, herramientas publicas y
  laboratorios.
- Mantener funcionando `python main.py` y las CLIs existentes durante toda la
  migracion.
- Evitar movimientos masivos sin una verificacion inmediata.
- Conservar wrappers de compatibilidad cuando una API publica cambie de modulo.
- Documentar cada frontera nueva en el mismo cambio que la introduce.

## Mapa Actual

| Ruta | Rol actual | Estado deseado |
| --- | --- | --- |
| `main.py` | Entrada de la app desktop | Se mantiene como entrada estable |
| `app/ui.py` | Detalle de proyecto y coordinacion de flujos | UI de proyecto, cada vez mas delgada |
| `app/main_window.py` | Ventana principal de seleccion de proyectos | Shell de arranque de la app |
| `app/project_dialogs.py` | Dialogos de creacion/edicion de proyectos | UI de metadatos de proyecto |
| `app/project_detail_core.py` | Estado y helpers del detalle de proyecto | Base compartida por los flujos del detalle |
| `app/project_detail_processing.py` | Procesamiento de proyecto/locales/modulos | Flujo de escaneo y escritura de configs |
| `app/project_detail_modules.py` | Listado y edicion tabular de modulos | Ventana de modulos por local |
| `app/project_detail_inspection.py` | Mixin de inspeccion/edicion de modulos | Flujo de inspeccion de piezas y En-Juego |
| `app/project_detail_color_changes.py` | Aplicacion de cambios de color por pieza, modulo o local | Persistencia cruzada testeable para colores |
| `app/project_detail_module_persistence.py` | Payloads, sincronizacion y guardado del modulo inspeccionado | Persistencia testeable del flujo de inspeccion |
| `app/project_detail_module_settings_panel.py` | Panel superior de dimensiones, cantidad y datos del modulo | UI reusable para settings del modulo inspeccionado |
| `app/project_detail_colors.py` | Colores disponibles y aplicacion por pieza/modulo/local | Helpers testeables para edicion de piezas |
| `app/project_detail_piece_editor.py` | Datos derivados del editor de piezas | Helpers testeables para plantillas y guardado de piezas |
| `app/project_detail_piece_editor_dialog.py` | Dialogo Qt para alta/edicion de piezas | UI del editor separada del flujo de inspeccion |
| `app/project_detail_piece_actions.py` | Botonera lateral de acciones del listado de piezas | UI reusable para acciones de inspeccion |
| `app/project_detail_piece_table.py` | Columnas, widgets centrados y configuracion visual de la tabla de piezas | Base UI del listado de piezas |
| `app/project_detail_piece_table_rows.py` | Render de filas y celdas del listado de piezas | UI reusable para poblar la tabla de piezas |
| `app/project_detail_programs.py` | Asociacion, limpieza y apertura de PGMX por pieza | Helpers de programas asociados a piezas |
| `app/project_detail_pgmx.py` | Cache y mensajes de inspeccion PGMX | Helpers de deteccion de ranuras no ejecutables |
| `app/project_detail_selected_piece_actions.py` | Acciones de pieza seleccionada para dibujo, source y reparacion PGMX | Orquestacion testeable de acciones sobre la fila seleccionada |
| `app/project_detail_en_juego_state.py` | Estado persistido En-Juego en configs de modulo | Helpers testeables para limpiar/sincronizar En-Juego |
| `app/project_detail_en_juego_layout.py` | Cantidades, instancias, posiciones guardadas/iniciales, serializacion, cotas, separacion, dimensiones y veta de En-Juego | Helpers testeables de layout/composicion |
| `app/project_detail_en_juego_view.py` | Vista, piezas arrastrables, cotas y plumas Qt del layout En-Juego | Componentes graficos reutilizables |
| `app/project_detail_en_juego_preview.py` | Carga/cache PGMX y render del preview de piezas En-Juego | Dibujo de operaciones sobre el layout |
| `app/project_detail_en_juego_dimensions.py` | Controlador de cotas editables del layout En-Juego | Anotaciones graficas separadas del dialogo |
| `app/project_detail_en_juego_configuration.py` | Dialogo principal de configuracion del layout En-Juego | Orquestacion del flujo visual En-Juego |
| `app/project_detail_en_juego_settings.py` | Normalizacion y guardado de settings del dialogo En-Juego | Helpers testeables para persistencia de opciones |
| `app/project_detail_en_juego_dialogs.py` | Subdialogos Qt, panel de controles y botonera En-Juego | UI dedicada para configurar opciones del En-Juego |
| `app/project_detail_en_juego_output.py` | Creacion `.pgmx` En-Juego desde el detalle de proyecto | Flujo de salida y resumen de generacion |
| `app/project_detail_piece_rows.py` | Normalizacion de filas de pieza y referencias PGMX | Helpers testeables para inspeccion de piezas |
| `app/project_detail_drawings.py` | Rutas, regeneracion y visor de dibujos SVG por pieza | Helpers visuales reutilizables del detalle |
| `app/project_detail_selectors.py` | Selectores editables de herrajes, guias y detalles | Dialogos reutilizables del detalle de proyecto |
| `app/project_detail_output.py` | Diagramas, planillas y salida CNC/ISO | Flujos de produccion/exportacion |
| `app/ui_constants.py` | Constantes compartidas de UI | Valores comunes para pantallas y dialogos |
| `app/options_dialogs.py` | Dialogos de opciones generales | Configuracion de tableros, herramientas, cortes, piezas y rutas |
| `app/qt_helpers.py` | Helpers genericos de ventanas/dialogos Qt | Utilidades compartidas de presentacion |
| `app/runtime.py` | Rutas runtime de la app | Fuente unica para rutas internas |
| `app/project_registry.py` | Registro de proyectos | Persistencia simple del registro |
| `app/project_store.py` | Carga/guardado de proyectos y configs locales | Servicio de persistencia de proyectos |
| `app/settings.py` | Configuracion, tableros, herramientas y En-Juego | Servicio de configuracion de app |
| `core/` | Modelo, parseo, resumen, nesting y En-Juego | Dominio productivo y servicios de aplicacion |
| `core/summary.py` | Resumen CSV y fachadas historicas de planillas | Compatibilidad para imports existentes |
| `core/production_sheet_data.py` | Carga normalizada de datos de planilla | Preparacion compartida por Excel y PDF |
| `core/production_sheet_images.py` | Imagenes de planilla, conversion SVG/PNG y popups | Aisla dependencias opcionales Pillow/CairoSVG/Qt |
| `core/production_sheet.py` | Planilla de produccion Excel y fachada PDF historica | Exportador Excel productivo |
| `core/production_sheet_pdf.py` | Planilla de produccion PDF interactiva | Renderer PDF productivo |
| `core/production_pdf.py` | Primitivos PDF de la planilla de produccion | Helpers testeables para objetos, coordenadas y JavaScript PDF |
| `core/nesting_model.py` | Tipos y constantes de corte/nesting | Contrato de datos compartido por empacadores y renderers |
| `core/nesting_boards.py` | Normalizacion, resolucion y margen de tableros de corte | Preparacion de tableros separada del empacador |
| `core/nesting_pdf.py` | Renderer PDF imprimible de diagramas de corte | Salida visual de nesting separada del empacador |
| `pgmx/` | Snapshot, adaptacion, sintesis, Vaciado y datos Maestro | Subsistema productivo PGMX fuera de `tools` |
| `pgmx/synthesis/` | Implementacion interna del sintetizador PGMX | Paquete productivo para specs, serializacion y extensiones PGMX |
| `pgmx/snapshot.py` | Snapshot PGMX publico | Herramienta publica estable |
| `pgmx/adapters.py` | Adaptadores PGMX publicos | Herramienta publica estable |
| `pgmx/processing.py` | Resolucion de programas PGMX, dibujos SVG, dimensiones y reparacion de slots | Servicios PGMX usados por UI, planillas y nesting |
| `pgmx/vaciado/` | Contrato V2 de Vaciado | Handoff hacia `pgmx.synthesis.vaciado` |
| `pgmx/vaciado_lab/` | Investigacion Vaciado y motor legado como oraculo | Laboratorio PGMX, no dependencia productiva directa |
| `pgmx/data/` | Baseline Maestro y catalogo de herramientas | Datos versionados del subsistema PGMX |
| `tools/synthesize_pgmx.py` | CLI y API historica de sintesis PGMX | Fachada compatible hacia `pgmx.synthesis` |
| `tools/pgmx_snapshot.py` | CLI y API historica de snapshot PGMX | Fachada compatible hacia `pgmx.snapshot` |
| `tools/pgmx_adapters.py` | CLI y API historica de adaptadores PGMX | Fachada compatible hacia `pgmx.adapters` |
| `tools/studies/` | Estudios reproducibles | Laboratorio versionado |
| `tools/pgmx_vaciado*` | Imports/CLIs historicos de Vaciado | Fachadas compatibles hacia `pgmx.vaciado*` |
| `iso_state_synthesis/` | Investigacion ISO por estado | Subsistema experimental pausado |
| `cnc_traceability/` | Herramienta XP standalone | Subsistema separado |

## Etapas De Migracion

1. Extraer infraestructura de `app/ui.py`.
   Hecho: `app/runtime.py`, `app/project_registry.py` y `app/settings.py`.
2. Extraer carga/guardado de proyectos desde `app/ui.py` hacia un modulo de
   aplicacion, sin cambiar el formato de `projects_list.json` ni los
   `project.json`.
   Hecho: `app/project_store.py`.
3. Extraer helpers compartidos de ventanas Qt.
   Hecho: `app/qt_helpers.py`.
4. Separar dialogos Qt de `app/ui.py` en modulos por responsabilidad:
   opciones, tableros, herramientas, piezas y cortes.
   Hecho: `app/options_dialogs.py`.
5. Separar dialogos de proyecto (`Nuevo`, `Editar`, locales) y shell principal.
   Hecho: `app/project_dialogs.py` y `app/main_window.py`.
6. Separar detalle de proyecto en modulos por flujo: procesamiento, inspeccion,
   planillas, cortes y generacion CNC.
   Hecho: `app/project_detail_core.py`, `app/project_detail_processing.py`,
   `app/project_detail_modules.py`, `app/project_detail_inspection.py` y
   `app/project_detail_output.py`.
   Avance adicional: panel de settings del modulo extraido a
   `app/project_detail_module_settings_panel.py`; selectores editables extraidos a
   `app/project_detail_selectors.py`; rutas, gestion de archivos y visor de
   dibujos SVG extraidos a `app/project_detail_drawings.py`; normalizacion de
   filas y referencias PGMX extraidas a `app/project_detail_piece_rows.py`;
   persistencia del modulo inspeccionado extraida a
   `app/project_detail_module_persistence.py`; aplicacion de cambios de color
   por alcance extraida a `app/project_detail_color_changes.py`;
   helpers de colores extraidos a `app/project_detail_colors.py`; datos del
   editor de piezas extraidos a `app/project_detail_piece_editor.py`;
   dialogo Qt del editor extraido a `app/project_detail_piece_editor_dialog.py`;
   botonera lateral de acciones de piezas extraida a
   `app/project_detail_piece_actions.py`; columnas/widgets/configuracion visual de
   tabla de piezas extraidos a `app/project_detail_piece_table.py`; render de
   filas/celdas de la tabla extraido a `app/project_detail_piece_table_rows.py`;
   programas asociados a piezas extraidos a `app/project_detail_programs.py`;
   cache/mensajes PGMX extraidos a `app/project_detail_pgmx.py`; acciones
   seleccionadas de dibujo/source/reparacion PGMX extraidas a
   `app/project_detail_selected_piece_actions.py`; estado
   persistido En-Juego extraido a `app/project_detail_en_juego_state.py`;
   helpers de layout/composicion En-Juego extraidos a
   `app/project_detail_en_juego_layout.py`; componentes graficos En-Juego
   extraidos a `app/project_detail_en_juego_view.py`; preview PGMX En-Juego
   extraido a `app/project_detail_en_juego_preview.py`; cotas editables
   extraidas a `app/project_detail_en_juego_dimensions.py`; dialogo principal de
   configuracion En-Juego extraido a `app/project_detail_en_juego_configuration.py`;
   normalizacion de
   settings del dialogo extraida a `app/project_detail_en_juego_settings.py`;
   subdialogos de divisiones/escuadrado, panel de controles y botonera En-Juego
   extraidos a
   `app/project_detail_en_juego_dialogs.py`; creacion `.pgmx` En-Juego extraida a
   `app/project_detail_en_juego_output.py`.
7. Separar `tools/synthesize_pgmx.py` en un paquete interno manteniendo
   `tools.synthesize_pgmx` como fachada publica.
   Hecho: el subsistema PGMX productivo vive en `pgmx/`; `pgmx/synthesis/core.py`
   contiene la implementacion heredada, `tools/synthesize_pgmx.py` quedo como
   fachada de compatibilidad y `pgmx/synthesis/vaciado.py` fija la frontera
   productiva para integrar `Vaciado` desde `pgmx.vaciado` sin depender del
   motor legado `pgmx.vaciado_lab.trace_engine`.
8. Revisar `core/` por dominios: proyectos/piezas, planillas, corte/nesting,
   En-Juego y puntos de contacto con `pgmx/`.
   Avance: `core/pgmx_processing.py` quedo como fachada compatible y la
   implementacion se movio a `pgmx/processing.py`; los imports productivos de
   UI, planillas y nesting apuntan ahora a `pgmx.processing`.
   Avance: primitivos PDF de la planilla de produccion extraidos desde
   `core.summary` a `core.production_pdf`, con cobertura focal para
   coordenadas, streams, apariencias y JavaScript PDF.
   Avance: exportadores Excel/PDF de planillas movidos a
   `core.production_sheet`; `core.summary` conserva el CSV y reexporta las
   funciones historicas para compatibilidad.
   Avance: carga normalizada de piezas, cantidades, dimensiones y notas PGMX de
   planilla movida a `core.production_sheet_data`, compartida por Excel y PDF.
   Avance: preparacion de imagenes de planilla, conversion SVG/PNG, fallback Qt,
   dibujos En-Juego y popups PDF movidos a `core.production_sheet_images`.
   Avance: renderer PDF interactivo de planillas movido a
   `core.production_sheet_pdf`; `core.production_sheet` conserva la fachada
   historica para imports existentes.
   Avance: tipos y constantes de corte/nesting movidos a
   `core.nesting_model`; `core.nesting` reexporta los nombres historicos para
   mantener compatibilidad con UI y laboratorios.
   Avance: renderer PDF imprimible de diagramas de corte movido a
   `core.nesting_pdf`; `core.nesting.generate_cut_diagrams` conserva la API
   publica y delega solo la salida visual.
   Avance: normalizacion, resolucion por material/espesor y aplicacion de
   margen de tableros movidas a `core.nesting_boards`; `core.nesting` conserva
   las fachadas historicas usadas por laboratorios.
9. Reubicar o etiquetar laboratorios sin mezclarlos con flujos productivos.

## Invariantes

- No cambiar comportamiento funcional como parte de un movimiento de archivos.
- Despues de cada etapa correr:

```powershell
python -m compileall main.py app core pgmx tools iso_state_synthesis cnc_traceability
python -c "import app.ui, core.parser, core.nesting, core.nesting_model, core.nesting_boards, core.nesting_pdf, core.summary, core.production_sheet, core.production_sheet_data, core.production_sheet_images, core.production_sheet_pdf, pgmx.processing, core.en_juego_synthesis; print('core imports ok')"
```

- Las suites de Vaciado estan pausadas por defecto. Para ejecutarlas cuando se
  reactive ese frente:

```powershell
$env:PRODACTION_ENABLE_VACIADO_TESTS='1'
python -m unittest tests.test_pgmx_vaciado_v2
python -m unittest tests.test_pgmx_vaciado
```

- Si una CLI publica se divide internamente, el comando viejo debe seguir
  funcionando.
- Los frentes pausados (`iso_state_synthesis/` y `pgmx/vaciado_lab/`) no se
  usan para dirigir la arquitectura productiva salvo que se reactive
  explicitamente ese frente. `pgmx/vaciado/` puede integrarse al subsistema
  PGMX solo a traves de `pgmx.synthesis.vaciado`.
