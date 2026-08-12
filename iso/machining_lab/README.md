# iso/machining_lab — Laboratorio de investigación empírica

Contiene los estudios controlados que alimentan la base de conocimiento del
convertidor. Cada sub-laboratorio es una serie numerada e independiente.

## Convención de series

| Serie | Prefijo | Descripción |
| --- | --- | --- |
| R001 | `r001_programa_vacio/` | Reinvestigación, etapa 1: programa sin mecanizados (configuración de programa). |
| R002 | `r002_areas/` | El área de ejecución: once fixtures que cerraron la fórmula del origen. |
| N (archivada) | — | Época anterior (no se usa como evidencia): fixtures en `Investigacion iso_converter\` de S:/P:, generadores y converter en la rama `iso_converter`. |

## Herramientas

Los fixtures que hace Fermín a mano en Maestro no tienen generador; se procesan con estos
módulos, que viven acá porque son del laboratorio, no del converter.

| Módulo | Qué contesta |
| --- | --- |
| `comparar_variantes.py` | Un lote de ISO contra una referencia: qué cambió y dónde. |
| `procesar_opciones.py` | Serie R_OPC: por fixture, ¿cambió el `.pgmx`? ¿y el `.iso`? (son preguntas distintas). |
| `verificar_nci.py` | Qué líneas del ISO salen literales de `NCI.CFG` y cuáles pone el emisor. |
| `buscar_en_binarios.py` | Qué módulo del emisor escribe una línea, y qué cadenas la rodean en el binario. Necesita Xilog Plus y Maestro instalados. |

## Regla de promoción

Un hallazgo puede pasar al convertidor definitivo solo cuando:

- La regla fue observada en ISO Maestro generado desde los fixtures del lab.
- Existe evidencia documentada en `iso/docs/experiments/`.
- Hay un test reproducible que detecte regresiones.
