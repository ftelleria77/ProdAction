"""Perforado: operaciones PUNTUALES (single = un taladro, pattern = su repetición rectangular).

El corte contra `milling/` es por la NATURALEZA de la operación (punto vs traza), NO por el
cabezal: la Sierra Vertical X vive en el cabezal perforador y sin embargo su canal es un fresado
(ver el docstring de `pgmx/synthesis/milling/__init__.py`).

Los módulos NO se llaman `drill.py` / `drill_pattern.py`: el paquete ya nombra la feature, y
`drilling.drill` solo tartamudearía. `single` y `pattern` son sus dos formas.
"""
