# Canal — rama D

**Documento vivo.** El **Canal**: la ranura que hace la **Sierra Vertical X** (herramienta
`082`). Segundo mecanizado de la rama D, después del perforado.

> **Por qué va detrás del perforado y no de los fresados** (Fermín, 2026-09-03): es un tipo de
> mecanizado distinto pero **pertenece al mismo cabezal**. Y lo dice la máquina, no nosotros:
> en `def.tlgx` la `082` es `KindOfTool = XilogBoringUnitTool` — cabezal perforador —, mientras
> la Sierra **Horizontal** (`E002`) es `XilogSpindleUnitTool` con `shStorePos = 2`, o sea que va
> al electromandril con cambio de herramienta. Todo lo que D1 derivó sobre el cabezal
> perforador —husos, máscaras de PLC, `SHF` del huso, `SHF[Z]=0` durante el bloque— se
> **hereda**, y el canal lo pone a prueba con una herramienta que no es una broca.

## 0. Estado

| | |
|---|---|
| ✅ derivado | **el bloque del canal** (§8): 52 líneas, y 8 de 8 predicciones |
| 🔮 predicho, sin confirmar | la cara única (Grupo 8) |
| ⛔ imposible | el canal en ángulo distinto de 0° (§11), y más profundo que 10 mm (§12) |
| ✅ derivado | **el sentido de corte y la cola** (§11): corta de X mayor a menor, y vuelve al final geométrico |
| ⏸ esperando a Fermín | los grupos 6 a 11 del lote D2 — **en campo `HG`** |
| ✅ descartado | el rechazo de la `082` del lote C: era del contexto `Xn` (§7) |
| ⛔ imposible | el Grupo 2 entero: sin herramienta no hay canal, y `Anchura` nunca se edita (§10) |

## 1. La ventana, capturada (2026-09-03)

`…\Reinvestigación\Mecanizados\Maestro UI - Canal.bmp` — pieza 400×400×18, sin herramienta
elegida todavía.

**En la cinta**, `Canal` vive en la pestaña **Operaciones**, grupo **`Fresado`**, entre
`Fresado` · **`Canal`** · `Corte con cuchilla` · `Vaciado` · `Galceado`. El grupo `Perforado`
es el de al lado y tiene una sola operación. ⇒ **la UI agrupa por familia de operación, no por
cabezal**: el canal está con los fresados aunque su herramienta esté en el perforador.

**El panel `Canal`**, campo por campo:

| sección | campo | valor en la captura |
|---|---|---|
| **Referencias** | (desplegable) | `Lado superior` |
| **Datos Canal** | `X punto inicio` | `0,000` |
| | `Y punto inicio` | `0,000` |
| | `X punto final` | `0,000` |
| | `Y punto final` | `0,000` |
| | `Anchura` | `0` — **en gris** |
| | `Profundidad` | `0` |
| | `Inclinación °` | **`90`** |
| | ☐ `Profundidad final` | sin marcar |
| | ☐ `Pasante` | sin marcar |
| **Corrección herramienta** | `Corrección izquierda` · `Corrección central` · `Corrección derecha` · `Corrección en longitud` | el **segundo** aparece activo |
| | ⦿ `Corrección C.N.` ○ `Corrección CAD` | C.N. — ⚠️ ver abajo |
| | ☐ `Rebaba` | `0,000`, en gris |
| **Datos tecnológicos** | `Información herramientas` | desplegable **vacío** + botón `Información completa` |
| | `Avanz.` · `Rotación (rpm)` | vacíos |

**Plegadas en esta captura**: `Estrategia` · `Acercamiento/Alejamiento` · `Datos avanzados` ·
`Datos máquina`. ✅ **Capturadas el mismo día con la herramienta puesta: §9.**

⚠️ **`Anchura` en gris** — dos lecturas posibles acá: que salga de la herramienta, o que esté
deshabilitada porque el desplegable de herramientas está vacío. ✅ **Contestado en §9: sale
de la herramienta.**

## 2. La nomenclatura queda fijada: **Canal**

Respuesta de Fermín (2026-09-03) a la pregunta de la regla 1: **en la UI de Maestro la
operación se llama `Canal`**. Con eso los cuatro nombres que circulaban se ordenan:

| nombre | qué es | veredicto |
|---|---|---|
| **`Canal`** | la operación en la UI | **el nombre** |
| `a:SlotSide` | el tipo en el `.pgmx` | de Maestro, intocable (regla 3) |
| `ChannelSpec` / `feature_name="Canal"` | nuestro sintetizador | coincide ✅ |
| «ranura lineal» | prosa de `docs/synthesize_pgmx_help.md` | descripción, no nombre |

### Y tres incongruencias que el lote tiene que resolver

Auditoría del `ChannelSpec` (`pgmx/synthesis/milling/channel.py`) contra la ventana:

| campo de la UI | nuestro spec | |
|---|---|---|
| `X/Y punto inicio` · `X/Y punto final` | `start_x/start_y/end_x/end_y` | ✅ |
| `Referencias` = `Lado superior` | `plane_name="Top"` | ✅ |
| `Profundidad` · `Profundidad final` | `target_depth` · — | ⚠️ **son `StartDepth`/`EndDepth`, los dos extremos de una rampa (§12)**. Nuestro spec tiene una sola profundidad |
| `Pasante` | `is_through` (booleano) | ⚠️ **Maestro lo escribe como expresión `dz1 / Sin(90)` + valor resuelto (§12)**, no como flag |
| `Acercamiento/Alejamiento` | `approach` / `retract` | ✅ |
| **`Anchura`** (en gris, `3,8`) | `tool_width = 3.8` **como parámetro de entrada** | ⛔ **CONFIRMADA (§9)**: la UI no lo deja poner, sale del disco. No es un parámetro nuestro |
| **`Inclinación °`** = `90` | `slot_angle = 1.5707963267948966` | ⚠️ el nombre no dice inclinación, y va en radianes contra grados |
| **`Corrección herramienta`**: cuatro botones | `side_of_feature`: `Center`/`Right`/`Left` | ✅ **RESUELTA (§13)**: son **tres valores + un interruptor**. El campo coincide; **falta modelar `IsPrecise`** |
| `Corrección C.N.` / `Corrección CAD` | `ActivateCNCCorrection` del `.pgmx` | ⭐ **lo decide la HERRAMIENTA (§10)**, no el usuario: la ventana no ofrece la opción (§9) |
| `Rebaba` | `side_offset` ← `SideOffset` | ✅ **CONFIRMADO (§13)**. Ojo: sólo actúa si `SideOfFeature` no es `Center` |
| `Corrección en longitud` | — | ⛔ **FALTA (§13)**: es `IsPrecise`, y el `ChannelSpec` no lo modela |
| — | `end_radius = 60` | ✅ **RESUELTO (§10)**: no es parámetro, es el radio del disco — y el *tipo* de extremo lo elige la herramienta |
| — | `material_position = "Left"` | ⚠️ no está en la parte visible de la ventana |

⚠️ **Y todos los defaults del `ChannelSpec` son de la época congelada.** Son hipótesis, no
evidencia: el lote los re-deriva o los tira.

## 3. Lo que la configuración ya dice, antes del primer fixture

Dos archivos de máquina describen la sierra por completo. **Ninguno es una constante nuestra**
(regla 4), y el primero **viaja dentro de cada `.pgmx`**.

### `def.tlgx` — el catálogo

| dato | valor |
|---|---|
| `ToolKey` | `082` · `KindOfTool = XilogBoringUnitTool` |
| `ToolBody` | **`UniversalBlade`** — un disco, no una fresa |
| `BladeThickness` | **3.8** |
| `Diameter` | 120 |
| `ToolOffsetLength` | **60** |
| `SinkingLength` | 10 |
| `SpindleSpeed` | min 4000 · **std 4000** · max 6000 |
| `FeedRate` | 5 · 5 · 5 |
| `HandOfCut` | `Right` · `DirectionOfWork` `Left` · `NumberOfTeeth` 1 |
| `shPlcOut` | **37** |
| `st_OFace` | **`Face1 = true`**, `Face2…Face5 = false` |

⇒ **La sierra sólo trabaja la cara 1 (superior)**, y lo dice el catálogo. Es el mismo mecanismo
que dejó a la cara inferior sin huso en el perforado (§7quinquies de `perforado.md`), pero al
revés: acá el límite es de la **herramienta**, no de la cara.

### `spindles.cfg` — el registro 82

Mismo formato que los husos del perforado (1000 registros de 42 líneas):

| pos | valor | lectura (por analogía con D1) |
|---|---|---|
| 0 | **82** | número de herramienta |
| 1 | **37** | número de PLC ⇒ la máscara |
| 2 | 3 | tipo (las brocas tienen 1) |
| **22** | **90.00** | ⭐ coincide con la `Inclinación °` de la ventana |
| 23 | 96.00 | ⇒ `SHF[X] = −96.000` |
| 24 | −128.85 | ⇒ `SHF[Y] = +128.850` |
| 25 | −22.15 | ⇒ `SHF[Z] = +22.150` |

> 📌 ~~La `082` tiene el mismo offset X que la broca `006` (96.00), que sí entra en campo `A`
> ⇒ el canal en campo A no debería toparse.~~
> ⛔ **REFUTADA el 2026-09-03: el canal en campo `A` NO postprocesa** (§8). El error estaba en
> comparar herramientas en vez de coordenadas — la `006` entra porque sus fixtures están en
> X=100. Con el offset 96, en campo `A` el límite del eje X cae en **X ≈ 79.85** de la pieza.

## 4. Un canal real, leído de la producción

⚠️ **Esto NO es un fixture.** Son ISO del taller: no sé de qué `.pgmx` salieron —probablemente
X-CAB vía XConverter, que es la rama F, diferida— ni qué se varió. Sirven para **formar
hipótesis falsables**, como el fixture mal guardado del §7 de `perforado.md`. No se deriva de
acá.

`grep "SVR 1.900"` sobre `P:\USBMIX` da **3157 ISO**, de `Prod 2023` a `Prod 2026`: los
`fondo.iso` y `lado_*.iso` de casi todos los muebles. El bloque es siempre el mismo:

```
?%ETK[0]=0
?%ETK[6]=82
?%ETK[17]=257
S4000M3
?%ETK[1]=16
MLV=2
SHF[X]=-96.000
SHF[Y]=126.950
SHF[Z]=22.150
G0 X891.550 Y500.100
G0 Z80.000
D1
SVL 60.000
VL6=60.000
SVR 1.900
VL7=1.900
G1 Z-10.000 F2000.000
?%ETK[7]=1
G1 X7.550 Z-10.000 F5000.000
G1 Z20.000 F5000.000
G0 Z20.000
D0
SVL 0.000 · VL6=0.000 · SVR 0.000 · VL7=0.000
?%ETK[7]=0
```

**Contra el bloque del taladro** (`perforado.md` §4): no hay `T`, ni `SYN`, ni `M06` —cabezal
perforador, confirmado—, pero **sí hay `D1`/`SVL`/`SVR`**, que el taladro no emite. Y la
máscara del huso cambió de registro: **`ETK[1]`, no `ETK[0]`**.

`?%ETK[7]` —el tipo de mecanizado— vale **`1`**, contra `3` del taladrado y `4` del fresado.

## 5. Predicciones falsables

Todas salen de la configuración, y todas se contestan con el Grupo 1 del lote.

| | predicción | de dónde |
|---|---|---|
| P1 | `?%ETK[6] = 82` | número de herramienta, como el huso en D1 |
| P2 | `?%ETK[1] = 16` y `?%ETK[0] = 0` | `shPlcOut = 37`, y **2^(37−33) = 16** ⇒ `ETK[0]` lleva los bits 1-32 y **`ETK[1]` los 33-64**. Es la extensión natural de `?%ETK[0] = 2^(pos1 − 1)` de `perforado.md` §Grupo 6 |
| P3 | `SVL 60.000` | `ToolOffsetLength` del catálogo |
| P4 | **`SVR 1.900` = `BladeThickness / 2`** | ⭐ **cierra la excepción abierta en `anatomia_iso.md`**: `SVR` es el radio del *cuerpo* de la herramienta. La vertical es un `UniversalBlade` (mitad del ancho de corte) y la horizontal está catalogada como `Endmill` (mitad del diámetro, 50). No son dos reglas: es una, sobre dos cuerpos distintos |
| P5 | `S4000M3` | `SpindleSpeed.Standard` |
| P6 | `SHF[X] = −96.000` · `SHF[Z] = +22.150` | `−pos23` / `−pos25`, la regla de D1 |
| P7 | `SHF[Y] = −pos24 − 1.9 = 126.950` | ⚠️ **la única que rompe la regla de D1**: el espesor del disco entra **dos veces**, en el `SVR` y en el `SHF[Y]`. Puede ser que dependa de la `Corrección herramienta` — lo decide el Grupo 4 |
| P8 | el canal sólo existe en la **cara superior** | `st_OFace.Face1 = true` |
| P9 | `?%ETK[7] = 1` | el tipo de mecanizado del canal |

## 6. Lo que el lote tiene que decidir

- **El sentido de corte**: la doc de la época congelada afirma que el postprocesador
  «normaliza el recorrido para cortar en el único sentido compatible con la rotación de los
  dientes». `HandOfCut = Right` está en el catálogo. Si es cierto, el converter **no puede**
  copiar el sentido del `.pgmx`.
- **La entrada y la salida del disco**: los ISO de producción muestran una cola de cuatro
  movimientos (subir, volver 0.75 mm atrás, bajar otra vez) que aparece en unos archivos y en
  otros no. Un disco de Ø120 entrando 10 mm no puede empezar la ranura a pique.
- **Si `Anchura` la pone la herramienta o el usuario.**
- **Los cuatro botones de `Corrección herramienta`**, y dónde cae el 1.9.
- **`Corrección CAD`**: el caso donde la traza guardada ya trae el offset (regla 5).
- **La `Inclinación °`**: si la ventana la deja mover, y si el ISO cambia.
- **El incremento del conteo del `Xmsg`** para un canal — sin eso no hay byte-idéntico en
  programas con mensaje.

## 7. ✅ El rechazo de la `082` era del contexto, y queda descartado

En el lote C, `R_PV_manual_op_XN_x-3700_Ab_T082` —un `Xn` con la herramienta `082`— **no
postprocesó**:

```
[23,5] - Bag.Oheads: Herramienta E82 no configurada
```

(`operaciones_maquina.md` §14.) Eso hacía dudar de todo este lote. **Descartado por Fermín
(2026-09-03): el rechazo es del contexto `Xn`, que pide la herramienta como herramienta de
cabezal —`Oheads`—, no del mecanizado.** En un canal la `082` se usa como unidad del
**perforador**, que es donde `def.tlgx` la declara y donde `spindles.cfg` le da registro
(el 82), y el taller corta canales con ella desde 2023.

⇒ **El lote D2 va derecho**, sin compuerta en el Grupo 1.

⇒ Y **corrige hacia atrás una afirmación de la rama C**: el §14 de `operaciones_maquina.md`
decía que la `082` «no está configurada en la máquina», y no es así — no está configurada
**en el cabezal que el `Xn` usa**. La consecuencia para el converter cambia de forma: el
chequeo no es *«¿existe la herramienta?»* sino *«¿existe en el cabezal que esta operación
usa?»*. Anotado allá con fecha.

> ⚠️ Lo que sigue sin estar derivado con evidencia nuestra es **la línea de corte misma**. Que
> la herramienta se pueda usar lo sabemos por producción y por Fermín; qué emite el ISO para
> un canal controlado lo dice el lote.

---

## 8. Grupo 1 — el bloque del canal, derivado (2026-09-03)

Primer fixture del lote D2, hecho por Fermín. **Dos archivos**: el mismo canal en campo `A`
—que **no postprocesa**, y quedó guardado con la captura del error— y en campo `HG`, que sí.
Canal de **(50, 200) a (350, 200)**, profundidad 10, herramienta `082`, pieza 400×400×18,
origen 0/0/0.

### ⛔ El rechazo en campo `A` era predecible, y mi predicción estaba mal

```
[6,8] - ChkPgm línea 29: Microinterruptor- de tope eje X (T= 82)
```

Es el mismo tope que rechazó la broca cónica y la `061` (`perforado.md` §Grupo 6). La cuenta:

```
50 − 3685.850 − 96 = −3731.850    contra AP_MINQUOTA del eje X = −3702.000   ⇒ se pasa 29.85
```

⇒ **En campo `A` la sierra no puede ir a la izquierda de X ≈ 79.85 mm de la pieza.**

📌 **Corrección mía.** El §3 decía «el canal en campo A no debería toparse» porque la `082`
comparte el offset X (96.00) con la broca `006`, que sí entra en `A`. **La comparación estaba
mal planteada**: la `006` entra porque sus fixtures están en **X=100**, no porque su offset
alcance. El límite no lo fija la herramienta sola, sino **la coordenada más a la izquierda que
esa herramienta tiene que alcanzar** — y yo comparé herramientas en vez de coordenadas.

⇒ Cuarta confirmación de que **el rechazo se anticipa desde la configuración**, y
⚖️ **decisión de Fermín: de acá en adelante todo el lote D2 va en campo `HG`.**

### El bloque: 52 líneas, insertadas de una

El diff contra el programa vacío en `HG` (`perforado.md` Grupo 0, 43 líneas) es limpio: cambia
la línea 1 (el nombre) y se insertan **52 líneas** después de la 21. El ISO queda en 95.

```
?%ETK[8]=1 · G40                    <- dos pares mas de preambulo de bloque
?%ETK[8]=1 · G40
?%ETK[6]=82
G17
MLV=2 · %Or[0].ofX/Y/Z              <- el segundo bloque de origen, como en el perforado
MLV=1 · SHF[X]/[Y]/[Z]              <- ojo: SHF[Z]=18.000, SIN el +%ETK[114]/1000
MLV=2
?%ETK[17]=257
S4000M3
?%ETK[1]=16
MLV=2 · SHF[X]=-96.000 · SHF[Y]=126.950 · SHF[Z]=22.150
G0 X350.000 Y200.000
G0 Z80.000
D1 · SVL 60.000 · VL6=60.000 · SVR 1.900 · VL7=1.900
G1 Z-10.000 F2000.000
?%ETK[7]=1
G1 X50.000 Z-10.000 F5000.000       <- el corte
G1 Z20.000 F5000.000                <- y la cola de cuatro movimientos
G1 X349.250 Z20.000 F5000.000
G1 X350.000 Z20.000 F5000.000
G1 Z20.000 F5000.000
G1 Z-10.000 F5000.000
G0 Z20.000
D0 · SVL 0.000 · VL6=0.000 · SVR 0.000 · VL7=0.000
?%ETK[7]=0 · G61 · MLV=0 · ?%ETK[1]=0 · ?%ETK[17]=0
G4F1.200 · D0 · G0 G53 Z201.000 · G64
```

### Las predicciones: 8 de 8

| | predicción | ISO | |
|---|---|---|---|
| P1 | `?%ETK[6] = 82` | `?%ETK[6]=82` | ✅ |
| P2 | `?%ETK[1] = 16` | `?%ETK[1]=16` | ✅ |
| P3 | `SVL 60.000` | idem | ✅ |
| P4 | `SVR 1.900` = `BladeThickness/2` | idem | ✅ |
| P5 | `S4000M3` | idem | ✅ |
| P6 | `SHF[X] = −96.000` · `SHF[Z] = +22.150` | idem | ✅ |
| P7 | `SHF[Y] = −pos24 − 1.9 = 126.950` | idem | ✅ · y §13 muestra que **el 1,9 de la corrección es otro**, en la traza |
| P9 | `?%ETK[7] = 1` | idem | ✅ |
| P8 | sólo cara superior | — | ⏸ Grupo 8 |

⇒ **La sierra queda descrita entera por la configuración**: `def.tlgx` —que viaja dentro del
`.pgmx`— y el registro 82 de `spindles.cfg`. Ni una constante interna (regla 4).

📌 **Refinamiento de P2**: `?%ETK[0]` **no se emite** en el bloque del canal. En los ISO de
producción aparecía un `?%ETK[0]=0` justo antes, pero era el cierre del bloque de taladrado
anterior, no parte de éste.

### ⭐⭐ El sentido de corte se NORMALIZA — y no está en el `.pgmx`

El canal se creó de **(50,200) a (350,200)** —la ventana lo muestra así— y el ISO **posiciona
en X=350 y corta hacia X=50**. Lo confirma el `.pgmx`: la trayectoria guardada es
`1 50 200 8 1 0 0`, o sea arranca en 50 y va en **+X**.

⇒ **La inversión la hace el postproceso, no el programa.** Es la primera confirmación con
evidencia de la época nueva de lo que la doc congelada afirmaba: el recorrido se normaliza al
único sentido compatible con la rotación del disco (`HandOfCut = Right` en el catálogo).

⇒ **El converter no puede copiar el sentido del `.pgmx`: tiene que aplicar la regla.** Falta
saber cuál es —¿siempre de X mayor a X menor, o depende de algo?—; lo contesta el Grupo 3, y
el `Invertir` del Grupo 10 dice si el usuario puede forzarlo.

### ⭐ La Z del canal no es la del taladro

| | taladro | canal |
|---|---|---|
| `SHF[Z]` del bloque | **0** (contra la mesa) | **22.150** (offset del huso) |
| `SHF[Z]` del programa | `18.000+%ETK[114]/1000` | **`18.000`**, sin el término |
| cota de corte | `espesor − prof + tool_offset` = **85.000** | **`−10.000`** = −profundidad |
| aproximación | `espesor + seguridad + tool_offset` = 115.000 | **`80.000`** |
| retracción entre movimientos | `Z115.000` | **`Z20.000`** = el plano de seguridad |

⇒ En el canal la Z va **desde la cara de la pieza y hacia abajo en negativo**, y el largo de la
herramienta entra por el `SHF[Z]` del huso, no por la cota.

🔮 **Hipótesis con mecanismo para el `G0 Z80.000`**: `60 + 20` = el **radio del disco** más el
plano de seguridad. Un disco de Ø120 tiene que levantar su radio entero para despejar. La
contesta el Grupo 4: con profundidad 5 el 80 se mueve o no.

### La cola de cuatro movimientos, ahora con fixture

Después de cortar sube a `Z20`, retrocede a `X349.250` —**0,75 mm** antes del punto de
arranque—, vuelve a `X350.000`, y **baja otra vez a `Z−10` sin cortar** antes de subir.

Es **el mismo 0,75 de los ISO de producción**, en otra pieza y otro campo ⇒ no es del programa,
es del mecanizado. **Sigue sin explicación**: 0,75 no es ninguna cota del catálogo de la `082`
(3,8 · 120 · 60 · 10). El Grupo 4 dice si escala con la profundidad.

### ⭐ Y el `.pgmx` de Maestro coincide con el de nuestro sintetizador

Las **ocho** geometrías serializadas son idénticas carácter por carácter:

| | |
|---|---|
| geometría de la feature | `8 0 300 / 1 50 200 0 1 0 0` |
| `Approach` | `8 0 30 / 1 50 200 38 0 0 -1` |
| `TrajectoryPath` | `8 0 300 / 1 50 200 8 1 0 0` |
| `Lift` | `8 0 30 / 1 350 200 8 0 0 1` |

📌 **Corrección de mi propio planteo.** Yo había dicho que para el canal «la traza ES la
incógnita» (regla 5), porque un disco de Ø120 no puede entrar a pique. **La evidencia dice que
sí entra a pique**: ni Maestro ni nosotros guardamos geometría de disco — la trayectoria
almacenada es la línea nominal más una bajada vertical, y todo lo que el disco necesita lo pone
el postproceso.

⚠️ Vale **para el caso con defaults**. `Rebaba`, la corrección de herramienta y `Canto a canto`
todavía pueden cambiar lo que se guarda, y ahí la regla 5 vuelve a aplicar. El resto del lote
se sigue haciendo a mano (decisión de Fermín), y con cada fixture se puede volver a chequear.

## 9. La ventana con la herramienta puesta (2026-09-03)

Cuatro capturas nuevas, con la `082` elegida. **La ventana cambia según la herramienta:**

- ✅ **`Anchura` = `3,8`, en gris** ⇒ el ancho **sale del disco** (`BladeThickness`), no del
  usuario. Cierra la duda del §1 y confirma la incongruencia del `ChannelSpec`: `tool_width`
  **no es un parámetro de entrada**.
- ⭐ **La sección `Estrategia` DESAPARECE**, y también los radios **`Corrección C.N.` /
  `Corrección CAD`**. Con el desplegable de herramientas vacío estaban; con la sierra, no. La
  sierra no tiene estrategia de fresado ni elección de corrector.
- **`Acercamiento/Alejamiento`**: `Habilitar` **destildado** en los dos —confirma el default
  del `ChannelSpec`—, y adentro `Entrada`/`Salir` = `Lineal`, `Acercamiento`/`Alejamiento` =
  `En cota`, `Sobreposición` = 0 y **`Multipl. radio` = 4**, que es el `RadiusMultiplier` del
  `UI00.exe.Config` del CNC (la PC de oficina técnica tiene 2 — ver la pregunta abierta de la
  hoja de ruta).
- **`Datos avanzados`**: `Invertir trabajo` → `Invertir`; `Canto a canto` → `Habilita canto a
  canto` + `Extra dist. inicial` / `Extra dist. final`; y **`Condición` = `True`**, que es el
  nodo `IF` del árbol del proyecto. **Ninguno estaba en el lote** ⇒ Grupo 10.
- **`Datos máquina`** → `Funciones máquina`: `Jerk`, `Jerk3D`, `Campana neumática`, `Campana
  auxiliar`, `Frenos ejes rotativos`, desenrollado del cabezal, `Soplador herramienta`,
  `Palpador electrónico`, regulación de velocidad. **Todas con `Selecciona` destildado**, o sea
  que ninguna interviene en lo derivado hasta acá. Son una familia de fixtures futura.
- **`Información herramientas` muestra `082(082)`** — el par que separaría `name` de
  `holder_key`, acá idénticos.

## 10. Grupo 2 — el canal SIEMPRE lleva herramienta, y la herramienta decide tres cosas (2026-09-04)

El Grupo 2 pedía dos fixtures y **ninguno de los dos se puede hacer**. Los dos negativos vienen
**con testigo** (capturas), así que se leen como derivados y no como probables.

### ⛔ Sin herramienta no hay canal

Al vaciar el desplegable `Información herramientas` **el botón `Aplicar` se deshabilita**: la
modificación no se puede completar. ⇒ **un `Canal` siempre lleva una herramienta explícita.**

⇒ Y con eso se cae la analogía con el perforado, donde el postprocesador **resolvía la broca
solo** a partir del diámetro y la punta. Acá no hay resolución automática que derivar: **el
converter puede contar con que el `.pgmx` trae el `ToolKey` del canal.**

### ⛔ Y `Anchura` no es editable ni con el desplegable vacío

Sigue en gris y **conserva el `3,8` de la sierra** aun después de sacar la herramienta. No hay
forma de pedir un canal «de tal ancho» y que Maestro elija la herramienta.

### ⭐ El par que salió por accidente: `082` contra `E004`

El archivo guardado como `…_NT_…` **no quedó sin herramienta: quedó con la `E004` (Fresa 4 mm,
ID 1903)**. El nombre afirma una cosa y el `.pgmx` dice otra — el caso que la regla del
`fixtures.md` §2 describe, atrapado por la auditoría.

Y como todo lo demás quedó igual, es **un par controlado**: dos canales idénticos que difieren
sólo en la herramienta. El `.pgmx` cambia en **cuatro cosas**:

| | `082` (Sierra Vertical X) | `E004` (Fresa 4 mm) |
|---|---|---|
| `ToolKey` | ID 1899 · `082` | ID 1903 · `E004` |
| `Width` | **3.8** | **4** |
| `SlotEndType` | `WoodruffSlotEndType` con `Radius` **60** | **`RadiusedSlotEndType`**, sin radio |
| `ActivateCNCCorrection` | **false** | **true** |

⇒ **Tres derivaciones**, y las tres tocan al `ChannelSpec`:

1. ⭐ **`Anchura` sigue a la herramienta**: 3.8 es el `BladeThickness` del disco, 4 es el
   diámetro de la fresa. Confirma lo del §9 desde el otro lado: **`tool_width` no es un
   parámetro de entrada nuestro**, es un dato derivado del catálogo.
2. ⭐ **`end_radius = 60` tampoco es un parámetro**: es el **radio del disco** (120/2), y el
   *tipo* de extremo lo elige la herramienta — `Woodruff` es el corte curvo que deja un disco,
   `Radiused` el extremo redondo de una fresa. Cierra la última fila abierta de la auditoría
   del §2.
3. ⭐⭐ **`ActivateCNCCorrection` depende de la herramienta**: `false` con la sierra, `true` con
   la fresa. **Es el campo exacto de la regla 5 del `CLAUDE.md`.**

> 📌 **Matiza el §8.** Ahí escribí que la traza del canal «no era la incógnita» porque el
> `.pgmx` de Maestro y el nuestro guardaban las mismas ocho geometrías. Eso vale **porque la
> corrección estaba en el botón del medio y el offset era cero**. Con `ActivateCNCCorrection`
> en `false` —el caso de la sierra—, en cuanto el Grupo 5 mueva la corrección **la trayectoria
> guardada va a traer el ±1,9 ya aplicado**, y ahí la regla 5 rige de lleno: esos fixtures los
> tiene que hacer Fermín, no el sintetizador.

### ⭐⭐ El desplegable ofrece OCHO herramientas, no una

`082(082)` · `E001(Widea 18 mm)` · `E002(Sierra Horiz.)` · `E003(Fresa Violeta)` ·
`E004(Fresa 4 mm)` · `E005(Fresa 45º)` · `E006(Rectificado)` · `E007(Recta 50mm)`

⇒ **El canal no es «el mecanizado de la sierra vertical»**: es una operación que acepta también
las herramientas del **electromandril**. Y eso abre dos cosas grandes:

- un canal con `E00x` tiene que emitir un bloque **con cambio de herramienta** (`T`, `SYN`,
  `M06`), como el fresado — o sea que el `Canal` produce **dos formas de bloque distintas**
  según el cabezal de su herramienta;
- ⭐ y la `E002` **falsa la regla del `SVR`** con un solo archivo: si `SVR` es el radio del
  *cuerpo*, la Sierra Horizontal está catalogada como `Endmill` de Ø100 ⇒ tiene que dar
  **`SVR 50.000`**, que es justo lo que muestran los ISO del taller. Si diera 1.9 o cualquier
  otra cosa, la derivación P4 se cae.

⇒ **Grupo 11** en el lote.

> El formato del desplegable es `Key(Descripción-Key)`, y la `082` sale como `082(082)` porque
> su `<Description />` está vacía en `def.tlgx` — lo mismo que ya había pasado con las brocas
> `058`/`059` en el perforado.

### 📌 El `Corrección C.N.` / `Corrección CAD`, cerrado

Primero escribí que los radios desaparecen **con la sierra elegida**; después apareció que
tampoco están **con el desplegable vacío**. Están en **una sola** de las cinco capturas: la
primera de todas, el panel recién abierto, sin operación creada. Y **Fermín confirma que la
ventana no ofrece esa opción** (2026-09-04).

⇒ **Editando un canal, el usuario NO elige el tipo de corrección.** Qué estado del panel
mostraba esos radios queda sin explicar, y da igual: lo que decide es la herramienta, y eso
está medido en el `.pgmx` — `ActivateCNCCorrection` vale `false` con la sierra y `true` con una
fresa (arriba).

## 11. Grupo 3 — el sentido, la cola, y los dos ángulos que la sierra no hace (2026-09-04)

Cinco `.pgmx` en campo `HG`, herramienta `082`, profundidad 10: el mínimo repetido como
referencia del grupo, el mismo al revés, uno perpendicular, uno diagonal y uno que sale de la
pieza por los dos lados.

**Los cinco nombres dicen la verdad.** Verificado leyendo la geometría serializada de cada
`.pgmx`, no el nombre (regla de `fixtures.md` §2):

| archivo | punto de arranque | dirección | largo |
|---|---|---|---|
| `…_x50_x350_y200_prof10` | (50, 200) | `1 0 0` | 300 |
| `…_x350_x50_y200_prof10` | (350, 200) | **`-1 0 0`** | 300 |
| `…_y50_y350_x200_prof10` | (200, 50) | **`0 1 0`** | 300 |
| `…_diagonal_prof10` | (50, 50) | **`0.7071 0.7071 0`** | 424.264 |
| `…_x-20_x420_y200_prof10` | **(−20, 200)** | `1 0 0` | **440** |

Y los cinco comparten campo `HG`, `082`, ancho 3.8, `WoodruffSlotEndType`,
`ActivateCNCCorrection=false`, plano de seguridad 20 e `Angle` = π/2.

### ⛔ Dos rechazos, el mismo mensaje

El **perpendicular** y el **diagonal** no postprocesan:

```
[16,44] - xMETAdb: (Línea <= 29) Angulo no válido del perfil con herramienta de tipo fresa de disco
```

⇒ De los tres ángulos probados en el plano XY, **sólo el 0° pasa**: 45° y 90° se rechazan.
La «Sierra Vertical **X**» corta **paralela al eje X y nada más**, y ahora está derivado con
fixture, no leído del nombre de la herramienta.

⭐ **Y el rechazo es de Winxiso, no de Maestro.** El editor deja crear el canal, lo dibuja en la
pieza y lo guarda sin chistar; el que se planta es el **postproceso**. ⇒ **un `.pgmx` válido
puede traer un canal imposible**, y el converter tiene que poder decir que no — es el caso de la
regla 4 (fail-loud), y esta vez con un mensaje de la propia máquina para imitar.

> 📌 **Nomenclatura**: la máquina llama a la `082` **«fresa de disco»**. Es el tercer nombre
> para la misma herramienta —`Sierra Vertical X` en el catálogo, `UniversalBlade` en el tipo
> del `.pgmx`, `fresa de disco` en el mensaje de Winxiso— y ninguno es nuestro.

### ✅ Control: el fixture es reproducible

El mínimo de este grupo y el del Grupo 1 —hechos por separado, con nombres distintos— dan ISO
**byte-idénticos salvo la línea 1**. El par es limpio.

### ⭐⭐ El corte va SIEMPRE de X mayor a X menor, y la cola es el REGRESO AL FINAL GEOMÉTRICO

Los tres ISO comparten el mismo corte físico y difieren **sólo** en la cola:

| creado | posiciona en | corta hacia | cola |
|---|---|---|---|
| 50 → 350 (**+X**) | `G0 X350.000` | `G1 X50.000` | **sí** — vuelve a 350 |
| 350 → 50 (**−X**) | `G0 X350.000` | `G1 X50.000` | **no** |
| −20 → 420 (**+X**) | `G0 X420.000` | `G1 X-20.000` | **sí** — vuelve a 420 |

⇒ **El sentido de corte está normalizado**: los tres cortan de X mayor a X menor, sea cual sea
el sentido en que se dibujó el canal. Confirma lo del §8 con tres casos en vez de uno.

⇒ ⭐⭐ **Y la cola de cuatro movimientos queda explicada**: la máquina termina dejando la
herramienta en el **punto final geométrico del canal**, bajada a la cota. Si el canal se dibujó
en −X, el corte termina justo ahí y no hay nada que agregar; si se dibujó en +X, el corte
termina en el extremo contrario y la máquina **vuelve** al punto final y vuelve a bajar.

```
G1 X50.000  Z-10.000 F5000     ← el corte, siempre de mayor a menor
G1 Z20.000  F5000              ← sube al plano de seguridad
G1 X349.250 Z20.000 F5000      ← vuelve, y se detiene 0,75 antes
G1 X350.000 Z20.000 F5000      ← llega al punto final geométrico
G1 Z20.000  F5000              ← (no mueve nada: ya está en 20)
G1 Z-10.000 F5000              ← y baja a la cota
G0 Z20.000
```

⇒ **Para el converter**: normalizar el sentido **no alcanza**. El `.pgmx` guarda el sentido
dibujado (`1 0 0` contra `-1 0 0`) y ese dato **sí llega al ISO** — no como dirección de corte,
sino decidiendo si hay cola. Hay que leerlo.

⇒ Y explica los ISO de producción: `fondo.iso` tiene la cola y `lado_izquierdo.iso` no. No eran
dos comportamientos: son dos canales dibujados en sentidos opuestos.

### ⭐ Cuando el canal excede la pieza no pasa nada especial

El de −20 a 420 da **el mismo ISO con otras coordenadas**: posiciona en `X420.000` —70 mm afuera
de la pieza, sobre la mesa—, baja a pique y corta hasta `X-20.000`. **El postprocesador no
agrega ninguna entrada ni salida**: escribe las coordenadas que le diste.

⇒ Se cae la duda que traía el §8 («un disco de Ø120 no puede empezar la ranura a pique»): entra
a pique, y **si querés que el disco entre desde afuera, extendés la línea vos**. Es exactamente
lo que hace la producción, que corta de 891,55 a 7,55 o hasta −10.

### 🚧 El `0,75`, acotado pero sin explicar

Aparece en los dos que tienen cola, y **es el mismo número**: 350 → 349,250 y 420 → 419,250.
No escala con el largo del canal (300 contra 440) ni con la posición, y en los ISO del taller es
también 0,75. Queda como **constante del regreso**, sin procedencia. El Grupo 4 dice si se mueve
con la profundidad.

## 12. Grupo 4 — el canal puede ser una RAMPA, y el disco tiene un tope de 10 mm (2026-09-04)

Seis `.pgmx`, cuatro con `.iso` y dos rechazados con captura. Fermín amplió el grupo por su
cuenta cruzando `Profundidad` con `Profundidad final`, que es justo lo que hacía falta para
separarlas.

| archivo | `StartDepth` | `EndDepth` | |
|---|---|---|---|
| `…_prof10` | 10 | 10 | ✅ la base |
| `…_prof5` | 5 | 5 | ✅ |
| `…_prof10_pf5` | 10 | **5** | ✅ |
| `…_prof5_pf10` | **5** | 10 | ✅ |
| `…_pf15` | 10 | **15** | ⛔ rechazado |
| `…_pasante` | **18** | **18** | ⛔ rechazado |

### ⭐⭐ `Profundidad` y `Profundidad final` son los dos extremos de una rampa

En el `.pgmx` son dos campos, `StartDepth` y `EndDepth`, y **la trayectoria guardada se
inclina**: con 10 y 5 la dirección pasa de `1 0 0` a `0.99986 0 0.016664` y el largo de 300 a
**300.0417** = √(300² + 5²).

En el ISO, y recordando que el corte va del extremo geométrico FINAL al INICIAL:

```
G1 Z-5.000  F2000.000            ← baja en X=350 a −EndDepth
G1 X50.000 Z-10.000 F5000.000    ← corta hasta X=50 bajando a −StartDepth (interpolado)
…
G1 Z-5.000  F5000.000            ← y la cola vuelve a X=350 y baja a −EndDepth
```

⇒ **`Profundidad` es la del punto de INICIO geométrico y `Profundidad final` la del FINAL.**
Las dos lecturas —la del `.pgmx` y la del ISO— coinciden, y el par cruzado (10/5 y 5/10)
descarta que sea al revés.

⇒ Y refina la regla de la cola del §11: la máquina deja la herramienta en el punto final
geométrico **bajada a la cota de ESE extremo**, no a la del corte.

### ✅ Lo que la profundidad NO mueve

Con 5 en vez de 10, el ISO cambia **sólo en las tres cotas Z** del bloque. Quedan iguales:

- ⭐ **el `G0 Z80.000`** ⇒ **no depende de la profundidad**. Sobrevive la hipótesis del §8:
  `60 + 20` = radio del disco más plano de seguridad;
- ⭐ **el `0,75` del regreso** ⇒ ahora es invariante en **largo, posición y profundidad**. Es una
  constante pura y sigue sin procedencia;
- el `Z20.000` de retracción, que es el plano de seguridad.

### ⛔ El tope: la longitud útil de la herramienta son 10 mm

Los dos rechazos dan el mismo mensaje:

```
[16,61] - xMETAdb: (Línea 22) Mecanizado en Z superior a la longitud útil de la herramienta
```

`pasante` pide 18 y `pf15` pide 15; **el `SinkingLength` de la `082` en `def.tlgx` es 10**.

⇒ **Quinto y sexto rechazo predecible desde la configuración**, y el primero que limita la
*profundidad*. Y se aplica a las **dos** cotas: `pf15` tiene `StartDepth` 10, válido, y lo
rechaza igual por el `EndDepth`.

⇒ **Un canal pasante con la sierra es imposible en esta máquina** salvo que la pieza tenga
10 mm o menos.

### ⭐⭐ `Pasante` no es un booleano: es una expresión paramétrica

El `.pgmx` del pasante no trae ningún flag. Trae una **`Parametrics.Expression`** que apunta al
`SlotSide` y a la propiedad compuesta `Depth.StartDepth`, con valor:

```
dz1 / Sin(90)
```

y el número resuelto (18) materializado en `StartDepth`/`EndDepth`.

⇒ **La `Inclinación` entra en la fórmula de la profundidad.** Con el disco a 90° el divisor es
1; inclinado, un pasante necesitaría el camino oblicuo por la placa. Es la primera evidencia de
que el campo `Inclinación °` **se usa** para algo más que validar el ángulo.

⇒ Y es un aviso para el sintetizador: nuestro `ChannelSpec` modela `is_through` como un
**booleano**, y Maestro lo escribe como expresión más valor resuelto. Hay que ver qué emite el
nuestro antes de darlo por equivalente.

## 13. Grupo 5 — los cuatro botones son TRES más UNO, y el segundo 1,9 aparece (2026-09-04)

Siete `.pgmx` con sus siete `.iso`. Fermín volvió a ampliar el grupo por su cuenta y esta vez
fue decisivo: en vez de cuatro archivos hizo **los tres primeros botones y los tres otra vez
combinados con el cuarto**, que es lo que destapó que el cuarto **no es un cuarto valor**.

### ⭐⭐ `SideOfFeature` + `IsPrecise`

**Los nombres de la UI** (Fermín, 2026-09-04, leídos de los tooltips):

| botón | nombre en la UI | campo del `.pgmx` |
|---|---|---|
| 1 | **`Corrección izquierda`** | `SideOfFeature = Left` |
| 2 | **`Corrección central`** | `SideOfFeature = Center` |
| 3 | **`Corrección derecha`** | `SideOfFeature = Right` |
| 4 | **`Corrección en longitud`** | `IsPrecise = true` |

⭐ **El nombre del cuarto describe exactamente lo que medimos**: corrige *en longitud*, que es
lo que hace — acorta el canal en las dos puntas. El campo del XML se llama `IsPrecise`, que no
lo dice.

> ⚠️ **Nomenclatura, para cuando se toque el `ChannelSpec`** (regla 1). Hay dos nombres
> legítimos para lo mismo: la UI dice `Corrección en longitud` y el `.pgmx` dice `IsPrecise`.
> El `ChannelSpec` ya viene nombrando sus campos por el **XML en snake_case**
> (`side_of_feature` ← `SideOfFeature`, `side_offset` ← `SideOffset`), así que lo consistente
> sería `is_precise`. **No lo cambio por mi cuenta**: queda anotado para decidirlo con Fermín
> junto con el resto de la corrección del spec.

Y lo que dice el archivo, leído del `.pgmx` y no del ícono:

| archivo | `SideOfFeature` | `IsPrecise` |
|---|---|---|
| `corr_1` | **`Left`** | false |
| `corr_2` | **`Center`** | false ← el default |
| `corr_3` | **`Right`** | false |
| `corr_1+4` · `corr_2+4` · `corr_3+4` | ídem | **true** |

⇒ **Resuelve la incongruencia del §2**: la ventana no tiene cuatro valores, tiene **tres más un
interruptor**. Nuestro `side_of_feature` (`Center`/`Right`/`Left`) es exactamente el campo de
Maestro ✅, y **lo que falta en el `ChannelSpec` es `IsPrecise`**.

### ⭐ La corrección lateral mueve la Y de la TRAZA, y aparece el segundo 1,9

| | `G0` del ISO |
|---|---|
| `Left` | `X350.000 Y`**`201.900`** |
| `Center` | `X350.000 Y200.000` |
| `Right` | `X350.000 Y`**`198.100`** |

±1,9 = **`BladeThickness / 2`**, y **el `SHF[Y]=126.950` no se mueve**.

⇒ **Los dos 1,9 son independientes**, que era la duda abierta de P7 (§5): el del huso está en el
`SHF` y es fijo; el de la corrección va en la **coordenada Y del movimiento**. No se pisan.

⇒ `Left` desplaza **+Y** y `Right` **−Y**, respecto del sentido en que se dibujó el canal
(acá 50→350, o sea +X).

### ⭐⭐ `IsPrecise` corrige la geometría del disco, con fórmula exacta

Con el cuarto botón activo el canal **se acorta en los dos extremos**:

```
G0 X350.000 → X316.834      y      G1 X50.000 → X83.166
```

**33.166247903553995 en cada punta**, y el `.pgmx` lo guarda con todos sus decimales
(`largo 233.66750419289201` contra 300).

Ese número es exactamente el avance horizontal que un disco necesita para llegar a la
profundidad:

```
√( p · (2r − p) )  =  √( 10 · (120 − 10) )  =  √1100  =  33.166247903553995
```

con **`p` = profundidad** y **`r` = `Diameter`/2 = 60** del catálogo. Coincidencia **a quince
dígitos**, así que no es un ajuste: es la fórmula.

⇒ **Qué significa**: sin `IsPrecise` la longitud pedida es la del **fondo** de la ranura —el
disco arranca a cortar antes y sale después, así que en la superficie la ranura es más larga—;
con `IsPrecise`, la longitud pedida es la de la **superficie**.

⇒ Y la cola del §11 sigue al extremo corregido: `X316.084` = 316.834 − **0,75**, el mismo
0,75 de siempre.

🔮 **Predicción falsable, barata**: con profundidad 5 el acortamiento tendría que ser
`√(5 · 115)` = **23.979**. Un solo fixture (`corr_2+4` con `prof5`) cierra la fórmula o la tira.

⚠️ Y abre un rechazo previsible: si el canal es **más corto que 2 × 33.166**, con `IsPrecise` la
trayectoria se daría vuelta. Sin fixture todavía.

### ⭐⭐ La regla 5, ahora con evidencia

Los seis llevan **`ActivateCNCCorrection = false`**, y **la trayectoria guardada YA trae la
corrección**: el `Approach`, el `TrajectoryPath` y el `Lift` de `corr_1` arrancan en
`Y 201.9`, y los de `+4` en `X 83.166`. La **geometría de la feature** —la línea nominal a
Z=0— queda intacta al lado, sin corregir.

⇒ Es exactamente el caso que describe la regla 5 del `CLAUDE.md`, y ahora está **medido**: si
estos fixtures los autorara el sintetizador, Maestro postprocesaría nuestra hipótesis de dónde
va el 1,9. Tienen que salir de Maestro, y salieron.

⇒ Y para el converter, la regla operativa: **el ISO sale del `Toolpath`, no de la geometría de
la feature.**

### ⭐ `Rebaba` es `SideOffset`, y sólo actúa si hay lado

Tres fixtures más de Fermín, uno por cada corrección lateral, con **`Rebaba` = 10**:

| | traza sin rebaba | con `Rebaba` 10 |
|---|---|---|
| `Corrección izquierda` | `Y 201.9` | **`Y 211.9`** (+10) |
| `Corrección central` | `Y 200.0` | **`Y 200.0`** — no se mueve |
| `Corrección derecha` | `Y 198.1` | **`Y 188.1`** (−10) |

⇒ **`Rebaba` → `SideOffset`**, que es el campo que la auditoría del §2 tenía como «sin
verificar» ✅. Se **suma al ±1,9** y lleva **el signo de la corrección lateral**.

⇒ ⚠️ **Con `Corrección central` el valor se guarda pero no hace nada**: el `.pgmx` trae
`SideOffset = 10` y la trayectoria es idéntica a la de `SideOffset = 0`. Para el converter:
`SideOffset` se aplica **según el lado**, y con `Center` se ignora. Es un negativo **con
testigo** —el valor está escrito en el archivo—, así que es derivado, no probable.

⏸ **Faltan los tres `.iso`.** El `.pgmx` ya muestra el desplazamiento en la traza, pero el par
completo confirma que llega al `G0` del bloque como los ±1,9 del Grupo 5.

> 📌 De paso aparecieron dos campos que todavía no tocamos: `OvercutLenghtInput` y
> `OvercutLenghtOutput` —el typo *Lenght* es de Maestro—, los dos en 0. Son candidatos a las
> `Extra dist. inicial` / `final` del `Canto a canto` (Grupo 10).

## 14. Lo que queda abierto

| | |
|---|---|
| `?%ETK[17]=257` | sale igual que en el perforado. Sigue sin variar |
| **el `0.75` de la cola** | invariante en largo, posición, profundidad **y corrección** (§11, §12, §13). Constante pura, sin procedencia |
| `end_radius = 60` · `material_position` | del `ChannelSpec` congelado, sin campo visible en la UI |
| ~~las cuatro secciones plegadas~~ | ✅ capturadas el 2026-09-03 (§9). `Estrategia` no existe con la sierra |
| ~~la regla del sentido de corte~~ | ✅ **RESUELTA (§11)**: siempre de X mayor a X menor |
| **el `G0 Z80.000`** | hipótesis: radio del disco + plano de seguridad. **No depende de la profundidad** (§12) |
| las `Funciones máquina` | nueve interruptores por operación, todos apagados. Familia de fixtures futura |
| **el acortamiento con `IsPrecise` a otra profundidad** | la fórmula predice 23.979 con prof 5. Un fixture la cierra |
| **un canal más corto que 2×33.166 con `IsPrecise`** | la trayectoria se daría vuelta. ¿Rechaza? |
| el `Corte con cuchilla` | operación vecina en la cinta, sin estudiar |
| **qué muestra los radios `Corrección C.N.`/`CAD`** | están en una captura de cuatro y no es la herramienta lo que los saca |
| **el canal con herramienta de electromandril** | ocho herramientas en el desplegable; sólo derivamos la sierra. Grupo 11 |
