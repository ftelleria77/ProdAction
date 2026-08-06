# iso/data — Configuración de máquina (snapshot de la PC del CNC)

REQUISITO del proyecto (Fermín, 2026-08-04): el converter lee la configuración de la
máquina y de las herramientas **siempre de los archivos extraídos de la PC del CNC**.
Tras una calibración, un cambio de configuración o el alta de una herramienta, esos
archivos cambian: se re-extraen y se sobreescriben acá. Sobreescribir = converter
actualizado, sin tocar código.

## Estructura

```
machine_config/snapshot/
  maestro/Cfgx/     ← S:\Maestro\Cfgx   (Head.cfg, Programaciones.settingsx, …)
  maestro/Tlgx/     ← S:\Maestro\Tlgx   (def.tlgx = catálogo de herramientas)
  xilog_plus/       ← S:\Xilog Plus     (axis.ini, Cfg\* completo, Job\def.tlg)
  manifest.csv      SHA256 por archivo — FECHA cada estado de config (los ISO de
                    referencia valen para la config con la que se postprocesaron)
```

Estos archivos no se editan a mano: son capturas de la configuración real de la
máquina en producción. Los shares `S:` son la PC del CNC (VPN
`fabrica.somosmobile.com.ar`).

## Instructivo de refresco (cuando cambia algo en la máquina)

1. Conectar la VPN si hace falta (`rasdial "fabrica.somosmobile.com.ar"`).
2. `py -m iso.machine_config check` — dice QUÉ cambió en S: respecto del snapshot
   (no toca nada).
3. `py -m iso.machine_config refresh` — copia S: → snapshot, regenera `manifest.csv`
   y `pgmx/data/tool_catalog.csv`.
4. `py -m pytest tests` — la suite dice si el cambio de config movió algo derivado.

`tool_catalog.csv`: las 17 columnas numéricas salen del `def.tlgx` (regeneración
automática, byte-validada contra el CSV curado). Las columnas `type` y `description`
son vocabulario de Fermín (regla 3; `type` alimenta la validación «Sierra Vertical X»
del canal) — se preservan entre refrescos, y una herramienta NUEVA sale con ellas
vacías + un aviso para completarlas a mano.

## Quién consume qué

- `iso/synthesis/_machine_config.py` — parsea en runtime `spindles.cfg`, `pheads.cfg`,
  `fields.cfg`, `Params.cfg` y `Programaciones.settingsx` del snapshot.
- `iso/synthesis/_tool_catalog.py` y `pgmx/synthesis/common/tools.py` — leen
  `pgmx/data/tool_catalog.csv` (derivado del `def.tlgx` de acá).
