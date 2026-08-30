# Los `.cfg` posicionales de Xilog Plus, mapeados

**Fuente: `ExtCad32.dll`**, el binario que lee los archivos. Los descriptores son una tabla
contigua de paso 8 (`[CLAVE]` + terminador `00`), escrita **en orden inverso** y cerrada por
un marcador `[FILE ]=<ARCHIVO>.CFG`.

> ⚠️ **Cada mapeo se valida contra los datos de la máquina**: ningún índice fuera del rango
> nombrado puede tener un valor distinto de cero en ningún registro. Donde eso no se cumple,
> el mapeo queda PENDIENTE en vez de darse por bueno.

⭐ marca los campos que esta máquina realmente usa.


## `fields.cfg` — registro de 30 líneas · 17 registros

El campo `FIELD` («Field name») es la **línea del nombre** del registro, no un valor.

| idx | clave | etiqueta |
|---|---|---|
| 0 | `SPECX` | X mirror image ⭐ |
| 1 | `SPECY` | Y mirror image ⭐ |
| 2 | `NBRID` | Number of cross elements |
| 3 | `FBRID` | Number of first cross element |
| 14 | `ORGX` | X origin ⭐ |
| 15 | `ORGY` | Y origin ⭐ |
| 16 | `ORGZ` | Z origin |
| 17 | `WIDTH` | X dimension of field ⭐ |
| 18 | `HEIGH` | Y dimension of field ⭐ |
| 19 | `OFYBT` | Y offset center of stop |
| 20 | `OFXPM` | X offset multifunctional plane |
| 21 | `OFYPM` | Y offset multifunctional plane |
| 22 | `OGRAD` | Optional step (0=NO, 1=YES) |
| 23 | `BATNT` | Joined front and side stops (0=NO, 1=YES) |
| 24 | `AOBAT` | Movable stop offset authomatic management (0=NO,1=YES) |
| 25 | `ORGX1` | X origin with mobile stop OFF (mm) |
| 26 | `WIDT1` | Width (Size X mm) with mobile stop OFF |
| 27 | `CNFSG` | Path ON/OFF step separator (mm) |
| 28 | `NASOL` | Number of lock holes |
| 29 | `FASOL` | Number of first lock hole |

**Validación**: los índices con algún valor ≠ 0 son `[0, 1, 14, 15, 17, 18]`.
✅ **Todos caen dentro del mapa.**

## `spindles.cfg` — registro de 42 líneas · 1000 registros

| idx | clave | etiqueta |
|---|---|---|
| 0 | `SPINN` | Spindle number (1-96 / 1-999) ⭐ |
| 1 | `PLC` | Plc enabling (1-96) ⭐ |
| 2 | `TYPE` | Type (0=blank=ND,1=P=flat,2=F=lance,3=D=disc,4=T,5=S) ⭐ |
| 3 | `SERIE` | Series (1=X,2=Y) ⭐ |
| 4 | `FACE` | Working side ⭐ |
| 5 | `HEAD` | Motor number (0-4) ⭐ |
| 6 | `MOTOR` | Frequency converter (0=NONE) ⭐ |
| 7 | `FREQC` | Double spindle selection ⭐ |
| 8 | `DBLSP` | T. Motor number (0-4) |
| 9 | `TMOTO` | Frequency converter T. (0=NONE) |
| 10 | `FREQT` | Offset D |
| 21 | `OFFSD` | Angle A/B |
| 22 | `ANGAB` | Offset X ⭐ |
| 23 | `OFFSX` | Offset Y ⭐ |
| 24 | `OFFSY` | Offset Z ⭐ |
| 25 | `OFFSZ` | Offset R ⭐ |
| 26 | `OFFSR` | Time taken (secs) |
| 27 | `TIMET` | Head number ⭐ |

**Validación**: los índices con algún valor ≠ 0 son `[0, 1, 2, 3, 4, 5, 6, 7, 22, 23, 24, 25, 27]`.
✅ **Todos caen dentro del mapa.**

## Descriptores extraídos pero SIN mapeo posicional todavía

| archivo | campos del descriptor | por qué |
|---|---|---|
| `pheads.cfg` | 39 | no tiene línea de nombre y no se detectó el paso del registro |
| `storepos.cfg` | 45 | ídem |
| `supports.cfg` | 40 | ídem |
| `axis.cfg` | 33 | el descriptor es genérico (`PA001`…`PA032`, «See the meaning in the User Manual») |
| `clamps.cfg` | 19 | el archivo está vacío en esta máquina (sólo el índice 0) |
| `gendata.cfg` · `xilog3.cfg` | 27 · 19 | descriptor extraído; falta cruzar el reparto int/float |

Ninguno de los tres primeros alimenta hoy al converter: los que usamos son `fields.cfg`
(origen), `spindles.cfg` (offsets de huso) y `Params.cfg` (límites de eje), que es de tipo INI
y ya viene con claves.
