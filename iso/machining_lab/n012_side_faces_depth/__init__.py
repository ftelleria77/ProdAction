"""N012 — Confirmar la fórmula del cut lateral en Left/Right/Back a depth≠28.

El fix de N011 (cut = borde ∓ TLC_CUT ± depth, approach fijo) se midió en Front.
N001 solo prueba las otras caras a depth=28 (donde el código viejo y el nuevo coinciden).
Esta tanda las prueba a depth=15 para confirmar la dirección de la profundidad por cara.
"""
