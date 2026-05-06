# Machine Config Snapshot

Copia local de investigacion para `iso_state_synthesis`.

## Fuentes

- `S:\Xilog Plus` -> `snapshot/xilog_plus`
- `S:\Maestro\Cfgx` -> `snapshot/maestro/Cfgx`
- `S:\Maestro\Tlgx` -> `snapshot/maestro/Tlgx`

## Exclusiones

- `S:\Xilog Plus\Fxc` no se conserva en este snapshot. Se clasifica como
  biblioteca de plantillas/ciclos para usar dentro del software Xilog Plus, no
  como fuente directa de configuracion de maquina para este enfoque.

## Uso

Esta copia es la fuente de investigacion del nuevo enfoque por estado. Las
consultas sobre datos de maquina deben apuntar primero a esta carpeta para no
depender de `iso_generation/`.

Para datos de herramienta de un trabajo concreto, la fuente primaria no es este
snapshot sino el `def.tlgx` embebido dentro del propio `.pgmx`. Las copias
`snapshot/maestro/Tlgx/def.tlgx` y `snapshot/xilog_plus/Job/def.tlg` quedan como
respaldo/contraste de la instalacion local.

El archivo `snapshot/manifest.csv` registra ruta fuente, ruta relativa, tamano
y SHA256 de cada archivo copiado.
