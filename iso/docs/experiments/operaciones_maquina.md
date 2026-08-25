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
| `Xmsg`: `IsInputEnable`, `Stop`, `Variable` | sin barrer; el `S0I0D0` sugiere que van ahí |
| `Park`: `Limit` | vale `Minimum` en los cuatro; sin barrer |
| `Park` en otros campos | `pa21` (HG) y `pa31` (A); faltan los demás para saber la regla |
| `Y` relativa | dos casos, dos campos; un tercero la cerraría |
| por qué la `Y` invierte | derivado el qué, no el porqué |
| `holder_key` contra `name` | **no resoluble en esta máquina** (14) |

## 17. El número del `Xmsg`: es un ACUMULADOR (2026-08-24)

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
N = base + Σ(costo de cada elemento que lo precede)
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

⇒ Los costos **+13** y **+45** se confirman **en los dos campos por separado**, que es lo que
lo levanta de coincidencia a regla.

⇒ Y el **+1 entre campo A y HG** es constante en los cuatro pares: la base cambia, los costos
no.

### 17.3 · Lo que todavía no se puede predecir

**La unidad.** El costo no es proporcional a las líneas del ISO: un `Xmsg` son 2 líneas y
cuesta 13; un `Xn` son 6 líneas y cuesta 45; el fresado son ~40 líneas y cuesta 206. Es un
contador de **algo del programa compilado**, no del texto del ISO.

⇒ Para emitir un ISO byte-idéntico con `Xmsg`, el converter necesitaría **la tabla de costos
de cada elemento** — y hoy tenemos tres entradas de esa tabla.

⇒ 🚧 Sigue bloqueando, pero ya no es un misterio: es una tabla que se llena midiendo. Cada
mecanizado que se estudie en la rama D puede aportar su costo poniéndole un `Xmsg` detrás.

> **Fixture que más rinde ahora**: un programa con **tres o cuatro `Xmsg` seguidos**. Si los
> saltos son 13, 13, 13, el costo del `Xmsg` queda cerrado y el modelo confirmado con más
> puntos. Y uno con **dos `Xn` y un `Xmsg` al final** verificaría que los costos se suman.
