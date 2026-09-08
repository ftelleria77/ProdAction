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
