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

## 2. La nomenclatura manda desde la UI de Maestro

Los nombres salen del vocabulario de la UI de Maestro (Fermín es quien la usa). Si en Maestro se
llama Galceado, no lo llamamos Squaring. Ver `iso/docs/experiments/` para el mapa
UI → .pgmx → ISO de cada feature.

Excepciones legítimas, que NO son incongruencias:
- **Nombres de Maestro en el XML** (`BottomAndSideFinishMilling`, `ContourFeature`,
  `DrillingOperation`): vienen del `.pgmx`. Intocables.
- **Conceptos compartidos** (`MillingDepthSpec`, `MillingStrategySpec`): no son features.
- **La tabla de alias de `_normalize_machining_order`**: ahí los alias SON la API (tolera plural,
  castellano y los nombres previos), no deuda.

## 3. Byte-idéntico o fail-loud. Nunca aproximar en silencio

El converter PGMX→ISO se valida **byte a byte** contra los ISO que produce Maestro. Si falta
evidencia para un caso, se RECHAZA con un mensaje que diga qué fixture falta — no se adivina.
Un default inventado es una hipótesis disfrazada: impide que el sistema note que no sabe.

**El convertidor no puede tener constantes internas para el cálculo de trazas.** Todo sale de la
config, del catálogo de herramientas o de la operación. Ver `converter_magic_numbers.md`.

## 4. Los fixtures: quién los hace, y por qué importa

- **Los genera el sintetizador** cuando la traza NO es la incógnita (el ISO es lo que se deriva).
- **Los hace Fermín en Maestro** cuando la traza ES la incógnita. Ejemplo: con
  `ActivateCNCCorrection=false` la trayectoria almacenada ya trae el offset — si yo la autorara,
  Maestro postprocesaría MI hipótesis y yo derivaría de mí mismo. Circular.

⚠️ **El corpus auto-generado tiene puntos ciegos por construcción.** Los 346 fixtures de
N001–N042 tienen todos `Xn` porque los escribía nuestro sintetizador; un `.pgmx` hecho a mano en
Maestro no lo trae, y ahí el footer es otro. Antes de confiar en que "el corpus lo cubre",
preguntate qué no puede contener por venir de nuestra propia autoría.

## 5. Comunicación

En **español rioplatense** ("vos"), siempre.
