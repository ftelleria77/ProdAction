"""N008 — Patrones de perforado (ReplicationPattern rectangular) con D8 ciego.

Un patrón se posprocesa como varias perforaciones individuales. Esta serie deriva:
  - dónde cae el `center` respecto de la grilla (¿esquina o centro?),
  - el orden en que Maestro emite los agujeros (row-major / column-major / serpentina).
para luego expandir el DrillPatternSpec a DrillSpec individuales en el converter.
"""
