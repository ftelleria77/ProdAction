# Anatomía del ISO — atribución línea por línea (rama B)

**Documento vivo.** Cada línea del ISO tiene que poder atribuirse a UNO de los tres
orígenes; lo que no se pueda atribuir queda escrito como desconocido, nunca como
supuesto. Crece con cada operación nueva.

Los tres orígenes (ver `programa_vacio.md`):

| # | Origen | Dónde vive |
|---|---|---|
| 1 | **Programa** | el `.pgmx` |
| 2 | **Máquina** | snapshot de la PC del CNC (`iso/data/machine_config/snapshot/`) |
| 3 | **Aplicación** | `<Maestro>\UI00.exe.Config` (ventana Opciones) |

Niveles de confianza, explícitos en cada fila:

- **DERIVADO** — la evidencia lo prueba (un fixture que varía esa cosa y sólo esa).
- **HIPÓTESIS** — encaja, pero un solo caso no lo separa de otras lecturas. Dice qué
  fixture lo confirmaría.
- **DESCONOCIDO** — no se sabe. No se rellena con nada.

## B1 · El esqueleto: programa sin mecanizados

**Fuente**: `R_PV_manual_base.pgmx` (autoría 100% manual de Fermín en Maestro,
2026-08-10) → `P:\USBMIX\ProdAction\Programas Manuales\Reinvestigación\r_pv_manual_base.iso`.
Pieza 400×400×18, origen 0/0/0, área HG, **cero operaciones**.

**43 líneas · 666 bytes · CRLF · termina CON CRLF · cp1252.**

Espacios finales: los llevan casi todas las líneas (uno), salvo la 1, la 3, la 5, la 7
y el bloque 22–29. La 43 (`M2`) lleva **dos**. No es adorno: es parte del byte.

### La estructura

| Líneas | Bloque |
|---|---|
| 1–2 | Cabecera: nombre y `;H` |
| 3–7 | Preámbulo de máquina |
| 8–21 | Puesta a punto del programa (origen, SHF) |
| 22–30 | Reset de registros |
| 31–42 | Teardown (SHF a cero) |
| 43 | Fin |

### Línea por línea

| # | Línea | Origen | Confianza |
|---|---|---|---|
| 1 | `% r_pv_manual_base.pgm` | **Programa** — nombre del ARCHIVO, en minúsculas, extensión `.pgm` | DERIVADO (el par `_cnc` lo prueba: cambió el nombre del archivo y cambió sólo esta línea) |
| 2 | `;H DX=400.000 DY=400.000 DZ=18.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 ` | ver desglose abajo | mixto |
| 3 | `?%ETK[500]=100` | ? | DESCONOCIDO |
| 5 | `_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )` | **Máquina** — parámetro 21 del eje 0 | DERIVADO (referencia explícita a `%ax`) |
| 7 | `G0 G53 Z %ax[2].pa[22]/1000` | **Máquina** — parámetro 22 del eje 2, en coordenadas de máquina (`G53`) | DERIVADO |
| 8 | `M58 ` | ? | DESCONOCIDO |
| 9 | `G71 ` | **Aplicación** — G71 es «medidas en mm» | HIPÓTESIS (lo confirma cambiar `IsMM`, que es global) |
| 10 | `MLV=0 ` | ? — abre el bloque de origen | DESCONOCIDO |
| 11 | `%Or[0].ofX=-400000.000 ` | **Programa + Máquina** — µm; `= campo_X(H) − DX = 0 − 400` | HIPÓTESIS (lo confirma `R_PV_dim_500x350x25`: debería dar −500000) |
| 12 | `%Or[0].ofY=-1515599.976 ` | **Máquina** — µm; `campo_Y(H) = −1515.60` de `fields.cfg` | DERIVADO (el valor está en el archivo) |
| 13 | `%Or[0].ofZ=18000.000 ` | **Programa** — µm; `= DZ` | HIPÓTESIS (lo confirma el fixture de dimensiones: debería dar 25000) |
| 14–15 | `?%EDK[0].0=0 ` · `?%EDK[1].0=0 ` | ? | DESCONOCIDO |
| 16 | `MLV=1 ` | ? | DESCONOCIDO |
| 17 | `SHF[X]=-400.000 ` | ídem 11, en mm | HIPÓTESIS |
| 18 | `SHF[Y]=-1515.600 ` | ídem 12, en mm | DERIVADO |
| 19 | `SHF[Z]=18.000+%ETK[114]/1000 ` | **Programa** (`DZ`) **+ Máquina** (corrección en runtime) | HIPÓTESIS sobre `DZ` |
| 20 | `?%ETK[8]=1 ` | ? | DESCONOCIDO |
| 21 | `G40 ` | cancelación de compensación — constante del protocolo | DERIVADO por contexto |
| 22 | `SYN` | ? | DESCONOCIDO |
| 23–29 | `?%ETK[0]=0` `[1]` `[2]` `[13]` `[17]` `[18]` `[19]` | reset de registros; el CONJUNTO de índices es fijo | DESCONOCIDO (por qué esos siete) |
| 30 | `?%EDK[13].0=1 ` | ? | DESCONOCIDO |
| 31–34 | `MLV=1 ` + `SHF[X]=0 ` `SHF[Y]=0 ` `SHF[Z]=0 ` | teardown: anula el SHF del nivel 1 | DERIVADO por contexto |
| 35–38 | `MLV=2 ` + `SHF` en cero | ídem nivel 2 — **aparece aunque el nivel 2 nunca se usó** | DERIVADO por contexto |
| 39 | `MLV=0 ` | vuelve al nivel 0 | DERIVADO por contexto |
| 40–41 | `VL6=0 ` · `VL7=0 ` | ? | DESCONOCIDO |
| 42 | `?%EDK[13].0=0 ` | cierra lo que abrió la 30 | DERIVADO por contexto |
| 43 | `M2  ` (dos espacios) | fin de programa | DERIVADO por contexto |

### Desglose del header `;H` (línea 2)

| Campo | Valor | Origen | Confianza |
|---|---|---|---|
| `DX` `DY` `DZ` | 400.000 / 400.000 / 18.000 | **Programa** — dimensiones de la pieza | DERIVADO (coinciden exacto) |
| `BX` `BY` `BZ` | 0.000 / 0.000 / 0.000 | **Programa** — origen de la fase **o** `WorkpieceOffset`; los dos valen 0 acá | HIPÓTESIS — lo separa `R_PV_origen_x100_y50` |
| `-HG` | | **Programa** — el «Área» de Parámetros de máquina (`ExecutionFields`) | DERIVADO |
| `V=0` | | ? | DESCONOCIDO |
| `*MM` | | **Aplicación** — unidad de medida (`IsMM`) | HIPÓTESIS |
| `C=0` | | **Programa** — `ContinuousCycle=false` | HIPÓTESIS — sin fixture (el synth no lo varía) |
| `T=0` | | **Programa** — `IsTechnologicalMirror=false` | HIPÓTESIS — sin fixture |

`Repetitions=1` **no aparece** en el header. Dónde va (o si no va) queda abierto.

### El origen sale de `fields.cfg`

`iso/data/machine_config/snapshot/xilog_plus/Cfg/fields.cfg` guarda un bloque de 29
valores por área, con la letra del área **al final** del bloque. Los dos primeros
valores de la terna son X e Y:

| Área | X | Y |
|---|---|---|
| E | −3688.00 | −1515.25 |
| F | −1843.00 | −1515.75 |
| G | −1843.00 | −1515.75 |
| **H** | **0.00** | **−1515.60** |

El ISO de un programa en área **HG** usa **Y = −1515.60**, que es el de **H**. Con qué
criterio un área combinada «HG» toma la de H y no la de G es **DESCONOCIDO**; lo
discrimina `R_PV_campo_EF` (si usa E o F).

Y hay una asimetría real entre ejes: **X resta DX y el eje Y no resta DY.**
`SHF[X] = 0 − 400 = −400` mientras `SHF[Y] = −1515.60` tal cual, con DY = 400 también.
El fixture de dimensiones (500×350) lo despeja de una.

### La precisión simple, confirmada con evidencia propia

`SHF[Y] = -1515.600` (mm) y `%Or[0].ofY = -1515599.976` (µm). Si la conversión fuera en
doble precisión, sería `-1515600.000`. En **float32**, `1515.6` es exactamente
`1515.5999755859375`; por 1000 y redondeado a tres decimales da **1515599.976**.

⇒ El emisor pasa por **precisión simple** al convertir a micras. Queda derivado en la
época nueva, sin depender de la anterior.

## Preguntas que abre el esqueleto

- ¿Qué es `V=0` del header? ¿Y `Repetitions`, que no aparece?
- ¿Por qué el reset toca justo los registros `ETK[0,1,2,13,17,18,19]`?
- ¿Qué son `M58`, `SYN`, `VL6`, `VL7`, `EDK[13].0`, `ETK[8]`, `ETK[500]`?
- El teardown escribe `MLV=2` aunque el nivel 2 nunca se usó: ¿es fijo o depende de la
  máquina?
- `%ETK[114]` de la línea 19: ¿qué corrección es, y de dónde sale?

Las responden los `.cfg` del snapshot, el manual de Xilog (`pgmx/docs/xilog_plus_pgm/`) y
los fixtures de R001 — en ese orden: primero leer, después preguntar (regla 2).
