"""N004 — Top drill: derivar la tabla por diámetro (etk6/etk0/spindle/feed/shf).

El converter hoy hardcodea solo D5/D8/D15. def.tlgx + oheads.cfg confirman que
también hay D4/D20/D35 montadas (etk6 = tool# de def.tlgx). Esta serie genera un
top drill simple por diámetro para derivar de los ISO de Maestro los valores que
no salen limpiamente de la config (etk0, spindle, feed, shf_x/y/z por husillo).
"""
