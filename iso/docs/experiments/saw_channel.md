# Canal con la Sierra Vertical X (082) — modelo derivado (N037, 9/9)

Primera operación del **Eje B**. La 082 vive FIJA en el **mandril 82 del cabezal perforador**
(sin ATC): Ø120, hoja 3.8/4 mm, hundimiento máx 10 mm, TLC 60, feed 5 m/min, S4000.
Restricción física: cara superior, dirección X, **sentido −x**.

Implementación: `iso/synthesis/_channel.py` (render), `_validation._validate_slot_milling`,
familia `saw_channels` en `_reader.ProgramOps`. Tests: `test_iso_saw_channel.py`.

## Header (sin ATC)

```
?%ETK[6]=82                ← nº de mandril (del nombre de la herramienta "082")
G17 / MLV=2 / %Or[0].of* / MLV=1 / SHF[*] / MLV=2     ← bloque de primera pasada (= router)
?%ETK[17]=257              ← constante del ciclo sierra (Tier B, procedencia pendiente)
S4000M3                    ← catálogo spindle_std
?%ETK[1]=16                ← constante del ciclo sierra (Tier B)
MLV=2
SHF[X]=-96.000             ← spindles.cfg mandril 82
SHF[Y]=126.950             ← spindles.cfg 128.85 − w/2 (¡la referencia es la CARA de la hoja!)
SHF[Z]=22.150
```

## Cuerpo por canal

```
G0 X{x_mayor} Y{y}         ← SIEMPRE arranca en el X MAYOR: Maestro NORMALIZA el sentido a −x
                              (el fixture xfwd autorado en +x salió byte-idéntico al base)
G0 Z{TLC+sp}               ← =80 con security 20; sec10 → 70 (sourced)
D1 / SVL 60 / VL6 / SVR 1.9 / VL7      ← SVL=TLC, SVR=w/2
G1 Z-{prof} F2000          ← plunge a descent_std×1000; prof ≤ 10 (hundimiento, validado prof10)
?%ETK[7]=1                 ← la sierra usa 1 (el router 4)
G1 X{x_menor} Z-{prof} F5000           ← corte a feed_std×1000 (regla Z de un solo eje)
G0 Z{sp}
D0 / SVL 0 / VL6 / SVR 0 / VL7 / ?%ETK[7]=0
```

## Transición entre canales (two)

`?%ETK[8]=1 / G40 / G17 / MLV=2` + **DOBLE G0** (última posición física → inicio del siguiente,
ambos a Z{TLC+sp}; el router usa triple) + re-setup D1/SVL/SVR.

## Epílogo propio

`G61 / MLV=0 / ?%ETK[1]=0 / ?%ETK[17]=0 / G4F1.200 / M5 / D0 / park…` — limpia las claves que
el header seteó, con dwell de 1.2 s (como los taladros, que limpian ETK[0]).

## Guardas

Solo-sierra por programa (mezcla con fresado/taladros sin fixture); no pasante; horizontal;
prof ≤ hundimiento; sin leads/rebaba/lado/material_position≠Left/end_radius≠60/ángulo≠90°.

## Números pendientes de procedencia (libro mayor)

`ETK[17]=257`, `ETK[1]=16`, `ETK[7]=1`, `G4F1.200` — constantes empíricas del ciclo sierra
hasta ubicarlas en machine config (candidatos: spindles.cfg / pheads.cfg).
