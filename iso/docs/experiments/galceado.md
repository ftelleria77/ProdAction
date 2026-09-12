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

⇒ Y por eso **el pendiente que §8 tenía anotado —«falta un caso en CAD para ver los arcos de
esquina»— es IMPOSIBLE**: la ventana no lo ofrece. Se cae.

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
| `contorno_pieza_pasante_extra1` | el `Extra` del pasante | pendiente de medir |
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

## 8. Lo que queda abierto

| | |
|---|---|
| ⚖️ **la nomenclatura** | el taller dice **`Escuadrado`** y Maestro dice tres cosas (§2). La decisión se reduce a: la spec por la **función** o por el **tipo del archivo**. **De Fermín** |
| el `Extra` del pasante | el archivo está, falta medirlo contra el `pasante` |
| `ContourType` con una **línea abierta** | el Galceado es de contorno: ¿la rechaza? El mensaje sería la respuesta |
| `ContourType` con un **círculo** | un cerrado que no es polígono |
| ~~el **offset exterior** y sus arcos de esquina~~ | ⛔ **IMPOSIBLE**: la ventana **no deja elegir CAD** (§3), así que el Galceado siempre emite la nominal con `G41`/`G42` y los arcos nunca aparecen |
| ❓ **el Galceado con multipaso** | en el fresado el multipaso **fuerza CAD**, y acá CAD **no se puede elegir**: las dos no pueden valer a la vez. **Un archivo lo decide** (§3) — es lo que más rinde de lo que queda |
| la **estrategia** y el **acercamiento** | las capturas están; falta un testigo de cada uno |
| el **barrido A5** | la rutina permanente, ocho archivos con captura |
