# Fresado — rama D

**Documento vivo.** El **Fresado**: la operación que recorre una geometría con una herramienta
del electromandril. Tercer mecanizado de la rama D, y el que menos evidencia propia tiene.

> 📌 **Por qué este doc nace tarde y con un solo fixture.** La primera —y hasta hoy única—
> traza de fresado de la época nueva llegó en el **lote de dibujos** (rama G), y quedó
> archivada en `dibujos.md` §13.1 mientras la rama D figuraba como 🔮 sin arrancar. La
> auditoría del 2026-08-27 lo detectó y la hoja de ruta lo anotó como *«falta consolidarlo en
> un doc de la rama D»*. **Esto es esa consolidación** (2026-09-07), con los números
> re-medidos.
>
> ⏭️ **2026-09-08: el lote D3 está pedido** (§8, 61 archivos). Y antes de pedirlo, los
> archivos heredados dieron **dos derivaciones y una corrección**, sin fixture nuevo: el «+20»
> de la cota de aproximación **es el plano de seguridad** (§4bis), el campo **no mueve el
> bloque** (§4ter), y los fixtures no eran uno sino **cinco**, en campo `A` y no `HG` (§1).
>
> ⭐⭐ **2026-09-08, mismo día: la tanda 1 está hecha — 35 pares y 12 capturas** (§9 a §14).
> Se cerró lo que la rama debía: **la rampa son ATRIBUTOS de operación**, no un campo de la
> ventana, y su serialización 3D **destraba el defecto que bloqueaba al sintetizador** (§10);
> el bloque queda explicado por el catálogo en **7 de 7 herramientas**, con el avance de la
> bajada derivado (§9); y de las geometrías salieron el `G2`/`G3` con centro absoluto, el
> círculo en **dos medias vueltas**, y que **Maestro aproxima la elipse en 36 arcos dentro del
> `.pgmx`** — el converter no tiene que saber aproximar (§12).
>
> ⭐⭐⭐ **2026-09-08, noche: grupos 4 y 5, 26 pares más** (§15 a §18). El de más peso:
> **`%DONTCARESPEEDV=1` —la línea que hace abortar el ISO de Maestro en la máquina— la emite
> «Salida a cota de seguridad» con multipaso**, y el fixture del hito del 2026-08-03 se llamaba
> `scs_mp5` justamente por eso. Además: `SVR` resulta ser el **radio de compensación**
> (cuerpo + `Rebaba`), `ActivateCNCCorrection = false` **cambia la estructura del bloque**, y
> la fórmula del acortamiento del canal queda **refutada para el fresado**. Y un `10` que no se
> puede escribir todavía: el retorno «En la pieza» está confundido entre la profundidad y
> `MillingRetractDistance` (§16.3).
>
> ⭐⭐ **Y el cierre del día: el Grupo 6** (§19 a §22). El acercamiento y el alejamiento salen
> con fórmula —**`RadiusMultiplier × SVR`**, diez puntos exactos—, `Bajada`/`Subida` resulta
> ser una **rampa** contra los dos movimientos de `Cota`, y el `Automático` del lado del arco
> **va cruzado** respecto de la corrección. Además **la UI fuerza CAD cuando hay multipaso**
> (dato de Fermín) ⇒ multipaso y `G41`/`G42` no coexisten nunca. Y los `corr_len` rehechos
> cierran el acortamiento: **es el radio, con dos profundidades**.
>
> ⭐⭐⭐ **2026-09-09 — Grupo 7: el tercer origen queda cerrado** (§23). Dos archivos con la
> `Cota de seguridad` **cruzada** contra la opción de Maestro, y captura de la ventana en cada
> postproceso: **el ISO sigue al archivo en los dos casos** ⇒ `SecurityDistance` **no se lee al
> postprocesar**, es sólo el default de creación. Con eso queda hecho el «experimento de las
> dos PCs» que estaba abierto desde el 2026-08-09 — y sin necesitar una segunda máquina.

## 1. Los fixtures heredados

Una **línea dibujada** que un `GeneralProfileFeature` llamado «Fresado» toma, con la
herramienta **`E001`** (Widea 18 mm), sobre la pieza de siempre. Viven en
`Dibujos\Rama G\` y todos tienen `.iso`.

> ⚠️ **CORRECCIÓN 2026-09-08.** Esta sección decía «el único fixture … campo `HG`». Las dos
> cosas eran falsas, y las dos se arreglan leyendo el atributo en vez del nombre —
> `fixtures.md` §2 en su forma más literal. **Son cinco archivos y hay dos campos.**

| archivo | `ExecutionFields` | prof. | plano seg. |
|---|---|---|---|
| `R_PV_manual_base_linea_01_fresada` | **`A`** | 9 | 20 |
| `R_PV_manual_base_linea_01_fresada_XMSG` | **`A`** | 9 | 20 |
| `R_PV_manual_base_origen_x100_y50_linea_fresada` | **`A`** | 5 | **30** |
| `R_PV_HG_manual_base_linea_01_fresada_XMSG` | `HG` | 9 | 20 |
| `R_PV_HG_manual_base_origen_x100_y50_linea_fresada` | `HG` | 5 | **30** |

La línea es de (50,50) a (350,50) en los `linea_01`; los `origen_x100_y50` mueven el origen de
la pieza y la dimensionan 500×450.

⚠️ **Igual es evidencia de otra rama.** No hubo lote de fresado: no se barrió ni un parámetro,
ni la estrategia, ni el acercamiento, ni la corrección. Casi todo lo de abajo sale de **un solo
par** — con dos excepciones, que son §4bis y §4ter y salieron de mirar los otros cuatro.

## 2. ⭐ Maestro REUTILIZA la geometría dibujada

Lo que trababa la rama G, y este fixture lo cerró: el `Feature` **apunta** a la geometría del
dibujo en vez de duplicarla. El ID aparece exactamente dos veces en el archivo — la definición
en `<Geometries>` y la referencia del `Feature`.

⇒ **Un nodo, dos dueños.** Nuestro sintetizador siempre crea la geometría junto con el
mecanizado; Maestro puede apuntar a una que ya existe. Detalle en `dibujos.md` §13.1.

## 3. ⭐ La traza NO es la geometría

Corrección de Fermín, y es la que ordena toda la rama D: **lo que llega al ISO es la traza; la
geometría es de dónde se calcula.**

- la corrección de fresa y la rebaba generan recorridos **paralelos**;
- el acercamiento y el alejamiento **agregan segmentos**;
- un vaciado produce una traza compleja a partir de **una o más** geometrías.

Este fixture lo muestra en el caso más simple: el XY de la traza **coincide** con la línea
dibujada —porque la compensación está cancelada, sólo hay `G40`— y aun así **agrega el
posicionamiento, la bajada en Z y la salida**, que una geometría plana no tiene.

## 4. El bloque, medido (2026-09-07)

Contra el programa vacío del mismo campo (43 líneas), el fresado de una línea agrega
**51 líneas**:

```
?%ETK[8]=1 · G40   ×2          <- preámbulo del bloque
MLV=0 · T1 · SYN · M06         <- cambio de herramienta
?%ETK[6]=1 · ?%ETK[9]=1 · ?%ETK[18]=1
S18000M3 · G17
MLV=2 · %Or[0].ofX/Y/Z         <- el segundo bloque de origen
MLV=1 · SHF[X]/[Y]/[Z]
MLV=2 · ?%ETK[13]=1
MLV=2 · SHF[X]=32.050 · SHF[Y]=-246.650 · SHF[Z]=-125.300   <- offset del electromandril
G0 X50.000 Y50.000
G0 Z145.400                    <- SVL + plano de seguridad
D1 · SVL 125.400 · VL6 · SVR 9.180 · VL7
G1 Z-9.000 F2000.000
?%ETK[7]=4
G1 X350.000 Z-9.000 F5000.000  <- el corte
G0 Z20.000
D0 · SVL 0.000 · …
```

### ⭐⭐ Y es EL MISMO BLOQUE que el canal con fresa

Comparado línea por línea contra el canal del Grupo 11 hecho con la `E004`
(`canal.md` §19), las **51 líneas coinciden en estructura**. Lo único que difiere:

| | fresado de línea | canal con `E004` |
|---|---|---|
| herramienta | `T1` · `?%ETK[9]=1` | `T4` · `?%ETK[9]=4` |
| del catálogo | `SVL 125.400` · `SVR 9.180` | `SVL 107.200` · `SVR 2.000` |
| coordenadas y cota | `Y50`, `Z-9` | `Y200`, `Z-10` |

⇒ **Dos operaciones distintas de la UI producen el mismo bloque de ISO.** Confirma desde el
otro lado lo que `canal.md` §19 derivó: **la familia de emisión la decide la HERRAMIENTA, no
la operación** — y `?%ETK[7]=4` es la del electromandril, se llame «Fresado» o «Canal».

## 4bis. ⭐⭐ El «+20» de la cota de aproximación NO es una constante: es el plano de seguridad

**Derivado el 2026-09-08 con archivos que ya estaban**, sin pedir un fixture nuevo.

`canal.md` §19 cerró la cota de aproximación como `ToolOffsetLength + plano de seguridad (20)`
con tres herramientas. Las tres tenían el plano en **20**, así que el 20 no estaba separado de
la fórmula. Los fixtures del origen desplazado lo tienen en **30**:

| fixture | `ApproachSecurityPlane` | `SVL` | aproximación | salida |
|---|---|---|---|---|
| `…_linea_01_fresada` | 20 | 125.400 | `G0 Z145.400` | `G0 Z20.000` |
| `…_origen_x100_y50_linea_fresada` | **30** | 125.400 | **`G0 Z155.400`** | **`G0 Z30.000`** |

```
Z de aproximación = ToolOffsetLength + plano de seguridad
Z de salida       = plano de seguridad
```

⇒ **La regla 4 del `CLAUDE.md` en un caso concreto**: un converter con el `20` escrito adentro
habría emitido `Z145.400` para un programa que pide `Z155.400`, y no habría podido notar que
no sabía. El número sale del `.pgmx`, de la operación.

⚠️ **Lo que este par NO separa**: `ApproachSecurityPlane` y `RetractSecurityPlane` valen lo
mismo en los dos archivos y cambian juntos, así que no se puede decir cuál gobierna cada cota
— sólo que las dos siguen al plano. Y el fixture varía tres cosas a la vez (origen, dimensión y
profundidad); las tres están descartadas como causa —el origen entra por `SHF`, la dimensión por
el header y la profundidad no mueve la aproximación (`canal.md` §12)—, pero **la variación
aislada la debe el lote D3, Grupo 7**.

### Y de paso reabre una predicción de A6 que estaba cerrada por falta de traza

`opciones_de_aplicacion.md` midió `SecurityDistance` (la clave de la ventana `Opciones`, **20**
en la PC del CNC y **30** en otra) sobre un programa vacío y dio idéntico, con la predicción de
que **necesita trayectoria para verse**. Acá hay trayectoria y el valor aparece.

📌 **Hipótesis, no derivación**: si el `30` de esos dos archivos es el `SecurityDistance` de la
PC donde se crearon, entonces Maestro **congela el default en el `.pgmx`** al crear la
operación ⇒ el converter **no necesita leer ese origen**. Lo contesta una pregunta, no un
fixture: en qué máquina se hicieron.

> ✅ **DERIVADO el 2026-09-09 (§23.2), y era exactamente ese mecanismo.** El Grupo 7 cruzó los
> valores —archivo en 30 con la opción en 20, y archivo en 25 con la opción en 30— y **el ISO
> siguió al archivo en los dos casos**, con captura de la ventana como testigo. La ventana
> `Opciones` da el **default de creación**; no se lee al postprocesar. Y de paso la variación
> aislada que esta sección le debía al Grupo 7 está hecha: tres cotas, 20 · 25 · 30.

## 4ter. ✅ El campo no mueve el bloque del fresado

Mismo día, mismos archivos. `…_origen_x100_y50_linea_fresada` existe en campo **`A`** y en
**`HG`**, idénticos en todo lo demás. El diff completo de sus ISO son **seis líneas**: los dos
bloques de origen (`%Or`/`SHF`), el nombre del programa, la marca del campo en el header y el
índice del `EDK` (`[10]` en `A`, `[13]` en `HG`).

⇒ **Ni una línea del bloque de fresado cambia.** Confirma para el fresado lo que el perforado
había mostrado: **el campo entra por el origen, no por la traza** — y por eso el lote D3 no
lleva grupo de campos.

## 5. Lo que se cumplió de lo predicho

| predicho (2026-08-19) | observado |
|---|---|
| `SVL`/`SVR` salen del catálogo | `SVL 125.400` · `SVR 9.180` = `ToolOffsetLength` y radio del cuerpo de la `E001` |
| `S…M3` sale de `SpindleSpeed.Standard` | `S18000M3`, y la `E001` tiene 18000 |

Y la cota de aproximación, `G0 Z145.400` = **`SVL` + 20**, la misma regla que el canal
(`canal.md` §19).

## 6. El incremento del conteo del `Xmsg`

**+206** para este fresado (`operaciones_maquina.md` §17.2).

> ⚠️ Ese número es de **un** fixture, y desde el 2026-09-07 sabemos que el conteo **mide
> caracteres del texto emitido** (`operaciones_maquina.md` §18). El 206 vale para *esta* traza,
> no para «el fresado» — otra geometría con otras coordenadas da otro número, y la regla es
> contar, no tabular.

## 7. Lo que falta, que es casi todo

El fresado **no tiene lote propio**. Con un solo fixture, sin barrido, quedan sin tocar:

| | |
|---|---|
| las cinco geometrías | sólo se probó la **línea**. Arco, círculo, polilínea y contorno, sin fixture |
| la **estrategia** de fresado | `MillingStrategySpec` existe en el sintetizador y no hay evidencia nueva |
| el acercamiento y el alejamiento | el fixture los tiene deshabilitados |
| la corrección (`G41`/`G42`) | el canal la derivó (`canal.md` §21); falta confirmar que el fresado se comporta igual |
| las pasadas en Z | y el bug de Maestro con `StepDepth` que no divide exacto (`hoja_de_ruta`, 2026-09-03) |
| el sentido de recorrido | el canal con sierra lo normaliza; con fresa va en el sentido dibujado. Sin probar en un contorno cerrado |

⇒ **Cuando la rama D siga, el fresado es el lote grande**: es la operación con más superficie
sin medir, y la que más geometrías admite.

## 8. El lote D3, pedido (2026-09-08)

`Mecanizados\Fresado\INSTRUCCIONES.md` — **61 archivos y 5 capturas, en trece grupos**, campo
`A`, herramienta base **`E004`** (Fresa 4 mm). La `E004` y no la `E001` a propósito: con Ø18,36
una fresa no entra en un círculo chico ni en una esquina viva, y el grupo más grande del lote es
el de geometrías.

Orden de trabajo declarado en dos tandas. La primera son los grupos 1 a 3 (22 archivos), que es
lo que más devuelve:

| grupo | qué decide |
|---|---|
| 1 · el mínimo (2) | el bloque con la herramienta del lote, y el ancla con el fixture heredado |
| 2 · profundidad, rampa y pasante (5) | ⭐ **destraba el defecto de `build_line_geometry_profile`**, y el **pasante**, que el canal no pudo hacer (el disco entra 10 mm; la `E004`, 22) |
| 3 · las geometrías (15) | ⭐⭐ arco, círculo, polilínea, rectángulo, polígono, elipse, texto, punto, contorno de la pieza. **Lo único que sólo el fresado puede contestar** |
| 4 · corrección y sobremedida (7) | `AllowanceSide`/`AllowanceBottom`, que **no existen en el canal**; el resto son testigos. Y `IsPrecise`, que **falsa la fórmula del acortamiento** |
| 5 · estrategia y pasadas (7) | el bug de `StepDepth`, y ⭐ **el par que explica el paro de máquina del 2026-07-30** («Salida a cota de seguridad» contra «En la Pieza») |
| 6 · acercamiento y alejamiento (6) | los segmentos que la traza agrega; el fixture heredado los tiene apagados |
| 7 · plano de seguridad (2) | la variación aislada que le falta a §4bis |
| 8 · varios fresados y el orden (4) | ⭐ si dos fresados con la misma fresa emiten **un** `M06` o dos |
| 9 · la cara (3) | ⭐⭐ la **cara inferior**: si se descarta en silencio como en el perforado, es el cuarto caso de fail-loud |
| 10 · testigos del canal (3) | `Invertir`, `Canto a canto`, `Condición` |
| 11 · el conteo del `Xmsg` (3) | la **fórmula** del fresado; el círculo separa «por operación» de «por caracteres» |
| 12 · barrido A5 (8, con captura) | la rutina permanente, sobre la operación que gobierna trazas |
| 13 · microuniones (2) | nunca se estudiaron, y no hay nada en el sintetizador |

### ❓ Una incongruencia de nomenclatura para resolver ANTES de tocar el sintetizador

Regla 1 del `CLAUDE.md`, planteada acá porque el lote la va a hacer visible: **nuestras specs
de fresado se llaman por la GEOMETRÍA y la del canal por la OPERACIÓN.**

| en la UI de Maestro | en el sintetizador |
|---|---|
| `Operaciones > Fresado` sobre una línea | `LineSpec` |
| `Operaciones > Fresado` sobre un círculo | `CircleSpec` |
| `Operaciones > Fresado` sobre una polilínea | `PolylineSpec` |
| `Operaciones > Fresado` sobre un contorno | `ContourSpec` |
| `Operaciones > Canal` | `ChannelSpec` ✅ |
| `Dibujar > Línea` (sin mecanizado) | `DrawingSpec` |

Las dos lecturas y lo que cambia según cuál valga:

- **«`LineSpec` es el fresado de una línea»** ⇒ hay cinco nombres para **una** operación de la
  UI, y `LineSpec` compite con `DrawingSpec` por la palabra «línea» (una dibuja, la otra
  mecaniza). Correspondería un `FresadoSpec` con la geometría como parámetro, y las cinco
  actuales pasarían a ser casos de uso — igual que rectángulo y polígono resultaron ser casos
  del mismo nodo (`dibujos.md` §12.4).
- **«`LineSpec` es la geometría, y el fresado va aparte»** ⇒ entonces hoy no existe la spec de
  la operación, y el eje de organización de `milling/` es la geometría. Hay que escribirlo.

⏸ **No se toca nada hasta que Fermín defina.** El sintetizador está congelado hasta que cierre
la rama D (decisión del 2026-09-07, reafirma C5), así que la pregunta no bloquea el lote:
bloquea la implementación, que es después.

---

# La tanda 1 del lote D3 (2026-09-08)

**35 pares `.pgmx` + `.iso` y 12 capturas**, hechos por Fermín en un día. Auditoría por
atributo: **35 de 35** en campo `A` y con la herramienta que afirma el nombre.

Tres cosas del pedido cambiaron en la máquina, y las tres mejoran el lote:

- **el Grupo 1 se hizo con las SIETE herramientas**, no con dos;
- **la rampa no se pide en la ventana del `Fresado`**: se agregan **atributos de profundidad**
  a un fresado existente (§10). Los `_pfN` que yo había pedido no existen;
- **`_geometria_sin_dibujo` es imposible**: en Maestro **siempre** se dibuja primero y después
  se aplica el fresado (§12.6).

Y Fermín amplió tres grupos por su cuenta — el arco `_invertir`, los tres puntos de entrada del
círculo y la elipse rotada —, que son justo los que cerraron el sentido de recorrido y el punto
de entrada.

## 9. Grupo 1 — las siete herramientas, y un nombre que miente

Los siete ISO tienen **95 líneas** y difieren **sólo en los números del catálogo**:

| | `T` = `?%ETK[9]` | `SVL` | `SVR` | `S` | `F` bajada | `F` corte | aproximación |
|---|---|---|---|---|---|---|---|
| `E001` | 1 | 125.400 | 9.180 | 18000 | 2000 | 5000 | 145.400 |
| `E002` | 2 | 107.000 | 50.000 | **6000** | 2000 | **3000** | 127.000 |
| `E003` | 3 | 111.500 | 4.760 | 18000 | **3000** | **18000** | 131.500 |
| `E004` | 4 | 95.000 | 2.000 | 18000 | 2000 | 5000 | 115.000 |
| `E005` | 5 | 145.900 | 38.000 | 18000 | 2000 | 5000 | 165.900 |
| `E006` | 6 | 120.870 | 40.000 | 18000 | 2000 | **2000** | 140.870 |
| `E007` | 7 | 152.100 | 8.860 | 18000 | 2000 | 5000 | 172.100 |

⇒ **7 de 7 explicados por `def.tlgx`**, con las mismas reglas que el canal (`canal.md` §23):
`SVL` = `ToolOffsetLength` · `SVR` = radio del cuerpo · `S` = `SpindleSpeed.Standard` ·
`F` del corte = `FeedRate.Standard × 1000` · aproximación = `SVL` + cota de seguridad ·
`T` = `?%ETK[9]` = `shStorePos`.

### ⭐ Y una regla nueva: el avance de la BAJADA es `DescentSpeed`

El canal no la pudo separar porque sus herramientas comparten el valor. Acá la `E003` tiene
`DescentSpeed = 3` y su bajada sale **`F3000`** mientras las otras seis salen `F2000`.

```
G1 Z-<prof> F<DescentSpeed × 1000>       <- la bajada vertical
G1 X…       F<FeedRate.Standard × 1000>  <- el corte
```

⇒ Dos velocidades distintas en el mismo bloque, las dos del catálogo. **Un número menos sin
procedencia.**

### ⚠️ El nombre del Grupo 1 dice `x50_x300_y150` y la traza es (50,200)→(350,200)

Los siete archivos lo afirman y los siete lo contradicen: la geometría del `.pgmx` es
`8 0 300` / `1 50 200 0 · 1 0 0`, y el ISO posiciona en `G0 X50.000 Y200.000` y corta hasta
`X350.000`. Control cruzado: el ISO del `E004` del Grupo 1 es **byte-idéntico** al `prof10` del
Grupo 2 salvo la línea del nombre — o sea, es exactamente el mínimo pedido.

⇒ **Ninguna derivación se apoya en ese nombre**, y por eso no cambia nada: `fixtures.md` §2
funcionando. Pero el corpus queda con siete nombres que mienten, y conviene renombrarlos a
`…_x50_y200_x350_y200_prof10` antes de que alguien los lea al revés.

## 10. ⭐⭐⭐ Grupo 2 — la rampa son ATRIBUTOS, y el defecto del sintetizador queda derivado

**Es el hallazgo que la tanda tenía que traer, y vino más limpio de lo esperado.**

### La UI: un atributo, no un campo

La ventana del `Fresado` **no tiene «Profundidad final»**. La rampa se arma con
`Operaciones > Atributos > Profundidad`, que abre una ventana propia de dos campos —
**`Profundidad`** y **`Posición (%)`** — y cuelga un punto sobre la geometría. El tooltip de la
cinta lo dice con todas las letras: *«permite crear un **atributo** de tipo profundidad»*.

⇒ **La nomenclatura de la UI y la del XML coinciden**, que no es lo habitual:

```xml
<Attributes>
  <b:OperationAttribute i:type="b:DepthAttribute">
    <b:IsNormalized>true</b:IsNormalized>
    <b:UPar>0.25</b:UPar>      <!-- Posicion (%) / 100 -->
    <b:Depth>5</b:Depth>       <!-- Profundidad        -->
  </b:OperationAttribute>
</Attributes>
```

⇒ ⭐ **El nodo `<Attributes>` deja de estar vacío y tiene dueño.** Estaba en todos los `.pgmx`
sin contenido desde el principio. Y sus hermanos en la cinta — **`Velocidad`** y
**`Microuniones`** — son con toda probabilidad otros dos tipos de `OperationAttribute`:
predicción falsable, barata de comprobar.

⚠️ **`Depth.StartDepth`/`EndDepth` NO cambian**: siguen los dos en la profundidad base. El
mecanismo del fresado **no es el del canal**, donde la rampa sí eran esos dos campos.

### El ISO: la traza se parte en un segmento por tramo

| archivo | atributos | el corte que emite |
|---|---|---|
| `prof10` | — | `G1 X350.000 Z-10.000` |
| `prof10_p0_10_p100_5` | (0 %, 10) (100 %, 5) | `G1 X350.000 Z-5.000` |
| `prof5_p0_5_p100_10` | (0 %, 5) (100 %, 10) | `G1 X350.000 Z-10.000` |
| `prof10_p25_10_p75_5` | (25 %, 10) (75 %, 5) | `G1 X125.000 Z-10.000` · `G1 X275.000 Z-5.000` · `G1 X350.000 Z-5.000` |
| `prof10_p25_5_p75_10` | (25 %, 5) (75 %, 10) | `G1 X125.000 Z-5.000` · `G1 X275.000 Z-10.000` · `G1 X350.000 Z-10.000` |

⇒ **`Posición (%)` es la fracción del recorrido**: 25 % de (50→350) es `X125`, 75 % es `X275`.
Y la `Z` **interpola linealmente entre atributos consecutivos**; antes del primero y después
del último queda constante.

### ⭐⭐ Y la serialización, que es lo que estaba trabado

El defecto del 2026-09-07 — `build_line_geometry_profile` con dos `Z` distintas serializa el
largo en 3D pero la **dirección plana**, y la curva de salida arranca en la `Z` del inicio —
queda **derivado con fixture**, y la corrección que se había calculado a mano acierta a los
diecisiete dígitos:

```
<d:string>8 0 300.04166377354994
1 50 200 8 0.99986114003960003 0 0.016664352333993333 </d:string>
```

`√(300² + 5²)` = `300.04166377354994` y `(300, 0, 5)/L` = `(0.99986114…, 0, 0.016664352…)`.
**Las dos en 3D.** La sesión anterior había anotado exactamente ese vector como el esperado.

Las tres reglas, ahora con evidencia:

1. **el largo y la dirección son 3D**, ambos;
2. **cada tramo arranca en la `Z` donde terminó el anterior** — `1 125 200 13` sigue a un tramo
   que terminó en 13;
3. ⭐ **la curva `Lift` arranca en la `Z` del FINAL del recorrido y ajusta su largo**: con
   `p0_10_p100_5` sale `8 0 25` desde `1 350 200 13` (25 = 38 − 13), no `8 0 30`. Era el
   segundo síntoma del defecto y estaba sin confirmar.

### ⭐ Y una regla de serialización que no se sabía

Con atributos de profundidad, el `TrajectoryPath` **cambia de tipo**: pasa de
`GeomTrimmedCurve` a **`GeomCompositeCurve`** — y lo hace **aunque tenga un solo miembro**
(`p0_10_p100_5` es un compuesto de uno). El envoltorio no depende de la cantidad de tramos sino
de que haya atributos.

## 11. Grupo 2 — el pasante, que el canal no pudo hacer

| archivo | corte |
|---|---|
| `pasante` | `G1 X350.000 Z-18.000` |
| `pasante_extra0` | **byte-idéntico** al anterior |
| `pasante_extra3` | `G1 X350.000 Z-21.000` |

```
cota del pasante = −(espesor + Extra)
```

⇒ Derivado con dos valores. El `Extra = 0` explícito **engorda el `.pgmx` en 28 bytes y no
toca el ISO**: es la expresión paramétrica que el canal ya había visto (`canal.md` §12), que
existe en el archivo aunque no cambie la salida.

La `E004` tiene `SinkingLength = 22` y la placa 18, así que entra. Con la sierra `082` el
pasante era imposible (entra 10 mm) y quedó como pregunta abierta de D2: **cerrada acá.**

## 12. Grupo 3 — las geometrías

Quince archivos. Todos con `E004`, cara superior, profundidad 10.

### 12.1 ⭐ El costo en líneas es exacto: `50 + N segmentos`

| geometría | segmentos | líneas que agrega |
|---|---|---|
| línea | 1 | **51** |
| círculo | 2 | 52 |
| polilínea abierta de 3 tramos | 3 | 53 |
| rampa de 2 atributos | 3 | 53 |
| rectángulo · contorno de la pieza | 4 | 54 |
| hexágono | 6 | 56 |
| elipse | 36 | 86 |

⇒ **50 líneas de bloque más una por segmento**, sobre siete casos. Con **varias operaciones** no
vale: `dos_fresados_una_geometria` (2 operaciones, 2 segmentos) agrega 71 y el texto (11
operaciones, 315 segmentos) agrega 546. Queda para la tanda 2.

### 12.2 ⭐⭐ El arco: `G3` antihorario, `G2` horario, y el centro va ABSOLUTO

```
G3 X200.000 Y300.000 I200.000 J200.000 F5000.000
```

`I`/`J` son el **centro en coordenadas absolutas de pieza** (200,200), no un incremento desde
el punto de arranque como en el ISO de muchos controles. Y el punto de arranque lo pone el
`G0 X…Y…` anterior.

⭐ **`Invertir` invierte el sentido de recorrido**: el ISO de `arco_…_invertir` es
**byte-idéntico** al de `arco_…_horario` salvo la línea del nombre. En el canal con sierra
`Invertir` sólo sacaba la cola (`canal.md` §18) — porque el sentido de la sierra está
normalizado. Con fresa, **el sentido es del programa y el casillero lo da vuelta**.

### 12.3 ⭐⭐ El círculo son DOS medias vueltas, y el punto de entrada es el ángulo

| archivo | entra en | emite |
|---|---|---|
| `circulo_…_r100` | `X300 Y200` (0°) | `G3` a `X100 Y200` · `G3` a `X300 Y200` |
| `…_pi90` | `X200 Y300` | `G3` a `X200 Y100` · `G3` a `X200 Y300` |
| `…_pi180` | `X100 Y200` | `G3` a `X300 Y200` · `G3` a `X100 Y200` |
| `…_pi270` | `X200 Y100` | `G3` a `X200 Y300` · `G3` a `X200 Y100` |

⇒ **Un círculo nunca se emite como un `G2`/`G3` de 360°**: siempre dos arcos de media vuelta,
por el punto diametralmente opuesto. Y el punto de entrada es el que elige el usuario, con el
centro `I`/`J` constante. Los cuatro van antihorario.

### 12.4 ⭐⭐ La elipse: el `.pgmx` guarda las DOS cosas, y la aproximación la hace Maestro

`GeomEllipse` **existe** — `dibujos.md` §12.2 había predicho su forma
(`3 C N̂ Û V̂ R_may R_men`) sin fixture, y acierta — y el archivo la guarda entera en
`<Geometries>`:

```
3 200 200 0  0 0 1  1 0 0  100 50
```

Pero el **toolpath** de esa misma operación es un `GeomCompositeCurve` de **36 arcos
circulares** (código de curva `2`), y el ISO emite esos 36 `G3` con centros que cambian en cada
uno.

⇒ ⭐⭐⭐ **La aproximación la hace Maestro al construir la traza, no el postprocesador.** Es la
misma lección que dio `ActivateCNCCorrection` en el canal, en su forma más fuerte: **la traza
puede tener una familia de curva distinta de la geometría que la originó.**

⇒ **El converter no tiene que saber aproximar una elipse.** Lee el toolpath y lo copia. Si
tuviera que reproducir la aproximación de Maestro, el byte-idéntico sería inalcanzable.

### 12.5 ⭐ El texto: once operaciones, un solo cambio de herramienta

«PRUEBA» produce **once** `GeneralProfileFeature` + `BottomAndSideFinishMilling` — un contorno
cerrado por cada uno: P(2) R(2) U(1) E(1) B(3) A(2). Confirma `dibujos.md` §13.2: el texto son
contornos, no una familia nueva.

En el ISO (589 líneas):

| | |
|---|---|
| `T4` · `M06` | **1** — ⭐⭐ **el cambio de herramienta NO se repite** entre operaciones de la misma fresa |
| `D1` · `SVL 95.000` · `G1 Z-10` · `?%ETK[7]=4` · `G0 Z20` | **11** — el corrector sí se re-emite por operación |
| `G0 Z115.000` | **1** — la cota de aproximación se emite una vez |
| `G2`/`G3` | **0** — ⭐ las curvas de las letras salen **poligonizadas**, 315 `G1` |

⇒ Contesta por adelantado el Grupo 8 de la tanda 2 (`dos_paralelos`), y lo confirma
`dos_fresados_una_geometria`: un solo `T4`/`SYN`/`M06`, y entre las dos operaciones un bloque de
transición de `G17` + `MLV=2` + tres `G0` con **X, Y y Z combinados en una línea**.

### 12.6 ⛔ Un fresado sobre un punto no existe, y un dibujo sin mecanizado no deja rastro

El `.pgmx` de `punto_200_200` **no tiene feature, ni operación, ni herramienta**: sólo el
`GeomCartesianPoint`. Maestro no deja crear el fresado (captura `fresado_sobre_punto`).

Y su ISO es **idéntico al programa vacío salvo la línea del nombre** — 687 bytes contra 668, y
la diferencia es exactamente el largo de más del nombre. Mismo control cruzado que cerró A7.

⇒ Tercer testimonio de que **una geometría sin mecanizado no llega al ISO**, ahora con un
mecanizado que se intentó y no se pudo crear.

⛔ **Y `_geometria_sin_dibujo` es imposible por construcción** (dato de Fermín): en Maestro
**siempre** se dibuja primero y después se aplica el fresado sobre el dibujo.

⇒ ⭐ **Nuestro sintetizador hace lo contrario**: crea la geometría junto con el mecanizado.
No es un defecto — el `.pgmx` resultante es válido — pero significa que **el camino de Maestro
es uno solo y el nuestro es otro**, y que la reutilización de §2 no es un caso especial: **es la
única forma que existe**.

### 12.7 Las líneas y los compuestos: la coordenada que no cambia se omite

```
G1 X350.000 Z-10.000 F5000.000     <- polilínea, tramo 1: cambia X
G1 Y350.000 Z-10.000 F5000.000     <- tramo 2: cambia Y, la X no se repite
G1 X50.000  Z-10.000 F5000.000
```

Y en el hexágono, donde cambian los dos ejes:

```
G1 X150.000 Z-10.000 F5000.000     <- sólo cambia X  -> se completa con Z
G1 X100.000 Y200.000 F5000.000     <- cambian X e Y  -> sin Z
```

⇒ **Regla de emisión (candidata, 6 casos): se emiten los ejes que cambian; si cambia uno solo,
se agrega la `Z` aunque sea constante.** Vale también para la línea simple y la perpendicular
(`G1 Y350.000 Z-10.000`). Le falta el caso de un tramo puramente vertical para cerrarla.

Lo demás del grupo:

- **rectángulo, hexágono y contorno de la pieza** cierran volviendo al punto de partida, con un
  segmento por lado y **sin nada especial en las esquinas vivas** — la corrección está
  cancelada (`G40`), así que la traza es la geometría;
- el **contorno de la pieza** corta sobre el borde exacto (`X0`/`X400`), no afuera;
- la línea que **sale de la pieza** (`x-20_x420`) no tiene tratamiento especial, igual que en el
  canal;
- la línea **perpendicular** (a lo largo de Y) postprocesa sin problema, lo que confirma que el
  rechazo del canal era **del disco**, no de la operación.

## 13. La ventana del `Fresado`, capturada (2026-09-08)

| sección | qué tiene |
|---|---|
| **Datos fresado** | `Anchura` (en **gris**, = Ø de la herramienta) · `Profundidad` · `Pasante` |
| **Corrección herramienta** | los cuatro botones · los radios **`Corrección C.N.` / `Corrección CAD`** · `Rebaba` |
| **Datos tecnológicos** | el desplegable de herramienta · `Avanz.` y `Rotación (rpm)` **vacíos** ⇒ del catálogo (y por eso el XML guarda `Feedrate`/`Spindle` en `0`) |
| **Estrategia** | desplegable con **Unidireccional · Bidireccional · Helicoidal · ZigZag** |
| **Acercamiento/Alejamiento** | — |
| **Datos avanzados** | `Invertir` · `Condición` · `Comentario` · ⭐ **`Cota de seguridad` = 20** |
| **Datos máquina** | las nueve `Funciones máquina`, todas apagadas |

### ⭐ Tres cosas que la ventana contesta sin fixture

1. **La `Cota de seguridad` es UN campo, y vive en `Datos avanzados`.** Escribe los dos del XML
   (`ApproachSecurityPlane` y `RetractSecurityPlane`) ⇒ **el fixture `secplane_ap30_ret10` del
   Grupo 7 es IMPOSIBLE**: la UI no los separa. Cuál gobierna cada cota no se puede decidir con
   archivos que Maestro produzca.
2. ⛔ **No hay `Sobremedida`** en ninguna sección ⇒ `AllowanceBottom` y `AllowanceSide` son
   campos del XML **sin campo en la ventana**, como `end_radius` y `material_position` en el
   canal. **Los dos fixtures de sobremedida del Grupo 4 son imposibles.**
3. ⛔ **No hay `Canto a canto`**: era del `Canal`. El fixture correspondiente del Grupo 10 se
   cae.

### ⚠️ Y una estrategia que no teníamos, y dos que no están

El desplegable ofrece **cuatro**. Nuestro sintetizador tiene `Unidireccional`, `Bidireccional`,
`Helicoidal` y `ContourParallel`:

- ⭐ **`ZigZag` es nueva** — no existe en el sintetizador;
- **`ContourParallel` no aparece** en el `Fresado`: es de vaciado;
- las dos que declara el scripting (`PlaneCutterLocation`, `SectioningMilling`) **tampoco**.

📌 Y la sección `Unidireccional` nombra las cosas distinto de nuestro código: **`Conexión entre
huecos`** con dos opciones — `Salida a cota de seguridad` / `En la pieza`, **sin un tercero
`Automatic`** —, y el par axial se llama **`Profundidad hueco`** y **`Último hueco`**, no
«profundidad de pasada». Regla 3: manda la UI.

## 14. Lo que la tanda 1 deja abierto

| | |
|---|---|
| los siete nombres del Grupo 1 | afirman `x50_x300_y150` y la traza es (50,200)→(350,200). Conviene renombrar |
| `Velocidad` y `Microuniones` | predicción: son `OperationAttribute` como `DepthAttribute` (§10). Sin fixture |
| el costo en líneas con **varias** operaciones | la regla `50 + N` vale para una sola. Con dos, 71; con once, 546 |
| la regla de emisión de ejes | 6 casos, le falta un tramo puramente vertical |
| `secplane_ap30_ret10` · las dos sobremedidas · `canto_a_canto` | ⛔ **imposibles**: la ventana no ofrece el campo (§13) |
| `ZigZag` | estrategia nueva, sin fixture y sin código |
| el sentido de recorrido de un **contorno cerrado** | horario o antihorario, y si `Invertir` lo da vuelta como en el arco |

---

# Grupos 4 y 5 (2026-09-08, noche)

**26 pares más.** Fermín los armó **cruzando** en vez de barrer uno por uno, y el cruce es lo
que hizo hablar a los dos grupos: la corrección lateral × el modo × la rebaba (Grupo 4), y las
dos conexiones × dos profundidades de pasada × con y sin pasada final (Grupo 5).

Auditoría por atributo: **26 de 26** en campo `A` con la `E004`, y cada nombre coincide con lo
que el archivo dice.

> ⚠️ **Dos archivos traen una variable de más**, y conviene tenerlo presente al leerlos:
> los `corr_len_*` están a **profundidad 18**, no 10 (§15.4), y los diez del Grupo 5 con
> multipaso tienen `ActivateCNCCorrection = false` mientras los dos sin multipaso lo tienen en
> `true` (§16.5). Ninguna de las dos invalida nada — las derivaciones de abajo están aisladas
> contra el archivo que corresponde —, pero las dos son preguntas.

## 15. Grupo 4 — la corrección, la rebaba y el modo

Once archivos: `izq`/`der` × `C.N.`/`CAD` × con y sin `rebaba_2`, más `corr_len` en los dos
modos, más el base.

### 15.1 ⭐ La `Rebaba` se SUMA al desplazamiento lateral

| archivo | posiciona en |
|---|---|
| base (`Center`) | `Y200.000` |
| `corr_izq_CAD` | `Y202.000` |
| `corr_der_CAD` | `Y198.000` |
| `corr_izq_CAD_rebaba_2` | **`Y204.000`** |
| `corr_der_CAD_rebaba_2` | **`Y196.000`** |

```
desplazamiento = lado × (radio del cuerpo + Rebaba)      Left = +Y · Right = −Y
```

El canal (§13) había dejado la `Rebaba` como *«`SideOffset`, y sólo actúa si hay lado»*. Con el
cruce queda la fórmula: **se suma al radio, en la misma dirección que la corrección.**

### 15.2 ⭐⭐ Y `SVR` no es sólo el radio del cuerpo: es el radio de COMPENSACIÓN

| | `SVR` / `VL7` |
|---|---|
| sin rebaba | `2.000` |
| con `Rebaba = 2` | **`4.000`** |

En los cuatro archivos con rebaba, en CAD y en C.N.

```
SVR = radio del cuerpo + Rebaba (SideOffset)
```

⇒ **Acota la regla del canal §19** (`SVR` = radio del cuerpo), que se derivó con `SideOffset = 0`
en todos los casos.

⇒ Y **desmiente una sospecha**: con `Corrección C.N.` la traza de `corr_der_CN_rebaba_2` es
**idéntica** a la de `corr_der_CN` —la línea nominal, `Y200`—, lo que parecía una rebaba
perdida en silencio. No lo es: **entra por el `SVR`**, que es el radio que se le pasa al
control para que compense. El diff de los dos ISO son exactamente dos líneas, `SVR` y `VL7`.

### 15.3 ⭐⭐ `ActivateCNCCorrection = false` cambia la ESTRUCTURA del bloque

Y esto no estaba previsto por nadie. El mismo recorrido sale con dos formas distintas:

| | modo corto | modo largo |
|---|---|---|
| | `G1 Z-10.000 F2000.000` | **`G1 Z20.000 F2000.000`** |
| | `?%ETK[7]=4` | `?%ETK[7]=4` |
| | | **`G1 Z-10.000 F5000.000`** |
| | `G1 X350.000 Z-10.000 F5000.000` | `G1 X350.000 Z-10.000 F5000.000` |
| | | **`G1 Z20.000 F5000.000`** |
| | `G0 Z20.000` | `G0 Z20.000` |

En el modo largo aparecen **tres movimientos** que en el corto no están, y —lo más importante
para el converter— **la bajada al material cambia de velocidad**: de `F2000` (`DescentSpeed`) a
`F5000` (el avance de corte). En el modo largo el `F2000` se gasta bajando al **plano de
seguridad**, que en el corto ni se emite.

**Qué lo enciende**, cruzando los cinco casos del grupo:

| `SideOfFeature` | `ActivateCNCCorrection` | `IsPrecise` | forma |
|---|---|---|---|
| `Center` | `true` | no | corto (el base) |
| `Center` | `true` | **sí** | **corto** (`corr_len_CN`) |
| `Center` | **`false`** | sí | **largo** (`corr_len_CAD`) |
| `Right`/`Left` | `false` | no | largo (`corr_*_CAD`) |
| `Right`/`Left` | `true` | no | largo, y además `G41`/`G42` (`corr_*_CN`) |

⇒ **Lo enciende el flag, no el lado ni `IsPrecise`**: el par `corr_len_CN` / `corr_len_CAD` lo
aísla — misma traza guardada, mismo `Center`, mismo `IsPrecise`, y sólo cambia
`ActivateCNCCorrection`. Uno sale corto y el otro largo.

⇒ Con `true` **y** lado, el bloque toma su tercera forma, la del canal §21: posiciona 1 mm
antes (`G0 X49.000`), emite `G42` (derecha) o `G41` (izquierda), recorre la línea **nominal**
`Y200`, y sale con `G40` 1 mm después (`X351.000`). Confirmado en los cuatro `corr_*_CN`.

### 15.4 ⭐⭐ `IsPrecise` con fresa acorta EL RADIO, y la fórmula del canal era del disco

`corr_len_CAD` y `corr_len_CN` guardan la traza **de 52 a 348** — 2 mm menos por punta, que es
exactamente el **radio de la `E004`**.

⇒ La fórmula del canal, `√(p·(2r−p))`, **no aplica**: con `p = 18` y `r = 2` el radicando es
negativo. Era la geometría de un **disco entrando en la placa**, no una regla de la operación.
Con una fresa cilíndrica, que entra a pique, el borde llega hasta su propio radio.

⚠️ **Un solo punto, y con una variable de más.** Los dos `corr_len` están a **profundidad 18**
(`Depth.StartDepth = EndDepth = 18`, traza en `Z 0`), no a 10 como el resto del grupo. Con eso
alcanza para **refutar** la fórmula del disco —que es imposible con esos números—, pero no para
afirmar que el acortamiento es el radio *independientemente de la profundidad*. Falta un
`corr_len` a otra profundidad.

❓ **Pregunta para Fermín**: ¿la profundidad 18 de esos dos la pusiste vos, o `Corrección en
longitud` la fuerza al espesor?

## 16. Grupo 5 — la estrategia, y de dónde sale `%DONTCARESPEEDV=1`

Quince archivos: `Unidireccional` × `SCS`/`EP` × {sin multipaso, `PH4`, `PH5`, `PH4+UH2`,
`PH5+UH2`}, más `Bidireccional` × las mismas cuatro combinaciones de multipaso, más el base.

### 16.1 ⭐⭐⭐ `%DONTCARESPEEDV=1` sale de «Salida a cota de seguridad»

**Es el hallazgo del grupo, y cierra un pendiente de agosto.** El diff entre `uni_scs_ph5` y
`uni_ep_ph5` son **tres líneas**, y una es:

```
%DONTCARESPEEDV=1
```

Está en el `_scs` y **no** en el `_ep`. Aparece en los cinco archivos con `LiftShiftPlunge`
y multipaso, y en ninguno de los demás.

⇒ ⭐⭐⭐ **Es la línea que hace abortar el ISO de Maestro en la máquina** (Alarma 67), la del
hito del 2026-08-03 — donde el ISO que emitimos nosotros corrió y el de Maestro no. Y el
archivo de aquel día se llamaba `scs_mp5`: **Salida a Cota de Seguridad, multipaso 5**. Es
literalmente este mismo caso, y recién ahora sabemos qué lo dispara.

⇒ Para el converter: **la línea existe, la emite Maestro, y el byte-idéntico la pide** — pero
`CLAUDE.md` §4 ya tiene el precedente resuelto: *el byte-idéntico es el método, no el fin, y
manda la máquina*. Queda como el caso más claro de esa excepción.

### 16.2 ⭐⭐ Qué hace cada conexión, medido

Con profundidad 10 y `PH = 5`, o sea dos pasadas:

| | `Salida a cota de seguridad` (`LiftShiftPlunge`) | `En la pieza` (`Straghtline`) |
|---|---|---|
| pasada 1 | `G1 Z-5` · `G1 X350 Z-5` | ídem |
| **el retorno** | `G1 Z20.000` · `G1 X50.000 Z20.000` | **`G1 Z5.000`** · `G1 X50.000 Z5.000` |
| pasada 2 | `G1 Z-10` · `G1 X350 Z-10` | ídem |

⇒ **`SCS` sube a la cota de seguridad** (20) y vuelve por arriba. **`EP` sube mucho menos** y
vuelve casi rozando.

Y la altura del retorno de `EP` sigue una regla exacta, sobre los seis retornos del grupo:

| pasada | retorno |
|---|---|
| `Z-4` | `Z6` |
| `Z-5` | `Z5` |
| `Z-8` | `Z2` |

```
altura del retorno = cota de la pasada + 10        ⇒ SIEMPRE SUBE 10 mm
```

### 16.3 ⚠️ Pero ese 10 está CONFUNDIDO, y hace falta un fixture para separarlo

Dos candidatos, y los dos valen 10 en este lote:

1. **la profundidad total del fresado** (10 en todos estos archivos);
2. **`MillingRetractDistance` = 10**, de la ventana `Opciones` — el tercer origen.

El segundo encaja mejor por significado (*«cuánto se levanta la fresa entre pasadas»*), y si
es ése, **sería la primera vez que una opción de la aplicación llega a la TRAZA** — algo que A6
no pudo ver nunca porque midió sobre programas vacíos, donde no hay recorrido.

⇒ **Lo separa un solo fixture**: el mismo multipaso `EP` con **profundidad 14** en vez de 10.
Si el retorno sube 10, es `MillingRetractDistance`; si sube 14, es la profundidad. Va al
Grupo 15.

> ⚠️ **ACOTADO el 2026-09-08, y cambia a quién le importa.** El toolpath del `.pgmx` de
> `uni_EP_ph5` trae las pasadas **ya calculadas**, y el retorno está ahí adentro:
> `8 0 10 | 1 350 200 13 0 0 1` — un tramo vertical de **10**, escrito por Maestro. Y el único
> `10` del archivo entero es la `Depth`; **no hay ningún campo `MillingRetractDistance`**.
>
> ⇒ **El converter no tiene que escribir ese número: lo lee de la traza.** La regla 4 no está
> en juego para él.
>
> ⇒ **La pregunta sigue viva, pero es del SINTETIZADOR**, que sí tiene que generar la traza. Y
> la asimetría empuja hacia `MillingRetractDistance`: si el valor no vive en el `.pgmx` pero
> aparece en la traza, lo puso Maestro al calcularla — igual que hace con los defaults de
> `SecurityDistance` y `RadiusMultiplier` (§21.8). El fixture a profundidad 14 lo decide.

### 16.4 ⭐ El reparto de pasadas, y qué hace el `Último hueco`

| archivo | pasadas |
|---|---|
| `PH5` | `−5` `−10` |
| `PH4` | `−4` `−8` `−10` |
| `PH5 + UH2` | `−5` `−8` `−10` |
| `PH4 + UH2` | `−4` `−8` `−10` |

```
sin UH:  pasos de PH desde la superficie; la última pasada es el resto
con UH:  el desbaste llega hasta (profundidad − UH) con pasos de PH,
         y después una pasada final a la profundidad
```

⭐ **Control fino**: `uni_scs_ph4` y `uni_scs_ph4_uh2` son **byte-idénticos** salvo el nombre —
y también `bi_ph4` con `bi_ph4_uh2`. Con `PH4` sobre 10 el reparto ya termina en `−8` y `−10`,
así que pedir la pasada final no cambia nada. ⇒ **el `Último hueco` no agrega un movimiento
propio: sólo cambia dónde caen las pasadas.**

### 16.5 🐞 El bug de `StepDepth`: el ISO lleva `4·4·2`

Con `PH = 4` sobre profundidad 10 el ISO emite `Z-4`, `Z-8`, `Z-10` — o sea **4 + 4 + 2**, con
el resto en la última pasada. Es lo que decía la nota del 2026-09-03.

⇒ **La cadena `.pgmx` → ISO es consistente**: lo que el archivo guarda es lo que el ISO emite.
La divergencia que anotaste (`3,33 × 3`) es del **control al ejecutar**, no del postproceso.
Para el converter no hay nada que reproducir: emite `4·4·2` como Maestro.

### 16.6 ⭐⭐ El `Bidireccional` no vuelve en vacío

```
G1 Z-5.000   · G1 X350.000 Z-5.000      <- pasada 1, hacia +X
G1 Z-10.000  · G1 X50.000  Z-10.000     <- baja EN EL EXTREMO y vuelve cortando
```

⇒ No hay retorno: profundiza donde terminó y corta de vuelta. Por eso `bi_ph5` son **98**
líneas contra las 100/101 de los unidireccionales con las mismas pasadas.

⇒ Y por eso **`Conexión entre huecos` no existe para el bidireccional**: los cuatro `bi_*`
guardan `StrokeConnectionStrategy = Straghtline` sin que nadie lo haya elegido — es el valor
que queda cuando la sección no ofrece la opción. **Lo que el sintetizador ya hacía es correcto**
(fija `Straghtline` para bidireccional, helicoidal y contour-parallel), verificado contra los
cuatro fixtures.

### 16.7 ✅ La estrategia sin multipaso NO llega al ISO

`uni_scs` y `uni_ep` son **byte-idénticos al base** salvo la línea del nombre. Sin pasadas no
hay conexión que resolver, así que la elección no deja rastro.

⇒ **Negativo con testigo interno**: los `.pgmx` sí difieren (`StrokeConnectionStrategy`
`LiftShiftPlunge` contra `Straghtline`), así que esto no es un «no lo puse».

### 16.8 ⭐⭐ `Conexión entre huecos` = `StrokeConnectionStrategy`, y el mapeo del sintetizador es correcto

| la UI | el XML |
|---|---|
| `Salida a cota de seguridad` | **`LiftShiftPlunge`** |
| `En la pieza` | **`Straghtline`** |

Verificado contra el código: `_serialize_unidirectional_connection_mode` mapea
`SafetyHeight → LiftShiftPlunge` e `InPiece → Straghtline`, y **eso coincide con los
fixtures**. El default `Automatic` cae en `LiftShiftPlunge`, que es el modo seguro.

⚠️ **Pero `Automatic` no existe en la ventana** —la UI tiene dos radios, no tres— y nuestro
`_resolve_unidirectional_connection_mode` lo resuelve como *«perfil cerrado ⇒ `InPiece`»*. Esa
regla **no tiene fixture de la época nueva**, y elige justo el modo que dejó a la fresa
volviendo a 2 mm de la superficie. No es un defecto probado; es una decisión heredada que
conviene volver a anclar.

## 17. Correcciones a lo que escribí ayer

- ⚠️ **`ZigZag` NO es una estrategia que falte en el sintetizador.** Ayer escribí que no
  existía; **existe en el código** (`ZigZagMillingStrategySpec`, con toolpath propio que corta
  en rampa alternando el sentido). Lo que falta es otra cosa, y sigue importando: **no está en
  `docs/synthesize_pgmx_help.md`** —que documenta cuatro builders— y su única ancla es
  **`N025`, serie N, época congelada**. El fixture del Grupo 5 sigue haciendo falta, pero para
  **re-anclar**, no para agregar.
- ✅ **`AllowanceSide` y `AllowanceBottom` no tienen campo en la UI** — ayer salía de leer las
  capturas, hoy lo confirma Fermín directamente. Son campos del XML sin manera de tocarlos
  desde Maestro.

## 18. Lo que estos dos grupos dejan abierto

| | |
|---|---|
| ⭐ **el `10` del retorno `En la pieza`** | ¿profundidad total o `MillingRetractDistance`? Un fixture a profundidad 14 lo separa (§16.3) |
| el acortamiento de `IsPrecise` | derivado que **no** es la fórmula del disco; falta otra profundidad para afirmar que es el radio |
| ❓ la profundidad 18 de los `corr_len` | ¿la puso Fermín o la fuerza `IsPrecise`? |
| ❓ el `ActivateCNCCorrection = false` de los multipaso | 10 de 10 con multipaso en `false`, 2 de 2 sin multipaso en `true`. ¿Lo tocó Fermín o lo fuerza Maestro? |
| `Cutmode = Climb` | aparece en los quince, nunca variado. Sin campo identificado en la ventana |
| el modo largo con `Center` + `CAD` **sin** `IsPrecise` | el testigo directo de §15.3; hoy se deduce del par `corr_len` |
| `%DONTCARESPEEDV=1` | derivado su origen; falta decidir **qué hace el converter con ella** (`CLAUDE.md` §4) |

---

# Grupo 6 y los dos cierres del Grupo 4 (2026-09-08, cierre del día)

**27 archivos nuevos** —Fermín volvió a ampliar: pedí 6 y salieron 27, cruzando tipo × modo ×
multiplicador × lado— más los dos `corr_len` rehechos. Auditoría por atributo: **28 de 28**.

## 19. ✅ Los dos `corr_len`, ahora sí aislados

Fermín los rehízo a **profundidad 10** (los primeros habían quedado en 18 sin querer). Y el
resultado no se movió: la traza sigue yendo **de 52 a 348**.

```
acortamiento de «Corrección en longitud» = radio de la herramienta, por punta
```

⇒ **DERIVADO con dos profundidades** (10 y 18) y una herramienta. La fórmula del canal
—`√(p·(2r−p))`, el avance que un **disco** necesita para llegar a la cota— **no es de la
operación: era del disco.** Una fresa cilíndrica entra a pique y su borde llega hasta su
propio radio, sin importar cuánto baje.

Y de paso el par queda perfecto para §15.3: con la misma profundidad que el base,
`corr_len_CAD` (Center, `false`) sale en **modo largo** y `corr_len_CN` (Center, `true`) en
**modo corto**. El flag es lo único que cambia.

## 20. ⭐⭐ Con multipaso, la UI FUERZA `Corrección CAD`

**Dato de Fermín**: con el multipaso puesto, `Corrección C.N.` no se puede configurar — al
aceptar, **la ventana selecciona CAD sola**.

⇒ Contesta la pregunta que dejó §18: los diez archivos con multipaso tienen
`ActivateCNCCorrection = false` **porque Maestro lo impone**, no porque se haya tocado. Y con
testigo directo: la UI lo hace a la vista.

Tres consecuencias, y las tres son reglas duras para el converter:

1. **Multipaso ⇒ nunca hay `G41`/`G42`.** La compensación siempre queda resuelta en la traza.
2. **Multipaso ⇒ siempre modo largo** (§15.3), porque el modo largo lo enciende `false`.
3. **La combinación «multipaso + C.N.» no existe** y no hay que preverla — si un `.pgmx`
   llegara con las dos, es un archivo que Maestro no pudo haber producido.

## 21. Grupo 6 — el acercamiento y el alejamiento

Veintisiete archivos: `acercamiento`/`alejamiento` × `lineal`/`arco` × `bajada|subida`/`cota`
× multiplicador `1,5`/`2`/`4`, más el lado del arco (`automático`/`izquierdo`/`derecho`), el
solape, y dos con corrección para ver qué hace el `automático`.

### 21.1 ⭐⭐ El tamaño sale de `RadiusMultiplier × SVR` — diez puntos, exacto

| multiplicador | largo (lineal) | radio (arco) |
|---|---|---|
| `1,5` | **3** (`X47` / `X353`) | **3** (centro en `J203`) |
| `2` | **4** (`X46`) | **4** (`J204`) |
| `4` | **8** (`X42` / `X358`) | **8** (`J208`) |

```
largo del acercamiento lineal = radio del arco = RadiusMultiplier × SVR
```

Con la `E004` (`SVR` = 2). Vale igual para el acercamiento y el alejamiento.

⇒ **Los dos factores tienen procedencia**: `RadiusMultiplier` sale del `.pgmx` y `SVR` del
catálogo. Ni una constante interna. Y ojo con el nombre: la UI lo llama *multiplicador del
radio* y multiplica el **radio de la herramienta**, no el de un arco previo.

### 21.2 ⭐⭐ `Bajada`/`Subida` es una RAMPA; `Cota` son dos movimientos

| | acercamiento **lineal** | acercamiento **arco** |
|---|---|---|
| `Bajada` | `G1 X50.000 Z-10.000 F2000` — un solo movimiento **diagonal** | `G3 X50 Y200 **Z-10** I50 J208` — un solo movimiento **helicoidal** |
| `Cota` | `G1 Z-10.000` **y después** `G1 X50.000 Z-10.000` | `G1 Z-10.000` **y después** `G3 X50 Y200 I50 J208` (plano) |

Y el alejamiento, espejado:

| | lineal | arco |
|---|---|---|
| `Subida` | `G1 X358.000 **Z20.000**` — rampa de salida | `G3 X358 Y208 **Z20** I350 J208` — hélice de salida |
| `Cota` | `G1 X358.000 Z-10.000` y después `G1 Z20.000` | `G3 X358 Y208 I350 J208` y después `G1 Z20.000` |

⇒ **`Bajada`/`Subida` entra y sale cortando en rampa; `Cota` baja (o sube) recto y entra (o
sale) en el plano.** La diferencia en el ISO es exactamente **una línea**.

### 21.3 El arco es un CUARTO de círculo tangente

Para el acercamiento con `mr4`: arranca en `(42, 208)`, centro en `(50, 208)` —o sea `I`/`J` en
el **punto de inicio del corte desplazado el radio**—, y termina en `(50, 200)`, que es el
inicio. Noventa grados, tangente al recorrido.

Para el alejamiento: centro en `(350, 208)`, del final del corte hacia afuera, terminando en
`(358, 208)`.

### 21.4 ⭐⭐ El lado del arco, y por qué `Automático` va CRUZADO con la corrección

La UI ofrece **`Automático` · `Izquierdo` · `Derecho`** cuando el acercamiento es arco (dato de
Fermín, y los fixtures lo miden):

| | arco que emite | centro |
|---|---|---|
| `Derecho` | **`G3`** | `J208` (Y **+** radio) |
| `Izquierdo` | **`G2`** | `J192` (Y **−** radio) |
| `Automático` + `Center` | `G3` | `J208` |
| `Automático` + **`Corrección izquierda`** | `G3` | `J208` |
| `Automático` + **`Corrección derecha`** | `G2` | `J192` |

⇒ ⚠️⚠️ **`Automático` sigue a la corrección, pero al REVÉS del nombre**: `Corrección
izquierda` produce el arco del lado **`Derecho`**, y `Corrección derecha` el del
**`Izquierdo`**.

Físicamente es lo correcto —el arco tiene que entrar por el lado donde **no** está el material
que la fresa va a compensar—, pero es una trampa de nomenclatura de las que la regla 1 del
`CLAUDE.md` describe: **un converter que asuma `Left → Left` se equivoca de lado y la fresa
entra por donde no debe.** Queda escrito acá para que nadie lo derive de memoria.

Sin corrección, el default es el mismo que `Corrección izquierda`.

### 21.5 ⭐ El milímetro de `G41`/`G42` se recorre por la TANGENTE del primer movimiento

Con corrección **y** acercamiento, el ISO agrega un movimiento que sin acercamiento no está:

```
G0 X42.000 Y209.000                          <- posiciona 1 mm antes del arco
?%ETK[7]=4
G41
G1 X42.000 Y208.000 Z20.000 F2000.000        <- el milímetro, en −Y
G1 Z-10.000 F2000.000
G3 X50.000 Y200.000 I50.000 J208.000 F2000.000
```

El arco arranca en `(42,208)` con tangente en **−Y**, y el milímetro de entrada se recorre
**en esa misma dirección**. Sin acercamiento el arranque es en `+X` y el milímetro va en `X`
(`X49 → X50`, canal §21).

⇒ **El `1 mm` no es «en X»: es a lo largo de la tangente del primer movimiento del recorrido.**
Acota lo que el canal había dejado como una constante en X.

### 21.6 ⛔ El `Solape` no llega al ISO

`alej_arco_mr4_cota_solape5` es **byte-idéntico** a `alej_arco_mr4_cota` salvo la línea del
nombre, con `OverLap = 5` guardado en el `.pgmx`.

⇒ **Negativo con testigo interno**: el archivo prueba que la opción estaba puesta, así que
esto es *derivado*, no *probable*.

⭐ **Y no es un negativo raro: es el esperado.** Dato de Fermín (2026-09-08): **el solape sirve
en un fresado de trayectoria CERRADA — el trazo final se extiende más allá del punto final.**
Sobre una línea abierta no hay adónde extenderse, porque el punto final es el fin del
recorrido; en un contorno, el final coincide con el arranque y el solape lo pasa de largo para
que no quede la marca del punto de cierre.

⇒ **Predicción falsable para el fixture del contorno**: con `OverLap = 5` sobre el perímetro
`(0,0)-(400,400)`, el último tramo tendría que pasarse **5 mm** del punto de cierre — o sea
terminar en `X5.000` en vez de `X0.000` — y el ISO ganar cero líneas, porque es el mismo
segmento más largo. Si en cambio agrega un segmento aparte, el modelo es otro.

### 21.7 El bloque se reordena cuando hay acercamiento

Con acercamiento habilitado, el preámbulo pasa de `G40 · G40 · G40` a
**`G40 · G40 · ?%ETK[7]=0 · G40`**, y el `?%ETK[7]=4` se emite **antes** de todo el descenso
en vez de después de la bajada.

⇒ Coherente con lo que el marcador significa: **`?%ETK[7]=4` delimita el recorrido de
trabajo**, y el acercamiento forma parte de él.

### 21.8 📌 Dos detalles del `.pgmx` que conviene tener anotados

- **`Speed = -1`** en todos los acercamientos y alejamientos habilitados. Es el «sin
  especificar» de este bloque, como el `0` de `Technology/Feedrate`: el avance sale del
  catálogo. Y se ve en el ISO — el acercamiento usa `F2000` (`DescentSpeed`) y el alejamiento
  `F5000` (avance de corte).
- **`RadiusMultiplier = 1.2` es lo que el archivo trae mientras el bloque está deshabilitado.**

  > ⚠️ **CORREGIDO por Fermín (2026-09-08).** Acá decía que el `RadiusMultiplier` del `.pgmx`
  > y el de `UI00.exe.Config` eran «claves distintas». **Es la misma cosa**: el de la ventana
  > `Opciones` es **el valor que aparece por defecto en `Multipl. de radio` cuando se activan
  > el acercamiento o el alejamiento**. En esta máquina vale **4** — que es justo uno de los
  > tres multiplicadores del lote, seguramente el que quedó sin tocar.
  >
  > Lo que **sí** sigue en pie es la parte que le importa al converter: el valor **queda
  > escrito en el `.pgmx`** al activar la casilla, y el ISO sigue al archivo, no a la
  > configuración de la máquina que postprocesa.

### ⭐⭐ Y eso destapa un patrón: la ventana `Opciones` da DEFAULTS que se congelan en el archivo

Es el segundo caso, y con el mismo nombre de clave a los dos lados:

| clave de `UI00.exe.Config` | valor en esta máquina | dónde aparece en el `.pgmx` |
|---|---|---|
| `SecurityDistance` | 20 | `ApproachSecurityPlane` / `RetractSecurityPlane` = 20 (§4bis) |
| `RadiusMultiplier` | 4 | `Approach/RadiusMultiplier` al activar la casilla |

⇒ **El tercer origen actúa en la CREACIÓN del programa, no en el postproceso** — al menos para
las claves que tienen contraparte en el `.pgmx`. Con eso, la pregunta que A6 dejó abierta el
2026-08-09 —*«¿esas opciones afectan al `.pgmx` o al postprocesado?»*— tiene respuesta para
este par: **al `.pgmx`**.

⇒ Y convierte en firme lo que §4bis anotaba como *hipótesis*: **el converter no necesita leer
`UI00.exe.Config`** para emitir estos números. Los lee del archivo.

⚠️ **No se generaliza a las 175 claves**: `PostFileFormat` sí actúa en el postproceso (decide
el formato de salida), y de las 17 que A6 barrió, dieciséis no llegan al ISO por otra razón —
actúan en la etapa 1. Lo derivado acá es el patrón de **las que tienen campo espejo en el
`.pgmx`**.
- ⚠️ Los archivos `alej_*` conservan el bloque `Approach` del archivo del que partieron
  (`Arc`/`Quote`/`Left`/`4`) con `IsEnabled = false`. **Los valores sobreviven al
  deshabilitar**, y el ISO no los usa: buen control de que `IsEnabled` es lo que manda.

## 22. Lo que queda abierto después del Grupo 6

| | |
|---|---|
| ⭐ **el `10` del retorno «En la pieza»** | sigue siendo el pendiente caro: ¿profundidad o `MillingRetractDistance`? Grupo 15 |
| ~~la profundidad 18 de los `corr_len`~~ | ✅ **cerrado**: era un cambio involuntario, ya rehechos a 10 |
| ~~el `ActivateCNCCorrection` de los multipaso~~ | ✅ **cerrado**: lo fuerza la UI (§20) |
| el `Solape` en un **contorno cerrado** | ⭐ Fermín explicó para qué es: **extiende el trazo final más allá del punto final**. Sobre una línea abierta no hay adónde extenderse ⇒ el negativo era el esperado. Fixture pedido con predicción (§21.6) |
| el lado del arco con **corrección + `Izquierdo`/`Derecho` explícitos** | hoy el cruce se derivó con `Automático`; falta ver si el explícito ignora la corrección |
| `Cutmode = Climb` | sigue sin campo identificado en la ventana |

---

# 23. Grupo 7 — la cota de seguridad, y el tercer origen queda cerrado (2026-09-09)

**Dos archivos, y valen por dos experimentos.** Fermín no sólo varió la `Cota de seguridad` del
programa: **cambió a la vez las Opciones de Maestro, y las cruzó**, dejando una captura de la
ventana por cada postproceso.

| archivo | `Cota de seguridad` (del programa) | `Distancia de seguridad` (Opciones) | `Paso de retroacción` (Opciones) |
|---|---|---|---|
| `cota_seguridad_30` | **30** | **20** | 10 |
| `cota_seguridad_25` | **25** | **30** | 15 |

Los dos valores van **al revés uno del otro**: el archivo que pide 30 se postprocesó con la
opción en 20, y el que pide 25 con la opción en 30. Es exactamente lo que hace falta para
separar quién manda.

## 23.1 ✅ La cota de seguridad, derivada con variación aislada

| archivo | `Cota` | aproximación | salida |
|---|---|---|---|
| base | 20 | `G0 Z115.000` | `G0 Z20.000` |
| `_25` | 25 | `G0 Z120.000` | `G0 Z25.000` |
| `_30` | 30 | `G0 Z125.000` | `G0 Z30.000` |

```
Z de aproximación = ToolOffsetLength + Cota de seguridad
Z de salida       = Cota de seguridad
```

⇒ **Tres valores sobre la misma herramienta**, y el diff entre `_25` y `_30` son **exactamente
dos líneas**: la cota de seguridad no toca nada más del bloque. Lo que §4bis había derivado con
un par que movía tres cosas a la vez, ahora está aislado.

Y el `.pgmx` lo confirma del otro lado: la curva `Approach` arranca en `espesor + cota`
(`Z38`, `Z43`, `Z48`) y mide `cota + profundidad` (30, 35, 40).

📌 **Un solo campo escribe los dos del XML.** `ApproachSecurityPlane` y `RetractSecurityPlane`
valen lo mismo en los tres archivos, porque la ventana tiene **una** `Cota de seguridad` en
`Datos avanzados` (§13). Cuál gobierna cada cota sigue sin poder separarse con archivos que
Maestro produzca — y ya no importa: se mueven juntos siempre.

## 23.2 ⭐⭐⭐ Y el cruce cierra el TERCER ORIGEN: la ventana `Opciones` NO se lee al postprocesar

Esta es la parte grande, y contesta una pregunta abierta desde el 2026-08-09.

- El archivo con `Cota de seguridad = 30` se postprocesó con `Distancia de seguridad = 20`
  ⇒ el ISO emitió **`Z125` y `Z30`**: siguió al **archivo**.
- El archivo con `25` se postprocesó con la opción en **30** ⇒ el ISO emitió **`Z120` y `Z25`**:
  siguió al **archivo** otra vez, y esta vez el valor de la opción era **mayor**, así que no
  hay forma de confundirlo con un mínimo o un tope.

```
Distancia de seguridad desde la mesa de trabajo  ->  SOLO el default al crear la operación
Cota de seguridad (Datos avanzados del programa) ->  lo que el ISO usa
```

⇒ ⭐ **`SecurityDistance` no se lee al postprocesar.** Y con **testigo**: las dos capturas
registran el valor exacto de la ventana en cada postproceso, así que este negativo es
**derivado**, no «probable» (`fixtures.md` §4).

### Qué pendientes cierra

- ✅ **El «experimento de las dos PCs»** que `configuracion_aplicacion.md` tenía planteado desde
  el 2026-08-09 —*«el mismo `.pgmx` postprocesado dos veces con una opción cambiada en el
  medio; si el ISO difiere, es postproceso»*— **está hecho, y da que NO es postproceso.** Y
  salió más barato de lo previsto: no hizo falta una segunda máquina.
- ✅ **La hipótesis de §4bis pasa a derivada.** Ahí se suponía que el `30` de los fixtures
  heredados venía de una PC con `SecurityDistance = 30` congelado en el archivo. Es
  exactamente el mecanismo, ahora medido.
- ✅ **Y confirma el patrón de §21.8** con su segundo caso probado: la ventana `Opciones` da
  **defaults que Maestro congela en el `.pgmx`** al crear la operación. El tercer origen actúa
  en la **creación**, no en la emisión.

⇒ **Para el converter**: no necesita `UI00.exe.Config` para la cota de seguridad ni para el
multiplicador del radio. Los lee del `.pgmx`. Es un origen menos que consultar en dos de los
tres números que lo preocupaban.

⚠️ **Sigue sin generalizarse a las 175 claves.** `PostFileFormat` decide el formato de salida y
sí actúa en el postproceso. Lo derivado vale para **las claves con campo espejo en el `.pgmx`**.

## 23.3 ⭐⭐ `MillingRetractDistance` tiene nombre en español, y el pendiente del `10` se abarata

Las capturas dan la traducción de la ventana, que hasta hoy sólo teníamos como clave en inglés:

| clave de `UI00.exe.Config` | en la ventana `Opciones > Parámetros` |
|---|---|
| `SecurityDistance` | **Distancia de seguridad desde la mesa de trabajo** |
| `MillingRetractDistance` | **Paso de retroacción en los fresados** |
| `RadiusMultiplier` | **Multiplicador del radio en aproximaciones/alejamientos** |
| `RapidFeed` | **Velocidad rápida en los desplazamientos** |

⇒ ⭐ **«Paso de retroacción en los fresados» describe literalmente el retorno entre pasadas**,
que es donde apareció el `10` sin procedencia (§16.3). El nombre no lo prueba, pero apunta
derecho.

⚠️ **Y estos dos archivos NO lo contestan**: no tienen multipaso, así que no hay retorno donde
se vea — aunque el valor pasó de 10 a 15 entre los dos postprocesos.

⇒ **El fixture que lo resuelve cambia, y se vuelve más directo.** Si `MillingRetractDistance`
se comporta como sus dos hermanas —default congelado al crear—, entonces **no alcanza con
postprocesar de nuevo**: hay que **crear** el fresado con la opción ya cambiada.

```
Poner «Paso de retroacción en los fresados» = 15, y RECIÉN AHÍ crear un
uni_EP_ph5 nuevo. Si la traza guardada trae «8 0 15» donde el actual trae
«8 0 10», es MillingRetractDistance. Si sigue en 10, es la profundidad.
```

Y se ve **sin postprocesar**, leyendo el `.pgmx`. El fixture a profundidad 14 sigue valiendo
como control cruzado, pero éste ataca la variable por su nombre.
