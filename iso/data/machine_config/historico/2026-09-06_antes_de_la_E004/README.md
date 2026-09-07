# Configuración de máquina de la época previa al cambio de la `E004`

**Qué es**: los cuatro archivos del snapshot que cambiaron el 2026-09-07, guardados tal como
estaban cuando se postprocesó **todo lo que hay medido hasta el 2026-09-06 inclusive**.

**Por qué existe**: el 2026-09-07 Fermín cambió la fresa de 4 mm (`E004`) y tuvo que rehacer
su calibración. Todos los fixtures de las ramas A, B, C, D1 (perforado) y D2 (canal) fueron
postprocesados **con esta configuración**, no con la que hay en `snapshot/`.

## Qué cambió

| archivo | cambio |
|---|---|
| `maestro/Tlgx/def.tlgx` | la `E004`: longitud **107,2 → 95**. Y **todos** los `tool_id` corridos |
| `xilog_plus/Job/def.tlg` | la misma longitud, en los tres campos que la llevan |
| `maestro_ui/UI00.exe.Config` | `RapidFeed` **50 → 164,042** · `IsMM` `true` → `True` (sólo el case) |
| `xilog_plus/Cfg/Env.cfg` | `Path` de `…\Xilog Plus\Cfg` a `…\Xilog Plus\JOB` |

### ⚠️ Los `tool_id` NO son estables

Al regenerar el catálogo, Maestro **reasigna todos los identificadores**. Se vio dos veces el
mismo día: primero corridos **+40** y, tras volver a generarlo, **+60** (`001`: 1888 → 1928 →
1948; `082`: 1899 → 1959).

⇒ **Nunca referenciar una herramienta por `tool_id` fuera del archivo que la lleva.** El `ID`
sólo es coherente **dentro** de un `.pgmx`, junto al `def.tlgx` que ese `.pgmx` trae embebido.
Hacia afuera, la herramienta se identifica por **nombre** (`082`, `E004`).

### ⚠️ El `RapidFeed`, sin barrer

`164,042` es `50` convertido a unidades imperiales (50 m/min = 164,042 ft/min): la aplicación
estuvo en pulgadas y al volver quedó el valor convertido. **No sabemos si llega al ISO**: el
barrido A6 midió la ventana Opciones sobre un programa vacío, y una velocidad de rápido sólo
se ve con traza. Queda como diferencia conocida entre esta época y la siguiente.

## Cómo usarlo

Para releer un fixture postprocesado hasta el 2026-09-06:

```python
from pathlib import Path
from pgmx.tlgx import load_tlgx

catalogo = load_tlgx(Path("iso/data/machine_config/historico/2026-09-06_antes_de_la_E004/def.tlgx"))
```

Y para el caso general, lo más seguro: **leer el `def.tlgx` que viaja dentro del propio
`.pgmx`** (`load_tlgx_from_pgmx`), que siempre es el que le corresponde.
