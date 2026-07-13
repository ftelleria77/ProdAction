# iso.synthesis — módulos productivos del convertidor PGMX→ISO.
#
# EJE DE ORGANIZACIÓN — ojo, NO es el mismo que el del sintetizador:
#
#   pgmx/synthesis/  se organiza por FEATURE     (line, channel, circle, arc, polyline, ...)
#   iso/synthesis/   se organiza por UNIDAD DE EJECUCIÓN (quién ejecuta, no qué se ejecuta)
#
#       _router.py      electromandril: line, circle, arc, polyline (y luego contour/pocket)
#       _saw.py         Sierra Vertical X (mandril 82 del cabezal perforador): el canal
#       _top_drill.py   perforador, taladros verticales
#       _side_drill.py  perforador, taladros laterales
#
# La asimetría es deliberada: el usuario AUTORA por feature, pero lo que determina la ESTRUCTURA
# del ISO (header, códigos ETK, transiciones entre operaciones, epílogo) es la unidad que ejecuta.
# Por eso `_reader.py` agrupa las specs en routers / saw_channels / top_drills / side_drills, y
# `converter.py` emite un bloque por grupo. El canal lo prueba: es un fresado (`ChannelSpec`, vive
# en milling/), pero su ISO se arma en `_saw.py` porque lo corta la sierra — aunque su CUERPO sea
# estilo router (`_saw.py` importa `_g1_cut` de `_router`).
#
# Antes de mover un render de archivo: preguntá QUIÉN lo ejecuta, no QUÉ es.

from .converter import convert

__all__ = ["convert"]
