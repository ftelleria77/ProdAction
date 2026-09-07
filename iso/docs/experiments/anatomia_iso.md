# Anatomía del ISO — atribución línea por línea (rama B)

**Documento vivo.** Cada línea del ISO tiene que poder atribuirse a UNO de los tres
orígenes; lo que no se pueda atribuir queda escrito como desconocido, nunca como
supuesto. Crece con cada operación nueva.

Los **cuatro** orígenes (los tres primeros, en `programa_vacio.md`):

| # | Origen | Dónde vive |
|---|---|---|
| 1 | **Programa** | el `.pgmx` |
| 2 | **Máquina** | snapshot de la PC del CNC (`iso/data/machine_config/snapshot/`) |
| 3 | **Aplicación** | `<Maestro>\UI00.exe.Config` (ventana Opciones) |
| 4 | **Emisor** | `iso/data/machine_config/emisor_iso.cfg` — **archivo nuestro** (2026-08-13) |

> El cuarto son las líneas que pone el generador ISO de Xilog y que no salen de ningún
> archivo de la instalación. Decisión de Fermín: **no se escriben dentro del converter**,
> se guardan como un origen más y se leen. Ver `emisor_iso.md`.

> ⭐ **El postproceso tiene dos etapas** (2026-08-12, ver `emisor_iso.md`):
> `.pgmx` → **XXL** → PGM → **ISO**. Maestro produce el XXL —donde actúan los orígenes 1 y
> 3—; el generador de Xilog lo traduce a ISO, y ahí actúan el origen 2 y el emisor. **El
> origen de la pieza se resuelve en la segunda etapa**: Maestro escribe `O X=0 Y=0 Z=0` y
> los `−400.000` de `fields.cfg` los pone el generador. Casi todo lo mapeado abajo pertenece
> a esa segunda etapa.

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
| 1 | `% r_pv_manual_base.pgm` | **Programa** — nombre del ARCHIVO, en minúsculas, extensión `.pgm` | **DERIVADO** — el fixture `dsdmt_25` lo prueba con los tres nombres separados: archivo `r_pv_manual_base_dsdmt_25`, miembro del ZIP `R_PV_manual_base_`, pieza `R_PV_manual_base`; el ISO emitió el del **archivo** |
| 2 | `;H DX=400.000 DY=400.000 DZ=18.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 ` | ver desglose abajo — **ojo: `DX/DY/DZ` son dimensión + origen**, ver B1b | mixto |
| 3 | `?%ETK[500]=100` | **Máquina** — `NCI.CFG`, `$GEN_INIT` | **DERIVADO** (B1f: copia literal) |
| 4 | *(vacía)* | **Máquina** — la línea que el `.CFG` tiene comentada entera | **DERIVADO** (B1f) |
| 5 | `_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )` | **Máquina** — `$GEN_INIT`; parámetro 21 del eje 0 | **DERIVADO** (literal + referencia a `%ax`) |
| 6 | *(vacía)* | **Máquina** — el `;` suelto del `.CFG` | **DERIVADO** (B1f) |
| 7 | `G0 G53 Z %ax[2].pa[22]/1000` | **Máquina** — `$GEN_INIT`; parámetro 22 del eje 2, en coordenadas de máquina (`G53`) | **DERIVADO** |
| 8 | `M58 ` | **Máquina** — `$GEN_INIT`; **habilita el bloqueo de la pieza** (`;abilita controllo vuoto`). El espacio final es el que separaba el comentario | **DERIVADO** (B1f), y confirmado por el fabricante: «M58: LLAMADA VACÍO GENERAL» (B1i) |
| 9 | `G71 ` | **Aplicación** — G71 es «medidas en mm» | HIPÓTESIS **debilitada** (B1g: no existe `G70` en ningún emisor); la decide el fixture `IsMM`=Pulgadas |
| 10 | `MLV=0 ` | **Emisor** (`PlPathFilter32.dll`) — selecciona el **nivel de transformación de coordenadas** al que se escribe; el nivel 0 es el que lleva el `%Or` | origen DERIVADO (B1g); el significado, **HIPÓTESIS fundada** (B1i) |
| 11 | `%Or[0].ofX=-400000.000 ` | **Máquina** (campo del área) **+ Programa** (`DX`, sólo si el campo vale 0) — µm | **DERIVADO** (fórmula en B1c, 11/11) |
| 12 | `%Or[0].ofY=-1515599.976 ` | ídem sobre el eje Y — µm | **DERIVADO** (misma fórmula) |
| 13 | `%Or[0].ofZ=18000.000 ` | **Programa** — µm; `= DZ` (o sea `depth + origin_z`) | DERIVADO (ver B1b) |
| 14–15 | `?%EDK[0].0=0 ` · `?%EDK[1].0=0 ` | **Emisor** (`PostISO.dll`) — plantilla de **índice fijo**, distinta de la de la línea 30. `EDK` = **bit de intercambio del CNC al PLC**; el `.0` es el bit. Banda `EDK 0–5` | origen DERIVADO (B1g); la familia y la banda, **DERIVADAS** del manual de SCM (B1i); qué gobierna cada bit, DESCONOCIDO |
| 16 | `MLV=1 ` | **Emisor** (`PlPathFilter32.dll`) | ídem línea 10 |
| 17 | `SHF[X]=-400.000 ` | ídem 11, en mm | **DERIVADO** (B1c) |
| 18 | `SHF[Y]=-1515.600 ` | ídem 12, en mm | **DERIVADO** (B1c) |
| 19 | `SHF[Z]=18.000+%ETK[114]/1000 ` | **Programa** (`DZ`) **+ Máquina** (corrección en runtime) | DERIVADO sobre `DZ` |
| 20 | `?%ETK[8]=1 ` | **Emisor** — `ETK 6–12` es la banda del **cambio de herramienta y la animación gráfica** | banda **DERIVADA** del manual de SCM (B1i). ⚠️ **El valor NO es constante**: en los ISO con mecanizado alterna 1 y 2, y la plantilla del láser lo pone en 0. Acá vale 1 sólo porque no hay operaciones |
| 21 | `G40 ` | cancelación de compensación — constante del protocolo | DERIVADO por contexto |
| 22 | `SYN` | **Emisor** — barrera de sincronización: el CNC calcula bloques por delante de la ejecución, y `SYN` obliga a esperar a que el anterior se haya ejecutado de verdad. En los ISO de SCM precede a cada `M06` y al bloque de reset | HIPÓTESIS **con mecanismo** (B1i); el origen (no es `NCI.CFG`) es **DERIVADO** |
| 23–29 | `?%ETK[0]=0` `[1]` `[2]` `[13]` `[17]` `[18]` `[19]` | **Máquina** — `NCI.CFG`, `$GEN_END`, copia literal | **DERIVADO** (B1f): son esos siete **porque están escritos ahí** |
| 30 | `?%EDK[13].0=1 ` | **Programa** (el área) — el índice depende de la MITAD de mesa: 10 izquierda, 13 derecha | **DERIVADO** (B1c) |
| 31–34 | `MLV=1 ` + `SHF[X]=0 ` `SHF[Y]=0 ` `SHF[Z]=0 ` | **Emisor** (`PlPathFilter32.dll`) — teardown: anula el SHF del nivel 1 | **DERIVADO** (B1g: el bloque está literal, con su par de apertura) |
| 35–38 | `MLV=2 ` + `SHF` en cero | ídem nivel 2 — aparece aunque el nivel 2 nunca se usó **porque la plantilla se emite entera** | **DERIVADO** (B1g) |
| 39 | `MLV=0 ` | vuelve al nivel 0 | DERIVADO por contexto |
| 40–41 | `VL6=0 ` · `VL7=0 ` | **Emisor** (`PlPathFilter32.dll`), en el bloque de **mesa** (travesaños y ventosas). Son los registros donde el emisor deja la **longitud** y el **radio** de la herramienta activa; acá en cero porque el programa no usó ninguna | origen DERIVADO (B1g); el contenido, **DERIVADO** contra el catálogo (B1i) |
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
| `BX` `BY` `BZ` | 0.000 / 0.000 / 0.000 | **Programa** — **traslación de la pieza respecto al TOPE**, por eje | **DERIVADO por doc** (Apéndice B de Xilog, ver abajo); falta el fixture que lo mueva |
| `-HG` | | **Programa** — `executionFields`, el «Área» de Parámetros de máquina | **DERIVADO** (doc SCM) |
| `V=0` | | **Programa** — `tableOptions`, el «Bloqueo» de Parámetros de máquina | **DERIVADO** (doc SCM) |
| `T=0` | | **Programa** — `mechanicalOptions`, las «Opciones mecánicas» | **DERIVADO** (doc SCM) |
| `C=0` | | **Programa** — `continuousCycle` | **DERIVADO** (doc SCM) |
| `*MM` | | **Aplicación** — unidad de medida (`IsMM`) | HIPÓTESIS |

> ⚠️ **Corrección.** La primera versión de esta tabla atribuía `T=0` a
> `IsTechnologicalMirror` por parecido de inicial. Es **`mechanicalOptions`**. El
> espejo tecnológico **no** está en el header, o está en otro lado. Caso de manual de
> la regla 2: la definición ya estaba escrita y contradecía lo que uno supondría.

### El header, completo, según el manual de Xilog

El **Apéndice B** del manual (`pgmx/docs/xilog_plus_pgm/09_13_reglas_estacionamiento.md`,
que contiene los apéndices) define las **variables predefinidas** del lenguaje y el
operador `HEADER(n)`, que devuelve cada campo del encabezamiento por índice:

| `HEADER(n)` | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Campo | `DX` | `DY` | `DZ` | `-` | `C` | `T` | `R` | `*` | `V` | reservado | `BX` | `BY` | `BZ` |

⇒ **El juego de letras del header está cerrado**: son doce campos más un reservado, y el
esqueleto emite todos salvo `R`. Y las tres variables de posición quedan definidas:

> `DX` Dimensión en X · `DY` Dimensión en Y · `DZ` Dimensión en Z
> `BX` *Traslazione in X del pezzo rispetto alla battuta* (ídem `BY`, `BZ`)

⇒ **`BX/BY/BZ` es la traslación de la pieza respecto al TOPE**, no el origen — coherente
con que R001 los haya dejado en cero al mover el origen. Sale de DESCONOCIDO. El fixture
que lo confirma es uno con `WorkpieceOffset` ≠ 0, que el sintetizador todavía no varía.

✅ **`R` (repeticiones) no aparece en este header, y ya se sabe por qué** (2026-08-12): el
XXL que produce Maestro **sí lo escribe** —`R=1`— y el ISO no lo lleva. La omisión ocurre
en el paso XXL → ISO, no en Maestro. Lo mismo con `/"def"`, el nombre del equipamiento, que
está en el XXL y no en el ISO. Ver `emisor_iso.md`.

> Y el **orden de los campos cambia** entre los dos: el XXL escribe
> `DX DY DZ -HG C T R *MM /"def" BX BY BZ V` y el ISO,
> `DX DY DZ BX BY BZ -HG V *MM C T`. El header del ISO no es el del programa reordenado por
> casualidad: lo reescribe la segunda etapa.

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

### ⛔ REFUTADA la condición del cero (lote D1 Grupo 0, 2026-08-27)

La fórmula de arriba es correcta en su forma; **su condición no**. Los ocho campos sueltos y
doce pares, con `.iso` de los veinte, dan esto:

| campo | `fields.cfg` X | `SHF[X]` | ¿resta DX? |
|---|---|---|---|
| A | −3685.85 | −3685.850 | no |
| **B** | **−1843.00** | **−2243.000** | **SÍ** ⇐ y X **no** vale cero |
| C | −1843.00 | −1843.000 | no |
| D | 0.00 | −400.000 | sí |
| E | −3688.00 | −3688.000 | no |
| **F** | **−1843.00** | **−2243.000** | **SÍ** |
| G | −1843.00 | −1843.000 | no |
| H | 0.00 | −400.000 | sí |

**`B` y `F` son exactamente las dos letras que R002 nunca probó.** En los seis campos que sí
tenía (A, C, D, E, G, H) «restar» y «valer cero» coincidían punto por punto, y la regla se
ajustó a la variable equivocada. Vale como caso de la regla 1 del `CLAUDE.md`: la condición
aguantó 17 días porque no había fixture que la separara.

⭐⭐ **Y el remate: `B` y `C` tienen registros BYTE-IDÉNTICOS en `fields.cfg`** —los 29 valores
iguales, X = −1843.00 los dos— **y producen orígenes distintos** (−2243.000 contra −1843.000).
⇒ **La regla no puede salir de `fields.cfg`.** No hay nada en el archivo que separe a B de C.

### ✅ Lo que sí predice los 20 casos: la posición de la letra en su par

```
SHF[eje] = campo(1ª letra del área, eje) − D_eje   SÓLO SI la letra es la SEGUNDA de su par
```

Los pares canónicos son **(A,B) (C,D) (E,F) (G,H)** —y siguen con (I,J), (K,L)…—, o sea las
letras tomadas de a dos desde la `A`. **La primera de cada par no resta; la segunda sí.**

Verificado en los veinte, incluidos los pares cruzados: `AD` → primera letra `A` → −3685.850 ·
`DA` → `D` → −400.000 · `EH` → `E` → −3688.000 · `HE` → `H` → −400.000.

Leído en castellano, es la misma imagen que ya estaba escrita —la coordenada marca el tope
contra el que apoya la pieza— pero con el tope correcto: **cada mitad de mesa tiene DOS topes,
y la letra dice cuál**. Contra el primero la esquina de la pieza *es* el tope; contra el
segundo la pieza cuelga hacia el negativo y la esquina queda en `tope − D`.

⚠️ **Pendiente para el converter**: el dato «primera o segunda del par» **no está en ninguna
config que tengamos**. Se puede calcular de la letra (posición par o impar en el alfabeto),
pero el *por qué* físico no está derivado, y la regla 4 del `CLAUDE.md` pide que nada de la
traza salga de una constante interna. Decidir si se declara en `emisor_iso.cfg` (el cuarto
origen) o si hay un archivo de máquina que todavía no miramos.

### ⚠️ El eje Y tiene la misma ambigüedad, y NO es resoluble en esta máquina

En Y, los cuatro campos de la fila delantera (A–D) valen `0.00` y **restan** `DY`; los cuatro
de la trasera (E–H) valen ≈ −1515 y **no** restan. Encaja con la condición del cero — pero
también con «la fila delantera resta». **Las dos lecturas están confundidas por construcción**:
la fila delantera *se define* por `Y = 0`. Con dos filas no hay fixture que las separe.

### ✅ La normalización la hace la ETAPA 2, y empareja de a dos

El `.pgmx` guarda la letra sola (`<a:ExecutionFields>A`) y el ISO emite el par (`-AB`). ⇒ **la
completa el generador de Xilog, no Maestro** — coherente con el modelo de dos etapas.

| pedido | emitido | | pedido | emitido |
|---|---|---|---|---|
| A | `-AB` | | E | `-EF` |
| B | `-BA` | | F | `-FE` |
| C | `-CD` | | G | `-GH` |
| D | `-DC` | | H | `-HG` |

**La letra pedida va siempre primero**, y la acompaña su par. Vale incluso para los campos que
no existen: `I` se normaliza a `IJ` y `J` a `JI` antes de que el postproceso los rechace.

### ✅ Los campos I–P no existen, y el rechazo distingue dos cosas

`fields.cfg` los tiene con el habilitado en `0`, y el postproceso los rechaza con **dos
mensajes distintos**, los dos con código `[23,6]` y los dos de **`Winxiso`** (la etapa 2):

| pedido | mensaje |
|---|---|
| `I` · `J` · `K` · `L` y sus pares | `Bag.  IJ: Área de trabajo no configurada` — **nombra el área**: la parseó y la normalizó, y falló el chequeo de habilitado |
| `00` · `01` · `10` · `11` | `Bag.Fields: Área de trabajo no configurada` — **no nombra ninguna**: nunca la parseó |

⇒ Confirma para qué sirve el flag de habilitado del registro, y que **el campo del área es de
LETRAS**: la codificación numérica `FLD` del manual (`1=A`, `12=AB`) es del operador de macros,
no algo que se pueda tipear acá.

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

> ✅ **CONFIRMADO con los ocho campos (2026-08-27).** El lote D1 Grupo 0 completa la tabla sin
> corregirla: `EDK[10]` para **A, B, E, F** y `EDK[13]` para **C, D, G, H**, en los veinte ISO.
> Y los pares cruzados agregan un dato: `AD` → **10** y `DA` → **13**, o sea que **lo decide la
> PRIMERA letra**, no el par — igual que el origen.

### La tabla de campos de esta máquina

De `fields.cfg`, ya parseado bien: bloques de 29 valores en columnas de 13 caracteres,
cada uno **cerrado** por una línea separadora rellena de `0x03` que lleva la letra. (El
primer bloque no trae letra: no es un campo.) Los valores 15 y 16 del bloque son X e Y;
el 18 y 19, ancho y alto.

> **El manual confirma qué hay en cada posición** (Apéndice B, operador `FIELD(a,n)`):
> `FIELD(a,5)` = origen X del campo · `FIELD(a,6)` = origen Y · `FIELD(a,7)` = origen Z ·
> `FIELD(a,8)` = dimensión X · `FIELD(a,9)` = dimensión Y. El orden coincide con el que
> se había leído posicionalmente, y **agrega un origen Z por campo** que todavía no
> miramos. El mismo apéndice define `FLD`, la codificación numérica del área: `1=A`…
> `12=AB`, `21=BA`, `101=E`… `112=EF` — o sea que **el par ordenado también es un
> número**, y el orden de las letras está codificado ahí (`AB`=12 contra `BA`=21).

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

## B1d · El esqueleto no es fijo: la aplicación le puede AGREGAR líneas (2026-08-10)

Del barrido de la ventana Opciones (`opciones_de_aplicacion.md`) salió algo que cambia
cómo hay que leer todo lo anterior.

Con **«Estacionamiento automático finalizada la ejecución»** marcado, el ISO del mismo
programa vacío pasa de **44 a 46 líneas**. Se insertan dos **entre el `G40` (21) y el
`SYN` (22)**:

```
G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000
_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )
```

⇒ **El esqueleto de 43 líneas no es «el esqueleto»: es el esqueleto con esta
configuración de aplicación.** Un programa idéntico, en una máquina con esa opción
marcada, emite 45. El converter no puede tratar el preámbulo y el cierre como plantilla
fija.

Detalles que importan para el byte:

- La segunda línea es **la misma instrucción que la línea 5** del preámbulo, pero **con
  dos espacios finales** (la del preámbulo no tiene ninguno).
- La primera usa la notación **sin corchetes** (`%ax0.pa21`), que no aparecía en el
  esqueleto. Las dos formas conviven en un mismo archivo.
- **El modo de paro no llega**: los tres valores de `FinalParkStopType` dan ISOs
  idénticos entre sí.
- Es **el mismo lugar** donde el `Xn` inserta su bloque de ocho líneas (B1b). Ese punto
  del archivo —entre el `G40` y el `SYN`— es donde van las operaciones de máquina.

## B1e · Las fases vacías no dejan rastro (2026-08-10)

Fixtures de Fermín con **dos y tres fases** (`Fase1`, `Fase2`, `Fase3`), postprocesados
con y sin `IsParkOnWorkplanChange`. Los `.pgmx` traen las fases de verdad —2 y 3
`MainWorkplan` con su `Setup`, contra 1 del base— y los **cuatro ISO salen idénticos al
base**: 44 líneas, sin una diferencia.

⇒ **El ISO no lleva marca de fase por el solo hecho de que la fase exista.** Un programa
con tres fases sin operaciones emite lo mismo que uno con una.

Queda abierto qué pasa con fases **que tengan contenido**: ahí es donde puede aparecer una
separación entre fases, y donde el «estacionamiento en cada cambio de fase» tendría un
cambio real donde manifestarse. Se cierra con un programa de dos fases con un mecanizado
en cada una.

## B1f · El preámbulo y el cierre están ESCRITOS en `NCI.CFG` (2026-08-12)

**Trece de las cuarenta y tres líneas del esqueleto no las inventa el emisor: las copia
de un archivo de configuración de la máquina que ya está en nuestro snapshot.**

`iso/data/machine_config/snapshot/xilog_plus/Cfg/NCI.CFG` tiene dos bloques que aparecen
**literales y en orden** en el ISO:

| Bloque del `.CFG` | Líneas del ISO | Qué es |
|---|---|---|
| `$GEN_INIT` | **3–8** | el preámbulo entero |
| `$GEN_END` | **23–29** | el reset de los siete registros |

Verificable en cualquier momento, contra cualquier ISO:

```
py -m iso.machining_lab.verificar_nci
```

y fijado como regresión offline en `tests/test_iso_nci_skeleton.py`.

### La regla de emisión: una sola, dos pasos

Lo que separa el `.CFG` del ISO son dos transformaciones, y con eso alcanza para los seis
casos del `$GEN_INIT`:

1. **se corta la línea en el primer `;`** — el comentario no se emite, pero lo que quedó
   antes sí, **con sus espacios**;
2. **`%%` se desdobla a `%`**.

| En `NCI.CFG` | En el ISO |
|---|---|
| `?%%ETK[500]=100` | `?%ETK[500]=100` |
| `;?%%ETK[500]=%%ax[0].pa[22]/1000 ;solo per zone` | *(línea vacía)* |
| `_paras( 0x00, X, 3, %%ax[0].pa[21]/1000, %%ETK[500] )` | `_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )` |
| `;` | *(línea vacía)* |
| `G0 G53 Z %%ax[2].pa[22]/1000` | `G0 G53 Z %ax[2].pa[22]/1000` |
| `M58 ;abilita controllo vuoto` | `M58 ` |

Dos cosas que esto explica y que estaban sin explicación:

- **Las líneas 4 y 6 del ISO están vacías** porque en el `.CFG` son comentarios enteros.
  Una línea comentada **no desaparece: deja su lugar.**
- **El espacio final de `M58 `** es el que separaba el comentario en el `.CFG`. No es
  adorno del emisor ni un capricho: viene del archivo, carácter por carácter. Para el
  byte-idéntico esto importa más que la instrucción misma.

### Qué queda respondido

- **`M58` es la habilitación del bloqueo de la pieza** — el comentario italiano dice
  `abilita controllo vuoto` («habilita el control de vacío») y el Apéndice I del manual de
  Xilog lo confirma: `M28`/`M38`/`M39`/`M58` son las peticiones de bloqueo, y la selección
  del tipo va **antes** de ellas.
- **Por qué el reset toca justo `ETK[0,1,2,13,17,18,19]`**: porque esos siete están
  escritos en `$GEN_END`. No es un conjunto canónico del lenguaje — es **configuración**.
- **`$GEN_END` no es el final del archivo**: quedan catorce líneas después (30–43). El
  emisor **inserta** el bloque configurable en un punto intermedio de su propio cierre.

### El corolario, que es el que pega fuerte

`NCI_ORI.CFG` —la versión de fábrica del mismo archivo, también en el snapshot— tiene
**otro preámbulo y otro cierre**:

| | `NCI.CFG` (instalado) | `NCI_ORI.CFG` (fábrica) |
|---|---|---|
| `$GEN_INIT` | seis líneas (`ETK[500]`, `_paras`, `G0 G53 Z`, `M58`) | **`M150`**, una línea |
| `$GEN_END` | los siete `ETK` | los siete `ETK` **+ `SYN JSR 8900`** |

⇒ **El preámbulo del ISO es configuración de la instalación, no protocolo.** Otra máquina
—u otra revisión de la misma— emite otro preámbulo, y el converter que lo lleve escrito
adentro produce un archivo que no es de esa máquina.

Esto es **B1d por un segundo camino**. Ahí el esqueleto cambiaba por la ventana Opciones
(configuración de la aplicación); acá cambia por `NCI.CFG` (configuración de la máquina).
Dos de los tres orígenes pueden reescribirlo. **La regla 4 en su forma más concreta: estas
trece líneas salen del snapshot, nunca de una constante del converter.**

De yapa, la primera línea del archivo: `$GEN_ISO_FOR_EXTERNAL_APP` vale **1** — la clave
que habilita a una aplicación externa (Maestro) a generar el ISO con este generador.

### Lo que quedó a la vista, y sigue abierto

Las líneas que **no** salen de `NCI.CFG` las pone el emisor, y el verificador ahora las
lista de una: la cabecera (1–2), el bloque de origen (9–21), el `SYN` (22) y el teardown
(30–43).

Sobre `?%EDK[n].0` hay un dato nuevo del relevamiento: las cadenas `?%%EDK[%d].0=1` y
`?%%EDK[%d].0=0` son **literales de `PostISO.dll`**, el generador ISO de Xilog Plus, con el
índice parametrizado. ⇒ El origen de esas líneas es el **emisor**, no un `.cfg`; el valor
del índice ya estaba derivado (la mitad de mesa, B1c). En la misma tabla de cadenas del
binario, y contiguas, están `M58/M28/M38/M39/M59` con sus `E30xxx` — lo que sugiere que
`EDK[n].0` es la habilitación de bloqueo **por zona**. Es contigüidad en una tabla de
strings: **HIPÓTESIS**, no prueba.

## B1g · Qué binario escribe cada línea que no sale de `NCI.CFG` (2026-08-12)

Barrido de las plantillas `printf` de los **7.683 archivos** de las dos instalaciones
(`Xilog Plus` y `Maestro`), en ASCII y en UTF-16. Las cadenas vecinas en la tabla de un
binario son casi siempre las del mismo bloque de emisión: por eso se mira el contexto.

> ⚠️ **Esto es otra dimensión, no un cuarto origen.** «Qué binario la escribe» no reemplaza
> a «de dónde sale el valor». Una línea emitida por el generador con valor fijo es una
> constante **del emisor** — y `NCI.CFG` acaba de mostrar que lo que parece fijo puede ser
> configuración. Sirve para saber **dónde mirar**, no para dar nada por cerrado.

| Líneas del ISO | Binario | Plantilla encontrada |
|---|---|---|
| 14–15 `?%EDK[0].0=0` `?%EDK[1].0=0` | `PostISO.dll` | `?%%EDK[1].0=%d` · `?%%EDK[0].0=%d` — **índice FIJO**, valor variable |
| 19 (el `%ETK[114]`) | `PostISO.dll` | `%%ETK[114]`, junto a la plantilla `G161 … Z((…)+(%%ETK[114]/1000))` |
| 22 `SYN` | `PostISO.dll` | contigua a `G64`, `G40` y `?%%EDK[%d].0=1` |
| 30 · 42 `?%EDK[13].0=1/0` | `PostISO.dll` | `?%%EDK[%d].0=1` · `=0` — **índice VARIABLE**, valor fijo |
| 9 `G71` | `PostISO.dll`, `nci32.dll`, `VtGenIso.dll` | en la tabla de códigos G, junto a `G80`, `G162`, `G4 F%.1f` |
| 10 · 16 · 31–39 `MLV=n` + `SHF[*]` | `PlPathFilter32.dll`, `VtGenIso.dll` | `MLV=0/1/2`, `SHF[X]=%.3f` |
| 40–41 `VL6=0` `VL7=0` | `PlPathFilter32.dll` | literales, dentro del bloque de teardown |

### Dos plantillas distintas para el mismo registro `EDK`

Es un detalle fino y separa dos filas que estaban juntas como «?»:

- `?%%EDK[0].0=%d` y `?%%EDK[1].0=%d` — **el índice está fijo en la plantilla** (0 y 1) y lo
  que varía es el valor. Son las líneas 14–15.
- `?%%EDK[%d].0=1` y `?%%EDK[%d].0=0` — **el índice es el parámetro** y el valor está fijo.
  Son las líneas 30 y 42, donde el índice es la mitad de mesa (10 ó 13, ver B1c).

⇒ `EDK[0]`/`EDK[1]` **no son «el área con otro índice»**: los escribe otra plantilla, con
otra forma. Qué son sigue siendo DESCONOCIDO, pero ya no se confunden con la línea 30.

### El teardown es del subsistema de MESA

El bloque completo de las líneas 30–42 está en `PlPathFilter32.dll`, **contiguo y con su
par de apertura**, y las cadenas que lo rodean dicen de qué se trata:

```
;Barre di appoggio · ;Quote di parcheggio · ;Limiti area di lavoro
;Posizionamento Ventosa %d della Traversa %d
;Cancellazione Ventosa %d della Traversa %d · ;Trascinamento Ventose della Traversa %d
?%%EDK[%d].0=0 · VL6=0 · VL7=0 · MLV=2 · SHF[X]=0 · SHF[Y]=0 · SHF[Z]=0
MLV=1 · SHF[X]=0 · SHF[Y]=0 · SHF[Z]=0 · ?%%EDK[%d].0=1
```

⇒ El teardown pertenece al módulo de la **mesa de trabajo** (travesaños y ventosas), no al
programa de la pieza. Eso **responde una de las preguntas abiertas**: el `MLV=2` que
aparece «aunque el nivel 2 nunca se usó» viene de ahí — el par de niveles es de esa
plantilla, que se emite entera.

### Lo que el barrido descartó, que también es resultado

- **`%Or[0].of*` no existe como plantilla literal en ningún archivo de las dos
  instalaciones.** Aparece únicamente en los ISO de salida ⇒ la línea se **compone en
  runtime** por concatenación. No hay dónde seguir buscándola; el valor ya está derivado
  por fixtures (B1c), que es lo que importa.
- **No existe `G70` en ningún emisor**, sólo `G71`. Eso **debilita la hipótesis** de que la
  línea 9 sea la unidad de medida (`IsMM`): si el ISO pudiera declarar pulgadas, tendría
  que existir el código contrario. Lo decide un fixture barato —`IsMM` = Pulgadas— que ya
  está en la lista de prioridad 3 del barrido.
- `?%%ETK[8]=%ld` aparece **una sola vez**, en `VtGenIso.dll`, dentro del bloque del **láser
  de cruce** (rodeada de `;Motore=%d,Strobe=%u` y `;Angolo=%.3f`). Nuestra línea 20 no lleva
  comentario y esta máquina no tiene ese dispositivo: **no alcanza para atribuirla.** Sigue
  DESCONOCIDA.

## B1h · Qué consulta el emisor, y qué no encuentra (2026-08-12)

Pregunta de Fermín, en el momento justo: *si estos DLL acceden a algún otro archivo, podrían
estar transcribiendo de una fuente que todavía no miramos.* La respuesta corta es que no hay
ninguna fuente escondida. La larga es más interesante.

### Los archivos que los DLL nombran

| Archivo | ¿Existe en la instalación? | ¿En el snapshot? |
|---|---|---|
| `axis.cfg` · `params.cfg` (`nci32.dll`, `PlPathFilter32.dll`) | sí | **sí** ✅ |
| `PviBeR.msg` (`PlPathFilter32.dll`) | sí | **falta** — es de mensajes |
| `PostISO.cfg` · `Script.cfg` (`PostISO.dll`) | **no existe** | — |
| `Motorplid.cfg` (`PlPathFilter32.dll`) | **no existe** | — |

Los tres que no existen hay que buscarlos **en la PC del CNC**: si allá están y acá no, son
fuente y no los estamos mirando. `PostISO.dll` construye su ruta como `..\CFG\` + nombre.

### Treinta claves de configuración que el emisor busca y NADIE define

Esto es lo que apareció de fondo. Los binarios consultan claves `$…` —el mismo mecanismo de
`$GEN_INIT` y `$GEN_END`— que **ningún archivo de la instalación define**. Verificado: sólo
existen dentro de los propios DLL.

| Familia | Cuántas | Qué gobiernan |
|---|---|---|
| `$MA_*` (`MA_XY_Z`, `MA_SET_POSITION`, `MA_UP3`, `MA_DOWN5`, `MA_FEEDRATE_XY`, `MA_RESTORE_END`…) | 16 | los movimientos de la **mesa** — el mismo módulo que emite nuestro teardown |
| `$PM_*` (`PM_INIT_FILE_MAC_%d`, `PM_END_BLK_MAC_%d`, `PM_END_CYC_MAC_%d`…) | 9 | macros de inicio y fin de archivo, bloque, ciclo y secuencia |
| `$KEY_G%d` · `$KEY_M%d` (`$KEY_G80`, `$KEY_G100`, `$KEY_M59`) | por código | **la traducción de cada código G y M** |

Y el emisor tiene su propio fail-loud: junto a `$KEY_G%d` está la plantilla
`;G%d: CORRISPONDENZA NON TROVATA!` — cuando no encuentra la clave de un código, **escribe un
comentario en el ISO diciéndolo**. Si esa línea aparece alguna vez en un ISO de referencia,
ya sabemos qué significa.

⇒ **Son puntos de extensión vacíos.** El esqueleto es fijo **porque nuestra configuración no
define esas claves**, no porque el emisor no pueda emitir otra cosa. Definir `$MA_XY_Z` en el
`.CFG` de otra máquina cambiaría líneas que hoy leemos como constantes.

### El reencuadre de la pregunta abierta

Esto **achica el «cuarto origen» en vez de agrandarlo**, y conviene decirlo con precisión:
casi todo lo que parecía constante del binario es en realidad **el valor por defecto de una
clave de configuración que nadie escribió**. No es «el emisor decide», es «la configuración
está vacía y el emisor tiene un default». Sigue siendo el binario el que lo aporta —la
pregunta de los tres o cuatro orígenes no se cierra sola—, pero el mecanismo es el mismo que
`NCI.CFG`, no uno nuevo.

### El generador está configurado igual en las dos PCs

`Nci.ini` —diez claves que gobiernan al generador: `[PLANE] enable=1`, `[DISC] enable=0`,
`[MACHINEFAMILY] version=2`, `[G0WITHSPINDLES] enable=0`, `[TESTMODE] enable=1`— y `NCI.CFG`
son **byte-idénticos entre la PC del CNC y la de oficina técnica**.

Vale para el experimento de las dos PCs: lo que difiere entre las máquinas es la
configuración de la **aplicación** (`UI00.exe.Config`), no la del **generador**. Refuerza la
expectativa de que el paso 0 dé un ISO idéntico.

`Nci.ini` ya estaba en el snapshot y no lo habíamos mirado nunca. `[DISC] enable=0` merece un
segundo vistazo cuando llegue el canal con sierra.

## B1i · El control es **ESA-GV**, y con eso `EDK`/`ETK` tienen diccionario (2026-08-14)

**Fuente**: *Nueva Guía de Diagnóstico para Fresadoras con Control Numérico + Lista códigos
M*, **SCM Group S.p.A.**, código **`9031191610B`**, versión 4.2 (2004), 395 páginas, en
castellano. Capítulos 7, 23, 32 y 12.

> ⚠️ El documento lleva impresa la reserva de propiedad de SCM y la prohibición de
> divulgarlo. **No se copia al repo, ni el PDF ni su texto.** Acá van los hechos sobre
> NUESTRA máquina, citando capítulo y código, como cualquier referencia externa.

### La cadena que identifica el control

1. El manual (cap. 7): *«Para las variables E.., relativas a los CNC **ESA-GV**, se
   transformarán en **ETK**..»*, y el capítulo 32 se titula «Parámetros ETK.. para máquinas
   con CNC ESA-GV».
2. Nuestro ISO usa `ETK` y `EDK`, no `E30000`.
3. El manual agrupa explícitamente `RD110s-TV-**Pratix**` (cap. 1) y documenta `ETK103` como
   parámetro «en RD110 (**CNC ESA-GV**)», cuyo equivalente NUM es `E30012` (cap. 14).

⇒ **La Pratix tiene CNC ESA-GV.** De los cuatro dialectos que declara `PostISO.dll`
(`ISO-OSAI(2)`, `ISO-ESAGV(2)`, `ISO-NUM`, `ISO-ORCHESTRA`, ver `emisor_iso.md`), **el
nuestro es `ISO-ESAGV(2)`**. Esto no es una hipótesis de estilo: cambia qué manual aplica a
cada línea del esqueleto.

### `EDK` — bit de intercambio del CNC al PLC

Capítulo 32, textual, con sus bandas — y familias hermanas del mismo rol (`EOK`, `EVK`,
`EQK`, `ESK`):

```
EDK 0 - EDK 5      EDK 10 - EDK 13      EDK 20 - EDK 21
```

| Nuestro | Banda | Lo que ya habíamos derivado por fixtures |
|---|---|---|
| `?%EDK[0].0` · `?%EDK[1].0` | 0–5 | — |
| `?%EDK[13].0` | 10–13 | B1c: **10 = mitad izquierda · 13 = mitad derecha** |

La banda 10–13 es exactamente el juego de mitades de mesa que R002 dedujo sin conocer el
manual. Y el `.0` deja de ser un misterio: **`EDK` es un registro de bits**, y `.0` es el bit.

### `ETK` — bandas por función

| Banda | Función (manual, cap. 32) | Los nuestros |
|---|---|---|
| `ETK 0–5` | mandos de salida ejes / mandriles de la taladradora | `ETK[0] [1] [2]` — el reset del `$GEN_END` |
| **`ETK 6–12`** | **cambio de herramienta y animación gráfica** | **`ETK[7]` · `ETK[8]`** |
| `ETK 13–101` | configuración de motorizaciones de ejes, mandriles y electromandriles | `ETK[13] [17] [18] [19]` |
| `ETK 16` | gestión Up-Down grupo hoja | — |
| `ETK 31–32` | tipo de bloqueo (bornes / vacío) | — |
| `ETK 102` · `ETK 103` | cabezales bajos · cambio de herramienta neumático RD110 | — |
| **> 103** | **no documentado** (ver abajo) | `ETK[114]` · `[500]` · `[903]` · `[904]` |

⭐ **`?%ETK[8]` es de la banda del cambio de herramienta.** Eso explica lo observado: alterna
1 y 2 dentro de un mismo programa con mecanizado, y la plantilla del láser de cruce lo pone
en 0. En el esqueleto vale 1 **porque no hay operaciones**, no porque sea constante.

### Por qué los índices altos no van a aparecer en ningún manual

El capítulo 33 —«Parámetros ETK.. para operaciones especiales (CNC ESA-GV)»— **está en blanco
a propósito**: *«Capítulo en blanco… Deberá rellenarse vez por vez al definir el tipo de
operación especial. Fecha ___ referencia nº de serie ___ Modelo máquina ___»*.

⇒ Los índices altos son **por máquina**, los completa el técnico en la puesta en marcha. El
documento que falta no es un manual genérico: es **el capítulo 33 rellenado para el número de
serie de nuestra Pratix**, y lo tiene el servicio técnico de SCM.

Lo poco que hay de esos índices sale de comentarios del propio fabricante, no del manual:

| Registro | Comentario | Dónde |
|---|---|---|
| `?%ETK[903]=%d` | `;traverse` (travesaños) | `PlPathFilter32.dll` |
| `?%ETK[904]=%d` | `;utensile` (herramienta) | `PlPathFilter32.dll` |
| `?%ETK[500]=%ax[0].pa[22]/1000` | `;solo per zone` | `NCI.CFG`, línea comentada |

### `VL6` / `VL7` — la longitud y el radio de la herramienta

En los ISO **con** mecanizado, `VL6` y `VL7` copian a las instrucciones `SVL` y `SVR`, que se
cargan con `D1` (corrector activo) y se anulan con `D0`:

```
T1 · S18000M3 · D1 · SVL 125.400 · VL6=125.400 · SVR 9.180 · VL7=9.180
      …
D0 · SVL 0.000 · VL6=0.000 · SVR 0.000 · VL7=0.000
```

Cruzados contra `pgmx/data/tool_catalog.csv` sobre ~2.000 ISO del taller, **`SVL` y `SVR` se
emiten siempre en pareja y coinciden al centésimo con el catálogo**:

| `SVR` | `SVL` | Catálogo | Herramienta |
|---|---|---|---|
| 9.180 | 125.400 | r 9.18 · L 125.4 | E001 Widea 18 mm |
| 2.000 | 107.200 | r 2.0 · L 107.2 | E004 Fresa 4 mm |
| 4.760 | 111.500 | r 4.76 · L 111.5 | E003 Fresa Violeta |
| 40.000 | 120.870 | r 40.0 · L 120.87 | E006 Rectificado |
| 38.000 | 145.900 | r 38.0 · L 145.9 | E005 Fresa 45º |
| 8.860 | 152.100 | r 8.86 · L 152.1 | E007 Recta 50mm |
| 50.000 | 107.000 | r 50.0 · L 107 | E002 Sierra Horizontal |
| **1.900** | 60.000 | r **60.0** · L 60 | 082 Sierra Vertical X ⚠️ |

⇒ `SVL` = `tool_offset_length` · `SVR` = `diameter / 2`. **DERIVADO**, y con consecuencia
directa: cuando la rama D emita mecanizados, estas dos líneas **salen del catálogo**, no de
una constante (regla 4).

⚠️ **La excepción, sin resolver**: la Sierra Vertical X recibe `SVR 1.900` cuando el radio de
su disco es 60. El 1,9 es la mitad de los 3,8 mm de corte de una sierra que el catálogo llama
«4 mm». La Sierra **Horizontal**, en cambio, sí recibe el radio del disco (50). Las dos
sierras se tratan distinto y **no sabemos por qué**: lo resuelve la rama D (canal).

> **Ojo con el nombre.** `SVL`/`SVR` se leen como *sovrametallo* (sobrematerial) en italiano,
> y esa es una lectura razonable de la instrucción. Pero los **valores** que SCM escribe ahí
> son la longitud y el radio de la herramienta. Si alguna vez modelamos este campo, se llama
> por lo que lleva, no por lo que sugiere la sigla (regla 1).

### `MLV` — nivel de transformación de coordenadas

**HIPÓTESIS fundada**, no derivado. Es la única lectura que explica el propio esqueleto:

```
MLV=0  →  %Or[0].ofX/Y/Z    (el origen, en µm)
MLV=1  →  SHF[X]/[Y]/[Z]    (el mismo origen, en mm)
```

y el teardown, que recorre los niveles 1 y 2 poniéndolos en cero antes de volver al 0 — o
sea, **limpia la pila entera**, se haya usado o no. Eso explica de paso el `MLV=2` «de un
nivel que nunca se usó» (B1g).

Lo que **no** pude corroborar: se le atribuyen registros hermanos (`MIR`, `SYS`) y un rango
`0…5`. Barridos los 382 binarios, **no existe `MIR[`, `SYS[` ni `MLV=3/4/5` como literal**.
Nuestro emisor sólo escribe `SHF` y sólo usa 0, 1 y 2. No lo refuta; tampoco lo confirma.

### `SYN` — barrera de sincronización

**HIPÓTESIS con mecanismo**: el CNC calcula bloques por delante de la ejecución física, y
`SYN` obliga al intérprete a esperar a que el bloque anterior se haya ejecutado de verdad.
Encaja con su posición —antes de tocar offsets y antes del cierre—, pero **no tiene evidencia
propia**: el manual de programación de OSAI (482 páginas, procesado entero) no lo documenta,
y el de SCM tampoco.

### Códigos M, de paso

- **`M58` = «LLAMADA VACÍO GENERAL (ZONA A-B)»** (cap. 12) — confirma por el fabricante lo
  que el comentario del `NCI.CFG` decía en italiano.
- **`M20` = «ningún cambio para el modo pasante (no se cierra al final del programa)»**
  (cap. 23) — es el `M20` del bloque del láser.
- ⚠️ El capítulo 23 lista los códigos M que siguen valiendo en máquinas ESA-GV
  (`M0 M3 M5 M6 M12 M15 M20 M31/32/33 M51 M110–114`…) y **`M58` no está en esa lista**. El
  documento es de 2004 y la máquina de 2011: no concluyo nada, queda anotado para mirar.

## Preguntas que abre el esqueleto

- ⚠️ ~~**¿Los orígenes son tres, o cuatro?**~~ **Respondida en los hechos el 2026-08-12**: los
  seis binarios del emisor **difieren entre la PC del CNC y la de oficina técnica** (el CNC
  tiene la build de 2011-11-18; oficina, la de 2011-10-14), y `nci32.dll` difiere hasta en
  tamaño y en plantillas de emisión. **No es «el binario hace siempre lo mismo»: hay dos
  emisores conviviendo**, así que el emisor es un origen. Detalle en `emisor_iso.md`.
  Con el marco de B1h: la mayoría de esas líneas son **el default de una clave de
  configuración que nadie definió**, no una decisión del binario. Lo que queda para decidir
  es más acotado — **si el snapshot registra al emisor**, y como los DLL no tienen número de
  versión, sería por hash, igual que el `manifest.csv`.
- ¿Qué es `V=0` del header? ¿Y `Repetitions`, que no aparece?
- ~~¿Por qué el reset toca justo los registros `ETK[0,1,2,13,17,18,19]`?~~ **RESPONDIDA
  (2026-08-12, B1f): porque están escritos en `$GEN_END` de `NCI.CFG`.** Es configuración
  de la máquina, no una constante del lenguaje.
- ~~¿Qué es `M58`?~~ **RESPONDIDA (B1f): habilita el bloqueo de la pieza (vacío).**
- ~~¿Qué son `SYN`, `VL6`, `VL7`, `EDK[13].0`, `ETK[8]`, `ETK[500]`?~~ **RESPONDIDA en gran
  parte (2026-08-14, B1i)**: `VL6`/`VL7` llevan longitud y radio de la herramienta (derivado
  contra el catálogo); `EDK` es un bit de intercambio CNC→PLC y su índice el dispositivo;
  `ETK[8]` es de la banda del cambio de herramienta **y no es constante**. Siguen abiertos el
  **significado de `SYN`** (hipótesis con mecanismo) y los **índices `ETK` altos**
  (`114`, `500`, `903`, `904`), que son por máquina y viven en el capítulo 33 rellenado.
- ~~El teardown escribe `MLV=2` aunque el nivel 2 nunca se usó: ¿es fijo o depende de la
  máquina?~~ **RESPONDIDA (2026-08-12, B1g): es una plantilla del módulo de mesa**
  (`PlPathFilter32.dll`), que se emite entera con sus dos niveles. **Y el 2026-08-14 (B1i) el
  significado pasa a hipótesis fundada**: `MLV` selecciona el **nivel de transformación de
  coordenadas** —el 0 lleva el `%Or`, el 1 el `SHF`— y el teardown limpia la pila entera.
- `%ETK[114]` de la línea 19: ¿qué corrección es, y de dónde sale? Aparece en `PostISO.dll`
  dentro de la plantilla `G161 … Z((…)+(%ETK[114]/1000))`, junto al bloque de palpado.

Las responden los `.cfg` del snapshot, el manual de Xilog (`pgmx/docs/xilog_plus_pgm/`) y
los fixtures de R001 — en ese orden: primero leer, después preguntar (regla 2).

---

# B2 · Qué agrega cada operación al esqueleto (2026-09-07)

`B1` atribuyó las 43 líneas del **programa vacío**. `B2` es la otra mitad: **qué le agrega cada
operación**, y de dónde sale cada número.

Se abre recién ahora, con dos mecanizados derivados —perforado (D1) y canal (D2)— más la única
traza de fresado que existe. Hasta hoy cada bloque vivía sólo en el doc de su rama.

> **Todas las cuentas de acá son contra el programa vacío del MISMO campo: 43 líneas.**
> Verificado el 2026-09-07 sobre los veinte campos del Grupo 0 del perforado: **los veinte dan
> 43**, así que el campo no cambia el largo del esqueleto.
>
> 📌 **Corrige un número que circulaba**: `perforado.md` §4 decía «sobre el ISO del programa
> vacío (44 líneas), un taladro agrega 40». Son **43** —como `programa_vacio.md` lo tuvo
> siempre— y el taladro agrega **41**.

## ⭐⭐ No hay un bloque por operación: hay uno por FAMILIA DE EMISIÓN

Y la familia la decide **la herramienta**, no la operación que elegiste en la UI. El registro
que la nombra es **`?%ETK[7]`**:

| `?%ETK[7]` | familia | cabezal | operaciones de la UI que la producen | líneas |
|---|---|---|---|---|
| **3** | taladrado | perforador | `Perforado` | **41** |
| **1** | corte con disco | perforador | `Canal` con la sierra `082` | **52** |
| **4** | fresado | electromandril | `Fresado` **y** `Canal` con una `E00x` | **51** |

⇒ La prueba más fuerte de que la familia es de la herramienta y no de la operación: el
**«Fresado» de una línea** y el **«Canal» hecho con la `E004`** dan **el mismo bloque de 51
líneas**, línea por línea, y sólo difieren en los números de la herramienta y las coordenadas
(`fresado.md` §4).

## Qué tienen en común las tres

```
?%ETK[8]=1 · G40   ×2          <- preámbulo del bloque de operaciones
…selección de herramienta…      <- lo que cambia por familia
MLV=2 · %Or[0].ofX/Y/Z         <- el segundo bloque de origen, igual al del esqueleto
MLV=1 · SHF[X]/[Y]/[Z]
MLV=2 · SHF[X]/[Y]/[Z]         <- el offset del HUSO o del cabezal
…el movimiento…
```

## Y en qué difieren

| | taladrado (3) | disco (1) | fresado (4) |
|---|---|---|---|
| cambio de herramienta | **no** | **no** | `MLV=0` · `T n` · `SYN` · `M06` |
| selección | `?%ETK[6]`=huso · `?%ETK[0]`=2^(plc−1) | `?%ETK[6]`=82 · `?%ETK[1]`=2^(plc−33) | `?%ETK[6]`=1 · `?%ETK[9]`=almacén · `?%ETK[13]` · `?%ETK[18]` |
| corrector | **no lo carga** | `D1` · `SVL` · `SVR` · `VL6` · `VL7` | ídem |
| `SHF` del programa | `SHF[Z]=0` — **Z contra la mesa** | `SHF[Z]`=espesor | `SHF[Z]`=espesor |
| `SHF` del cabezal | del registro del huso | del registro 82 | `32.050 / −246.650 / −125.300` |
| cota de corte | `espesor − prof + ToolOffsetLength` | **−profundidad** | **−profundidad** |
| aproximación | `espesor + seguridad + ToolOffsetLength` | `ToolOffsetLength + seguridad` | ídem |
| espera al cerrar | `G4F1.200` | `G4F1.200` | **no** |

## De dónde sale cada número

**Ninguno es una constante interna** (regla 4). Las fuentes, con su derivación:

| en el ISO | sale de | dónde se derivó |
|---|---|---|
| `SVL` | `ToolOffsetLength` del catálogo | `canal.md` §19 · `perforado.md` Grupo 6 |
| `SVR` | radio del **cuerpo**: `BladeThickness/2` (disco) o `Diameter/2` (fresa) | `canal.md` §19, y el manual de Xilog lo escribe igual |
| `S…M3` | `SpindleSpeed.Standard` | `perforado.md` §7bis |
| `F` del corte | `FeedRate.Standard × 1000` | `canal.md` §23 |
| `F` de la bajada | `DescentSpeed.Standard × 1000` | ídem |
| cota de aproximación | **`ToolOffsetLength` + plano de seguridad** | `canal.md` §19, tres herramientas |
| `?%ETK[0]` / `?%ETK[1]` | `2^(shPlcOut−1)` y `2^(shPlcOut−33)` | `perforado.md` Grupo 6 · `canal.md` §8 |
| `?%ETK[6]` | número de huso o de herramienta | ídem |
| `T` y `?%ETK[9]` | `shStorePos` del catálogo | `canal.md` §23, 7/7 |
| `SHF` del huso | `−pos23 / −pos24 / −pos25` de `spindles.cfg` | `perforado.md` §7 |
| plano de seguridad | `ApproachSecurityPlane` del `.pgmx` | `canal.md` §10 |

⚠️ **El catálogo es `def.tlgx`, que viaja dentro de cada `.pgmx`** — y sus valores de longitud
son **resultados de calibración**, no geometría declarada (`fixtures.md` §7).

## Lo que B2 todavía NO cubre

| | |
|---|---|
| `?%ETK[17]=257` | igual en las tres familias, nunca varió |
| `G4F1.200` | la espera del cierre en las familias del perforador |
| el `0,75` de la cola del disco | un solo candidato, `gendata.cfg` (`emisor_iso.md`) |
| el `1 mm` de entrada/salida del `G41`/`G42` | sin procedencia |
| el conteo del `Xmsg` | **se cuenta**, no se tabula (`operaciones_maquina.md` §18); falta la base |
| `Vaciado`, `Galceado`, `Corte con cuchilla` | operaciones sin estudiar: pueden abrir familias nuevas |
