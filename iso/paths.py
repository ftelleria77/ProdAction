"""Rutas raíz de los subsistemas de archivos de máquina.

Convención:
  PGMX_ROOT  — S:\\Maestro\\Projects\\ProdAction
               Archivos .pgmx: tanto los generados manualmente en Maestro
               como los sintetizados por el subsistema pgmx/.

  ISO_ROOT   — P:\\USBMIX\\ProdAction
               Archivos .iso: tanto los postprocesados por Maestro desde
               los .pgmx como los convertidos por el subsistema iso/.

Cada estudio o lote de producción vive en un subdirectorio con el mismo
nombre bajo ambas raíces, de modo que el par PGMX/ISO de una pieza
siempre se ubica en rutas simétricas.

Archivo de la serie N (2026-08-07): Fermín movió TODAS las carpetas de la
serie N, en AMBAS raíces, al subdirectorio `Investigacion iso_converter\\`
— la simetría se conserva, un nivel más abajo. La serie nueva de la
reinvestigación (R001+) sigue en la raíz de ambas.

Ejemplo para el lote N001:
  PGMX: S:\\Maestro\\Projects\\ProdAction\\Investigacion iso_converter\\N001_baselines\\N_A001_top_1hole_D5.pgmx
  ISO:  P:\\USBMIX\\ProdAction\\Investigacion iso_converter\\N001_baselines\\N_A001_top_1hole_D5.iso
"""

from pathlib import Path

PGMX_ROOT: Path = Path(r"S:\Maestro\Projects\ProdAction")
ISO_ROOT: Path = Path(r"P:\USBMIX\ProdAction")
