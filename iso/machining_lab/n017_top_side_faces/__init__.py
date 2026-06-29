"""N017 — Confirmar la transición Top→Side en Right y Back (bloque SHF + piso/shf).

N016 (Front) mostró que la transición Top→Side NO lleva el bloque SHF previo al G40, y
N001 c001 (Left) sí lo lleva. La hipótesis (igual que la restauración del epílogo) es:
Left/Back llevan el bloque, Front/Right no. Esta tanda prueba Right (debería NO llevarlo)
y Back (debería llevarlo), a sp=2 (piso) y sp=20.
"""
