# Plan De Modularizacion Del Sintetizador PGMX

Estado: plan arquitectonico inicial, 2026-06-02.

Este plan convierte el frente abierto de `ClosedPocket`/pocket milling en un
patron general para desarrollar mecanizados del sintetizador PGMX. La meta es
que cada familia de
mecanizado tenga el mismo recorrido:

1. evidencia y experimentacion en laboratorio;
2. contrato de dominio estable;
3. adaptacion desde snapshots Maestro;
4. sintesis productiva `.pgmx`;
5. pruebas de compatibilidad y regresion;
6. fachadas historicas sin logica nueva.

No se mueve codigo como parte de este documento. El primer objetivo es fijar el
mapa de destino para poder migrar sin cambiar comportamiento.

## Principios

- `pgmx.synthesis` sigue siendo la API publica del sintetizador.
- `tools.synthesize_pgmx` y `tools.pgmx_synthesis` siguen siendo fachadas de
  compatibilidad.
- Los laboratorios no son dependencia productiva directa.
- Las reglas pasan a produccion solo cuando tienen evidencia Maestro, tests y
  un contrato de dominio claro.
- `Vaciado` deja de ser una excepcion nominal: se integra en la familia
  Maestro `ClosedPocket`/pocket milling, igual que los demas mecanizados se
  integran en su familia correspondiente.
- La modularizacion se hace por movimiento controlado: primero mover codigo sin
  cambio funcional, despues ajustar dependencias.

## Estructura Objetivo

```text
pgmx/
  synthesis/
    __init__.py              # API publica estable
    core.py                  # fachada interna temporal durante la migracion
    common/
      program.py             # orquestacion de request, estado, worksteps y escritura final
      xml.py                 # namespaces, nodos, IDs, serializacion comun
      geometry.py            # primitivas, perfiles y curvas reutilizables
      depth.py               # reglas de profundidad y cota de corte
      piece.py               # pieza: dimensiones, origen, planos/caras
      tools.py               # catalogo y validaciones de herramienta
      strategy.py            # estrategias Maestro comunes
      hydration.py           # lectura de templates/source-pgmx
      leads.py               # acercamiento/alejamiento Maestro
    milling/
      line.py
      slot.py
      profile.py             # polilineas abiertas/cerradas y perfiles con arcos
      circle.py
      squaring.py
      pocket.py              # ClosedPocket / pocket milling productivo
    drilling/
      single.py
      pattern.py
  machining_lab/
    README.md
    pocket_milling/
      ...
    line_milling/
      ...
    slot_milling/
      ...
    profile_milling/
      ...
    drilling/
      ...
```

`pgmx/machining_lab/` es el destino conceptual del laboratorio general. El
laboratorio actual `pgmx/vaciado_lab/` y el contrato experimental
`pgmx/vaciado/` son fuentes historicas de migracion: en el mapa objetivo ambos
desaparecen como paquetes propios y su contenido util se integra en
`pgmx.synthesis.milling.pocket` y `pgmx.machining_lab.pocket_milling`.
Las rutas historicas bajo `tools/` solo pueden quedar como fachadas temporales
durante la transicion.

## Familias

| Familia | Contrato actual | Produccion objetivo | Laboratorio objetivo |
| --- | --- | --- | --- |
| Linea | `LineMillingSpec` | `pgmx.synthesis.milling.line` | `pgmx.machining_lab.line_milling` |
| Ranura | `SlotMillingSpec` | `pgmx.synthesis.milling.slot` | `pgmx.machining_lab.slot_milling` |
| Perfil | `PolylineMillingSpec`, `CircleMillingSpec` | `pgmx.synthesis.milling.profile`, `circle` | `pgmx.machining_lab.profile_milling` |
| Escuadrado | `SquaringMillingSpec` | `pgmx.synthesis.milling.squaring` | `pgmx.machining_lab.squaring` |
| Pocket / ClosedPocket | `PocketMillingSpec`, legado `pgmx.vaciado` | `pgmx.synthesis.milling.pocket` | `pgmx.machining_lab.pocket_milling` |
| Taladro | `DrillingSpec` | `pgmx.synthesis.drilling.single` | `pgmx.machining_lab.drilling` |
| Patron de taladros | `DrillingPatternSpec` | `pgmx.synthesis.drilling.pattern` | `pgmx.machining_lab.drilling` |
| Xn | `XnSpec` | `pgmx.synthesis.common.program` | sin laboratorio propio |

## Flujo De Promocion

Cada familia debe avanzar con el mismo protocolo:

1. `machining_lab`: catalogar ejemplos, generar analisis y documentar memoria
   viva.
2. `pgmx.<familia>` o subcontrato equivalente: modelar geometria, estrategia,
   profundidad y restricciones sin XML productivo.
3. `pgmx.adapters`: adaptar snapshots Maestro al contrato publico o al contrato
   V2 de la familia.
4. `pgmx.synthesis.<familia>`: serializar XML productivo sin depender del
   laboratorio.
5. Tests:
   - smoke import de API/fachadas;
   - unidad del contrato de dominio;
   - adaptacion desde corpus Maestro;
   - sintesis contra baseline;
   - roundtrip o comparacion exacta cuando exista fixture manual.
6. Documentacion:
   - README del laboratorio;
   - memoria temporal o current-state del frente;
   - ayuda publica si cambia la API.

## Etapas

### Etapa 1 - Inventario Y Frontera

- Listar funciones y dataclasses exportadas por `pgmx.synthesis.core`.
- Marcar cuales son comunes y cuales pertenecen a una familia.
- Registrar dependencias actuales desde `pgmx.synthesis.core` hacia
  `pgmx.vaciado_lab`.
- Crear una matriz de tests que cubra cada familia antes de mover codigo.

Salida esperada: inventario documentado y tests verdes sin cambios funcionales.

### Etapa 2 - Laboratorio General

- Crear `pgmx/machining_lab/README.md`.
- Crear `pgmx/machining_lab/pocket_milling/` como destino del laboratorio
  actual.
- Mover primero documentacion y memoria de `Vaciado` hacia el laboratorio
  `pocket_milling`, dejando referencias compatibles solo mientras dure la
  transicion.
- Despues mover modulos de analisis y trace engine, manteniendo
  `pgmx.vaciado_lab.*` como fachada temporal.
- Actualizar `tools.pgmx_vaciado.*` para que apunte al nuevo destino indirecto.

Salida esperada: `Vaciado` funciona igual, pero deja de ser un laboratorio con
nombre propio; queda absorbido por el laboratorio general de pocket milling.

### Etapa 3 - Base Comun Del Sintetizador

- Extraer helpers comunes desde `pgmx.synthesis.core` hacia
  `pgmx.synthesis.common`.
- Mantener imports y `__all__` actuales desde `pgmx.synthesis`.
- No cambiar nombres publicos ni version publica todavia.

Salida esperada: menos acoplamiento interno, API publica identica.

### Etapa 4 - Modulos Productivos Por Familia

Migrar una familia por vez:

1. taladros y patrones, porque tienen frontera clara;
2. linea y ranura;
3. perfiles y circulos;
4. escuadrado;
5. pocket milling / `ClosedPocket`.

Cada migracion debe dejar:

- modulo productivo propio;
- tests de fachada publica;
- tests de sintesis existentes pasando;
- cero imports productivos desde `machining_lab`.

### Etapa 5 - Integracion De Pocket Milling Sin Motor Legado

- Reubicar el motor experimental en `pgmx.machining_lab.pocket_milling`.
- Integrar el contrato experimental `pgmx.vaciado` dentro de
  `pgmx.synthesis.milling.pocket` y retirar el paquete separado.
- Hacer que `pgmx.synthesis.milling.pocket` sea el unico punto productivo para
  `ClosedPocket`/pocket milling.
- Eliminar la dependencia directa `pgmx.synthesis.core -> pgmx.vaciado_lab`.
- Promover solo las reglas cerradas desde laboratorio hacia
  `pgmx.synthesis.milling.pocket`.

Salida esperada: la produccion conoce el mecanizado como `ClosedPocket` a
traves de `milling.pocket`, sin contrato `pgmx.vaciado` ni laboratorio
`pgmx.vaciado_lab` como paquetes finales.

### Etapa 6 - Expansion Del Laboratorio

- Agregar laboratorios por familia cuando haya una pregunta abierta real.
- Usar la misma estructura del laboratorio piloto de pocket milling:
  - `memory/current-state.md`;
  - comandos de analisis reproducibles;
  - fixtures externos documentados;
  - criterio de promocion.
- Evitar scripts nuevos sueltos bajo `tools/` salvo CLIs publicas o fachadas.

### Etapa 7 - Limpieza Final

- Reducir `pgmx.synthesis.core` a fachada interna o eliminarlo si ya no cumple
  rol real.
- Mantener `tools.synthesize_pgmx` y `tools.pgmx_synthesis` como compatibilidad.
- Retirar `pgmx.vaciado_lab`, `pgmx.vaciado` y fachadas `tools.pgmx_vaciado*`
  cuando la memoria, tests y comandos hayan migrado a pocket milling.
- Actualizar `docs/synthesize_pgmx_help.md` con el nuevo mapa.

## Plan De Cierre Operativo

Estado fijado: 2026-06-05, despues de extraer familias productivas,
dispatcher y CLI.

Este es el orden operativo para terminar la modularizacion sin cambiar
comportamiento publico:

1. Completar `pgmx.synthesis.common.program`.
   - Mover `Xn`, estado de pieza, request, ejecucion programatica,
     validacion transversal y escritura final desde `core.py`.
   - Mantener `core.py` como reexport/alias de compatibilidad mientras dure la
     migracion.
2. Separar serializacion y contenedor si `common.program` queda demasiado
   cargado.
   - `common.xml` debe contener normalizacion XML, namespaces y helpers de
     nodos.
   - `common.program` puede conservar la escritura final del `.pgmx` si sigue
     siendo parte de la ejecucion del programa.
3. Eliminar dependencias productivas hacia `pgmx.vaciado_lab`. Hecho:
   `pgmx.synthesis.milling.pocket` usa `pocket_rectangular` y `pocket_trace`
   dentro de `pgmx.synthesis.milling`.
   - `pgmx.synthesis.milling.pocket` no debe importar laboratorio como motor
     productivo final.
   - Solo se promueven al modulo productivo reglas cerradas y testeadas.
4. Crear el laboratorio general. Hecho: el laboratorio vive en
   `pgmx.machining_lab.pocket_milling` y `pgmx.vaciado_lab` queda como fachada
   historica.
   - La implementacion real vive en `pgmx.machining_lab.pocket_milling`.
   - Mantener fachadas historicas solo durante la transicion.
5. Integrar o retirar el contrato separado `pgmx.vaciado`.
   - `ClosedPocket`/pocket milling debe quedar como familia de
     `pgmx.synthesis.milling.pocket`.
6. Reducir `pgmx.synthesis.core` a fachada interna. Hecho: `core.py` solo
   reexporta los modulos reales y mantiene el `__all__` publico historico.
   - No debe contener logica nueva.
   - Debe sostener compatibilidad con `tools.synthesize_pgmx` y
     `tools.pgmx_synthesis`.
7. Actualizar documentacion publica y limpiar fachadas historicas cuando los
   tests y comandos hayan migrado.

## Validacion Minima Por Etapa

```powershell
py -3 -m unittest tests.test_pgmx_synthesis_package
py -3 -m unittest tests.test_pgmx_public_facades
py -3 -m unittest tests.test_pgmx_vaciado_v2
py -3 -m unittest tests.test_pgmx_vaciado
py -3 -m compileall -q pgmx tools tests
```

Si se toca una familia concreta, correr tambien sus tests especificos y un
smoke import de las fachadas historicas.

## Pendientes Explicitos

- Definir si `profile.py` absorbe circulos o si `circle.py` queda como familia
  propia permanente.
- Decidir si `PocketMillingSpec` sigue siendo el contrato publico final de
  `ClosedPocket`/pocket milling o si se crea una spec nueva dentro de
  `milling.pocket`.
- Separar reglas genericas de toolpath de reglas particulares de Maestro.
- Definir un comando de regeneracion/validacion de corpus para cada laboratorio.
