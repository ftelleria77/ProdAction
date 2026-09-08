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
