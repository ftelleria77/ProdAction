# iso/data — Configuración de máquina

Snapshots de los archivos de configuración de la máquina CNC SCM Group
necesarios para la síntesis ISO.

## Contenido

```
machine_config/   Archivos de configuración de Xilog Plus.
  NCI.CFG         Plantillas de preámbulo y cierre ($GEN_INIT, $GEN_END).
  NCI_ORI.CFG     Configuración de origen y referencias de ejes.
  pheads.cfg      Tabla de cabezales: spindles, herramientas y offsets.
```

Estos archivos no se modifican manualmente. Son capturas (snapshots) de la
configuración real de la máquina en producción.
