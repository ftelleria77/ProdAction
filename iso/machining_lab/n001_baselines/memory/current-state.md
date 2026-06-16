# N001 — Estado actual

Última actualización: 2026-06-16

## Fixtures generados

20 archivos `.pgmx` en `S:\Maestro\Projects\ProdAction\ISO\N_new_engine_2026_06_15\`.
Generados con `generate.py`. SHA256 registrado en el manifiesto de salida.

## Pendiente

- Conversión a ISO con Maestro (requiere acceso físico a la máquina CNC).
- Análisis de los ISO resultantes con `analyze.py`.

## Preguntas abiertas que responde este lote

| ID | Pregunta |
| --- | --- |
| Q-A01 | ¿Qué valores toman ETK[6] y ETK[0] para cada diámetro de taladro vertical (D5, D8, D15)? |
| Q-A02 | ¿Cuál es la fórmula exacta de Z de corte en taladro vertical? |
| Q-A03 | ¿Cómo cambia el bloque de herramienta entre dos agujeros de la misma herramienta vs. herramienta distinta? |
| Q-A04 | ¿Qué velocidad de spindle (S...M3) usa cada diámetro de taladro vertical? |
| Q-B01 | ¿Qué valores toman ETK[6] y ETK[0] para cada cara lateral (Left, Right, Front, Back)? |
| Q-B02 | ¿Cuál es la fórmula de la cota fija lateral en cada cara? |
| Q-B03 | ¿Cómo se representa el cambio de cara en el ISO? |
| Q-C01 | ¿Cuál es la secuencia exacta de transición top→side, side→top, top→router, router→top? |
| Q-D01 | ¿Cuál es el bloque completo de preparación de router E004 para una pasada lineal? |
| Q-D02 | ¿Cómo se representa una segunda pasada con la misma herramienta? |
