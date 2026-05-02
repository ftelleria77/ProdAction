# Memoria actual - Trazabilidad CNC de proyectos

## Objetivo

Reformular el antiguo visualizador CNC como una herramienta auxiliar de
trazabilidad de ejecucion de proyectos.

El subsistema debe ayudar al operador del CNC a:
- abrir o seleccionar un proyecto de ProdAction;
- ver locales, modulos y piezas/programas de mecanizado;
- ver la estructura de salida generada junto con las planillas de produccion;
- ver archivos `.iso` postprocesados listos para enviar al CNC;
- previsualizar la pieza/programa que se va a mecanizar;
- vaciar la carpeta `USBMIX` controlada del CNC;
- copiar de a uno los `.iso` a `USBMIX` para ejecutar;
- registrar el avance real de la tarea de mecanizado;
- persistir ese avance para poder cerrar y volver a abrir la herramienta sin
  perder estado.

Este documento conserva la memoria historica y el estado de trabajo del
subsistema. El contrato estable resumido vive en
`cnc_traceability/docs/contract.md`.

## Restriccion critica

El visualizador debe poder correr como ejecutable en Windows XP 32 bits.

Consecuencias tecnicas:
- el ejecutable principal actual de ProdAction usa `PySide6` y Python moderno;
  ese stack no es compatible con Windows XP 32 bits.
- el visualizador CNC debe pensarse como subsistema separado, con dependencias
  minimas y compatibles con XP.
- no debe depender de Qt moderno, WebView moderno, navegadores embebidos ni
  librerias que exijan Windows 7+.
- el build debe producir un ejecutable 32 bits.
- queda pendiente validar en la PC real del CNC:
  - version de Windows XP;
  - permisos de escritura;
  - disponibilidad de red/unidades compartidas;
  - resolucion de pantalla;
  - si se puede copiar un runtime adicional o debe ser un unico ejecutable /
    carpeta portable.

## Separacion respecto de la aplicacion principal

El visualizador CNC no debe reemplazar la aplicacion principal.

La aplicacion principal seguira siendo responsable de:
- crear proyectos;
- escanear estructura `project -> local -> module`;
- sintetizar o reparar `.pgmx`;
- generar documentos de produccion;
- generar o estudiar `.iso`.

El visualizador CNC debe ser una herramienta de piso/planta:
- abrir datos ya generados;
- mostrar informacion operativa;
- preparar el proximo `.iso` a ejecutar en `USBMIX`;
- registrar avance;
- evitar cambios destructivos sobre el proyecto.

## Fuentes de datos existentes

Estructura actual relevante:
- `projects_list.json`
  - registro local de proyectos conocidos.
  - entradas observadas:
    - `project_name`
    - `client_name`
    - `source_folder`
    - `project_data_file`
- `project.json`
  - snapshot principal del proyecto dentro de `source_folder`.
  - contiene nombre, cliente, locales y datos reconstruidos por la app.
- `local_config.json`
  - archivo por local.
  - contiene listado de modulos del local, rutas relativas y dimensiones
    nominales.
- carpetas de modulos
  - contienen archivos `.pgmx`, `.csv` y posiblemente salidas asociadas.
- futuras salidas `.iso`
  - el sistema principal genera, junto con las planillas de produccion, una
    estructura de carpetas identica a la del proyecto: proyecto, locales y
    modulos.
  - en esa estructura se volcaran los archivos `.iso` postprocesados para el
    CNC.
  - esa estructura de salida debe ser fuente principal del visualizador CNC.
- carpeta `USBMIX`
  - existe en la PC del CNC.
  - es la carpeta desde la cual el CNC carga el programa `.iso` para ejecutar.
  - debe contener un unico archivo por ejecucion.
  - el visualizador debe poder vaciarla y copiar alli un unico `.iso`
    seleccionado.

Reglas de datos ya establecidas en el sistema:
- preservar la jerarquia `project -> local -> module`;
- no identificar modulos solo por nombre, porque puede haber nombres repetidos;
- usar ruta relativa como clave estable de modulo cuando sea posible;
- cada local mantiene su propio resumen en `local_config.json`.
- la estructura generada por `Generar Planillas` debe conservar la misma
  jerarquia para que el operador trabaje con carpetas familiares.

## Indice publicado por el sistema principal

El sistema principal puede determinar el orden de proyectos para mecanizado y
registrarlo en un archivo accesible por el subsistema CNC.

Objetivo del archivo:
- ser el punto de entrada del visualizador al iniciar;
- listar los proyectos disponibles en el orden de trabajo definido desde
  ProdAction;
- indicar donde esta la carpeta original del proyecto;
- indicar donde esta la estructura de salida CNC generada junto con las
  planillas;
- permitir abrir locales y modulos sin que el operador tenga que buscar
  manualmente carpetas.

Nombre propuesto del archivo:
- `cnc_project_viewer_index.json`
- o `prodaction_cnc_queue.json`

Ubicacion propuesta:
- una carpeta compartida accesible por la PC del CNC;
- o la misma raiz donde se generan las estructuras CNC de salida;
- la ruta exacta debe quedar configurable en el sistema principal y en el
  visualizador.

Responsabilidad del sistema principal:
- crear/actualizar este indice cuando se generan las planillas y la estructura
  CNC;
- permitir reordenar proyectos si el flujo de produccion lo requiere;
- guardar rutas absolutas o rutas resolubles desde la PC CNC;
- conservar el orden seleccionado por el usuario.

Responsabilidad del visualizador CNC:
- leer el indice al iniciar;
- mostrar proyectos en el orden publicado;
- permitir abrir cada proyecto, sus locales y modulos;
- detectar si una ruta ya no existe y mostrar advertencia;
- no reescribir el orden salvo que se defina explicitamente una funcion futura
  de reordenamiento desde el CNC.

Campos minimos propuestos:
- `format_version`;
- `updated_at`;
- `projects`, como lista ordenada;
- por proyecto:
  - `project_id` o clave estable;
  - `project_name`;
  - `client_name`;
  - `source_folder`;
  - `project_data_file`;
  - `cnc_output_root`;
  - `production_pdf_paths` opcional;
  - `locales`, con nombre, ruta relativa y orden;
  - `modules`, con nombre, local, ruta relativa y orden;
  - `status_hint` opcional.

Regla importante:
- el indice publicado no reemplaza el archivo de avance.
- el indice dice que existe y en que orden debe verse.
- `cnc_progress.json` registra que hizo el operador: copias a `USBMIX`,
  mecanizados, problemas y observaciones.

## Flujo operativo CNC requerido

Flujo minimo esperado:
1. El operador abre el visualizador.
2. El visualizador lee el indice publicado por el sistema principal si esta
   configurado.
3. El operador selecciona un proyecto del orden publicado, o manualmente una
   estructura de salida CNC si el indice no esta disponible.
4. Navega por proyecto, local y modulo.
5. Selecciona una pieza/programa `.iso` pendiente.
6. El visualizador muestra una vista previa de la pieza que se va a mecanizar.
7. El operador prepara la ejecucion:
   - el visualizador confirma la carpeta `USBMIX` configurada;
   - vacia `USBMIX`;
   - copia solo el `.iso` seleccionado a `USBMIX`;
   - verifica que en `USBMIX` quede un unico archivo.
8. El operador ejecuta el programa desde el CNC.
9. Al finalizar, el operador marca la pieza/programa como mecanizada.
10. El avance queda persistido.

Reglas de seguridad para `USBMIX`:
- la ruta de `USBMIX` debe estar configurada explicitamente.
- antes de vaciar la carpeta, el programa debe mostrar la ruta completa.
- solo se debe vaciar la carpeta configurada como `USBMIX`, nunca una ruta
  calculada ambiguamente.
- conviene limitar el borrado a archivos de ejecucion conocidos, inicialmente
  `.iso`, salvo que el usuario confirme otra politica.
- antes de copiar, verificar que el `.iso` fuente exista y sea legible.
- despues de copiar, verificar que `USBMIX` contenga exactamente un archivo
  ejecutable para el CNC.
- si no se puede limpiar o copiar, no marcar nada como mecanizado.
- el marcado como mecanizado debe ser accion manual posterior a la ejecucion,
  no consecuencia automatica de copiar el archivo.

## Persistencia del avance CNC

El avance del operador no debe escribirse mezclado en archivos generados por
Maestro si no es necesario.

Formato propuesto pendiente de implementacion:
- archivo por proyecto, por ejemplo:
  - `cnc_progress.json`
  - o `prodaction_cnc_progress.json`
- ubicacion preferida inicial:
  - dentro de la carpeta raiz del proyecto, junto a `project.json`;
  - si la PC CNC no puede escribir alli, permitir elegir una carpeta local de
    estado.

Campos minimos a persistir:
- version del formato;
- fecha/hora de ultima modificacion;
- proyecto:
  - nombre;
  - ruta raiz;
  - archivo `project.json` usado como fuente;
- estado por local;
- estado por modulo;
- estado por pieza/programa cuando se pueda identificar;
- ruta relativa del `.iso` fuente dentro de la estructura de salida;
- nombre del archivo copiado a `USBMIX`;
- fecha/hora de copia a `USBMIX`;
- fecha/hora de marcado como mecanizado;
- usuario/operador opcional;
- observaciones libres;
- historial simple de eventos o, al menos, marca de ultima modificacion.

Estados operativos iniciales:
- `pendiente`;
- `en_proceso`;
- `completado`;
- `pausado`;
- `observado` o `con_problema`;
- `copiado_a_usbmix`;
- `mecanizado`;
- `omitido` / `no_aplica` si hace falta.

El sistema debe tolerar:
- modulos agregados despues de haber creado el archivo de avance;
- modulos eliminados o movidos;
- nombres repetidos;
- archivos faltantes;
- rutas de red temporalmente no disponibles.
- archivos `.iso` que aparecen despues de creado el estado inicial.
- una carpeta `USBMIX` que queda con archivos inesperados de una ejecucion
  anterior.

## Experiencia de usuario esperada

Pantalla principal:
- lista de proyectos disponibles segun el indice publicado;
- boton para abrir carpeta/estructura manual si no existe indice;
- datos visibles:
  - proyecto;
  - cliente;
  - locales;
  - modulos por local;
  - avance total;
  - modulos pendientes / completos / con problema.

Vista de local:
- lista de modulos del local;
- estado de cada modulo;
- cantidad de piezas o programas asociados cuando este dato este disponible;
- filtro por estado.

Vista de modulo:
- nombre del modulo;
- ruta relativa;
- dimensiones nominales si existen;
- piezas/programas detectados;
- archivos `.iso` disponibles dentro del modulo;
- vista previa de la pieza/programa seleccionado;
- botones simples de estado:
  - iniciar;
  - preparar en USBMIX;
  - completar;
  - pausar;
  - marcar problema;
  - agregar observacion.

Vista de preparacion CNC:
- pieza/programa seleccionado;
- ruta del `.iso` fuente;
- ruta configurada de `USBMIX`;
- contenido actual de `USBMIX`;
- accion para vaciar y copiar el `.iso` seleccionado;
- confirmacion de que quedo un unico archivo en `USBMIX`;
- accion separada para marcar como mecanizado despues de la ejecucion.

Requisitos de operacion CNC:
- controles grandes y legibles;
- no depender de atajos de teclado complejos;
- confirmacion antes de marcar un lote grande como completo;
- mostrar claramente si el archivo de avance se guardo;
- mostrar claramente que archivo esta actualmente cargado en `USBMIX`;
- recuperarse bien despues de cerrar la app o reiniciar la PC;
- funcionar sin internet.

Vista previa de pieza:
- debe permitir al operador confirmar visualmente que el programa seleccionado
  corresponde a la pieza correcta antes de copiarlo a `USBMIX`.
- fuente primaria:
  - levantar la imagen desde la carpeta original del proyecto, del mismo modo
    que la ventana de edicion de pieza del sistema principal.
  - la ventana de edicion resuelve la pieza desde `source` / `cnc_source`,
    genera o reutiliza un SVG junto al modulo original y lo muestra como vista
    previa.
  - el flujo principal `Generar Planillas` ya llama a
    `generate_project_piece_drawings(...)`, por lo que en condiciones normales
    deberian existir SVG por pieza junto a los modulos originales.
- mapeo esperado:
  - el operador trabaja en la estructura de salida CNC;
  - esa estructura replica `project -> local -> module`;
  - usando la ruta relativa del `.iso` dentro de la estructura de salida, el
    visualizador debe encontrar el modulo equivalente en la carpeta original
    del proyecto;
  - desde ese modulo original debe buscar la imagen/SVG de la pieza.
- fallback:
  - si no hay SVG disponible, mostrar texto con modulo, pieza, dimensiones y
    ruta del `.iso`;
  - opcionalmente indicar que la imagen debe regenerarse desde el sistema
    principal;
  - la falta de imagen no debe bloquear la ejecucion, pero debe quedar visible
    como advertencia.

## Compatibilidad Windows XP 32 bits

Requisitos de build a validar antes de implementar:
- elegir tecnologia compatible con XP 32 bits.
- evitar dependencias modernas.
- generar un paquete portable o instalador simple.
- probar en una VM o equipo real XP 32 bits antes de entregar.

Opciones tecnicas a evaluar:
- Python antiguo compatible con XP + Tkinter + empaquetado compatible.
- Lazarus/Free Pascal con GUI Win32.
- C/C++ Win32 nativo.
- .NET Framework antiguo/WinForms si la PC CNC ya lo tiene instalado.

Decision pendiente:
- seleccionar stack definitivo despues de conocer limitaciones reales de la PC
  del CNC.

## Integracion con ProdAction

El visualizador debe leer datos de ProdAction, pero mantener bajo acoplamiento.

Preferencias iniciales:
- leer el indice publicado por el sistema principal si existe;
- leer `projects_list.json`, `project.json` y `local_config.json`;
- leer la estructura de salida CNC generada por `Generar Planillas`;
- detectar `.iso` dentro de esa estructura;
- mapear cada `.iso` de salida contra el modulo original por ruta relativa;
- buscar previews en la carpeta original del modulo antes de intentar cualquier
  generacion local;
- no importar `PySide6`;
- no requerir pandas/openpyxl/cairosvg;
- evitar usar modulos de la app principal si eso arrastra dependencias no
  compatibles con XP;
- si se reutiliza logica, extraer helpers puros y sin dependencias modernas.

Contrato de lectura:
- si existe `cnc_project_viewer_index.json` o equivalente, usarlo como fuente
  de orden de proyectos y rutas principales.
- si existe `project.json`, usarlo como fuente primaria.
- si existe `local_config.json`, usarlo para local/modulo.
- si faltan snapshots, permitir escaneo basico de carpetas.
- si existe una estructura de salida CNC, usarla para encontrar `.iso` y
  relacionarlos por ruta relativa con local/modulo.
- para preview, usar primero el SVG ya existente en la carpeta original del
  modulo, generado por el sistema principal.
- si no se encuentra el SVG, no asumir que el `.iso` contiene informacion
  suficiente para dibujar la pieza.

Contrato de escritura:
- escribir solo el archivo de avance CNC.
- no modificar `.pgmx`, `.csv`, `project.json` ni `local_config.json` salvo que
  se defina explicitamente una funcion futura para sincronizar.
- no modificar los `.iso` fuente de la estructura de salida.
- copiar `.iso` hacia `USBMIX` es una accion permitida.
- vaciar `USBMIX` es una accion permitida solo sobre la ruta configurada y con
  guardas de seguridad.

## Preguntas abiertas

- Cual sera el flujo exacto del operador:
  - por modulo;
  - por pieza;
  - por archivo `.iso`;
  - por placa / tanda de mecanizado.
- Que unidad de avance importa mas para el CNC:
  - modulo completo;
  - pieza individual;
  - programa ISO;
  - cantidad de repeticiones.
- Si alcanza con usar siempre previews generadas por la app principal o si hace
  falta una generacion local compatible con XP como respaldo.
- Como mapear con certeza el nombre de archivo `.iso` al `source/cnc_source` de
  la pieza cuando el postprocesado cambie el nombre.
- Que formato y ubicacion final debe tener el indice publicado por el sistema
  principal.
- Si el visualizador debe permitir reordenar proyectos o solo consumir el orden
  definido desde el sistema principal.
- Como se identifica una pieza/programa ya mecanizado cuando hay copias o
  repeticiones.
- Se necesita soporte multioperador o solo una PC CNC.
- El archivo de avance debe imprimirse/exportarse.
- El estado debe mostrarse tambien en la app principal de ProdAction.
- Donde conviene guardar el estado si el proyecto esta en una unidad de red
  lenta o con permisos limitados.
- Como se configura la ruta exacta de `USBMIX` en cada CNC.
- Si `USBMIX` puede contener archivos auxiliares que no deben borrarse.
- Si al copiar el `.iso` se debe conservar el nombre original o normalizarlo a
  un nombre fijo para el CNC.

## Fuera de alcance inicial

No implementar en la primera version:
- edicion de proyectos;
- generacion de `.pgmx`;
- generacion de `.iso`;
- nesting;
- visualizacion 3D;
- conexion directa con la CNC;
- sincronizacion en tiempo real entre varias PCs;
- cambios destructivos en archivos de produccion;
- borrado fuera de la carpeta `USBMIX` configurada.

## Primer plan de implementacion propuesto

1. Confirmar ambiente real de la PC CNC:
   - Windows XP 32 bits;
   - resolucion;
   - permisos;
   - acceso a unidades `S:` / `P:` u otras rutas reales.
2. Definir tecnologia de ejecutable compatible.
3. Crear un prototipo minimo que:
   - lea el indice publicado por el sistema principal;
   - muestre proyectos en el orden publicado;
   - abra la estructura de salida CNC generada por las planillas;
   - lea `project.json` / `local_config.json` cuando esten disponibles;
   - muestre locales y modulos;
   - liste `.iso` por local/modulo;
   - muestre una vista previa o fallback textual de la pieza;
   - permita configurar `USBMIX`;
   - vacie `USBMIX` y copie un unico `.iso`;
   - permita marcar pieza/programa como pendiente/en proceso/copiado a
     USBMIX/mecanizado/con problema;
   - guarde `cnc_progress.json`.
4. Probar apertura/cierre y recuperacion de estado.
5. Recien despues agregar piezas/programas y filtros avanzados.

## Implementacion inicial

Primer prototipo creado:
- `cnc_traceability/viewer_xp.py`

Decision tecnica inicial:
- usar Tkinter y solo libreria estandar de Python;
- mantener el visualizador separado de la aplicacion PySide6 principal;
- evitar `pathlib`, anotaciones de tipos, `dataclasses`, f-strings y APIs
  modernas para facilitar un runtime 32 bits compatible con Windows XP;
- apuntar inicialmente a Python antiguo compatible con XP, a validar entre
  Python 2.7 y Python 3.4 segun el empaquetado disponible.

Funcionalidad del primer prototipo:
- abre un indice JSON publicado por el sistema principal;
- tambien permite abrir manualmente una estructura CNC;
- lista proyectos en el orden del indice;
- escanea archivos `.iso` dentro de la carpeta CNC;
- agrupa visualmente por local y modulo segun la ruta relativa;
- guarda avance en `cnc_progress.json`;
- permite marcar estados iniciales:
  - `pendiente`;
  - `en_proceso`;
  - `con_problema`;
  - `mecanizado`;
  - `copiado_a_usbmix`;
- permite configurar carpeta `USBMIX`;
- prepara `USBMIX` borrando solo `.iso` existentes, copiando un unico `.iso`
  seleccionado y verificando que la carpeta quede con un solo archivo.

Guarda de seguridad implementada:
- si `USBMIX` contiene archivos que no son `.iso`, el prototipo no los borra y
  no copia el nuevo archivo;
- si el `.iso` fuente no existe, no copia ni cambia estado;
- copiar a `USBMIX` marca `copiado_a_usbmix`, pero no marca `mecanizado`;
- `mecanizado` sigue siendo una accion manual posterior.

Vista previa:
- el prototipo busca imagenes junto al modulo original usando la ruta relativa
  del `.iso`;
- intenta mostrar formatos simples soportados por Tkinter (`.gif`, `.png`,
  `.ppm`, `.pgm`) cuando el runtime los soporte;
- si encuentra `.svg`, lo informa como vista previa disponible, pero no lo
  renderiza dentro del runtime XP para evitar dependencias modernas;
- queda pendiente decidir si el sistema principal debe exportar previews
  `.gif` o `.png` compatibles con XP junto con los `.svg`.

Validacion realizada:
- `py -3 -m py_compile cnc_traceability\viewer_xp.py`;
- prueba de helpers con carpeta temporal:
  - normalizacion de indice;
  - escaneo de `.iso`;
  - extraccion de local/modulo desde ruta relativa;
  - actualizacion de estado en memoria.

## Separacion de ventanas

Decision de flujo:
- la ventana principal del subsistema es `Proyectos`;
- esa ventana se llena automaticamente con la lista y el orden de proyectos
  publicados en el indice del sistema principal;
- abrir un proyecto no reemplaza la ventana principal: abre una segunda ventana
  independiente.

Ventana de proyecto:
- titulo: `Proyecto: [nombre del proyecto - cliente]`;
- muestra una lista continua con formato de planilla;
- divide visualmente por locales con encabezamientos horizontales;
- dentro de cada local, agrupa por modulo;
- cada fila corresponde inicialmente a un programa `.iso`;
- columnas iniciales:
  - casilla de verificacion;
  - nombre de la pieza;
  - dimensiones;
  - archivo `.ISO` asociado;
  - observaciones.

Comportamiento de la planilla:
- la casilla de verificacion marca la fila como `mecanizado`;
- desmarcarla devuelve la fila a `pendiente`;
- las observaciones se guardan en `cnc_progress.json`;
- el nombre del archivo `.ISO` se muestra como accion clickeable;
- al hacer click sobre el `.ISO`, se abre una tercera ventana de visualizacion
  de la pieza/programa.

Ventana de visualizacion de pieza:
- muestra la vista previa o fallback textual;
- muestra pieza, dimensiones, local, modulo, ruta del ISO, estado y
  observaciones;
- conserva acciones operativas:
  - preparar en `USBMIX`;
  - marcar como mecanizado;
  - marcar problema.

Mapeo de pieza para la planilla:
- el prototipo busca `module_config.json` en el modulo original equivalente al
  modulo de salida CNC;
- intenta asociar el `.iso` por nombre de archivo contra:
  - `id`;
  - `name`;
  - `source`;
  - `cnc_source`;
  - `f6_source`;
- si encuentra la pieza, usa su nombre, dimensiones y observaciones base;
- si no puede asociarla, usa el nombre base del `.iso` como fallback.

Validacion adicional:
- `py -3 -m py_compile cnc_traceability\viewer_xp.py`;
- prueba con carpeta temporal que confirma:
  - lectura de `.iso`;
  - agrupacion por local/modulo;
  - asociacion contra `module_config.json`;
  - carga de nombre de pieza, dimensiones y observaciones.

## Reorganizacion Como Subsistema - 2026-05-02

Se separo el subsistema de trazabilidad CNC en:

`cnc_traceability/`

Nueva estructura:

- `cnc_traceability/viewer_xp.py`
  - aplicacion XP-compatible basada en Tkinter y libreria estandar.
- `cnc_traceability/config/cnc_project_viewer_settings.json`
  - configuracion local inicial.
- `cnc_traceability/README.md`
  - entrada corta al subsistema.
- `cnc_traceability/docs/contract.md`
  - contrato estable de responsabilidades, datos y reglas de seguridad.
- `cnc_traceability/memory/current-state.md`
  - esta memoria historica.

Lectura de producto:

- ya no se trata como un script suelto para visualizar ISO;
- se lo define como herramienta auxiliar para registrar trazabilidad de
  ejecucion en la PC del CNC;
- sigue separado de la app principal porque debe conservar compatibilidad con
  Windows XP 32 bits.

Cambio tecnico aplicado:

- la configuracion pasa a buscarse en una carpeta `config/` junto al ejecutable
  o junto al script en desarrollo;
- el titulo principal de la ventana pasa a `Trazabilidad CNC`;
- el titulo de aplicacion pasa a `ProdAction CNC - Trazabilidad`.
