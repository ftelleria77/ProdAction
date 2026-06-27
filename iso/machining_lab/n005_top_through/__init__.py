"""N005 — Top drill pasante (is_through) plano, para derivar el z_cut del pasante.

Usa D8 (queda Flat; D5 pasante se vuelve Conical y va en la tanda de cónicos).
Varía espesor × extra_depth para aislar la fórmula de profundidad del pasante.
Hipótesis: z_cut = tlc - extra_depth (fondo de mesa en z=tlc, ignora target_depth).
"""
