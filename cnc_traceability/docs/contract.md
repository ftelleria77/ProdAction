# Contrato De Trazabilidad CNC

## Proposito

La herramienta de trazabilidad CNC registra y acompana la ejecucion real de un
proyecto ya preparado por ProdAction.

Su responsabilidad es:

- abrir un indice de proyectos o una estructura CNC ya generada;
- mostrar locales, modulos, piezas y archivos `.iso`;
- preparar un unico `.iso` en la carpeta `USBMIX`;
- registrar estados operativos por pieza/programa;
- conservar observaciones del operador.

No debe:

- generar `.pgmx`;
- postprocesar `.iso`;
- modificar datos productivos del proyecto;
- borrar archivos fuera de la carpeta `USBMIX` configurada;
- marcar una pieza como mecanizada solo por haber copiado el `.iso`.

## Frontera Con ProdAction Principal

ProdAction principal conserva estas responsabilidades:

- crear y escanear proyectos;
- administrar locales, modulos y piezas;
- sintetizar o reparar `.pgmx`;
- generar planillas, PDF y estructura de salida CNC;
- publicar el indice o cola de proyectos para la PC del CNC.

Trazabilidad CNC consume esa salida y registra lo que ocurre en piso.

## Entradas

La herramienta acepta:

- `cnc_project_viewer_index.json`;
- `prodaction_cnc_queue.json`;
- apertura manual de una carpeta CNC;
- archivos `.iso` dentro de la estructura de salida;
- `module_config.json` cuando existe una carpeta de modulo original asociable.

## Salidas

La salida principal es `cnc_progress.json`, guardado en la estructura CNC del
proyecto o, si no hay salida CNC, en la carpeta fuente disponible.

Estados actuales:

- `pendiente`;
- `en_proceso`;
- `copiado_a_usbmix`;
- `mecanizado`;
- `con_problema`.

## Seguridad USBMIX

La ruta de `USBMIX` debe estar configurada explicitamente.

Al preparar una ejecucion:

- solo se borran archivos `.iso` existentes dentro de `USBMIX`;
- si hay archivos no `.iso`, la operacion se bloquea;
- se copia un unico `.iso`;
- se verifica que la carpeta quede con un solo `.iso` esperado;
- el estado pasa a `copiado_a_usbmix`, no a `mecanizado`.

## Compatibilidad XP

El runtime objetivo es Windows XP 32 bits. Por eso el modulo debe seguir usando
Tkinter y libreria estandar, sin dependencias modernas ni APIs incompatibles con
un empaquetado antiguo.
