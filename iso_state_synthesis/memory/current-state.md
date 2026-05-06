# ISO State Synthesis

Nueva memoria de trabajo para redisenar la generacion ISO desde cero sin
arrastrar la arquitectura por patrones de `iso_generation/`.

Ultima actualizacion: 2026-05-05

## Alcance

- Dejar `iso_generation/` como esta.
- Trabajar en la rama `iso-state-synthesis` para no afectar el flujo principal
  del sistema.
- Crear un entorno nuevo para investigar y luego implementar el enfoque por
  estado, parametros y diferenciales.
- No traer por ahora contenido de la memoria vieja ni del contrato viejo.
- Usar los mismos archivos `.pgmx` e `.iso` de estudio como corpus de
  investigacion cuando haga falta evidencia.
- Antes de empezar a codificar, repasar esta memoria completa con el usuario y
  depurar los detalles que el usuario vea necesarios.

## Objetivo Del Enfoque

Construir un traductor `.pgmx -> .iso` que pueda explicar cada linea emitida
como consecuencia de una de estas fuentes:

- un dato de la pieza;
- un dato del trabajo indicado en el `.pgmx`;
- un dato de herramienta o maquina;
- un estado que debe estar activo para ejecutar una etapa;
- un reset necesario despues de una etapa;
- una regla observada y documentada contra pares `.pgmx/.iso`.

El objetivo no es coleccionar combinaciones como `perfil + taladros laterales`
o `ranura + taladros`, sino entender que estado requiere cada etapa y emitir el
diferencial entre el estado actual y el estado objetivo.

## Principio De Diseno

Eliminar la idea de transiciones por combinacion de tipo de mecanizado.

El generador nuevo debe sintetizar el ISO desde datos observados, estados
requeridos y diferenciales entre etapas, no desde una lista creciente de
patrones como `polilinea -> taladros laterales` o `ranura -> taladros`.

Una combinacion nueva deberia fallar solamente si falta conocer:

- que datos pide una etapa;
- que estado objetivo necesita;
- que reset deja al terminar;
- como pasar desde el estado anterior al nuevo.

No deberia fallar por no existir un caso global con nombre propio.

## Vocabulario Inicial

- `Estado actual`: mapa de valores que el ISO ya dejo activos en un punto del
  programa. Incluye valores de pieza, herramienta, cara/plano, offsets,
  correctores, seguridad, posicion y cualquier variable modal observada.
- `Estado objetivo`: mapa de valores que deben estar activos antes de ejecutar
  una etapa concreta.
- `Diferencial`: conjunto ordenado de lineas ISO necesarias para transformar el
  estado actual en el estado objetivo.
- `Etapa`: momento ejecutable del programa. Puede ser preparacion de pieza,
  preparacion de herramienta, aproximacion, corte, retirada, reset o cierre.
- `Trabajo`: mecanizado pedido por el `.pgmx`, con su herramienta, cara,
  geometria, profundidad, sentido, compensacion, entradas/salidas y parametros
  propios.
- `Traza`: geometria ejecutable de un trabajo una vez traducida a movimientos
  ISO. No incluye por si sola la preparacion modal.
- `Reset`: cambio de estado que Maestro o la CNC dejan como condicion esperada
  despues de una etapa. Puede ser explicito en ISO o implicito por una familia
  de trabajo.
- `Fuente`: origen que justifica un valor. Debe ser una ruta dentro del `.pgmx`,
  una configuracion de maquina, una constante observada o una regla todavia
  marcada como hipotesis.

## Capas De Estado

Para no mezclar todo en una misma bolsa, el estado se va a separar inicialmente
en estas capas:

- `pieza`: dimensiones, origen, area/campo de trabajo, nombre de programa y
  datos de cabecera.
- `maquina`: configuracion, limites, parqueos, seguridad y valores que no nacen
  de una pieza puntual.
- `herramienta`: seleccion, spindle, velocidad, avance, largo, radio, offsets y
  habilitaciones asociadas.
- `trabajo`: cara/plano, familia de mecanizado, profundidad, lado de
  compensacion, estrategia de entrada/salida y datos propios de la operacion.
- `movimiento`: posicion conocida, modo de avance, corrector activo, marco
  modal y condiciones necesarias para interpretar la traza.
- `salida`: lineas emitidas, lineas obligadas aunque no cambie un valor, y
  resets pendientes.

Estas capas son un punto de partida. Si un valor no entra bien en ninguna,
conviene marcarlo como `sin_clasificar` antes que forzarlo.

## Configuracion De Maquina

El entorno nuevo tiene su propia copia local de investigacion:

- `iso_state_synthesis/machine_config/snapshot/xilog_plus`, copiada desde
  `S:\Xilog Plus`, excluyendo `Fxc`;
- `iso_state_synthesis/machine_config/snapshot/maestro/Cfgx`, copiada desde
  `S:\Maestro\Cfgx`;
- `iso_state_synthesis/machine_config/snapshot/maestro/Tlgx`, copiada desde
  `S:\Maestro\Tlgx`.

El manifiesto vive en
`iso_state_synthesis/machine_config/snapshot/manifest.csv` y registra ruta
fuente, ruta relativa, tamano y SHA256.

A partir de esta decision, cuando se investiguen datos de maquina para este
enfoque se debe consultar primero esta copia local. Las rutas `S:` quedan como
fuente original para refrescar el snapshot, no como dependencia cotidiana del
analisis.

Decision: `Xilog Plus/Fxc` queda fuera del snapshot porque se considera
biblioteca de plantillas/ciclos del software Xilog Plus, no configuracion
directa de maquina.

## Reglas Iniciales

- Esta memoria empieza de cero por decision del usuario.
- La memoria vieja solo se consulta si el usuario pide traer un dato concreto.
- La investigacion nueva de datos de maquina debe usar la copia local propia de
  `iso_state_synthesis/machine_config/snapshot`, no el snapshot historico de
  `iso_generation/`.
- Las decisiones nuevas deben registrarse aca antes de modificar codigo.
- El primer resultado esperado no es codigo, sino una memoria revisada y
  depurada que sirva como contrato de trabajo para este entorno.
- Cada regla nueva debe registrar su evidencia minima: que `.pgmx` se miro, que
  `.iso` se comparo y que diferencia explica.
- Un valor puede quedar como `hipotesis`, pero no como verdad silenciosa.
- La salida nueva debe poder explicar por que emite una linea y tambien por que
  decide no emitirla.
- Los nombres internos deben describir estado y responsabilidad, no casos de
  combinacion.

## Metodo De Investigacion

1. Elegir un par `.pgmx/.iso` pequeno.
2. Separar manualmente el ISO en etapas.
3. Para cada etapa, anotar:
   - estado recibido;
   - estado objetivo;
   - diferencial emitido;
   - traza ejecutada;
   - reset producido;
   - fuente de cada valor.
4. Repetir con una pieza casi igual que cambie una sola variable.
5. Mover el valor explicado a una regla de estado solo cuando sobreviva a la
   comparacion entre variantes.

Este metodo busca evitar que una coincidencia puntual se convierta demasiado
pronto en arquitectura.

## Primer Experimento Propuesto

Antes de codificar, hacer una tabla de estados para una pieza minima y dos
variantes cercanas:

- una pieza con una unica operacion simple;
- una variante que cambie solo la posicion de la traza;
- una variante que cambie solo el origen de pieza;
- una comparacion linea por linea que separe datos de pieza, datos de trabajo y
  datos de maquina.

Resultado esperado del experimento:

- una lista corta de campos de estado confirmados;
- una lista de campos dudosos;
- una primera forma de tabla `estado actual -> estado objetivo -> diferencial`;
- una decision sobre la estructura inicial que recien entonces se va a codificar.

Primer documento creado:

- `iso_state_synthesis/experiments/001_top_drill_state_table.md`

Pares elegidos:

- base: `ISO_MIN_001_TopDrill_Base`
- cambio de traza: `ISO_MIN_002_TopDrill_Y60`
- cambio de origen: `ISO_MIN_006_TopDrill_OriginY10`

Decision de formato: la primera tabla vive en Markdown porque todavia es
material de discusion humana. Si el modelo se estabiliza, se pasa luego a CSV o
JSON para alimentar codigo.

## Preguntas Abiertas

- Que variables observadas son realmente estado modal y cuales son solo
  comandos repetidos por seguridad.
- Que resets dependen de la familia de herramienta y cuales dependen de la
  etapa exacta ejecutada.
- Como representar una linea ISO obligatoria aunque su valor coincida con el
  estado actual.
- Como distinguir entre posicion fisica conocida y posicion logica suficiente
  para emitir el proximo bloque.
- Que nivel de detalle del `.pgmx` conviene conservar crudo para no perder
  evidencia.
- Como registrar una regla que funciona para el corpus actual pero todavia no
  esta demostrada causalmente.

## Plan Tentativo

1. Revisar y aprobar esta memoria como contrato inicial.
2. Armar el primer experimento manual de tabla de estados.
3. Definir el formato de evidencia y de tabla antes de escribir codigo.
4. Crear la primera estructura interna del entorno.
5. Implementar lectura de evidencia sin emitir ISO.
6. Implementar calculo de estados objetivo para un caso minimo.
7. Implementar el diferencial y comparar contra Maestro solo para ese caso.
8. Ampliar por capas de estado, no por combinaciones de mecanizados.

## Pendiente Inmediato

- Revisar esta memoria con el usuario antes de codificar.
- Revisar el experimento `001_top_drill_state_table.md` con el usuario.
- Decidir si la tabla manual ya alcanza para crear la primera estructura
  interna o si falta abrir una segunda pieza minima.
