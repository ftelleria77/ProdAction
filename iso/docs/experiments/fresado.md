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
>
> 🔄 **Grupo 8, la matriz de cambios de herramienta** (§24): 56 archivos —las siete fresas ×
> las siete, más canal y taladro—, **auditados 56 de 56 y todavía sin postprocesar**. Las
> predicciones están escritas antes del ISO, y hay **tres cosas para arreglar primero**: el
> canal quedó a profundidad 0 y dos pares de archivos son duplicados exactos.
>
> ✅ **Y el Grupo 8 cerró el mismo día** (§24.6): Fermín corrigió las tres cosas y postprocesó
> los **54**. De las siete predicciones, **seis se cumplen** —incluido el `71` exacto de la
> diagonal y los 98 bloques explicados por el catálogo— y **una se cae**: la matriz **no es
> simétrica**, porque el bloque cambia de forma según vaya primero o segundo. Las **tres
> transiciones** quedan medidas, y la de cabezal es **idéntica para el canal y para el
> taladro**.
>
> ⭐⭐⭐ **Grupo 9 — y una técnica de oficio que cambia el planteo** (§25): el fresado en el
> canto **no se pide en el canto** (los dos `front` no postprocesan). Se dibuja una polilínea
> en la cara **superior** que entra y sale **fuera de la pieza**, y el **diámetro** de la
> Sierra Horizontal hace el surco lateral — con la bajada en Z siempre al aire. Y el ISO que
> sale es **un fresado normal**: el converter no necesita nada nuevo, pero **no puede exigir
> que la traza caiga dentro de la pieza**. Además, **cuarto caso de fail-loud**: la cara
> inferior se descarta en silencio, aunque esta vez **deja dos líneas de rastro**.
>
> 🚨 **Grupo 10 — el `G41`/`G42` no sale de una tabla** (§26). Fermín cruzó `Invertir` con las
> tres correcciones, y aparece que **el código de compensación se deriva de `SideOfFeature`
> JUNTO CON el sentido de recorrido**: `Right` invertido emite `G41`, no `G42`. Un converter
> que use una tabla fija desde el lado **come del lado equivocado en todo mecanizado
> invertido**. Y los dos silencios resultan distinguibles: `Condición = False` no deja rastro,
> el descarte de la cara inferior sí.
>
> ⭐⭐⭐ **Grupos 11 a 13** (§27-§29). El `Xmsg` movido de lugar prueba que **el conteo sólo
> mira lo emitido ANTES** —intercalado y simple dan el mismo 422— y que el `M5` es
> **condicional**; pero **la fórmula no sale del ISO**, lo que acota lo que el canal había
> derivado. Y en el barrido A5 aparece el **primer parámetro de máquina que toca la traza**:
> el **espejo tecnológico**, que con la sierra no se veía porque el disco normaliza el sentido.
> Las microuniones quedan postergadas (no se pueden aplicar todavía).
>
> ⭐⭐⭐ **Grupo 14** (§30): los **tres atributos de la cinta son un solo mecanismo** —
> `SpeedAttribute` tiene la forma exacta del de profundidad y parte la traza igual—, y el
> **offset exterior de un contorno REDONDEA las esquinas** con el radio de la fresa: el
> toolpath tiene ocho elementos donde la geometría tiene cuatro. Además `Invertir` en un
> cerrado invierte el **giro** conservando el arranque, y el **arranque en el punto medio de
> un lado** (aporte de Fermín) cierra la regla de emisión de ejes con el caso que faltaba.
>
> ⭐⭐⭐ **Grupos 15 y 16** (§31-§32): **el `10` del retorno es `MillingRetractDistance`** — con
> la opción en 15 y profundidad 12 sube **15**, y los dos candidatos quedan separados; el
> **`Solape` prolonga el último tramo** en su dirección, independiente del radio del lead. Y
> §33 hace el **inventario de lo que queda abierto**: catorce puntos, de los cuales **tres
> deciden código** y el grupo final propuesto son **9 archivos**.
>
> ⭐⭐⭐ **2026-09-11 — Grupo 18, el final** (§34): **el espejo tecnológico NO espeja, invierte**
> —byte-idéntico a `Invertir`— **pero la traza guardada no lo refleja**, así que el converter
> tiene que aplicarlo él. El arco de esquina **escala con `SVR` sin degenerar** ni con la
> `E001` en 50×50; el lado del arco **explícito ignora** la corrección; el `ZigZag` queda
> **re-anclado**; y en un contorno **cerrado no hay retorno entre pasadas**. Cinco puntos del
> inventario cerrados.

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

### ⚖️ DECIDIDO (Fermín, 2026-09-10): es un BUG de Maestro, y es la línea que paró el CNC

⇒ **El converter la OMITE siempre**, y ahora **sabe exactamente cuándo Maestro la habría
emitido** —«Salida a cota de seguridad» con multipaso— en vez de descubrirla comparando. La
omisión deliberada ya existía (`DELIBERATE_OMISSIONS`); lo que faltaba era el gatillo.

### ⭐⭐⭐ Y con eso se unifican los dos incidentes de julio y agosto

Eran el mismo bug visto desde dos lados, y hasta hoy figuraban como cosas distintas:

| | |
|---|---|
| **2026-07-30** — la máquina **se detuvo con error** a mitad del primer fresado, y la causa estaba en el **segundo**: un fresado lineal **unidireccional** con la `E004` y `Conexión entre huecos` en **«Salida a cota de seguridad»** (`incidentes.md` de la Pratix) | ⇒ **es exactamente la configuración que emite la línea** |
| **2026-08-03** — el ISO de Maestro **aborta** con `Alarma 67: Assegnazione a registro inesistente` por `%DONTCARESPEEDV=1`, y el nuestro —que la omite— **corre** (`iso_first_machine_run`) | ⇒ **es la misma línea**, ya identificada pero sin saber qué la disparaba |

⇒ Y explica el detalle que el registro del incidente dejó como raro: **por qué frenó en el
PRIMER fresado si la causa estaba en el segundo**. 🔮 Hipótesis (no derivada): el control
**pre-lee** el programa, así que el intérprete llega a la línea inválida mientras la máquina
todavía está ejecutando movimientos anteriores del buffer.

❓ **Una pregunta chica que cerraría el encaje**: el registro del 07-30 no dice si ese segundo
fresado tenía **multipaso**. Los fixtures muestran que la línea aparece con SCS **y** multipaso,
y **no** con SCS sin pasadas. Si tenía multipaso, el encaje es completo.

### ⭐⭐ Y aparece un beneficio concreto del converter sobre Maestro

El workaround que se usó en la máquina fue pasar ese fresado a **«En la pieza»** — y eso
**cambia la trayectoria**: el retorno entre pasadas deja de ir a la cota de seguridad y sube
sólo `MillingRetractDistance` (§31), o sea **la fresa vuelve mucho más abajo, casi rozando**.
Se evitó el aborto a costa de un recorrido menos seguro.

⇒ **El converter puede tener las dos cosas**: emitir el programa con «Salida a cota de
seguridad» —el retorno alto, seguro— **y sin la línea del bug**. Es el primer caso donde el
converter no sólo iguala a Maestro sino que **produce un programa mejor que el que Maestro
puede producir**.

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

---

# 24. Grupo 8 — la matriz de cambios de herramienta (2026-09-09)

**56 archivos, y todavía sin postprocesar.** Fermín lo llevó mucho más lejos de lo pedido: en
vez de los cuatro casos del pedido, armó **la matriz 7×7 completa** de fresas más las
combinaciones con canal y con taladro.

⚠️ **Esta sección se escribe ANTES del ISO**, con la auditoría del `.pgmx` y las predicciones.
Es el mismo orden que funcionó en el canal, donde la configuración dio nueve predicciones
falsables y el primer archivo acertó ocho de ocho.

## 24.1 Qué hay, leído del archivo

Todos en campo `A`, pieza de siempre, dos fresados **paralelos** —`Y150` y `Y250`, de `X50` a
`X350`, profundidad 10— salvo donde se diga.

| bloque | n | qué es |
|---|---|---|
| **matriz de fresas** | **49** | las siete `E00x` × las siete, en orden: `Fresado 1 - EAAA` + `Fresado 2 - EBBB` |
| — de esas, la **diagonal** | 7 | la misma fresa dos veces (`dos_paralelos`) |
| — fuera de la diagonal | 42 | dos fresas distintas (`dos_fresas`) |
| **con canal** | 2 | fresado `E001` en `Y150` + canal `082` en `Y250` (de `X100` a `X350`), en **los dos órdenes** |
| **con taladro** | 3 | fresado `E001` + agujero **Ø8, profundidad 15, en (100,100)**, en los dos órdenes |
| base | 1 | el mínimo del lote |

⭐ **Y el `.pgmx` trae un dato que no habíamos usado**: Maestro **nombra y numera los pasos del
workplan con su herramienta** — `Fresado 1 - E001`, `Canal 2 - 082`, `Taladrado 1 - D8P`. Es un
segundo lugar donde el archivo afirma qué hace, y sirve para auditar sin leer el `ToolKey`.

## 24.2 ✅ Auditoría: 56 de 56

Leyendo el **orden del workplan** —no el de `<Operations>`, que es un catálogo (`perforado.md`)—
los 56 nombres coinciden con lo que el archivo dice: herramientas correctas y en el orden que
el nombre afirma. Con 49 combinaciones de dos herramientas hechas en una hora, era el lote con
más riesgo de un «guardar como» pisado, y no ocurrió.

## 24.3 ⚠️ Tres cosas para arreglar ANTES de postprocesar

Son 56 postprocesos; conviene no gastarlos en balde.

### ⛔ El canal quedó a profundidad 0

Los dos archivos con canal tienen el `SlotSide` con `Depth.StartDepth = EndDepth = **0**`. En
el lote D2 el canal mínimo llevaba **10**.

El `0` es el **estado neutro** que Maestro guarda cuando la operación se creó y todavía no
tiene profundidad efectiva. Un canal a profundidad 0 no corta nada, así que el ISO puede salir
sin el bloque del canal — y entonces **estos dos fixtures no medirían la transición entre
cabezales, que es justamente lo que el par tiene que decidir**.

⇒ **Ponerle profundidad 10 al canal** en los dos archivos antes de postprocesar. (Y si se
postprocesan igual, el resultado es dato de todos modos: diría qué hace Maestro con un
mecanizado de profundidad nula.)

### 📌 Dos pares de archivos son duplicados exactos

Verificado comparando el XML entero, no el nombre:

| | |
|---|---|
| `E001_D8P_fresado_taladro` | **XML idéntico** a `E001_top_D8P_fresado_taladro_top` (953 líneas, diff vacío) |
| `E004_dos_paralelos` | **XML idéntico** a `E004_E004_dos_paralelos` (1008 líneas, diff vacío) |

⇒ **Son 54 programas distintos, no 56.** No contamina nada —un duplicado no puede contradecir
a nadie—, pero son dos postprocesos que no hacen falta. Si la intención del `_top_` era poner
el taladro en una cara **distinta** de la superior, ese archivo está sin hacer.

## 24.4 Las predicciones

Todo lo de abajo sale de lo ya derivado, y cada línea es falsable.

### La diagonal (misma fresa dos veces) — 7 archivos

| | |
|---|---|
| `T n` · `SYN` · `M06` | **UNO solo** — el texto de once contornos (§12.5) y `dos_fresados_una_geometria` ya lo mostraron |
| `D1` · `SVL` · `SVR` · `G1 Z-10` · `?%ETK[7]=4` · `G0 Z20` | **dos veces**, uno por operación |
| `G0 Z<SVL+20>` | **una sola vez** |
| entre las dos | `G17` · `MLV=2` · tres `G0` con **X, Y y Z combinados** |
| líneas que agrega | **71** contra el programa vacío (lo que dio `dos_fresados_una_geometria`, que también son 2 operaciones y 2 segmentos) |

### Fuera de la diagonal (dos fresas) — 42 archivos

| | |
|---|---|
| `T` · `SYN` · `M06` | **DOS veces**, una por herramienta ⇒ el bloque de transición es más largo que en la diagonal |
| los números de cada bloque | del catálogo, uno por fresa: `T` = `?%ETK[9]` = `shStorePos`, `SVL` = `ToolOffsetLength`, `SVR` = radio del cuerpo, `S` = `SpindleSpeed.Standard`, `F` = `FeedRate.Standard × 1000`, bajada = `DescentSpeed × 1000`, aproximación = `SVL` + 20 |
| `?%ETK[7]` | **4 en los dos bloques** — las catorce herramientas son del electromandril |
| la matriz | **simétrica en contenido**: `EAAA_EBBB` y `EBBB_EAAA` tienen que dar los mismos dos bloques **en orden invertido** |

⇒ Si los 42 se explican con el catálogo, **el cambio de herramienta queda cerrado con 49
casos** y no hará falta volver sobre él en ningún mecanizado posterior.

### Con canal — 2 archivos

El canal con `082` va por el **cabezal perforador** y el fresado por el **electromandril**
(`canal.md` §19), así que este par es la **transición entre cabezales**:

| | |
|---|---|
| bloque del canal | `?%ETK[6]=82` · `?%ETK[1]=16` · `?%ETK[7]=**1**` · **sin** `T`/`SYN`/`M06` · `SHF` `-96 / 126.95 / 22.15` · `S4000M3` · `G4F1.200` |
| bloque del fresado | `T1` · `SYN` · `M06` · `?%ETK[7]=**4**` · `SHF` `32.05 / -246.65 / -125.30` |
| entre los dos | **`G0 G53 Z201.000`**, como la transición canal → taladro del canal §16 — aunque acá las dos herramientas viven en cabezales distintos, no en el mismo |
| el orden | el ISO respeta el **orden del workplan**, en los dos sentidos |

⚠️ Con el canal en profundidad 0, es probable que no salga nada de esto.

### Con taladro — 3 archivos (2 distintos)

| | |
|---|---|
| bloque del taladro | `?%ETK[7]=**3**`, herramienta **resuelta automáticamente** por diámetro y punta — el `ToolKey` viene **vacío** en el archivo, como en el perforado |
| Ø8 y profundidad 15 | el ISO tiene que bajar a `Z-15` |
| la transición | `G0 G53 Z201.000` entre el electromandril y el cabezal perforador |
| el orden | los dos sentidos están, y tienen que salir invertidos |

## 24.5 Lo que este grupo cierra si las predicciones se cumplen

- **el cambio de herramienta entre fresas**, con las 49 combinaciones;
- **la transición entre cabezales** en los dos sentidos y con dos vecinos distintos (canal y
  taladro);
- y el **costo en líneas de una segunda operación**, que hoy tiene un solo punto (71, de
  `dos_fresados_una_geometria`) y que la regla `50 + N segmentos` no cubre para varias
  operaciones (§12.1).

## 24.6 ✅ Resultados — los 54 postprocesados (2026-09-09)

Fermín corrigió la profundidad del canal y borró los dos duplicados: **54 pares**, todos con
ISO. Contra las predicciones de §24.4, **seis de siete se cumplen y una se cae**.

### ✅ El cambio de herramienta, cerrado con 49 combinaciones

| | predicho | medido |
|---|---|---|
| diagonal (misma fresa): `T`/`SYN`/`M06` | **uno solo** | ✅ **7 de 7** |
| diagonal: líneas que agrega | **71** | ✅ **71**, en las siete |
| fuera de la diagonal: `T`/`SYN`/`M06` | **dos** | ✅ **42 de 42** |
| fuera de la diagonal: líneas | — | **86**, en las 42 |
| `D1` / corrector | uno por operación | ✅ **2** en las 49 |
| `?%ETK[7]=4` | en los dos bloques | ✅ **42 de 42** |
| todos los números, del catálogo | `T` · `SVL` · `S` · aproximación · `F` corte · `F` bajada | ✅ **98 bloques comprobados, 0 discrepancias** |

⇒ **Ninguna de las 49 combinaciones introduce un número que no venga de `def.tlgx`.** El
cambio de herramienta entre fresas queda cerrado; no hay que volver sobre él en los mecanizados
que faltan.

### ⭐⭐ El costo en líneas de una segunda operación, con fórmula

```
1 fresado                        51        (= 50 + 1 segmento)
+ 1 fresado con la MISMA fresa   +20   ->  71
+ 1 fresado con OTRA fresa       +35   ->  86
                                  ⇒ el cambio de herramienta cuesta 15 líneas
```

El `71` coincide con `dos_fresados_una_geometria` (§12.1), que también son dos operaciones de
un segmento con la misma fresa — pero sobre **una sola** geometría. ⇒ el costo **no depende de
si comparten la geometría**.

### ⭐⭐ Las tres transiciones, medidas

**Misma fresa — 5 líneas.** No baja a la cota de cambio ni para el husillo: se mueve por
arriba, a la cota de aproximación.

```
G17 · MLV=2
G0 X350.000 Y150.000 Z145.400     <- desde donde terminó
G0 X50.000  Y250.000 Z145.400     <- al inicio del siguiente
G0 X50.000  Y250.000 Z145.400     <- ⚠️ REPETIDA, idéntica a la anterior
```

⚠️ **El tercer `G0` está repetido** — el mismo destino dos veces. Ya había aparecido en
`dos_fresados_una_geometria` y ahora se confirma en las siete de la diagonal: **es sistemático,
no un accidente**. El converter tiene que emitirlo para el byte-idéntico.

**Otra fresa — 13 líneas.** Cierra el corrector, sube a la cota de cambio, **para el husillo**,
vuelve a subir, y recién ahí cambia:

```
?%ETK[7]=0 · G0 Z20.000 · D0 · SVL 0 · VL6=0 · SVR 0 · VL7=0
MLV=0 · G0 G53 Z201.000 · MLV=2 · ?%ETK[13]=0 · ?%ETK[18]=0
M5                                 <- para el husillo
MLV=0 · G0 G53 Z201.000            <- el G53 va DOS veces
MLV=0 · T2 · SYN · M06 · ?%ETK[9]=2 · ?%ETK[18]=1 · S6000M3 · G17 · MLV=2 · ?%ETK[13]=1
```

**Otro cabezal — 15 líneas**, y ⭐⭐ **es IDÉNTICA para el canal y para el taladro**:

```
G0 Z20.000 · D0 · SVL 0 · VL6=0 · SVR 0 · VL7=0
?%ETK[7]=0 · ?%ETK[8]=1 · G40
MLV=0 · G0 G53 Z201.000 · MLV=2
G61                                <- parada exacta
MLV=0 · ?%ETK[13]=0 · ?%ETK[18]=0
G0 G53 Z201.000
G64                                <- vuelve a corte continuo
```

⇒ **La transición la decide el CABEZAL, no la operación que sigue.** Es la misma regla que
`canal.md` §19 derivó para el bloque: **manda la herramienta**. Recién después de `G64` los dos
divergen — el canal emite `?%ETK[6]=82` · `?%ETK[17]=257` · `S4000M3` · `?%ETK[1]=16` y el
`SHF` de la sierra; el taladro, `MLV=1` · `SHF[Z]=0.000+%ETK[114]/1000`.

📌 **Y la diferencia entre las dos**: entre fresas hay **`M5`** y no hay `G61`/`G64`; entre
cabezales hay **`G61`/`G64`** y `?%ETK[8]=1`/`G40`, y **no hay `M5`**.

### ❌ La predicción que se cae: la matriz NO es simétrica

Predije que `EAAA_EBBB` y `EBBB_EAAA` darían **los mismos dos bloques en orden invertido**.
**No pasa en ninguno de los 21 pares.** El bloque de una herramienta mide 48 líneas cuando va
primero y 56 cuando va segundo.

⇒ **La forma del bloque depende de la POSICIÓN**, no sólo de la herramienta:

- el **primero** trae el preámbulo del programa — `?%ETK[6]=1` y los dos bloques de origen
  (`%Or[0].of*` y `SHF`), que no se repiten;
- el **segundo** trae la transición y una selección más corta: **no repite `?%ETK[6]`** ni el
  origen.

⇒ Para el converter: **no hay un «bloque por herramienta» reutilizable**. Hay un bloque de
apertura y un bloque de continuación, y la herramienta sólo decide los números de adentro. Era
lo que la predicción daba por sentado y el lote lo refuta.

📌 **Mi error, para el registro**: la predicción salió de que los dos bloques tienen los mismos
*números*, y confundí eso con que tuvieran las mismas *líneas*. Los 42 archivos lo dicen desde
el largo total —86 en todos, no 84 ni 88—, que ya avisaba que hay algo fijo además de las dos
operaciones.

### 📌 Y el orden cuesta distinto cuando hay dos cabezales

| | canal primero | fresado primero |
|---|---|---|
| con canal `082` | **94** | **95** |

| | taladro primero | fresado primero |
|---|---|---|
| con taladro `D8P` | **84** | **82** |

⇒ Los dos pares difieren, y **no en el mismo sentido**: con el canal empezar por la sierra sale
una línea más corto, con el taladro empezar por la broca sale dos más largo. Sin explicación
todavía; queda anotado como observación, no como regla.

---

# 25. Grupo 9 — la cara, y la técnica para ranurar el canto (2026-09-09)

Cuatro archivos: los tres del pedido —de los cuales **sólo el `bottom` postprocesó**— y **uno
que agregó Fermín**, que es el que cambia el panorama.

Los cuatro tienen la `Cota de seguridad` en **30**, porque se crearon después de poner la
opción de Maestro en 30 (Grupo 7). 📌 Es un testigo más del patrón de §23.2: **el default de
la ventana queda congelado en los archivos nuevos**, y se ve en el ISO (`G0 Z137.000` =
`SVL 107` + 30, salida `G0 Z30.000`).

## 25.1 ⛔ Cuarto caso de fail-loud: la cara inferior — pero deja rastro

`bottom_E004` **sí postprocesa**, y el ISO son **45 líneas**. Contra el programa vacío (43):

```
1c1
< % r_pv_a_manual_perf.pgm
> % r_pv_a__fresado_bottom_e004.pgm
19a20,21
> ?%ETK[8]=1
> G40
```

**El fresado no está**: ni `T`, ni `M06`, ni `SVL`, ni un solo `G1` de corte. Maestro **descarta
en silencio** el mecanizado de la cara inferior, igual que con el perforado — el caso que hizo
escribir la excepción de fail-loud del `CLAUDE.md` §4.

⇒ 🚨 **Cuarto caso de fail-loud del converter**, y el segundo de esta clase (mecanizado que
desaparece sin aviso). La pieza sale sin el surco y nadie se entera.

### ⭐ Pero acá hay un matiz que el perforado no tenía

En el perforado el ISO salía **idéntico** al vacío: el descarte era **indetectable** desde el
archivo emitido. Acá quedan **dos líneas**, `?%ETK[8]=1` y `G40`, que son **el preámbulo del
bloque de fresado** — el mismo que en un fresado normal aparece tres veces.

⇒ **Maestro empieza a emitir el bloque y lo abandona.** Hay un testigo en el ISO: un preámbulo
de fresado sin bloque detrás.

⇒ Para el converter esto **no cambia la decisión** —rechaza igual, por la regla 4—, pero sí
significa que un ISO de Maestro con ese patrón se puede **diagnosticar** sin tener el `.pgmx` al
lado.

## 25.2 ⛔ El fresado directo en el canto no postprocesa

`front_E004` y `front_E002` piden el mismo recorrido sobre la **cara delantera** —una línea en
`(50, 9) → (350, 9)`, o sea a media altura del canto— y **ninguno de los dos produce ISO**.

⇒ Confirma para el fresado lo que `canal.md` §15 había derivado para el canal: **el canto no se
mecaniza pidiéndolo en el canto**. Vale tanto para una fresa del electromandril como para la
Sierra Horizontal.

## 25.3 ⭐⭐⭐ La técnica que sí funciona: el surco en el canto se pide desde la cara SUPERIOR

**Aporte de oficio de Fermín**, y es la forma real de hacerlo en producción.

En vez de pedir el mecanizado en la cara delantera, se dibuja **a mano una polilínea en la cara
superior** que entra y sale **fuera de la pieza**, y se deja que el **diámetro** de la sierra
horizontal haga el trabajo lateral:

```
tramo 1:  (50, −60) → (50, −40)     entra 20 mm hacia la pieza, por afuera
tramo 2:  (50, −40) → (350, −40)    el surco, a lo largo del canto
tramo 3:  (350, −40) → (350, −60)   sale 20 mm, otra vez hacia afuera
```

Con la **`E002`** (Ø100, radio 50) y profundidad 7:

| el eje de la sierra en | el filo llega a | qué pasa |
|---|---|---|
| `Y = −60` | `Y = −10` | **10 mm antes del borde**: la bajada vertical es **al aire** |
| `Y = −40` | `Y = +10` | **penetra 10 mm** en el canto |

⇒ **La bajada en Z ocurre siempre fuera de la pieza**, que es lo que hace la técnica viable: un
disco de Ø100 no puede entrar a pique en el material.

⇒ Y el ISO lo confirma línea por línea:

```
G0 X50.000 Y-60.000        <- posiciona AFUERA de la pieza
G0 Z137.000                <- SVL 107 + cota 30
G1 Z-7.000 F2000.000       <- baja al aire
?%ETK[7]=4
G1 Y-40.000 Z-7.000 F3000.000    <- penetra
G1 X350.000 Z-7.000 F3000.000    <- el surco
G1 Y-60.000 Z-7.000 F3000.000    <- sale
G0 Z30.000                       <- sube afuera
```

### ⭐⭐ Y lo mejor para el converter: no hay nada nuevo que emitir

El bloque es **un fresado normal**: `?%ETK[7]=4`, electromandril, `D1`/`SVL 107`/`SVR 50`, y
**96 líneas = 43 + 53**, que es `50 + 3 segmentos` — la misma regla de §12.1.

⇒ **El «surco en el canto» no es una familia de emisión ni una operación especial: es
geometría.** Todo lo que el converter necesita ya está derivado.

⚠️ **Con una condición que sí hay que respetar: la traza sale de la pieza.** Los tres tramos
viven en `Y` **negativa**, fuera del borde. Un converter que valide «la traza tiene que caer
dentro de la pieza» rechazaría un programa correcto y de uso corriente.

📌 **Y una consecuencia de método**: la cara de un mecanizado **no se puede leer de la cara del
plano**. Este programa dice `Top` y produce un surco en el **canto delantero**. Lo que decide
qué superficie se trabaja es la **geometría más el diámetro de la herramienta**, no la
declaración del plano.

---

# 26. Grupo 10 — `Invertir`, `Condición`, y el `G41`/`G42` que no sale de una tabla (2026-09-10)

Nueve archivos en vez de los tres del pedido: Fermín **cruzó la inversión con las tres
correcciones** y extendió el cruce a los `condicion_false`. Y el cruce es lo que destapa el
hallazgo — con los tres archivos sueltos no se veía.

| | base | `_invertir` | `_condicion_false` |
|---|---|---|---|
| `corr_central` | ✅ | ✅ | ✅ |
| `corr_derecha` | ✅ | ✅ | ✅ |
| `corr_izquierda` | ✅ | ✅ | ✅ |

## 26.1 `Invertir` es `IsGeomSameDirection = false`

No es un campo aparte: el casillero de `Datos avanzados` escribe `IsGeomSameDirection` en
`false`. Y la traza guardada se emite **al revés**, con la dirección negada:

```
base       8 0 300 | 1 50  200 8   1 0 0
invertir   8 0 300 | 1 350 200 8  -1 0 0
```

En el ISO, el recorrido pasa de `X50 → X350` a `X350 → X50`. ⇒ Confirma en una línea recta lo
que el arco había mostrado (§12.2), y **cierra el testigo que el Grupo 6 dejó pendiente**.

## 26.2 ⭐⭐⭐ El `G41`/`G42` NO sale del `SideOfFeature`: sale de cruzarlo con el sentido

| `SideOfFeature` | `IsGeomSameDirection` | ISO |
|---|---|---|
| `Right` | `true` | **`G42`** |
| `Right` | **`false`** | **`G41`** |
| `Left` | `true` | **`G41`** |
| `Left` | **`false`** | **`G42`** |
| `Center` | cualquiera | ninguno |

```
G41/G42 = f( SideOfFeature , IsGeomSameDirection )   -- no de SideOfFeature solo
```

### Por qué, y es lo que lo hace sólido

Porque **la traza corregida NO cambia de lado al invertir**. `corr_derecha` guarda su traza en
`Y198` —200 menos el `SVR`— y `corr_derecha_invertir` **también en `Y198`**: lo único que
cambia es el sentido.

⇒ El **lado físico** de la pieza es el mismo; lo que se dio vuelta es por dónde se lo recorre.
Y como `G41`/`G42` se definen *respecto del sentido de avance*, para conservar de qué lado
queda el material Maestro **tiene que cambiar el código**.

⇒ 🚨 **Para el converter**: emitir `G41`/`G42` con una tabla fija desde `SideOfFeature` da el
lado equivocado en **todos** los mecanizados invertidos, y la fresa come del lado que no debe.
Lo seguro es lo que el canal §21 ya sugería: **el `.pgmx` guarda la traza corregida**, así que
el código G se deriva de **qué lado cae la traza respecto del sentido de recorrido**, no de la
etiqueta.

📌 Y el milímetro de entrada/salida se invierte con todo lo demás: `G0 X49` → `G0 X351`, y la
entrada `G1 X50` → `G1 X350`. Coherente con §21.5 — es «1 mm antes del arranque», y el arranque
cambió de punta.

## 26.3 `Condición` es `IsEnabled` del paso del workplan, y borra sin dejar rastro

El diff del `.pgmx` entre el base y el `condicion_false` es **una línea**:

```
<IsEnabled>true</IsEnabled>   ->   <IsEnabled>false</IsEnabled>
```

Vive en el `MachiningWorkingStep` del workplan — no es un nodo `Condition` ni una expresión, y
es lo que el árbol del proyecto muestra como el nodo `IF`.

Y en el ISO:

- **idéntico al programa vacío salvo la línea del nombre**, en los tres;
- y **los tres son byte-idénticos entre sí** ⇒ **la corrección configurada no deja ningún
  rastro** cuando el paso está deshabilitado.

⇒ Confirma el canal §18 y lo extiende: `Condición = False` **borra el mecanizado entero**, con
todo lo que se le haya puesto encima.

## 26.4 ⭐⭐ Y los dos silencios resultan distinguibles

Contrastando con el Grupo 9:

| | qué queda en el ISO | |
|---|---|---|
| `Condición = False` | **nada** — idéntico al vacío | el usuario **lo pidió** |
| cara inferior (§25.1) | **dos líneas**: `?%ETK[8]=1` · `G40` | el usuario **no lo pidió** |

⇒ ⭐ **El rastro de dos líneas distingue un descarte involuntario de una deshabilitación
deliberada.** Maestro empieza a emitir el bloque de la cara inferior y lo abandona; con la
condición en falso no lo empieza nunca.

⇒ Es una señal aprovechable: sirve para **diagnosticar** un ISO de Maestro sin tener el `.pgmx`
al lado. No cambia la regla —el descarte silencioso se rechaza igual—, pero da una forma de
detectarlo después.

## 26.5 ✅ `Canto a canto` no existe en el fresado

**Confirmado por Fermín**: es una opción **exclusiva del canal**. Ayer salía de leer las
capturas de `Datos avanzados` (§13); hoy es dato directo.

⇒ El fixture correspondiente del pedido queda **cerrado como imposible**, con testigo.

---

# 27. Grupo 11 — el `Xmsg`: el conteo es POSICIONAL, y el `M5` es condicional (2026-09-10)

Ocho archivos: el fresado simple, el círculo y los dos paralelos, cada uno con y sin `Xmsg`,
**más el `Xmsg` movido de lugar** — al inicio del programa y **intercalado** entre los dos
fresados. Esos dos últimos los agregó Fermín, y son los que rompen el problema.

## 27.1 Lo que el `Xmsg` emite, y que el `M5` es CONDICIONAL

| posición | qué agrega |
|---|---|
| **al final** | `M5 ;(xISO362-> Spegne mandrino)` · `$0?422S0I0D0?` · `G4 F0` → **3 líneas** |
| **al inicio** | `$0?212S0I0D0?` · `G4 F0` → **2 líneas, sin `M5`** |
| **intercalado** | `M5 ;(…)` · `$0?422S0I0D0?` · `G4 F0` · **`S18000M3`** → **4 líneas** |

⇒ ⭐⭐ **El `M5` sólo se emite si el husillo está girando.** Al inicio del programa no hay nada
en marcha, así que no hay nada que apagar — y el bloque sale de dos líneas.

⇒ ⭐ **Y el intercalado agrega un `S18000M3`**: el `Xmsg` **corta el husillo y lo vuelve a
arrancar** para seguir. El de al final no lo necesita porque el programa termina.

Los largos cuadran exactos contra el mismo programa sin mensaje (114 líneas): **+2** al inicio,
**+3** al final, **+4** intercalado.

## 27.2 ⭐⭐⭐ El conteo depende SÓLO de lo emitido antes — con un control perfecto

| caso | posición | `$0?N` |
|---|---|---|
| dos fresados | **al inicio** | **212** |
| un fresado (línea) | al final | **422** |
| dos fresados | **intercalado** (después del primero) | **422** |
| un fresado (círculo) | al final | **533** |
| dos fresados | al final | **563** |

⇒ **`intercalado` y `un fresado` dan el MISMO número: 422.** Son programas distintos —uno tiene
un segundo fresado después del mensaje— y coinciden porque **lo que se emitió antes del `Xmsg`
es idéntico**.

⇒ **DERIVADO: el conteo es acumulativo de lo emitido hasta ese punto, y no mira nada de lo que
viene después.** Confirma el modelo del canal (`N = base + Σ incrementos`) con el control que
faltaba, y lo hace **verificable**: mover el mensaje de lugar cambia el número de forma
predecible.

Y los incrementos quedan medidos:

```
base del programa (campo A)      212
+ un fresado de línea           +210   ->  422
+ un fresado de círculo         +321   ->  533
+ un SEGUNDO fresado de línea   +141   ->  563
```

📌 **El segundo fresado cuesta menos que el primero** (141 contra 210): la misma asimetría
apertura/continuación que el Grupo 8 midió en líneas (§24.6). Los 69 de diferencia son el
preámbulo.

## 27.3 ⚠️ Pero la fórmula NO sale del ISO, y eso acota lo que el canal había derivado

`canal.md` §23 concluyó que el conteo **cuenta caracteres del texto emitido**. Con estos cinco
puntos se puede poner a prueba, y **ninguna forma de contar el ISO da el número**:

| forma de contar el texto anterior al `Xmsg` | línea (N=422) | círculo (N=533) | dos (N=563) | inicio (N=212) |
|---|---|---|---|---|
| caracteres sin fin de línea | 917 | 986 | 1178 | 435 |
| con `LF` | 982 | 1052 | 1263 | 458 |
| con `CRLF` | 1047 | 1118 | 1348 | 481 |
| sin espacios finales | 858 | 926 | 1103 | 418 |

Ninguna proporción se mantiene: 865/422 = 2,05 pero 934/533 = 1,75 y 1127/563 = 2,00. Y **la
cantidad de líneas tampoco sirve**: el círculo tiene *menos* líneas antes (66) que los dos
fresados (85) y un `N` más alto respecto de ellas.

⇒ ⭐ **Lo que el canal derivó sigue en pie en su parte cualitativa** —el conteo es sensible al
*contenido*, no sólo al tipo de operación: por eso `X92.500` daba distinto que `X100.000`— pero
**la unidad que cuenta no es el carácter del ISO.**

### 🔮 El candidato, y el fixture de dos minutos que lo decide

La cadena es `.pgmx` → **XXL** → **PGM** → ISO, y el conteo lo escribe el generador de Xilog en
la segunda etapa. Si cuenta caracteres, lo más probable es que cuente **el PGM**, que tiene otro
formato por instrucción.

⇒ **Postprocesar uno solo de estos con `PostFileFormat = PGM`** y contar ahí. Es el mismo
fixture barato que `canal.md` §25 pedía para el `0,75`, y ahora tiene un segundo motivo.

⚠️ **Roza una decisión de alcance**: el XXL y el PGM se cerraron como línea de trabajo el
2026-08-14 (`fixtures.md`). La decisión sigue valiendo para *derivar la traza*; esto es otra
cosa — **un contador que el ISO no explica**, y que hoy bloquea el byte-idéntico de todo
programa con mensaje. Queda planteado, no ejecutado.

📌 **Y un segundo contador sin explicar**: el `xISO` del comentario del `M5` (362, 448, 503) se
mueve con la posición igual que el `$0?`, pero su diferencia contra él no es constante (60, 85,
60). Aparece sólo cuando hay `M5`.

# 28. Grupo 12 — el barrido A5, y el espejo tecnológico SÍ toca la traza

Diez archivos, **nueve con su captura de la ventana** (9 de 9: el protocolo cumplido, como en
el canal §24). Todos dan **94 líneas**, igual que la referencia: **ningún parámetro de máquina
agrega ni quita una línea**.

## 28.1 ⚠️ Primero: seis nombres dicen `EF` y el archivo está en `A`

| archivo | el nombre afirma | el `.pgmx` dice |
|---|---|---|
| `…_A5_bloqueo_10` · `_60` · `_predefinido` | `EF` | **`A`** |
| `…_A5_mecanicas_laser` · `_elevadores` | `EF` | **`A`** |
| `…_A5_repeticiones_3` | `EF` | **`A`** |

Es exactamente el modo de falla que motivó la regla del 2026-08-27: el campo se cambia en la
misma ventana que el parámetro que se está variando, y el cambio no quedó aplicado al programa.

⇒ **No invalida nada, y de hecho conviene**: los seis están en campo `A`, **igual que la
referencia**, así que el diff mide **sólo** el parámetro. Si hubieran quedado en `EF`, el efecto
del campo se mezclaría con el del parámetro y el par no serviría. Lo que hay que corregir es el
nombre.

> ✅ **CORREGIDO por Fermín el 2026-09-10**, `.pgmx` y `.iso`. La auditoría vuelve a dar
> limpio: los seis pasaron a `R_PV_A_fresado_A5_…` y **coinciden con su archivo**.
>
> ⚠️ **Quedó un huérfano**: `R_PV_EF_fresado_A5_repeticiones_3.pgmx` sigue en la carpeta, con
> **XML idéntico** al renombrado y **sin `.iso`** (el suyo ya se renombró). Es una copia
> muerta — se puede borrar. Verificado comparando el XML entero, no el nombre.

📌 Los dos `areas_combinadas` **sí** están donde dicen (`EF` y `HG`), y por eso difieren en 18 y
22 líneas: eso es **el campo**, ya derivado (R002 y §4ter). Valen como control, no como
parámetro nuevo.

## 28.2 Cinco que sólo tocan el header

| fixture | `.pgmx` | la línea del header |
|---|---|---|
| `bloqueo_10` | — | `V=0` → **`V=2`** |
| `bloqueo_60` | — | `V=0` → **`V=10`** |
| `bloqueo_predefinido` | — | `V=0` → **`V=9`** |
| `mecanicas_elevadores` | `MechanicalOptions=1` | `T=0` → **`T=1`** |
| `mecanicas_laser` | `MechanicalOptions=10` | `T=0` → **`T=10`** |

⇒ Confirma el barrido A5 original (todas las diferencias caen en la línea del header: unas
mueven `V`, otras `T`), y agrega una **correspondencia 1:1**: `MechanicalOptions` del `.pgmx` va
directo al campo **`T`** del header. El bloqueo, en cambio, entra a `V` **como código** (10→2,
60→10, predefinido→9), no como valor.

## 28.3 ✅ `Repeticiones = 3` no llega — byte-idéntico, con testigo interno

Cero líneas de diferencia contra la referencia. Y el `.pgmx` guarda `Repetitions = 3`, así que
**el negativo tiene testigo**: no es un «no lo puse». Tercera vez que se mide (dibujos §14.1,
canal §24, acá).

## 28.4 ⭐⭐⭐ El espejo tecnológico SÍ llega al ISO — y contradice al canal

```
G0 X50.000  Y200.000        ->   G0 X350.000 Y200.000
G1 X350.000 Z-10.000        ->   G1 X50.000  Z-10.000
```

**Dos líneas, y son de la TRAZA.** El recorrido pasa de `X50 → X350` a `X350 → X50`.

⇒ `canal.md` §24 había derivado que *«el espejo tecnológico no espeja nada, y ahora con
testigo»*. **Con la sierra era cierto** — y ahora se entiende por qué: la `082` **normaliza el
sentido de corte** (siempre de X mayor a menor, §11 del canal), así que espejar no podía
cambiar nada observable. **Con fresa el sentido es del programa, y el espejo se ve.**

⇒ ⭐ **Es el primer parámetro de máquina que toca la traza** en toda la reinvestigación, y es
justamente el que el canal había marcado como «el candidato».

### ⚠️ Pero con esta geometría no se puede distinguir «espejar» de «invertir»

La línea va de `X50` a `X350` sobre una pieza de 400: **está centrada**. Un espejo en X
respecto del centro lleva `(50, 350)` a `(350, 50)` — que es **lo mismo** que invertir el
sentido.

⇒ **Hace falta una geometría asimétrica.** Con una línea de `X50` a `X250`:

| | resultado |
|---|---|
| si **espeja** | `X350 → X150` |
| si sólo **invierte el sentido** | `X250 → X50` |

⇒ Es la diferencia entre que el converter tenga que **transformar coordenadas** o sólo **dar
vuelta el orden**, y se decide con un archivo. Va al Grupo 17.

📌 Y hay un tercer candidato a descartar de paso: que el espejo produzca lo mismo que
`Invertir` (§26.1). Si el ISO del espejo sobre la línea centrada es **byte-idéntico** al del
`corr_central_invertir`, son el mismo efecto por dos caminos.

# 29. Grupo 13 — las microuniones quedan postergadas

**Dato de Fermín**: **las microuniones no se pueden aplicar** sobre el fresado en esta pieza.
Debe haber una configuración específica que las habilita, todavía sin identificar. Se retoman
cuando aparezca.

El archivo que quedó es el **pasante limpio** (`ThroughMillingBottom`, profundidad 18, ISO con
`G1 Z-18.000`), y su `<Attributes/>` está **vacío**.

⇒ ⭐ **Eso confirma indirectamente la predicción de §10**: si las microuniones fueran un
`OperationAttribute` —como el `DepthAttribute` de la rampa—, vivirían en ese nodo. El nodo está
donde tiene que estar, y vacío, porque la operación no se pudo crear.

⏸ **Queda abierto** y no bloquea nada del converter: sin fixture no hay nada que emitir.

---

# 30. Grupo 14 — los atributos son un solo mecanismo, y el offset exterior redondea (2026-09-10)

Diecisiete pares en vez de los tres del pedido: Fermín agregó **las correcciones y las
inversiones sobre el contorno cerrado** —el caso de producción— y **rectángulos que arrancan en
el punto medio de un lado**.

## 30.1 ⭐⭐⭐ Los tres atributos de la cinta son UN SOLO mecanismo

La predicción de §10 —que `Velocidad` sería otro `OperationAttribute` como el de la
profundidad— **se cumple con la misma forma exacta**:

```xml
<b:OperationAttribute i:type="b:SpeedAttribute">
  <b:IsNormalized>true</b:IsNormalized>
  <b:UPar>0.5</b:UPar>      <!-- Posicion (%) / 100, igual que la profundidad -->
  <b:Speed>3</b:Speed>
</b:OperationAttribute>
```

Y en el ISO **parte la traza en el punto del atributo**, igual que la rampa:

```
G1 X200.000 Z-10.000 F5000.000     <- hasta el 50%: el avance del catálogo
G1 X350.000 Z-10.000 F3000.000     <- desde ahí: F3000
```

`UPar = 0,5` → `X200` = `50 + 0,5 × 300` ✅ la misma fórmula del porcentaje. Y **`Speed = 3` →
`F3000`**: ×1000, la misma escala que `FeedRate.Standard`.

```
OperationAttribute = { UPar , valor }   ->  parte la traza en ese punto
   DepthAttribute  ->  cambia la Z desde ahí
   SpeedAttribute  ->  cambia la F desde ahí
   (microuniones)  ->  el tercero, sin fixture todavía (§29)
```

⇒ **Un solo modelo para los tres**, en el converter y en el sintetizador. Y el nodo
`<Attributes>` —vacío en todo el corpus hasta el Grupo 2— queda explicado entero.

## 30.2 ⭐⭐⭐ El offset EXTERIOR redondea las esquinas; el interior las deja vivas

Sobre el perímetro de la pieza `(0,0)-(400,400)`, con la `E004` (radio 2):

**`corr_izq_CAD`** — la traza va **hacia adentro**, rectángulo `(2,2)-(398,398)`, **cuatro `G1`
y esquinas vivas**:

```
G0 X2.000 Y2.000 · G1 X398.000 · G1 Y398.000 · G1 X2.000 · G1 Y2.000
```

**`corr_der_CAD`** — la traza va **hacia afuera**, y **cada esquina es un arco de radio 2
centrado en el vértice nominal**:

```
G0 X-2.000 Y0.000
G3 X0.000   Y-2.000  I0.000   J0.000       <- esquina (0,0)
G1 X400.000
G3 X402.000 Y0.000   I400.000 J0.000       <- esquina (400,0)
G1 Y400.000
G3 X400.000 Y402.000 I400.000 J400.000     <- esquina (400,400)
G1 X0.000
G3 X-2.000  Y400.000 I0.000   J400.000     <- esquina (0,400)
G1 Y0.000
```

⇒ Es geometría de offset pura: hacia afuera una esquina viva **dejaría material**, así que se
redondea con el radio de la herramienta; hacia adentro los lados se cruzan y la esquina queda
viva.

⇒ ⭐⭐ **Y para el converter es una buena noticia con una advertencia**: el `.pgmx` **ya guarda
esos arcos** en el toolpath —es la traza corregida (canal §21)—, así que **no hay que calcular
ningún offset**. Pero **el toolpath tiene más elementos que la geometría**: ocho contra cuatro.
Un converter que asuma «un segmento de traza por segmento de geometría» se rompe acá. Se ve
hasta en el tamaño del archivo: 7397 bytes contra 7214 del interior.

## 30.3 `Invertir` en un cerrado invierte el GIRO y conserva el arranque

| | recorrido |
|---|---|
| `contorno_pieza` | `X400 · Y400 · X0 · Y0` — **antihorario** |
| `contorno_pieza_invertir` | `Y400 · X400 · Y0 · X0` — **horario** |

Los dos arrancan en `(0,0)`.

⇒ Distinto de la línea abierta (§26.1), donde `Invertir` **cambiaba el punto de arranque** (de
`X50` a `X350`). En un cerrado el arranque es el mismo nodo, así que lo único que se da vuelta
es el **sentido de giro**. Es el dato que el Grupo 10 no podía dar.

📌 **Y el sentido de giro importa en producción**: decide si la fresa trabaja a favor o en
contra del avance. Con `Center` no hay corrección, pero el acabado cambia.

## 30.4 ✅ Cuarto testigo del «modo largo», ahora en un cerrado

Con `Center` sobre el contorno:

| | `ActivateCNCCorrection` | ISO |
|---|---|---|
| `contorno_pieza_invertir` | `true` | modo corto |
| `contorno_pieza_invertir_CN` | `true` | **byte-idéntico** al anterior |
| `contorno_pieza_invertir_CAD` | **`false`** | **modo largo** (`G1 Z20 F2000` · `G1 Z-10 F5000` · `G1 Z20 F5000`) |

⇒ Confirma §15.3 por cuarta vez, y ahora sobre geometría cerrada: **lo enciende el flag**, no
el lado ni la forma.

## 30.5 ⭐⭐ El arranque en el punto MEDIO de un lado — y cierra la regla de emisión de ejes

Aporte de Fermín, y tiene razón de oficio: **arrancar en el medio de un lado evita empezar y
terminar en una esquina**, que es donde la fresa deja marca.

| archivo | arranca en | segmentos |
|---|---|---|
| `rectangulo_inicio_horizontal` | `(200, 50)` — medio del lado inferior | **5** |
| `rectangulo_inicio_vertical` | `(350, 200)` — medio del lado derecho | **5** |
| `rectangulo_solo_vertical` | `(200, 50)` | **6** |

⇒ **El lado que contiene el arranque se recorre en dos tramos** —al principio y al final—, así
que un rectángulo de cuatro lados sale en **cinco** segmentos. Y el conteo lo confirma:
`50 + 5 = 55` líneas agregadas (98 − 43) ✅, contra las 54 del rectángulo que arranca en un
vértice (§12.1).

### ✅ Y `solo_vertical` cierra la regla que quedaba abierta

Era el fixture que faltaba (§12.7): **dos tramos puramente verticales, consecutivos**.

```
G1 Y200.000 Z-10.000 F5000.000
G1 Y350.000 Z-10.000 F5000.000
```

**Los dos emiten `Y` + `Z`.** ⇒ La regla queda **derivada**, con el caso que le faltaba:

```
se emiten los ejes que CAMBIAN;
si cambia uno solo, se completa con la Z aunque sea constante.
```

Ocho casos, incluidos dos verticales seguidos. Y su conteo: `50 + 6 = 56` (99 − 43) ✅.

## 30.6 Lo que este grupo deja abierto

| | |
|---|---|
| el **sentido de giro** con corrección | los ocho `contorno_corr_*` cruzan lado × modo × inversión; falta ver si el giro por defecto (antihorario) cambia con la corrección o es siempre del programa |
| el arco de esquina con **otra herramienta** | el radio es `SVR` en un caso (`E004`, radio 2); con la `E001` (9,18) el arco sería mucho mayor y podría no caber en un rectángulo chico |
| ~~el tramo puramente vertical~~ | ✅ **cerrado acá** (§30.5) |
| ~~`Velocidad` como atributo~~ | ✅ **derivado acá** (§30.1) |
| ~~el contorno cerrado con `Invertir`~~ | ✅ **derivado acá** (§30.3) |

---

# 31. ⭐⭐⭐ Grupo 15 — el `10` del retorno ES `MillingRetractDistance` (2026-09-10)

**Tres archivos, sin `.iso` — y no hacen falta**: se lee del `.pgmx`, como estaba previsto. El
diseño de Fermín separa las dos cosas que había que separar.

| archivo | cómo se hizo | `Paso de retroacción` |
|---|---|---|
| `…_uni_EP_ph5` | el original del Grupo 5 | 10 |
| `…_uni_EP_ph5_retroaccion_15` | **reguardado** con la opción en 15 | 15 |
| `…_nuevo_…_retroaccion_15` | **creado de cero** con la opción en 15 | 15 |

## 31.1 Reguardar no cambia nada

El toolpath del **reguardado** es **idéntico** al original, tramo por tramo:

```
8 0 300  1 50 200 13   1 0 0     <- pasada 1 (prof 5)
8 0 10   1 350 200 13  0 0 1     <- sube 10
8 0 300  1 350 200 23 -1 0 0     <- retorno
8 0 15   1 50 200 23   0 0 -1    <- baja 15
8 0 300  1 50 200 8    1 0 0     <- pasada 2 (prof 10)
```

⇒ ✅ **Confirma el patrón de §23.2 en su forma más fuerte**: la opción actúa **al crear**, y una
vez que la traza está calculada **no se recalcula al guardar**. Es el control que ninguna otra
prueba podía dar.

## 31.2 ⭐⭐⭐ Y el creado de cero lo resuelve: sube 15, no 12

El tercero se hizo con la opción en **15** y —a propósito— con **profundidad 12**, para que el
valor de la opción y la profundidad **no coincidan**:

```
8 0 250  1 50 150 13   1 0 0     <- pasada 1: Z13 = 18−5   (prof 5)
8 0 15   1 300 150 13  0 0 1     <- SUBE 15  -> Z28
8 0 250  1 300 150 28 -1 0 0     <- retorno
8 0 20   1 50 150 28   0 0 -1    <- baja 20  -> Z8
8 0 250  1 50 150 8    1 0 0     <- pasada 2: Z8  = 18−10  (prof 10)
8 0 15   1 300 150 8   0 0 1     <- SUBE 15  -> Z23
8 0 250  1 300 150 23 -1 0 0     <- retorno
8 0 17   1 50 150 23   0 0 -1    <- baja 17  -> Z6
8 0 250  1 50 150 6    1 0 0     <- pasada 3: Z6  = 18−12  (prof 12)
```

**Sube 15**, no 12.

```
altura del retorno «En la pieza» = MillingRetractDistance     («Paso de retroacción en los fresados»)
bajada al siguiente paso         = MillingRetractDistance + el paso de esa pasada
```

La bajada lo confirma dos veces: `20 = 15 + 5` (paso completo) y `17 = 15 + 2` (el resto,
12 − 10). Y el reparto `5 · 10 · 12` sigue la regla de §16.4: pasos de `PH` con el resto al
final.

⇒ **DERIVADO, y los dos candidatos de §16.3 quedan separados**: con la opción en 10 y
profundidad 10 subía 10; con la opción en 15 y profundidad 12 sube **15**. Si fuera la
profundidad, subiría 12.

### Qué significa para cada lado

- **Para el converter: nada que hacer, y era lo que faltaba confirmar.** El número **no es un
  campo del `.pgmx`** —no existe ningún `MillingRetractDistance` ahí— sino que está **dentro de
  la traza**, calculado por Maestro. El converter **lo lee**. La advertencia de §16.3 («el
  converter no puede escribir ese 10») queda cerrada: nunca tuvo que escribirlo.
- **Para el sintetizador: sí lo necesita**, y ahora sabe de dónde sale — el **tercer origen**,
  `UI00.exe.Config`. Es el primer caso donde el sintetizador **tiene que leer** una opción de la
  aplicación para producir una traza correcta.

📌 De paso, el resto del archivo nuevo verifica tres reglas ya derivadas: `Approach` = `8 0 35`
desde `Z48` = espesor + **cota 30** (§23.1), `Lift` = `8 0 42` hasta `Z48`, y las tres pasadas
con su reparto.

# 32. Grupo 16 — el solape, derivado (2026-09-10)

Siete archivos que cruzan **lado × solape × multiplicador de radio**, sobre el perímetro de la
pieza con acercamiento y alejamiento **en arco**. Y arrancan en el **punto medio de un lado**,
la técnica del Grupo 14.

## 32.1 ⭐⭐ El solape continúa el recorrido más allá del cierre — tal cual lo describiste

Sin solape, el contorno cierra en su punto de arranque y sale por el arco:

```
G1 Y200.000 Z-18.000              <- cierra en (0,200), el punto medio del lado
G3 X-8.000 Y208.000 I-8.000 J200.000
```

Con `Solape = 5`:

```
G1 Y200.000 Z-18.000              <- cierra
G1 Y205.000 Z-18.000              <- ⭐ SIGUE 5 mm más allá
G3 X-8.000 Y213.000 I-8.000 J205.000    <- y el arco de salida se corre con él
```

Con `Solape = 20` → `G1 Y220.000`, y el arco en `J220`.

```
el solape es el valor en mm, y agrega un segmento que PROLONGA el último tramo;
el arco de alejamiento arranca del punto nuevo
```

⇒ **Dos valores (5 y 20) y el dato de oficio coinciden**: *«el trazo final se extiende más allá
del punto final»*.

## 32.2 ⭐ Es independiente del multiplicador de radio — y eso lo dio el cruce

| | radio del arco | solape |
|---|---|---|
| `corr_izq_solape_5` (`mr4`) | 8 (`I-8`) | 5 |
| `corr_izq_mr2_solape_5` (`mr2`) | **4** (`I-4`) | 5 |
| `corr_izq_mr2_solape_20` | 4 | **20** |

⇒ El radio del lead cambia con `RadiusMultiplier × SVR` (§21.1) y **el solape no se mueve**.
Son dos parámetros independientes, y sin el cruce no se podía afirmar.

## 32.3 Y sigue la dirección del último tramo, no un eje fijo

Con `corr_der`, donde el contorno arranca en `(200, 0)` —el medio del lado **inferior**— el
solape sale en **X**:

```
G1 X200.000 Z-18.000
G1 X205.000 Z-18.000              <- los 5 mm, ahora en X
G2 X213.000 Y-8.000 I205.000 J-8.000
```

⇒ **El solape prolonga el último tramo en su propia dirección.** Coherente con el `1 mm` de la
compensación (§21.5), que también va por la tangente.

## 32.4 ❌ Mi predicción falló en la forma (acertó en el valor)

§21.6 predijo *«el ISO no gana líneas, porque es el mismo segmento más largo»*. **Gana una**
(105 → 106): Maestro **no alarga el último `G1`, agrega uno nuevo** — emite `G1 Y200` y después
`G1 Y205`.

⇒ El valor de 5 mm estaba bien; la forma, no. Para el converter la diferencia importa: **el
solape es un segmento propio de la traza**, no un ajuste de coordenada del anterior — y como
el `.pgmx` guarda la traza entera, ya viene así.

## 32.5 ⛔ Y el `Solape` sin corrección: el archivo quedó SIN OPERACIÓN

`contorno_pieza_solape_5.pgmx` pesa 5770 bytes contra ~7500 de los otros, **no tiene ni
`Operation` ni `ManufacturingFeature`**, y su ISO es **idéntico al programa vacío salvo el
nombre**.

⇒ El fresado no llegó a crearse. No alcanza para afirmar *por qué* —si la ventana no deja
aplicar el solape sin corrección, o si quedó a medias por otro motivo— así que queda como
**observación, no como derivación**. ❓ **Pregunta para Fermín**: ¿la ventana rechazó algo ahí,
o el archivo quedó sin terminar?

---

# 33. Inventario de lo que queda abierto en el fresado (2026-09-10)

**Repaso completo de las secciones de pendientes** —§14, §18, §22, §29, §30.6— contra lo que
los grupos posteriores fueron cerrando. Se hace explícito porque es el modo de falla que la
auditoría del 2026-08-27 describió: *un doc que no sabe lo que ya se contestó*, y que en
`perforado.md` §9 dejó cuatro «abiertos» que estaban cerrados.

## 33.1 ✅ Lo que se cerró, y dónde

| pendiente | cerrado en |
|---|---|
| el defecto de `build_line_geometry_profile` (la rampa) | §10 — serialización 3D, a 17 dígitos |
| el `10` del retorno «En la pieza» | **§31 — es `MillingRetractDistance`** |
| `Velocidad` como atributo | §30.1 — `SpeedAttribute`, un solo mecanismo con la profundidad |
| el costo en líneas con **varias** operaciones | §24.6 — `+20` misma fresa, `+35` con otra |
| la regla de emisión de ejes | §30.5 — con dos verticales consecutivos, ocho casos |
| el acortamiento de `IsPrecise` | §19 — es el radio, con dos profundidades |
| la profundidad 18 de los `corr_len` | §19 — era involuntaria, rehechos |
| el `ActivateCNCCorrection` de los multipaso | §20 — lo fuerza la UI |
| el modo largo con `Center` + `CAD` | §30.4 — cuarto testigo, en cerrado |
| el `Solape` en un contorno cerrado | **§32 — prolonga el último tramo, indep. del radio** |
| el contorno cerrado con `Invertir` | §30.3 — invierte el giro, conserva el arranque |
| el cambio de herramienta | §24.6 — 49 combinaciones, 98 bloques del catálogo |
| las tres transiciones | §24.6 — 5 / 13 / 15 líneas, y la de cabezal es una sola |
| la cota de seguridad | §23.1 — tres valores, y **§23.2** cierra el tercer origen |
| el fresado en el canto | §25.3 — se pide desde arriba, y es un fresado normal |

## 33.2 ⚠️ Lo que sigue abierto

Ordenado por lo que cuesta si no se cierra.

### A. Decide código del converter

| | |
|---|---|
| ~~**1. ¿el espejo ESPEJA o INVIERTE?**~~ | ✅ **CERRADO §34.1: INVIERTE.** Byte-idéntico al de `Invertir`, y `espejo + invertir` vuelve al original. **Pero la traza guardada NO lo refleja** —lo aplica el postprocesador— así que el converter **tiene que leer `IsTechnologicalMirror` y aplicar la inversión**, y el ISO no deja marca |
| **2. el conteo del `Xmsg`** | §27.3, y analizado a fondo en `operaciones_maquina.md` §19. ⚖️ **Decisión de Fermín (2026-09-11): el converter NO puede rechazar los programas con mensaje** — el `Xmsg` es la parada que permite **girar la pieza**, o sea la solución al fail-loud de la cara inferior (§25.1). ⭐ Y el análisis cambió la interpretación: **`N` no es un contador sino un PUNTERO al texto** en el programa compilado, porque el mensaje **no viaja en el ISO**. ⇒ la salida más barata es probar si el `N` hace falta para **ejecutar**: la parada la dan `M0` + `G4 F0`, que no dependen de él |
| ~~**3. `%DONTCARESPEEDV=1`**~~ | ✅ **CERRADO (Fermín, 2026-09-10)**: es un **bug de Maestro** y es la línea que paró el CNC. El converter **la omite siempre**, y ahora sabe cuándo Maestro la habría emitido. De paso **unifica los incidentes del 07-30 y del 08-03** — eran el mismo bug — y deja un beneficio concreto: el converter puede emitir «Salida a cota de seguridad» *sin* la línea, o sea la traza segura **y** ejecutable. Ver §16.1 |

### B. Podría romper una traza real

| | |
|---|---|
| ~~**4. el arco de esquina con otra herramienta**~~ | ✅ **CERRADO §34.2 y §35.1**: el radio es `SVR` y escala sin degenerar por afuera. **Y el offset INTERIOR imposible resultó el QUINTO FAIL-LOUD**: con la `E006` (radio 40) en un rectángulo de 50×50 Maestro **declara** que no puede calcular la traza y **emite igual**, delegando al CN. ⭐ La señal para el converter es limpia y está en el `.pgmx`: **`ToolpathList` vacío ⇒ rechazar** |
| ~~**5. el sentido de giro con corrección**~~ | ✅ **CERRADO §34.3 y §34.6, y la respuesta es doble**: en **C.N.** el sentido **no cambia** (sólo el código G); en **CAD con multipaso** sí cambia. ⚠️ Y abre un hilo: Maestro tiene **dos formas** de resolver el lado —cambiar el offset o cambiar el sentido— y no está derivado qué elige cuál. No afecta al converter (lee la traza); sí al sintetizador |
| ~~**6. el lado del arco EXPLÍCITO**~~ | ✅ **CERRADO §34.4: lo ignoran.** `Automático` es el único que sigue a la corrección. Y acota §21.5: el milímetro de `G41`/`G42` va por la tangente **sólo si el lado del arco es coherente** con la corrección |

### C. Anotado, sin costo conocido

| | |
|---|---|
| **7. `Cutmode = Climb`** | aparece en los quince archivos de estrategia, **nunca variado**, y sin campo identificado en la ventana |
| ~~**8. `ZigZag`**~~ | ✅ **RE-ANCLADO §34.5**: corta en rampa continua alternando el sentido, con **pasada final plana** y arranque en la superficie. Valida lo que el sintetizador ya tenía. ⏭️ Falta comparar el detalle contra el código |
| ~~**9. `Helicoidal`**~~ | ✅ **DERIVADA §35.2**: cada media vuelta baja `PH/2` y el resto **se reparte en la última vuelta** (distinto del unidireccional); `Habilitar pasada final` agrega **una vuelta completa plana**. Se aplica a geometría **cerrada**, que es la única donde una hélice tiene sentido |
| **10. el `xISO` del comentario del `M5`** | segundo contador (362, 448, 503), se mueve con la posición pero su relación con el `$0?` no es constante |
| **11. el orden con dos cabezales** | §24.6. Empezar por el cabezal perforador cambia el largo del ISO, y **no en el mismo sentido** con canal (94/95) que con taladro (84/82) |
| **12. los siete nombres del Grupo 1** | dicen `x50_x300_y150` y la traza es (50,200)→(350,200). Ninguna derivación los usa; conviene renombrar |
| **13. el `Solape` sin corrección** | §32.5. El archivo quedó **sin operación**: no se sabe si la ventana lo rechaza o quedó a medias |

### D. En pausa por decisión

| | |
|---|---|
| **14. las microuniones** | §29. No se pueden aplicar todavía; falta identificar la configuración que las habilita. **No bloquea al converter**: sin fixture no hay nada que emitir |

## 33.3 El grupo final propuesto — 9 archivos

Con esto el fresado quedaría cerrado. Están ordenados por lo que decide cada uno.

### El espejo, que es el que decide código (2)

- [ ] `R_PV_A_manual_fresado_top_E004_x50_x250_y200_prof10`
- [ ] `R_PV_A_manual_fresado_top_E004_x50_x250_y200_espejo_tecnologico` (+ captura)
      Línea **asimétrica**, de `X50` a `X250`. Si el ISO da `X350 → X150` **espeja**; si da
      `X250 → X50` sólo **invierte**.

### El arco de esquina con la fresa grande (2)

- [ ] `R_PV_A_manual_fresado_top_E001_contorno_pieza_corr_der`
      El perímetro con la **`E001`** (radio 9,18) y corrección **exterior**. El arco de esquina
      tendría que salir de radio 9,18.
- [ ] `R_PV_A_manual_fresado_top_E001_rectangulo_50_50_100_100_corr_der`
      Un rectángulo **chico** (50×50) con la misma fresa: el arco de 9,18 en las esquinas de un
      lado de 50 es el caso límite. **Si Maestro rechaza, el mensaje es la respuesta.**

### El sentido de giro, comparable (2)

- [ ] `R_PV_A_manual_fresado_top_E004_contorno_medio_izq_corr_izq`
- [ ] `R_PV_A_manual_fresado_top_E004_contorno_medio_izq_corr_der`
      **El mismo contorno, con el mismo arranque** (el punto medio del lado izquierdo), cambiando
      **sólo** el lado de la corrección. Es lo que los ocho del Grupo 14 no pueden dar.

### El lado del arco explícito contra la corrección (2)

- [ ] `R_PV_A_manual_fresado_top_E004_corr_izq_acerc_arco_mr4_cota_lado_izq`
- [ ] `R_PV_A_manual_fresado_top_E004_corr_der_acerc_arco_mr4_cota_lado_izq`
      Los dos con el lado del arco en **`Izquierdo` explícito**. Si los dos dan el mismo arco,
      el explícito **ignora** la corrección; si difieren, la respeta.

### La estrategia que falta re-anclar (1)

- [ ] `R_PV_A_manual_fresado_top_E004_estrategia_zigzag_ph5`
      **`ZigZag`** con multipaso, sobre la línea del mínimo. Es la única de las cuatro sin
      fixture de esta época, y el sintetizador la emite apoyado en `N025` — serie N, congelada.

### Y una pregunta sin archivo

❓ **El `Solape` sin corrección** (§32.5): ¿la ventana lo rechazó, o el archivo quedó a medias?
Si lo rechaza, es un ⛔ derivado y no hay nada que hacer.

---

# 34. Grupo 18 — el grupo final (2026-09-11)

**15 pares**, con extras sobre los 9 pedidos: el cruce completo del espejo, el control con `E004`
de los dos casos de la `E001`, y **dos archivos que cruzan todo a la vez** (contorno cerrado +
pasante + corrección + multipaso).

## 34.1 ⭐⭐⭐ El espejo tecnológico NO espeja: invierte el sentido

El cruce de cuatro archivos sobre la línea **asimétrica** `X50 → X250` lo cierra:

| archivo | `IsTechnologicalMirror` | `IsGeomSameDirection` | ISO |
|---|---|---|---|
| base | `false` | `true` | `X50 → X250` |
| `_invertir` | `false` | **`false`** | `X250 → X50` |
| `_espejo_tecnologico` | **`true`** | `true` | **`X250 → X50`** |
| `_espejo_tecnologico_invertir` | **`true`** | **`false`** | **`X50 → X250`** |

Si espejara respecto del centro de la pieza, `X50→X250` daría `X350→X150`. **No pasa**: da las
mismas coordenadas al revés.

Y los dos controles son **byte-idénticos**, verificado sin la línea del nombre:

- `_espejo_tecnologico` == `_invertir` ⇒ **el espejo produce exactamente el mismo ISO que
  `Invertir`**;
- `base` == `_espejo + _invertir` ⇒ **se cancelan**.

```
sentido del ISO = sentido de la traza guardada  XOR  IsTechnologicalMirror
```

⇒ **Para el converter: no hay que transformar coordenadas.** Y queda descartado el espejo
respecto de la pieza y respecto del origen.

### 🚨 Pero hay una trampa: la traza guardada NO refleja el espejo

| | traza guardada (`TrajectoryPath`) |
|---|---|
| base | `1 50 150 8 · 1 0 0` |
| `_espejo_tecnologico` | **`1 50 150 8 · 1 0 0`** — *la misma que el base* |
| `_invertir` | `1 250 150 8 · -1 0 0` |

⇒ **El espejo lo aplica el POSTPROCESADOR**, no el `.pgmx`. Es el primer caso donde el ISO no
copia la traza guardada por una razón que **no** es `ActivateCNCCorrection`.

⇒ 🚨 **El converter tiene que leer `IsTechnologicalMirror` y aplicar la inversión él mismo.**
No puede confiar en la traza. Y **el ISO no deja marca**: el header sale idéntico, así que
mirando sólo el ISO no hay forma de saber si el espejo estaba puesto.

📌 **Nomenclatura, y no es nuestra**: «espejo tecnológico» **no espeja**. Un converter que lea
el nombre y transforme coordenadas rompe todo. *(Con una línea, «invertir» y «espejar respecto
del centro de la propia línea» coinciden; lo que importa es que el ISO es byte-idéntico al de
`Invertir`, así que para emitir da igual. Separarlos del todo pediría una geometría asimétrica
como la polilínea — hilo suelto de bajo costo.)*

## 34.2 ✅ El arco de esquina con la `E001`: el offset exterior no degenera

El radio del arco de esquina **es `SVR`**, y escala sin problema:

| geometría | herramienta | radio del arco | rectas |
|---|---|---|---|
| perímetro 400×400 | `E004` | **2** | 400 (intactas) |
| perímetro 400×400 | `E001` | **9,18** | 400 |
| rectángulo **50×50** | `E004` | 2 | 50 |
| rectángulo **50×50** | `E001` | **9,18** | 50 |

⇒ **Ninguno se rechaza**, ni el caso límite (arco de 9,18 en esquinas de un lado de 50). Y las
rectas **mantienen su largo**: en el offset exterior los arcos se agregan afuera, no recortan
los lados.

⇒ Geométricamente era esperable: **el offset exterior nunca degenera** — por chica que sea la
pieza, afuera hay lugar. ⚠️ **El caso límite real es el offset INTERIOR** con una fresa grande
en una geometría chica, y eso **sigue sin probar**.

📌 Y de paso, el radio del **lead** con la `E001` da `mr4 × 9,18 = 36,72` ✅ — confirma §21.1 con
una herramienta más y un radio grande.

⚠️ **Estos cuatro archivos están en modo C.N.**, así que el ISO lleva la línea **nominal** y los
arcos de esquina **no aparecen** ahí: están en la **traza guardada** del `.pgmx`, que es de
donde se leyeron. El ISO sólo muestra los arcos del acercamiento.

## 34.3 ✅ El sentido de giro NO cambia con la corrección — en C.N.

`contorno_medio_izq_corr_izq` y `_corr_der`, mismo arranque `(0,200)`:

```
los dos:   G0 X0 Y201 · G1 X0 Y200 · G1 Y0 · G1 X400 · G1 Y400 · G1 X0 · G1 Y200
difieren:  G41                      contra                      G42
```

⇒ **Mismo recorrido, mismo arranque, mismo milímetro de entrada. Sólo cambia el código G.**

⇒ Con esto la tabla del §26.2 queda **verificada en los cuatro cuadrantes**: ayer el cruce fue
*mismo lado × sentido distinto*, hoy es *mismo sentido × lado distinto*. La regla
`G41/G42 = f(SideOfFeature, IsGeomSameDirection)` se sostiene en los dos ejes.

## 34.4 El lado del arco explícito IGNORA la corrección

Los dos con `lado_izq` **explícito** dan **el mismo arco**: `G3 X0 Y200 I8 J200`, arrancando en
`(8,208)`, con `corr_izq` y con `corr_der`.

⇒ **`Izquierdo`/`Derecho` explícitos mandan sobre la corrección**; `Automático` es el único que
la sigue (§21.4).

### 📌 Y acota §21.5: el milímetro no siempre va por la tangente

| | posiciona en | entra a | dirección |
|---|---|---|---|
| `corr_izq` + `lado_izq` | `X9 Y208` | `X8 Y208` | **−X** = la tangente del arco |
| `corr_der` + `lado_izq` | **`X7 Y208`** | `X8 Y208` | **+X** = *contra* la tangente |

⇒ §21.5 derivó que el milímetro de `G41`/`G42` se recorre **por la tangente del primer
movimiento**. Vale cuando el lado del arco es **coherente** con la corrección; cuando se fuerza
el contrario —la combinación que `Automático` evita— entra **al revés**.

## 34.5 ⭐⭐ El `ZigZag`, re-anclado con un fixture de esta época

Con `PH = 3` sobre profundidad 15:

```
G1 Z0.000  F5000          <- arranca en la SUPERFICIE, no en la cota
G1 X250 Z-3.000           <- baja 3 MIENTRAS avanza
G1 X50  Z-6.000           <- vuelve, bajando 3 más
G1 X250 Z-9.000
G1 X50  Z-12.000
G1 X250 Z-15.000
G1 X50  Z-15.000          <- la última, PLANA: deja el fondo parejo
```

⇒ **Corta en rampa continua alternando el sentido**: la herramienta nunca sale del material y
no hay retorno en vacío. Cinco rampas de 3 mm hasta la cota, más **una pasada plana de vuelta**.

⇒ ✅ **Valida lo que el sintetizador ya tenía** (`ZigZagMillingStrategySpec`: «corta en rampa
alternando el sentido»), cuya única ancla era **`N025`, serie N, época congelada**. Queda
re-anclado. ⏭️ Falta comparar el detalle contra el código —el arranque en `Z0` y la pasada final
plana—, que es trabajo de implementación.

## 34.6 ⭐⭐⭐ Los dos extras: el escuadrado pasante con corrección y multipaso

`contorno_medio_izq_pasante_corr_izq/der_uni_ep_ph5` — **134 líneas cada uno**, el caso más
completo del lote. Confirma cinco reglas de una sola vez:

| | |
|---|---|
| **CAD forzado** | no hay `G41`/`G42` y la traza va desplazada ⇒ ✅ **§20**: con multipaso la UI fuerza CAD |
| **arcos de esquina** | 16 arcos = 4 esquinas × 4 pasadas, radio 2 ⇒ ✅ **§30.2** en CAD real y en cada pasada |
| **el reparto** | `Z−5 · −10 · −15 · −18` con `PH=5` sobre 18 ⇒ ✅ **§16.4**, ahora sobre un pasante |
| **el offset exterior** | `X−2` · `X402` · `Y402` · `Y−2`, rectas intactas ⇒ ✅ **§34.2** |
| **la cota del pasante** | `Z−18` = espesor ⇒ ✅ **§11** |

### ⭐⭐ Y trae algo nuevo: en un contorno CERRADO no hay retorno entre pasadas

```
G1 Y200.000 Z-5.000        <- cierra la pasada en el punto de arranque
G1 Z-10.000 F5000.000      <- baja y SIGUE: no sube, no vuelve
```

⇒ **El retorno «En la pieza» de §31 no aparece.** Y es lógico: en un cerrado el final coincide
con el arranque, así que **no hay que volver a ningún lado** — baja y arranca la pasada
siguiente.

⇒ ⭐ **Completa el modelo del multipaso**: `Conexión entre huecos` —y con ella el
`MillingRetractDistance`— **sólo actúa en geometría ABIERTA**.

### ⚠️ Y abre un hilo nuevo: hay DOS formas de resolver el lado de la corrección

| | recorrido | arcos | offset |
|---|---|---|---|
| `…_corr_izq_…` | `Y400 · X400 · Y0 · X0` — **horario** | `G2` | afuera |
| `…_corr_der_…` | `Y0 · X400 · Y400 · X0` — **antihorario** | `G3` | afuera |

Los dos van **por afuera** y lo que cambia es **el sentido de giro**. Y es coherente con el
nombre: `SideOfFeature` es el lado de la **herramienta respecto del avance**, y recorrer al
revés pone el material del otro lado.

> ⚠️ **CORREGIDO el 2026-09-11 — esto era un artefacto mío, y la regla es UNA sola.**
>
> Escribí que «Maestro tiene dos maneras de resolver el lado» porque §30.2 mostró el offset
> yendo **hacia adentro** con `Left` y acá va **hacia afuera** con `Left`. Comparé dos archivos
> con **dibujos distintos** — el mismo error que ya había cometido con los ocho
> `contorno_corr_*` del Grupo 14.
>
> **Dato de Fermín**: *el sentido de giro de la traza lo establece el PROGRAMADOR en función del
> tipo de material; para resolver el lado de la corrección, el método aconsejable es cambiar el
> lado del offset.* Y los dibujos lo confirman: las direcciones de los miembros son
> `+Y · +X · −Y · −X` en el `corr_izq` y `−Y · +X · +Y · −X` en el `corr_der` — **dos dibujos
> con sentidos opuestos**. Los dos `contorno_medio_izq_corr_*` sin multipaso, en cambio,
> comparten el dibujo exacto, y por eso ahí el recorrido no cambia (§34.3).

⇒ ⭐⭐⭐ **Queda UNA regla, y explica los dos casos que parecían contradecirse:**

```
SideOfFeature = el lado de la HERRAMIENTA respecto del AVANCE
```

Dado el sentido que trae el dibujo, eso determina solo si el offset cae adentro o afuera:

| | dibujo | avance en el primer tramo | `Left` cae |
|---|---|---|---|
| §30.2 (`corr_izq_CAD`) | antihorario desde `(0,0)` | `+X` por el borde inferior | a `+Y` = **adentro** ✅ |
| §34.6 (`corr_izq` pasante) | desde `(0,200)` hacia `+Y` | `+Y` por el borde izquierdo | a `−X` = **afuera** ✅ |

⇒ **No hay dos resoluciones: hay un dibujo distinto.** Y el modelo completo queda en cuatro
piezas independientes:

- el **dibujo** da el sentido de recorrido (decisión del programador, según el material);
- **`IsGeomSameDirection`** lo invierte si hace falta (§26.1);
- **`SideOfFeature`** da el lado de la herramienta respecto del avance ⇒ de ahí sale de qué lado
  cae el offset;
- el **`G41`/`G42`** sale de cruzar lado × sentido (§26.2), y sólo en modo C.N.

---

# 35. Los cierres del 2026-09-11 (tarde, desde la PC del CNC)

Cinco entregas: los siete del Grupo 1 re-postprocesados, la **helicoidal** sobre el círculo, el
**`.pgm` y el `.xxl`** del `Xmsg`, y el offset **interior** con fresas grandes — que resultó ser
**el quinto caso de fail-loud, y el primero con señal limpia en el `.pgmx`**.

## 35.1 🚨 QUINTO FAIL-LOUD: el offset interior imposible — y Maestro lo declara

Sobre el rectángulo de **50×50** con corrección **interior** (`G41`):

| herramienta | radio (`SVR`) | `50 − 2·radio` | `TrajectoryPath` del `.pgmx` |
|---|---|---|---|
| `E004` | 2 | 46 | **8 miembros** (4 rectas + 4 arcos, offset exterior) |
| `E001` | 9,18 | 31,64 | **4 miembros** (rectas, esquinas vivas) |
| **`E006`** | **40** | **−30** ⛔ | **`[]` — NINGUNO** |

### La advertencia, capturada

> **Atención.** Imposible crear la trayectoria de la herramienta para el trabajo Fresado.
> **El trabajo se ejecutará en la máquina aplicando la corrección definida por el CN.**

⇒ **Maestro declara que no puede calcular la traza y delega al control.** No es un descarte
silencioso como la cara inferior (§25.1): **avisa**. Pero el aviso queda en la pantalla.

### ⚠️ Y el ISO sale igual, sin ninguna marca

```
G0 X49.000 Y50.000
SVR 40.000            <- el radio real de la E006
G41
G1 X50.000 Y50.000 · G1 X100.000 · G1 Y100.000 · G1 X50.000 · G1 Y50.000
```

La **línea nominal** —el rectángulo exacto— más `G41` y `SVR 40.000`. ⇒ Le pide al control que
meta una fresa de **Ø80 dentro de un rectángulo de 50×50**. El CN tampoco puede.

⇒ 🚨 **Es el peor de los cinco casos de fail-loud**: los otros cuatro *descartan* algo; éste
**emite un programa imposible**, con el radio correcto y la trayectoria que no se puede
recorrer.

### ⭐⭐⭐ Pero la señal para el converter es limpia, y está en el archivo

```
operación con ToolpathList VACÍO  ⇒  Maestro no pudo calcular la traza  ⇒  RECHAZAR
```

**No hace falta validar geometría**: el `.pgmx` lo dice. El `E006` no tiene ni `Approach`, ni
`TrajectoryPath`, ni `Lift` — los otros dos sí. Es una comprobación de una línea.

⇒ ⭐⭐ **Segundo beneficio concreto del converter sobre Maestro** (el primero fue
`%DONTCARESPEEDV`, §16.1): Maestro avisa en pantalla y emite igual; el converter, por la
regla 4, **se detiene**. Y con un mensaje que puede nombrar la causa —herramienta demasiado
grande para el contorno— porque tiene el `SVR` y la geometría.

📌 De paso, la `E006` confirma el catálogo una vez más: su corte sale en **`F2000`**
(`FeedRate.Standard` = 2), contra los `F5000` de las otras.

## 35.2 ⭐⭐ La estrategia `Helicoidal`, derivada

Sobre el círculo de radio 100, pasante (18 mm), `PH = 5`:

```
G1 Z0.000                                    <- arranca en la SUPERFICIE
G3 X100 Y200 Z-2.500  I200 J200              <- media vuelta, baja PH/2
G3 X300 Y200 Z-5.000  I200 J200              <- media vuelta, baja PH/2  (vuelta completa: 5)
…  Z-7.500 · Z-10.000 · Z-12.500 · Z-15.000
G3 X100 Y200 Z-16.500 I200 J200              <- ⚠️ la última vuelta baja 1,5 por media
G3 X300 Y200 Z-18.000 I200 J200
```

```
cada media vuelta (G3 de 180°) baja PH/2
el resto se REPARTE en la última vuelta, no se agrega una pasada
```

Con 18 y `PH=5`: tres vueltas completas (5+5+5 = 15) y la última baja **3**, o sea **1,5 por
media vuelta**. ⇒ Es **distinto del unidireccional**, donde el resto era una pasada entera más
(§16.4).

### Y `Habilitar pasada final` agrega una vuelta completa PLANA

El `_hpf` agrega **dos `G3` sin `Z`** al final — una vuelta entera a la cota final, sin bajar,
para dejar la pared pareja. Dos líneas más (103 → 105).

⇒ ✅ **Valida el `HelicalMillingStrategySpec` del sintetizador** en sus dos campos principales:
`axial_cutting_depth` (`PH`) y `allows_finish_cutting` (`Habilitar pasada final`). El
`axial_finish_cutting_depth` (`UH`) de la helicoidal sigue sin fixture.

📌 Y contesta de hecho el pendiente «`Helicoidal` sobre una línea»: **se aplica a geometría
cerrada**, que es la única donde una hélice tiene sentido.

## 35.3 El `.pgm` y el `.xxl`: el conteo lo calcula la ETAPA 2

Llegaron los dos intermedios del `..._prof10_XMSG` (conteo **422**):

| | tamaño | qué es |
|---|---|---|
| `.xxl` | 1032 bytes | **texto legible**, 27 líneas |
| `.pgm` | 2900 bytes | **binario** con el texto de cada instrucción embebido |

### ⛔ Lo que queda descartado

- **El conteo NO está en el XXL.** El XXL escribe `XMSG N="" Q=0 I=0` — sin ningún número.
- **El conteo NO está en el PGM.** Buscado el `422` como entero de 2 y 4 bytes, en los dos
  endianness, en los 2900 bytes: **cero apariciones**. Y el `362` del `xISO` tampoco.

⇒ ⭐ **El conteo lo genera la etapa 2** —el generador de Xilog, al emitir el ISO— y no viaja en
ningún intermedio. Cierra la pregunta de *dónde* se calcula.

### 🔮 La hipótesis que queda, y el fixture que la cierra

El `XMSG` está en el **offset 2488** del PGM (de 2900). Si `N` fuera un desplazamiento sobre el
PGM, la constante sería `2488 − 422 = 2066`. **Con un solo PGM no se puede verificar.**

⇒ **El fixture que lo decide es UNO, y el `.pgmx` ya existe**:

```
postprocesar a PGM el archivo  Operaciones\R_PV_manual_op_xmsg_dos_largo.pgmx
```

Tiene **dos mensajes en un mismo programa**, con conteos **212** y **244** (§17.6). ⇒ En un solo
PGM hay **dos** `XMSG`, y la diferencia de sus offsets tiene que dar **32**. Si da, el conteo es
un offset del PGM y queda derivado sin necesitar más archivos; si no da, la hipótesis se cae.

📌 **Y encaja con el texto**: ese archivo tiene `Text = "Mensaje largo al operador"` (25) y
`"Otro texto"`, mientras el del Grupo 11 tiene el texto **vacío** —por eso el XXL mostraba
`N=""`, y no había contradicción con §17.6—. El PGM sí lleva el texto, así que el largo del
primer mensaje **corre el offset del segundo**: exactamente el `+largo(texto)` medido.

## 35.4 ✅ Los siete del Grupo 1, re-postprocesados

Renombrados a `…_x50_x350_y200_prof10` —que es lo que la traza dice— y con sus ISO nuevos, así
que **el par vuelve a ser consistente**: la línea 1 del ISO coincide con el nombre del archivo.
El corpus queda sin nombres que mientan.

---

# 36. Grupo 19 — el `Xmsg` en programas reales, y los incrementos se suman (2026-09-11)

Cinco archivos, y son justo los que el conteo necesitaba: **el `Xmsg` solo** en los tres modos
de paro, **`Xn` → `Xmsg` → `Xn`** (la secuencia de girar la pieza), y **el programa completo de
dos caras**.

## 36.1 El bloque mínimo del `Xmsg`, aislado del todo

Un programa con **un solo `Xmsg`** y nada más, contra el programa vacío:

| modo | `.pgmx` | qué agrega al ISO |
|---|---|---|
| `Ningún paro` | `Stop = Nothing` | `?%ETK[8]=1` · `G40` · **`$0?212S0I0D0?`** · `G4 F0` — **4 líneas** |
| `Paro con espera de start` | `Stop = NoUnlock` | ídem con **`S1`**, más **`M0`** — **5 líneas** |

⇒ ⭐ **La base del conteo queda confirmada en el caso más limpio posible: `212` en campo `A`**,
con el `Xmsg` como único elemento del programa. Y el `?%ETK[8]=1` + `G40` que en los otros
archivos venían del preámbulo de un mecanizado, acá aparecen solos: **son del bloque, no del
mecanizado**.

### ⚠️ Un nombre que mintió, atrapado por el atributo — y corregido el mismo día

`R_PV_A_manual_xmsg_solo_pdes` afirmaba `Paro con Desbloqueo` y el `.pgmx` decía
**`Stop = NoUnlock`** — el mismo que el `_pes`, y por eso los dos ISO salían **idénticos**.
`fixtures.md` §2 funcionando otra vez.

> ✅ **Corregido por Fermín**: el `.pgmx` ahora dice `Stop = Unlock` y el ISO emite
> **`$0?212S2I0D0?`**.

### ⭐⭐ Con eso los tres modos de paro quedan derivados en un programa MÍNIMO

| la UI | `.pgmx` | ISO | `M0` |
|---|---|---|---|
| `Ningún Paro` | `Nothing` | `$0?212`**`S0`**`I0D0?` | no |
| `Paro con Espera de Start` | `NoUnlock` | `$0?212`**`S1`**`I0D0?` | **sí** |
| `Paro con Desbloqueo y Espera de Start` | `Unlock` | `$0?212`**`S2`**`I0D0?` | **sí** |

El diff entre el `pes` y el `pdes` es **UNA sola línea** — el `S1` contra el `S2`. Nada más.

⇒ ⭐ **El desbloqueo no agrega ninguna instrucción al ISO**: la diferencia entre «espera de
start» y «desbloqueo y espera de start» vive **entera en el campo `S`**, y el control decide
qué hacer con ella. El `M0` es idéntico en los dos.

⇒ Confirma §18 (canal, Grupo 14) y lo **mejora**: allá el programa llevaba un canal y había
más ruido en el diff; acá el aislamiento es perfecto.

## 36.2 ⭐⭐ `Xn` → `Xmsg` → `Xn`: el incremento del `Xn` NO depende del valor

```
$0?257S1I0D0?        ⇒  257 = 212 + 45
```

Y el `Xn` que lo precede tiene **`X = -2500`**, mientras el `ops_tres` donde se midió el `45`
tenía **`X = -3700`**. **Mismo largo de texto emitido, valor distinto, mismo incremento.**

⇒ ✅ **Es exactamente el fixture que §17.6 pedía** —*«el mismo programa con `x-2500` en vez de
`x-3700`»*— y el resultado confirma la regla general del §18: **el conteo mide el largo del
texto que el ISO escribe, no el valor**. `X-2500.000` y `X-3700.000` tienen los mismos
caracteres.

⇒ Y el `45` del `Xn` pasa de *«observado una sola vez»* a **medido dos veces con valores
distintos**.

## 36.3 ⭐⭐⭐ El programa de dos caras, completo — y los incrementos se suman

`fresado_xn_xmsg_taladro_xn` es la **técnica real**, postprocesada de punta a punta:

```
T1 · SYN · M06 · […fresado del contorno con la E001, pasante…]
M5 · G0 G53 Z201.000 · G0 G53 X-2500.000        <- Xn: retira la cabina
$0?787S1I0D0? · G4 F0 · M0                      <- Xmsg: PARA y espera start
G0 G53 Z201.000 · […taladrado…]                  <- la otra cara
M5 · G0 G53 Z201.000 · G0 G53 X-3700.000 Y1000.000   <- Xn final
```

⇒ **Es el caso de uso que justifica todo el trabajo sobre el `Xmsg`**: el `M0` para la máquina,
el operario gira la pieza, y el start reanuda con el mecanizado de la otra cara. El converter
lo tiene medido.

### El conteo: `787`

```
787 = 212 (base) + 530 (el fresado) + 45 (el Xn)
```

⇒ ⭐ **Los incrementos se suman**, con dos elementos distintos antes del mensaje. El modelo
`N = base + Σ incrementos` queda confirmado en un programa realista.

⚠️ **El `530` no se puede verificar por separado** —no hay el mismo fresado con un `Xmsg`
inmediatamente detrás— así que sale por resta. Es plausible: ese fresado es el contorno de la
pieza con la `E001`, con lead en arco de radio 36,72 y coordenadas largas (`X163.280`,
`Y-37.720`, `X236.720`), o sea mucho texto emitido.

### 📌 Y una observación fina: el `Xn` emite la `Y` con el signo invertido

El `.pgmx` guarda `Y = -1000` y el ISO emite **`G0 G53 X-3700.000 Y1000.000`**. La `X` conserva
el signo (`-2500` → `X-2500.000`) y la `Y` lo invierte.

⚠️ Anotado como **observación**, no como derivación: es un solo caso, y el `Xn` es de la rama C
— conviene cruzarlo contra `operaciones_maquina.md` antes de darlo por regla. Si se confirma,
es una trampa de signo para el converter.

## 36.4 ✅ Y el test de ejecución queda listo para correr

El `xmsg_solo_pes` es el programa inocuo que hacía falta: **un solo mensaje con paro, sin
ningún mecanizado**. Ya está postprocesado.

Y al lado quedó preparado **`r_pv_a_manual_xmsg_solo_pes_nfalso.iso`**, idéntico salvo el
conteo:

```
$0?212S1I0D0?      ->      $0?999S1I0D0?
```

`999` tiene el mismo largo que `212`, así que **no se movió ni un byte** del resto del archivo
(sólo la línea 1, que lleva el nombre del programa, para que el par siga siendo consistente).

⇒ **Ejecutar los dos y comparar.** Si los dos paran y esperan start, el `N` **no bloquea el
byte-idéntico** y se declara divergencia deliberada, como `%DONTCARESPEEDV` (`CLAUDE.md` §4).
Si el falso da alarma o no para, el `N` es esencial y hay que ir al `.pgm` del
`xmsg_dos_largo` (§35.3).
