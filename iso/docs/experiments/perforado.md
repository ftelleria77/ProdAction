# Perforado — rama D

**Documento vivo.** El grupo **Perforado** de la cinta de Maestro; la operación que crea se
llama **`Taladrado`**. Lote `…\Reinvestigación\Mecanizados\Perforado\`, instrucciones en
`INSTRUCCIONES.md` de esa carpeta.

Es la **primera traza de mecanizado derivada de punta a punta** en la época nueva: `.pgmx` y
`.iso` de cada caso, con el programa vacío del mismo lote como referencia.

## 1. La ventana, capturada (2026-08-27)

Tres capturas en la carpeta del lote. Lo que fijan:

- El panel se llama **`Taladrado`**, y así queda el nombre del mecanizado. ⇒ **`Taladrado` es
  vocabulario de Maestro**, no invención nuestra: `Perforado` es el grupo de la cinta y
  `Taladrado` la operación. Lo que el default del sintetizador decía, coincide.
- **Referencias** (la cara): `Lado superior` · `derecho` · `izquierdo` · `delantero` ·
  `trasero` · **`inferior`** — seis, incluida la inferior, que el sintetizador no modela.
- **Datos perforado**: `Coordenada X` · `Coordenada Y` · `Profundidad` · `Diámetro orificio` ·
  casilla `Pasante` · **Tipo de agujero: Plano · Cónico · Abocinado**.
  ⇒ el **Abocinado existe**; la doc del sintetizador lo daba por fuera de alcance «porque no
  hay caso manual validado».
- **Datos tecnológicos**: `Información herramientas` (desplegable) y **Parámetros de trabajo:
  `Avanz.` y `Rotación (rpm)`**, los dos vacíos por defecto.
- Secciones plegadas, sin capturar todavía: `Repeticiones`, **`Estrategia`**, `Datos avanzados`,
  `Datos máquina`. **El plano de seguridad y las pasadas no están en la parte visible**: tienen
  que vivir en alguna de ésas.
- El desplegable de herramientas sobre `Lado superior` ofrece **`001`–`007` y también
  `E001`–`E007`** — se puede taladrar con fresa. Las laterales `058`–`061` no aparecen: la
  lista está **filtrada por cara**.

⚠️ **`Diámetro orificio` y la herramienta son campos INDEPENDIENTES.** El diámetro se tipea; la
herramienta se elige aparte, o no se elige.

## 2. Los dos métodos dan el MISMO ISO

Grupo 1 se hizo dos veces: eligiendo la broca (`top_001_…`) y sin elegirla, sólo con diámetro y
punta plana (`top_D8_…`).

**En el `.pgmx` la única diferencia son once tags, todos del `ToolKey`:**

| | con herramienta elegida | sin elegir |
|---|---|---|
| `ToolKey/ID` | `1888` | `0` |
| `ToolKey/ObjectType` | `…ToolDataModel.Tool.CuttingTool` | `System.Object` |
| `ToolKey/Name` | `001` | vacío |

Todo lo demás —diámetro, profundidad, punto, tipo de punta— es idéntico.

**Y los ISO salen byte-idénticos salvo la línea 1**, en los cuatro pares comparables (el quinto
par no era comparable, ver §7).

⇒ ⭐ En estos casos la herramienta elegida **no cambia nada**: el postprocesador la resuelve
desde el diámetro y el tipo de punta, y llega al mismo huso.

> 📌 **CORREGIDO el 2026-09-03.** Acá decía que la herramienta elegida «NO viaja al ISO». **Es
> falso**, y lo destapó el barrido del corpus entero (`fixtures.md` §6): de 34 pares que
> difieren sólo en el `ToolKey`, **dos mueven el ISO**, y los dos son de la broca `007`.
>
> | fixture | diámetro | punta declarada | herramienta | huso emitido |
> |---|---|---|---|---|
> | `top_005` | 5 | Flat | `005` | **5** |
> | `top_007` | 5 | **Flat** | `007` | **7** |
> | `top_D5P` | 5 | Flat | (vacía) | **5** |
> | `top_D5C` | 5 | Conical | (vacía) | **7** |
>
> `top_007` declara punta **plana** y herramienta **007**, y emite el huso **7**. Con el mismo
> diámetro y la misma punta, elegir la herramienta cambia el resultado.
>
> ⇒ **La formulación correcta**: si NO elegís herramienta, el postprocesador la resuelve por
> diámetro + punta; si la elegís, **manda la elegida**, aunque contradiga la punta del feature.
> Los pares del Grupo 1 salían idénticos porque ahí las dos vías **coinciden** (Ø8 plana → 001),
> no porque la herramienta se ignore.
>
> Y de paso confirma con evidencia nueva algo que la doc del sintetizador traía de la época
> congelada: al elegir la `007` sobre un agujero Ø5, **Maestro normaliza el `BottomCondition` a
> `FlatHoleBottom`** y deja la familia cónica expresada sólo por el `ToolKey`.

⇒ Y confirma con evidencia de la época nueva una fila de la tabla `tool_resolution="Auto"` del
sintetizador: **plana Ø8 → `001` / `1888`**.

## 3. Dónde vive cada dato en el `.pgmx`

| dato | nodo |
|---|---|
| diámetro, profundidad (`StartDepth`/`EndDepth`), tipo de punta | **`<Features>`** (el `RoundHole`) |
| centro del agujero | **`<Geometries>`**, un `GeomCartesianPoint` (`_x`, `_y`, `_z`) |
| **herramienta (`ToolKey`)** | **`<Operations>`** — *no* en el feature |
| tecnología (`Feedrate`, `CutSpeed`, `Spindle`) | `<Operations>`, en `<Technology i:type="MillingTechnology">` |

Dos rarezas de nomenclatura de Maestro, ninguna nuestra: la tecnología de un taladro se
serializa como **`MillingTechnology`**, y `Diameter` va con prefijo de namespace mientras
`StartDepth` no.

Con `Avanz.` y `Rotación` vacíos en la UI, `Feedrate`/`CutSpeed`/`Spindle` quedan en **`0`** ⇒
el `F` y el `S` del ISO **no salen del programa**: salen del catálogo de herramientas.

## 4. El bloque del taladrado en el ISO

Sobre el ISO del programa vacío (44 líneas), un taladro agrega **40**. El cuerpo, con la broca
`001` en (100,100) a profundidad 10:

```
?%ETK[17]=257
S6000M3
?%ETK[0]=1
G0 X100.000 Y100.000
G0 Z115.000
?%ETK[7]=3
MLV=2
G1 G9 Z85.000 F2000.000
G0 Z115.000
```

Y el cierre agrega `G4F1.200` (una espera) antes del `G0 G53 Z201.000` de siempre.

**Contra el bloque del fresado** (`dibujos.md` §13.1), lo que NO está: **no hay `T`, ni `SYN`,
ni `M06`, ni `D1`/`SVL`/`SVR`**. ⇒ el taladro **no hace cambio de herramienta**: va en el
cabezal perforador, y el huso se selecciona por registro.

| token | qué es |
|---|---|
| `?%ETK[7]` | **el tipo de mecanizado**: `3` en el taladrado, `4` en el fresado |
| `?%ETK[6]` | **el número de huso** (1 con la broca `001`, 5 con la `005`) |
| `?%ETK[0]` | **máscara de bits del huso**: `1` = 2⁰ para el huso 1, `16` = 2⁴ para el huso 5 ⇒ **`2^(huso−1)`** |
| `?%ETK[17]` | `257` en los diez fixtures. Sin variar todavía |
| `G1 G9` | el `G9` (paro exacto) es del taladro; el fresado usa `G1` a secas |
| `G4F1.200` | espera al final del bloque. Origen sin derivar |

## 5. ⭐ La cota Z lleva la longitud de la herramienta

Durante el bloque el `SHF[Z]` se pone en **0** (y se restaura a `18.000+%ETK[114]/1000` al
salir), así que la Z va contra la mesa y no contra la cara de la pieza. Con eso:

```
Z_iso = espesor − profundidad + tool_offset_length(broca)
```

> 📌 **Corregido el 2026-08-28.** Acá decía `DZ`, que en esta doc significa el valor del header
> —**dimensión + origen**—, y es otra cosa. Lo separó `oz5` (§5bis): con origen Z=5 el header
> pasa a `DZ=23` y **la Z de corte no se mueve**. Es el **espesor de la pieza**.

Verificado en los cuatro casos del Grupo 1, con `tool_offset_length = 77` para la broca `001`:

| caso | profundidad | esperado | ISO |
|---|---|---|---|
| aproximación | −20 (plano de seguridad) | 18 + 20 + 77 | **115.000** |
| `prof10` | 10 | 18 − 10 + 77 | **85.000** |
| `prof5` | 5 | 18 − 5 + 77 | **90.000** |
| `pasante` | 18 | 18 − 18 + 77 | **77.000** |

⇒ **El pasante llega justo a la cara inferior, sin excedente.**

Y el **plano de seguridad vale 20** en los cuatro, sin haberlo tocado — es el default que la
ventana no muestra en la parte visible.

### ✅ RESUELTO por el Grupo 6 (2026-08-29): el offset sale del CATÁLOGO

Los laterales usan **65**, que es el `tool_offset_length` de las brocas `058`–`061`, contra el
**77** de las verticales. ⇒ **no es una constante del cabezal: es la longitud de la
herramienta.** Lo de abajo queda como registro de por qué el Grupo 2 no podía decidirlo.

### ⚠️ Por qué el Grupo 2 no lo pudo separar

La fórmula encaja en el 100% de la evidencia, pero **las siete brocas verticales del catálogo
tienen `tool_offset_length = 77`** (verificado el 2026-08-28 sobre los 26 ISO del Grupo 2: los
siete husos, a profundidad 10, dan `Z85.000`). ⇒ con esta familia **no se distingue**:

| lectura | fórmula |
|---|---|
| sale del catálogo | `Z = DZ − prof + tool_offset_length(broca)` |
| es del cabezal perforador | `Z = DZ − prof + 77` |

Y no hay `77` significativo en la configuración de máquina: el de `spindles.cfg` es el índice
del huso 77, y `pheads.cfg` no tiene la estructura de registros para atribuírselo.

**Dos fixtures baratos la separan**, cualquiera de los dos alcanza:

1. **Taladrar con una fresa.** El desplegable del `Taladrado` ofrece `E001`–`E007`, con offsets
   de 107 a 152.1 — todos distintos de 77. Si la `Z` los sigue, sale del catálogo.
2. **Las caras laterales** (Grupo 6): las brocas `058`–`061` tienen offset **65**.

A favor de la lectura del catálogo hay un antecedente fuerte y de otra rama: en el fresado, el
`SVL` **es** el `tool_offset_length` de la herramienta (`anatomia_iso.md` B1i, `SVL 125.400`
para `E001`). Pero eso es el `SVL`, no la `Z`, así que **sigue siendo analogía, no derivación**.

## 6. La X y la Y van DIRECTO — la Y no se invierte

`G0 X100.000 Y100.000` con el agujero en (100,100); `y300` da `Y300.000` y `x250` da `X250.000`.

⇒ **Cierra la contradicción que quedaba abierta**: el `Xn` invierte la Y
(`operaciones_maquina.md` §4.3) y **el taladrado no**. No es una regla del ISO: es del `Xn`.

## 7. ⭐⭐ El huso sale de `spindles.cfg`

Un fixture mal guardado (§8) resultó tener **diámetro 5** en vez de 8, y eso dio el segundo
punto: el postprocesador lo resolvió a la broca `005`, que vive en **otro huso**. Los dos ISO
difieren en exactamente cuatro líneas:

| | broca `001` (huso 1) | broca `005` (huso 5) |
|---|---|---|
| `?%ETK[6]=` | 1 | **5** |
| `?%ETK[0]=` | 1 | **16** |
| `SHF[X]=` (en `MLV=2`) | 0.000 | **−64.000** |
| `SHF[Z]=` (en `MLV=2`) | 0.000 | **−0.950** |

`SHF[X]`/`SHF[Z]` en `MLV=2` son **el offset físico del huso dentro del cabezal**. Y están en la
configuración de máquina: `xilog_plus/Cfg/spindles.cfg`, **1000 registros de 42 líneas** (misma
forma que `fields.cfg`: el nombre al final, rellenado con `0x03`).

| registro | pos 0 | pos 23 | pos 24 | pos 25 |
|---|---|---|---|---|
| 1 | 1 | — | — | — |
| 2 | 2 | — | −32.00 | 0.20 |
| 3 | 3 | — | −64.00 | 0.25 |
| 4 | 4 | 32.00 | — | 0.35 |
| **5** | **5** | **64.00** | — | **0.95** |
| 6 | 6 | 96.00 | — | 0.20 |
| 7 | 7 | 128.00 | — | — |

⇒ **`SHF[X] = −pos23` y `SHF[Z] = −pos25` del registro del huso.** El huso 5 da −64.000 y
−0.950; el huso 1, que tiene las dos vacías, da 0.000 y 0.000. **Cuatro valores, cuatro
aciertos.**

⇒ **No hace falta ninguna constante interna**: los offsets del cabezal salen de la config, como
pide la regla 4 del `CLAUDE.md`.

### Predicciones para el Grupo 2 (falsables)

Si la lectura es correcta, las siete brocas tienen que dar:

| broca | huso | `?%ETK[6]` | `?%ETK[0]` | `SHF[X]` | `SHF[Z]` |
|---|---|---|---|---|---|
| 001 (Ø8) | 1 | 1 | 1 | 0.000 | 0.000 |
| 002 (Ø15) | 2 | 2 | 2 | ? (pos24 → ¿`SHF[Y]`=+32?) | −0.200 |
| 003 (Ø20) | 3 | 3 | 4 | ? (pos24 → ¿`SHF[Y]`=+64?) | −0.250 |
| 004 (Ø35) | 4 | 4 | 8 | −32.000 | −0.350 |
| 005 (Ø5) | 5 | 5 | 16 | **−64.000** ✅ | **−0.950** ✅ |
| 006 (Ø4) | 6 | 6 | 32 | −96.000 | −0.200 |
| 007 (Ø5 cónica) | 7 | 7 | 64 | −128.000 | 0.000 |

Los husos 2 y 3 son los que dicen **qué es la posición 24**: si mueven `SHF[Y]` en vez de
`SHF[X]`, la 23 es la X del huso y la 24 la Y.

## 7bis. Grupo 2: la tabla de husos, verificada 21/21 (2026-08-27)

Fermín hizo el barrido de las siete brocas **cuatro veces**: campo `A` y campo `HG`, cada uno
por los dos métodos (eligiendo la herramienta y por diámetro + punta). 26 ISO.

**Las predicciones de §7 se cumplen todas:**

| broca | huso | `?%ETK[6]` | `?%ETK[0]` | `SHF[X]` | `SHF[Y]` | `SHF[Z]` | `S` |
|---|---|---|---|---|---|---|---|
| 001 · Ø8 plana | 1 | 1 | 1 | 0.000 | 0.000 | 0.000 | 6000 |
| 002 · Ø15 plana | 2 | 2 | 2 | 0.000 | **+32.000** | −0.200 | 4000 |
| 003 · Ø20 plana | 3 | 3 | 4 | 0.000 | **+64.000** | −0.250 | 4000 |
| 004 · Ø35 plana | 4 | 4 | 8 | −32.000 | 0.000 | −0.350 | 4000 |
| 005 · Ø5 plana | 5 | 5 | 16 | −64.000 | 0.000 | −0.950 | 6000 |
| 006 · Ø4 plana | 6 | 6 | 32 | −96.000 | 0.000 | −0.200 | 6000 |
| 007 · Ø5 cónica | 7 | 7 | 64 | −128.000 | 0.000 | 0.000 | 6000 |

⭐ **La posición 24 de `spindles.cfg` es la `Y` del huso.** Era lo único que §7 no podía decidir:
los husos 2 y 3 tienen la 23 vacía y la 24 en −32/−64, y son los únicos que mueven `SHF[Y]`.

⇒ **La regla completa, 21 valores y 21 aciertos:**

```
SHF[X] = −pos23 · SHF[Y] = −pos24 · SHF[Z] = −pos25   del registro del huso en spindles.cfg
?%ETK[6] = numero de huso        ?%ETK[0] = 2^(huso − 1)
```

Y el `S…M3` sale del catálogo (`spindle_speed_std`): 6000 para 001/005/006/007, 4000 para
002/003/004. Misma regla que el fresado.

### Los dos métodos coinciden huso por huso

`D8P`→1 · `D15P`→2 · `D20P`→3 · `D35P`→4 · `D5P`→5 · `D4P`→6 · `D5C`→7.

⇒ La resolución por diámetro + punta **acierta la broca exacta**, y **la punta discrimina entre
dos brocas del mismo diámetro**: Ø5 plana → `005` (huso 5) y Ø5 cónica → `007` (huso 7).
Confirma con evidencia de la época nueva la fila `Conical D5 → 007` de la tabla del
sintetizador.

> Detalle de la UI, visible en la captura del error: **al elegir la herramienta, `Diámetro
> orificio` queda en gris**. Los dos métodos son excluyentes en la ventana.

### ⭐ El campo y el mecanizado son ORTOGONALES

El mismo taladro en `A` y en `HG` difiere en **exactamente** el bloque de origen (`%Or`/`SHF`
del programa, dos veces) y el índice del `EDK` (10 contra 13). **El bloque del taladrado —huso,
`S`, `XY`, `Z`— es idéntico.**

⇒ Contesta la pregunta que motivaba el lote D2 sin necesidad de fixtures nuevos: la traza de un
mecanizado **no se mueve con el campo**; el campo entra sólo por el origen.

### ⛔ La broca cónica NO se puede usar en campo A — y es predecible

Los dos fixtures de campo `A` con el huso 7 (`top_007` y `top_D5C`) **no postprocesan**:

```
[6,8] - ChkPgm línea 21: Microinterruptor- de tope eje X (T= 7)
```

Es otro chequeador (`ChkPgm`, no `Bag`) y otro código (`[6,8]`), y **sale de la cuenta**:

| | |
|---|---|
| agujero, en coordenadas de pieza | X = 100 |
| origen del campo A | `SHF[X]` = −3685.850 |
| offset del huso 7 | `SHF[X]` = −128.000 |
| **X de máquina** | **−3713.850** |
| límite del eje X (`Params.cfg`, `AP_MINQUOTA`) | **−3702.000** |

Se pasa **11.85 mm**. El huso 6, que está a −96, entra por 20.15 mm de margen — por eso es el
último que funciona en campo A. En `HG` (`SHF[X]` = −400) el mismo agujero da −428: holgado.

⇒ ⭐ **El converter puede anticipar este rechazo**: todo lo que necesita está en la config de
máquina. No hace falta emitir el ISO para descubrir que la máquina no llega.

⇒ Y es la primera vez que **el campo deja de ser ortogonal**: no cambia la traza, pero **decide
si la traza es ejecutable**.

## 5bis. El ORIGEN de la pieza (Grupo 1bis, 2026-08-28)

Diez fixtures en tres campos (`A`, `B`, `HG`), variando **sólo el origen** sobre el mínimo.
Idea de Fermín: todo el Grupo 1 tenía origen 0/0/0, y con origen cero el espesor y el `DZ` del
header son el mismo número.

### ⭐ La traza va en coordenadas de PIEZA, y la `Z` usa el ESPESOR

- **`G0 X100.000 Y100.000` en los diez**, también con origen (100,50) ⇒ la XY del taladro **no
  absorbe el origen**. Confirma para el taladrado lo que el 2026-08-24 derivó para el fresado.
- **`Z85.000` en los diez**, también con origen Z=5 ⇒ **la `Z` se calcula contra el espesor**
  (18), no contra el header (23). Es la corrección de §5.

El origen Z **sí** entra, pero por otro lado: `SHF[Z]` del bloque del mecanizado pasa de
`0.000` a **`5.000`**. ⇒ la máquina baja los 5 mm de más; sólo que viajan por el
desplazamiento y no por la cota.

### ⭐⭐ Los dos bloques de origen, por fin separados

El ISO trae el bloque de origen **dos veces** —el del esqueleto y el del mecanizado— y con
origen cero salen idénticos, que es por qué nunca se había podido leer la diferencia (anotado
el 2026-08-24 sobre un fresado, sin derivar).

| campo | eje | ¿el campo resta la dimensión? | bloque 1 → bloque 2 |
|---|---|---|---|
| A | X | no | `SHF[X]` −3685.850 → **−3585.850** (`+ox`) |
| A | Y | sí | `ofY` −450000 → **−500000** (`−oy`) |
| B | X | sí | `ofX` −2343000 → **−2443000** (`−ox`) |
| B | Y | sí | `ofY` −450000 → **−500000** (`−oy`) |
| HG | X | sí | `ofX` −500000 → **−600000** (`−ox`) |
| HG | Y | no | `SHF[Y]` −1515.600 → **−1465.600** (`+oy`) |

⇒ **La regla, seis casos y seis aciertos:**

```
el eje que RESTA la dimensión   -> el origen entra en %Or, restando
el eje que NO resta             -> el origen entra en SHF,  sumando
```

Y el eje Z, que nunca resta, cumple la segunda mitad: `SHF[Z]` del bloque 2 **es** el origen Z
(0.000 sin origen, 5.000 con `oz5`), en los cuatro casos que lo tienen.

### ✅ La regla del campo, confirmada en `B`

`B` era la letra que refutó la condición del cero (`anatomia_iso.md` B1c) y nunca se había
probado con origen. Da **−2343.000** = −1843 − (400+100): resta **dimensión + origen**, como
`H`. La regla aguanta en el único caso que faltaba.

## 5ter. Grupo 3 — seguridad y tecnología (2026-08-28)

Doce fixtures, seis en `A` y seis en `HG`. Fermín agregó dos variantes que no estaban pedidas
—otro valor de avance y la **profundidad de pasada**— y la segunda resultó clave.

| variación | en el `.pgmx` | en el ISO |
|---|---|---|
| **avance** = 1 · 3 | `Feedrate` | `F1000.000` · `F3000.000` ⇒ **`F = avance × 1000`** |
| **rotación** = 3000 | `Spindle` | `S3000M3` ⇒ **directo, sin multiplicar** |
| **plano de seguridad** = 50 | `ApproachSecurityPlane` **y** `RetractSecurityPlane`, los dos | `G0 Z145.000` en las dos apariciones = 18 + **50** + 77 |
| **pasadas** = 3 | *no es un número: ver abajo* | el ciclo de tres pasadas |
| **prof. de pasada** = 2 · 4 | ídem | cinco pasadas de 2 · **tres de 3.333** |

⇒ **El plano de seguridad SÍ llega al ISO.** El barrido A6 lo había dejado como «necesita
trayectoria para manifestarse» (`opciones_de_aplicacion.md`): acá se manifestó, y confirma la
fórmula de la aproximación `Z = espesor + seguridad + offset`.

⇒ Y el avance del programa **pisa al del catálogo**: sin tocarlo sale `F2000` = el
`descent_speed_std` de la broca por 1000; con `Feedrate=1` sale `F1000`.

### ⭐ La profundidad de pasada es un MÁXIMO, no un paso

| pedido | pasadas emitidas |
|---|---|
| prof. de pasada **2**, agujero de 10 | 5 pasadas de **2.000** |
| prof. de pasada **4**, agujero de 10 | **3** pasadas de **3.333** |
| **3 pasadas**, agujero de 10 | 3 pasadas de **3.333** |

⇒ `n = ceil(profundidad / paso)`, y después **divide en `n` partes iguales**. Con paso 4 no
hace dos de 4 y una de 2: hace tres de 3.333.

⇒ Y por eso **`prof. de pasada 4` y `3 pasadas` dan el ISO byte-idéntico**: son dos maneras de
pedir lo mismo, y el ISO no guarda cuál se usó.

### ⭐ El ciclo de pecking, y el `+1` medido

```
G0 Z115.000                    aproximación
G1 G9 Z93.000 F2000.000        pasada 1
G0 X100.000 Y100.000 Z115.000  retiro TOTAL al plano de seguridad
G0 Z94.000                     reposicionamiento = profundidad alcanzada + 1
G1 G9 Z91.000 F2000.000        pasada 2
G0 Z93.000                     retiro a la profundidad de la pasada ANTERIOR
G0 Z92.000                     reposicionamiento = 91 + 1
G1 G9 Z89.000 F2000.000        pasada 3
…
G1 G9 Z85.000 F2000.000        última pasada
G0 X100.000 Y100.000 Z115.000  retiro final
```

- **La primera pasada retira al plano de seguridad completo**; las intermedias sólo hasta la
  profundidad de la pasada anterior.
- Antes de cada pasada baja en rápido hasta **1 mm por encima** de lo ya perforado.

⇒ ⭐ **Ese es el número mágico `peck+1`** que el `plan_cierre_converter.md` cita como el
precedente de un cierre Tier D, y por primera vez está **medido**: seis ocurrencias entre los dos fixtures, siempre `1.000` exacto.

⚠️ **Medido no es atribuido.** Los dos fixtures usan el mismo `1`, así que no se distingue una
constante del emisor de un parámetro de configuración que vale 1. Falta ubicarlo.

### ⚠️ Con pasadas, el `.pgmx` guarda la trayectoria EXPANDIDA

El `TrajectoryPath` deja de ser un `GeomTrimmedCurve` (una recta) y pasa a ser un
**`GeomCompositeCurve`** con **10 claves de miembro**: el recorrido queda **ya calculado** en el
archivo.

> 📌 **Corregido el 2026-08-30.** Acá decía además que «el número de pasadas no se guarda como
> número». **Es falso**: el `.pgmx` guarda **las dos cosas**. El modelo tiene
> `MultiStepDrilling` con `StepNumber`, `StepDepth` e **`IsStepDepth`** —el interruptor entre
> las dos formas— y los fixtures lo confirman:
>
> | fixture | `IsStepDepth` | `StepNumber` | `StepDepth` |
> |---|---|---|---|
> | `pasadas_3` | `false` | **3** | 0 |
> | `profpasada_2` | `true` | 1 | **2** |
> | `profpasada_4` | `true` | 1 | **4** |
>
> Y confirma el `ceil`: `profpasada_4` guarda un `4` y el ISO emite **tres pasadas de 3.333**.
> El redondeo lo hace quien expande la trayectoria, no está guardado.

Es la regla 5 del `CLAUDE.md` en acción: si estos fixtures los generara nuestro sintetizador,
Maestro postprocesaría **nuestra** hipótesis del ciclo de pecking y la derivación sería
circular.

### ⭐⭐ RESUELTO (2026-08-30): el ISO NO sale de la trayectoria guardada

`ScmGroup.XCam.MachiningDataModel`, decompilado, tiene el generador entero en
`ToolpathGenerator`:

```csharp
if (multiStepDrilling.IsStepDepth)
    paso = (StepDepth >= Precision.Technology() && StepDepth <= total) ? StepDepth : total;
else
    paso = (StepNumber > 1) ? (total / StepNumber) : total;

while (acum < total) {
    acum += paso;
    if (acum > total) acum = total;        // el último se recorta
    corte = origen + dir * acum;
    if (acum >= total) retiro = origen;    // el último retira al origen
    composite.AddSegment(anterior -> corte);
    composite.AddSegment(corte -> retiro);
    …
}
```

Con `StepDepth = 4` sobre 10 mm, ese bucle guarda cortes en **4 · 8 · 10** — tres pasadas de
**4, 4 y 2**. Y el ISO de ese mismo fixture emite **tres pasadas de 3.333**.

⇒ **La trayectoria guardada no es la que llega al ISO.** Coincide el **número** de pasadas, no
el reparto.

Y el manual de Xilog cierra el círculo: el parámetro `G` de la instrucción `B` es el «**número
de pasadas** (se divide en **partes iguales**)».

**Tres fuentes independientes que coinciden:**

| fuente | qué aporta |
|---|---|
| el código de Maestro | cuenta las pasadas: el bucle da **3** |
| el manual de Xilog | lo que viaja es `G` = número de pasadas, repartidas **iguales** |
| el ISO | tres pasadas de **3.333** ✓ |

⇒ La fórmula que se había derivado del ISO —`n = ceil(prof / paso)`, partes iguales— **era
correcta**, y ahora tiene mecanismo: el `ceil` sale del `while` que recorta la última pasada; el
reparto igual, del `G` de Xilog.

#### 📌 Y refina el alcance de la regla 5 para este caso

El 28 se escribió que si el sintetizador generara estos fixtures, «Maestro postprocesaría
**nuestra** hipótesis del ciclo de pecking». **Para el perforado, no**: lo que viaja a la etapa
2 son `StepNumber`/`StepDepth`, no el recorrido. La trayectoria guardada es interna.

La regla 5 sigue en pie —su ejemplo es la compensación con `ActivateCNCCorrection=false`, donde
la trayectoria almacenada **sí** lleva el offset— pero **el perforado no es un caso de
circularidad**. Hay que decidir caso por caso, no por familia.

#### ⏸ Y el `+1` queda localizado, no resuelto

No está en el generador de Maestro: el composite guardado son pares corte/retiro sin
reposicionamiento. ⇒ **el `+1` lo agrega la etapa 2**, el emisor nativo. Sigue sin ubicarse su
valor, pero ya se sabe de qué lado buscarlo.

## 6bis. Grupos 4 a 7 (2026-08-29)

Veinticuatro fixtures más, con agregados de Fermín en los grupos 5 y 6 que resultaron los más
productivos del lote.

### Grupo 4 — varios agujeros: la estructura y el ORDEN

- **El preámbulo se emite UNA vez por programa**: `?%ETK[17]=257`, el `S…M3` y la selección de
  huso no se repiten. Cada agujero más con el mismo huso cuesta **exactamente 12 líneas**
  (84 → 96 → 108 → 132, y 552 para los 40 del patrón 8×5 = 84 + 39×12).
- **El paso 32 NO agrupa husos.** `dos_x32` y `dos_x50` difieren **sólo en la coordenada**.
  La perforadora tiene los husos a paso 32 y el manual de Xilog describe la instrucción `B` con
  varias herramientas a la vez, pero **Maestro no lo genera**: un agujero, un movimiento.
  (Candidato a que lo haga el `Optimizador`, que es un botón aparte y no se tocó.)
- **Cambiar de huso** reescribe `?%ETK[6]`, el `SHF` del huso y `?%ETK[0]` — y **`ETK[0]` se
  reemplaza, no se acumula** (`1` → `16`, no `17`) ⇒ confirma que no hay perforación
  simultánea de varios husos.
- ⭐ **El ISO respeta el orden de CREACIÓN.** Los mismos tres agujeros creados de izquierda a
  derecha salen `100 · 200 · 300`; creados al revés, salen `300 · 200 · 100`. **El converter no
  reordena: emite en el orden de la lista.**

### Grupo 5 — el patrón es azúcar, y tiene un ángulo

- ⭐ **`patron_3x1_32` es byte-idéntico a `tres_x32`** (los tres agujeros sueltos). ⇒ el
  `ReplicateFeature` **no deja rastro**: el converter puede expandirlo y olvidarlo.
- El `8x5` da 40 agujeros y 552 líneas, que es la cuenta de las 12 líneas por agujero.
- ⭐ **`RowLayoutAngle`** —90 por defecto— **rota la dirección de las FILAS, no el patrón
  entero**: las columnas siguen sobre X con paso 32, y con 60° la segunda fila se corre a
  `(+16, +27.713)` = `(32·cos60, 32·sin60)`.

⚠️ **Nuestro `DrillPatternSpec` no modela el ángulo**: tiene columnas, filas y los dos pasos,
pero no `RowLayoutAngle`. Es un hueco del sintetizador, no del converter.

### Grupo 6 — las caras laterales

**El movimiento va por el eje de la cara** (`G1 G9 Y…` en delantera/trasera, `G1 G9 X…` en
derecha/izquierda), y **la altura del agujero entra por la Z del posicionamiento**, directo
(`G0 Z9.000` contra `G0 Z5.000`).

⭐⭐ **Y cierra la fórmula de la cota**, que el Grupo 2 no podía separar:

| cara | cara de entrada | punta | emitido | cuenta |
|---|---|---|---|---|
| trasera | Y=400 | 385 | **Y450.000** | 385 **+ 65** |
| delantera | Y=0 | 15 | **Y−50.000** | 15 **− 65** |
| derecha | X=400 | 385 | **X450.000** | 385 + 65 |
| izquierda | X=0 | 15 | **X−50.000** | 15 − 65 |
| superior | Z=18 | 8 | **Z85.000** | 8 **+ 77** |

```
coordenada emitida = punta − (dirección de avance) × tool_offset_length
aproximación       = cara − (dirección) × (plano de seguridad + tool_offset_length)
```

⇒ **El offset sale del catálogo de herramientas** (65 lateral, 77 vertical), no es una
constante del cabezal. La ambigüedad de §5 queda cerrada sin necesitar el fixture con fresa.

### ⭐ Las brocas delantera y trasera están CRUZADAS

| `.pgmx` elige | `?%ETK[6]` emitido | qué cara mecaniza |
|---|---|---|
| `058` | **59** | trasera |
| `059` | **58** | delantera |
| `060` | 60 | derecha |
| `061` | 61 | izquierda |

Verificado en el `ToolKey` de cada archivo (IDs 1895/1896), no en el nombre. En las verticales
y en derecha/izquierda el número de herramienta y el de huso coinciden; **en delantera/trasera
no**.

⇒ Y `pgmx/data/tool_catalog.csv` dice lo contrario: llama a `058` «Broca Plana Cara
**Delantera**» y a `059` «Cara **Trasera**».

> 📌 **Corrección de procedencia (Fermín, 2026-08-30): el CSV lo armó él con IA como resumen y
> NO es origen de datos.** Todas las citas al catálogo de este documento —el `77`, el `65`, los
> `6000`/`4000`— quedaron **re-ancladas en `def.tlgx`**, que sí viene de la máquina y coincide
> en los doce registros. `def.tlgx` además **viaja dentro de cada `.pgmx`**, así que el
> converter lo tiene siempre a mano. Ver `iso/docs/plan_software_scm.md` §1.

⭐ **La descripción es nuestra, no de la máquina**: en `def.tlgx` el nodo de las dos brocas
trae **`<Description />` vacía**. Todas las descripciones del CSV las escribió alguien a mano
al derivarlo (la brecha F0.7), y en este par quedaron al revés.

⚠️ **Consecuencia de método**: ninguna columna `description` del catálogo es evidencia. Lo que
sí está en `def.tlgx` es el `Name`, el diámetro y las longitudes.

### ⭐⭐ El `?%ETK[0]` no es `2^(huso−1)`

Los laterales emiten `1073741824` (2³⁰) para los husos 58 y 59, y `2147483648` (2³¹) para el 60
y el 61 — o sea que **dos husos distintos comparten máscara**, y la regla derivada con los
verticales no vale.

Lo que sí vale, y sale de la config: la **posición 1** del registro de `spindles.cfg`.

| huso | pos 1 | `?%ETK[0]` | |
|---|---|---|---|
| 1 | 1 | 1 = 2⁰ | ✓ |
| 5 | 5 | 16 = 2⁴ | ✓ |
| 58 · 59 | **31** | 1073741824 = 2³⁰ | ✓ |
| 60 · 61 | **32** | 2147483648 = 2³¹ | ✓ |

```
?%ETK[0] = 2^(pos1 del registro del huso − 1)
```

En las verticales `pos1` coincide con el número de huso, y por eso la regla vieja parecía
funcionar. **Queda sourced desde la configuración**, que es lo que pide la regla 4.

Y la regla del `SHF` del huso se confirma también en los laterales —`SHF = −pos23 / −pos24 /
−pos25`— con **doce valores más**, incluidos los `66.500 / 66.450 / 66.300` de la Z.

### ⛔ El `061` en campo A tampoco entra

`[6,8] - ChkPgm línea 21: Microinterruptor- de tope eje X (T= 61)`, el mismo mecanismo que la
cónica: `−50 − 3685.850 − 118.000 = −3853.850`, contra el límite `−3702.000`. Se pasa 151.85 mm.
En `HG` da −568 y postprocesa sin problema — por eso el fixture se rehízo ahí.

⇒ Segunda confirmación de que **el rechazo es predecible desde la config**.

### Grupo 7 — la tabla de incrementos del `Xmsg`

Base del campo A: **212**.

| fixture | `N` | incremento |
|---|---|---|
| un taladro vertical | 349 | **+137** |
| el mismo con la X en `92.5` | 348 | **+136** |
| un taladro lateral | 346 | **+134** |
| cinco agujeros en fila | 621 | **+409** |

⇒ **Un agujero vertical cuesta 137; cada agujero adicional con el mismo huso, 68**
(`137 + 4×68 = 409` ✓). Un lateral cuesta **134**.

⚠️ **Y el contenido pesa, pero al revés de lo esperado**: la coordenada `92.5` —un carácter más
que `100`— **baja** el conteo en 1. Con el `Xmsg` el texto más largo lo subía. Medido, sin
explicación.

> ✅ **RESUELTO el 2026-09-07, y no era al revés: estábamos contando el número equivocado.**
> El conteo mira el **texto EMITIDO**, no el valor tipeado. En el ISO la coordenada sale
> siempre con tres decimales: `X100.000` son **ocho** caracteres y `X92.500` son **siete**. El
> `92.5` no tiene un carácter más — tiene uno **menos**, y por eso baja el conteo en 1.
> Exactamente lo esperado.
>
> Lo confirmó el canal desde el otro lado: `X50.000` y `X92.500` tienen **el mismo largo**, y
> el conteo **no se mueve** (`canal.md` §23). Detalle en `operaciones_maquina.md`.

## 7ter. El Optimizador no cambia nada — y se sabe por qué (2026-09-01)

Idea de Fermín: el botón `Optimizador` nunca se usó en el taller porque no se le veía
diferencia en la ejecución. La sospecha era que la diferencia estaba en las sutilezas que este
lote destapó — que Maestro no agrupa husos ni reordena.

**Dato de método**: al activar la Optimización automática, **Maestro guarda el archivo solo**,
agregándole `Opt` al final del nombre. Eso es el **testigo**: la opción estaba puesta, y lo
prueba el software, no una etiqueta escrita a mano.

### El resultado: nulo, en los dos lados

| | |
|---|---|
| el `.pgmx` optimizado contra el original | **6 tags distintos**, todos de la `Key` del proyecto (`ID 1908` → `0`). El contenido —operaciones, coordenadas, orden— es idéntico |
| los ISO | **idénticos línea por línea** en los seis casos: `dos_x32`, `dos_x50`, `fila5_x32`, `tres_orden_inverso`, `patron_8x5_32` (40 agujeros) y el par a 64 mm |

⇒ **La optimización no se guarda en el `.pgmx` y no cambia el ISO.** El converter **no tiene que
reproducirla**.

### ⭐⭐ Y la razón no es que el optimizador sea flojo

El decompilado dice que agrupa por **`HoleType` = diámetro + profundidad + tipo de punta**, y
que un huso sólo toma un agujero si `IsCompatibleHole` e `IsCompatibleHolePosition`.

Los siete husos verticales de esta máquina, según `def.tlgx`:

| huso | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| diámetro | 8 | 15 | 20 | 35 | 5 | 4 | 5 |
| punta | plana | plana | plana | plana | plana | plana | **cónica** |

**Ningún par de husos hace el mismo tipo de agujero.** Los dos de Ø5 se separan por la punta,
que es parte del `HoleType`.

⇒ **En esta máquina la perforación múltiple es imposible por construcción**: cada tipo de
agujero tiene exactamente un huso capaz, así que no hay dos que puedan bajar juntos. El
optimizador no tiene nada que agrupar — y por eso el taller nunca le vio diferencia.

Lo confirma el fixture que Fermín agregó a propósito: **dos agujeros a 64 mm**, que es
exactamente la distancia entre el huso 1 y el huso 5. Geométricamente los dos husos caen sobre
los dos agujeros a la vez — pero son Ø8 y Ø5, o sea **dos `HoleType` distintos**, y no se
agrupan.

⚠️ **Alcance**: vale para **esta** máquina. En un cabezal con dos husos de la misma broca el
optimizador sí agruparía, y ahí el converter tendría que reproducirlo. La conclusión es sobre
la configuración, no sobre el algoritmo.

## 7quater. Grupo 9 — la tecnología entre agujeros (2026-09-01)

Cuatro fixtures con dos y tres brocas de distinta velocidad en el mismo programa. Contestan lo
que el lote anterior no podía, porque las brocas `001` y `005` comparten las 6000 rpm.

### ⭐ El `S` se re-emite sólo cuando CAMBIA el valor

`001_002_003_velocidades` — brocas de 6000, 4000 y 4000 rpm:

```
?%ETK[6]=1 · S6000M3 · ?%ETK[0]=1 · … F2000.000
?%ETK[6]=2 · S4000M3 · ?%ETK[0]=2 · … F1000.000
?%ETK[6]=3 ·  (sin S) · ?%ETK[0]=4 · … F1000.000
```

El tercer huso **no repite el `S`** porque sigue en 4000. ⇒ no es «uno por cambio de huso»: es
**uno por cambio de valor**. Y `002_001_velocidades` lo confirma al revés (4000 → 6000).

### El `F` sí se emite en cada agujero, y sale del AVANCE

| broca | penetración Std | avance Std | rotación Std | ISO |
|---|---|---|---|---|
| 001 | 2 | **2** | 6000 | `F2000` · `S6000` |
| 002 | 2 | **1** | 4000 | `F1000` · `S4000` |
| 003 | 2 | **1** | 4000 | `F1000` · sin `S` |

⇒ **`F = avance Std × 1000`**. La broca `002` es la que lo separa: tiene la misma penetración
que la `001` (2) y distinto avance (1), y el ISO sigue al avance.

*(Corrige lo escrito en §5ter, que atribuía el `F2000` a la penetración — con la `001` sola las
dos columnas valen 2 y no se distinguían.)*

Y `001_002_avances`, con los avances puestos a mano, da `F3000` y `F1000`: **el programa pisa al
catálogo, agujero por agujero**.

### ❌ No hay pausa entre agujeros, ni al cambiar de huso

Un solo `G4F1.200`, al cierre, en los cuatro — **incluso cuando el husillo pasa de 6000 a 4000
rpm**. Negativo **con testigo**: el `S` sí cambia en el mismo archivo, así que la variación
estaba puesta.

## 7quinquies. Grupo 10 — varias caras (2026-09-02)

Diecisiete fixtures de Fermín, con agregados propios: las laterales hechas **también por
diámetro**, y las combinaciones entre caras que el lote no tenía.

### ⭐⭐ La cara inferior se descarta EN SILENCIO

`spindles.cfg` no tiene ningún huso con `FACE = 6`. La UI igual ofrece `Lado inferior`, y
Maestro **acepta y guarda** el programa.

| | |
|---|---|
| `bottom_D8P` solo | el ISO es el del **programa vacío** más dos líneas: `?%ETK[8]=1` y `G40` — el preámbulo del bloque de operaciones, abierto y vacío |
| `bottom_D8P` + `top_D8P` | el `.pgmx` tiene **2 features**; el ISO emite **1 agujero** |

⇒ **No hay error, no hay advertencia: el agujero desaparece.** La pieza saldría sin él y nada
avisa.

⚠️ **Y le plantea una decisión al converter**, porque las dos reglas del `CLAUDE.md` chocan:
el byte-idéntico manda **reproducir el silencio**; el fail-loud manda **rechazar**.

### ⚖️ DECISIÓN DE FERMÍN (2026-09-03): excepción, y fail-loud

Cuando las dos reglas se contradicen, **gana el fail-loud**. Un agujero que desaparece sin aviso
es peor que un ISO que no coincide byte a byte con el de Maestro.

**Por ahora**: el converter **rechaza** un programa con mecanizados en la cara inferior, y dice
por qué.

**Más adelante, con el converter completo**, el arreglo no es emitir el silencio sino **resolver
la pieza**: el sintetizador de `.pgmx` agrega

1. un **`Xn`** y un **`Xmsg`** con el texto **«Girar Pieza»**,
2. una **fase** nueva con origen en (0, 0),
3. y **traslada la perforación a la cara superior**.

Así se mecanizan primero la cara superior y las cuatro laterales, el operario gira la pieza, y
la cara inferior se mecaniza **puesta hacia arriba** — que es como el taller lo haría a mano.

⇒ Es la primera excepción declarada a la regla 4, y no debilita el byte-idéntico: lo que se
emite sigue siendo verificable contra Maestro **para los programas que Maestro puede hacer
bien**. Lo que se rechaza es un caso donde Maestro produce una pieza incorrecta en silencio.

### ⛔ Pero una cara CON huso y un diámetro imposible sí falla

`front_D15P` — Ø15 en la cara delantera, cuyo único huso lleva una broca Ø8:

```
[10,9] - BOopt: (Línea 21) No hay una broca para colocar en la repetición 0
        por incompatibilidad geométrica o final de carrera ejes
```

⇒ **Dos comportamientos distintos ante la misma imposibilidad**: cara sin husos → silencio;
cara con huso y diámetro incompatible → rechazo explícito. El converter tiene que distinguirlos.

### ⭐⭐ El ISO NO reordena entre caras

`top_front_top_alternado` —superior, delantera, superior, creados así— emite **en ese orden**,
con el huso 1, después el 58, después el 1 **otra vez**. Su control `top_top_front_directo`
emite los dos de arriba seguidos.

⇒ La regla del orden de creación, ya derivada dentro de una cara, **vale también entre caras**.
Maestro no agrupa por cara aunque volver salga caro.

### ⭐⭐ La transición entre caras, y una fórmula de la época congelada que acierta

Volver de una cara a otra emite un retiro absoluto de máquina:

```
?%ETK[6]=<huso nuevo>
MLV=0
G0 G53 Z124.500          <- el retiro
…
S<velocidad>M3           <- la velocidad va DESPUES del retiro
```

Aparece en **los siete** archivos que combinan dos caras y en **ninguno** de una sola —
incluidos `front`+`back`, así que también hay transición entre dos laterales.

Y el valor sale de la fórmula que la época congelada había derivado para el `TLC_LATERAL`:

```
g53_z = DZ + 20 + max(77, plano_de_seguridad + shf_z del huso)
      = 18 + 20 + max(77, 20 + 66.50) = 124.500   ✓
```

⇒ **Re-derivada con evidencia de la época nueva.** Predicción falsable: volver de la cara
**derecha** (huso 60, `shf_z` 66.45) daría **124.450**, y de la **izquierda** (66.30),
**124.300**.

### Lo demás que contestó el lote

| | |
|---|---|
| costo por agujero extra en una lateral | **16 líneas** (contra 12 en la superior) |
| el patrón en una lateral | **byte-idéntico** a los tres agujeros sueltos — sigue siendo azúcar |
| por herramienta contra por diámetro | **el mismo ISO**, también en las laterales |
| el `S` al cambiar de cara | **se re-emite**, en los dos sentidos (4000→6000 y 6000→4000) |

> 📌 Dos de los pares por-diámetro daban diferencias, y **ninguna era de la herramienta**: en
> uno cambió el **orden** de los agujeros y en otro la **profundidad** (`Y450` = prof 15 contra
> `Y447` = prof 18). El par limpio —el patrón en la cara delantera— sale en cero.

### 📌 Y el catálogo de mensajes queda direccionable

El error del `D15P` destapó que el volcado del 30 estaba mal parseado: los `.msg` tienen
**bloques `MODULE`** y la numeración `@NNN` **reinicia en cada uno** (32 veces sólo para `@009`
en `Sys.msg`). Con el formato real —`MODULE <n>,<prefijo>: ,<cantidad>`— los tres rechazos que
capturamos se resuelven exactos, prefijo incluido:

| en pantalla | `MODULE` | mensaje |
|---|---|---|
| `[23,6] - Bag. IJ:` | 23 · `Bag.%s:` | Área de trabajo no configurada |
| `[6,8] - ChkPgm línea 21:` | 6 · `ChkPgm línea %U:` | Microinterruptor- de tope eje X (T=%c%d) |
| `[10,9] - BOopt:` | 10 · `BOopt:` | (Línea %D) No hay una broca para colocar… |

⇒ El corchete es **(MODULE, @NNN)**, y el prefijo que se ve sale de la cabecera del módulo.
3.083 mensajes en 55 módulos.

## 7sexies. Grupo 11 — las cinco caras, en HG (2026-09-03)

Diez pares en campo `HG`, el único donde entran las cinco caras (la broca `061` se pasa del
tope del eje X en campo A).

### ⭐⭐ El pecking, CERRADO

`profpasada_7` era el fixture que separaba los dos modelos al máximo. Sobre el agujero de 10:

| | cortes esperados | Z |
|---|---|---|
| «respeta el paso» | 7 · 10 | 88.000 · 85.000 |
| «reparte iguales» | 5 · 10 | **90.000 · 85.000** |

**El ISO emite `Z90.000` y `Z85.000`.** ⇒ **reparte en partes iguales**, sin margen.

Y `profpasada_4_bis` —el mismo caso rehecho y repostprocesado— da otra vez `91.667 · 88.333 ·
85.000`. ⇒ **el ISO anterior no era de una versión vieja del archivo**; la hipótesis del fixture
desincronizado queda descartada.

⇒ La regla queda firme: **`n = ceil(profundidad / paso)`, y después partes iguales.** La
profundidad de pasada es un **máximo**, no un paso.

> 🐞 **Lectura de Fermín (2026-09-03): es un bug de Maestro.** Lo que la UI ofrece como
> «profundidad de pasada» y lo que la máquina ejecuta no coinciden cuando el paso no divide
> exacto: Maestro guarda y muestra `4 · 4 · 2` y el CNC hace `3.33 · 3.33 · 3.33`. Con
> `StepDepth = 2` coinciden por casualidad, y por eso pasa desapercibido.
>
> ⏸ **Se retoma al estudiar las estrategias de fresado y sus multipasadas**, donde el mismo
> mecanismo vuelve a aparecer y con más variantes. Para el converter no cambia nada: lo que hay
> que reproducir es lo que emite la máquina.

### ⭐⭐ La fórmula del `G53` de transición, afinada

Las tres predicciones aciertan —`124.450` desde la derecha, `124.300` desde la izquierda,
`124.500` desde delantera y trasera— pero el lote muestra que **no es el huso del que se sale**:
es el **máximo de los dos**.

`cuatro_laterales` lo destapa: la transición **derecha → izquierda** emite `124.450`, no
`124.300`.

```
G0 G53 Z = DZ + 20 + max( 77 , seguridad + shf_z(huso que sale) , seguridad + shf_z(huso que entra) )
```

| transición | shf_z en juego | emitido |
|---|---|---|
| sup → derecha · derecha → sup | 0 · 66.45 | **124.450** |
| sup → izquierda · izquierda → sup | 0 · 66.30 | **124.300** |
| derecha → izquierda | 66.45 · 66.30 | **124.450** (el mayor) |
| izquierda → delantera | 66.30 · 66.50 | **124.500** (el mayor) |
| sup → delantera / trasera | 0 · 66.50 | **124.500** |

**Doce transiciones verificadas sobre las cuatro caras laterales.** Es la fórmula que la época
congelada tenía para el `TLC_LATERAL` —con su `max` sobre los husos involucrados— re-derivada
entera con evidencia de la época nueva.

### ⭐ El orden se respeta con cinco caras y siete transiciones

`cinco_caras_orden_alternado` emite **sup → DER → sup → IZQ → sup → DEL → sup → TRA**: cuatro
oportunidades de agrupar los agujeros superiores, y **no agrupó ninguna**.

El par estricto es `tres_caras_dos_agujeros` contra su alternado —**los mismos seis agujeros**—
y también respeta el orden: tres bloques contra seis. El costo de no agrupar: **39 líneas más**
(215 contra 176) por tres transiciones extra, o sea **13 líneas por transición**.

### ⭐⭐ Y el orden de ejecución NO vive en `<Features>` ni en `<Operations>`

Los dos archivos de `tres_caras` tienen **las mismas features y las mismas operaciones, en el
mismo orden del documento**, y sus ISO son distintos. Lo que cambia son los
**`MachiningWorkingStep`**, cada uno apuntando por ID a un feature y a una operación.

⇒ `<Features>` y `<Operations>` son **catálogos sin orden significativo**; el plan de ejecución
—y por lo tanto el orden que el ISO respeta— vive en los **working steps del workplan**.

#### Y no hay clave de orden: el orden ES la posición (2026-09-03)

Fermín aclara que en el alternado **sólo reordenó los perforados ya creados**, sin tocar nada
más. Los seis `MachiningWorkingStep` son los mismos en los dos archivos —mismos `OperationID`,
mismos `ManufacturingFeatureID`, mismos nombres— y **`Priority` vale `0` en los doce**.

| archivo | orden de los working steps |
|---|---|
| `tres_caras_dos_agujeros` | `Taladrado` · `(1)` · `(2)` · `(3)` · `(4)` · `(5)` |
| `…_alternados` | `Taladrado` · **`(2)`** · **`(4)`** · **`(1)`** · **`(3)`** · `(5)` |

⭐ Los nombres los pone Maestro **al crear** cada paso, así que en el alternado quedan salteados:
**el nombre conserva la historia de creación y la posición conserva el orden de ejecución.**

⇒ **El converter lee `Workplans/MainWorkplan/Elements` en orden de documento.** `Priority`
existe pero no ordena — con esta evidencia. Si alguna vez aparece distinto de `0` (fases, otros
tipos de mecanizado), hay que volver acá.

⚠️ El barrido del corpus (`fixtures.md` §6) **no vio esto**: aplana por rutas y los working
steps quedaron fuera de su alcance. Punto ciego del barrido, no de los datos.

### 🎁 Y la cara inferior, confirmada dos veces más

Fermín agregó por su cuenta perforaciones en la **cara inferior**:

| fixture | features en el `.pgmx` | agujeros en el ISO |
|---|---|---|
| `cinco_caras_orden_natural` | **6** | **5** |
| `cinco_caras_orden_alternado` | **9** | **8** |

⇒ El **descarte silencioso** de §7quinquies queda confirmado en un programa **multi-cara**,
donde todo lo demás se emite normalmente. No es un caso de borde de un programa de un solo
agujero.

### El resto, confirmado

- **La velocidad se re-emite por cambio de VALOR, no de huso ni de cara.**
  `002_003_derecha_izquierda` (husos 2·3·60·61) emite el `S` **dos veces**: `4000` al empezar
  —y no lo repite en el huso 3, que también es 4000— y `6000` al pasar a la derecha, sin
  repetirlo en la izquierda. Su gemelo alternado lo emite las cuatro veces.
- **El patrón sigue siendo azúcar en las cuatro laterales** (`cuatro_laterales_patron`, ocho
  agujeros en cuatro patrones 2×1).

## 8. El fixture que mintió, y para qué sirvió

`R_PV_A_manual_perf_top_D8_x100_y100_prof5.pgmx` **guarda diámetro 5 y profundidad 10**: el
`5` se tipeó en `Diámetro orificio` en vez de en `Profundidad`. Los dos campos están uno
encima del otro en la ventana.

- Lo detectó el verificador de fixtures (`iso/docs/fixtures.md`), no la lectura del ISO: el
  ISO era **coherente consigo mismo** y sólo desentonaba contra los otros nueve.
- ✅ **Corregido el 2026-08-28**: `top_D8_x100_y100_prof5` se rehízo con Ø8/prof5 (da
  `Z90.000`, huso 1) y el archivo original quedó como **`top_D5P_x100_y100_prof10`**
  (`Z85.000`, huso 5, `SHF[X]=−64.000`, `SHF[Z]=−0.950`), que es la evidencia del huso 5 en
  el Grupo 1. Los dos con su `.iso`. El lote quedó en **0 contradicciones sobre 73 archivos**.
- Es el **primer caso real** del modo de falla que motivó la regla del nombre (2026-08-27), y
  de una variante que no se había previsto: no es que el cambio no se aceptara, es que **el
  valor entró en el campo de al lado**.
- Y de rebote **dio el hallazgo de §7**: sin ese error no habría un segundo huso en el Grupo 1.

⏸ **Hay que rehacerlo** con diámetro 8 y profundidad 5. Conviene **conservar el actual** con un
nombre que diga la verdad (`top_D5P_x100_y100_prof10`), porque es la evidencia del huso 5.

## 8bis. Estado del lote (2026-08-28)

| grupo | `.pgmx` | `.iso` | estado |
|---|---|---|---|
| 0 · el campo | 34 | 20 | ✅ completo. Los 14 sin ISO son los campos `I`–`L` y los numéricos, rechazados — con captura del error |
| 1 · el mínimo y sus cotas | 11 | 11 | ✅ completo. El `top_D8_…_prof5` se rehízo el 28 y el archivo viejo quedó como `top_D5P_…_prof10` (§8) |
| 2 · la broca | 28 | 26 | ✅ completo. Los 2 sin ISO son la cónica en campo A, rechazada por carrera de eje (§7bis) |
| 3–7 | — | — | ⬜ pendientes |

**Todos los ISO tienen su `.pgmx`.** Los siete de `HG` por diámetro habían quedado fuera de la
carpeta del grupo y se movieron el 28; verificados uno por uno: campo `HG`, diámetro y punta los
que dice el nombre, y `ToolKey` vacío en los siete —o sea que **son de verdad el método por
diámetro**, que es lo que el nombre no alcanza a afirmar por sí solo.

> Por eso el verificador chequea, desde el 28, que **un nombre con `D<n><P|C|A>` implique
> `ToolKey` vacío**: el esquema de nombres distingue los dos métodos, así que el método también
> es una afirmación verificable, no una convención de palabra.

## 9. Lo que queda abierto

| | |
|---|---|
| `?%ETK[17]=257` | igual en los diez. Falta hacerlo variar |
| `G4F1.200` | la espera del cierre: de dónde sale el 1.2 |
| el plano de seguridad | vale 20 por defecto y no está en la parte visible de la ventana. Falta la captura de las secciones plegadas |
| `Estrategia` en un taladro | sección sin capturar; ni siquiera sabemos qué ofrece |
| pasadas / descarga de virutas | no aparecen en la ventana visible. Deciden el número mágico `peck+1` |
| la posición 24 de `spindles.cfg` | ¿es la `Y` del huso? Lo contestan las brocas 002 y 003 |
| el incremento del conteo del `Xmsg` | Grupo 7 |
