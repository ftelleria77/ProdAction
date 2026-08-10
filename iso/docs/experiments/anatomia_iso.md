# Anatomía del ISO — atribución línea por línea (rama B)

**Documento vivo.** Cada línea del ISO tiene que poder atribuirse a UNO de los tres
orígenes; lo que no se pueda atribuir queda escrito como desconocido, nunca como
supuesto. Crece con cada operación nueva.

Los tres orígenes (ver `programa_vacio.md`):

| # | Origen | Dónde vive |
|---|---|---|
| 1 | **Programa** | el `.pgmx` |
| 2 | **Máquina** | snapshot de la PC del CNC (`iso/data/machine_config/snapshot/`) |
| 3 | **Aplicación** | `<Maestro>\UI00.exe.Config` (ventana Opciones) |

Niveles de confianza, explícitos en cada fila:

- **DERIVADO** — la evidencia lo prueba (un fixture que varía esa cosa y sólo esa).
- **HIPÓTESIS** — encaja, pero un solo caso no lo separa de otras lecturas. Dice qué
  fixture lo confirmaría.
- **DESCONOCIDO** — no se sabe. No se rellena con nada.

## B1 · El esqueleto: programa sin mecanizados

**Fuente**: `R_PV_manual_base.pgmx` (autoría 100% manual de Fermín en Maestro,
2026-08-10) → `P:\USBMIX\ProdAction\Programas Manuales\Reinvestigación\r_pv_manual_base.iso`.
Pieza 400×400×18, origen 0/0/0, área HG, **cero operaciones**.

**43 líneas · 666 bytes · CRLF · termina CON CRLF · cp1252.**

Espacios finales: los llevan casi todas las líneas (uno), salvo la 1, la 3, la 5, la 7
y el bloque 22–29. La 43 (`M2`) lleva **dos**. No es adorno: es parte del byte.

### La estructura

| Líneas | Bloque |
|---|---|
| 1–2 | Cabecera: nombre y `;H` |
| 3–7 | Preámbulo de máquina |
| 8–21 | Puesta a punto del programa (origen, SHF) |
| 22–30 | Reset de registros |
| 31–42 | Teardown (SHF a cero) |
| 43 | Fin |

### Línea por línea

| # | Línea | Origen | Confianza |
|---|---|---|---|
| 1 | `% r_pv_manual_base.pgm` | **Programa** — nombre del ARCHIVO, en minúsculas, extensión `.pgm` | DERIVADO (el par `_cnc` lo prueba: cambió el nombre del archivo y cambió sólo esta línea) |
| 2 | `;H DX=400.000 DY=400.000 DZ=18.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 ` | ver desglose abajo — **ojo: `DX/DY/DZ` son dimensión + origen**, ver B1b | mixto |
| 3 | `?%ETK[500]=100` | ? | DESCONOCIDO |
| 5 | `_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )` | **Máquina** — parámetro 21 del eje 0 | DERIVADO (referencia explícita a `%ax`) |
| 7 | `G0 G53 Z %ax[2].pa[22]/1000` | **Máquina** — parámetro 22 del eje 2, en coordenadas de máquina (`G53`) | DERIVADO |
| 8 | `M58 ` | ? | DESCONOCIDO |
| 9 | `G71 ` | **Aplicación** — G71 es «medidas en mm» | HIPÓTESIS (lo confirma cambiar `IsMM`, que es global) |
| 10 | `MLV=0 ` | ? — abre el bloque de origen | DESCONOCIDO |
| 11 | `%Or[0].ofX=-400000.000 ` | **Máquina** (campo del área) **+ Programa** (`DX`, sólo si el campo vale 0) — µm | **DERIVADO** (fórmula en B1c, 11/11) |
| 12 | `%Or[0].ofY=-1515599.976 ` | ídem sobre el eje Y — µm | **DERIVADO** (misma fórmula) |
| 13 | `%Or[0].ofZ=18000.000 ` | **Programa** — µm; `= DZ` (o sea `depth + origin_z`) | DERIVADO (ver B1b) |
| 14–15 | `?%EDK[0].0=0 ` · `?%EDK[1].0=0 ` | ? | DESCONOCIDO |
| 16 | `MLV=1 ` | ? | DESCONOCIDO |
| 17 | `SHF[X]=-400.000 ` | ídem 11, en mm | **DERIVADO** (B1c) |
| 18 | `SHF[Y]=-1515.600 ` | ídem 12, en mm | **DERIVADO** (B1c) |
| 19 | `SHF[Z]=18.000+%ETK[114]/1000 ` | **Programa** (`DZ`) **+ Máquina** (corrección en runtime) | DERIVADO sobre `DZ` |
| 20 | `?%ETK[8]=1 ` | ? | DESCONOCIDO |
| 21 | `G40 ` | cancelación de compensación — constante del protocolo | DERIVADO por contexto |
| 22 | `SYN` | ? | DESCONOCIDO |
| 23–29 | `?%ETK[0]=0` `[1]` `[2]` `[13]` `[17]` `[18]` `[19]` | reset de registros; el CONJUNTO de índices es fijo | DESCONOCIDO (por qué esos siete) |
| 30 | `?%EDK[13].0=1 ` | **Programa** (el área) — el índice depende de la MITAD de mesa: 10 izquierda, 13 derecha | **DERIVADO** (B1c) |
| 31–34 | `MLV=1 ` + `SHF[X]=0 ` `SHF[Y]=0 ` `SHF[Z]=0 ` | teardown: anula el SHF del nivel 1 | DERIVADO por contexto |
| 35–38 | `MLV=2 ` + `SHF` en cero | ídem nivel 2 — **aparece aunque el nivel 2 nunca se usó** | DERIVADO por contexto |
| 39 | `MLV=0 ` | vuelve al nivel 0 | DERIVADO por contexto |
| 40–41 | `VL6=0 ` · `VL7=0 ` | ? | DESCONOCIDO |
| 42 | `?%EDK[13].0=0 ` | cierra lo que abrió la 30 | DERIVADO por contexto |
| 43 | `M2  ` (dos espacios) | fin de programa | DERIVADO por contexto |

### Desglose del header `;H` (línea 2)

**Resuelto por la documentación de SCM** (2026-08-10), no por fixtures: la firma de
`SetMachiningParameters` del lenguaje de scripting (`pgmx/docs/maestro_scripting/
04_tools_workpiece.md`) dice, parámetro por parámetro, **a qué letra del header `;H`
corresponde cada uno**:

```
SetMachiningParameters(
    string executionFields,   // «same as - in the Xilog H header instruction»
    int    repetitions,       // «same as R …»
    long   tableOptions,      // «same as V …»
    long   mechanicalOptions, // «same as T …»
    bool   continuousCycle    // «same as C …»
)
```

| Campo | Valor | Origen | Confianza |
|---|---|---|---|
| `DX` `DY` `DZ` | 400.000 / 400.000 / 18.000 | **Programa** — **dimensión + origen** de cada eje, no la dimensión sola | DERIVADO (ver B1b) |
| `BX` `BY` `BZ` | 0.000 / 0.000 / 0.000 | ? — **no es el origen** (con origen 100/50/5 siguen en cero); queda `WorkpieceOffset` como candidato | DESCONOCIDO (ver B1b) |
| `-HG` | | **Programa** — `executionFields`, el «Área» de Parámetros de máquina | **DERIVADO** (doc SCM) |
| `V=0` | | **Programa** — `tableOptions`, el «Bloqueo» de Parámetros de máquina | **DERIVADO** (doc SCM) |
| `T=0` | | **Programa** — `mechanicalOptions`, las «Opciones mecánicas» | **DERIVADO** (doc SCM) |
| `C=0` | | **Programa** — `continuousCycle` | **DERIVADO** (doc SCM) |
| `*MM` | | **Aplicación** — unidad de medida (`IsMM`) | HIPÓTESIS |

> ⚠️ **Corrección.** La primera versión de esta tabla atribuía `T=0` a
> `IsTechnologicalMirror` por parecido de inicial. Es **`mechanicalOptions`**. El
> espejo tecnológico **no** está en el header, o está en otro lado. Caso de manual de
> la regla 2: la definición ya estaba escrita y contradecía lo que uno supondría.

**`R` (repeticiones) no aparece** en este header, y el programa tiene `Repetitions=1`:
la lectura natural es que el emisor **omite la letra cuando vale el default**. Sin
fixture todavía — lo confirma un programa con repeticiones ≠ 1.

Y queda a la vista que **`V` y `T` son enteros que agregan varias opciones cada uno**
(«Bloqueo» y «Opciones mecánicas» tienen su panel de sub-opciones en la UI), lo que
refuerza la hipótesis del bitmask anotada en `programa_vacio.md`.

### El origen sale de `fields.cfg`

`iso/data/machine_config/snapshot/xilog_plus/Cfg/fields.cfg` guarda un bloque de 29
valores por área, con la letra del área **al final** del bloque. Los dos primeros
valores de la terna son X e Y:

| Área | X | Y |
|---|---|---|
| E | −3688.00 | −1515.25 |
| F | −1843.00 | −1515.75 |
| G | −1843.00 | −1515.75 |
| **H** | **0.00** | **−1515.60** |

El ISO de un programa en área **HG** usa **Y = −1515.60**, que es el de **H**. Con qué
criterio un área combinada «HG» toma la de H y no la de G es **DESCONOCIDO**; lo
discrimina `R_PV_campo_EF` (si usa E o F).

Y hay una asimetría real entre ejes: **X resta DX y el eje Y no resta DY.**
`SHF[X] = 0 − 400 = −400` mientras `SHF[Y] = −1515.60` tal cual, con DY = 400 también.
El fixture de dimensiones (500×350) lo despeja de una.

### La precisión simple, confirmada con evidencia propia

`SHF[Y] = -1515.600` (mm) y `%Or[0].ofY = -1515599.976` (µm). Si la conversión fuera en
doble precisión, sería `-1515600.000`. En **float32**, `1515.6` es exactamente
`1515.5999755859375`; por 1000 y redondeado a tres decimales da **1515599.976**.

⇒ El emisor pasa por **precisión simple** al convertir a micras. Queda derivado en la
época nueva, sin depender de la anterior.

## B1b · Lo que dijeron los seis fixtures de R001 (2026-08-10)

Postprocesados en el CNC. Cada uno varía UNA cosa contra `R_PV_base`, así que la línea
que se mueve es la respuesta. **Dos hipótesis de arriba quedaron refutadas.**

### ✅ `;H DX·DY·DZ` NO son las dimensiones de la pieza: son **dimensión + origen**

| Fixture | Pieza | Origen | Header |
|---|---|---|---|
| base | 400×400×18 | 0/0/0 | `DX=400 DY=400 DZ=18` |
| dimensiones | **500×350×25** | 0/0/0 | `DX=500 DY=350 DZ=25` |
| origen XY | 400×400×18 | **100/50**/0 | **`DX=500 DY=450`** DZ=18 |
| origen Z | 400×400×18 | 0/0/**5** | DX=400 DY=400 **`DZ=23`** |

`DX = length + origin_x` · `DY = width + origin_y` · `DZ = depth + origin_z`. **DERIVADO**
por dos fixtures independientes. Tiene sentido físico: lo que el header declara es la
**envolvente ocupada** sobre la mesa, y correr el origen la agranda.

⇒ Un converter que escriba ahí las dimensiones de la pieza acierta **sólo** cuando el
origen es 0/0/0.

### ❌ REFUTADO: `BX·BY·BZ` no es el origen

Con origen 100/50/5 los tres siguen en `0.000`. Lo que el origen mueve son `DX/DY/DZ`
(arriba) y los `%Or`/`SHF`. Qué es `BX·BY·BZ` vuelve a **DESCONOCIDO**; el candidato que
queda es `WorkpieceOffsetX/Y/Z`, que el sintetizador no varía.

### ✅ `%Or[0].ofZ` y `SHF[Z]` = `DZ` (ya con el origen sumado)

25.000 con la pieza de 25 y 23.000 con origen Z=5 sobre pieza de 18. **DERIVADO.**

### ✅ `%Or[0].ofY` = el Y del área, y nada más

No se movió con DY (400→350) ni con el origen Y (0→50): quedó en `-1515.60` en los tres.
Con área EF pasó a `-1515.25`. ⇒ **`ofY` sale del área, y sólo del área. DERIVADO.**

### ✅ RESUELTO EN B1c — la fórmula del origen

Lo que sigue quedó abierto con R001 y lo cerró **R002** (ver más abajo): el origen se
calcula por eje contra el campo del área, y **sólo se resta la dimensión cuando la
coordenada del campo es cero**.

### ❌ Lo que R001 refutó: `ofX` no es `campo_X − DX` sin más

| Área | Campo en `fields.cfg` | `ofX` emitido |
|---|---|---|
| **HG** | X = 0.00 | −400.000 (pieza 400) · −500.000 (pieza 500 **y** origen X=100) |
| **EF** | X = −3688.00 | **−3688.000** (pieza 400) |

Con HG la fórmula `campo_X − (DX+ox)` daba bien (0−400, 0−500). Con EF debería dar
−4088 y el emisor puso **−3688**, o sea el valor del campo tal cual. La regla que sirve
para un área no sirve para la otra ⇒ **la fórmula de `ofX` queda DESCONOCIDA**, y con
ella la correspondencia área↔bloque de `fields.cfg` (que se había leído asignando cada
letra al bloque que la precede — tampoco está confirmado).

Lo discrimina un lote de áreas: AB, CD, y HG/EF con piezas de distinta medida.

### ✅ El área también cambia el registro `EDK`

`?%EDK[13].0` con **HG** → `?%EDK[10].0` con **EF**, en las dos apariciones (la que abre
en la línea 30 y la que cierra en la 42). ⇒ **el índice del `EDK` identifica el área.**
Con dos áreas no alcanza para la tabla completa: hace falta el mismo lote.

### ✅ El bloque del `Xn` («Operación nula»)

Con un `Xn` de defaults, el ISO gana **ocho líneas** entre el `G40` de la línea 21 y el
`SYN`, sin tocar nada más:

```
?%ETK[8]=1
G40
G61
MLV=0
D0
G0 G53 Z201.000
G0 G53 X-3700.000
G64
```

- **`X-3700.000` es el valor del `Xn`**, no una constante: es el `x` de la spec.
- `Z201.000` no está en el programa ⇒ **Máquina** (pendiente de ubicar en qué `.cfg`).
- `G61`/`G64` abren y cierran el bloque; `D0` y `MLV=0` lo preparan.
- **No hay `M5`.** El Xn va en el CUERPO del programa, no en el cierre.

## B1c · El área, resuelta (lote R002, 2026-08-10)

Once fixtures sin operaciones, variando sólo el área (y, en tres, la medida o el origen).
Cierra las tres preguntas que había dejado R001.

### ✅ La fórmula del origen — verificada 11/11

```
SHF[eje] = campo(primera letra del área, eje)  −  D_eje   SÓLO SI campo(eje) == 0
```

donde `D_eje` es el valor del header `;H` (o sea **dimensión + origen**, ver B1b) y
`%Or[0].of*` es lo mismo en micras.

Leído en castellano: **la coordenada del campo marca el tope contra el que apoya la
pieza.** Si el tope está en 0 —el extremo de la mesa—, la pieza cuelga hacia el negativo
y su esquina queda en `−D`. Si el tope ya está en negativo, la esquina **es** el tope, y
la medida de la pieza no entra.

Por eso R001 parecía contradecirse: con `HG` (campo H, X = 0) el emisor restaba `DX`, y
con `EF` (campo E, X = −3688) no. No eran dos reglas: es una sola, y el `0` era la
condición.

| Fixture | Área | 1ª letra | campo X · Y | `SHF[X]` | `SHF[Y]` |
|---|---|---|---|---|---|
| `ab` | AB | A | −3685.85 · 0.00 | −3685.850 | −400.000 |
| `cd` | CD | C | −1843.00 · 0.00 | −1843.000 | −400.000 |
| `dc` | DC | **D** | 0.00 · 0.00 | **−400.000** | −400.000 |
| `ef` | EF | E | −3688.00 · −1515.25 | −3688.000 | −1515.250 |
| `gh` | GH | G | −1843.00 · −1515.75 | −1843.000 | −1515.750 |
| `hg` | HG | **H** | 0.00 · −1515.60 | **−400.000** | −1515.600 |
| `ab_dx600` | AB | A | X ≠ 0 | −3685.850 (**no se mueve**) | −400.000 |
| `ef_dx600` | EF | E | X ≠ 0 | −3688.000 (**no se mueve**) | −1515.250 |
| `hg_dx600` | HG | H | X = 0 | **−600.000** (sigue a DX) | −1515.600 |
| `ef_ox100` | EF | E | X ≠ 0 | −3688.000 (**el origen tampoco entra**) | −1515.250 |

Nótese que el eje Y obedece la misma regla, no otra: los campos A–D tienen `Y = 0`, y ahí
`SHF[Y] = −DY = −400`; los E–H tienen `Y ≈ −1515`, y ahí se usa tal cual. Lo que en R001
parecía «X resta y el eje Y no» era, otra vez, la condición del cero.

### ✅ Manda la PRIMERA letra del área

`CD` → −1843 (campo C) contra `DC` → −400 (campo D). Mismas dos letras, distinto orden,
distinto origen. Ídem `GH` (−1843, campo G) contra `HG` (−400, campo H). **El orden no es
cosmético: elige el campo de referencia.**

### ✅ Un área de una sola letra se normaliza

Pedimos área `A` y el ISO emitió **`-AB`**. Maestro completa el par.

### ✅ La tabla de `?%EDK[n]` — es la MITAD de la mesa, no la fila

| Área | 1ª letra | `EDK` |
|---|---|---|
| AB · EF | A · E | **10** |
| CD · DC · GH · HG | C · D · G · H | **13** |

Las áreas que arrancan en la mitad **izquierda** de la mesa (campos A/B y E/F, los de X
más negativo) usan `EDK[10]`; las de la mitad **derecha** (C/D y G/H), `EDK[13]`. La fila
(Y = 0 contra Y ≈ −1515) **no** influye. Con cuatro áreas por mitad no hay más casos que
probar en esta máquina.

### La tabla de campos de esta máquina

De `fields.cfg`, ya parseado bien: bloques de 29 valores en columnas de 13 caracteres,
cada uno **cerrado** por una línea separadora rellena de `0x03` que lleva la letra. (El
primer bloque no trae letra: no es un campo.) Los valores 15 y 16 del bloque son X e Y;
el 18 y 19, ancho y alto.

| Campo | X | Y | ancho | alto |
|---|---|---|---|---|
| A | −3685.85 | 0.00 | 1843 | 1555 |
| B | −1843.00 | 0.00 | 1843 | 1555 |
| C | −1843.00 | 0.00 | 1843 | 1555 |
| D | 0.00 | 0.00 | 1843 | 1555 |
| E | −3688.00 | −1515.25 | 1843 | 1555 |
| F | −1843.00 | −1515.75 | 1843 | 1555 |
| G | −1843.00 | −1515.75 | 1843 | 1555 |
| H | 0.00 | −1515.60 | 1843 | 1555 |

Dos filas de cuatro campos de 1843 × 1555: la fila `Y = 0` (A–D) y la fila `Y ≈ −1515`
(E–H). Los campos I–P están en cero — no existen en esta máquina.

⚠️ **Ojo con A y E**: −3685.85 y −3688.00 difieren en 2,15 mm, y sus pares de la otra fila
también (−1515.25 contra −1515.60/−1515.75). No es ruido del emisor: **son valores de
calibración, distintos por campo**, y salen del archivo tal cual. Un converter que
promedie o redondee ahí rompe el byte-idéntico.

## Preguntas que abre el esqueleto

- ¿Qué es `V=0` del header? ¿Y `Repetitions`, que no aparece?
- ¿Por qué el reset toca justo los registros `ETK[0,1,2,13,17,18,19]`?
- ¿Qué son `M58`, `SYN`, `VL6`, `VL7`, `EDK[13].0`, `ETK[8]`, `ETK[500]`?
- El teardown escribe `MLV=2` aunque el nivel 2 nunca se usó: ¿es fijo o depende de la
  máquina?
- `%ETK[114]` de la línea 19: ¿qué corrección es, y de dónde sale?

Las responden los `.cfg` del snapshot, el manual de Xilog (`pgmx/docs/xilog_plus_pgm/`) y
los fixtures de R001 — en ese orden: primero leer, después preguntar (regla 2).
