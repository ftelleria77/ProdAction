"""Rutas raíz de los subsistemas de archivos de máquina.

Convención:
  PGMX_ROOT  — S:\\Maestro\\Projects\\ProdAction
               Archivos .pgmx: tanto los generados manualmente en Maestro
               como los sintetizados por el subsistema pgmx/.

  ISO_ROOT   — P:\\USBMIX\\ProdAction
               Archivos .iso: tanto los postprocesados por Maestro desde
               los .pgmx como los convertidos por el subsistema iso/.

Cada estudio o lote vive en un subdirectorio con el mismo nombre bajo
ambas raíces, de modo que el par PGMX/ISO de una pieza siempre se ubica
en rutas simétricas.

Ejemplo para el lote R001 (reinvestigación):
  PGMX: S:\\Maestro\\Projects\\ProdAction\\R001_programa_vacio\\R_PV_base.pgmx
  ISO:  P:\\USBMIX\\ProdAction\\R001_programa_vacio\\R_PV_base.iso

La serie N (época anterior, archivada 2026-08-07) vive en el subdirectorio
`Investigacion iso_converter\\` de AMBAS raíces y no se usa como evidencia
durante la reinvestigación.
"""

from pathlib import Path

PGMX_ROOT: Path = Path(r"S:\Maestro\Projects\ProdAction")
ISO_ROOT: Path = Path(r"P:\USBMIX\ProdAction")
