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
| ✅ derivado | nada todavía: **el lote no existe** |
| 🔮 predicho desde la configuración | huso, máscara, `SHF`, `SVL`, `SVR`, `S`, cara única |
| ⏸ esperando a Fermín | el lote D2, y las cuatro secciones plegadas de la ventana |
| ✅ descartado | el rechazo de la `082` del lote C: era del contexto `Xn` (§7) |

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

**Plegadas, sin capturar**: `Estrategia` · `Acercamiento/Alejamiento` · `Datos avanzados` ·
`Datos máquina`. Es el mismo agujero que tuvo el perforado con el plano de seguridad: los
defaults que no se ven llegan igual al ISO. **Faltan esas cuatro capturas.**

⚠️ **`Anchura` en gris no está explicado.** Dos lecturas, y cambian el modelo: puede estar
deshabilitada **porque sale de la herramienta** (`BladeThickness = 3.8` del catálogo) o
**porque todavía no hay herramienta elegida** en el desplegable, que en la captura está vacío.
Lo decide un fixture con herramienta puesta.

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
| **`Anchura`** (en gris) | `tool_width = 3.8` **como parámetro de entrada** | ⚠️ si la UI no lo deja poner, no es un parámetro nuestro: es un dato de la herramienta |
| **`Inclinación °`** = `90` | `slot_angle = 1.5707963267948966` | ⚠️ el nombre no dice inclinación, y va en radianes contra grados |
| **`Corrección herramienta`**: **cuatro** botones | `side_of_feature`: **tres** valores (`Center`/`Right`/`Left`) | ⚠️ falta uno |
| `Corrección C.N.` / `Corrección CAD` | — | ⚠️ es el interruptor de la regla 5 del `CLAUDE.md`: con CAD la traza guardada **ya trae el offset** |
| `Rebaba` | ¿`side_offset`? | ⚠️ sin verificar |
| — | `end_radius = 60` · `material_position = "Left"` | ⚠️ no están en la parte visible de la ventana |

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

> 📌 La `082` tiene el **mismo offset X que la broca `006`** (96.00), que sí entra en campo `A`.
> Las que se topaban con el `AP_MINQUOTA` eran la `007` (128) y la `061` (118) ⇒ **el canal en
> campo A no debería toparse**. Predicción, no certeza.

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

## 8. Lo que queda abierto

| | |
|---|---|
| `?%ETK[17]=257` | sale igual que en el perforado. Sigue sin variar |
| la cola de 4 movimientos | aparece en unos ISO de producción y en otros no. Sin explicación |
| `end_radius = 60` · `material_position` | del `ChannelSpec` congelado, sin campo visible en la UI |
| las cuatro secciones plegadas | `Estrategia`, `Acercamiento/Alejamiento`, `Datos avanzados`, `Datos máquina` |
| el `Corte con cuchilla` | operación vecina en la cinta, sin estudiar |
