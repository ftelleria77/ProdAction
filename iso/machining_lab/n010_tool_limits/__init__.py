"""N010 — Topes de feed/spindle por herramienta vertical.

El def.tlgx embebido no es fiable (su Standard no coincide con el ISO real: D5 flat
dice 3 pero N004 dio F2000). Los topes reales se derivan empíricamente: un agujero por
herramienta con override enorme (feed=9.999 m/min, spindle=99999 rpm) → el ISO clampa al
máximo de cada tool, revelando max_feed (y si el spindle clampa) por diámetro/punta.
"""
