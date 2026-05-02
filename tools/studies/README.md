# Herramientas De Estudio

Este directorio agrupa scripts reproducibles de investigacion que no forman
parte del flujo productivo principal.

- `iso/minimal_fixtures_2026_05_03.py`: tanda minima usada para estudiar el
  postprocesado Maestro/ISO.
- `cut_diagrams/ordering_lab.py`: laboratorio comparativo de ordenamientos y
  packers de guillotina.

La regla de mantenimiento es no sumar nuevos scripts puntuales en el nivel
principal de `tools/`. Si el caso es exploratorio, debe entrar aqui con un
nombre de estudio claro; si se estabiliza como API, debe migrar a `core/` o a
una herramienta publica documentada.
