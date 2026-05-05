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

## Principio De Diseno

Eliminar la idea de transiciones por combinacion de tipo de mecanizado.

El generador nuevo debe sintetizar el ISO desde datos observados, estados
requeridos y diferenciales entre etapas, no desde una lista creciente de
patrones como `polilinea -> taladros laterales` o `ranura -> taladros`.

## Plan Tentativo

1. Leer completamente el `.pgmx`: dimensiones, origen, trabajos, herramientas,
   trazas, corrimientos, secuencias de trabajo y demas datos relevantes.
2. Establecer que parametros acompanan a la pieza propiamente y cuales
   pertenecen a cada trabajo a realizar.
3. Determinar que valores deben tener esos parametros en cada etapa de
   ejecucion segun lo indicado por el `.pgmx`.
4. Determinar la traza de cada mecanizado.
5. Definir que valores observados deben resetearse luego de cada ejecucion,
   dependiendo de la tarea ejecutada.
6. Calcular el diferencial de valores entre una etapa de ejecucion y la
   siguiente para sintetizar la transicion necesaria.
7. Construir el ISO completo con esos datos: parametros de pieza, parametros de
   trabajo, trazas, resets y diferenciales de estado.

## Reglas Iniciales

- Esta memoria empieza de cero por decision del usuario.
- La memoria vieja solo se consulta si el usuario pide traer un dato concreto.
- Las decisiones nuevas deben registrarse aca antes de modificar codigo.
- El primer resultado esperado no es codigo, sino una memoria revisada y
  depurada que sirva como contrato de trabajo para este entorno.

## Pendiente Inmediato

- Revisar esta memoria con el usuario antes de codificar.
- Definir la primera estructura interna del nuevo entorno solo despues de esa
  revision.
