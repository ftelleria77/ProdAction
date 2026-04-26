# Memoria auxiliar - Ventana Nuevo Modulo

## Objetivo

Diseñar la futura ventana `Nuevo Modulo` antes de tocar codigo de aplicacion.

Esta memoria funciona como espacio de cierre de idea: primero se definen alcance,
campos, validaciones y flujo esperado. Recién cuando la idea esté cerrada se
implementará en `app/ui.py`.

## Estado actual

- En la ventana del proyecto existe `Nuevo Local`, que crea la carpeta del local y su `local_config.json`.
- En la ventana `Local: ...` existe el botón `Nuevo Modulo`.
- Hoy `Nuevo Modulo` abre un dialogo simple que pide solo el nombre.
- Al confirmar:
  - crea la carpeta del modulo dentro del local;
  - crea un `module_config.json` base;
  - agrega el modulo a `self.project.modules`;
  - actualiza `local_config.json` y `project.json`;
  - refresca la lista del local.
- El boton `Abrir Modulo` esta deshabilitado si no hay una fila seleccionada.

## Problema a resolver

El dialogo actual es demasiado pobre: crea un modulo vacio sin permitir cargar
datos basicos que luego se configuran en la ventana de inspeccion del modulo.

La idea es que `Nuevo Modulo` sea una ventana propia, pero sin duplicar trabajo
ni crear una experiencia pesada para una accion frecuente.

## Cambio de enfoque

La necesidad principal no es cargar mas campos al crear un modulo vacio.

La necesidad real es tener una base de datos de modulos estandar prediseñados,
organizados en carpetas, para poder armar rapidamente un local completo.

Entonces `Nuevo Modulo` deberia evolucionar hacia un selector/insertador de
modulos estandar. Crear un modulo vacio seguiria siendo posible, pero dejaria
de ser el flujo principal.

## Ronda 2 - Biblioteca de modulos estandar

### Objetivo funcional

Permitir que el usuario arme un local eligiendo modulos predefinidos desde una
biblioteca organizada por categorias.

Ejemplos de categorias posibles:

- Bajos.
- Altos.
- Alacenas.
- Columnas.
- Placards.
- Cajoneras.
- Aplicados.
- Especiales.

Ejemplos de acciones esperadas:

- Insertar un modulo estandar en el local actual.
- Insertar varias unidades del mismo modulo.
- Renombrar el modulo al insertarlo.
- Ajustar cantidad.
- Ajustar medidas si el modulo lo permite.
- Abrir el modulo insertado para editar piezas/detalles.

### Estructura posible en disco

Crear una carpeta de biblioteca en la raiz del sistema, por ejemplo:

```text
module_library/
  Bajos/
    Bajo_2_puertas/
      module_template.json
      preview.svg
      programs/
      drawings/
    Bajo_cajonera/
      module_template.json
      preview.svg
      programs/
  Alacenas/
    Alacena_2_puertas/
      module_template.json
      preview.svg
      programs/
```

Alternativa: usar una biblioteca dentro de cada proyecto, pero por ahora parece
mas conveniente que sea global para poder reutilizarla entre obras.

### Archivo `module_template.json`

Cada modulo estandar deberia tener un archivo descriptor propio, separado del
`module_config.json` de un proyecto real.

Propuesta inicial:

```json
{
  "schema_version": 1,
  "template_id": "bajo_2_puertas",
  "name": "Bajo 2 puertas",
  "category": "Bajos",
  "description": "",
  "default_quantity": 1,
  "dimensions": {
    "x": 800,
    "y": 560,
    "z": 720
  },
  "settings": {
    "herrajes_y_accesorios": "",
    "guias_y_bisagras": "",
    "detalles_de_obra": ""
  },
  "pieces": [],
  "assets": {
    "programs_dir": "programs",
    "preview": "preview.svg"
  }
}
```

Notas:

- `pieces` podria copiar la misma estructura que hoy vive en `module_config.json`.
- Los `source` de las piezas deberian ser relativos a la carpeta del template.
- Al insertar el modulo en un local, el sistema copiaria programas/archivos
  necesarios y reescribiria los `source` para que apunten a la carpeta del nuevo modulo.
- `module_config.json` seguiria siendo el archivo del modulo ya instanciado en
  el proyecto, no el archivo maestro de biblioteca.

### Flujo desde `Local: ...`

El boton `Nuevo Modulo` podria abrir una ventana con:

- Arbol/categorias a la izquierda.
- Lista de modulos estandar al centro.
- Vista previa/detalle a la derecha.
- Campos de insercion abajo o a la derecha:
  - nombre final del modulo;
  - cantidad;
  - medidas editables si corresponde;
  - opcion `Crear vacio`.

Flujo minimo:

1. Usuario elige categoria.
2. Usuario selecciona modulo estandar.
3. El sistema propone un nombre.
4. Usuario confirma.
5. Se crea carpeta del modulo en el local.
6. Se crea `module_config.json` a partir del template.
7. Se copian assets necesarios.
8. Se refresca la lista del local.
9. El modulo nuevo queda seleccionado.

Flujo alternativo:

- Boton `Crear modulo vacio` para mantener el comportamiento actual.

### Armado rapido de local completo

Para armar un local completo, hay dos niveles posibles:

Nivel 1 - Insercion individual:

- Se elige un modulo estandar y se inserta.
- Se repite para cada modulo.
- Es simple y facil de implementar.

Nivel 2 - Carrito de modulos:

- El usuario va agregando modulos a una lista temporal.
- Ajusta nombres/cantidades.
- Confirma una sola vez.
- El sistema crea todo el local.
- Es mas potente, pero requiere mas diseño.

La memoria queda abierta para decidir si empezamos con Nivel 1 y dejamos Nivel 2
para una segunda etapa.

### Crear la biblioteca

Tambien hace falta definir como se cargan los modulos estandar.

Opciones:

1. Manual por carpeta:
   - el usuario crea carpetas y archivos `module_template.json`.
   - simple para desarrollar, menos comodo para usuario final.

2. "Guardar como modulo estandar" desde un modulo existente:
   - se toma un modulo ya armado;
   - se elige categoria y nombre;
   - se copia a `module_library`;
   - se normalizan rutas de programas.
   - parece el flujo mas natural.

3. Editor de biblioteca:
   - ventana dedicada para crear/editar/eliminar templates.
   - mas completo, pero mas trabajo.

Propuesta para primera etapa:

- Implementar importacion/creacion desde modulo existente con `Guardar como estandar`.
- Permitir lectura de carpetas ya existentes en `module_library`.

### Riesgos tecnicos

- Rutas de PGMX:
  - hay que evitar que un template apunte a una carpeta de un proyecto viejo.
  - conviene copiar programas al template y luego al modulo instanciado.

- Colores/materiales:
  - un modulo estandar puede tener colores genericos o colores reales.
  - hay que decidir si al insertar se conserva color o se adapta al proyecto.

- Nombres duplicados:
  - al insertar varias veces el mismo template en un local, hay que proponer
    nombres incrementales.

- Parametrizacion:
  - si un modulo cambia de ancho/alto/profundidad, no necesariamente alcanza con
    editar `settings.x/y/z`; las piezas tambien deberian recalcularse.
  - primera etapa podria manejar templates de medidas fijas.

- Programas CNC:
  - si las piezas cambian de medida, los programas asociados pueden dejar de ser validos.
  - primera etapa podria copiar modulos fijos sin recalculo automatico.

### Decision tecnica tentativa

Para una primera version robusta:

- Biblioteca global en `module_library/`.
- Templates de medida fija.
- Cada template es una carpeta autocontenida.
- Insertar template copia su carpeta/base al local.
- La ventana `Nuevo Modulo` funciona como selector de biblioteca.
- Se mantiene `Crear modulo vacio` como escape.

## Ronda 3 - Observacion de `S:\Maestro\Projects\01 - Mobile STD\01 - BM - Bajomesada`

Ruta observada:

```text
S:\Maestro\Projects\01 - Mobile STD\01 - BM - Bajomesada
```

### Lectura general

Esta carpeta ya funciona como una biblioteca real de modulos estandar.

No esta organizada con `module_template.json`, sino por convencion de carpetas
y archivos generados por el sistema actual de Maestro/Mobile.

Estructura general detectada:

```text
01 - BM - Bajomesada/
  01 - 1PD - 1 Puerta Derecha/
    01 - PC - Perfil C/
      BM-1PD-PC-300/
      BM-1PD-PC-350/
      ...
  02 - 1PI - 1 Puerta Izquierda/
    01 - PC - Perfil C/
      BM-1PI-PC-300/
      ...
  03 - 2P - 2 Puertas/
    01 - PC - Perfil C/
      BM-2P-PC-600/
      ...
    02 - FL - Faja L/
    03 - MA - Manijas/
  ...
```

Capas conceptuales:

1. Familia principal: `BM - Bajomesada`.
2. Tipo de modulo: `1PD`, `1PI`, `2P`, `3C`, etc.
3. Variante/acabado/sistema: `PC - Perfil C`, `FL - Faja L`, `MA - Manijas`.
4. Modulo concreto por medida: `BM-2P-PC-1000`, `BM-1PD-PC-300`, etc.

### Categorias observadas

```text
01 - 1PD - 1 Puerta Derecha      7 modulos hoja, 70 archivos
02 - 1PI - 1 Puerta Izquierda    7 modulos hoja, 70 archivos
03 - 2P - 2 Puertas             15 carpetas hoja, 143 archivos
04 - 3PD - 3Puertas ID+D         2 modulos hoja, 31 archivos
07 - 3C - 3 Cajones              2 carpetas hoja, 31 archivos
08 - BA - Bandejero Abierto      1 modulo hoja, 11 archivos
09 - ES - Especiero              2 modulos hoja, 46 archivos
```

Conteo de archivos por extension:

```text
303 .pgmx
33  .mixx
33  .csv
33  sin extension
```

Interpretacion:

- Hay 33 carpetas de modulo completo con descriptor sin extension + CSV + MIXX.
- Hay 303 programas `.pgmx`.
- Las carpetas sin descriptor completo parecen auxiliares o parametrizadas.

### Forma de un modulo completo

Ejemplo:

```text
03 - 2P - 2 Puertas/
  01 - PC - Perfil C/
    BM-2P-PC-1000/
      BM-2P-PC-1000
      BM-2P-PC-1000.csv
      BM-2P-PC-1000.mixx
      Estante.pgmx
      Faja-964-PC.pgmx
      Fondo.pgmx
      FondoF6.pgmx
      Lateral_Der.pgmx
      Lateral_Izq.pgmx
      Puerta_Der.pgmx
      Puerta_Izq.pgmx
```

Otro ejemplo:

```text
01 - 1PD - 1 Puerta Derecha/
  01 - PC - Perfil C/
    BM-1PD-PC-300/
      BM-1PD-PC-300
      BM-1PD-PC-300.csv
      BM-1PD-PC-300.mixx
      Estante.pgmx
      Faja-264-PC.pgmx
      Fondo.pgmx
      FondoF6.pgmx
      Lateral_Der.pgmx
      Lateral_Izq.pgmx
      Puerta_Der.pgmx
```

### Archivo sin extension

El archivo sin extension con el mismo nombre del modulo contiene lineas `P/...`
que listan los programas PGMX con rutas absolutas.

Ejemplo observado:

```text
P/"S:\...\BM-2P-PC-1000\Lateral_Izq.pgmx" -HG R=1 *MM /"DEF" C0 T0 V0
P/"S:\...\BM-2P-PC-1000\Faja frontal.pgmx" -HG R=2 *MM /"DEF" C0 T0 V0
```

Implicacion:

- Si copiamos un modulo a un proyecto real, este archivo queda con rutas
  absolutas al maestro viejo.
- Para usarlo como asset copiado, habria que regenerarlo o reescribir rutas.
- Para ProdAction probablemente alcance con usar el CSV + PGMX, no depender de
  este archivo sin extension.

### CSV del modulo

El `.csv` parece ser el descriptor mas util para ProdAction.

Ejemplo observado en `BM-2P-PC-1000.csv`:

```text
1FSX;F1;Lateral_Izq;1;0;742;580;18;BCO18;0;Lateral_Izq.pgmx;;;;;Lateral_Izq;;;;;BCO18
2FDX;F2;Lateral_Der;1;0;742;580;18;BCO18;0;Lateral_Der.pgmx;;;;;Lateral_Der;;;;;BCO18
3CP;T;Tapa;1;0;964;580;0;BCO00;0;Tapa.pgmx;;;;;Tapa;;;;;BCO00
```

Patron:

- Separador `;`.
- 21 columnas detectadas en la primera linea.
- Incluye tipo de pieza, nombre, cantidad, dimensiones, espesor, material,
  veta y archivo PGMX relativo.
- El campo de PGMX es relativo al directorio del modulo, por ejemplo
  `Lateral_Izq.pgmx`.

Esto es muy conveniente para importar como template.

### MIXX

Los `.mixx` empiezan con firma ZIP:

```text
50 4B 03 04 ...
```

Implicacion:

- Son contenedores comprimidos.
- No hace falta entenderlos para una primera etapa si el CSV + PGMX alcanza.
- Podrian copiarse como asset adicional para conservar compatibilidad externa.

### Carpetas especiales

Se detectaron hojas sin descriptor completo:

```text
03 - 2P - 2 Puertas\02 - FL - Faja L
03 - 2P - 2 Puertas\03 - MA - Manijas
07 - 3C - 3 Cajones\Parametricos
```

Observaciones:

- `02 - FL - Faja L` y `03 - MA - Manijas` aparecieron sin archivos.
- `Parametricos` contiene solo PGMX:
  - `Faja-764-PC.pgmx`
  - `FondoN1F6.pgmx`
  - `Fren_Cajon_SupN0.pgmx`
  - `Lar_Der_Cajon_SupN0.pgmx`
  - `Lat_Izq_Cajon_SupN0.pgmx`

Implicacion:

- La biblioteca debe distinguir entre:
  - modulos insertables completos;
  - carpetas auxiliares;
  - recursos parametrizados.

Para primera etapa conviene listar solo carpetas que tengan:

- archivo sin extension con el mismo nombre de carpeta;
- `.csv` con el mismo nombre;
- PGMX asociados.

### Deduccion para `Nuevo Modulo`

La ventana `Nuevo Modulo` no necesita inventar un formato nuevo desde cero.

Primera etapa recomendada:

- Elegir una raiz de biblioteca, inicialmente:
  `S:\Maestro\Projects\01 - Mobile STD`.
- Navegar por familias y categorias usando carpetas.
- Detectar como modulo insertable toda carpeta hoja que tenga:
  - `<nombre_modulo>.csv`;
  - PGMX referenciados desde ese CSV.
- Mostrar nombre/codigo/ancho a partir del nombre de carpeta.
- Al insertar:
  - crear carpeta del modulo en el local;
  - copiar PGMX necesarios;
  - leer CSV y generar `module_config.json`;
  - no copiar necesariamente `.mixx` ni archivo sin extension en primera etapa;
  - opcionalmente copiar `.mixx` y archivo sin extension como respaldo.

### Cambios a decisiones tentativas

La decision anterior de crear `module_template.json` queda en pausa.

Nueva decision tentativa:

- Usar la estructura existente de Maestro como fuente primaria.
- No exigir migracion inicial a `module_template.json`.
- Crear un adaptador/importador de modulo estandar desde carpeta Maestro.
- Mas adelante, si hace falta, generar un indice/cache propio para acelerar la UI.

## Ronda 4 - Base de datos parametrica de modulos y piezas

### Idea ampliada

La biblioteca no tiene por que limitarse a copiar modulos fijos. Podemos
estudiar los archivos existentes, extraer patrones y construir una base de
datos que permita sintetizar piezas y modulos a demanda.

El objetivo seria:

- reconocer que piezas componen cada tipo de modulo;
- deducir dimensiones desde parametros como ancho, alto y profundidad;
- conservar materiales, veta, cantos y programas asociados;
- analizar los PGMX para registrar perforaciones y fresados;
- insertar modulos completos sin que el usuario tenga que armar pieza por pieza.

### Fuentes de informacion

Primera lectura:

- El `.csv` del modulo es el mejor descriptor de despiece.
- Los `.pgmx` son la fuente de verdad para mecanizados.
- El archivo sin extension puede servir como indice adicional de programas, pero
  no conviene depender de el porque contiene rutas absolutas y algunas aparecen
  desactualizadas.
- El `.mixx` puede copiarse como respaldo, pero no parece necesario para la
  primera etapa de ProdAction.

Columnas utiles detectadas en CSV:

```text
0  id interno / codigo de linea
1  tipo de pieza
2  nombre de pieza
3  cantidad
5  dimension A
6  dimension B
7  espesor
8  material
9  veta
10 programa PGMX relativo
11-14 posibles cantos / materiales de borde
15 nombre base de pieza
20 material final repetido
```

Esto permite cargar una pieza casi directamente al modelo actual de ProdAction.

### Patrones por tipo de modulo

En los Bajomesada `PC - Perfil C` se ven reglas muy consistentes.

Para `1PD` y `1PI`:

```text
F1 Lateral_Izq       742 x 580 x 18
F2 Lateral_Der       742 x 580 x 18
T  Tapa              (W - 36) x 580 x 0
B  Fondo             (W - 0.9) x 580 x 18
R  Estante           (W - 36) x 547 x 18
A1/A2 Puerta         723.1 x (W - 3.9) x 18
S  Trasera           717 x (W - 16) x 3
D2 Faja frontal      70 x (W - 36) x 18, cantidad 2
```

La diferencia entre `1PD` y `1PI` no cambia la caja: cambia la puerta usada
(`Puerta_Der` o `Puerta_Izq`) y por lo tanto el programa/asimetria de herrajes.

Para `2P`:

```text
F1/F2 Laterales      742 x 580 x 18
T  Tapa              (W - 36) x 580 x 0
B  Fondo             (W - 0.9) x 580 x 18
R  Estante           (W - 36) x 547 x 18
A1 Puerta_Izq        723.1 x (W / 2 - 3.9) x 18
A2 Puerta_Der        723.1 x (W / 2 - 3.9) x 18
S  Trasera           717 x (W - 16) x 3
D2 Faja frontal      70 x (W - 36) x 18, cantidad 2
```

Para `3PD`:

```text
F1/F2 Laterales      742 x 580 x 18
B  Fondo             (W - 0.9) x 580 x 18
L  Tabique           742 x 90 x 18
R  Estante           (W / 2 - 18.4) x 547 x 18
M  Caballete         353 x 547 x 18
A1/A2 Puertas        723.1 x (W / 3 - 3.9) x 18
S  Trasera           717 x (W - 16) x 3
D2 Faja frontal      70 x (W - 36) x 18, cantidad 2
```

Para `3C`:

- Hay una subestructura de cajones inferiores y superiores.
- Las piezas usan prefijos como `DRAW1...` y `DRAW2...`, que conviene conservar
  como grupo/subconjunto.
- El modulo observado `BM-3C-PC-800` tiene 18 lineas:
  - frente/tapa de cajon inferior;
  - laterales, trasera, frente y fondo de cajon inferior;
  - dos cajones superiores con sus piezas repetidas;
  - caja del bajo con laterales, tapa, fondo, trasera y faja.
- Como solo hay un ancho observado para `3C`, las formulas de cajones deben
  quedar marcadas como tentativas hasta comparar mas ejemplos.

Para `ES - Especiero`:

```text
H  Tapa_Cajon        723.1 x (W - 3.9) x 18
Q/G Frente/Trasera   (W - 63.9) x 610 x 18
C1/C2 Laterales cajon 464 x 250/110 x 18
E  Fondo cajon inf   (W - 99) x 464 x 18
E  Fondo cajon sup   (W - 79) x 484 x 3
Caja base            mismas reglas generales de bajo: W - 36, W - 0.9, W - 16
```

Para `BA - Bandejero Abierto`:

- El nombre `BM-BA-PC-150-400` parece traer dos parametros: ancho 150 y
  profundidad 400.
- Solo hay un ejemplo observado; conviene tratarlo como template fijo hasta
  tener mas muestras.

### Fresados y operaciones CNC

Usando el parser actual de ProdAction sobre PGMX se pudo extraer:

- dimensiones reales de dibujo;
- caras del programa (`Top`, `Bottom`, `Left`, `Right`, etc.);
- perforaciones con posicion, diametro y profundidad;
- trayectorias de fresado como polilineas;
- fresados circulares cuando existan en el PGMX.

Ejemplos observados:

```text
BM-2P-PC-800 / Lateral_Izq
  20 operaciones: 16 perforaciones Top, 4 perforaciones Right
  3 trayectorias de fresado

BM-2P-PC-800 / Fondo
  8 perforaciones Top
  2 trayectorias de fresado

BM-2P-PC-800 / Puerta_Der
  6 perforaciones Top
  1 trayectoria de fresado

BM-3C-PC-800 / Lateral_Izq
  27 operaciones: 23 perforaciones Top, 4 perforaciones Right
  4 trayectorias de fresado

BM-2P-PC-800 / Faja-764-PC.pgmx
  12 operaciones
  5 trayectorias de fresado

BM-2P-PC-800 / FondoF6.pgmx
  16 perforaciones
  0 trayectorias de fresado
```

Lectura tecnica:

- Los PGMX contienen suficiente informacion para una base de datos de patrones
  CNC.
- Para sintetizar de verdad no alcanza con listar piezas: tambien hay que
  parametrizar operaciones por cara.
- En una primera etapa conviene copiar programas existentes y guardar su
  analisis como metadato.
- En una etapa posterior se podrian convertir perforaciones/fresados en reglas
  relativas a dimensiones, por ejemplo `x = W - 35`, `y = 37`, o `x = W / 2`.

### Problemas detectados en nombres de programas

Hay que resolver fuentes PGMX con cuidado.

Ejemplo:

- En `BM-2P-PC-800.csv`, la pieza `Faja frontal` referencia
  `Faja frontal.pgmx`.
- En la carpeta real aparece `Faja-764-PC.pgmx`, no `Faja frontal.pgmx`.
- El archivo sin extension tambien lista `Faja frontal.pgmx`, aunque ese nombre
  no existe en la carpeta observada.

Implicacion:

- El importador no debe fallar silenciosamente si el `source` del CSV no existe.
- Debe intentar resolucion por:
  1. ruta exacta del CSV;
  2. coincidencia insensible a mayusculas/minusculas;
  3. nombre base de pieza;
  4. patrones por tipo, por ejemplo `Faja-<ancho>-PC.pgmx`;
  5. PGMX locales listados en el archivo sin extension, usando solo el nombre de
     archivo y no la ruta absoluta.
- Todo PGMX no resuelto debe quedar reportado para que el usuario pueda revisar
  la biblioteca.

Tambien hay programas auxiliares no representados como pieza principal:

- `FondoF6.pgmx`;
- `FondoN1F6.pgmx`;
- `Lat_Izq_Cajon_InfN0F6.pgmx`;
- `Lar_Der_Cajon_SupN0F6.pgmx`;
- otros sufijos `F6`.

Estos deberian guardarse como programas asociados/auxiliares de una pieza, no
como piezas nuevas de corte, salvo que decidamos lo contrario.

### Base de datos propuesta

La base puede tener tres niveles.

Nivel 1 - Catalogo observado:

```text
LibrarySource
  root_path
  scanned_at

ModuleTemplateObserved
  id
  family_path
  type_code
  variant_code
  module_code
  nominal_width
  nominal_depth
  nominal_height
  csv_path
  source_folder
  mixx_path
  descriptor_path

ObservedPiece
  module_template_id
  row_code
  piece_type
  name
  quantity
  dim_a
  dim_b
  thickness
  material
  grain
  cnc_source
  edge_fields
```

Este nivel permite insertar modulos fijos rapidamente.

Nivel 2 - Recetas parametrizadas:

```text
ModuleRecipe
  type_code
  variant_code
  parameters: W, H, D, material_caja, material_frente

PieceRecipe
  piece_type
  name
  quantity_expr
  dim_a_expr
  dim_b_expr
  thickness_expr
  material_expr
  grain_expr
  source_pattern
  group_name
```

Este nivel permite sintetizar un despiece nuevo a partir de un ancho dado.

Nivel 3 - Patrones CNC:

```text
ProgramPattern
  piece_recipe_id
  source_pgmx
  face_dimensions
  operation_patterns
  milling_path_patterns
  auxiliary_programs

OperationPattern
  face
  operation_type
  x_expr
  y_expr
  diameter
  depth

MillingPathPattern
  face
  points_expr
  closed
```

Este nivel permitiria, mas adelante, sintetizar o adaptar programas CNC.

### Estrategia recomendada

No conviene saltar directamente a "generar todo" desde cero.

Propuesta por etapas:

1. `Importador de biblioteca Maestro`
   - Escanea carpetas.
   - Detecta modulos completos.
   - Lee CSV.
   - Resuelve PGMX.
   - Crea un indice/cache local.

2. `Nuevo Modulo desde biblioteca`
   - Muestra familias/tipos/medidas disponibles.
   - Inserta un modulo fijo copiando PGMX y creando `module_config.json`.
   - Ya permitiria armar un local completo mucho mas rapido.

3. `Analizador de familias`
   - Compara varios modulos del mismo tipo.
   - Deduce formulas como `W - 36`, `W / 2 - 3.9`, etc.
   - Propone recetas parametrizadas revisables.

4. `Sintesis de despiece`
   - El usuario elige tipo y medidas.
   - El sistema genera piezas segun receta.
   - Si no hay PGMX exacto, puede usar el mas cercano o marcar el programa como
     pendiente de generacion.

5. `Sintesis CNC`
   - Convertir patrones de perforaciones/fresados en reglas.
   - Generar PGMX nuevo o adaptar uno existente.
   - Esta etapa debe ser posterior porque tiene mas riesgo productivo.

### Decision tentativa actualizada

Para avanzar sin sobrecargar el sistema:

- La primera version debe ser una base observada/importada, no una sintesis CNC
  completa.
- El CSV debe ser la entrada principal para crear piezas.
- Los PGMX deben copiarse y analizarse, pero inicialmente seguir siendo
  programas existentes.
- Las formulas detectadas deben guardarse como propuesta/reporte, no aplicarse
  automaticamente hasta que validemos reglas por familia.
- La ventana `Nuevo Modulo` deberia empezar como selector de biblioteca, con
  posibilidad futura de `Crear desde receta parametrica`.

## Ronda 5 - Panel 3D en `Nuevo Modulo`

### Objetivo

La ventana `Nuevo Modulo` debe incluir un panel de visualizacion 3D para ver el
modulo seleccionado antes de insertarlo en el local.

La vista 3D tiene que ayudar a decidir rapido:

- tipo de modulo;
- ancho/profundidad/alto;
- cantidad y ubicacion general de puertas, cajones, estantes, fajas y laterales;
- sentido visual del modulo;
- posibles diferencias entre variantes similares.

No debe intentar reemplazar la inspeccion tecnica de pieza ni el dibujo CNC de
cada PGMX. Para eso siguen siendo mejores las vistas existentes de piezas y
fresados.

### Ubicacion en la ventana

Disposicion propuesta:

```text
Nuevo Modulo
---------------------------------------------------------------
Categorias / filtros | Modulos disponibles | Vista 3D + detalle
                     |                     |
                     |                     | [panel 3D]
                     |                     |
                     |                     | Medidas, piezas, avisos
---------------------------------------------------------------
Nombre final | Cantidad | Crear vacio | Insertar | Cancelar
```

La vista 3D queda a la derecha porque acompana a la seleccion. Cuando el usuario
cambia de modulo, se actualiza automaticamente.

En pantallas chicas, la vista podria estar en una solapa `Vista 3D` para no
aplastar la lista de modulos.

### Nivel visual de primera etapa

Primera version recomendada: modelo 3D esquematico.

Debe representar:

- caja exterior;
- laterales;
- tapa/base/fondo;
- puertas;
- cajones;
- estantes visibles;
- fajas;
- trasera opcional con transparencia;
- colores aproximados por material;
- veta sugerida con lineas sutiles si el dato esta disponible.

No hace falta modelar:

- perforaciones;
- bisagras;
- fresados;
- cantos reales;
- espesores perfectos de cada rebaje;
- herrajes pequenos.

La razon es practica: la vista 3D es para elegir el modulo, no para validar CNC.

### Datos necesarios

Para construir la vista 3D se puede partir de dos fuentes:

1. CSV del modulo observado:
   - piezas;
   - dimensiones;
   - cantidad;
   - material;
   - veta;
   - tipo de pieza.

2. Receta parametrizada, cuando exista:
   - tipo de modulo;
   - formulas de piezas;
   - reglas de posicion.

El CSV tiene dimensiones pero no trae posicion 3D directa. Por lo tanto hace
falta una capa de reglas de posicion por tipo de pieza.

### Reglas de posicion iniciales

Para bajomesada simples:

```text
F1 Lateral_Izq       plano vertical izquierdo
F2 Lateral_Der       plano vertical derecho
T  Tapa              plano horizontal superior/interior
B  Fondo             base/plano horizontal inferior
R  Estante           plano horizontal intermedio
S  Trasera           plano posterior fino
D1/D2 Fajas          frente superior/inferior segun nombre
A1 Puerta_Izq        frente izquierdo
A2 Puerta_Der        frente derecho
H  Tapa_Cajon        frente de cajon visible si material de frente
C1/C2 Laterales cajon piezas internas simplificadas o invisibles por defecto
G/Q Trasera/Frente cajon piezas de cajon internas simplificadas
E  Fondo cajon       fondo de cajon simplificado
```

Para primera etapa, si una pieza no tiene regla de posicion, se omite de la
geometria principal y se lista como `sin posicion 3D definida` en el detalle.

### Controles del panel

Controles minimos:

- rotar con arrastre;
- zoom con rueda;
- encuadrar/restablecer vista;
- selector de vista: frente, perspectiva, superior, lateral;
- alternar transparencia de puertas;
- alternar mostrar/ocultar piezas internas;
- indicador de cantidad de piezas representadas y omitidas.

No hace falta editar desde el 3D en la primera etapa.

### Tecnica posible con dependencias actuales

El proyecto ya tiene PySide6. En el entorno actual estan disponibles:

- `PySide6.QtOpenGLWidgets`;
- `PySide6.Qt3DCore`;
- `PySide6.Qt3DRender`;
- `PySide6.QtWebEngineWidgets`.

Rutas posibles:

1. `Qt3D` dentro de PySide6:
   - mas natural para una escena 3D real;
   - permite camara, luces, materiales y mallas;
   - sin agregar dependencia externa;
   - conviene verificar empaquetado si se distribuye la app.

2. `QOpenGLWidget` propio:
   - control total y pocas dependencias;
   - mas trabajo para camara, picking y textos;
   - util si Qt3D da problemas de compatibilidad.

3. `QWebEngineView` con Three.js:
   - visualmente muy potente;
   - requiere incluir Three.js local o depender de assets web;
   - mezcla una mini app web dentro de la app Qt.

Decision tentativa:

- Empezar con `Qt3D` si funciona estable en la instalacion real.
- Mantener un fallback 2D/isometrico en `QGraphicsView` si Qt3D no esta
  disponible.

### Modelo interno sugerido

Crear una representacion independiente de Qt:

```text
ModulePreviewModel
  width
  height
  depth
  pieces: list[PreviewPiece]

PreviewPiece
  name
  piece_type
  width
  height
  thickness
  material
  grain
  transform / position
  visible
  opacity
```

Ventajas:

- sirve para Qt3D, QOpenGL o fallback 2D;
- permite probar la conversion CSV -> 3D sin abrir ventanas;
- separa reglas de negocio de la interfaz.

### Flujo esperado

1. Usuario selecciona un modulo de biblioteca.
2. Se lee el CSV o cache del modulo.
3. Se genera `ModulePreviewModel`.
4. El panel 3D renderiza la escena.
5. Si el usuario cambia ancho/variante, la vista se recalcula.
6. Si faltan reglas de posicion, se muestran avisos discretos en el detalle.
7. Al insertar, el panel no escribe nada por si mismo: solo ayuda a elegir.

### Relacion con sintesis futura

El panel 3D puede convertirse en una pieza clave para validar recetas:

- si una formula de pieza esta mal, el modulo se vera mal;
- si falta una pieza esperada, la vista lo evidencia;
- si una puerta/cajon queda invertido, se detecta antes de insertar.

Pero la primera version debe ser tolerante: mostrar lo que entiende y reportar
lo que no entiende.

## Propuesta inicial de modulo vacio (en pausa)

Esta seccion queda como referencia para el flujo alternativo `Crear modulo
vacio`. La direccion principal paso a ser `Nuevo Modulo desde biblioteca`.

La ventana `Nuevo Modulo` podria pedir:

- Local destino.
- Nombre del modulo.
- Cantidad.
- Medidas nominales `X`, `Y`, `Z`.
- Herrajes y accesorios.
- Guias y bisagras.
- Detalles de obra.

Campos opcionales:

- Plantilla de modulo, si mas adelante existen presets.
- Crear y abrir automaticamente el modulo al guardar.

## Reglas de flujo

- Si se abre desde `Local: Nombre`, el local destino queda preseleccionado.
- Si solo hay un local disponible, no hace falta mostrar selector editable.
- Si hubiera multiples locales visibles, se puede mostrar un selector.
- Si el usuario cancela, no se crea carpeta ni config.
- Si confirma, se crea todo de una vez.
- Al terminar, la lista del local se refresca y el nuevo modulo queda seleccionado.

## Validaciones

- Nombre obligatorio.
- Nombre valido como carpeta de Windows:
  - no puede ser `.` ni `..`;
  - no puede terminar con espacio o punto;
  - no puede contener `< > : " / \ | ? *`.
- No puede existir otro modulo con el mismo nombre dentro del mismo local.
- No puede existir ya una carpeta con ese nombre en el local.
- Cantidad debe ser entero mayor o igual a 1.
- Medidas `X`, `Y`, `Z` pueden quedar vacias o ser numericas.

## Persistencia esperada

Al crear el modulo se deberia escribir `module_config.json` con:

```json
{
  "module": "Nombre",
  "path": "...",
  "generated_at": "...",
  "en_juego_layout": {},
  "en_juego_settings": {},
  "settings": {
    "x": "",
    "y": "",
    "z": "",
    "herrajes_y_accesorios": "",
    "guias_y_bisagras": "",
    "detalles_de_obra": ""
  },
  "pieces": []
}
```

Notas:

- `en_juego_settings` deberia usar los defaults reales existentes en codigo.
- Las dimensiones vacias deben persistir como cadena vacia para mantener compatibilidad con el flujo actual.
- La cantidad vive en `ModuleData.quantity` y en `local_config.json`, no dentro de `settings`.

## Diseño de interfaz

Opcion compacta:

- Ventana modal titulada `Nuevo Modulo`.
- Formulario de dos columnas.
- Botones inferiores `Crear` y `Cancelar`.
- Tamaño similar a un dialogo utilitario, no a la ventana grande de inspeccion.

Campos:

1. `Local`
2. `Nombre`
3. `Cantidad`
4. `X`
5. `Y`
6. `Z`
7. `Herrajes y accesorios`
8. `Guias y bisagras`
9. `Detalles de obra`

## Preguntas abiertas

- ¿La biblioteca debe ser global para todos los proyectos o propia de cada proyecto?
- ¿Empezamos con modulos de medida fija o necesitamos parametrizacion desde el primer dia?
- ¿Al insertar un modulo estandar debe copiar programas PGMX, dibujos SVG y otros assets?
- ¿Como deberia manejar colores/materiales: conservar, preguntar, o adaptar a tableros configurados?
- ¿Hace falta un modo "carrito" para crear varios modulos de una vez?
- ¿Queremos un boton `Guardar como modulo estandar` desde la ventana de inspeccion de modulo?
- ¿Debe abrir automaticamente la ventana de inspeccion del modulo despues de crearlo?
- ¿La cantidad deberia usar los mismos botones `+/-` que la inspeccion del modulo?
- ¿Conviene incluir desde el inicio campos de piezas, o eso debe seguir viviendo solo en `Abrir Modulo`?
- ¿El usuario espera poder crear varias piezas/modulos en cadena sin cerrar la ventana?
- ¿El nombre default debe seguir siendo `Aplicados`?
- ¿La vista 3D inicial debe ser esquematica o intentar reproducir espesores y
  posiciones reales desde el primer dia?
- ¿Conviene mostrar puertas cerradas por defecto o transparentes para ver
  estantes/cajones internos?
- ¿El panel 3D debe permitir editar medidas desde la vista o solo visualizar?

## Decisiones pendientes

- [ ] Ubicacion de la biblioteca: raiz Maestro configurable, cache local, o ambas.
- [ ] Formato definitivo del indice/cache de biblioteca.
- [ ] Templates fijos importados vs recetas parametricas.
- [ ] Flujo para crear recetas desde modulos existentes.
- [ ] Si `Nuevo Modulo` sera selector de biblioteca con opcion secundaria de modulo vacio.
- [ ] Campos definitivos de la ventana.
- [ ] Comportamiento posterior a crear: solo seleccionar, abrir modulo, o preguntar.
- [ ] Nivel de validacion visual: warnings modales o mensajes dentro de la ventana.
- [ ] Si se reutilizan controles actuales de cantidad/listas auxiliares o se dejan simples.
- [ ] Como resolver PGMX faltantes o con nombres divergentes.
- [ ] Si los programas `F6` se guardan como auxiliares asociados a una pieza.
- [ ] Cuando pasar de copiar PGMX existentes a sintetizar/adaptar PGMX.
- [ ] Tecnologia del panel 3D: Qt3D, QOpenGLWidget, QWebEngine/Three.js o
  fallback isometrico.
- [ ] Reglas iniciales de posicion por tipo de pieza.
- [ ] Nivel de detalle visual para puertas, cajones, estantes y fajas.

## No tocar todavia

- No modificar `app/ui.py` para esta idea hasta cerrar el diseño.
- No cambiar estructura de `module_config.json` salvo que se decida explicitamente.
- No mezclar esta memoria con el generador de diagramas de corte ni En-Juego.
