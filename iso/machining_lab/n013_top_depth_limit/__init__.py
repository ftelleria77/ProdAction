"""N013 — Límite de hundimiento del taladro vertical (def.tlgx SinkingLength).

Igual que el lateral: el vertical no puede hundirse más que su SinkingLength. La D20
(tool 003) tiene SinkingLength=20 → un pasante en panel de 40 mm (40 > 20) debe dar error.
Mapea el borde para confirmar antes de implementar el límite en el converter.
"""
