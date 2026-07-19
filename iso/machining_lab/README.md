# iso/machining_lab — Laboratorio de investigación empírica

Contiene los estudios controlados que alimentan la base de conocimiento del
convertidor. Cada sub-laboratorio es una serie numerada e independiente.

## Convención de series

| Serie | Prefijo | Descripción |
| --- | --- | --- |
| N001 | `n001_baselines/` | Fixtures de línea base: taladro vertical, lateral y router. |

## Regla de promoción

Un hallazgo puede pasar a `iso/synthesis/` solo cuando:

- La regla fue observada en ISO Maestro generado desde los fixtures del lab.
- Existe evidencia documentada en `iso/docs/experiments/`.
- Hay un test reproducible que detecte regresiones.
