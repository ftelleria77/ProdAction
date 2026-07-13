# Plan De Modularizacion Del Sintetizador PGMX

Estado: cierre arquitectonico formal y limpieza de fachadas historicas,
2026-06-05.

Este plan convierte el frente abierto de `ClosedPocket`/pocket milling en un
patron general para desarrollar mecanizados del sintetizador PGMX. La meta es
que cada familia de
mecanizado tenga el mismo recorrido:

1. evidencia y experimentacion en laboratorio;
2. contrato de dominio estable;
3. adaptacion desde snapshots Maestro;
4. sintesis productiva `.pgmx`;
5. pruebas de compatibilidad y regresion;
6. retiro de fachadas historicas cuando los imports ya migraron.

Este documento nacio como mapa de destino. Al cierre formal del 2026-06-05,
el mapa ya quedo ejecutado como reorganizacion arquitectonica del sintetizador;
los pendientes listados al final son decisiones de producto/compatibilidad o
frentes tecnicos, no bloqueos de modularizacion.

## Principios

- `pgmx.synthesis` sigue siendo la API publica del sintetizador.
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
    core.py                  # fachada interna historica; reexporta modulos reales
    common/
      program.py             # orquestacion de request, estado y worksteps
      output.py              # finalizacion XML Maestro y escritura del contenedor PGMX
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
      pocket_contract.py     # contrato promovido desde el V2 historico de Vaciado
    drilling/
      single.py
      pattern.py
  machining_lab/
    README.md
    pocket_milling/
      ...
    # futuros laboratorios por familia, solo ante preguntas abiertas reales:
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
laboratorio historico `pgmx/vaciado_lab/` y el contrato experimental
`pgmx/vaciado/` ya fueron retirados como paquetes propios; su contenido util se
integro en
`pgmx.synthesis.milling.pocket`, `pgmx.synthesis.milling.pocket_contract` y
`pgmx.machining_lab.pocket_milling`.
Las fachadas historicas `tools.pgmx_synthesis` y `tools.pgmx_vaciado*` tambien
fueron retiradas.

## Familias

| Familia | Contrato actual | Produccion objetivo | Laboratorio objetivo |
| --- | --- | --- | --- |
| Linea | `LineSpec` | `pgmx.synthesis.milling.line` | `pgmx.machining_lab.line_milling` |
| Ranura | `ChannelSpec` | `pgmx.synthesis.milling.slot` | `pgmx.machining_lab.slot_milling` |
| Perfil | `PolylineSpec`, `CircleSpec` | `pgmx.synthesis.milling.profile`, `circle` | `pgmx.machining_lab.profile_milling` |
| Escuadrado | `ContourSpec` | `pgmx.synthesis.milling.squaring` | `pgmx.machining_lab.squaring` |
| Pocket / ClosedPocket | `PocketSpec`, contrato promovido `pgmx.synthesis.milling.pocket_contract` | `pgmx.synthesis.milling.pocket` | `pgmx.machining_lab.pocket_milling` |
| Taladro | `DrillSpec` | `pgmx.synthesis.drilling.single` | `pgmx.machining_lab.drilling` |
| Patron de taladros | `DrillPatternSpec` | `pgmx.synthesis.drilling.pattern` | `pgmx.machining_lab.drilling` |
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

Las etapas siguientes quedan como historial de ejecucion del cierre
arquitectonico. Las tareas activas ya no son migrar fachadas historicas, sino
mantener la frontera limpia y abrir laboratorios nuevos solo cuando exista una
pregunta tecnica concreta.

### Etapa 1 - Inventario Y Frontera

Estado: completada.

- Listar funciones y dataclasses exportadas por `pgmx.synthesis.core`.
- Marcar cuales son comunes y cuales pertenecen a una familia.
- Registrar dependencias heredadas desde `pgmx.synthesis.core` hacia
  `pgmx.vaciado_lab`.
- Crear una matriz de tests que cubra cada familia antes de mover codigo.

Salida esperada: inventario documentado y tests verdes sin cambios funcionales.

### Etapa 2 - Laboratorio General

Estado: completada para el laboratorio piloto de pocket milling.

- Crear `pgmx/machining_lab/README.md`.
- Crear `pgmx/machining_lab/pocket_milling/` como destino del laboratorio
  historico de Vaciado.
- Mover documentacion, memoria, analizadores y trace engine utiles hacia
  `pocket_milling`.
- Retirar las fachadas temporales despues de migrar imports, tests y comandos.

Salida esperada: `Vaciado` funciona igual, pero deja de ser un laboratorio con
nombre propio; queda absorbido por el laboratorio general de pocket milling.

### Etapa 3 - Base Comun Del Sintetizador

Estado: completada.

- Extraer helpers comunes desde `pgmx.synthesis.core` hacia
  `pgmx.synthesis.common`.
- Mantener imports y `__all__` actuales desde `pgmx.synthesis`.
- No cambiar nombres publicos ni version publica todavia.

Salida esperada: menos acoplamiento interno, API publica identica.

### Etapa 4 - Modulos Productivos Por Familia

Estado: completada para las familias publicas actuales.

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

Estado: completada.

- Reubicar el motor experimental en `pgmx.machining_lab.pocket_milling`.
- Integrar el contrato experimental `pgmx.vaciado` dentro de
  `pgmx.synthesis.milling.pocket_contract`, antes de retirar la fachada cuando
  migren los imports.
- Hacer que `pgmx.synthesis.milling.pocket` sea el unico punto productivo para
  `ClosedPocket`/pocket milling.
- Eliminar la dependencia directa `pgmx.synthesis.core -> pgmx.vaciado_lab`.
- Promover solo las reglas cerradas desde laboratorio hacia
  `pgmx.synthesis.milling.pocket`.

Salida esperada: la produccion conoce el mecanizado como `ClosedPocket` a
traves de `milling.pocket`, con el contrato en `milling.pocket_contract`, sin
contrato `pgmx.vaciado` ni laboratorio `pgmx.vaciado_lab` como paquetes
finales.

### Etapa 6 - Expansion Del Laboratorio

Estado: protocolo vigente, no tarea abierta obligatoria.

- Agregar laboratorios por familia cuando haya una pregunta abierta real.
- Usar la misma estructura del laboratorio piloto de pocket milling:
  - `memory/current-state.md`;
  - comandos de analisis reproducibles;
  - fixtures externos documentados;
  - criterio de promocion.
- Evitar scripts nuevos sueltos bajo `tools/` salvo CLIs publicas o fachadas.

### Etapa 7 - Limpieza Final

Estado: completada.

- `pgmx.synthesis.core` quedo reducido a fachada interna historica.
- `tools.synthesize_pgmx`, `tools.pgmx_snapshot`, `tools.pgmx_adapters`,
  `tools.pgmx_synthesis`, `pgmx.vaciado_lab`, `pgmx.vaciado` y fachadas
  `tools.pgmx_vaciado*` fueron retiradas.
- `docs/synthesize_pgmx_help.md` documenta el mapa publico vigente.

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
   cargado. Hecho: `pgmx.synthesis.common.output` contiene la finalizacion XML
   Maestro y la escritura del contenedor `.pgmx`; `common.program` reexporta
   esos nombres para compatibilidad.
   - `common.xml` debe contener normalizacion XML, namespaces y helpers de
     nodos.
   - `common.program` conserva la ejecucion del programa y delega la salida
     final en `common.output`.
3. Eliminar dependencias productivas hacia `pgmx.vaciado_lab`. Hecho:
   `pgmx.synthesis.milling.pocket` usa `pocket_rectangular` y `pocket_trace`
   dentro de `pgmx.synthesis.milling`.
   - `pgmx.synthesis.milling.pocket` no debe importar laboratorio como motor
     productivo final.
   - Solo se promueven al modulo productivo reglas cerradas y testeadas.
4. Crear el laboratorio general. Hecho: el laboratorio vive en
   `pgmx.machining_lab.pocket_milling`.
   - La implementacion real vive en `pgmx.machining_lab.pocket_milling`.
   - Las fachadas historicas de Vaciado fueron retiradas al cerrar la limpieza.
5. Integrar o retirar el contrato separado `pgmx.vaciado`. Hecho:
   `pgmx.synthesis.milling.pocket_contract` contiene el contrato V2 promovido.
   - `ClosedPocket`/pocket milling queda como familia de
     `pgmx.synthesis.milling.pocket`.
6. Reducir `pgmx.synthesis.core` a fachada interna. Hecho: `core.py` solo
   reexporta los modulos reales y mantiene el `__all__` publico historico.
   - No debe contener logica nueva.
   - Ya no sostiene fachadas publicas bajo `tools/`.
7. Actualizar documentacion publica y limpiar fachadas historicas. Hecho: la
   ayuda publica usa `pgmx.synthesis`, `pgmx.snapshot` y `pgmx.adapters`; el
   inventario general vive en `docs/repository_audit_inventory.md`.

## Cierre Formal De Etapa Arquitectonica

Fecha de cierre: 2026-06-05.

La etapa arquitectonica de modularizacion del sintetizador PGMX queda cerrada
con estos criterios:

- La API publica vigente es `pgmx.synthesis`.
- `pgmx.synthesis.core` queda reducido a fachada interna historica; no dirige
  arquitectura ni debe recibir logica nueva.
- Las responsabilidades comunes quedaron separadas en `pgmx.synthesis.common`:
  programa, XML, salida, pieza, profundidad, herramientas, estrategia,
  hidratacion y acercamientos/alejamientos.
- Las familias productivas quedaron separadas en `pgmx.synthesis.milling` y
  `pgmx.synthesis.drilling`.
- `ClosedPocket`/pocket milling quedo integrado en
  `pgmx.synthesis.milling.pocket`.
- El contrato V2 historico de Vaciado quedo promovido a
  `pgmx.synthesis.milling.pocket_contract`.
- `pgmx.vaciado`, `pgmx.vaciado_lab`, `tools.synthesize_pgmx`,
  `tools.pgmx_snapshot`, `tools.pgmx_adapters`, `tools.pgmx_synthesis`,
  `tools.pgmx_vaciado` y `tools.pgmx_vaciado_v2` fueron retirados despues de
  migrar imports, tests y comandos al mapa final.
- `pgmx.machining_lab.pocket_milling` queda como laboratorio/evidencia, no como
  dependencia productiva directa.
- La ayuda publica del sintetizador quedo alineada en
  `docs/synthesize_pgmx_help.md`.

Validacion de cierre publicada:

```powershell
py -3 -m unittest tests.test_pgmx_synthesis_package tests.test_pgmx_public_facades tests.test_pgmx_vaciado_v2 tests.test_pgmx_vaciado
py -3 -m compileall -q pgmx tools tests
git diff --check
```

Resultado registrado: `71` tests `OK`, `compileall` `OK`, `git diff --check`
`OK`.

Queda fuera de este cierre:

- desarrollar nuevos casos de pocket milling/vaciado;
- implementar el sintetizador ISO;
- definir compatibilidad externa futura si aparece un consumidor fuera del
  repositorio;
- convertir decisiones abiertas de producto en codigo sin acuerdo previo.

## Validacion Minima Por Etapa

```powershell
py -3 -m unittest tests.test_pgmx_synthesis_package
py -3 -m unittest tests.test_pgmx_public_facades
py -3 -m unittest tests.test_pgmx_vaciado_v2
py -3 -m unittest tests.test_pgmx_vaciado
py -3 -m compileall -q main.py app core pgmx iso_state_synthesis cnc_traceability tools tests
```

Si se toca una familia concreta, correr tambien sus tests especificos y un
smoke import de la API publica vigente.

## Decisiones Cerradas Posteriores Al Cierre

- `profile.py` y `circle.py` se mantienen como modulos productivos separados.
  Motivo: los circulos comparten algunas bases con perfiles, pero tienen reglas
  propias de familia, estrategia helicoidal y serializacion circular especifica.
- `PocketSpec` se mantiene como contrato publico final de
  `ClosedPocket`/pocket milling. Motivo: ya esta expuesto por `pgmx.synthesis`,
  validado por tests, documentado en la ayuda publica y alineado con el
  contrato promovido `pgmx.synthesis.milling.pocket_contract`.

## Decisiones Trasladadas Al Laboratorio

Estas decisiones ya no bloquean el cierre arquitectonico del sintetizador.
Quedan trasladadas al laboratorio de mecanizados y deberan retomarse cuando se
reactive la investigacion del sintetizado de vaciados/pocket milling.

- Separar reglas genericas de toolpath de reglas particulares de Maestro, a
  partir de evidencia nueva del laboratorio.
- Definir un comando de regeneracion/validacion de corpus para el laboratorio,
  empezando por `pgmx.machining_lab.pocket_milling`.
