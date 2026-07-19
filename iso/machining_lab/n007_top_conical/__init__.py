"""N007 — Top drill cónico: única broca cónica de la máquina = tool 007 (D5 punta
cónica), auto-seleccionada por el sintetizador en D5 + pasante (salvo override a
punta plana). Cualquier otro Ø es siempre plano.

Deriva del ISO los parámetros de la tool 007 (etk6/etk0/spindle/feed/shf) y la regla
de z_cut del cónico-pasante. Incluye un control D5-pasante-plano (tool 005) para
contraste. Brocas cónicas adicionales / taper_height arbitrario requieren reinstalar
herramientas (cambian config + def.tlgx embebido) → extensión futura.
"""
