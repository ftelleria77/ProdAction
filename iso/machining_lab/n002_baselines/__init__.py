"""N002 — Segunda serie de fixtures para el convertidor PGMX→ISO.

Foco: validar la fórmula del G53 Z de transición lateral
(`g53_z = 83.000 + max(shf_z_origen, shf_z_destino)`) y desacoplar la base
83.000 de la geometría de pieza (origin_z, espesor, posición del agujero),
que en N001 estaban todas fijas.
"""
