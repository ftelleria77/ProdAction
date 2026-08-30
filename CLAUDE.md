# ProdAction — reglas para todo agente

## 1. Antes de construir: buscar incongruencias en la nomenclatura

**Antes de escribir código nuevo, revisá los nombres involucrados. Si encontrás una
incongruencia, PARÁ y preguntale a Fermín, o pedile una definición. No la resuelvas por tu
cuenta ni construyas encima.**

Una incongruencia es un nombre que no dice lo que la cosa es, o que dice dos cosas a la vez:

- una spec llamada por la operación genérica y no por su feature (`SquaringMillingSpec` para lo
  que la UI llama Galceado);
- un parámetro cuyo valor no significa lo que aparenta (`xn=None` significando "el Xn POR
  DEFECTO" en vez de "ninguno");
- dos interruptores para lo mismo (`xn` + `include_xn`);
- un nombre nuestro que no existe en la UI de Maestro, o que existe con otro significado.

### Por qué es una regla y no una preferencia de estilo

Porque las incongruencias **fabrican evidencia falsa**, y este proyecto se sostiene sobre la
evidencia. Casos reales, todos encontrados por Fermín después de que yo construyera encima:

- **El test que mentía en su nombre.** `test_no_xn_uses_default` decía verificar "sin Xn". Nunca
  lo hizo: `xn=None` escribía el Xn por defecto, así que el .pgmx que generaba SÍ tenía Xn. La
  incongruencia del parámetro hizo que el caso "sin Xn" fuera **infabricable**, y el test que
  decía cubrirlo daba verde. El agujero quedó tapado por su propia red.
- **`X_PARK = -3700.0`.** Existía para inventar un park cuando no había Xn — un caso que nunca
  pudo derivarse. Un número mágico que tapaba un agujero: mientras estuvo, el converter no podía
  notar que le faltaba evidencia.
- **`_saw.py` → `_channel.py`.** Renombré por "congruencia con `ChannelSpec`" sin preguntar. El
  converter se organiza por **unidad de ejecución**, no por feature: rompí el eje.
- **"milling/ = cabezal fresador".** Definición inventada por mí. La Sierra Vertical X vive en el
  cabezal PERFORADOR y hace el canal, que está en `milling/`.

En los cuatro casos el costo de preguntar era una pregunta. El costo de no preguntar fue
construir sobre una definición falsa y descubrirlo más tarde.

### Cómo preguntar

Nombrá la incongruencia concreta, decí las lecturas posibles y **cuál sería la consecuencia de
cada una**. No pidas "confirmame el nombre": mostrá qué cambia según la respuesta.

## 2. Ante un programa de Maestro: consultar PRIMERO la documentación

**Cuando trabajes con un programa de Maestro (una operación, un campo del `.pgmx`, la estructura
de un `Executable`), consultá la documentación antes de asumir nada o de pedirle a Fermín que te
lo explique.** Casi siempre la definición ya está escrita y validada.

Dónde mirar, en orden:

1. **`docs/synthesize_pgmx_help.md`** — la API de nuestro sintetizador: qué specs y builders hay,
   qué escribe cada uno en el `.pgmx`. `docs/pgmx_snapshot_help.md` es el lado de lectura.
2. **`iso/docs/experiments/<feature>.md`** — el mapa UI → `.pgmx` → ISO de la época nueva
   (serie R), con lo derivado y lo pendiente (ej. `programa_vacio.md`).
3. **`pgmx/docs/`** — el manual de referencia de SCM: `xilog_plus_pgm/` (editor Xilog Plus) y
   `maestro_scripting/` (API de scripting). Es la fuente sobre Maestro/Xilog mismo, no sobre
   nuestro código. `pgmx/docs/README.md` es el índice.

**La época anterior está congelada y NO se consulta durante la reinvestigación** (decisión
2026-08-07): los labs (`pgmx/machining_lab/*`, `iso/machining_lab/n0*`), los experimentos de la
serie N y el converter viejo viven en las ramas `iso_converter` y `respaldo/ejecucion-plan-f0-f3`.
La época nueva deriva su propia evidencia con la serie R; lo congelado no es fuente.

Por qué es regla: la definición correcta suele existir y contradecir lo que uno supondría. El Xn,
el Xmsg y el Park (Aparcamiento) son **tres operaciones distintas** con tipos serializados
distintos — `XnSpec` / `XmsgSpec` / `ParkSpec` ya en producción —; el converter viejo las venía
tratando como si "Xn" y "park" fueran lo mismo, y estaba documentado desde antes en el lab de
aparcamiento de la época anterior. Preguntar sin leer primero desperdicia el trabajo ya hecho, y
peor: invita a reinventarlo mal (ver la regla 1).

Si leíste y la documentación NO cubre el caso, o se contradice con lo que ves en un archivo real,
ESO sí es para traérselo a Fermín — nombrando qué doc miraste y qué no cerró.

## 3. La nomenclatura manda desde la UI de Maestro

Los nombres salen del vocabulario de la UI de Maestro (Fermín es quien la usa). Si en Maestro se
llama Galceado, no lo llamamos Squaring. Ver `iso/docs/experiments/` para el mapa
UI → .pgmx → ISO de cada feature.

Excepciones legítimas, que NO son incongruencias:
- **Nombres de Maestro en el XML** (`BottomAndSideFinishMilling`, `ContourFeature`,
  `DrillingOperation`): vienen del `.pgmx`. Intocables.
- **Conceptos compartidos** (`MillingDepthSpec`, `MillingStrategySpec`): no son features.
- **La tabla de alias de `_normalize_machining_order`**: ahí los alias SON la API (tolera plural,
  castellano y los nombres previos), no deuda.

## 4. Byte-idéntico o fail-loud. Nunca aproximar en silencio

El converter PGMX→ISO se valida **byte a byte** contra los ISO que produce Maestro. Si falta
evidencia para un caso, se RECHAZA con un mensaje que diga qué fixture falta — no se adivina.
Un default inventado es una hipótesis disfrazada: impide que el sistema note que no sabe.

**El convertidor no puede tener constantes internas para el cálculo de trazas.** Todo sale de la
config, del catálogo de herramientas o de la operación. Ver `converter_magic_numbers.md`.

## 5. Los fixtures: quién los hace, y por qué importa

- **Los genera el sintetizador** cuando la traza NO es la incógnita (el ISO es lo que se deriva).
- **Los hace Fermín en Maestro** cuando la traza ES la incógnita. Ejemplo: con
  `ActivateCNCCorrection=false` la trayectoria almacenada ya trae el offset — si yo la autorara,
  Maestro postprocesaría MI hipótesis y yo derivaría de mí mismo. Circular.

⚠️ **El corpus auto-generado tiene puntos ciegos por construcción.** Los 346 fixtures de
N001–N042 tienen todos `Xn` porque los escribía nuestro sintetizador; un `.pgmx` hecho a mano en
Maestro no lo trae, y ahí el footer es otro. Antes de confiar en que "el corpus lo cubre",
preguntate qué no puede contener por venir de nuestra propia autoría.

### El nombre de un fixture no es evidencia (2026-08-27)

Los archivos manuales pueden tener errores, **sobre todo en el nombre**: uno guardado con la
marca `HG` puede haber quedado en campo `A` porque el cambio no se aceptó antes de guardar.

- **Ninguna derivación cita un nombre de archivo. Cita el atributo leído del `.pgmx`.**
- Y por eso mismo **el nombre tiene que afirmar cuanto se pueda** — un nombre que afirma se
  puede atrapar mintiendo; `arco_07` no se puede chequear contra nada.
- **Un negativo sin testigo se escribe «probable», no «derivado».** Si lo que se varió no vive
  en el `.pgmx` (parámetros de máquina, ventana Opciones) y el ISO tampoco cambia, los archivos
  no pueden probar que la variación estaba puesta ⇒ ese fixture va **con captura de la ventana**.

Detalle, corpus y auditoría en `iso/docs/fixtures.md`.

## 6. Comunicación

En **español rioplatense** ("vos"), siempre.
