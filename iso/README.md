# iso — Convertidor PGMX → ISO

Paquete para la conversión directa de archivos `.pgmx` (Maestro) a código ISO
(G-code) para la máquina CNC SCM Group.

## Estructura

```
iso/
  data/           Configuración de máquina: snapshots de NCI.CFG, pheads.cfg, etc.
  docs/           Documentación de investigación y uso.
    memory/       Memoria acumulada de parámetros ISO observados.
    experiments/  Resultados de estudios controlados con fixtures.
    contracts/    Contratos de interfaz y formato XISO intermedio.
  machining_lab/  Laboratorio de pruebas empíricas.
    n001_baselines/  Primer lote de fixtures: taladro vertical, lateral y router.
  synthesis/      Módulos productivos del convertidor.
```

## Enfoque

El convertidor se construye desde cero mediante análisis empírico:

1. Generar fixtures `.pgmx` con variaciones controladas.
2. Convertir a ISO con Maestro en la máquina CNC.
3. Analizar los ISO resultantes para derivar las reglas de conversión.
4. Implementar cada regla con su nivel de confianza documentado.

El código productivo en `synthesis/` solo incorpora reglas validadas contra
corpus Maestro real. Las hipótesis sin validar viven en `machining_lab/`.
