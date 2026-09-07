# Fresado — rama D

**Documento vivo.** El **Fresado**: la operación que recorre una geometría con una herramienta
del electromandril. Tercer mecanizado de la rama D, y el que menos evidencia propia tiene.

> 📌 **Por qué este doc nace tarde y con un solo fixture.** La primera —y hasta hoy única—
> traza de fresado de la época nueva llegó en el **lote de dibujos** (rama G), y quedó
> archivada en `dibujos.md` §13.1 mientras la rama D figuraba como 🔮 sin arrancar. La
> auditoría del 2026-08-27 lo detectó y la hoja de ruta lo anotó como *«falta consolidarlo en
> un doc de la rama D»*. **Esto es esa consolidación** (2026-09-07), con los números
> re-medidos.

## 1. El único fixture

`R_PV_manual_base_linea_01_fresada` (+ su variante con `Xmsg`), campo `HG`, pieza 400×400×18.
Una **línea dibujada** de (50,50) a (350,50) que un `GeneralProfileFeature` llamado «Fresado»
toma, con la herramienta **`E001`** (Widea 18 mm) y profundidad 9.

⚠️ **Es un fixture de otra rama.** No hubo lote de fresado: no se barrió ni un parámetro, ni
la estrategia, ni el acercamiento, ni la corrección. Todo lo de abajo sale de **un solo par**.

## 2. ⭐ Maestro REUTILIZA la geometría dibujada

Lo que trababa la rama G, y este fixture lo cerró: el `Feature` **apunta** a la geometría del
dibujo en vez de duplicarla. El ID aparece exactamente dos veces en el archivo — la definición
en `<Geometries>` y la referencia del `Feature`.

⇒ **Un nodo, dos dueños.** Nuestro sintetizador siempre crea la geometría junto con el
mecanizado; Maestro puede apuntar a una que ya existe. Detalle en `dibujos.md` §13.1.

## 3. ⭐ La traza NO es la geometría

Corrección de Fermín, y es la que ordena toda la rama D: **lo que llega al ISO es la traza; la
geometría es de dónde se calcula.**

- la corrección de fresa y la rebaba generan recorridos **paralelos**;
- el acercamiento y el alejamiento **agregan segmentos**;
- un vaciado produce una traza compleja a partir de **una o más** geometrías.

Este fixture lo muestra en el caso más simple: el XY de la traza **coincide** con la línea
dibujada —porque la compensación está cancelada, sólo hay `G40`— y aun así **agrega el
posicionamiento, la bajada en Z y la salida**, que una geometría plana no tiene.

## 4. El bloque, medido (2026-09-07)

Contra el programa vacío del mismo campo (43 líneas), el fresado de una línea agrega
**51 líneas**:

```
?%ETK[8]=1 · G40   ×2          <- preámbulo del bloque
MLV=0 · T1 · SYN · M06         <- cambio de herramienta
?%ETK[6]=1 · ?%ETK[9]=1 · ?%ETK[18]=1
S18000M3 · G17
MLV=2 · %Or[0].ofX/Y/Z         <- el segundo bloque de origen
MLV=1 · SHF[X]/[Y]/[Z]
MLV=2 · ?%ETK[13]=1
MLV=2 · SHF[X]=32.050 · SHF[Y]=-246.650 · SHF[Z]=-125.300   <- offset del electromandril
G0 X50.000 Y50.000
G0 Z145.400                    <- SVL + plano de seguridad
D1 · SVL 125.400 · VL6 · SVR 9.180 · VL7
G1 Z-9.000 F2000.000
?%ETK[7]=4
G1 X350.000 Z-9.000 F5000.000  <- el corte
G0 Z20.000
D0 · SVL 0.000 · …
```

### ⭐⭐ Y es EL MISMO BLOQUE que el canal con fresa

Comparado línea por línea contra el canal del Grupo 11 hecho con la `E004`
(`canal.md` §19), las **51 líneas coinciden en estructura**. Lo único que difiere:

| | fresado de línea | canal con `E004` |
|---|---|---|
| herramienta | `T1` · `?%ETK[9]=1` | `T4` · `?%ETK[9]=4` |
| del catálogo | `SVL 125.400` · `SVR 9.180` | `SVL 107.200` · `SVR 2.000` |
| coordenadas y cota | `Y50`, `Z-9` | `Y200`, `Z-10` |

⇒ **Dos operaciones distintas de la UI producen el mismo bloque de ISO.** Confirma desde el
otro lado lo que `canal.md` §19 derivó: **la familia de emisión la decide la HERRAMIENTA, no
la operación** — y `?%ETK[7]=4` es la del electromandril, se llame «Fresado» o «Canal».

## 5. Lo que se cumplió de lo predicho

| predicho (2026-08-19) | observado |
|---|---|
| `SVL`/`SVR` salen del catálogo | `SVL 125.400` · `SVR 9.180` = `ToolOffsetLength` y radio del cuerpo de la `E001` |
| `S…M3` sale de `SpindleSpeed.Standard` | `S18000M3`, y la `E001` tiene 18000 |

Y la cota de aproximación, `G0 Z145.400` = **`SVL` + 20**, la misma regla que el canal
(`canal.md` §19).

## 6. El incremento del conteo del `Xmsg`

**+206** para este fresado (`operaciones_maquina.md` §17.2).

> ⚠️ Ese número es de **un** fixture, y desde el 2026-09-07 sabemos que el conteo **mide
> caracteres del texto emitido** (`operaciones_maquina.md` §18). El 206 vale para *esta* traza,
> no para «el fresado» — otra geometría con otras coordenadas da otro número, y la regla es
> contar, no tabular.

## 7. Lo que falta, que es casi todo

El fresado **no tiene lote propio**. Con un solo fixture, sin barrido, quedan sin tocar:

| | |
|---|---|
| las cinco geometrías | sólo se probó la **línea**. Arco, círculo, polilínea y contorno, sin fixture |
| la **estrategia** de fresado | `MillingStrategySpec` existe en el sintetizador y no hay evidencia nueva |
| el acercamiento y el alejamiento | el fixture los tiene deshabilitados |
| la corrección (`G41`/`G42`) | el canal la derivó (`canal.md` §21); falta confirmar que el fresado se comporta igual |
| las pasadas en Z | y el bug de Maestro con `StepDepth` que no divide exacto (`hoja_de_ruta`, 2026-09-03) |
| el sentido de recorrido | el canal con sierra lo normaliza; con fresa va en el sentido dibujado. Sin probar en un contorno cerrado |

⇒ **Cuando la rama D siga, el fresado es el lote grande**: es la operación con más superficie
sin medir, y la que más geometrías admite.
