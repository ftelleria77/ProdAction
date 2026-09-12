# Galceado (Escuadrado) — rama D

**Documento vivo.** La operación que **escuadra la pieza**: la lleva a sus medidas finales y
sus esquinas a 90°. En el taller se la llama **`Escuadrado`**; el botón de Maestro dice
`Galceado` y el archivo dice `Perfilado` (§2). Cuarto mecanizado de la rama D,
y el primero que arranca con **medio lote resuelto antes del segundo archivo**.

> ⭐⭐⭐ **2026-09-12 — la predicción del Grupo 1 se cumplió BYTE A BYTE.** El mismo contorno
> hecho con `Fresado` y con `Galceado` produce **el mismo ISO**, idéntico salvo la línea del
> nombre. ⇒ **el Galceado no es una familia de emisión nueva**, y todo lo derivado en el fresado
> se hereda entero.

## 1. ⭐⭐⭐ El par de control: `Fresado` contra `Galceado`, byte-idénticos

Fermín hizo el mismo contorno de la pieza `(0,0)-(400,400)` con las **dos operaciones**, misma
herramienta (`E004`), misma profundidad (10):

```
r_pv_a_fresado_top_e004_contorno_pieza_prof10.iso    102 líneas
r_pv_a_galceado_top_e004_contorno_pieza_prof10.iso   102 líneas
diff (sin la línea 1)  ->  BYTE-IDÉNTICOS
```

⇒ **Tercera confirmación —y la más fuerte posible— de que la familia de emisión la decide la
HERRAMIENTA, no la operación de la UI.** El canal (§19 de `canal.md`) y el fresado (§4 de
`fresado.md`) habían mostrado que *«coinciden en estructura»*; acá coinciden **byte a byte**.

⇒ **Para el converter: el Galceado no necesita ni una línea propia de emisión.** Lo que sí
necesita es el **modelo del `.pgmx`**, que es donde están las diferencias.

⇒ Y se hereda todo, sin re-barrer: el bloque (`50 + N segmentos`), el catálogo (`SVL`, `SVR`,
`S`, `F`, `DescentSpeed`), la cota de seguridad, los atributos, las transiciones, el conteo del
`Xmsg`, los seis casos de fail-loud.

## 2. ⚠️ La nomenclatura: el taller dice `Escuadrado` y Maestro dice TRES cosas

Era lo primero que el lote pedía, y la captura de la ventana lo resuelve — el problema **no es
nuestro**:

| dónde | cómo lo llama |
|---|---|
| **el taller** (dato de Fermín, 2026-09-12) | **`Escuadrado`** — *«esa es la función: escuadrar la pieza, o sea, llevar la pieza a sus medidas finales y sus esquinas a 90 grados»* |
| el **botón** de la cinta `Operaciones` | **`Galceado`** |
| el **tooltip** de ese botón | **«Contorno.** Mando que permite crear un contorno…» |
| el **panel** que se abre, y su sección | **`Perfilado`** / `Datos perfilado` |
| el **`Name`** que Maestro escribe en el `.pgmx` | **`Perfilado`** |
| el **tipo serializado** | **`ContourFeature`** |
| nuestro código | `contour.py`, docstring *«Squaring milling contracts»* |

### ⚠️ CORRECCIÓN MÍA (2026-09-12): el docstring del código NO estaba inventado

Escribí que *«Squaring no es ninguno de los tres»* y que era un nombre nuestro sin respaldo.
**Es falso.** Con el dato de Fermín: **`Squaring` es `Escuadrado` en inglés** — o sea, el
docstring nombraba la operación **por el término del taller y por su función**, que es la única
de las seis denominaciones que **dice lo que la operación hace**.

⇒ Y eso **matiza el ejemplo que el `CLAUDE.md` usa para enseñar la regla 1**:

> *«una spec llamada por la operación genérica y no por su feature (`SquaringMillingSpec` para
> lo que la UI llama Galceado)»*

La parte que **sigue en pie** es la de fondo: la spec se nombra por **lo que hace** y no por
**lo que es en el archivo**, y eso oculta que el tipo serializado es `ContourFeature`. La parte
que **hay que ajustar** es el paréntesis: presenta `Galceado` como si fuera el nombre correcto,
y resulta que **`Galceado` es sólo uno de los tres nombres que Maestro usa en la misma
pantalla** — y probablemente el peor, porque *galce* es el rebaje donde algo encaja, no una
escuadra. Huele a mala traducción del italiano.

⇒ ⚖️ **Y eso convierte la decisión en algo más chico de lo que parecía**: no hay que elegir
entre seis nombres, hay que decidir **si la spec se llama por la función (`Escuadrado` /
`Squaring`) o por el tipo del archivo (`Contour`)**. Mi propuesta ahora:

| | |
|---|---|
| en la **doc y al hablar** | **`Escuadrado`**, el término del taller y el único que dice qué hace |
| el **tipo serializado** | **`ContourFeature`**, intocable (viene del `.pgmx`) |
| la **spec** del sintetizador | por el tipo del archivo, para que el nombre diga **qué es**: `ContourSpec` (el archivo ya se llama `contour.py`) |
| y se **documenta** que la UI dice `Galceado`/`Contorno`/`Perfilado` | no es cosmético: **`Perfilado` es lo que el converter lee del `.pgmx`** |

📌 Lo que hay que corregir del código en cualquier caso es **el docstring**: hoy dice sólo
«Squaring milling contracts», sin explicar que es el `Galceado` de la cinta ni que Maestro lo
serializa como `ContourFeature`. Un lector que abra el archivo no puede saber de qué operación
se trata.

## 3. La ventana `Perfilado`, capturada

| sección | qué tiene |
|---|---|
| **Datos perfilado** | `Anchura` (en **gris**, = Ø de la herramienta) · `Profundidad` · `Pasante` · `Rebaba` (en gris) |
| ⭐ **Perfil** | radios **`Pieza`** / **`Geometría`** |
| ⭐ **Lado** | radios **`Externo`** / **`Interno`** — **en gris cuando el perfil es `Pieza`** |
| **Datos tecnológicos** | el desplegable de herramienta · `Avanz.` y `Rotación` vacíos |
| **Estrategia** · **Acercamiento/Alejamiento** · **Datos avanzados** · **Datos máquina** | plegadas, y con las capturas hechas |

### ⛔ Y lo que NO tiene, que es la diferencia de fondo con el `Fresado`

**No tiene los cuatro botones de corrección de herramienta ni los radios `Corrección C.N.` /
`Corrección CAD`.**

⇒ ⭐⭐ **El Galceado no expone la corrección: la resuelve con `Perfil` + `Lado`.** En vez de
elegir «izquierda/derecha» respecto del avance —que en un contorno cerrado es poco intuitivo—,
elegís **externo o interno respecto del contorno**. Es la misma cosa dicha de la forma en que un
escuadrado se piensa.

⇒ Y por eso **el Grupo 4 del pedido (la corrección) no existe como tal**: queda reemplazado por
el barrido de `Perfil` × `Lado`, que Fermín ya arrancó en el Grupo 2.

### ⭐⭐ Y hay DOS restricciones más, que son las que importan (dato de Fermín, 2026-09-12)

> *«La ventana reemplaza las correcciones izquierda y derecha por interno y externo, y **no
> ofrece ninguna opción para corrección central**. Tampoco me permite **modificar manualmente
> entre CAD y C.N.**»*

Los **14 archivos del lote lo respaldan**: `SideOfFeature` vale sólo `Right` (12) o `Left` (2),
**nunca `Center`**, y `ActivateCNCCorrection` está en **`true` en todos**.

#### 1 · No existe la corrección central ⇒ el Galceado SIEMPRE corrige

En el fresado `Center` era el default: sin corrección, `G40`, la traza nominal. Acá **no se
puede elegir**, y tiene sentido físico — un escuadrado sin corrección comería la mitad del
material que tiene que dejar, así que la pieza saldría con la medida equivocada.

⇒ ⭐ **Regla del modelo**: un `ContourFeature` **nunca** lleva `SideOfFeature = Center`.
⇒ Y el converter lo puede usar como **validación**: un `.pgmx` con esa combinación es un archivo
que **Maestro no pudo haber producido**.

#### 2 · No se puede elegir CAD ⇒ el Galceado SIEMPRE emite `G41`/`G42`

`ActivateCNCCorrection` no es editable en esta ventana, y está fijo en `true`.

⇒ ⭐⭐ **El ISO del Galceado lleva SIEMPRE la línea nominal más `G41`/`G42`**, nunca la traza
offseteada. Y de ahí salen tres consecuencias para el converter, todas a favor:

| | |
|---|---|
| **nunca hay que deshacer la corrección** | el trabajo fino que el canal §21 derivó no aplica acá |
| **nunca aparecen los arcos de esquina** del offset exterior | son del modo CAD (`fresado.md` §30.2) |
| **nunca se enciende el «modo largo»** | lo enciende `cnc = false` (`fresado.md` §15.3) |

> ⚠️ **Las tres valen sólo SIN multipaso.** Escribí acá que el pendiente «falta un caso en CAD
> para ver los arcos de esquina» **era imposible porque la ventana no lo ofrece**, y es falso:
> con multipaso la ventana pone `cnc = false` **por su cuenta**. Las tres consecuencias se dan
> vuelta y los arcos aparecen. Ver **§9**.

#### ❓ Pero abre una pregunta concreta, y es la del Grupo 6

En el fresado, **con multipaso la UI FUERZA `CAD`** (`fresado.md` §20). Acá **CAD no se puede
elegir**. Las dos cosas no pueden ser ciertas a la vez, así que el Galceado con multipaso tiene
que hacer **una de tres**:

| | qué significaría |
|---|---|
| sale con `cnc = false` | la UI lo **fuerza sin mostrarlo** ⇒ el flag no es editable, pero sí cambia |
| sale con `cnc = true` y traza nominal | el Galceado **no** se rige por la regla del fresado |
| **no admite multipaso** | otra restricción de la operación |

⇒ **Un solo archivo lo decide**: el contorno de la pieza con `Unidireccional` + `PH`. Es el que
más rinde de lo que queda del lote.

## 4. El modelo en el `.pgmx`: tres diferencias contra el fresado

Descontando los identificadores internos, el diff del XML entre los dos archivos del par de
control son **tres cosas**:

| | `Fresado` | `Galceado` |
|---|---|---|
| tipo de feature | `GeneralProfileFeature` | **`ContourFeature`** |
| `Name` del paso y de la feature | `Fresado` | **`Perfilado`** |
| campo propio | — | **`<ContourType>`** |

### ⭐ `ContourType` es el radio `Perfil`

| la UI | el `.pgmx` |
|---|---|
| `Perfil = Pieza` | **`ContourType = Workpiece`** |
| `Perfil = Geometría` | **`ContourType = Geometry`** |

### ⭐⭐ Y el `Lado` NO es un campo nuevo: reusa `SideOfFeature`

| la UI | el `.pgmx` | el ISO |
|---|---|---|
| `Lado = Externo` | **`SideOfFeature = Right`** | **`G42`** |
| `Lado = Interno` | **`SideOfFeature = Left`** | **`G41`** |
| `Perfil = Pieza` (lado en gris) | `Right` — el default | `G42` |

El diff de los ISO entre externo e interno es **UNA sola línea**: `G42` contra `G41`. Todo lo
demás —la traza nominal incluida— es idéntico, porque están en modo C.N. y el control compensa.

⇒ ⭐ **Para el converter esto es una buena noticia**: `Externo`/`Interno` **no agrega nada** al
modelo. Es el `SideOfFeature` que ya sabe leer, con otra etiqueta en la UI. Y el `G41`/`G42`
sigue la misma regla del fresado — cruzar el lado con el sentido (`fresado.md` §26.2).

⇒ Y confirma desde otra operación lo que `fresado.md` §34.6 dejó en una sola regla:
**`SideOfFeature` es el lado de la herramienta respecto del avance**, y la UI del Galceado lo
presenta como *externo/interno* porque en un contorno cerrado con sentido conocido las dos
formas de decirlo son equivalentes.

## 5. Grupo 1 — los cuatro puntos de inicio

Fermín amplió el grupo con el contorno arrancando en **el medio de cada uno de los cuatro
lados**:

| archivo | arranca en | el milímetro del `G42` va en |
|---|---|---|
| `_inicio_frontal_medio` | `(200, 0)` | `X199 → X200` ⇒ **+X** |
| `_inicio_derecho_medio` | `(400, 200)` | `Y199 → Y200` ⇒ **+Y** |
| `_inicio_trasero_medio` | `(200, 400)` | `X201 → X200` ⇒ **−X** |
| `_inicio_izquierdo_medio` | `(0, 200)` | `Y201 → Y200` ⇒ **−Y** |

⇒ **Los cuatro recorren en el mismo sentido (antihorario)** y sólo cambia el punto de arranque.
Y los cuatro salen en **cinco segmentos**, porque el lado que contiene el arranque se recorre en
dos tramos — igual que en el fresado (`fresado.md` §30.5).

⇒ ⭐ **Y el milímetro de entrada de `G41`/`G42` va SIEMPRE por la tangente del primer
movimiento**, ahora con las **cuatro direcciones** medidas. Confirma `fresado.md` §21.5 y cierra
el acotamiento que §34.4 le había puesto: cuando el lado es coherente, la tangente manda.

## 6. Grupo 2 — lo que ya está (iniciado)

| archivo | qué varía | resultado |
|---|---|---|
| `contorno_pieza_prof10` | el mínimo con `Perfil = Pieza` | la referencia |
| `contorno_pieza_pasante` | `ThroughMillingBottom`, depth 18 | ✅ igual que el fresado |
| `contorno_pieza_pasante_extra1` | el `Extra` del pasante | ✅ **`Z−19`** = −(espesor + `Extra`) — §12 |
| `contorno_pieza_prof10_rebaba5` | `SideOffset = 5` | ✅ la `Rebaba` es `SideOffset`, igual que el fresado |
| `rectangulo_geometria_lado_externo` · `_interno` | ⭐ `ContourType = Geometry` × `Lado` | **`G42`** contra **`G41`**, una línea de diff |
| los dos anteriores `_inicio_medio` | el arranque en el punto medio, sobre geometría | |

⇒ Con esto el `Perfil` y el `Lado` quedan **derivados los cuatro cruces** de la ventana.

## 7. Lo que el lote ya no necesita

Por el par de control byte-idéntico del §1, se cae casi todo el pedido original:

| grupo del pedido | estado |
|---|---|
| 1 · el mínimo y la predicción | ✅ **cumplida byte a byte** |
| 2 · lo propio de la ventana | 🔄 **en curso** — y son dos campos: `Perfil` y `Lado` |
| 3 · la geometría | ⚠️ **replantear**: lo que decide es `ContourType`, no la familia de la geometría. Queda ver si acepta una **línea abierta** y un **círculo** |
| 4 · la corrección | ⛔ **no existe**: la ventana no la ofrece (§3) |
| 5 · los testigos de lo heredado | ⛔ **innecesario**: el ISO es byte-idéntico al del fresado |
| 6 · estrategia y multipaso | ⚠️ **acotar**: las capturas muestran el mismo desplegable de cuatro; basta un testigo |
| 7 · el barrido A5 | ✅ **sigue en pie** — es la rutina permanente, y en el fresado el espejo tecnológico **sí** tocó la traza |

## 8. Lo que quedaba abierto al abrir el lote — y qué pasó con cada cosa

> 📌 Esta tabla es de **antes** de la tanda reorganizada. El estado vigente está en **§16**.

| | |
|---|---|
| ⚖️ **la nomenclatura** | ⚖️ **SIGUE ABIERTA** — el taller dice **`Escuadrado`** y Maestro dice tres cosas (§2). La decisión se reduce a: la spec por la **función** o por el **tipo del archivo**. **De Fermín** |
| el `Extra` del pasante | ✅ **CERRADO (§12)**: `Z = −(espesor + Extra)` |
| `ContourType` con una **línea abierta** | ✅ **CERRADO (§14)**: **la rechaza**, con cartel — y el cartel era la respuesta, como decía la anotación |
| `ContourType` con un **círculo** | ✅ **CERRADO (§13.3)**: se emite en **dos arcos de media vuelta** |
| ~~el **offset exterior** y sus arcos de esquina~~ | ✅ **CERRADO (§9)** — y **al revés de lo que había escrito**: con multipaso la ventana fuerza `cnc = false` sin mostrarlo, y los cuatro arcos de radio `SVR` centrados en los vértices **aparecen** |
| ❓ **el Galceado con multipaso** | ✅ **CERRADO (§9)**: de las tres respuestas posibles salió **la primera** — la UI lo fuerza **sin mostrarlo** |
| la **estrategia** y el **acercamiento** | ✅ **CERRADOS (§10 y §11)** — y con mucho más que un testigo: las tres estrategias y un barrido de 18 archivos |
| el **barrido A5** | ⏳ **SIGUE EN PIE** — la rutina permanente, ocho archivos con captura. Es lo único grande que falta |

---

# El lote reorganizado (2026-09-12) — 42 pares y 11 capturas

Fermín reorganizó las carpetas y entregó **más de lo pedido**: `Grupo 1` con 6 pares, `Grupo 2`
con 30 y `Grupo 3` con 6, más **once capturas**. De los 42 ISO hay **36 distintos**; las seis
repeticiones están identificadas una por una en §15.

## 9. ⭐⭐⭐ El multipaso FUERZA `CAD` sin mostrarlo, y los arcos de esquina SÍ aparecen

§3 dejó la pregunta con tres respuestas posibles y dijo que **un archivo la decidía**. Son
cuatro, y la respuesta es **la primera**:

| archivo | nodo `MachiningStrategy` | `ActivateCNCCorrection` |
|---|---|---|
| `contorno_pieza_prof10` (la referencia) | **no existe** | **`true`** |
| `uni_SCS_ph5` | `UnidirectionalMilling` | **`false`** |
| `uni_EP_ph5` | `UnidirectionalMilling` | **`false`** |
| `bi_ph5` | `BidirectionalMilling` | **`false`** |
| `zigzag_pa2_pr3` | `ZigZagMilling` | **`false`** |

⇒ ⭐⭐ **La ventana fuerza `CAD` sin mostrarlo.** Es el mismo comportamiento que el fresado
(`fresado.md` §20), sólo que acá el radio ni siquiera existe para verlo: la única señal es el
atributo en el archivo. Y el ISO lo confirma por los dos lados — los cuatro **no llevan
`G41`/`G42`** (tres `G40` y nada más, contra el `G42` + cuatro `G40` de la referencia) y la
traza sale **ya offseteada**: `X−2`, `X402`, `Y402`, `Y−2` para un cuadrado de 400 con `SVR 2`.

### 9.1 ⚠️ CORRECCIÓN MÍA: los arcos de esquina NO son imposibles

Escribí en §3 y §8 que el pendiente «falta un caso en CAD para ver los arcos de esquina» **era
IMPOSIBLE porque la ventana no ofrece CAD**. **Es falso**, y el error es de método: razoné sobre
**lo que la ventana deja elegir** en vez de **leer el atributo en los archivos** — que es
exactamente lo que `CLAUDE.md` §5 manda («ninguna derivación cita un nombre; cita el atributo
leído del `.pgmx`»). La ventana no lo ofrece **y lo cambia igual**.

Los arcos están, cuatro por pasada:

```
G1 Z-5.000 F5000.000
G3 X0.000   Y-2.000   I0.000   J0.000     <- esquina (0,0),     radio 2
G1 X400.000 Z-5.000
G3 X402.000 Y0.000    I400.000 J0.000     <- esquina (400,0)
G1 Y400.000 Z-5.000
G3 X400.000 Y402.000  I400.000 J400.000   <- esquina (400,400)
G1 X0.000   Z-5.000
G3 X-2.000  Y400.000  I0.000   J400.000   <- esquina (0,400)
G1 Y0.000   Z-5.000
```

⇒ **Radio `SVR`, centro exactamente en el vértice, ocho elementos donde la geometría tiene
cuatro.** Misma regla que `fresado.md` §30.2, ahora con testigo propio.

⇒ Y la conclusión útil **se invierte**: el converter del Galceado **sí tiene que saber redondear
las esquinas del offset exterior**, porque el multipaso se lo mete por la puerta de atrás.

### 9.2 ⭐⭐ Y acota el gatillo de `%DONTCARESPEEDV=1`

`uni_SCS_ph5` es `LiftShiftPlunge` + multipaso —la combinación exacta que `fresado.md` §16.1
identificó como la que emite **la línea que para el CNC**— y **no la emite**. Más todavía: el
diff entre `uni_SCS_ph5` y `uni_EP_ph5` está **vacío**.

La diferencia con el fresado es **la geometría**: allá los cinco testigos eran una **línea
abierta** (`x50_x350_y200_prof10`), acá es un **contorno cerrado**, y en un cerrado **no hay
retorno entre pasadas** (`fresado.md` §34.6) — la herramienta se hunde en el mismo punto donde
cerró la vuelta anterior.

⇒ ⭐ **El gatillo no es «SCS + multipaso»: es «SCS + multipaso *con retorno real*»**, o sea
geometría abierta. Importa concretamente: omitir esa línea es una **divergencia deliberada
declarada**, y una divergencia se audita por su gatillo — cuanto más preciso, menos casos en que
el converter se aparta de Maestro sin necesidad.

## 10. Las tres estrategias

### 10.1 Los nombres, de la ventana al `.pgmx`

Las capturas `galceado_estrategia_*.PNG` dan el mapa completo, y el desplegable es **el mismo
que el del fresado**:

| ventana | `.pgmx` | valor en el lote |
|---|---|---|
| `Estrategia` → **`Unidireccional`** | `MachiningStrategy i:type="UnidirectionalMilling"` | |
| `Estrategia` → **`Bidireccional`** | `BidirectionalMilling` | |
| `Estrategia` → **`ZigZag`** | `ZigZagMilling` | |
| `Conexión entre huecos` → **`Salida a cota de seguridad`** | `StrokeConnectionStrategy` = **`LiftShiftPlunge`** | |
| `Conexión entre huecos` → **`En la pieza`** | `StrokeConnectionStrategy` = **`Straghtline`** | |
| `Habilitar multipaso` | `AllowMultiplePasses` | `true` |
| `Profundidad hueco` | **`AxialCuttingDepth`** | `5` |
| `Último hueco` | **`AxialFinishCuttingDepth`** | `0` |
| ZigZag → `Pasada avance` | **`FeedCuttingDepth`** | `2` |
| ZigZag → `Pasada retorno` | **`ReturnCuttingDepth`** | `3` |

> 📌 **`Straghtline` está mal escrito en el enum de Maestro** (falta la `i` de *Straight*). El
> converter tiene que leer **el typo**, no la palabra correcta. Es el tipo de detalle que un
> nombre «arreglado» rompería en silencio.

Y el nodo trae **cuatro campos que la ventana del Galceado no muestra**: `Overlap` (el solape,
en `0`), `Cutmode` (**`Climb`**, o sea concordancia), `RadialCuttingDepth` y
`RadialFinishCuttingDepth` (los dos en `0`). ⇒ el modelo es **compartido con el `Vaciado`**, que
es el que necesita pasadas radiales. **No inventar campos para el Galceado: leer los que hay.**

### 10.2 `Unidireccional`: en un contorno cerrado `SCS` y `EP` son byte-idénticos

Dos pasadas, las dos en **el mismo sentido**, con un hundimiento vertical entre ellas **en el
mismo punto donde cerró la anterior**:

```
G1 Z-5.000     <- pasada 1 a media profundidad
   ... la vuelta completa ...
G1 Z-10.000    <- hundimiento en el punto de cierre, sin retirada ni reposicionado
   ... la vuelta completa otra vez ...
```

⇒ `LiftShiftPlunge` y `Straghtline` **no llegan al ISO**: el diff está vacío. Confirma el
hallazgo del fresado desde el otro lado — y es lo que habilita el acotamiento de §9.2.

### 10.3 `Bidireccional`: alterna el sentido, y los arcos cambian de `G3` a `G2`

La segunda pasada recorre el contorno **al revés**: arranca por `G1 Y400` en vez de `G1 X400`, y
**los cuatro arcos de esquina pasan de `G3` a `G2`**.

⇒ 📌 Es la consecuencia geométrica correcta —el mismo arco recorrido al revés cambia de
sentido—, y es una **trampa para el converter**: el `G2`/`G3` de un arco de esquina **no lo
decide el lado de la corrección**, lo decide el sentido de esa pasada. En una estrategia
bidireccional el signo alterna pasada a pasada.

### 10.4 ⭐⭐⭐ `ZigZag`: es una hélice continua, y la Z **está serializada en el `.pgmx`**

En un contorno cerrado el ZigZag no hace pasadas planas: **baja mientras recorre**. Son cinco
vueltas para una profundidad de 10:

| vuelta | sentido | `Z` al cerrar | paso |
|---|---|---|---|
| 1 | adelante (`G3`) | `−2.000` | **2** = `FeedCuttingDepth` |
| 2 | atrás (`G2`) | `−5.000` | **3** = `ReturnCuttingDepth` |
| 3 | adelante (`G3`) | `−7.000` | **2** |
| 4 | atrás (`G2`) | `−10.000` | **3** |
| 5 | adelante (`G3`) | `−10.000` | **0** — una vuelta **plana** de terminación |

⇒ **Los dos pasos alternan según el sentido**, y el nombre del archivo (`pa2_pr3`) dice
exactamente eso: `Pasada avance` 2 en las vueltas de ida, `Pasada retorno` 3 en las de vuelta.
La quinta vuelta plana aparece **aunque `Último hueco` valga `0`**: la necesita para limpiar el
escalón que la hélice deja en el fondo.

#### Y dentro de cada vuelta la `Z` **no** es proporcional a lo recorrido

Las `Z` intermedias de la primera vuelta son `−0.004, −0.503, −0.880, −1.440, −1.721, −1.930,
−1.983, −2.000`. Una hélice uniforme daría `−0.004, −0.500, −0.504, −1.000, −1.004, −1.500,
−1.504, −2.000`. **No coincide**: el **72 %** del descenso ocurre en la primera mitad, y los
cuatro arcos de esquina se comen el **36 %** siendo el **0.8 %** del recorrido.

Y el perfil es **el mismo en las dos vueltas**, en fracción del paso — idéntico con paso 2 y con
paso 3. O sea: es determinista, no es ruido.

#### ⭐⭐⭐ Pero el converter **no necesita la fórmula**, porque la traza viene resuelta

El `Toolpath` de tipo `TrajectoryPath` es un `GeomCompositeCurve` con **40 elementos** (5 vueltas
× 8) y cada uno serializa su **largo 3D**:

```
<d:string>8 0 400.000311283444
1 ...</d:string>
```

Y `400.000311283444` = **√(400² + 0.499²)** — el largo 3D del tramo con su caída de `Z`
incluida. Los cuatro tramos rectos de la primera vuelta declaran `400.000311`, `400.000392`,
`400.000054` y `400.000000`, que devuelven exactamente las caídas `0.499`, `0.560`, `0.209` y
`0.017` del ISO. Los arcos serializan **el ángulo barrido** (`1.5707949…` ≈ π/2) y un **radio
efectivo mayor que 2** (`2.0304`, `2.0169`, `2.0679`), que es el de la hélice y no el del
círculo.

⇒ ⭐⭐⭐ **La `Z` rara está guardada, no hay que derivarla.** Es el **tercer caso** del mismo
patrón, y ya se puede enunciar como regla del converter:

| caso | qué resuelve Maestro dentro del `.pgmx` |
|---|---|
| la **elipse** | la aproxima en 36 arcos (`fresado.md` §27) |
| la **rampa** | largo **y** dirección en 3D, exacta a 17 dígitos |
| la **hélice del ZigZag** | los 40 largos 3D, con la `Z` de cada elemento |

⇒ **Regla: cuando la geometría de la traza es difícil, el converter la LEE; no la calcula.** Y
al revés —esto es lo que hay que cuidar— **no puede inventar** una hélice uniforme «razonable»:
sería un default disfrazado de hipótesis, justo lo que `CLAUDE.md` §4 prohíbe. Si algún día
apareciera un `.pgmx` con la estrategia puesta y **sin** traza serializada, es **fail-loud**.

## 11. El acercamiento y el alejamiento, barrido completo (18 archivos)

Fermín barrió `{acercamiento, alejamiento}` × `{lineal, arco}` × `{mr2, mr4}` × `{cota,
bajada/subida}`, con **dos herramientas de `SVR` distinto**, más dos archivos que combinan los
dos con arranque en el medio. Es el barrido más completo del lote y cierra la operación entera.

### 11.1 ⭐⭐ La distancia es `RadiusMultiplier × SVR`, con dos radios que lo prueban

| herramienta | `SVR` | `mr` | distancia emitida |
|---|---|---|---|
| `E004` | `2.000` | 2 | **4.000** |
| `E004` | `2.000` | 4 | **8.000** |
| `E001` | `9.180` | 2 | **18.360** |
| `E001` | `9.180` | 4 | **36.720** |

⇒ **Dos herramientas y dos multiplicadores**: el producto queda derivado, no ajustado. Y vale
igual para el **arco** (es su radio) y para la **recta** (es su largo) — el mismo número, dos
geometrías.

### 11.2 El modo decide **dónde va la `Z`**, y eso cuenta líneas

| modo | qué hace | líneas vs. base |
|---|---|---|
| **`Quote`** (`cota`) | baja **vertical** en el punto de arranque del acercamiento y **después** hace el movimiento a la cota final | **+1** |
| **`Down`** (`bajada`) | el movimiento de acercamiento **lleva la `Z`**: `G1` inclinado, o `G2`/`G3` **helicoidal** | **+0** |
| **`Up`** (`subida`) | el movimiento de alejamiento **lleva la subida**, y absorbe el `G1 Z30` | **+0** |

Los cuatro casos del acercamiento con la `E004`, tal cual salen:

```
recta / cota      G1 X-4 Y0 Z30 F2000  ·  G1 Z-10 F2000  ·  G1 X0 Z-10 F2000
recta / bajada    G1 X-4 Y0 Z30 F2000  ·                    G1 X0 Z-10 F2000        <- inclinado
arco  / cota      G1 X-4 Y-4 Z30 F2000 ·  G1 Z-10 F2000  ·  G2 X0 Y0 I0 J-4 F2000
arco  / bajada    G1 X-4 Y-4 Z30 F2000 ·                    G2 X0 Y0 Z-10 I0 J-4    <- helicoidal
```

⇒ ⭐ **El arco en `bajada` es un `G2`/`G3` con `Z`**: una hélice de un cuarto de vuelta. (Lo
había dado por ausente al medir con un patrón que exigía `I`/`J` inmediatamente después de la
`Y`; el arco estaba, con la `Z` en el medio. **El patrón mentía, no el archivo.**)

### 11.3 El arco es tangente, y su centro cae **del lado de la corrección**

| | |
|---|---|
| **acercamiento** | centro a distancia `mr × SVR` del punto de arranque, **perpendicular** al primer movimiento; un cuarto de vuelta |
| **alejamiento** | centro a la misma distancia del punto de cierre, perpendicular al **último** movimiento |
| **el lado** | el centro cae del lado donde está la herramienta (`Right` ⇒ a la derecha del avance) |

Ejemplo del alejamiento con la `E001` (`SVR 9.180`, `mr2`): cierra en `(0,0)` viniendo en `−Y`, y
emite `G2 X-18.360 Y-18.360 I-18.360 J0.000` — centro `(−18.36, 0)`, radio `18.36`, un cuarto de
vuelta.

### 11.4 El milímetro de entrada y de salida va **por la tangente**, siempre

El `G0` de preposición cae **1 mm antes** del primer punto y el `G1` final **1 mm después** del
último, los dos **sobre la tangente**:

| caso | preposición | salida |
|---|---|---|
| base, arranque en `(0,0)` hacia `+X` | `X−1 Y0` | `X0 Y−1` |
| acercamiento recto `mr2` (arranca en `X−4`) | `X−5 Y0` | |
| acercamiento recto `mr4` (arranca en `X−8`) | `X−9 Y0` | |
| alejamiento en arco (cierra en `(−18.36,−18.36)` con tangente `−X`) | | `X−19.36 Y−18.36` |

⇒ Confirma §5 con dos casos nuevos: **el milímetro se mide desde el punto del acercamiento, no
desde el contorno**, y en un arco se mide **sobre la tangente del arco**.

### 11.5 ⚠️ Y una asimetría que el converter tiene que respetar: los avances

| | avance emitido |
|---|---|
| el movimiento de **acercamiento** | **`F2000`** = el de bajada (`DescentSpeed`) |
| el movimiento de **alejamiento** | **`F5000`** = el de corte (`FeedRate`) |

⇒ No es simétrico y no es deducible del sentido común: **entrar** es una bajada, **salir** es un
corte. Los ocho archivos del alejamiento y los ocho del acercamiento lo sostienen.

### 11.6 ⚠️ Dos nombres que el archivo desmiente (auditoría de los 18)

`CLAUDE.md` §5: el nombre no es evidencia. Auditando **tipo × multiplicador × modo** contra el
`.pgmx`, **16 de 18 coinciden** y dos no:

| archivo | lo que afirma el nombre | lo que dice el `.pgmx` | consecuencia |
|---|---|---|---|
| `E004_acerc_arco_mr4_bajada` | `mr = 4` | **`RadiusMultiplier = 2`** | es un **duplicado exacto** de `_mr2_bajada` (diff vacío) |
| `E001_aleja_lineal_mr2_subida` | modo `Up` | **`DetachMode = Quote`** | es un **duplicado exacto** de `_mr2_cota` (diff vacío) |

⇒ **Los dos cruces que esos nombres prometen quedan sin testigo**: `arco + bajada + mr4` y
`lineal + subida + mr2`. Ninguno bloquea nada —la fórmula está cruzada por las otras catorce
combinaciones, y los dos casos son **predecibles**: radio `8` helicoidal el primero, `18.36` con
la subida absorbida el segundo—, pero **quedan anotados como predicción a verificar**, no como
derivados.

⇒ 📌 Y de paso: el `Approach` con `IsEnabled = false` trae `RadiusMultiplier = 1.2`, que **no es
ninguno de los defaults de la ventana `Opciones`** (2 en una PC, 4 en otra). Es el default de
fábrica del nodo, inerte mientras el acercamiento está apagado. **Un valor que no significa lo
que aparenta**: leerlo sin mirar `IsEnabled` sería inventar un acercamiento que no existe.

## 12. Profundidad, `Pasante`, `Extra` y `Rebaba`

| archivo | campo | efecto en el ISO |
|---|---|---|
| `contorno_pieza_prof10` | `Profundidad = 10` | `Z−10.000` |
| `contorno_pieza_prof15` | `Profundidad = 15` | `Z−15.000` |
| `contorno_pieza_pasante` | `Pasante`, espesor `dz1 = 18` | `Z−18.000` |
| `contorno_pieza_pasante_extra1` | `Pasante` + `Extra = 1` | ⭐ **`Z−19.000`** |
| `contorno_pieza_prof10_rebaba5` | `Rebaba = 5` | ⭐ `SVR 2.000` → **`SVR 7.000`**, y `VL7=7.000` |

⇒ ⭐ **`Extra` es el sobrepaso por debajo de la cara inferior**: `Z = −(espesor + Extra)`. Cierra
el pendiente de §8. Es el mismo mecanismo que el pasante del fresado, con el nombre de este
panel.

⇒ **`Rebaba` entra por `SVR`**, no por la traza: `SVR = radio del cuerpo + Rebaba` (2 + 5 = 7),
y se escribe **dos veces** — en `SVR` y en la variable `VL7`. Igual que el fresado.

## 13. Grupo 3 — `Perfil`, `Lado` y el círculo

### 13.1 ⭐⭐ `ContourType` es de dónde sale la geometría, **no** un parámetro de emisión

El diff entre `contorno_pieza_prof10` (`Workpiece`) y `rectangulo_geometria_lado_externo_prof10`
(`Geometry`) son **cuatro bloques —siete líneas— y nada más**: los mismos códigos, la misma estructura,
**otras coordenadas** (el rectángulo dibujado va de 50 a 350, el contorno de la pieza de 0 a 400).

⇒ ⭐ **El converter no necesita ninguna rama por `ContourType`**: resuelve la polilínea —del
perímetro de la pieza o del dibujo— y emite igual. Es un campo del **modelo**, no del **emisor**.

### 13.2 ⭐⭐ `Externo`/`Interno` es `SideOfFeature`, con testigo cruzado

| archivo | `SideOfFeature` | emite |
|---|---|---|
| `rectangulo_geometria_lado_externo_prof10` | `Right` | **`G42`** |
| `rectangulo_geometria_lado_interno_prof10` | `Left` | **`G41`** |
| `circulo_geometria_lado_externo_prof10` | `Right` | **`G42`** |
| `circulo_geometria_lado_interno_prof10` | `Left` | **`G41`** |

Los dos pares tienen **una sola línea de diff**, y la traza es **idéntica**: mismos puntos, mismo
sentido, mismo radio. El contorno se recorre **antihorario**, y en antihorario el afuera queda a
la **derecha** del avance ⇒ `Externo` = `Right` ⇒ `G42`.

⇒ ⭐⭐ **La ventana renombra `SideOfFeature`, no agrega nada.** «Externo/Interno» es «Right/Left»
resuelto contra el sentido del dibujo, que es **la misma regla única** que el fresado derivó con
la corrección de Fermín del 09-11. El converter lee el campo y aplica la regla que ya tiene:
**cero reglas nuevas para el Galceado**.

📌 Y con eso queda claro por qué en los Grupos 1 y 2 **todo es `Right`**: con `Perfil = Pieza`
la ventana **deshabilita** los radios de `Lado` (visible en gris en las capturas). El `Lado` sólo
se elige sobre `Geometría` — y de ahí que el único par que lo cruza sea el del Grupo 3.

### 13.3 ⭐ El círculo completo sale en **dos arcos de media vuelta**

```
G0 X300.000 Y199.000
G1 X300.000 Y200.000 Z30.000 F2000.000
G1 Z-10.000 F2000.000
G3 X100.000 Y200.000 I200.000 J200.000 F5000.000    <- media vuelta
G3 X300.000 Y200.000 I200.000 J200.000 F5000.000    <- la otra media
G1 Z30.000 F5000.000
G40
G1 X300.000 Y201.000 Z30.000 F5000.000
```

⇒ ⭐ **Un círculo cerrado NO se emite como un `G3` único.** Se parte en dos de 180°, y tiene que
ser así: un arco cuyo punto final es igual al inicial es ambiguo para el control. **Regla de
emisión, no detalle de estilo.**

⇒ Y el círculo arranca en `(300, 200)` —el punto de `X` máxima— con preposición en `(300, 199)`
y salida en `(300, 201)`: el milímetro **sobre la tangente del arco**, que en ese punto es `±Y`.
Confirma §11.4 en geometría curva.

⇒ El ISO son **101 líneas** contra las 103 del rectángulo: dos arcos donde había cuatro rectas.

## 14. ⛔ El Galceado **rechaza** la geometría abierta — con testigo

`galceado_linea_error.PNG` es la captura del intento de aplicar el Galceado a **una línea**, y
Maestro la rechaza con un cartel:

> ¡Atención! **Las geometrías compatibles con perfilado son geometrías cerradas como el círculo,
> la elipse y la polilínea. El perfilado no se puede aplicar en geometrías de diferente tipo.**

⇒ ⭐⭐ **Cierra el pendiente de §8 con un negativo *con testigo***, que es lo que `CLAUDE.md` §5
exige: no es que el ISO no cambie, es que **no hay ISO** — la operación no se crea.

⇒ Y le da al converter una **validación de entrada**: un `ContourFeature` cuya geometría **no
cierra** es un archivo que **Maestro no pudo haber producido**. Es la segunda validación de este
tipo en el Galceado, junto a la de `SideOfFeature = Center` (§3).

⇒ 📌 La captura confirma además, de paso, tres cosas de la ventana: el cartel **también dice
«perfilado»** —no «galceado»— ⇒ `Perfilado` es el nombre de la operación **en los mensajes de
Maestro**, no sólo en el título del panel; `Anchura` está en gris con el **Ø de la herramienta**;
y la pieza del lote es **400 × 400 × 18** (`dx1`/`dy1`/`dz1`).

### 14.1 Los testigos de lo que **no** está puesto

`galceado_acercamiento_datos_avanzados.PNG` y los dos `..._datos_máquna_*.PNG` son los testigos
que `CLAUDE.md` §5 pide para un negativo:

| sección | lo que muestra |
|---|---|
| **Datos avanzados** | `Invertir` **sin marcar** · `Condición` = `True` · `Comentario` vacío · **`Cota de seguridad` = 30** |
| **Datos máquina** | las **nueve** funciones de máquina con `Selecciona` **sin marcar** (Paleta, Jerk, Jerk3D, Campana neumática, Campana auxiliar, Frenos ejes rotativos, Desenrollado cabezal 5 ejes, Soplador herramienta, Palpador electrónico) |

⇒ La `Cota de seguridad = 30` del panel es **la misma** que el `.pgmx` guarda en
`ApproachSecurityPlane` / `RetractSecurityPlane` y que el ISO emite como `Z30.000`. Cierra el
circuito de los tres lados.

⇒ Y el `MachineFunctions` vacío del `.pgmx` **queda respaldado por la captura**, no por la
ausencia: nada seleccionado ⇒ nada emitido.

⇒ 📌 El Galceado **sí** tiene `Invertir` y `Condición`, así que **no hacen falta archivos
nuevos**: es el mismo mecanismo que el fresado ya derivó. Lo que **no** tiene es la elección
`CAD`/`C.N.` — ahora confirmado **por captura**, no sólo por el dato de Fermín.

## 15. Las seis repeticiones de los 42 ISO

Auditando los 42 ISO ignorando la línea `% nombre.pgm`, quedan **36 clases**. Las seis
repeticiones, una por una:

| los que dan el mismo ISO | por qué |
|---|---|
| `fresado_top_E004_contorno_pieza_prof10` ≡ `galceado_top_E004_contorno_pieza_prof10` | ⭐ **el par de control de §1**, reconfirmado |
| ese mismo `galceado` en el `Grupo 1` y en el `Grupo 2` | la referencia, duplicada a propósito en los dos grupos |
| `Grupo 1/..._inicio_frontal_medio` ≡ `Grupo 2/..._inicio_medio` | el mismo caso con dos nombres; «inicio medio» **es** el frontal |
| `uni_SCS_ph5` ≡ `uni_EP_ph5` | ⭐ **§9.2** — la conexión entre huecos no llega al ISO en cerrado |
| `acerc_arco_mr2_bajada` ≡ `acerc_arco_mr4_bajada` | ⚠️ **§11.6** — el `mr4` no quedó aplicado |
| `aleja_lineal_mr2_cota` ≡ `aleja_lineal_mr2_subida` | ⚠️ **§11.6** — la `subida` no quedó aplicada |

⇒ Cuatro de las seis son **intencionales o informativas**; dos son los nombres que el archivo
desmiente.

## 16. Inventario: qué quedó cerrado y qué queda

### Cerrado en esta tanda

| | |
|---|---|
| ⭐⭐⭐ el **multipaso fuerza `CAD`** y los **arcos de esquina aparecen** | §9 — y **corrige** lo que yo había declarado imposible |
| ⭐⭐ el **gatillo de `%DONTCARESPEEDV`** acotado a geometría **abierta** | §9.2 |
| ⭐⭐⭐ la **hélice del ZigZag viene serializada**; el converter la lee | §10.4 |
| las **tres estrategias** y sus **diez campos**, del panel al `.pgmx` | §10.1 |
| ⭐⭐ acercamiento y alejamiento: **`mr × SVR`** con **dos radios**, los **tres modos**, el **arco tangente** y la **asimetría de avances** | §11 |
| el **`Extra`** del pasante = sobrepaso bajo la cara inferior | §12 |
| **`ContourType`** no es parámetro de emisión | §13.1 |
| **`Externo`/`Interno`** es `SideOfFeature`: **cero reglas nuevas** | §13.2 |
| ⭐ el **círculo se parte en dos arcos** de media vuelta | §13.3 |
| ⛔ el Galceado **rechaza la geometría abierta**, con captura | §14 |
| los **testigos** de `Datos avanzados` y `Datos máquina` | §14.1 |

### Lo que sigue abierto

| | |
|---|---|
| ⚖️ **la nomenclatura** | §2. Y la captura del cartel **agrega un dato**: Maestro llama `perfilado` a la operación **también en sus mensajes**. **De Fermín** |
| el **barrido A5** | la rutina permanente — ocho archivos con captura. Es lo único grande que falta |
| `arco + bajada + mr4` y `lineal + subida + mr2` | §11.6 — **predichos**, sin testigo |
| la **elipse** como contorno | el cartel la nombra como válida; no hay archivo |
| el `Cutmode` (`Climb`) y las pasadas **radiales** | §10.1 — están en el `.pgmx` y **no** en esta ventana ⇒ son del **`Vaciado`** |
| el perfil de `Z` **dentro** de una vuelta del ZigZag | §10.4 — no hace falta para el converter (viene serializado), pero **no está entendido** |
