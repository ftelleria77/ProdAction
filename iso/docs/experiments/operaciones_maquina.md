# Operaciones de máquina — rama C

**Documento vivo.** Las **Funciones C.N.** de la UI de Maestro: `Xn` = «Operación nula»,
`Xmsg` = «Impresión mensaje», `Park` = «Aparcamiento». Más **Palpación** y **Corte con
cuchilla**, que no modelamos.

A diferencia de los dibujos (`dibujos.md`), estas **sí llegan al ISO** — y por primera vez en
la reinvestigación tenemos el par completo: `.pgmx` **y** su `.iso`.

---

## 1. El lote

`S:\…\Reinvestigación\Operaciones\` — **28 `.pgmx` manuales de Fermín** (2026-08-20) con sus
27 ISO postprocesados en el CNC. Uno sin `Xn` (`R_PV_manual_op`) como referencia, y 27
variando **una cosa por archivo**:

| grupo | n | qué varía |
|---|---|---|
| X | 2 | `x-2500` · `x-3700` |
| Y | 2 | `y0` · `y-1000` |
| referencia | 2 | `Ab` · `Re` |
| herramienta | 7 | `E001`…`E007` |
| velocidad + herramienta | 15 | `V2`…`V20` cruzadas con las siete |

⚠️ **La pieza de este lote no es la del programa vacío**: su origen da `SHF[X]=-3685.850` y
`SHF[Y]=-400.000`, contra `-400.000` y `-1515.600` del `manual_base`. Es otra área. No cambia
nada de lo derivado abajo, pero los números no son comparables directamente con los de
`anatomia_iso.md`.

## 2. Dónde entra el bloque, y cuánto mide

Entre el `G40` del esqueleto y el `SYN`, exactamente donde `anatomia_iso.md` (B1b) lo había
anticipado y donde el estacionamiento automático mete el suyo (B1d).

> ⚠️ **CORREGIDO el 2026-08-22** con el lote de `Xmsg`/`Park`/`XN_dos`: las dos primeras
> líneas **no son del `Xn`**, son el **preámbulo del bloque de operaciones**, y se emiten
> **una sola vez** aunque haya varias. El cuerpo del `Xn` son **seis** líneas, y el de un
> `Xn` que no es el primero, **cinco** — no repite el `MLV=0`. Ver §9.

**Sin herramienta — ocho líneas** (dos de preámbulo + seis propias)**:**

```
?%ETK[8]=1        <- repite la línea 20 del esqueleto
G40               <- repite la 21
G61
MLV=0
D0
G0 G53 Z201.000
G0 G53 X-3700.000
G64
```

**Con herramienta — quince líneas**, y el orden de `G61` y `MLV=0` **se invierte**:

```
?%ETK[8]=1
G40
MLV=0             <- ahora ANTES del G61
T1                <- número de herramienta
SYN
M06               <- cambio de herramienta
G61
D0
G0 G53 Z201.000
G0 G53 X-3700.000
G64
G61               <- y un segundo bloque de cierre, que sin herramienta no está
D0
G0 G53 Z201.000
G64
```

> `?%ETK[8]` cae en la banda del **cambio de herramienta** (`ETK 6–12`, ver `anatomia_iso.md`
> B1i). Que el bloque del `Xn` abra repitiéndolo encaja con eso.

## 3. El nodo en el `.pgmx`

```xml
<Executable i:type="Xn">
  <Key><ID>1927</ID><ObjectType>ScmGroup.XCam.MachiningDataModel.Xn</ObjectType></Key>
  <Name>Xn</Name>
  <Description/>
  <IsEnabled>true</IsEnabled>
  <Priority>0</Priority>
  <GeometryID>…</GeometryID>
  <WorkpieceID>…</WorkpieceID>
  <Reference>Absolute</Reference>
  <Speed>10</Speed>
  <SpindleEnable>Off</SpindleEnable>
  <Tool>
    <a:ID>1900</a:ID>
    <a:ObjectType>ScmGroup.XCam.ToolDataModel.Tool.CuttingTool</a:ObjectType>
    <a:Name>E001</a:Name>
  </Tool>
  <X>-3700</X>
  <Y i:nil="true"/>
</Executable>
```

Los nombres de los campos son **`Reference`, `Speed`, `SpindleEnable`, `Tool`, `X`, `Y`**.

## 4. Campo por campo

### 4.1 · `X` — va directo, sin transformar

`x-2500` → `X-2500.000`; `x-3700` → `X-3700.000`. **DERIVADO**, 2/2.

### 4.2 · `Reference` — `Absolute` / `Relative`

| `Reference` | `.pgmx` | ISO |
|---|---|---|
| `Absolute` | `X=-3700` | `X-3700.000` |
| `Relative` | `X=-3700` | `X-7385.850` |

Y `−7385.850 = −3700 + (−3685.850)` — **exactamente el `SHF[X]` de la pieza**.

⇒ **`Absolute` = coordenada de máquina, va tal cual. `Relative` = relativa al origen de la
pieza: se le suma el `SHF` del eje.** DERIVADO.

⚠️ Los dos nodos `Xn` son **idénticos salvo `<Reference>`**: la diferencia no está en la `X`.

### 4.3 · `Y` — opcional, y **con el signo invertido**

| `.pgmx` | ISO |
|---|---|
| `<Y i:nil="true"/>` | *(no se emite la Y)* |
| `<Y>0</Y>` | `Y0.000` |
| `<Y>-1000</Y>` | **`Y1000.000`** |

⭐ **«Sin Y» y «Y=0» son casos DISTINTOS**, y el `.pgmx` los distingue explícitamente:
`<Y i:nil="true"/>` contra `<Y>0</Y>`. Es la evidencia directa de la incongruencia que el
`CLAUDE.md` (regla 1) cita como caso testigo — `xn=None` significando «el Xn por defecto» en
vez de «ninguno». Acá el archivo lo dice sin ambigüedad.

> ✅ **RESUELTO el 2026-08-22** con cinco valores en dos campos: **`Y_iso = −Y_pgmx`**,
> sistemático. Ver §9.2. Sigue sin explicar **por qué** el eje Y invierte y el X no; lo que ya
> no hace falta es adivinar la regla.

### 4.4 · `Speed` — decide `G0` contra `G1`, y vale ×1000

| `Speed` | ISO |
|---|---|
| `0` | `G0 G53 X-3700.000` — rápido, sin `F` |
| `2` | `G1 G53 X-3700.000 F2000.000` |
| `3` · `4` · `5` · `6` · `9` · `10` · `20` | `F3000` · `F4000` · `F5000` · `F6000` · `F9000` · `F10000` · `F20000` |

⇒ **`F = Speed × 1000`**, y **`Speed = 0` cambia el código de `G1` a `G0`**. DERIVADO, 8/8.

Coherente con la máquina: el `AP_VELMAX` del eje X es `25000`, y el máximo probado fue 20.

### 4.5 · `Tool` — agrega el cambio de herramienta

`E001`→`T1`, `E002`→`T2`, …, `E007`→`T7`. Y agrega `SYN` + `M06` y el segundo bloque de
cierre (§2).

⚠️ **Ambigüedad que este lote NO puede resolver.** En el catálogo, `E001` tiene
`holder_key=001`, `E002`→`002`… o sea que `holder_key` y el número del `name` **coinciden**
para las siete. Con estos fixtures no se puede separar si el `T` sale del **puesto en el
almacén** (`holder_key`) o del **nombre**. El fixture que lo decide es un `Xn` con una
herramienta numérica —`001` o `082`—, donde los dos caminos darían distinto.

### 4.6 · `SpindleEnable` — sin barrer

Vale `Off` en los 27. La UI ofrece otros valores y no se probó ninguno.

## 5. ⭐ El `Z201.000` sale de la configuración de máquina

Era el hueco declarado en `emisor_iso.cfg`: *«el bloque de ocho líneas del `Xn` no está acá:
su `Z201.000` no tiene origen conocido todavía (rama C)»*. **Ya lo tiene.**

`Cfg/Params.cfg` está organizado en bloques por eje (`AP_NAME = ASSE X` / `ASSE Y` /
`ASSE Z`), y el del eje Z trae:

| clave | valor | mm |
|---|---|---|
| `AP_MINQUOTA` | `-53000` | −53.000 |
| **`AP_MAXQUOTA`** | **`201000`** | **201.000** |
| **`AP_PARKQTA`** | **`201000`** | **201.000** |
| `AP_VELMAX` | `15000` | |

⇒ **`Z201.000` es configuración de máquina, no una constante.** `AP_PARKQTA` («cota de
aparcamiento») es la lectura semánticamente correcta para un `Xn`, que retira el cabezal para
que el operario acceda a la pieza.

⚠️ `AP_PARKQTA` y `AP_MAXQUOTA` **valen lo mismo en esta máquina**, así que la evidencia no
las separa. Cualquiera sirve para el converter; para saber cuál es, haría falta una máquina o
una config donde difieran.

### Y de paso, el número mágico viejo queda explicado

`Params.cfg`, eje X: **`AP_MINQUOTA = -3702000`** = −3702.000 mm, el límite mecánico.

El converter de la época anterior tenía `X_PARK = -3700.0` como constante interna, y el
`CLAUDE.md` lo cita como número mágico que tapaba un agujero. Ahora se ve qué era: **un valor
tipeado a mano dos milímetros adentro del tope del eje**. No sale de la config — **es una
elección del operario**, y por eso no podía derivarse. Los fixtures de este lote usan el mismo
−3700 porque Fermín lo tipeó.

## 6. Lo que este lote NO puede derivar

| | |
|---|---|
| `SpindleEnable` | `Off` en los 27 |
| el `T` | `holder_key` y `name` coinciden en las siete herramientas usadas |
| `AP_PARKQTA` vs `AP_MAXQUOTA` | valen lo mismo |
| el signo de la `Y` | dos fixtures, y el resultado cae fuera del rango del eje |
| `Relative` con `Y` | sólo hay `Relative` sin `Y`; falta ver si la `Y` relativa también suma el `SHF` |
| varios `Xn` en un programa | todos los fixtures tienen **uno solo**. La memoria del proyecto dice que el `Xn` es **posicional** y que puede haber varios (cara A → `Xn` + `Xmsg` girar → cara B → `Xn`); eso sigue sin fixture |
| `Xmsg` y `Park` | sin fixtures todavía |

## 7. Un hallazgo lateral sobre el `GeometryID`

El `Xn` lleva un `<GeometryID>` que aparece en **dos formas** en el lote:

- `<GeometryID i:nil="true"/>` — sólo en `x-3700_Ab_NT`
- `<GeometryID><a:ID>0</a:ID><a:ObjectType i:nil="true"/></GeometryID>` — en los otros 26

**No correlaciona con ningún campo del `Xn`**: `x-2500_Ab_NT` y `x-3700_Ab_NT` difieren sólo
en la `X` y tienen formas distintas. Probablemente sea rastro de **cómo se creó o editó** el
archivo, como pasó con dibujar-contra-editar en la línea (`dibujos.md` §5).

✅ **Y no llega al ISO**: los dos fixtures producen el mismo bloque de ocho líneas salvo la
`X`. Para el converter, da igual cuál se emita.

> 📌 **Para cuando toquemos código**: `_build_xn_step` elige hoy entre dos formas de
> `GeometryID` según **`spec.y is None`**. La evidencia dice que la forma **no depende de la
> `Y`**. Y además la rama «con Y» escribe `ObjectType = System.Object`, una **tercera** forma
> que **Maestro no escribe en ninguno de los 27**. Hay que verificarlo contra los fixtures
> antes de cambiar nada.

## 8. Contra lo que ya modela el sintetizador

`XnSpec` **ya tiene los seis campos** que Maestro escribe:

```
reference · x · y · name · speed · spindle_enable · tool_id · tool_object_type · tool_name
```

⇒ El modelo está completo; lo que falta verificar es la **emisión**. Con este lote se puede
hacer, porque por primera vez hay `.pgmx` y `.iso` del mismo caso. Pendiente para la pasada
de código:

1. **`GeometryID`** — la rama de `_build_xn_step` está condicionada a `spec.y is None`, y la
   evidencia dice que la forma **no depende de la `Y`** (§7). La rama «con Y» escribe una
   tercera forma que Maestro no usa.
2. **`speed`** — verificar que emitimos `G1` + `F = speed × 1000`, y `G0` cuando es 0.
3. **`reference`** — verificar que `Relative` suma el `SHF` del eje.
4. **`y`** — verificar el `<Y i:nil="true"/>` cuando no hay `Y`, y **el signo invertido**,
   que primero hay que entender.
5. El bloque del `Xn` **no está en `emisor_iso.cfg`**, que lo declara ausente justamente
   porque el `Z201.000` no tenía origen. Ahora lo tiene (§5): sale de `Params.cfg`, así que
   entra como los demás valores de máquina, no como literal.

---

# Segunda tanda (2026-08-22): `Xmsg`, `Park`, y el `Xn` en dos campos

**64 `.pgmx` y 60 `.iso`.** Fermín rehízo el lote en **campo HG** además del original en
**campo A**, y agregó los bloques 1 y 2 que estaban pedidos. Tener **el mismo programa en dos
áreas** resultó ser mucho más que una duplicación: separó cosas que con un campo solo se
confundían.

| | campo A | campo HG |
|---|---|---|
| `SHF[X]` | −3685.850 | −400.000 |
| `SHF[Y]` | −400.000 | −1515.600 |

## 9. Estructura real del bloque de operaciones

`XN_dos` (dos `Xn` en un programa) lo deja a la vista — **trece líneas**:

```
?%ETK[8]=1      <- PREÁMBULO del bloque, una sola vez
G40             <-      ídem
G61 · MLV=0 · D0 · G0 G53 Z201.000 · G0 G53 X-3700.000 · G64    <- Xn 1: SEIS líneas
G61 ·          D0 · G0 G53 Z201.000 · G0 G53 X-2500.000 · G64    <- Xn 2: CINCO
```

Tres reglas:

1. **`?%ETK[8]=1` + `G40` son del bloque, no del `Xn`**, y se emiten una vez aunque haya
   varias operaciones.
2. **El segundo `Xn` no repite el `MLV=0`.**
3. **El orden de la lista se respeta** — confirmado también por `OPS_tres`
   (`Xn` → `Xmsg` → `Park`), que emite los tres cuerpos en ese orden.

Y con eso queda respondida la pregunta de la memoria del proyecto: **sí se pueden poner varios
`Xn` en un programa**, y cada uno emite su cuerpo.

### 9.2 · `Y` — el signo se invierte, y ahora está derivado

| `.pgmx` | ISO |
|---|---|
| `+50` | **−50.000** |
| `+500` | **−500.000** |
| `0` | `0.000` |
| `−100` | **+100.000** |
| `−1000` | **+1000.000** |

⇒ **`Y_iso = −Y_pgmx`**, 5/5, idéntico en los dos campos. **DERIVADO.**

Queda abierto **por qué**: la `X` conserva el signo y la `Y` no. Es coherente con que el eje Y
de la pieza y el de la máquina apunten al revés, pero eso hoy es lectura, no evidencia.

> 🚨 **2026-09-11 — y tiene consecuencia física, medida en la máquina.** Fermín ejecutó un
> programa con `Y = −1000`: el ISO emite `Y1000.000` y **el CNC se planta sin terminar la
> ejecución**. El eje Y va de **−1870 a +131 mm** (`Params.cfg`), así que `+1000` está **fuera
> de recorrido** — mientras el `−1000` que se tipeó **sí** está dentro del rango físico.
>
> ✅ **Y confirmado ejecutando en los dos sentidos**: con `Y = +1000` el ISO emite `Y-1000.000`,
> la máquina **ejecuta** y queda en **(−3700, −1000)**. ⇒ **la inversión es la convención
> correcta** —el usuario pide `+1000` y la máquina va a `−1000`, una cota alcanzable— y el
> **rango útil en la UI** queda derivado: **`−131` a `+1870`**, el espejo del físico.
>
> ⚖️ ⇒ **El error de Maestro no es invertir: es NO VALIDAR.** Acepta un valor que su propia
> configuración declara inalcanzable, no avisa al tipearlo, y postprocesa igual.
>
> ⇒ Es el **sexto caso de fail-loud** del converter, y el primero **confirmado ejecutando**. Se
> cubre con lo que ya hay: `AP_MINQUOTA ≤ cota ≤ AP_MAXQUOTA` antes de emitir un `G53`.
> Detalle en `fresado.md` §37.
>
> 📌 Y el pendiente de §6 —*«varios `Xn` en un programa … sigue sin fixture»*— queda **cubierto**
> por los dos archivos del Grupo 19 del fresado.

### 9.3 · `Relative` — el segundo campo lo separó

Con un solo campo las dos fórmulas posibles daban lo mismo. Con dos, no:

| campo | `Reference` | `.pgmx` | ISO |
|---|---|---|---|
| A | `Relative`, sin `Y` | X=−3700 | `X-7385.850` |
| A | `Relative`, `Y=-1000` | | `X-7385.850 Y-600.000` |
| HG | `Relative`, `Y=-1000` | | `X-4100.000 Y515.600` |

- **X**: `X + SHF[X]` → A: −3700 + (−3685.850) = −7385.850 ✓ · HG: −3700 + (−400) = −4100 ✓
- **Y**: `Y − SHF[Y]` → A: −1000 − (−400) = −600 ✓ · HG: −1000 − (−1515.600) = +515.600 ✓

⇒ **`X_iso = X + SHF[X]` · `Y_iso = Y − SHF[Y]`.** La `X` suma y la `Y` resta — coherente con
la inversión de 9.2.

⚠️ Dos casos para la `Y` relativa, pero con `SHF[Y]` muy distintos (−400 y −1515.600), así que
la fórmula está bastante restringida. Un tercer campo la cerraría.

## 10. `Xmsg` — dos líneas, y **el texto NO viaja**

```
$0?212S0I0D0?
G4 F0
```

⭐ **Dos textos distintos dan la misma línea.** `PRUEBA` y `Girá la pieza` emiten los dos
`$0?212S0I0D0?` en campo A. **El texto del mensaje no está en el ISO.**

El nodo del `.pgmx` sí lo tiene, junto a otros tres campos:

```xml
<IsInputEnable>false</IsInputEnable>
<Stop>Nothing</Stop>
<Text>PRUEBA</Text>
<Variable/>
```

El `S0I0D0` de la línea parece mapear a esos campos (`Stop`, `IsInputEnable`, …), todos en 0
acá — **sin barrer**.

### El número, y por qué importa

| programa | campo A | campo HG |
|---|---|---|
| sólo `Xmsg` | `212` | `213` |
| `OPS_tres` | `257` | `258` |

**No es un contador de sesión** (los postprocesos fueron en orden y el número no crece
monótono), **no depende del texto** (dos textos, mismo número) y **cambia con el campo** (+1 de
A a HG) y con la cantidad de operaciones.

🚧 **Esto bloquea el byte-idéntico para cualquier programa con `Xmsg`.** Sin saber de dónde
sale ese número, el converter no puede emitir la línea. Es el hueco más serio de la rama C.

## 11. `Park` — es lo mismo que el estacionamiento automático, y **depende del campo**

| campo | bloque emitido |
|---|---|
| **HG** | `G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000` · `_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )` |
| **A** | `_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ax[0].pa[22]/1000 )` · `G0G53 X%ax0.pa31/1000 Y%ax1.pa22/1000` · `_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )` |

Dos diferencias, y ninguna es cosmética:

1. **El parámetro de eje cambia**: `%ax0.pa21` en HG, **`%ax0.pa31`** en A.
2. **Campo A agrega un `_paras` por delante.**

⭐ **Y el bloque de HG es exactamente el `$EMI_PARK_FINAL` de `emisor_iso.cfg`** — el que se
derivó de los fixtures `eafe_*` del estacionamiento **automático** de la ventana Opciones
(B1d). ⇒ **El «Aparcamiento» de la UI y el «estacionamiento automático al terminar» emiten lo
mismo**: uno puesto a mano en la lista, el otro agregado por la aplicación.

⇒ Y corrige el alcance de `emisor_iso.cfg`: ese bloque **no es fijo**, depende del campo.

### `Stop` no llega

`R_PV_*_PARK_pes` cambia `<Stop>Nothing</Stop>` por `<Stop>NoUnlock</Stop>` y **el ISO sale
idéntico**, en los dos campos. Otra vez «el modo se pierde».

## 12. `Electromandril` (`SpindleEnable`) tampoco llega

`..._E001_SpEncendido` contra `..._E001`: **ISO idénticos** salvo el nombre del archivo, en los
dos campos. El campo existe en el `.pgmx` y **no tiene efecto en el ISO**.

## 13. La UI del `Xn`, por fin capturada

De la captura de error del `T082` (ver 14), el panel derecho de Maestro:

| campo de la UI | tag del `.pgmx` |
|---|---|
| **`X final`** | `X` |
| **`Y final`** | `Y` — vacío cuando es `nil` |
| **`Referencia`** (`Absoluto`) | `Reference` (`Absolute`) |
| **`Velocidad`** | `Speed` |
| **`Electromandril`** (`Apagado`) | `SpindleEnable` (`Off`) |
| **`Información herramientas`** | `Tool` |

Y la cinta confirma el grupo **Funciones C.N.** de la pestaña **Máquinas**: `ISO`,
`Operación nula`, `Impresión mensaje`, `Aparcamiento`, `Palpación`.

## 14. Un fixture que NO postprocesó, y lo que enseña

`R_PV_manual_op_XN_x-3700_Ab_T082` — el `Xn` con la herramienta **`082`** (Sierra Vertical X)
pedido para separar `holder_key` de `name`. **Winxiso lo rechaza:**

```
[23,5] - Bag.Oheads: Herramienta E82 no configurada
```

Tres cosas se siguen:

1. **El emisor llama `E<n>` a la herramienta**, con `n` = el número sin ceros a la izquierda.
   `082` → `E82`; y `E001` → `E1` → `T1`, que es lo que veníamos viendo.
2. ⭐ **El catálogo de Maestro (`def.tlgx`) y la tabla de herramientas de la MÁQUINA son dos
   cosas distintas.** La `082` existe en el catálogo y **no está configurada en la máquina**.
   El converter tiene que contar con que una herramienta válida en el `.pgmx` puede no serlo
   para el postproceso.
3. ⛔ **La ambigüedad `holder_key` contra `name` NO se puede resolver con esta máquina**: las
   únicas herramientas que las separarían son justamente las que no están configuradas.

> 📌 **CORREGIDO el 2026-09-03 (lectura de Fermín, confirmada).** El punto 2 decía que la
> `082` **«no está configurada en la máquina»**, y eso es falso: está en `spindles.cfg` como
> registro **82** (con `shPlcOut = 37`, offsets propios y `Face1`), y el taller corta canales
> con ella desde 2023 — **3157 ISO** en `P:\USBMIX`. Lo que no existe es la `082` **en la
> tabla `Oheads`**, que es el cabezal al que apunta el `Xn`.
>
> ⇒ **El rechazo es del CONTEXTO, no de la herramienta.** El titular del punto 2 se sostiene
> —el catálogo de Maestro y las tablas de la máquina son cosas distintas—, pero la
> consecuencia para el converter se afina: una herramienta puede estar configurada **para un
> cabezal y no para otro**, así que lo que hay que chequear no es «¿existe la herramienta?»
> sino «¿existe en el cabezal que esta operación usa?».
>
> ⚠️ Y el punto 3 se queda **sin su premisa**: la `082` sí está configurada. Que la ambigüedad
> `holder_key`/`name` siga sin resolverse hay que re-derivarlo, no darlo por dicho. Detalle en
> `experiments/canal.md`.

## 15. Estado de los fixtures de esta tanda

| | |
|---|---|
| pares `.pgmx` + `.iso` completos | **60** |
| `R_PV_HG_manual_op_XN_x-3700_Ab_E006` | ⚠️ **falta el `.iso`** — el nodo está bien, parece un salteo |
| `R_PV_HG_manual_op_XN_x-3700_Re_NT` | ⚠️ **falta el `.iso`** — y es el que cerraría `Relative` sin `Y` en el segundo campo |
| `R_PV_manual_op_Xmsg_NP` | `Xmsg` con `<Text i:nil="true"/>` (mensaje vacío). Sin `.iso` |
| `R_PV_manual_op_XN_x-3700_Ab_T082` | ❌ **no postprocesa** — ver 14. Queda como evidencia del error, no como fixture |

## 16. Lo que sigue abierto en la rama C

| | |
|---|---|
| 🚧 **el número del `Xmsg`** | bloquea el byte-idéntico de todo programa con mensaje |
| `Xmsg`: `IsInputEnable`, `Stop`, `Variable` | ✅ **`Stop` BARRIDO el 2026-09-07** (ver abajo): la hipótesis del `S0I0D0` era correcta. `IsInputEnable` y `Variable` siguen sin barrer |
| `Park`: `Limit` | vale `Minimum` en los cuatro; sin barrer |
| `Park` en otros campos | `pa21` (HG) y `pa31` (A); faltan los demás para saber la regla |
| `Y` relativa | dos casos, dos campos; un tercero la cerraría |
| por qué la `Y` invierte | derivado el qué, no el porqué |
| `holder_key` contra `name` | **no resoluble en esta máquina** (14) |

## 17. El número del `Xmsg`: es un CONTEO (2026-08-24)

Era el hueco que bloqueaba el byte-idéntico de todo programa con mensaje. Cuatro fixtures
nuevos —dos mensajes en un programa, el mismo programa repostprocesado, y un `Xmsg` detrás de
un fresado— lo acotan casi del todo.

### 17.1 · Lo que queda descartado

| hipótesis | evidencia que la mata |
|---|---|
| depende del **texto** | `PRUEBA` y `Girá la pieza` dan los dos `212` |
| es un **contador de sesión** | repostprocesar `xmsg_prueba` sin tocar nada **vuelve a dar 212**: es determinista |
| es un **offset de bytes** del ISO | `N=212` aparece con 458 bytes por delante en un archivo y con 455 en otro |
| es el **número de línea** del ISO | línea 24 → 212 en dos programas, pero la relación no es lineal entre casos |

### 17.2 · El modelo que sí encaja

```
N = conteo inicial + Σ(en cuánto lo incrementa cada elemento que lo precede)
```

| | campo A | campo HG |
|---|---|---|
| **base** (esqueleto, primer `Xmsg` del programa) | **212** | **213** |
| coste de un `Xmsg` que lo precede | **+13** | **+13** |
| coste de un `Xn` que lo precede | **+45** | **+45** |
| coste del fresado de `linea_01_fresada` | **+206** | **+206** |

Las cuatro medidas, en los dos campos:

| fixture | campo A | campo HG |
|---|---|---|
| `xmsg_prueba` / `xmsg_acentos` | 212 | 213 |
| `xmsg_dos` (los dos mensajes) | 212 · **225** | 213 · **226** |
| `ops_tres` (`Xn` → `Xmsg` → `Park`) | **257** = 212 + 45 | **258** = 213 + 45 |
| `linea_01_fresada_XMSG` | **418** = 212 + 206 | **419** = 213 + 206 |

⇒ Los incrementos **+13** y **+45** se confirman **en los dos campos por separado**, que es lo que
lo levanta de coincidencia a regla.

⇒ Y el **+1 entre campo A y HG** es constante en los cuatro pares: el conteo inicial cambia, los incrementos
no.

### 17.3 · Lo que todavía no se puede predecir

**Qué se cuenta.** El incremento no es proporcional a las líneas del ISO: un `Xmsg` son 2 líneas y
cuesta 13; un `Xn` son 6 líneas y cuesta 45; el fresado son ~40 líneas y cuesta 206. Es un
contador de **algo del programa compilado**, no del texto del ISO.

⇒ Para emitir un ISO byte-idéntico con `Xmsg`, el converter necesitaría **la tabla de incrementos
de cada elemento** — y hoy tenemos tres entradas de esa tabla.

⇒ 🚧 Sigue bloqueando, pero ya no es un misterio: es una tabla que se llena midiendo. Cada
mecanizado que se estudie en la rama D puede aportar su incremento poniéndole un `Xmsg` detrás.

> **Fixture que más rinde ahora**: un programa con **tres o cuatro `Xmsg` seguidos**. Si los
> saltos son 13, 13, 13, el incremento del `Xmsg` queda cerrado y el modelo confirmado con más
> puntos. Y uno con **dos `Xn` y un `Xmsg` al final** verificaría que los incrementos se suman.

### 17.4 · Qué se cuenta: NO es nada visible en el ISO

Nomenclatura fijada con Fermín (2026-08-25): **conteo**, y **en cuánto lo incrementa cada
elemento**. Se descartó «costo», que sugería gasto y no es eso.

La pregunta que queda es **conteo de qué**. Se probaron cinco medidas del propio ISO, todas
tomadas hasta la línea del mensaje:

| N | líneas | bytes | caracteres sin espacios | tokens | números |
|---|---|---|---|---|---|
| 212 | 23 | 458 | 374 | 42 | 50 |
| 225 | 25 | 478 | 388 | 45 | 57 |
| 257 | 29 | 518 | 412 | 60 | 60 |
| 418 | 66 | 1069 | 840 | 101 | 118 |

**Ninguna da una relación lineal con N.** La más prometedora era *tokens* —dos programas con
`N=212` tienen los dos 42 tokens— pero la pendiente no se sostiene: +3 tokens dan +13, +7 dan
+32 y +49 dan +161.

⇒ **El conteo no cuenta nada del ISO.** Cuenta algo del programa compilado que el ISO no
muestra. Y como el estudio del XXL/PGM está cerrado por decisión del 2026-08-14, no se va a
buscar por ahí.

### 17.5 · Por qué eso NO bloquea al converter

Que no sepamos la unidad **no impide calcular N**, siempre que los incrementos sean estables
por elemento. El converter puede llevar el conteo sumando incrementos de una tabla empírica,
sin saber qué representa el número — igual que emite `Z201.000` sin saber qué es una «cota de
aparcamiento».

⚠️ **Lo que sí hay que verificar es que el incremento sea estable.** El del fresado (+206) es
de **ese** fresado: uno más largo casi seguro incrementa más. O sea que el incremento
probablemente **dependa del contenido** del elemento, no sólo de su tipo.

> **El fixture que lo decide**: `xmsg_dos` pero con el **primer mensaje mucho más largo**. Si
> el segundo sigue dando **+13**, el incremento del `Xmsg` es fijo y no depende del texto —
> que es lo que se espera, porque el texto no viaja al ISO. Si cambia, el conteo depende del
> contenido y la tabla se vuelve mucho más cara de llenar.

### 17.6 · El incremento del `Xmsg` DEPENDE DEL CONTENIDO (2026-08-25)

Era la pregunta que 17.5 dejaba planteada, y la respuesta es la que complica:
`R_PV_manual_op_XMSG_dos_largo` es `xmsg_dos` con el **primer** mensaje más largo.

| fixture | 1er mensaje | largo | 2º mensaje | incremento |
|---|---|---|---|---|
| `XMSG_dos` | `PRUEBA` → **212** | 6 | **225** | **+13** |
| `XMSG_dos_largo` | `Mensaje largo al operador` → **212** | **25** | **244** | **+32** |

El texto crece **+19** caracteres y el conteo se corre **+19** exactos.

⇒ **`incremento(Xmsg) = largo del texto + 7`** — pendiente 1, fijada por el delta; ordenada 7,
confirmada por los dos puntos.

⇒ Y una consecuencia bonita: **el largo del propio mensaje NO mueve su propio `N`** (los dos
primeros mensajes dan 212 pese a medir 6 y 25). El conteo es la posición **al empezar** a
emitir el elemento.

⇒ Y otra que cierra un círculo: **el texto ocupa lugar en el conteo aunque no aparezca en el
ISO**. Confirma que el conteo cuenta algo del **programa compilado**, donde el texto sí está —
coherente con 17.4, y con que el mensaje viaje como número.

### ⚠️ Lo que esto le hace a la tabla

La tabla de incrementos **no es «un número por tipo de operación»**: es **una fórmula por
tipo**, y hay que derivar cada una. Para el `Xmsg` ya está; para todo lo demás, no.

| elemento | incremento |
|---|---|
| `Xmsg` | **`largo(texto) + 7`** — derivado, 2 puntos con pendiente fijada |
| `Xn` | `45` observado **una sola vez** (`ops_tres`, con `x-3700`, sin herramienta ni `Y`). ⚠️ Ahora hay que sospechar que **también depende del contenido**: los dígitos de la `X`, la `Y`, la herramienta, la velocidad |
| fresado de `linea_01_fresada` | `206`, y casi seguro depende del largo de la traza |

> **Lo que hay que medir para el `Xn`**: el mismo programa con `x-2500` en vez de `x-3700`
> (mismo largo de texto, otro número), con `Y`, y con herramienta — cada uno con un `Xmsg`
> detrás. Si el 45 se mueve, el `Xn` también tiene fórmula.

### ⚠️ Y una que puede morder: ¿caracteres o bytes?

Los tres textos medidos son **ASCII puro** (`PRUEBA`, `Otro texto`,
`Mensaje largo al operador`), así que **no se puede distinguir si el conteo cuenta caracteres
o bytes**. Con un acento las dos lecturas se separan: `Girá la pieza` son 13 caracteres pero
14 bytes en UTF-8 y 13 en cp1252.

⇒ Fixture barato que lo cierra: `xmsg_dos` con el primer mensaje **con acentos**. Hoy tenemos
`XMSG_acentos`, pero ahí el mensaje acentuado es el **único**, así que no mueve nada medible.

## 18. El `Stop` del `Xmsg` sí llega, y el conteo cuenta CARACTERES (2026-09-07)

Tres fixtures que Fermín agregó al Grupo 14 del canal por su cuenta —*«no recuerdo si habíamos
hecho este estudio completo»*—. No lo habíamos hecho: el §17 listaba `Stop` como **sin barrer**.

### ⭐ Los tres modos de paro, de punta a punta

| opción de la UI | `.pgmx` | ISO |
|---|---|---|
| **`Ningún Paro`** | `<Stop>Nothing</Stop>` | `$0?443`**`S0`**`I0D0?` |
| **`Paro con Espera de Start`** | `<Stop>NoUnlock</Stop>` | `$0?443`**`S1`**`I0D0?` + **`M0`** |
| **`Paro con Desbloqueo y Espera de Start`** | `<Stop>Unlock</Stop>` | `$0?443`**`S2`**`I0D0?` + **`M0`** |

⇒ **La hipótesis del §17 era correcta**: el `S` de la instrucción es el campo `Stop`. Y encaja
con la plantilla leída del emisor —`$0?%ld S%d I%d D%.*f?` en `isotrd.dll` (`emisor_iso.md`)—:
el `%ld` es el conteo y el primer `%d` es el paro.

⇒ Los dos modos con paro agregan además un **`M0`** (paro programado) después del `G4 F0`.

⚠️ **Y contrasta con el `Park`**, cuyo campo `Stop` **no** llega al ISO (§14 bis). Mismo nombre
de campo, dos operaciones, dos comportamientos. El converter no puede tratarlos igual.

### ⭐⭐ El conteo cuenta el texto EMITIDO, no el valor tipeado

El fixture pedía el canal arrancando en **X = 92,5** en vez de 50, para ver si el incremento
—121 por canal— dependía del contenido, como pasaba en el perforado.

**No se movió**: los dos dan `xISO382` y `$0?443`.

Y ahí está la explicación de la anomalía que el perforado había dejado escrita como *«al revés
de lo esperado, medido y sin explicación»*: allá `92.5` **bajaba** el conteo en 1 contra `100`,
lo que parecía absurdo porque «92.5» tiene un carácter más que «100».

**Pero el conteo no mira lo que uno tipea: mira lo que el ISO escribe.** Y el ISO escribe las
coordenadas con tres decimales siempre:

| | tipeado | emitido | caracteres |
|---|---|---|---|
| perforado | `100` | `X100.000` | **8** |
| perforado | `92.5` | `X92.500` | **7** ⇒ uno menos, conteo −1 ✅ |
| canal | `50` | `X50.000` | **7** |
| canal | `92.5` | `X92.500` | **7** ⇒ igual, conteo sin cambio ✅ |

⇒ **Las dos medidas encajan con la misma regla**, y la del perforado deja de ser una anomalía.

⇒ Para el byte-idéntico esto cambia la naturaleza del problema: **no falta «la fórmula de cada
mecanizado», falta contar el texto que el propio converter va a emitir.** Es un conteo sobre la
salida, no una tabla de constantes por tipo de operación.

📌 **Sigue faltando la base del conteo** —de dónde arranca— y qué son la `I` y la `D`.

## 19. El `Xmsg` en el ISO, analizado a fondo (2026-09-11)

**Decisión de alcance de Fermín**: *el converter **no puede rechazar** los programas con
mensaje.* El `Xmsg` es la **parada con espera de start** que le da al operario la oportunidad
de **girar la pieza** — o sea, es la pieza central de la técnica de mecanizado en las dos
caras, que es justamente el caso que §25.1 dejó como fail-loud (la cara inferior se descarta en
silencio).

⇒ Hay que resolverlo. Esta sección es el análisis minucioso, sobre **28 mensajes en 25
archivos** de todo el corpus (ramas C, D1, D2 y D3).

### 19.1 Qué agrega exactamente un `Xmsg` al ISO

Entre **dos y cuatro líneas**, según el contexto:

| línea | cuándo aparece |
|---|---|
| `M5 ;(xISO<n>-> Spegne mandrino)` | **sólo si el husillo está girando**. Al inicio del programa no aparece |
| `$0?<N>S<stop>I0D0?` | **siempre** — la instrucción del mensaje |
| `G4 F0` | **siempre** |
| `M0` | **sólo con `Paro con espera de start` o `con desbloqueo`** (`S1`/`S2`) |
| `S<velocidad>M3` | **sólo si hay que rearrancar** el husillo: el `Xmsg` **intercalado** entre dos mecanizados lo agrega |

Verificado con los tres modos de paro (canal, Grupo 14) y con las tres posiciones (fresado,
Grupo 11).

⚠️ **Y lo que NO agrega: el texto del mensaje.** No aparece en ninguna parte del ISO.

### 19.2 ⭐⭐⭐ Entonces el `N` no es un «contador»: es un PUNTERO al texto

Si el texto que el operario lee no viaja en el ISO, la máquina lo tiene que sacar de otro lado
— y lo único que el ISO lleva es el número. ⇒ **`N` es un desplazamiento dentro del programa
compilado**, donde el texto sí vive.

Esa lectura explica de una sola vez todo lo que se había medido por separado:

| observación | queda explicada |
|---|---|
| crece con **todo lo emitido antes** (§27.2: intercalado = simple) | es una **posición**, no una cuenta |
| el **texto ocupa lugar** aunque no salga en el ISO (§17.6) | en el compilado el texto **sí está** |
| `incremento(Xmsg) = largo(texto) + 7` | el texto **más 7 bytes de cabecera** |
| es **determinista** (repostprocesar da lo mismo) | es una posición, no un contador de sesión |
| **no se corresponde con nada del ISO** (§17.4) | el ISO es **otro formato** |
| el **campo `S`** viaja al lado (§18) | son los campos de una misma instrucción, `$0?%ld S%d I%d D%.*f?` |

### 19.3 ⛔ Y contesta la pregunta: contar líneas NO sirve

| elemento | líneas que agrega al ISO | cuánto incrementa `N` |
|---|---|---|
| `Xmsg` | 2 | **13** |
| `Xn` | 6 | **45** |
| perforado de un agujero | 41 | **137** |
| fresado de una línea | 51 | **210** |
| **fresado de un círculo** | **52** | **321** |

⇒ El par que lo cierra: **el círculo agrega UNA línea más que la línea recta y el conteo sube
111.** No hay proporción posible.

Y tampoco son los caracteres del ISO. Midiendo el bloque que cada mecanizado agrega:

| caso | incremento | líneas | caracteres del bloque |
|---|---|---|---|
| perforado | 137 | 41 | 485 |
| fresado línea | 210 | 51 | 556 |
| fresado círculo | **321** | 52 | **624** |
| fresado dos líneas | 351 | 71 | 824 |

Entre el perforado y el fresado de línea la diferencia de caracteres (+71) casi coincide con la
del conteo (+73) — pero **el círculo la rompe**: +68 caracteres contra **+111** de conteo. Un
arco escribe menos en el ISO de lo que ocupa en el compilado.

⇒ ✅ **Confirma §17.4 con dos medidas más**: el conteo no cuenta nada del ISO.

### 19.4 Las tres salidas, por costo

> # ✅✅✅ RESUELTO EN LA MÁQUINA (2026-09-11): el `N` NO hace falta para ejecutar
>
> **Fermín ejecutó los dos pares con el conteo falseado y corrieron bien.**
>
> | programa | `N` real | `N` falso | resultado |
> |---|---|---|---|
> | `xmsg_solo_pes` — sólo el mensaje | `212` | `999` | ✅ **para y espera start** |
> | `xn_xmsg_xn_pes` — `Xn` · `Xmsg` · `Xn` | `257` | `999` | ✅ **para, y al dar start EJECUTA el segundo `Xn`** |
>
> El segundo es el que decide: tiene un movimiento **después** del mensaje, así que prueba que
> **el programa sigue corriendo** con un conteo equivocado. No es sólo que pare.
>
> ⇒ ⭐⭐⭐ **El conteo deja de bloquear el byte-idéntico.** Pasa a ser una **divergencia
> deliberada declarada**, igual que `%DONTCARESPEEDV=1` (`CLAUDE.md` §4: *el byte-idéntico es el
> método, no el fin, y manda la máquina*).
>
> ⇒ ⭐⭐ **Y con eso el converter puede emitir programas con `Xmsg`** — o sea, **la técnica de
> mecanizado en las dos caras queda habilitada**, que era el motivo por el que no se podía
> rechazar (§19).
>
> ### Lo que queda por decidir (⚖️ de Fermín): qué `N` emite el converter
>
> | opción | |
> |---|---|
> | **el que salga de la tabla** (base + incrementos conocidos) | byte-idéntico donde se pueda; impredecible dónde sí y dónde no |
> | **un valor fijo y determinista** | simple y auditable; nunca byte-idéntico en el campo `N` |
>
> En los dos casos **el comparador tiene que descontar el campo `N`**, como hace con las
> omisiones deliberadas — pero descontando **un campo dentro de una línea**, que es nuevo:
> `DELIBERATE_OMISSIONS` hoy trabaja con líneas enteras.
>
> 📌 **Y un apunte para la regla 4**: ya son **tres** los casos donde el byte-idéntico no es el
> objetivo — `%DONTCARESPEEDV=1`, el ruido de milésimas de Maestro, y ahora el conteo del
> `Xmsg`. La nota de `iso_first_machine_run` decía que *si aparecen más, conviene que Fermín
> decida si la regla se reescribe*. **Aparecieron.**

**A. ⭐ La más barata, y la que puede desbloquear todo: ¿el `N` hace falta para EJECUTAR?**

La parada que le importa al operario la producen **`M0` + `G4 F0`**, que **no dependen del
`N`**. Si el número está mal, lo peor que puede pasar es que el mensaje salga vacío o
equivocado — **pero la pieza para igual**.

⇒ Y es **seguro de probar**: un programa con **un solo `Xmsg`** con paro, sin ningún
mecanizado, no mueve nada. Se ejecuta dos veces: con el `N` que emite Maestro y con uno
**cambiado a mano**.

| si | entonces |
|---|---|
| las dos paran y esperan start | el `N` **no bloquea**: se declara divergencia deliberada, como `%DONTCARESPEEDV` (`CLAUDE.md` §4), y el converter emite el que pueda |
| la segunda falla o no muestra el mensaje | el `N` es esencial y hay que ir a B o C |

**B. Un `.pgm` de dos minutos.** La cadena es `.pgmx → XXL → PGM → ISO`, y el contador lo
escribe el generador de Xilog. Si `N` es un desplazamiento del compilado, el **PGM** es el
formato donde el texto vive y las coordenadas ya están formateadas.

⚖️ **Roza la decisión del 2026-08-14** de cerrar el XXL/PGM como línea de trabajo — y conviene
decir por qué **no la contradice**: aquella decisión fue *no razonar la traza a través de un
intermedio que no emitimos*, porque eso evita el fixture. Acá no se trata de derivar la traza,
sino de **leer un contador que el ISO no muestra**. Es una excepción acotada, con un propósito
único y verificable.

**C. La tabla empírica por elemento.** Es lo que §17.5 proponía, y **hoy se sabe que es cara**:
no es «un número por tipo» sino una **fórmula por tipo**, y el círculo muestra que hasta la
familia de curva cambia el resultado. Habría que derivar una fórmula por cada geometría y por
cada mecanizado. Es el camino de último recurso.

⇒ **Recomendación: A primero.** Cuesta un programa inocuo y dos ejecuciones, y si sale bien
cierra el tema sin tocar la decisión del XXL/PGM ni llenar ninguna tabla.
