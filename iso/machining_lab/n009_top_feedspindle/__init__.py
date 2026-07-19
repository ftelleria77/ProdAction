"""N009 — Override de feedrate/spindle por operación en taladro vertical (D8 ciego).

El converter hoy usa F/S por herramienta (TOP_TOOL) y el fail-loud rechaza overrides.
Esta serie deriva cómo el override del spec cambia el `S....M3` y el `F` del corte, y
en qué unidades entra el feedrate (dos valores distintos lo desambiguan).
"""
