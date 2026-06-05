# Vaciado V2 - Memoria Temporal

Ultima actualizacion: 2026-05-31

## Proposito

Esta memoria temporal concentra el plan y la investigacion para reconstruir el
codigo de sintesis de `Vaciado` desde cero, usando el conocimiento acumulado
pero corrigiendo el enfoque actual.

La idea central es separar topologia, estrategia, profundidad y serializacion
Maestro. El codigo viejo queda como referencia y oraculo hasta que el nuevo
motor demuestre equivalencia por lote; al final se elimina el codigo viejo.

## Reglas De Trabajo

- El motor nuevo debe nacer en paralelo al viejo.
- El codigo nuevo no debe importar `tools.pgmx_vaciado.trace_engine`.
- Los nombres nuevos deben ser geometricos, no nombres de casos:
  `single_seed_balanced`, `two_seed_bridge`, `right_wall_seed`, etc.
- Las variantes de estrategia son ejes ortogonales, no tipos de vaciado:
  herramienta, `Overlap`, `AllowanceSide`, sentido, `InsideToOutSide`,
  `StrokeConnectionStrategy`, multipaso y helicoidal futura.
- Maestro sigue siendo el oraculo de validacion, pero no debe ser la explicacion
  conceptual de la traza.
- No borrar el motor viejo hasta tener equivalencia validada para los casos ya
  soportados.
- Registrar hallazgos con fecha ISO y distinguir hecho observado, inferencia y
  decision.

## Plan De Reconstruccion

1. Congelar evidencia.
   - Crear matriz viva de casos `Vaciado_001..035` y variantes `E001..E007`.
   - Registrar topologia, estrategia, estado, salida esperada y resolvedor viejo.

2. Crear modulo nuevo.
   - Candidato: `tools/pgmx_vaciado_v2/`.
   - Debe consumir specs/adaptadores estables o `.pgmx`, no el motor viejo.

3. Definir contrato nuevo.
   - `VaciadoGeometry`: contorno exterior, islas fisicas, semillas de ruta.
   - `VaciadoStrategy`: herramienta, overlap, allowance, sentido, orden y
     conexion.
   - `VaciadoDepth`: pasada simple, multipaso y helicoidal futura.
   - `VaciadoTrace`: primitivas geometricas, eventos y secuencia final.

4. Construir motor por capas.
   - `geometry.py`: puntos, lineas, arcos, bbox, winding.
   - `offsets.py`: familias de offset.
   - `events.py`: completo, parcial, puente, contacto con pared, cruce entre
     islas, lobulo terminal.
   - `topology.py`: offsets + eventos -> recorrido abstracto.
   - `traversal.py`: aplica `InsideToOutSide` y `RotationDirection`.
   - `connectors.py`: seguridad (`LiftShiftPlunge`) o conexion en pieza
     (`Straghtline`).
   - `depth.py`: niveles Z y multipaso.
   - `maestro_serializer.py`: cortes y arcos equivalentes a Maestro.

5. Meta 1: rectangulares sin islas.
   - Reproducir `Vaciado_001..019`.
   - Validar herramienta, overlap, allowance, sentido, conexion y multipaso.

6. Meta 2: una semilla.
   - Reproducir `Vaciado_027`, `Vaciado_028` y variantes `E001..E007`.
   - Evitar funciones nombradas por caso.

7. Meta 3: multiples semillas.
   - Reproducir `Vaciado_029` y `Vaciado_030`.
   - Modelar puentes, lobulos, contacto con pared y recortes como eventos.

8. Meta 4: cerrar pendiente real.
   - Resolver `Vaciado_031` base con el modelo nuevo.
   - Toda regla nueva debe nombrarse como evento/topologia general.

9. Meta 5: circular/non-polyline.
   - Abordar `Vaciado_035`.
   - Decidir curvas nativas vs polilinizacion con tolerancia explicita.

10. Comando productivo de lote.
    - Regenerar soportados.
    - Comparar contra Maestro.
    - Reportar exactos, mismatches, no soportados y saltados.
    - No dejar archivos invalidos en `generated`.

11. Cutover.
    - Integrar motor nuevo en `tools.synthesize_pgmx`.
    - Redirigir tests al motor nuevo.
    - Borrar `trace_engine.py` viejo y helpers obsoletos.
    - Actualizar memoria y documentacion.

## Taxonomia Inicial

Topologias conocidas:

- `rectangular_no_islands`: contorno rectangular sin islas.
- `single_seed_balanced`: una semilla rectangular con claros balanceados.
- `single_seed_unbalanced`: una semilla rectangular desplazada.
- `two_seed_symmetric`: dos semillas/islas rectangulares simetricas.
- `right_wall_seed`: semilla de ruta contra pared derecha.
- `multi_seed_hybrid`: pendiente; guia actual `Vaciado_031` base.
- `non_polyline_outer`: pendiente; guia actual `Vaciado_035`.

Ejes de estrategia:

- `tool_width`.
- `overlap`.
- `allowance_side`.
- `rotation_direction`.
- `inside_to_outside`.
- `stroke_connection_strategy`.
- `allow_multiple_passes`.
- `is_helic_strategy`.

Eventos geometricos:

- `complete_offset`.
- `partial_offset`.
- `bridge_between_seed_and_outer`.
- `bridge_between_seeds`.
- `wall_contact`.
- `seed_crossing`.
- `terminal_lobe`.
- `maestro_serialization_cut`.

## Estado Inicial

- Cerrado por el motor viejo: rectangulares sin islas, `Vaciado_027`,
  `Vaciado_028`, `Vaciado_029` y `Vaciado_030`.
- Pendiente real: `Vaciado_031` base, `Vaciado_035`, y comando productivo de
  lote.
- Riesgo principal: repetir el patron viejo de acumular ramas por caso en vez
  de consolidar eventos geometricos reutilizables.

## Registro De Avances

### 2026-05-31

- Se decidio reconstruir el motor de `Vaciado` desde cero en paralelo al viejo.
- Se registro el plan para separar topologia, estrategia, profundidad y
  serializacion.
- Se creo la matriz base inicial en
  `tools/pgmx_vaciado/memory/vaciado-v2-baseline.md`.
- Se recupero acceso a `S:` y `P:` remapeando las unidades persistentes contra
  `\\gateway.mobile.local`.
- Se encontro Python real en
  `C:\Users\fermi\AppData\Local\Python\bin\python3.exe`; los aliases
  `py`/`python` de `WindowsApps` siguen siendo no confiables.
- Validacion: `python3 -B -m unittest tests.test_pgmx_vaciado` corrio `57`
  tests `OK`.
- Se regeneraron reportes externos en
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_v2_baseline_2026_05_31`:
  scanner `232` filas, `78` casos manuales, `77` adaptados, `1`
  `snapshot_only`, `14499` primitivas.
- Se creo el paquete experimental `tools/pgmx_vaciado_v2/`, sin importar
  `tools.pgmx_vaciado.trace_engine`.
- Primer contrato V2 implementado:
  - `adapters.py`: adaptador desde `PocketMillingSpec` estable hacia contrato
    V2;
  - `geometry.py`: `BBox`, `PolylineContour`, `VaciadoGeometry`;
  - `strategy.py`: `VaciadoStrategy`, con `effective_offset` y `radial_step`;
  - `depth.py`: `VaciadoDepth`;
  - `trace.py`: `plan_rectangular_no_islands`, `OffsetFamily` y
    `RectangularNoIslandTracePlan`.
- Se agrego `tests/test_pgmx_vaciado_v2.py` con 5 tests para:
  - offsets rectangulares sin islas;
  - `InsideToOutSide` como reordenamiento de recorrido;
  - `AllowanceSide` y `Overlap` como ejes de estrategia;
  - rechazo explicito de geometria interna en la meta 1.
  - adaptacion de `manual/Vaciado_008.pgmx` real desde `PocketMillingSpec`.
- Validacion:
  - `python3 -B -m unittest tests.test_pgmx_vaciado_v2`: `5` tests `OK`;
  - `python3 -B -m unittest tests.test_pgmx_vaciado`: `57` tests `OK`.
- Proximo paso recomendado: ampliar la validacion V2 de
  `rectangular_no_islands` contra `Vaciado_001..019` usando solo contrato V2 y
  plan de offsets, antes de emitir trayectorias.

### 2026-05-31 - Validacion Rectangular Estable V2

- Se amplio la validacion V2 al subconjunto rectangular estable completo:
  `Vaciado_001..021`, `Vaciado_023..026` y `Vaciado_032..034`.
- La prueba adapta cada `.pgmx` real desde `PocketMillingSpec`, construye el
  contrato V2 y verifica que el bbox real de `TrajectoryPath` Maestro coincida
  con el primer offset calculado por `plan_rectangular_no_islands`.
- Hallazgos de normalizacion:
  - `Vaciado_002` es rectangular aunque arranca en el medio del borde inferior;
    V2 debe aceptar rectangulos con puntos colineales extra sobre el perimetro.
  - `Vaciado_026` conserva ruido flotante en una esquina
    (`99.99999999999994`, `325.00000000000006`); V2 debe comparar vertices con
    tolerancia, no por igualdad exacta.
- Se ajusto `PolylineContour.is_axis_aligned_rectangle` para aceptar ambas
  situaciones sin relajar a poligonos arbitrarios.
- Validacion:
  - `python3 -B -m unittest tests.test_pgmx_vaciado_v2`: `6` tests `OK`;
  - `python3 -B -m unittest tests.test_pgmx_vaciado`: `57` tests `OK`.
- Proximo paso recomendado: agregar primitivas abstractas V2 para loops
  rectangulares, manteniendo separadas la familia de offsets y la serializacion
  Maestro.

### 2026-05-31 - Primitivas Rectangulares Abstractas V2

- Se agrego `tools/pgmx_vaciado_v2/primitives.py` con:
  - `TracePrimitive2D`;
  - `TracePrimitiveSequence2D`;
  - `rectangular_loop_sequence(...)`.
- `plan_rectangular_no_islands` ahora produce `primitive_sequences` en el orden
  de `traversal_offsets`.
- La orientacion se modela como politica de estrategia:
  - `CounterClockwise`: abajo -> derecha -> arriba -> izquierda;
  - `Clockwise`: izquierda -> arriba -> derecha -> abajo.
- La serializacion Maestro sigue fuera de V2. Esta capa solo describe
  primitivas geometricas abstractas.
- Tests agregados:
  - orden de `primitive_sequences` segun `InsideToOutSide`;
  - loop rectangular `CounterClockwise`;
  - loop rectangular `Clockwise`.
- Validacion:
  - `python3 -B -m unittest tests.test_pgmx_vaciado_v2`: `8` tests `OK`;
  - `python3 -B -m unittest tests.test_pgmx_vaciado`: `57` tests `OK`.
- Proximo paso recomendado: crear una capa de trayectoria 3D V2 para una sola
  profundidad, derivada de primitivas abstractas, y compararla contra puntos
  Maestro en el subset rectangular estable.

## Preguntas Abiertas

- Nombre definitivo del paquete nuevo: `tools/pgmx_vaciado_v2/` u otra ruta.
- Formato de la matriz viva: Markdown, CSV o JSON versionado.
- Criterio para aceptar curvas nativas en `Vaciado_035`.
- Alcance minimo del comando productivo de lote para declarar cutover.
