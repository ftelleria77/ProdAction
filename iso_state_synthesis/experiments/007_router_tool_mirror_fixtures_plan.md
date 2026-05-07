# Experimento 007 - Piezas Espejo Por Herramienta Router

Fecha: 2026-05-07

## Proposito

Confirmar que las reglas de fresado lineal/contorno no dependen de `ToolKey=E004`.
El emisor ya acepta operaciones de fresado con herramientas `E00x`, incluida
`E002`, y toma numero, largo, radio, avances y velocidad desde el `def.tlgx`
embebido. Falta evidencia generada por Maestro para las mismas trayectorias con
otras herramientas.

Este plan es un recordatorio operativo: crear piezas espejo en Maestro, exportar
sus ISO y correr `compare-candidate`. No es una regla de seguridad para
generacion automatica de `.pgmx`.

## Pieza Base

Usar la misma placa que el corpus actual:

- dimensiones: `400 x 250 x 18`;
- origen: `X=5`, `Y=5`, `Z=25`;
- plano: `Top`;
- operacion: `BottomAndSideFinishMilling`;
- `SideOfFeature=Center`;
- sin estrategia;
- acercamiento y alejamiento deshabilitados.

## Recorridos Espejo

| Codigo | Pieza control | Geometria | Profundidad | Trayectoria |
| --- | --- | --- | --- | --- |
| `LINE_V_P15` | `Pieza_015` | `LineVertical` | `target_depth=15` | `(200,50) -> (200,200)` |
| `OPEN_POLY_THRU_E05` | `Pieza_022` | `OpenPolyline` | pasante `extra_depth=0.5` | `(150,0) -> (100,150) -> (300,100) -> (250,250)` |
| `CIRCLE_D100_CCW_THRU_E05` | `Pieza_025` | `Circle`, antihorario | pasante `extra_depth=0.5` | centro `(200,125)`, radio `50` |
| `CIRCLE_D100_CW_THRU_E05` | `Pieza_026` | `Circle`, horario | pasante `extra_depth=0.5` | centro `(200,125)`, radio `50` |

Para los casos pasantes mantener `overcut_length=0.5`. Para `LINE_V_P15`
mantener `overcut_length=0`.

## Herramientas A Cubrir

Crear la matriz para:

- `E001`
- `E002`
- `E003`
- `E004` ya cubierto por las piezas control
- `E005`
- `E006`
- `E007`

Si Maestro rechaza una combinacion por tipo de herramienta, registrar el rechazo
como evidencia. El conversor ISO no debe imponer esa restriccion por cuenta
propia.

## Nombres Sugeridos

Usar nombres estables para poder barrerlos por prefijo:

```text
Pieza_Tool_E001_LINE_V_P15
Pieza_Tool_E001_OPEN_POLY_THRU_E05
Pieza_Tool_E001_CIRCLE_D100_CCW_THRU_E05
Pieza_Tool_E001_CIRCLE_D100_CW_THRU_E05
```

Repetir el patron reemplazando `E001` por `E002`, `E003`, `E005`, `E006` y
`E007`. `E004` puede reutilizar `Pieza_015`, `Pieza_022`, `Pieza_025` y
`Pieza_026` como control, o duplicarse con el mismo patron si conviene una serie
homogenea.

## Validacion Esperada

Comando por pieza:

```powershell
py -3 -m iso_state_synthesis compare-candidate `
  S:\Maestro\Projects\ProdAction\ISO\<pieza>.pgmx `
  P:\USBMIX\ProdAction\ISO\<pieza>.iso
```

Resultado esperado para cada pieza aceptada por Maestro:

- `Resultado: igual`;
- mismo orden estructural que el control `E004`;
- diferencias de texto ISO solo derivadas de herramienta: `Tn`, `?%ETK[9]=n`,
  `SVL/VL6`, `SVR/VL7`, `S...M3`, feeds y coordenadas/toolpaths si Maestro los
  recalcula por radio.

Si aparece `Resultado: distinto`, guardar el diff completo y clasificar si el
cambio es una regla real por herramienta o una limitacion del emisor.
