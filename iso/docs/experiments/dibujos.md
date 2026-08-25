# Dibujos — las geometrías del `.pgmx` y cómo las escribe Maestro

**Época nueva, 2026-08-16.** Fixtures manuales de Fermín sobre `R_PV_manual_base`, en
`Programas Manuales\Reinvestigación\Dibujos\`. Etapa 1: qué escribe Maestro en el `.pgmx`.

> **Criterio de la rama (Fermín, 2026-08-16): el `.pgmx` que produce nuestro sintetizador
> tiene que ser FUNCIONALMENTE idéntico al de Maestro, no byte-idéntico.** El
> byte-idéntico sigue siendo obligatorio donde importa —el `.iso`, que es el producto del
> converter (regla 4)—; el `.pgmx` es una herramienta para fabricar fixtures, y una
> diferencia que no cambia la pieza no es un defecto. Este documento marca cada hallazgo
> con esa vara.

## 1. Un dibujo es geometría SIN mecanizado

Dibujar una línea agrega **un solo nodo** en `<Geometries>` y **`<Features/>` sigue
vacío**. La geometría queda disponible para que después un mecanizado la use, pero por sí
sola no produce nada.

## 2. La UI

Pestaña **Dibujar**, grupo **Geometrías**: `Línea` · `Arco` · `Círculo` · `Elipse` ·
`Polilínea` · `Rectángulo` · `Punto` · `Texto`. (Los otros grupos son **Modificar** —
Conexión, Cortar, Unir, Offset, Mover, Gira, Escala, Reflejar, Oponer, Invertir, Punto
inicial, Medidas—, **Planos inclinados** y **Osnap**.)

Al elegir `Línea` aparece una barra contextual con el **método**, y con `2 Puntos` Maestro
pide primero el **Punto inicial** y después el **Punto final**. Cada punto se ingresa
gráficamente o **por teclado**, en cajitas `X` e `Y` flotantes. La barra ofrece además
`Secuencia Simple` y `Coordenadas Cartesianas`, que no se barrieron todavía.

Una línea ya creada se edita en el panel **«Línea» → «Datos geométricos»**:

| control | nota |
|---|---|
| checkbox **Coordenadas absolutas** | ⚠️ **NO es `<a:IsAbsolute>`, y no se guarda en el archivo** — ver §13.5. Es un modo de visualización |
| `Xi` `Yi` `Zi` · `Xf` `Yf` `Zf` | `Zi`/`Zf` deshabilitados sobre un plano 2D |
| **`Longitud`** y **`Ángulo`** | campos propios, editables — la recta se puede definir por ahí |

Los valores se muestran con **tres decimales** (`344,819`, `29,539`), igual que la grilla
de Parámetros: es presentación, el XML guarda mucha más precisión.

## 3. El nodo

```xml
<a:GeomGeometry i:type="a:GeomTrimmedCurve">
  <Key xmlns="…Utility">
    <ID>1927</ID>
    <ObjectType>ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve</ObjectType>
  </Key>
  <Name xmlns="…Utility"/>
  <a:IsAbsolute>false</a:IsAbsolute>
  <a:PlaneID xmlns:b="…Utility">
    <b:ID>1918</b:ID>
    <b:ObjectType>ScmGroup.XCam.MachiningDataModel.ProjectModule.Plane</b:ObjectType>
  </a:PlaneID>
  <a:_serializationGeometryDescription>…</a:_serializationGeometryDescription>
</a:GeomGeometry>
```

- El `ID` sale del mismo contador que los parámetros: el primer libre del archivo.
- `Name` va **vacío** (la línea no se nombra desde la UI).
- `PlaneID` apunta a un `ProjectModule.Plane`, uno de los seis de la pieza.
- Los nombres `GeomTrimmedCurve` / `GeomGeometry` son del vocabulario de **OpenCascade**,
  el motor geométrico. No son de Maestro ni nuestros.

## 4. `_serializationGeometryDescription`, decodificado

Dos renglones de números separados por espacios, **con un espacio final en el segundo** y
salto de línea al final:

```
8   0   424.26406871192853              tipo · parámetro inicial · parámetro final
1   50 50 0   0.7071… 0.7071… 0         curva base · punto de partida · dirección
```

| campo | qué es |
|---|---|
| `8` | código de la curva recortada (`GeomTrimmedCurve`) |
| `0` y `424.264…` | el intervalo `[t inicial, t final]` |
| `1` | código de la curva base: **recta** |
| `50 50 0` | punto de partida |
| `0.7071… 0.7071… 0` | **dirección unitaria** (módulo verificado = 1.0) |

Como la dirección es unitaria, **`t final` es la longitud** y el punto final se reconstruye
con `P + t·D` — verificado: da exactamente `(350, 220)` en la línea 2.

Los números se escriben con **17 dígitos significativos** (`.17g`, el G17 de .NET), no con
el formato compacto del resto del `.pgmx`. El sintetizador ya lo hace bien: tiene una
función aparte, `_format_maestro_number`, y **no** pasa por `_compact_number` — que
truncaría `424.26406871192853` a `424.264069` y destruiría la geometría.

## 5. La dirección: Maestro tiene DOS caminos, y el nuestro es uno de ellos

Derivado de las dos líneas, y explica ambas con un solo mecanismo:

| cómo se calcula | línea 1 (45°) | línea 2 (29,539°) |
|---|---|---|
| `dx / double(L)` — lo que hace el sintetizador | ❌ `…746` | ✅ |
| `dx / L` redondeando **una sola vez** | ✅ `…757` | ✅ |

### ⚠️ CORREGIDO el 2026-08-17: no hay tal defecto. Hay DOS caminos

La lectura de arriba —«Maestro guarda el double más cercano al valor real de `d/|d|`, y
nuestro `dx/double(L)` está 1 ULP corrido»— **quedó refutada** por el fixture de las cuatro
fórmulas. El cuadro real, sobre la **misma** línea a 45°:

| archivo | cómo se definió | dirección | punto final reconstruido |
|---|---|---|---|
| `linea.pgmx` | **dibujada** con `2 Puntos` | `…757` | `350.00000000000006` |
| `linea(4formulas).pgmx` | con las 4 coordenadas atadas a fórmulas | **`…746`** | **`350.0` exacto** |
| `linea_2.pgmx` | **editada** en el panel | `dx/double(L)` | exacto |

⇒ **El `…746` no es un error: es el valor que hace exactos los extremos**, y Maestro lo
elige él mismo cuando hay restricciones que cumplir. Los dos caminos son suyos:

- **al dibujar**, usa la normalización de una sola redondeada (`…757`) y el punto final
  queda con ~5·10⁻¹⁴ de error, que a nadie le importa porque nada lo restringe;
- **al editar o al resolver fórmulas**, usa `d/double(L)` — que es exactamente lo que hace
  nuestro sintetizador.

⇒ **El sintetizador NO tiene defecto acá.** Coincide con el camino que Maestro usa cuando
el resultado tiene que ser exacto. Queda retirado el «1 ULP a corregir», y con él la lista
de los siete lugares con patrón `d / length`: no hay nada que arreglar en ellos por este
motivo.

⚠️ **Dos errores míos en esta sección, para que no se repitan**:
1. Con la línea 1 sola se concluyó que Maestro usaba `cos`/`sin` del ángulo, porque
   `cos(π/4)` da el valor observado. **Falso**: a 45° media docena de fórmulas coinciden
   por simetría.
2. Después se escribió que «se descartó que dependiera de cómo se creó la línea, porque
   las dos se hicieron igual». **También falso, y por mala lectura**: `linea_2` salió de
   **editar** la primera en el panel, no de dibujar una nueva — Fermín lo había dicho desde
   el principio. Dibujar y editar **sí** son caminos distintos.

## 6. Los fixtures

En `S:\Maestro\Projects\ProdAction\Programas Manuales\Reinvestigación\Dibujos\`:

| archivo | línea | ángulo | qué derivó |
|---|---|---|---|
| `R_PV_manual_base_linea.pgmx` | (50,50)→(350,350) | 45° | la forma del nodo y del `_serialization…` |
| `R_PV_manual_base_linea_2.pgmx` | (50,50)→(350,220) | 29,539° | que la regla es `d/|d|`; **el sintetizador lo reproduce byte a byte** |
| `R_PV_manual_base_linea_3.pgmx` | (50,50)→(220,350) | 60,461° | la 2 con X e Y intercambiadas: mismos cosenos directores dados vuelta |

Las tres con `Línea → 2 Puntos`, coordenadas por teclado.

Y tres estados más de `linea_2`, que derivaron la regla de compensación de §7:

| archivo | qué es |
|---|---|
| `R_PV_manual_base_linea_2(reguardado).pgmx` | abierta y guardada sin tocar nada |
| `R_PV_manual_base_linea_2(reguardado con formula).pgmx` | con `EndX = dx1 - 50` |
| `R_PV_manual_base_linea_Distancia_130.pgmx` | ⚠️ **sobrescrito** el 17:32 al retipear `Xi`; el estado de las 16:34 sólo sobrevive citado en §7 |
| `R_PV_manual_base_linea(4formulas).pgmx` | las **cuatro** coordenadas atadas a fórmulas — retiró el falso defecto de §5 |
| `R_PV_manual_base_linea(4formulas)_500_400.pgmx` | pieza 500×400 ⇒ línea (50,50)→(450,350), triángulo **3-4-5** con longitud exacta 500 |
| `R_PV_manual_base_linea(4formulas)_400_500.pgmx` | pieza 400×500 ⇒ el simétrico, (50,50)→(350,450) |

Los dos últimos son los que **refutaron la regla de compensación**: longitud exactamente
representable, cuatro restricciones puestas, y aun así `5.7·10⁻¹⁴` de error en el extremo.

⚠️ **Los tres primeros no son equivalentes entre sí**: `linea.pgmx` se **dibujó** con la
herramienta, y `linea_2` / `linea_3` salieron de **editarla** en el panel. Eso cambia cómo
Maestro calcula la dirección (§5) y no es un detalle de procedimiento.

## 7. Geometría PARAMÉTRICA: una coordenada atada a un parámetro (2026-08-17)

Fixtures de Fermín: sobre `R_PV_manual_base_linea.pgmx` agregó el parámetro
`Distancia` y puso el **`Yf`** del punto final como la expresión **`dx1 - Distancia`**.

| archivo | `Distancia` | punto final | longitud |
|---|---|---|---|
| `R_PV_manual_base_linea_Distancia.pgmx` | 50 | (350, 350) | el parámetro **sin usar** todavía |
| `R_PV_manual_base_linea_Distancia_50.pgmx` | 50 | (350, **350**) | 424,264 |
| `R_PV_manual_base_linea_Distancia_130.pgmx` | 130 | (350, **270**) | 372,022 |

### `Parametrics.Expression` es el mecanismo general, no algo de la pieza

```
id 1924   WorkPiece#1917.Length        = 'dx1'
id 1930   GeomTrimmedCurve#1927.EndY   = 'dx1 - Distancia'
```

Misma forma exacta: ata **(objeto, propiedad) → fórmula de texto**. Sirve para cualquier
propiedad de cualquier objeto. Y da el mapeo del panel: el campo **`Yf`** de la UI se
llama **`EndY`** adentro.

### ⭐ La geometría se guarda RESUELTA; la fórmula vive aparte

El `_serializationGeometryDescription` trae el punto final **ya calculado** —reconstruido
da exactamente `400 − Distancia`—, y la expresión está en `<Expressions>`, en otro nodo.
El `.pgmx` guarda **las dos cosas, en dos lugares distintos**.

⇒ **El converter puede leer el número e ignorar la fórmula. No necesita evaluar
expresiones nunca.** Es la respuesta a la pregunta que A7 tenía retirada.

⇒ Y cambiar el valor del parámetro **recalcula la geometría**: dirección y longitud
nuevas. Un parámetro **usado** sí mueve la traza, a diferencia de los sin usar (§8).

### ⚠️ Maestro introduce ruido de punto flotante al recalcular

```
linea.pgmx              1 50 50 0 …                ← exacto
linea_Distancia_50      1 49.999999999999659 …     ← el mismo punto, que nadie editó
```

El **punto de partida**, que el usuario nunca tocó, deja de ser `50`. El ruido es de
**~3·10⁻¹³ mm**, la longitud también se mueve en el último dígito, y **no es un valor
fijo**: los tres archivos traen ruidos distintos (`…702`, `…659`, `…702`), o sea se
regenera en cada recálculo.

⭐ **Lo confirma la propia UI de Maestro**: al posar el cursor sobre el campo `Xi`, el
tooltip dice **`Type: Double | Value: 49,9999999999997`** mientras el campo muestra
`50,000`. Verificado: es **el mismo double** que trae el XML (`49.999999999999702`) — el
tooltip lo escribe con 15 dígitos (el `ToString()` por defecto de .NET) y el XML con 17.

⇒ **El ruido nace en Maestro**, no en cómo leemos el archivo. No hay forma de pedirle un
`.pgmx` «limpio».

⭐ **Lo agrega la ESCRITURA** (derivado el 2026-08-17, tercera pasada). Fermín retipeó `50`
hasta que el tooltip mostró **`Value: 50` exacto** —o sea el modelo estaba limpio— y
guardó: el archivo salió con **`49.99999999999996`**.

⚠️ Corrige lo que este documento dijo primero —«el ruido nace en el modelo, no en la
serialización»—, deducido de que tooltip y XML coincidían. Coincidían porque **ese modelo
ya venía sucio de una lectura previa**. Con el modelo limpio, la escritura ensucia igual.
La cadena es: **se genera al escribir y se propaga al leer.**

Y no es parejo: al retipear `Xi` su error bajó diez veces (`3·10⁻¹³` → `4·10⁻¹⁴`) pero el
de **`Yi` subió** (`3·10⁻¹³` → `6·10⁻¹³`), y los dos dejaron de ser iguales entre sí.
Tocar un campo movió el otro.

⭐⭐ **Y no entra sólo al recalcular: entra por el TECLADO.** Fermín volvió a escribir `50`
en ese mismo campo `Xi` y el tooltip pasó a **`49,9999999999999`** — otro valor, otra vez
distinto de `50`, y **distinto del anterior** (`…97` → `…99`). Escribir el número exacto no
produce el número exacto, y el resultado **no depende sólo de lo que se tipea sino del
estado previo**.

Como el campo muestra `50,000` redondeado a tres decimales, **el ruido no se puede
corregir a mano**: quien lo intente escribe `50` y obtiene otro valor, sin verlo.

### 🔍 Parecía haber compensación — y NO la hay (leer hasta el final)

**Derivado el 2026-08-17** con tres estados de `linea_2` — (50,50)→(350,220) —,
reconstruyendo `P + t·D` desde la serialización, con todo el ruido adentro:

| estado | punto de partida | punto final reconstruido |
|---|---|---|
| original | **exacto** `50 50` | **exacto** `(350, 220)` |
| reguardado, **sin** fórmula | **exacto** `50 50` | `349.99999999999966`, `219.99999999999986` |
| reguardado, **con** `EndX = dx1 - 50` | `50.0000000000003`, `50.0000000000002` | **exacto** `(350, 220)` |

Sobre estos tres casos parecía haber una regla —«Maestro conserva exacto el extremo
restringido y manda el error al otro»—, y encajaba hacia atrás con `_Distancia_130`, donde
la fórmula estaba en `EndY` y el punto final daba `(350, 270)` exacto en las dos versiones
del archivo.

### ⛔ Esa regla NO se sostiene: la refutó el triángulo 3-4-5

`R_PV_manual_base_linea(4formulas)_500_400.pgmx` — pieza 500×400, las **cuatro** fórmulas
puestas, línea (50,50)→(450,350), o sea `dx=400`, `dy=300` y longitud **exactamente 500**:

```
MAESTRO    t = 500.00000000000006   D = (0.79999999999999993, 0.60000000000000009)
           P + t·D = (450.0, 350.00000000000006)      ← error 5.7·10⁻¹⁴
NOSOTROS   t = 500                  D = (0.80000000000000004, 0.59999999999999998)
           P + t·D = (450.0, 350.0)                   ← exacto
```

**El extremo restringido NO salió exacto**, con las cuatro restricciones puestas. Y con los
valores obvios (`500`, `0.8`, `0.6`) el resultado *sería* exacto: Maestro eligió peores.

⇒ **No hay compensación deliberada.** Maestro arrastra error en su cálculo y los casos que
dieron exacto —el de 45° con cuatro fórmulas, `_Distancia_130`— fueron **suerte del
redondeo**, no una garantía. La lectura que se sostiene es la simple: *Maestro calcula con
un error de ~10⁻¹³ y a veces se cancela.*

⇒ Y **delata que el ruido viene de antes**: `√(400² + 300²)` da **500 exacto** en doble
precisión, y los cuadrados también. `500.00000000000006` **no puede salir de ahí** ⇒ los
`dx`/`dy` internos de Maestro no son 400 y 300, aunque el punto de partida se serialice
como `50 50` limpio.

⇒ **Nuestro sintetizador es más exacto que Maestro en este caso.** Otro motivo para no
tocar nada por «parecernos» a él.

📌 **Lección de método, dos veces en el mismo día**: se derivaron dos reglas de tres o
cuatro observaciones —primero el método de cálculo de la dirección, después la
compensación— y **las dos cayeron con el fixture siguiente**. Con números de punto flotante
en juego, tres casos no alcanzan: hay que buscar el caso que *debería* romperla.

⚠️ **Cuidado al mirar**: el error se muda de lugar. Ver un extremo limpio no significa que
el archivo esté limpio — hay que reconstruir **los dos**. El reguardado sin fórmula parece
intacto si sólo se mira el punto de partida.

### Con los cuatro extremos restringidos: exacto a 45°, con error en 3-4-5

`R_PV_manual_base_linea(4formulas).pgmx` ata las cuatro coordenadas:

```
id 1929   GeomTrimmedCurve#1927.StartX = 'Distancia'        → 50
id 1930   GeomTrimmedCurve#1927.StartY = 'Distancia'        → 50
id 1931   GeomTrimmedCurve#1927.EndX   = 'dx1 - Distancia'  → 350
id 1932   GeomTrimmedCurve#1927.EndY   = 'dy1 - Distancia'  → 350
```

```
8 0 424.26406871192853
1 50 50 0 0.70710678118654746 0.70710678118654746 0
```

**Punto de partida exacto Y punto final exacto** — `(50,50)` y `(350.0, 350.0)`, error
cero en los cuatro números.

⚠️ Pero **eso NO se repite con otros ángulos**: los dos fixtures 3-4-5 de más abajo, con
las mismas cuatro fórmulas, dejan `5.7·10⁻¹⁴` de error en el extremo. Este caso salió
redondo por el redondeo, no por una garantía.

Lo que sí queda de acá:

- ⇒ el **mapeo completo del panel**: `Xi`→**`StartX`**, `Yi`→**`StartY`**,
  `Xf`→**`EndX`**, `Yf`→**`EndY`**;
- ⇒ que una fórmula sobre el punto de partida **sí** se puede poner, con lo cual la
  predicción que este documento había dejado anotada quedó respondida por el costado: se
  pueden restringir los cuatro extremos a la vez.

⇒ Y **el campo de la UI lo esconde**: muestra `50,000` redondeado a tres decimales. El
tooltip es la única forma de ver el valor real sin abrir el archivo — sirve como
herramienta de diagnóstico cuando una coordenada no cierra.

⇒ **El byte-idéntico en el `.pgmx` no es caro: es inalcanzable.** Dos archivos que
representan la misma línea difieren según qué se editó, y eso no depende de nosotros.
Confirma la decisión de método del 2026-08-16 —funcionalmente idéntico— por una vía que
no se había previsto.

⇒ **Aviso para el converter**: un `.pgmx` real puede traer `49.999999999999702` donde el
usuario escribió `50`. No se pueden asumir números redondos ni comparar por igualdad.
Calibración con evidencia: las tolerancias del código son `1e-9` (24 usos), `1e-6` (9),
`1e-12` (3) y **`1e-15` (6)**. El ruido observado es **300 veces mayor que `1e-15`** —
esos seis usos deciden «¿esto es cero?» en `leads.py` y en `_format_maestro_number`.
**Pendiente de verificar** si reciben valores leídos de un `.pgmx` o sólo calculados por
el sintetizador; en el segundo caso el ruido no llega y no hay nada que corregir.

### ⚠️ Límite de estos fixtures

`R_PV_manual_base_linea_Distancia.pgmx` **no es el estado del paso 3**: Fermín lo re-guardó
al final de la sesión para sacar la captura (timestamp 16:38, contra 16:34 de los otros).
Por eso trae el ruido **sin** tener la `Expression` del `EndY`. ⇒ **Con estos tres archivos
no se puede aislar qué acción dispara el recálculo.** Si algún día importa, lo aíslan dos
fixtures triviales: abrir `linea.pgmx` y guardar sin tocar nada, y abrir y agregar sólo un
parámetro. Hoy no bloquea nada: para el converter lo que importa es que el ruido **existe**
y su **magnitud**, y eso ya está derivado.

## 8. ✅ Una geometría sin mecanizado NO deja rastro en el ISO (2026-08-17)

Las tres líneas se postprocesaron en el CNC. Los tres ISO son **idénticos al del programa
vacío** salvo la línea 1, que lleva el nombre del archivo — 43 líneas, mismo contenido.
Control cruzado: la diferencia de bytes de cada uno es **exactamente** el largo de más del
nombre, sin un byte sobrante.

⇒ **El converter puede ignorar las geometrías que ningún mecanizado usa.** Una línea
dibujada es material de dibujo, no de programa: sólo llega al ISO a través del mecanizado
que la tome. Coincide con lo de §1 —dibujar no crea `Feature`— y con el resultado gemelo
de los parámetros sin uso (`parametros.md`, §8).

⚠️ Esto **no** dice qué pasa cuando un mecanizado sí la usa: ahí la línea se convierte en
traza y es toda la rama D.

## 9. El sintetizador frente a las ocho geometrías — auditoría (2026-08-17)

Pregunta de Fermín: *¿nuestro sintetizador puede generar todos los tipos de dibujos?* La
respuesta corta es **no**, y hay **dos huecos distintos** que conviene no mezclar.

### 9.1 · No sabe hacer «dibujos» — ninguno

Un dibujo es geometría con `<Features/>` **vacío** (§1). La API pública
`build_synthesis_request` (`pgmx/synthesis/common/program.py`) acepta sólo esto:

```
lines · channels · polylines · arcs · circles · contours · pockets
drills · drill_patterns · ordered_machinings · xn · workplans
parametric_variables · pieces
```

**Todos son mecanizados**: viven en `synthesis/milling/` y `synthesis/drilling/`, y cada uno
produce un `Feature`. **No hay parámetro `geometries=` ni `drawings=`.**

⇒ El sintetizador emite geometría **sólo como subproducto de una operación**; no puede
dejarla suelta. De las ocho geometrías de la pestaña Dibujar sabe autorar **cero como
dibujo**.

### 9.2 · De los tipos de geometría, cubre cinco de ocho

| UI «Dibujar» | Tipo / primitiva | Código de curva | Forma que emite |
|---|---|---|---|
| Línea | `GeomTrimmedCurve` + `Line` | `1` | `8 t0 t1` ⏎ `1 P D ` |
| Arco | `GeomTrimmedCurve` + `Arc` | `2` | `8 a0 a1` ⏎ `2 C N̂ Û V̂ R ` |
| Círculo | `GeomCircle` | `2` | `2 C N̂ Û V̂ R` — **sin** el envoltorio `8`, porque no está recortado |
| Polilínea | `GeomCompositeCurve` | (por miembro) | una serialización por miembro |
| Punto | `GeomCartesianPoint` | — | sin serialización de curva |
| **Rectángulo** | — | — | no existe como tipo propio; componible con cuatro líneas, **sin fixture que lo confirme** |
| **Elipse** | — | — | **no existe en el código** |
| **Texto** | — | — | **no existe en el código** |

Lo que sí está bien: `_primitive_to_serialization` levanta
`ValueError("Tipo de primitiva no soportado: …")`. **Fail-loud, no aproxima en silencio** —
regla 4 en código.

### 9.3 · ⚠️ La evidencia detrás de cada una NO es equivalente

Esto importa más que el conteo:

| geometría | con qué está respaldada |
|---|---|
| **Línea** | ✅ **fixtures manuales de Maestro de la época nueva** (§3–§7); el sintetizador reproduce `linea_2` byte a byte |
| **Arco** | ⚠️ **roundtrip contra nosotros mismos** (`tests/test_pgmx_arc_authoring.py`: sintetiza → lee → compara). Su propio docstring dice que «la validación final es **N040** postprocesado en Maestro» — **serie N, época congelada, declarada no-fuente** |
| **Círculo · Polilínea** | ⚠️ ídem: se derivaron sirviendo mecanizados de la época anterior, no desde la pestaña Dibujar |
| **Punto** | ⚠️ sin test propio |

Verificado: **ningún test compara geometría sintetizada contra un `.pgmx` hecho a mano en
Maestro**, y en el repo **no hay ningún fixture de dibujo**. La única geometría verificada
así es la línea, y esa verificación vive en este documento, **no en la suite**.

⇒ Es el punto ciego de la **regla 5** en su forma más pura: el arco y el círculo **se validan
contra nuestra propia autoría**, y su única ancla externa es de una época que esta
reinvestigación declaró no-fuente.

### 9.4 · Dos asimetrías que sólo un fixture puede resolver

> ⏭️ **La primera quedó resuelta el 2026-08-18 por el fixture del arco: ver §10.**

1. **El espacio final.** El círculo cierra con `{radio}\n` y el arco con `{radio} \n`. En la
   línea el espacio final está DERIVADO (§4); en las otras dos no lo verificó nadie.
2. **La base del arco.** `_build_maestro_arc_serialization` fija la orientación en
   `0 0 N̂z 1 0 0 0 N̂z 0` —una base constante—, mientras `_build_oriented_maestro_arc_serialization`
   la recibe como parámetro. Cuál usa Maestro **al dibujar** un arco no está derivado.

### 9.5 · Un pendiente de §7, cerrado leyendo código

§7 dejó anotado verificar si los seis usos de tolerancia `1e-15` reciben valores **leídos**
de un `.pgmx` o sólo calculados. Uno de ellos está en `_format_maestro_number`:

```python
if math.isclose(number, 0.0, abs_tol=1e-15):
    return "0"
```

`pgmx/adapters.py` construye `GeometryPrimitiveSpec` **desde un snapshot leído** y arma con
ellos un request de síntesis, que termina en `_primitive_to_serialization`. ⇒ **Sí llegan
valores leídos de un `.pgmx`.**

Consecuencia, con el ruido medido en §7 (~3·10⁻¹³): una coordenada que Maestro dejó en
`3·10⁻¹³` en vez de `0` **no** se colapsa a `0`, porque la tolerancia es ~300 veces más
chica que el ruido. Con la vara de «funcionalmente idéntico» eso **no es un defecto**
(3·10⁻¹³ mm no mueve nada), pero explica por qué un archivo releído y re-sintetizado no da
byte-idéntico — y refuerza §7: el byte-idéntico en el `.pgmx` no es caro, es inalcanzable.

### 9.6 · Qué conviene corregir, y qué no

- **Verificar arco, círculo, polilínea y punto contra fixtures manuales de la época nueva.**
  Es el hueco real: hoy dependen de la época congelada.
- **Elipse y texto**: no existen. Sólo hacen falta si algún `.pgmx` de entrada los trae —y
  eso es del lado de la **lectura**, no de la síntesis.
- **Dibujos sueltos** (geometría sin `Feature`): §8 derivó que **no llegan al ISO**, así que
  el converter puede ignorarlos. Agregarlos al sintetizador sólo serviría para fabricar
  fixtures que testeen que no pasa nada.
- **Rectángulo**: antes de componerlo con cuatro líneas hay que ver si Maestro lo guarda así
  o como otra cosa. Es una pregunta de fixture, no de código.

## 10. El ARCO: primer fixture de la época nueva, y dos deltas contra el sintetizador (2026-08-18)

> ⏭️ **Superado por §12** (2026-08-19). Esta sección se derivó con **un solo arco**. El lote
> «Rama G» trajo 20 y resolvió las dos preguntas que quedaban abiertas acá: el espacio final
> es **por código de curva** (§12.1) y la base fija del sintetizador **no es un defecto**
> (§12.3). Queda como registro de cómo se llegó.

Fixtures de Fermín en `…\Reinvestigación\Dibujos\`:

| archivo | qué es |
|---|---|
| `R_PV_manual_param_radio_antes.pgmx` | el parámetro `radio` creado **antes** de dibujar; `<Geometries>` vacío |
| `R_PV_manual_param_radio_antes_Arco.pgmx` | el arco dibujado sobre ese programa |

`<Features/>` sigue vacío en los dos, como manda §1: dibujar no crea mecanizado.

### Lo que escribe Maestro

```
8 3.1415926535897931 4.7123889803846897
2 300 300 0 0 -0 1 1 0 0 -0 1 0 200
```

Decodificado con la gramática de §4:

| campo | valor | qué es |
|---|---|---|
| `8` · `π` · `3π/2` | | curva recortada, intervalo angular — un cuarto de arco de 180° a 270° |
| `2` | | código de la curva base: **círculo** |
| `300 300 0` | | centro |
| `0 -0 1` | | normal **N̂** |
| `1 0 0` | | **Û** |
| `-0 1 0` | | **V̂** |
| `200` | | radio |

⇒ El arco usa **el mismo envoltorio `8` que la línea** y una curva base de código **`2`**,
con centro, base ortonormal orientada y radio. La forma que el sintetizador ya emitía es la
correcta; las diferencias son dos, y finas.

### ⚠️ Delta 1 — el espacio final: la línea SÍ, el arco NO

Comparado byte a byte contra los fixtures:

```
LINEA  maestro: '8 0 424.26406871192853\n1 50 50 0 0.70710678118654757 0.70710678118654757 0 \n'
ARCO   maestro: '8 3.1415926535897931 4.7123889803846897\n2 300 300 0 0 -0 1 1 0 0 -0 1 0 200\n'
                                                                                        ↑ sin espacio
```

**El sintetizador le pone espacio final al arco** (`…200 \n`), porque aplica la regla que
derivó de la línea. Es el único byte que separa nuestra salida de la de Maestro cuando se le
pasa la base correcta.

Y nuestro código es **inconsistente consigo mismo**: `_build_circle_geometry_serialization`
cierra **sin** espacio y los dos builders de arco **con** espacio.

### ⚠️ Delta 2 — el cero negativo

Maestro escribe `-0` en **N̂y** y en **V̂x**. `_build_oriented_maestro_arc_serialization` lo
reproduce si se le pasa `-0.0` (su `_format_maestro_orientation_number` ya distingue el signo
del cero). Pero `_build_maestro_arc_serialization` —el de base FIJA, el que usa el vaciado—
tiene la base hardcodeada como `0 0 N̂z 1 0 0 0 N̂z 0` y emite `0` donde Maestro emite `-0`.

Numéricamente `-0.0 == 0.0`, así que con la vara del encabezado —funcionalmente idéntico— **no es un defecto funcional**. Lo que
delata es otra cosa, y esa sí importa: **la base fija es una conjetura**. Maestro no la
escribe así; la deriva, y el `-0` es la firma de ese cálculo.

### ⛔ Por qué NO se corrige el código todavía

**Es UNA observación.** §5 registra que este documento derivó dos reglas de tres o cuatro
casos y **las dos cayeron con el fixture siguiente**. El espacio final del arco tiene hoy
`n=1`, y encima la línea —la única otra geometría medida— se comporta al revés.

Antes de tocar la serialización hay que saber si la regla es **por tipo de curva**, y para
eso hacen falta los fixtures de §11. Cambiarla ahora movería los bytes de **todos** los arcos
que emite el sintetizador —los de `leads.py` (×4) y los ocho del vaciado en `pocket.py`— sobre
una sola medición.

## 11. Plan de fixtures para cerrar el barrido de Dibujar

> ✅ **EJECUTADO el 2026-08-19**: Fermín armó el lote «Rama G» con 88 fixtures y cubrió los
> puntos 1 a 5 y el 8. Resultados en §12. Quedan sin fixture el **texto** (punto 7) y la
> **elipse** quedó cubierta por el lote aunque estaba listada como opcional (punto 6).

Uno por archivo, sobre `R_PV_manual_base`, en `…\Reinvestigación\Dibujos\`. Lo que decide
cada uno:

| # | fixture | qué decide |
|---|---|---|
| 1 | **segundo arco**, otro centro/radio/ángulos | si el «sin espacio final» es del tipo arco o de ese archivo. **Es el que desbloquea la corrección** |
| 2 | **círculo** | su código de curva y si lleva o no envoltorio `8`; confirma o refuta nuestro `GeomCircle` |
| 3 | **polilínea** de 3 segmentos | cómo se arma el `GeomCompositeCurve`: un miembro por segmento, y qué llevan `_serializingMembers` y `_serializingKeys` |
| 4 | **rectángulo** | si Maestro lo guarda como composite de cuatro líneas o como otra cosa |
| 5 | **punto** | la forma del `GeomCartesianPoint` |
| 6 | **elipse** | el código de curva base; hoy el sintetizador no la tiene |
| 7 | **texto** | qué guarda; hoy el sintetizador no lo tiene |
| 8 | **arco por otro método** de la barra contextual | si el método de dibujo cambia el nodo, como pasó con dibujar-vs-editar en la línea (§5) |

Con 1 a 5 alcanza para corregir el sintetizador. 6 y 7 son para saber si hay que rechazarlas
fail-loud al **leer** un `.pgmx` ajeno — no para emitirlas.

## 12. El lote «Rama G»: 88 fixtures, ocho familias (2026-08-19)

Fermín armó `…\Reinvestigación\Dibujos\Rama G\` con **88 `.pgmx` manuales**, uno por dibujo,
todos sobre `R_PV_manual_base`. `<Features/>` está vacío en los 88: son dibujos de verdad.

| familia | n | tipo del nodo | serializaciones |
|---|---|---|---|
| línea | 10 | `GeomTrimmedCurve` | 1 |
| arco | 20 | `GeomTrimmedCurve` | 1 |
| círculo | 13 | `GeomCircle` | 1 |
| **elipse** | 9 | **`GeomEllipse`** | 1 |
| polilínea | 18 | `GeomCompositeCurve` | 0 (usa miembros) |
| polígono | 6 | `GeomCompositeCurve` | 0 |
| rectángulo | 8 | `GeomCompositeCurve` | 0 |
| punto | 4 | `GeomCartesianPoint` | 0 (usa `_x/_y/_z`) |

### 12.1 · ⭐ El espacio final es POR CÓDIGO DE CURVA

Era el delta que §10 dejó sin decidir por tener `n=1`. Con el lote queda derivado:

| código de curva | qué es | espacio final antes del `\n` | casos |
|---|---|---|---|
| `1` | recta | **SÍ** | **130** |
| `2` | círculo / arco | **NO** | **44** |
| `3` | elipse | **NO** | **9** |

Vale **dentro y fuera** de los compuestos: un miembro recto de una polilínea también lo lleva.

⇒ **La regla no es «la línea sí y el arco no»: es del código de la curva base.** Y confirma
que al arco del sintetizador le sobra ese byte, mientras que su círculo estaba bien.

### 12.2 · La forma de cada familia

```
línea    8 t0 t1                    ⏎  1 Px Py Pz  Dx Dy Dz ␣
arco     8 ang0 ang1                ⏎  2 Cx Cy Cz  N̂  Û  V̂  R
círculo  2 Cx Cy Cz  N̂  Û  V̂  R                    ← sin envoltorio 8: no está recortado
elipse   3 Cx Cy Cz  N̂  Û  V̂  R_mayor R_menor      ← ídem, y DOS radios
punto    (sin serialización)  <a:_x> <a:_y> <a:_z>
```

El compuesto no tiene serialización propia: lleva `_serializingKeys` —un `<b:unsignedInt>`
por miembro, cada uno con **ID propio**— y `_serializingMembers` —un `<b:string>` por
miembro, cada uno con la serialización completa de su curva—.

### 12.3 · El arco: sentido derivado, y la base que no importa

Fermín describió los primeros ocho (centro, sentido y ángulos). Con eso:

⇒ **`N̂z = +1` para antihorario y `−1` para horario. 8 de 8.**

Y sobre los 20: **el barrido angular es siempre positivo y ≤ 2π**. La base no es arbitraria,
está al servicio de que el arco se recorra en sentido creciente. `Û` y `V̂` son siempre
ejes-alineados.

Reconstruí los extremos de cada arco desde el archivo, se los pasé a nuestro builder y comparé:

| | |
|---|---|
| idéntico salvo el espacio final | 1 |
| difiere **sólo en el signo del cero** (`-0` contra `0`) | 9 |
| difiere en **1 ULP** en `t0` | 1 |
| usa una **base espejada** | 9 |
| **describen la misma curva** (14 puntos muestreados, tol. 1e-6) | **20 / 20** |

> ⚠️ **Corrección de §10.** Ahí se dijo que la base fija del sintetizador era «una conjetura»
> y que coincidía en 11 de 20. Es más preciso decir que **es una elección canónica válida**:
> Maestro a veces usa la espejada —y con los ocho descriptos no se pudo derivar qué la
> decide—, pero las dos parametrizan **la misma curva, con el mismo sentido y los mismos
> extremos**. Verificado a mano en `arco_04`: Maestro usa `Û=(−1,0,0)` con `t ∈ [π, 2.5π]`,
> nosotros `Û=(1,0,0)` con `t ∈ [0, 1.5π]`.
>
> ⇒ Con la vara del encabezado —funcionalmente idéntico— **el arco necesita UN arreglo, no
> una reescritura de la base: sacarle el espacio final.** Los `-0` y el ULP no son defectos.

### 12.4 · ⭐ Polígono, polilínea y rectángulo son EL MISMO nodo

Pregunta de Fermín, y la respuesta es tajante. Comparé la firma estructural de los **32**
compuestos —y el esqueleto del XML **completo**, no sólo `<Geometries>`—:

- **una sola firma** para las tres familias;
- `ObjectType` = `…Geometry.GeomCompositeCurve` en los 32;
- **ninguna** sección, tag ni atributo presente en una familia y ausente en otra.

⇒ **La herramienta de la UI se pierde en el archivo.** Un rectángulo es un compuesto cerrado
de cuatro rectas; un polígono, uno cerrado de N; una polilínea, uno abierto o cerrado de N.
Nada dice qué botón lo hizo.

Es el mismo patrón que ya apareció dos veces —**el modo se pierde**: los tres modos de los
parámetros de máquina daban el mismo `V`, y los tres modos de paro daban ISOs idénticos—,
ahora un nivel más arriba.

⇒ **El sintetizador necesita UN builder, no tres.** Rectángulo y polígono no son tipos: son
casos de uso.

### 12.5 · Lo que se derivó de los compuestos

- **Los 32 están encadenados**: el fin de cada miembro es el inicio del siguiente.
- **No hay flag de «cerrado»** — el cierre es geométrico. Polilíneas: 4 abiertas, 7 cerradas
  (más 7 con arcos). Polígonos: 6/6 cerrados. Rectángulos: 8/8.
  > ⚠️ **Para el converter**: el cierre hay que **calcularlo**, y con el ruido de punto
  > flotante de §7 (~3·10⁻¹³) **no se puede comparar por igualdad exacta**. Necesita
  > tolerancia, y la tolerancia hay que justificarla con evidencia.
- ⭐ **Siete polilíneas mezclan rectas y arcos en el mismo compuesto.** El sintetizador ya lo
  soporta: `build_polyline_spec` acepta `(end)` para recta y `(end, center, winding)` para arco.
- **El lado partido**: cuando el trazo arranca en medio de un lado, ese lado se guarda en
  **dos miembros colineales que comparten la misma recta base** —uno al principio y otro al
  final—. Pasa en `rectangulo_02/07/07+`, `poligono_04` y `polilinea_15`: exactamente los
  cinco que tienen un par colineal.
- **Los ángulos no se normalizan**: se observó `t1 = 8.019 rad`, mayor que 2π.

> 📌 **Error de lectura, y la regla que lo evita.** Al principio leí `P` como punto inicial y
> `t1` como longitud, y concluí que a tres rectángulos les sobraba un segmento. **Falso**: el
> segmento va de `P + t0·D` a `P + t1·D`, y en los miembros de un compuesto `t0` rara vez es
> 0 —se vio uno con `t0 = 44.4`—. En la línea de §4 valía 0 y por eso la lectura simplificada
> funcionaba. Lo corrigió Fermín.

### 12.6 · Lo que el lote NO puede derivar

Cinco propiedades **no varían en ninguno de los 88 archivos**:

| propiedad | valor único | qué queda sin saber |
|---|---|---|
| `IsAbsolute` | `false` | **no lo pone el checkbox** (§13.5): marcarlo no cambia el archivo. Qué lo pondría en `true`, DESCONOCIDO |
| `PlaneID` | `1918` | **una sola cara**; los otros cinco planos sin tocar |
| `Name` | vacío | si una geometría se puede nombrar |
| `Z` | `0` | nada fuera del plano |
| fórmulas | **cero** | cómo se parametriza un radio, un centro o un eje |

Los dos que pesan para el converter son **el plano** —un dibujo en otra cara apunta a otro
`Plane` y no hay ni un caso— y **las fórmulas** —§7 derivó cómo se ata una coordenada de
línea, pero no los nombres de las propiedades del arco, el círculo ni la elipse—.

Y dos familias fuera de lugar:

- **Falta `texto`**, la octava de la lista de la UI de §2.
- **Aparece `polígono`, que no está en esa lista.** Con §12.4 deja de importar para el modelo
  —es el mismo nodo— pero la lista de §2 hay que revisarla igual, porque `texto` **sí** podría
  ser otro nodo.


## 13. Bloque 3 (2026-08-22): la reutilización, el texto, el plano y el radio paramétrico

Cinco fixtures pedidos, cuatro derivados y uno que no capturó lo que buscaba.

### 13.1 · ⭐ Maestro REUTILIZA la geometría dibujada — no la duplica

Era lo único que trababa la rama G, y `R_PV_manual_base_linea_01_fresada` lo cierra:

| | `linea_01` | `linea_01_fresada` |
|---|---|---|
| geometrías | 1 (`GeomTrimmedCurve`, ID **1927**) | **1** (`GeomTrimmedCurve`, ID **1927**) |
| serialización | `8 0 300` ⏎ `1 50 50 0 1 0 0 ` | **idéntica** |
| `<Features>` | vacío | un `GeneralProfileFeature` llamado **«Fresado»** |

Y el `Feature` apunta a la geometría del dibujo:

```xml
<ManufacturingFeature i:type="a:GeneralProfileFeature">
  <Key><ID>2008</ID>…</Key>
  <Name>Fresado</Name>
  <GeometryID>
    <b:ID>1927</b:ID>
    <b:ObjectType>…Geometry.GeomTrimmedCurve</b:ObjectType>
  </GeometryID>
  <OperationIDs>… BottomAndSideFinishMilling (2007) …</OperationIDs>
```

El ID `1927` aparece **exactamente dos veces** en todo el archivo: la definición en
`<Geometries>` y la referencia del `Feature`.

⇒ **Un nodo, dos dueños.** Es la misma estructura que ya produce nuestro sintetizador —el
`GeometryID` del `Feature` apunta al dibujo y la trayectoria vive en la `Operation`—; la
diferencia es que el nuestro **siempre crea** la geometría junto con el mecanizado, y Maestro
puede **apuntar a una que ya existe**.

### ⚠️ Corrección de Fermín: la geometría es la REFERENCIA, no la traza

Acá había escrito «una geometría que un mecanizado toma **sí llega al ISO**». **Está mal, y
de un modo que importa.** Lo correcto es que **PUEDE llegar** — porque lo que el ISO lleva es
la **traza**, y la traza se *calcula a partir de* la geometría:

- la **corrección de fresa** y la **rebaba** generan recorridos **paralelos** a la geometría;
- el **acercamiento** y el **alejamiento** de un fresado **agregan segmentos** al principio y
  al final;
- un **vaciado** produce una traza compleja a partir de **una o más** geometrías.

Son operaciones donde el recorrido de la fresa **puede ser distinto** de la geometría, o que
la usan como **referencia para calcular** el recorrido. Se estudian en la rama D.

El propio fixture lo muestra, en el caso más simple posible. `linea_01_fresada` da **95
líneas** contra las 44 del programa vacío, y su cuerpo es:

```
G0 X50.000 Y50.000        <- posicionamiento
G0 Z145.400
D1 · SVL 125.400 · SVR 9.180
G1 Z-9.000 F2000.000      <- bajada en Z
G1 X350.000 Z-9.000 F5000.000
G0 Z20.000                <- salida
D0 · SVL 0.000 · SVR 0.000
```

La geometría dibujada es `(50,50) → (350,50)`, y **el XY de la traza coincide** — pero
coincide **porque la compensación está cancelada**: en todo el archivo sólo hay `G40`, ningún
`G41`/`G42`. Y aun coincidiendo en XY, **la traza no es la geometría**: agrega el
posicionamiento, la bajada en Z y la salida, que una geometría plana no tiene.

⇒ La formulación correcta: **lo que llega al ISO es la traza; la geometría es de dónde se
calcula.** Cuándo coinciden y cuándo no, lo decide la operación — y eso es la rama D.

### De paso, dos predicciones del 2026-08-19 que se cumplen

Es el primer fixture de la época nueva con traza de fresado real, y confirma lo que se había
anticipado desde el lote de dibujos:

| predicho | observado |
|---|---|
| `SVL`/`SVR` salen del catálogo de herramientas | `SVL 125.400` · `SVR 9.180` = `tool_offset_length` y `diameter/2` de **E001** |
| `S…M3` sale de `spindle_speed_std` | `S18000M3`, y E001 tiene `spindle_speed_std = 18000` |

### 13.2 · ⭐ El `Texto` NO es una familia nueva: son contornos

`R_PV_manual_base_texto_01` no trae ningún `GeomText`. Trae **seis `GeomCompositeCurve`**.

⇒ **Maestro convierte el texto a contornos al dibujarlo** — uno por glifo. Estructuralmente
ya está cubierto por lo que sabemos; lo que haría falta para *generarlo* es tipografía, que es
otro problema y no del formato.

⇒ Con esto, **las ocho geometrías de la pestaña Dibujar caben en cinco tipos de nodo**:
`GeomTrimmedCurve`, `GeomCircle`, `GeomEllipse`, `GeomCompositeCurve` y `GeomCartesianPoint`.
El barrido de familias queda **cerrado**.

### 13.3 · La geometría paramétrica del círculo: `Radius`

`R_PV_manual_base_circulo_radio_param` tiene un parámetro `Radio = 90` y esta expresión:

```
ref=1951  GeomCircle   Property=Radius   Index=-1   Value=Radio
```

⇒ **`GeomCircle.Radius`**, mismo mecanismo `Parametrics.Expression` que el `EndY` de la línea
(§7). Y la geometría se guarda **resuelta** (`… 0 90`), con la fórmula aparte — otra vez el
patrón de §7.

Mapa de propiedades conocido hasta hoy:

| geometría | propiedades con expresión derivadas |
|---|---|
| `GeomTrimmedCurve` (línea) | `StartX` · `StartY` · `EndX` · `EndY` |
| `GeomCircle` | `Radius` |
| `WorkPiece` | `Length` · `Width` · `Depth` |

### 13.4 · El plano: `PlaneID` cambia con la cara

`R_PV_manual_base_linea_cara2` trae **`PlaneID = 1920`**, contra el `1918` de los 88 fixtures
anteriores. ⇒ **Una geometría dibujada en otra cara apunta a otro `Plane`**, como se esperaba.
El hueco «los 88 están en una sola cara» queda cubierto para el caso de una segunda.

Quedan las otras cuatro caras, y saber si el `Plane` de un dibujo determina algo más.

### 13.5 · ⭐ «Coordenadas absolutas» NO SE GUARDA en el archivo

Y NO es el `<a:IsAbsolute>` del XML. Las dos cosas se creían lo mismo desde §2; las dos son
falsas.

**Lo que vio Fermín** (captura del 2026-08-24, `R_PV_manual_base_linea_01_abs.pgmx`):

- la casilla **«Coordenadas absolutas» marcada**;
- los campos `Xi Yi Zi Xf Yf Zf Longitud Ángulo` **en gris**, no editables;
- **sin asterisco** en la barra de título ⇒ el archivo está **guardado**;
- y al **cerrar y reabrir**, la casilla vuelve a aparecer **desmarcada**.

**Lo que dice el archivo**, leído después de ese guardado:

| | |
|---|---|
| `linea_01.pgmx` (19/08) vs `linea_01_abs.pgmx` (24/08, reguardado con la casilla marcada) | **XML byte a byte idéntico** |
| `<a:IsAbsolute>` de la **geometría** | `false` en los **dos** |
| los seis `IsAbsolute=true` que aparecen en el archivo | son de **`<Planes>`**, los seis planos de la pieza. Nada que ver con el dibujo |
| diferencia de tamaño (5788 vs 5804 B) | sólo el **nombre más largo** de los miembros del ZIP |

⇒ **DERIVADO: la casilla es un MODO DE VISUALIZACIÓN, no un dato del dibujo.** Que los campos
queden **en gris** al marcarla lo dice por otro lado: en absolutas no se edita, se mira.

⇒ ⚠️ **Queda REFUTADA la correspondencia que §2 daba por buena** —«checkbox Coordenadas
absolutas ↔ `<a:IsAbsolute>` del XML»—. Nunca hubo evidencia de eso; era una lectura
razonable que el fixture desarma. Es exactamente el patrón de la regla 1: un nombre igual en
dos lados que resultó ser dos cosas.

⇒ Y con eso, **`<a:IsAbsolute>` de la geometría vuelve a DESCONOCIDO**: vale `false` en los 89
dibujos que tenemos y no sabemos qué lo pondría en `true`. Ya no alcanza con marcar la casilla.

### Lo que la captura sí muestra de la referencia absoluta

Con la casilla marcada, sobre la pieza base (400×400×18, origen 0/0/0):

| campo | relativas | absolutas |
|---|---|---|
| `Xi` `Yi` | 50 · 50 | **50 · 50** |
| `Xf` `Yf` | 350 · 50 | **350 · 50** |
| **`Zi` `Zf`** | 0 · 0 | **18 · 18** |

⇒ Lo único que cambia es la **Z**: 0 en relativas, 18 en absolutas. Coherente con que la
referencia relativa mida desde la **cara superior** y la absoluta desde la **base** de la
pieza — pero es **una pieza con origen 0/0/0**, así que en XY las dos referencias coinciden
por construcción y no se pueden separar. Haría falta una pieza con origen XY distinto de cero.

### 📌 Y una corrección mía

El 22 escribí que este fixture «no capturó el cambio» y pedí rehacerlo verificando que la
casilla quedara marcada. **El fixture estaba bien desde el principio**: no hay nada que
capturar, porque Maestro no lo guarda. El error fue mío — di por sentada la correspondencia
de §2 en vez de tratarla como lo que era, una hipótesis sin fixture.

### 13.6 · El origen de la pieza: la geometría y la traza son RELATIVAS a él

`R_PV_manual_base_origen_x100_y50_linea` y su versión fresada, en los dos campos. El origen
de la pieza pasa de `(0,0)` a `(100,50)` y la línea se deja donde estaba.

**Dónde vive el origen**: en el `<Workpiece>`, tags **`<b:_xP>`** y **`<b:_yP>`**. Es el único
cambio del `.pgmx`:

```
-<b:_xP>0</b:_xP>      +<b:_xP>100</b:_xP>
-<b:_yP>0</b:_yP>      +<b:_yP>50</b:_yP>
```

**La geometría no se mueve.** La serialización es **byte a byte idéntica** a la de
`linea_01`: `8 0 300` ⏎ `1 50 50 0 1 0 0 `.

⇒ **Las coordenadas de una geometría dibujada son relativas al origen de la pieza.**

**La traza tampoco se mueve.** En el ISO del fresado, con origen `(0,0)` y con `(100,50)`:

```
G0 X50.000 Y50.000
G1 X350.000 …
```

⇒ ⭐ **La traza se emite en coordenadas de PIEZA, no de máquina.** El origen entra por otro
lado: el bloque `SHF`/`%Or`. Es exactamente lo que el converter necesita saber para mapear un
dibujo a la traza — y con origen `(0,0)` las dos lecturas coincidían y no se podían separar.

**Dónde sí se ve el origen**, en el ISO:

| | origen (0,0) | origen (100,50) |
|---|---|---|
| header `;H` | `DX=400.000 DY=400.000` | **`DX=500.000 DY=450.000`** |
| 1er bloque (esqueleto) | `SHF[X]=-3685.850` · `SHF[Y]=-400.000` | `SHF[X]=-3685.850` · **`SHF[Y]=-450.000`** |
| 2º bloque (del mecanizado) | `SHF[X]=-3685.850` · `SHF[Y]=-400.000` | **`SHF[X]=-3585.850`** · `SHF[Y]=-450.000` |

- El header confirma lo de R001: **`;H DX/DY` es dimensión + origen** (400+100=500,
  400+50=450), la envolvente ocupada — no las medidas de la pieza.
- Y aparece que **hay dos bloques de origen**: el del esqueleto y otro que abre el mecanizado,
  y **no son iguales** cuando el origen no es cero. El segundo corre la `X` en +100.

⚠️ **Caveat del fixture**: la profundidad del fresado difiere entre los dos archivos
(`Z-9.000` contra `Z-5.000`), así que no son gemelos exactos. No afecta lo derivado arriba
—que es sobre XY— pero sí impide comparar el eje Z.

## 14. Bloque 4 (2026-08-22): dos negativos, uno con testigo y otro sin

Fermín tuvo que **reiniciar Maestro** para que cada opción tomara efecto — dato que vale por
sí solo: **son opciones que se leen al arrancar la aplicación**, no en cada postproceso.

### 14.1 · `Repeticiones = 3` — no llega al ISO. Testigo interno ✅

| | |
|---|---|
| `.pgmx` | `<a:Repetitions>1</a:Repetitions>` → **`3`** |
| ISO | **idéntico** al base salvo el nombre del archivo |

⇒ **DERIVADO**: las repeticiones no llegan al ISO. Cierra el último parámetro que había
quedado fuera del barrido A5, y confirma por segunda vía lo que ya decía `emisor_iso.md`: el
XXL escribe `R=…` y el paso a ISO lo descarta. Ahora con `R=3`, no sólo con el default.

### 14.2 · `Pulgadas` — no llega tampoco, pero **el fixture no tiene testigo**

| | |
|---|---|
| `.pgmx` | **byte a byte idéntico** al base |
| ISO | **idéntico** salvo el nombre |

⇒ Con la unidad en pulgadas, ni el `.pgmx` ni el ISO cambian. Para el converter eso significa
que **`*MM` y `G71` literales son correctos**: la opción nunca los mueve.

⚠️ **Pero este negativo es más débil que los otros**, y conviene decir por qué: como el
`.pgmx` tampoco cambió, **el archivo no puede probar que la opción estaba puesta**. Es un
negativo sin testigo interno — a diferencia de `Repeticiones`, donde el `.pgmx` muestra el 3.

Lo que lo cerraría del todo: un fixture en pulgadas **con una cota tipeada**, o una captura de
la ventana Opciones con la unidad en pulgadas junto al archivo. Fermín reinició Maestro dos
veces a propósito, así que lo más probable es que el negativo sea real; queda anotado como
«probable, sin testigo».

> 📌 Y una consecuencia para `emisor_iso.cfg`: su encabezado declara que **el converter no
> puede emitir en pulgadas** hasta tener este fixture. Con esto, la salvedad se puede
> reformular: no es que no sepamos emitir pulgadas — es que **la opción no produce pulgadas
> en el ISO**. Pendiente de actualizar cuando toquemos el archivo.

## 15. Lo que queda abierto

- ⏸ **Postprocesar los tres fixtures paramétricos de §7.**
  > **Predicción falsable**: los tres ISO van a dar **idénticos al del programa vacío**,
  > incluido el de `Distancia=130` con la línea corrida, porque sigue sin haber mecanizado
  > y §8 derivó que la geometría no llega al ISO. **Si alguno diera distinto, se cae §8** —
  > y sería el hallazgo más grande de estos días.
- ~~Las otras **siete geometrías** de la pestaña Dibujar~~ → el **arco** quedó derivado
  (§10) y el resto tiene plan de fixtures en **§11**. Quedan seis.
- Los otros **métodos** de la barra contextual de Línea (además de `2 Puntos`), y qué
  significan `Secuencia Simple` y `Coordenadas Cartesianas`.
- Definir una línea **por `Longitud` y `Ángulo`** en vez de por dos puntos: ¿queda el mismo
  nodo? Era el discriminador de una hipótesis que ya se descartó por otro camino, pero
  sigue siendo una entrada de la UI que no se barrió.
- ~~El checkbox **«Coordenadas absolutas»** en `true`~~ **RESUELTO (§13.5): no se guarda.** Queda abierto **qué pone `<a:IsAbsolute>` de una geometría en `true`**, que es otra cosa.
- Qué otras **propiedades** de un `GeomTrimmedCurve` admiten expresión además de `EndY`
  (presumiblemente `StartX`/`StartY`/`EndX`, y quizá `Longitud` y `Ángulo`).
- **Qué acción dispara el recálculo** que mete el ruido (§7): lo aíslan dos fixtures
  triviales —abrir y guardar sin tocar nada, y abrir y agregar sólo un parámetro—. No
  bloquea nada hoy. Se sabe que **tipear un valor exacto ya alcanza** para ensuciarlo, así
  que la pregunta que queda es si hace falta que la geometría tenga una restricción.
- Verificar si los seis usos de tolerancia **`1e-15`** reciben valores leídos de un `.pgmx`
  (donde el ruido de 3·10⁻¹³ los desborda) o sólo calculados por el sintetizador.
