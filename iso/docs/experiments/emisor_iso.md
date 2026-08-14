# El emisor: quién escribe materialmente el ISO

**Documento vivo.** Nació el 2026-08-12 de una pregunta que quedó abierta en
`anatomia_iso.md`: hay líneas del esqueleto que no salen del programa, ni de la
configuración de máquina, ni de la ventana Opciones — **las escribe el binario que genera
el ISO**. La pregunta era si eso constituye un cuarto origen. La copia completa de la PC
del CNC la respondió el mismo día.

## ⭐⭐ El postproceso tiene DOS etapas, y casi todo lo que investigamos vive en la segunda

**2026-08-12.** El paso 0 —postprocesar el programa base en la PC de oficina técnica— no
produjo ningún `.iso`. Produjo **otros tres archivos**, y ahí estaba el hallazgo:

| Archivo | Qué es |
|---|---|
| `R_PV_manual_base_Of_Tec.xxl` | el programa en **XXL**, formato de texto de Xilog |
| `R_PV_manual_base_Of_Tec.pgm` | el mismo, **compilado a binario** (`BMB … Xilog3-9.0`) |
| `R_PV_manual_base_Of_Tec.inf` | el log del compilador: `XXL/PGM Compiler Version 9.0`, `[LINES]=16`, `[ERRORS]=0` |

⇒ La cadena es **`.pgmx` → XXL → PGM → ISO**, y lo que se detuvo fue el último tramo. Los
tres archivos están versionados en `evidencia/paso0_oficina_tecnica/`.

### El binario lo dice, tramo por tramo (2026-08-14)

> **Cómo se llegó a esto, y por qué hubo que volver.** La cadena se había inferido de que
> los tres archivos aparecieran juntos y de que el ISO nombre un `.pgm` en su línea 1.
> **Eso no alcanzaba**: coocurrencia no es dirección. Fermín lo cuestionó con un argumento
> correcto —`.iso`, `.xxl` y `.pgm` son los tres valores de `PostFileFormat`, o sea
> **formatos de salida elegibles**—, y al ir a verificarlo apareció la evidencia dura.

`Winxiso.exe` (`<Xilog Plus>\Bin\`) trae en su tabla de cadenas **su propia ayuda de línea
de comando**, con una modalidad por tramo:

```
Options:
  -o    [XXL -> PGM]
  -f    [XXL+BMP -> PGM]
  -c    [PGM -> ISO]
  -t    [symbol map]
```

⇒ **`-c [PGM -> ISO]` es literal**: el ISO se genera **desde el PGM**. El tramo que estaba
inferido queda DERIVADO. Y los tres tramos tienen ahora evidencia independiente:

| Tramo | Evidencia |
|---|---|
| `.pgmx` → XXL | el XXL lleva la versión de Maestro (`;Versione : 1.00.006.1009;`) y la fecha de creación |
| XXL → PGM | el `.inf` (`XXL/PGM Compiler Version 9.0`, `[LINES]=16` = las 16 líneas del XXL) **y** `-o [XXL -> PGM]` |
| PGM → ISO | **`-c [PGM -> ISO]`** |

### Y las dos lecturas se unifican

`PostFileFormat` **sí** es un selector de formato (`XXL` / `PGM` / `ISO`; en esta máquina
vale `ISO`). Las dos cosas son ciertas a la vez, y encajan: **la cadena es una sola, y el
selector decide dónde se detiene.** Con `ISO` se recorre entera, y por eso el postproceso
deja los cuatro archivos.

> **Predicción falsable, y fixture barato**: postprocesar el programa base con
> `PostFileFormat` = **XXL** debería dejar sólo el `.xxl`; con **PGM**, el `.xxl` + `.pgm` +
> `.inf`. Si cada valor deja **sólo** su propio archivo, la unificación es falsa y hay que
> volver a mirar. No necesita trayectoria: se puede hacer con el programa vacío, hoy.

### El XXL del programa vacío, entero

```
H DX=400.000 DY=400.000 DZ=18.000 -HG C=0 T=0 R=1 *MM /"def" BX=0.000 BY=0.000 BZ=0.000 V=0
;**********************************************************
; >> Post P. Release...
;Versione : 1.00.006.1010;
; >> Descrizione del programma...
; Data di creazione: 8/12/2026 8:19:19 PM
;
; >> Utensili utilizzati...
;
; >> Inizio Programma...
;**********************************************************
.END
;**********************************************************
F=1
O X=0 Y=0 Z=0 F=1 ;ChangePlane
;FINEPROG
```

**Dieciséis líneas contra las 43 del ISO.** Y la comparación de los dos headers dice dónde
ocurre cada cosa:

| | XXL (lo que produce Maestro) | ISO (lo que produce el generador) |
|---|---|---|
| forma | `H DX=…` — **instrucción** | `;H DX=…` — **comentario** |
| orden | `DX DY DZ -HG C T R *MM /"def" BX BY BZ V` | `DX DY DZ BX BY BZ -HG V *MM C T` |
| `R=1` | **está** | **no está** |
| `/"def"` (equipamiento) | **está** | **no está** |
| origen | `O X=0 Y=0 Z=0 F=1 ;ChangePlane` — **sin resolver** | `%Or[0].ofX=-400000.000` · `SHF[X]=-400.000` — **resuelto** |

Tres cosas quedan derivadas de una:

1. ✅ **`R` (repeticiones) se pierde en la segunda etapa.** Estaba anotado como hipótesis
   («el emisor omite la letra cuando vale el default»). Ahora se ve: Maestro **sí** lo
   escribe (`R=1`) y el ISO no lo lleva. La omisión no es de Maestro.
2. ✅ **El nombre del equipamiento (`/"def"`) tampoco sobrevive** al paso a ISO.
3. ⭐ **El origen se resuelve en la SEGUNDA etapa.** Maestro emite `O X=0 Y=0 Z=0`, el
   origen del programa tal cual; los `−400.000` y `−1515.600` de `fields.cfg` **los pone el
   generador de Xilog**, no Maestro. Toda la fórmula de B1c pertenece a esa etapa.

### Por qué esto reordena el modelo de orígenes

| Etapa | Quién | Qué aporta |
|---|---|---|
| 1 · `.pgmx` → XXL | **Maestro** | el programa (origen 1) y su configuración de aplicación (origen 3) |
| 2 · XXL/PGM → ISO | **el generador de Xilog** | `fields.cfg`, `NCI.CFG`, el `SHF`, los `%Or`, el teardown de mesa (origen 2 + el emisor) |

**Esto explica el resultado que más se repitió en el barrido**: de 17 opciones de la ventana
Opciones, sólo una llega al ISO. No es que el ISO las ignore — es que esas opciones actúan
en la **etapa 1**, y sólo llegan al ISO las que Maestro alcanza a escribir en el XXL. El
estacionamiento automático llega porque Maestro lo escribe; las de traza no llegan **en un
programa vacío** porque no hay trayectoria que escribir.

### ⭐ Las dos PCs producen el MISMO intermedio (2026-08-13)

El CNC postprocesó el mismo programa base y esta vez se guardaron **los cuatro** archivos.
Comparados contra los de oficina técnica:

| | Diferencias |
|---|---|
| `.xxl` (522 bytes en los dos) | **dos líneas**: `;Versione : 1.00.006.1009;` contra `…1010`, y la fecha de creación |
| `.pgm` (1.655 bytes en los dos) | **catorce bytes**, todos dentro de esas mismas dos cadenas |
| `.inf` | idéntico (`[LINES]=16`, `[ERRORS]=0`) |

⇒ **La etapa 1 es idéntica entre las dos máquinas.** Maestro produce exactamente el mismo
intermedio en las dos, salvo su firma de versión y el momento en que se corrió.

⇒ Y por lo tanto: **toda la diferencia entre las dos PCs vive en la etapa 2** — justamente
la que oficina técnica no puede completar. Para el programa vacío, el experimento de las
dos PCs queda respondido: **la máquina donde se prepara el programa no cambia nada**; lo que
manda es la que hace la segunda etapa.

### El postproceso es repetible, y el ISO no firma quién lo hizo

Dos cosas más de este juego de archivos:

- **El ISO del CNC de hoy es idéntico al del 2026-08-10**, salvo la línea 1 (el nombre del
  archivo). Tres días, y **los 17 fixtures del barrido de opciones en el medio**: el
  postproceso es repetible y la configuración volvió intacta. Es la misma conclusión que dio
  el `UI00.exe.Config`, ahora por el lado de la salida.
- **La versión de Maestro se pierde en el paso a ISO.** El XXL la escribe
  (`;Versione : 1.00.006.1009;`) y el ISO **no la lleva en ninguna línea**.

  > ❌ **Descartado (Fermín, 2026-08-13)**: se había propuesto guardar el `.xxl` junto a cada
  > ISO de referencia para conservar esa firma. **No se hace.** La trazabilidad de los ISO y
  > los archivos XXL quedan fuera del método; el XXL se usó para entender la cadena y ahí
  > termina su rol. Los del paso 0 quedan versionados como evidencia de este hallazgo, no
  > como práctica.

### Qué del XXL sobrevive al ISO

De las **16 líneas** del XXL, al ISO llegan **dos cosas**:

| Del XXL | En el ISO |
|---|---|
| `H DX=… R=1 … /"def" …` | la línea 2, reescrita: otro orden, sin `R`, sin `/"def"`, y como comentario |
| `O X=0 Y=0 Z=0 F=1` | las seis líneas de origen (`%Or[0].of*` y `SHF[*]`), **resueltas contra `fields.cfg`** |

**El resto no llega**: las once líneas de comentario del encabezado (release, versión, fecha,
«Utensili utilizzati»), y las marcas `.END`, `F=1` y `;FINEPROG`.

⇒ **De las 43 líneas del ISO, sólo dos tienen antecedente en el XXL. Las otras 41 nacen en
la segunda etapa.** Para un programa vacío, el ISO es casi por completo un producto de la
configuración de máquina y del emisor — el programa aporta sus medidas y su origen.

### ~~El XXL como intermedio observable~~ — RETIRADA COMO MÉTODO (2026-08-14)

> ❌ **Esta regla se dio de baja.** Decía: «cuando una línea del ISO no se entienda, se puede
> preguntar si ya estaba en el XXL, y eso dice en cuál de las dos etapas nace». Queda escrita
> como historia, **no se usa**.
>
> **Por qué.** Razona sobre el ISO **a través de un intermedio que no controlamos, no
> emitimos y no vamos a convertir**. El método de la época separa programa de máquina de una
> sola manera: **variando una cosa y viendo qué se mueve** (fixtures de variación controlada).
> El XXL es un atajo que evita el fixture, y evitar el fixture es exactamente lo que las
> reglas 4 y 5 del `CLAUDE.md` advierten — es una forma de equivocarse a distancia.
>
> **Y no hacía falta.** Ninguno de los hallazgos que sostienen el converter salió de acá: la
> fórmula del origen es de R002 (11 fixtures), el dialecto y las plantillas son de los
> binarios del emisor, `VL6`/`VL7` del catálogo de herramientas, y `EDK`/`ETK` del manual de
> SCM. Lo que el XXL aportó fue **relato**: por qué pasan cosas que los fixtures ya habían
> mostrado.
>
> **Alcance de la rama B, para que no se vuelva a mezclar**: se estudia **qué emite** el
> emisor (`PostISO.dll`, `nci32.dll`, `VtGenIso.dll`, `PlPathFilter32.dll`) — eso es lo que
> hay que reproducir byte a byte. **No** se estudian los formatos XXL y PGM, ni cómo se
> invoca `Winxiso`, ni el XConverter (que es del lado de la **entrada**: produce algunos de
> los `.pgmx` que habrá que convertir, y eso es la rama F).

## Por qué oficina técnica no llega al ISO

Lo que se sabe:

- **`PostFileFormat` vale `ISO` en las dos PCs** — no es la opción.
- **El compilador XXL/PGM terminó sin errores** (`[ERRORS]=0`) y dejó sus temporales en
  `<Xilog Plus>\WinXisoTemp\` (`.pgm`, `.r00`, `_AGRep.grp`, `_EIODataStep.sds`).
- `Winxiso.exe` y los DLL del generador **están** en las dos instalaciones.
- Toda la configuración de Xilog (`Cfg\`, 82 archivos) es **byte-idéntica** entre las dos, y
  `NCI.CFG` —con su `$GEN_ISO_FOR_EXTERNAL_APP = 1`— también.
- En `WinXisoTemp\` hay un caso anterior, de **marzo de 2025**, con exactamente el mismo
  patrón y sin `.iso` ⇒ **esta instalación no generó ISO nunca**, no es algo que se rompió
  hoy.

Lo que queda como candidato, por descarte: la diferencia está en **los binarios del
generador** (que difieren entre las dos PCs, ver abajo) o en algo fuera de `Cfg\` —
habilitación, licencia o instalación. Que la versión de oficina técnica sea justamente la
que tiene las plantillas del header **en formato PGM** encaja con lo observado, pero
contigüidad no es prueba.

### La consecuencia práctica, que importa hoy

**El barrido de opciones no se puede mudar a oficina técnica**: hay que seguir haciéndolo en
el CNC. Era la pregunta que el paso 0 venía a responder, y quedó respondida — con un «no»,
que también es respuesta.

Y el experimento de las dos PCs para las claves de traza (`RadiusMultiplier`,
`SecurityDistance`) **no se puede hacer como estaba planteado**: si una de las dos no emite
ISO, no hay dos ISO que comparar. Habría que compararlos en XXL, que es lo que las dos sí
producen — y ahí se vería si esas claves se congelan en la etapa 1.

## Quién genera el ISO

No lo genera Maestro por su cuenta: usa el **generador de Xilog Plus**, y la clave que lo
habilita está en el `NCI.CFG` de la máquina, en la primera línea del archivo:

```
$GEN_ISO_FOR_EXTERNAL_APP
1
```

Los módulos que aportan las líneas del esqueleto (`anatomia_iso.md`, B1g) son:

| Binario | Qué aporta |
|---|---|
| `PostISO.dll` | el bloque de puesta a punto, `SYN`, los `?%EDK[…]`, la tabla de códigos G y M |
| `PlPathFilter32.dll` | el teardown (`MLV`/`SHF`/`VL6`/`VL7`), dentro de su bloque de **mesa** |
| `VtGenIso.dll` | plantillas de `MLV`/`SHF` y el bloque del láser de cruce |
| `nci32.dll` | códigos G y las plantillas del header |

## ⭐⭐ El esqueleto es UN DIALECTO ENTRE CUATRO, y el nuestro es ESA-GV (2026-08-14)

`PostISO.dll` no emite «el ISO»: emite el ISO **de un control concreto**. Su tabla de cadenas
trae la lista de dialectos, contigua a las plantillas de nuestro propio esqueleto
(`?%%EDK[1].0=%d`, `%%ETK[114]`, `G64`, `SYN`, `G40`, `G168`, `G169`):

```
ISO-OSAI(2)          ISO-ESAGV(2)        ISO-NUM ERGON
ISO-OSAI(2) LUA      ISO-ESAGV(2) LUA    ISO-ORCHESTRA
ISO-ORCHESTRA LUA    ISO-NUM LUA
```

Y `VtGenIso.dll` trae dos clases hermanas del mismo bloque: `VtGenIso_CrossLaserOsai` y
`VtGenIso_CrossLaserKvara`.

⇒ Es un hallazgo del mismo tipo que B1d —el esqueleto no es plantilla fija— pero un nivel más
arriba: **no cambia una línea, cambia el lenguaje entero**.

### Dónde se elige, y por qué no está escrito

`Nci.ini`, la configuración del generador que ya estaba en el snapshot, tiene la clave:

```
[CNCNAME]
name=
```

**Vacía.** Es otra vez el mecanismo de B1h: la clave existe, ningún archivo la define, y el
emisor usa su default. Nuestro ISO es el dialecto **por defecto**.

### Cuál es, resuelto por el manual del fabricante

No por el default, sino por el lado del contenido (`anatomia_iso.md`, B1i). La *Guía de
Diagnóstico* de SCM `9031191610B` v4.2 dice que en los CNC **ESA-GV** las variables `E..`
«se transformarán en **ETK**..», agrupa `RD110s-TV-**Pratix**` y documenta `ETK103` como
parámetro de RD110 con CNC ESA-GV. Nuestro ISO usa `ETK` y `EDK`.

⇒ **La Pratix es CNC ESA-GV, y el dialecto emitido es `ISO-ESAGV(2)`.**

### Qué cambia para el converter

`emisor_iso.cfg` guarda el esqueleto de **un** dialecto. Su encabezado declaraba la versión de
Maestro y la fecha de los binarios, pero no **para qué control** vale. Si `[CNCNAME]` dejara
de estar vacío, o si el archivo se usara contra una máquina con otro control, el esqueleto
entero es otro y nada lo advertía. Queda anotado en la procedencia del archivo.

## El XConverter no tiene nada del esqueleto (2026-08-14)

Pregunta de Fermín: ¿el XConverter revela de dónde salen las líneas que pusimos en
`emisor_iso.cfg`, o las tiene también en el código?

**Barrido de 28 archivos** —los cuatro `XConverter*` de la carpeta de Maestro y los 12+12 de
`C:\SPAI\X-CAB` y `C:\SPAI\EASYNEST`—, en ASCII y UTF-16, contra 20 patrones que cubren todo
lo que hoy vive en `emisor_iso.cfg`: `MLV`, `SHF[*]`, `VL6/VL7`, `EDK[`, `ETK[`, `%Or[`,
`SYN`, `_paras(`, `%ax[n].pa`, `G0G53`, `H DX=`, `G71/G70`, `G40`, `M2/M58`, `$GEN_`, `$MA_`,
`$PM_`, `$KEY_`, `NCI.CFG`.

**Cero coincidencias.** Lo único que aparece son extensiones de archivo (`\temp.xxl`, `.xcs`).

Control positivo, para que el negativo valga: los mismos 20 patrones contra los binarios que
B1g ya atribuyó aciertan **9/20** en `PlPathFilter32.dll`, **8/20** en `PostISO.dll`, 7/20 en
`VtGenIso.dll` y 3/20 en `nci32.dll`.

⇒ **El cuarto origen se sostiene**: esas líneas no tienen otra fuente que los binarios del
emisor. Y queda reconfirmado por una segunda vía que el XConverter no produce ISO — no es que
le falte la modalidad, **no tiene el vocabulario**.

> El barrido de B1g no podía llegar acá por dos límites de `buscar_en_binarios.py`: las raíces
> están fijas en las dos instalaciones de SCM (`C:\SPAI` queda afuera) y el filtro sólo toma
> `.dll`/`.exe` (así que `Xconverter.exe.new` nunca se miró). Son puntos ciegos de la
> herramienta, no del método.

## ⭐ Las dos PCs NO tienen el mismo emisor (2026-08-12)

Comparación por sha256 entre la copia completa del CNC (`S:\Copia CNC`) y la instalación de
oficina técnica. **Los seis binarios difieren.**

| Binario | CNC | Oficina técnica |
|---|---|---|
| `PostISO.dll` | 262.144 B · **2011-11-18** | 262.144 B · 2011-10-14 |
| `PlPathFilter32.dll` | 184.320 B · **2011-11-18** | 184.320 B · 2011-10-14 |
| `VtGenIso.dll` | 262.144 B · **2011-11-18** | 262.144 B · 2011-10-14 |
| `nci32.dll` | **319.488 B** · **2011-11-18** | **315.392 B** · 2011-10-14 |
| `Nci.dll` · `ChkPgm32.dll` | difieren | difieren |

**El CNC tiene la build más nueva**, de un mes después. Y la diferencia no es cosmética:
`nci32.dll` además **pesa 4 KB más** y su tabla de cadenas cambió. Las plantillas del
header en formato PGM (`(H DX%.*f`, ` BX%.*f`, ` BY%.*f`, …) están **sólo en la versión de
oficina técnica**; la del CNC no las tiene.

> ⚠️ **Ninguno de estos DLL tiene número de versión** (`FileVersion` vacío: son de 2011).
> Su identidad sólo puede ser **fecha + tamaño + hash**, como el `manifest.csv`.

### Qué se sigue de esto

1. **El emisor es un origen.** No es «el binario hace siempre lo mismo»: hay dos emisores
   distintos conviviendo en el taller, y difieren justamente en plantillas de emisión.
2. **Toda evidencia queda fechada contra un emisor.** Un ISO de referencia prueba lo que
   emite *esa* build. Los ISO de la serie R salieron todos del CNC, así que son
   consistentes entre sí — pero no son transferibles a la otra PC sin verificar.
3. **Sube el valor del paso 0** (postprocesar el programa base en oficina técnica). Ya no
   es confirmar lo esperado: ahora hay un motivo concreto para que pueda dar distinto, y
   el resultado importa igual en los dos sentidos.

### Lo que este hallazgo NO dice

Que los binarios difieran **no prueba** que el ISO difiera. Las diferencias podrían estar
en rutas de código que este esqueleto no ejercita, y la evidencia disponible apunta a que
buena parte del preámbulo y del cierre viene de `NCI.CFG` —que **sí es idéntico en las dos
PCs**, igual que `Nci.ini`—. El paso 0 es exactamente el experimento que lo separa.

## El matiz que ordena todo esto: config vacía, no constante

De B1h: los binarios consultan **30 claves `$…`** que ningún archivo de la instalación
define (`$MA_*` de mesa, `$PM_*` de macros de archivo/bloque/ciclo, y `$KEY_G%d`/`$KEY_M%d`
para la traducción de cada código G y M).

⇒ Casi todo lo que parecía «constante del binario» es en realidad **el valor por defecto de
una clave de configuración que nadie escribió**. El mecanismo es el mismo de `NCI.CFG`, no
uno nuevo: el emisor lee configuración, y cuando no la encuentra tiene un default.

El emisor incluso trae su propio fail-loud: si no encuentra la clave de un código G escribe
`;G%d: CORRISPONDENZA NON TROVATA!` **dentro del ISO**.

## ✅ El cuarto origen, hecho archivo (Fermín, 2026-08-13)

**Decisión**: las líneas que pone el emisor no se escriben dentro del converter — se
guardan en un archivo de configuración más, al lado del snapshot de la máquina, y el
converter lo lee como cuarto origen.

`iso/data/machine_config/emisor_iso.cfg`, leído por `iso/emisor.py`.

| | |
|---|---|
| **Alcance** | el **esqueleto completo**, con `<marcadores>` donde se insertan el header, el origen, los bloques de `NCI.CFG` y el cuerpo |
| **Formato** | el de los `.cfg` de Xilog: `$CLAVE` … `$`; fuera de los bloques, todo es comentario |
| **Prefijo** | `$EMI_`, nunca `$GEN_`/`$MA_`/`$KEY_`, que son claves reales de SCM |

### La regla prestada, y por qué

Dentro de los bloques rige **la misma regla de emisión que el emisor aplica al `NCI.CFG`**:
la línea se corta en el primer `;` y lo anterior se emite tal cual. No es por simetría
estética — es por los **espacios finales**:

```
G71 ;   ->  "G71 "     M2  ;   ->  "M2  "     SYN   ->  "SYN"
```

Las líneas 9 a 43 del ISO llevan un espacio al final, la 22 ninguno y la 43 dos. Escritos
al desnudo, el primer editor con «quitar espacios finales» los borraría en silencio y el
byte-idéntico se rompería sin que nadie lo note. Con el `;` que los cierra, **son visibles
y a prueba de editor**. Un `;` literal —lo necesita la línea del header— se escribe `;;`.

Dos diferencias deliberadas con el `NCI.CFG`, escritas en el propio archivo: acá el `%`
**no** se duplica (nuestras líneas no pasan por ningún printf) y el archivo va en **UTF-8**,
porque es nuestro y tiene acentos.

### Cómo se verifica que sirve

`tests/test_iso_emisor.py` rearma el ISO del programa vacío desde el archivo y lo compara
**byte a byte** contra el de referencia (`evidencia/paso0_cnc/`). Si alguien toca un espacio,
el test cae. También comprueba que un valor faltante **explota con `KeyError`** en vez de
completarse solo: regla 4, en código.

### Lo que el archivo declara que NO sabe

Escrito en su propio encabezado, para que el hueco viaje con el dato:

- `*MM` y `G71` están literales porque toda la evidencia se derivó con `IsMM=true`. **Hasta
  que haya un fixture en pulgadas, el converter no puede emitir en pulgadas.**
- El bloque de ocho líneas del `Xn` no está: su `Z201.000` todavía no tiene origen (rama C).
- `?%EDK[0].0` y `?%EDK[1].0` van con valor 0, el único observado.
- ⚠️ **`?%ETK[8]=1` NO es constante** (agregado 2026-08-14, B1i): pertenece a la banda del
  **cambio de herramienta** (`ETK 6–12`), y en los ISO con mecanizado alterna 1 y 2. Vale 1
  acá sólo porque el programa vacío no cambia de herramienta. **En cuanto haya mecanizado con
  más de una, este valor es incorrecto.**
- El esqueleto es el del dialecto **`ISO-ESAGV(2)`**; hay otros tres, y la clave que los
  elige (`[CNCNAME]` de `Nci.ini`) está vacía en esta máquina.

## Decisión pendiente

**¿El snapshot incluye también los binarios del emisor?** El archivo de arriba registra
*qué* emite; no registra *quién* lo emitió. Hoy `emisor_iso.cfg` lo dice en prosa en su
encabezado (Maestro 1.00.006.1009, binarios del 2011-11-18). Formalizarlo sería sumar su
sha256 al manifest, sin necesariamente versionar 1 MB de DLL.

Lo que cambia: con el emisor registrado, el converter puede fallar ruidosamente si el ISO de
referencia salió de otra build. Sin registrarlo, esa diferencia es invisible.

## Herramienta

```
py -m iso.machining_lab.buscar_en_binarios barrer "VL[67]=" "SHF\[Z\]"
py -m iso.machining_lab.buscar_en_binarios contexto <binario> "^SYN$"
```
