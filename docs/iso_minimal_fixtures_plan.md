# Plan De Fixtures Minimos ISO

Estado: 2026-05-02.

Este documento guarda el punto exacto de reanudacion para la investigacion ISO
cuando haya acceso a la computadora del CNC/Maestro. El objetivo es generar
`.pgmx` minimos y comparables, postprocesarlos con Maestro, copiar los `.iso`
resultantes y continuar la inferencia del contrato CNC sin perder contexto.

## Rutas

- Generar `.pgmx` en la compu de fabrica:
  `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03`
- Maestro postprocesa los `.iso` en:
  `C:\PrgMaestro\USBMIX`
- Copiar los `.iso` postprocesados a una carpeta accesible para estudio:
  `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03`

No sobrescribir los `Pieza_0xx` historicos. Usar los nombres `ISO_MIN_*`.

## Comando

Desde la raiz del repo `ProdAction`:

```powershell
python tools/generate_iso_minimal_fixtures.py --output-dir "S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03"
```

El script escribe:

- los `.pgmx` de prueba;
- `manifest.csv` con nombre, ruta, hash y objetivo de cada fixture.

## Suite inicial

Todas las piezas usan `execution_fields = HG`, salvo que se indique lo
contrario. La idea es cambiar una sola variable por archivo.

| Fixture | Cambio controlado | Objetivo |
| --- | --- | --- |
| `ISO_MIN_001_TopDrill_Base` | base `100x100x18`, origen `5/5/25`, taladro superior D5 en `50/50` | referencia limpia para `%Or`, `SHF`, `MLV`, `ETK` |
| `ISO_MIN_002_TopDrill_Y60` | solo cambia Y del taladro `50 -> 60` | separar coordenada de operacion vs shift de maquina |
| `ISO_MIN_003_TopDrill_X60` | solo cambia X del taladro `50 -> 60` | idem eje X |
| `ISO_MIN_004_TopDrill_DY200` | solo cambia ancho de panel `100 -> 200` | ver si `DY` afecta `%Or/SHF[Y]` |
| `ISO_MIN_005_TopDrill_DX200` | solo cambia largo de panel `100 -> 200` | ver si `DX` afecta area/origen |
| `ISO_MIN_006_TopDrill_OriginY10` | solo cambia `origin_y` `5 -> 10` | aislar efecto de `WorkpieceSetup/Placement` |
| `ISO_MIN_010_LeftDrill_Base` | taladro lateral izquierdo D8 | validar `ETK[8]`, `SHF` y offsets de spindle lateral |
| `ISO_MIN_011_RightDrill_Base` | taladro lateral derecho D8 | idem lado derecho |
| `ISO_MIN_012_FrontDrill_Base` | taladro lateral frontal D8 | idem frente |
| `ISO_MIN_013_BackDrill_Base` | taladro lateral trasero D8 | idem fondo |
| `ISO_MIN_020_LineE004_Base` | linea pasante E004 centrada en Y50 | referencia router/fresado |
| `ISO_MIN_021_LineE004_Y60` | solo cambia Y de la linea `50 -> 60` | separar coordenada router vs `SHF[Y]` |
| `ISO_MIN_022_LineE004_PH5` | misma linea, estrategia unidireccional `PH=5` | ver efecto de estrategia en `G41/G42`, niveles y `MLV` |
| `ISO_MIN_023_LineE004_OriginY10` | misma linea, `origin_y` `5 -> 10` | comparar origen con fresado router |

## Que comparar despues del postprocesado

Para cada `.iso`, extraer:

- cabecera `;H DX=... DY=... DZ=... -HG`;
- `%Or[0].ofX`, `%Or[0].ofY`, `%Or[0].ofZ`;
- todos los `SHF[X/Y/Z]`;
- todos los `MLV=...`;
- `?%ETK[0]`, `?%ETK[6]`, `?%ETK[7]`, `?%ETK[8]`, `?%ETK[9]`,
  `?%ETK[13]`, `?%ETK[17]`, `?%ETK[18]`, `?%ETK[114]`;
- `SVL`, `SVR`, `D0/D1`, `T`, `M06`, `S...M3`;
- movimientos `G0 G53`, especialmente `Z201.000`, `X-3700.000`,
  `Z149.500` y `Z149.450`;
- presencia/ausencia de `G41/G42`.

## Hipotesis que se busca cerrar

1. `fields.cfg` explica la familia de valores Y alrededor de `-1515`, pero
   falta la correccion exacta que produce `%Or[0].ofY=-1515599.976`,
   `SHF[Y]=-1515.600` y `SHF[Y]=-1510.600`.
2. Si mover la geometria en Y cambia coordenadas ISO pero no `SHF[Y]`, entonces
   `SHF[Y]` es marco/area de maquina y no posicion de operacion.
3. Si cambiar `origin_y` mueve `DX/DY` o `%Or/SHF`, el origen de PGMX entra en
   la formula de area; si no, solo afecta cabecera o geometria Maestro.
4. Los laterales deben confirmar el mapeo `ETK[8]` y los offsets fisicos de
   `spindles.cfg`.
5. E004 debe confirmar el bloque router (`T4`, `ETK[9]=4`, `SVL=107.200`,
   `SVR=2.000`) en piezas chicas y comparables.

## Pendiente secundario

La memoria ISO historica recomienda repetir piezas equivalentes a
`Pieza_092..Pieza_095` agregando estrategia `PH=5` para cerrar el cruce
`Left/Right + Down/Up + PH=5`. Eso queda como segunda tanda, despues de cerrar
primero el contrato `HG/%Or/SHF`.
