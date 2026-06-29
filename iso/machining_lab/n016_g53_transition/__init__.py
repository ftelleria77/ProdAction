"""N016 — Re-derivar el g53 de transición (Top→Side) con security_plane variable.

El g53 lateral usa hoy `DZ + SECURITY_SIDE(20) + max(eff(sp)+shf_z)`, eff(sp)=max(sp,5).
Esos dos números (el +20 fijo y el piso 5) se "validaron" con N003 = config de Maestro
DESCARTADA. Esta tanda barre el security_plane lateral en una transición Top→Side (config
canónica) para confirmar si el +20 es fijo o sigue al sp (como pasó con el approach, N014),
y si el piso 5 es real. Un taladro vertical + uno lateral Front Ø8.
"""
