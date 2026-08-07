# iso/machining_lab — Laboratorio de investigación empírica

Contiene los estudios controlados que alimentan la base de conocimiento del
convertidor. Cada sub-laboratorio es una serie numerada e independiente.

## Convención de series

| Serie | Prefijo | Descripción |
| --- | --- | --- |
| R001 | `r001_programa_vacio/` | Reinvestigación, etapa 1: programa sin mecanizados (configuración de programa). |
| N (archivada) | — | Época anterior (no se usa como evidencia): fixtures en `Investigacion iso_converter\` de S:/P:, generadores y converter en la rama `iso_converter`. |

## Regla de promoción

Un hallazgo puede pasar al convertidor definitivo solo cuando:

- La regla fue observada en ISO Maestro generado desde los fixtures del lab.
- Existe evidencia documentada en `iso/docs/experiments/`.
- Hay un test reproducible que detecte regresiones.
