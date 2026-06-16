# N001 — Fixtures de línea base

Primer lote empírico del convertidor PGMX→ISO. Cada fixture aísla una variable
para que el análisis del ISO Maestro resultante sea inequívoco.

## Grupos

| Grupo | Fixtures | Variable aislada |
| --- | --- | --- |
| A | N_A001..A007 | Taladro vertical: herramienta única/múltiple, agujeros múltiples, profundidades mixtas. |
| B | N_B001..B008 | Taladro lateral: cada cara + combinaciones. |
| C | N_C001..C007 | Transiciones entre familias: top→side, side→top, top→router, router→top, etc. |
| D | N_D001..D002 | Router (line milling): pasada simple y doble. |

## Flujo de trabajo

1. `generate.py` — genera los 20 `.pgmx` en el directorio de salida.
2. Convertir con Maestro en la máquina CNC (acceso físico requerido).
3. `analyze.py` — compara los `.iso` generados y extrae reglas.
4. Documentar hallazgos en `memory/current-state.md` y en `iso/docs/experiments/`.

## Estado

- [x] Fixtures generados (`generate.py` operativo).
- [ ] Conversión Maestro pendiente (requiere acceso a la máquina).
- [ ] Análisis de ISO pendiente.
