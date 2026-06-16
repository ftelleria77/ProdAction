# N001 — Estado actual

Última actualización: 2026-06-16

## Fixtures

24 archivos `.pgmx` en `S:\Maestro\Projects\ProdAction\N001_baselines\`.  
24 archivos `.iso` postprocesados en `P:\USBMIX\ProdAction\N001_baselines\`.

## Análisis

**Completado.** Ver `iso/docs/experiments/n001/analysis.md`.

Todas las preguntas abiertas (Q-A01..Q-D02) tienen respuesta.

## Hallazgos principales

### Reordenamiento de Maestro
Maestro ignora el orden del PGMX. Ejecuta siempre: **Router → Top drill → Side drill**.
Dentro de la misma familia, misma herramienta = mismo bloque (sin re-setup).

### Top drill
- ETK[6]: D5=5, D8=1, D15=2
- ETK[0]: D5=16, D8=1, D15=2
- Z_cut = 95 − target_depth | Z_security = 115
- Spindle: D5/D8 = 6000 rpm, D15 = 4000 rpm

### Side drill
- ETK[6]: Left=61, Right=60, Front=58, Back=59
- ETK[0]: Left/Right = 0x80000000, Front/Back = 0x40000000
- ETK[8]: Left=3, Right=2, Front=5, Back=4
- TLC_LATERAL = 37 (constante de máquina)
- Security margin = 20 mm
- Z_side = center_y (height from piece bottom)

### Router E004
- ATC: T4 / M06 / ETK[6]=1 / ETK[9]=4 / ETK[18]=1 / S18000M3
- Z_approach = 127.200, Z_cut = −target_depth, Z_retract = security_plane
- SVL = Z_approach − security_plane, SVR = tool_width / 2
- Segunda pasada: no re-setup, G17 + doble G0 a nueva posición

## Próximo paso

Implementar el convertidor productivo en `iso/synthesis/` usando las reglas del análisis.
