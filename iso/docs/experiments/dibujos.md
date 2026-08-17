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
| checkbox **Coordenadas absolutas** | ↔ `<a:IsAbsolute>` del XML. Sin marcar = `false` |
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

## 9. Lo que queda abierto

- ⏸ **Postprocesar los tres fixtures paramétricos de §7.**
  > **Predicción falsable**: los tres ISO van a dar **idénticos al del programa vacío**,
  > incluido el de `Distancia=130` con la línea corrida, porque sigue sin haber mecanizado
  > y §8 derivó que la geometría no llega al ISO. **Si alguno diera distinto, se cae §8** —
  > y sería el hallazgo más grande de estos días.
- Las otras **siete geometrías** de la pestaña Dibujar (arco, círculo, elipse, polilínea,
  rectángulo, punto, texto): qué código de curva base usa cada una y qué lleva su
  `_serializationGeometryDescription`.
- Los otros **métodos** de la barra contextual de Línea (además de `2 Puntos`), y qué
  significan `Secuencia Simple` y `Coordenadas Cartesianas`.
- Definir una línea **por `Longitud` y `Ángulo`** en vez de por dos puntos: ¿queda el mismo
  nodo? Era el discriminador de una hipótesis que ya se descartó por otro camino, pero
  sigue siendo una entrada de la UI que no se barrió.
- El checkbox **«Coordenadas absolutas»** en `true`: qué cambia además de `IsAbsolute`.
- Qué otras **propiedades** de un `GeomTrimmedCurve` admiten expresión además de `EndY`
  (presumiblemente `StartX`/`StartY`/`EndX`, y quizá `Longitud` y `Ángulo`).
- **Qué acción dispara el recálculo** que mete el ruido (§7): lo aíslan dos fixtures
  triviales —abrir y guardar sin tocar nada, y abrir y agregar sólo un parámetro—. No
  bloquea nada hoy. Se sabe que **tipear un valor exacto ya alcanza** para ensuciarlo, así
  que la pregunta que queda es si hace falta que la geometría tenga una restricción.
- Verificar si los seis usos de tolerancia **`1e-15`** reciben valores leídos de un `.pgmx`
  (donde el ruido de 3·10⁻¹³ los desborda) o sólo calculados por el sintetizador.
