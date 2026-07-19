"""Fresado: operaciones de TRAZA (line, channel, circle, arc, polyline, contour, pocket).

⚠️ El corte `milling/` vs `drilling/` es por la NATURALEZA de la operación, NO por el cabezal:

    milling  = la herramienta RECORRE un camino sobre la pieza (traza continua)
    drilling = la herramienta baja y sube en un PUNTO

El CANAL es la prueba de que el criterio no es el cabezal: lo hace la Sierra Vertical X, que vive
fija en el mandril 82 del cabezal PERFORADOR (ver `iso/synthesis/_saw.py`) — y aun así es un
fresado, porque recorre. En el ISO su cuerpo es estilo router (G0 → D1/SVL/SVR → plunge → corte
lineal); lo único propio del perforador es el header (`?%ETK[6]=82`) y el epílogo.

El criterio coincide con el vocabulario de Maestro (fresado / perforación), que es el que manda.
"""
