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
- Proximo paso recomendado: crear la matriz de evidencia/base antes de escribir
  codigo nuevo.

## Preguntas Abiertas

- Nombre definitivo del paquete nuevo: `tools/pgmx_vaciado_v2/` u otra ruta.
- Formato de la matriz viva: Markdown, CSV o JSON versionado.
- Criterio para aceptar curvas nativas en `Vaciado_035`.
- Alcance minimo del comando productivo de lote para declarar cutover.
