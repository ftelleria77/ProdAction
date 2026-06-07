# Auditoria De `tools/studies/`

Estado: bloque auditado como laboratorio reproducible, 2026-06-07.

`tools/studies/` agrupa scripts de investigacion versionados. No es API
productiva ni punto de entrada para usuarios finales. Su responsabilidad es
conservar evidencia ejecutable, generar fixtures y comparar hipotesis antes de
promover reglas a `core/`, `pgmx/` o `iso_state_synthesis/`.

## Mapa Actual

| Ruta | Responsabilidad |
| --- | --- |
| `tools/studies/README.md` | Frontera general de estudios reproducibles. |
| `tools/studies/cut_diagrams/ordering_lab.py` | Laboratorio archivado de ordenamientos y packers de guillotina. Consume contratos publicos/compatibles de `app` y `core.nesting`. |
| `tools/studies/iso/README.md` | Catalogo de estudios ISO fechados y criterio de promocion. |
| `tools/studies/iso/*_fixtures_*.py` | Generadores fechados de fixtures PGMX para aislar reglas Maestro/ISO. |
| `tools/studies/iso/top_drill_*_2026_05_13.py` | Estudios vivos de ordenamiento de taladros superiores contra corpus pareado. |
| `tools/studies/iso/txh001_transition_audit_2026_05_13.py` | Auditoria viva de la transicion `T-XH-001`. |
| `tools/studies/iso/block_transition_corpus_analysis_2026_05_13.py` | Auditoria viva de residuales por bloque/transicion del sintetizador ISO. |

## Fronteras

- Los estudios de corte pueden depender de `app.project_store`, `app.settings`
  y del contrato compatible de `core.nesting`.
- Los estudios ISO de fixtures pueden depender de `pgmx.synthesis` y
  `pgmx.adapters`.
- Las auditorias ISO vivas pueden emitir candidatos mediante
  `iso_state_synthesis.emitter`, pero deben importar comparacion desde
  `iso_state_synthesis.comparison` y agrupamiento desde
  `iso_state_synthesis.work_groups`.
- Ningun script de estudio debe convertirse en dependencia productiva directa.
  Si una regla se estabiliza, se promueve al subsistema correspondiente con
  tests o comando reproducible.

## Procesos Donde Interviene

| Proceso | Entrada | Salida | Codigo |
| --- | --- | --- | --- |
| Comparar ordenamientos de corte | Proyecto real + settings | Reporte de tableros/placas/merma | `cut_diagrams.ordering_lab.run_experiments`. |
| Generar fixtures ISO | Parametros embebidos + baseline PGMX | Lotes `.pgmx` y CSV de manifest | `tools.studies.iso.*_fixtures_*.generate`. |
| Auditar corpus ISO | Raices PGMX/ISO pareadas | CSV/Markdown de residuales | `txh001_transition_audit_2026_05_13`, `block_transition_corpus_analysis_2026_05_13`. |
| Preparar evidencia futura | Scripts fechados | Casos reproducibles para Maestro | Catalogo de `tools/studies/iso/README.md`. |

## Lectura De Codigo

`ordering_lab.py` es grande porque conserva varios algoritmos experimentales en
un solo archivo fechado. Eso es aceptable mientras siga archivado como
laboratorio y no como API. Ya no importa helpers privados de `app`; usa
`app.project_store`, `app.settings` y `core.nesting`.

Los estudios ISO mantienen nombres fechados y CLI con `argparse`. Varios
insertan la raiz del repo en `sys.path` para poder ejecutarse como scripts de
estudio desde entornos simples; no se promueve ese patron a codigo productivo.

## Comentarios Y Documentacion

La frontera general y el catalogo ISO estan documentados. Los docstrings de los
scripts principales explican si son fixtures, analisis o auditorias. Para una
auditoria real no alcanza leer comentarios: hay que mirar el README de la
carpeta, el nombre fechado del script y el subsistema al que apunta.

## Deuda Residual Aceptada

- `tools/studies/` no tiene suite dedicada completa. La validacion base es
  `compileall`, import/`--help` puntual y ejecucion manual cuando existe corpus
  externo.
- `ordering_lab.py` conserva algoritmos extensos en un unico modulo; su
  contrato vivo con produccion es `core.nesting_compat.LAB_COMPATIBILITY_NAMES`.
- Las auditorias ISO dependen de corpus externo Maestro/ISO para ser utiles.
  La auditoria funcional del sintetizador ISO queda pausada y no dirige este
  cierre general.
- No deben agregarse scripts nuevos en `tools/` raiz; los estudios nuevos van
  bajo `tools/studies/<tema>/` o a un paquete experimental documentado.

## Validacion Del Bloque

Comandos esperados:

```powershell
py -3 -m compileall -q tools
py -3 -m compileall -q main.py app core pgmx iso_state_synthesis cnc_traceability tools tests
py -3 -m unittest discover -s tests -p "test*.py"
```
