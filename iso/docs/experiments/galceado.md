# Galceado — rama D

**Documento vivo.** El **Galceado**: el escuadrado del contorno. Cuarto mecanizado de la rama D,
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

## 2. ⚠️ La nomenclatura: Maestro usa TRES nombres, en la misma pantalla

Era lo primero que el lote pedía, y la captura de la ventana lo resuelve — el problema **no es
nuestro**:

| dónde | cómo lo llama |
|---|---|
| el **botón** de la cinta `Operaciones` | **`Galceado`** |
| el **tooltip** de ese botón | **«Contorno.** Mando que permite crear un contorno…» |
| el **panel** que se abre, y su sección | **`Perfilado`** / `Datos perfilado` |
| el **`Name`** que Maestro escribe en el `.pgmx` | **`Perfilado`** |
| el **tipo serializado** | **`ContourFeature`** |

Y del lado nuestro, `pgmx/synthesis/milling/contour.py` lleva el docstring
*«Squaring milling contracts»* — **«Squaring» (escuadrado) no es ninguno de los tres**.

⇒ La regla 3 dice *«la nomenclatura manda desde la UI de Maestro»*, pero acá **la UI dice tres
cosas distintas**. ⚖️ **Es una decisión de Fermín.** Mi propuesta, para que la evalúe:

| | |
|---|---|
| la **operación** se llama **`Galceado`** | es el botón que se aprieta y el término del taller |
| el **tipo serializado** queda **`ContourFeature`** | viene del `.pgmx`: intocable (regla 3, excepción legítima) |
| y se **documenta** que Maestro nombra el paso **`Perfilado`** | no es cosmético: **es lo que el converter lee del archivo** |

📌 Y el docstring de `contour.py` hay que corregirlo en cualquiera de los casos: hoy afirma un
nombre que no existe en ningún lado.

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
| ⚖️ **la nomenclatura** | tres nombres de Maestro más el nuestro inventado (§2). **Decisión de Fermín** |
| el `Extra` del pasante | el archivo está, falta medirlo contra el `pasante` |
| `ContourType` con una **línea abierta** | el Galceado es de contorno: ¿la rechaza? El mensaje sería la respuesta |
| `ContourType` con un **círculo** | un cerrado que no es polígono |
| el **offset exterior** y sus arcos de esquina | el fresado los derivó (§30.2); acá está en C.N., así que no se ven. Falta un `CAD` |
| la **estrategia** y el **acercamiento** | las capturas están; falta un testigo de cada uno |
| el **barrido A5** | la rutina permanente, ocho archivos con captura |
