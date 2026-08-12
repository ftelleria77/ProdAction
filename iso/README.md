# iso — Conversión PGMX → ISO (época de reinvestigación)

Paquete de la investigación para el convertidor de archivos `.pgmx` (Maestro) a código
ISO (G-code) de la CNC SCM Group. Desde 2026-08-07 este árbol contiene SOLO la época
nueva: la reinvestigación metódica desde cero. El convertidor anterior, sus tests y sus
labs quedaron congelados fuera de esta rama (ramas `iso_converter` y
`respaldo/ejecucion-plan-f0-f3`) y no se referencian durante la reinvestigación.

## Estructura

```
iso/
  data/           Configuración de máquina: snapshot de los archivos extraídos de la
                  PC del CNC (def.tlgx, spindles.cfg, fields.cfg, …). Fuente única;
                  se refresca sobreescribiendo la carpeta tras cada calibración.
  docs/           Documentación de la investigación.
    experiments/  Un doc por experimento: mapa UI → .pgmx → ISO, derivado y pendiente.
  machine_config.py  Refresco y verificación del snapshot contra una copia del CNC.
  machining_lab/  Laboratorio de fixtures controlados (serie R).
  paths.py        Rutas raíz S:/P: de los pares PGMX/ISO.
```

El snapshot **no se copia a mano**: qué archivos entran está escrito en la tabla
`SELECCION` de `machine_config.py`, y el manifest declara de dónde salió cada uno.

```
py -m iso.machine_config verificar --fuente "S:\Copia CNC"   # no escribe nada
py -m iso.machine_config refrescar --fuente "S:\Copia CNC"
```

## Método

1. Fixtures `.pgmx` de variación controlada (una opción por archivo), serie R.
2. Postproceso en Maestro (PC del CNC) → ISO de referencia.
3. Anatomía del ISO: atribuir cada línea y cada valor a su origen (configuración del
   programa, configuración de la máquina, u operación).
4. Byte-idéntico o fail-loud; nunca aproximar en silencio.

La nomenclatura de los algoritmos es genérica y usa la terminología de Maestro; no se
nombra por proyectos de producción ni por fixtures de la investigación.
