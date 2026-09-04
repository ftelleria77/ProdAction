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
| ⛔ imposible | el canal en cualquier ángulo que no sea paralelo al eje X (§11) |
| ✅ derivado | **el sentido de corte y la cola** (§11): corta de X mayor a menor, y vuelve al final geométrico |
| ⏸ esperando a Fermín | los grupos 4 a 11 del lote D2 — **en campo `HG`** |
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
| **Corrección herramienta** | cuatro botones de ícono | el **segundo** aparece activo |
| | ⦿ `Corrección C.N.` ○ `Corrección CAD` | C.N. |
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
| `Profundidad` · `Pasante` | `target_depth` · `is_through` | ✅ |
| `Acercamiento/Alejamiento` | `approach` / `retract` | ✅ |
| **`Anchura`** (en gris, `3,8`) | `tool_width = 3.8` **como parámetro de entrada** | ⛔ **CONFIRMADA (§9)**: la UI no lo deja poner, sale del disco. No es un parámetro nuestro |
| **`Inclinación °`** = `90` | `slot_angle = 1.5707963267948966` | ⚠️ el nombre no dice inclinación, y va en radianes contra grados |
| **`Corrección herramienta`**: **cuatro** botones | `side_of_feature`: **tres** valores (`Center`/`Right`/`Left`) | ⚠️ falta uno — Grupo 5 |
| `Corrección C.N.` / `Corrección CAD` | `ActivateCNCCorrection` del `.pgmx` | ⭐ **lo decide la HERRAMIENTA (§10)**: `false` con la sierra, `true` con una fresa. Los radios no siempre están en la ventana y no sabemos qué los muestra |
| `Rebaba` | ¿`side_offset`? | ⚠️ sin verificar |
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
| P7 | `SHF[Y] = −pos24 − 1.9 = 126.950` | idem | ✅ |
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

### 📌 Una corrección al §9

Ahí escribí que los radios `Corrección C.N.` / `Corrección CAD` **desaparecen con la sierra
elegida**. Las capturas de hoy lo desmienten: tampoco están **con el desplegable vacío**. Están
en la primera captura de todas —el panel recién abierto, sin operación— y no están en ninguna
de las otras tres. **El disparador no es la herramienta y no sabemos cuál es.** Lo que sí es
dato duro es el campo del `.pgmx`, que cambia con la herramienta (arriba).

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

## 12. Lo que queda abierto

| | |
|---|---|
| `?%ETK[17]=257` | sale igual que en el perforado. Sigue sin variar |
| **el `0.75` de la cola** | constante: no escala con el largo ni con la posición (§11). Sin procedencia |
| `end_radius = 60` · `material_position` | del `ChannelSpec` congelado, sin campo visible en la UI |
| ~~las cuatro secciones plegadas~~ | ✅ capturadas el 2026-09-03 (§9). `Estrategia` no existe con la sierra |
| ~~la regla del sentido de corte~~ | ✅ **RESUELTA (§11)**: siempre de X mayor a X menor |
| **el `G0 Z80.000`** | hipótesis: radio del disco + plano de seguridad |
| las `Funciones máquina` | nueve interruptores por operación, todos apagados. Familia de fixtures futura |
| el `Corte con cuchilla` | operación vecina en la cinta, sin estudiar |
| **qué muestra los radios `Corrección C.N.`/`CAD`** | están en una captura de cuatro y no es la herramienta lo que los saca |
| **el canal con herramienta de electromandril** | ocho herramientas en el desplegable; sólo derivamos la sierra. Grupo 11 |
