# N001 — Análisis de lote baseline

Fecha: 2026-06-16  
Fuente: 24 archivos `.iso` generados por Maestro a partir de los 24 `.pgmx` del lote N001.  
Geometría de referencia: PIECE_L=300, PIECE_W=200, PIECE_D=18, ORIGIN_X=5, ORIGIN_Y=5, ORIGIN_Z=25.

---

## 1. Estructura de todo archivo ISO

Todo archivo ISO sigue la secuencia:

```
PREAMBLE        — cabecera de pieza + inicialización de máquina
OPERATION(S)    — uno o más bloques de operación
EPILOGUE        — limpieza y park
```

### 1.1 PREAMBLE

```
% {nombre_pgmx}.pgm
;H DX={DX} DY={DY} DZ={DZ} BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58
G71
MLV=0
%Or[0].ofX={-DX*1000}
%Or[0].ofY=-1515599.976
%Or[0].ofZ={DZ*1000}
?%EDK[0].0=0
?%EDK[1].0=0
MLV=1
SHF[X]=-{DX}
SHF[Y]=-1515.600
SHF[Z]={DZ}+%ETK[114]/1000
```

Donde:
- `DX = PIECE_L + ORIGIN_X` = 305
- `DY = PIECE_W + ORIGIN_Y` = 205
- `DZ = ORIGIN_Z + PIECE_D` = 43

A continuación siguen bloques `?%ETK[8]=N G40` que dependen de las caras laterales presentes en el programa. Si no hay taladro lateral: tres bloques con `?%ETK[8]=1`. Si hay cara lateral, el último bloque cambia.

### 1.2 Bloque G40 por cara lateral

La configuración de la PRIMERA cara lateral (después del reordenamiento de Maestro) determina el último G40 del preamble:

| Primera cara | Último G40 | SHF adicional |
|---|---|---|
| ninguna (solo top/router) | `?%ETK[8]=1 G40` | — |
| Left | `MLV=1 SHF[X]=-{DX} SHF[Y]=-{1515.6-DY}={-1310.6} SHF[Z]={DZ}+ETK[114]/1000 ?%ETK[8]=3 G40` | SHF[Y] cambia a -1310.600 |
| Right | `?%ETK[8]=2 G40` | sin cambio de SHF |
| Front | `?%ETK[8]=5 G40` | sin cambio de SHF |
| Back | `MLV=1 SHF[X]=-{ORIGIN_X}={-5} SHF[Y]=-1510.600 SHF[Z]={DZ}+ETK[114]/1000 ?%ETK[8]=4 G40` | SHF[X] cambia a -ORIGIN_X |

Después del bloque G40 siempre:
```
MLV=1
SHF[Z]={ORIGIN_Z}+%ETK[114]/1000
MLV=2
G17
```

### 1.3 EPILOGUE (idéntico en todos los archivos)

```
G61
MLV=0
?%ETK[0]=0
?%ETK[17]=0
G4F1.200
M5
D0
G0 G53 Z201.000
G0 G53 X-3700.000
G64
SYN
?%ETK[0]=0
?%ETK[1]=0
?%ETK[2]=0
?%ETK[13]=0
?%ETK[17]=0
?%ETK[18]=0
?%ETK[19]=0
?%EDK[13].0=1
MLV=1
SHF[X]=0
SHF[Y]=0
SHF[Z]=0
MLV=2
SHF[X]=0
SHF[Y]=0
SHF[Z]=0
MLV=0
VL6=0
VL7=0
?%EDK[13].0=0
M2
```

Para programas con taladro lateral, el epilogue incluye un bloque adicional de restauración justo antes de `G64`:
```
MLV=1
SHF[X]=-{DX}
SHF[Y]=-1510.600
SHF[Z]={DZ}+%ETK[114]/1000
G61
MLV=0
D0
G0 G53 Z201.000
G64
```

---

## 2. Reordenamiento de operaciones por Maestro

**Maestro ignora el orden del PGMX.** La prioridad de ejecución es siempre:

1. **Router** (requiere ATC, se ejecuta primero)
2. **Top drill** (taladros verticales)
3. **Side drill** (taladros laterales)

Verificado en C001, C002 (top+left), C004, C005 (router+top), C006, C007 (router+left).

Dentro de la misma familia:
- Holes del mismo diámetro (misma herramienta): se agrupan en un solo bloque de setup + N cortes.
- Diámetros distintos: bloques separados, ordenados por el diámetro del primer taladro en PGMX.

Caras laterales múltiples (B005 Left+Right, B006 Front+Back, B008 Left+Front):
- B008 (input: Left, Front) → ISO: Front, Left: Front tiene mayor prioridad que Left.
- B005 (input: Left, Right) → ISO: Left primero.
- B006 (input: Front, Back) → ISO: Front primero.
- Prioridad empírica observada: **Front > Left > Right > Back** (requiere confirmación con más fixtures).

---

## 3. Taladro vertical (Top Drill)

### 3.1 Herramientas y registros (Q-A01, Q-A04)

| Diámetro | ETK[6] | ETK[0] | Spindle | Feed (mm/min) | SHF[X] MLV2 | SHF[Y] MLV2 | SHF[Z] MLV2 |
|---|---|---|---|---|---|---|---|
| D5 | 5 | 16 | S6000M3 | 2000 | -64.000 | 0.000 | -0.950 |
| D8 | 1 | 1 | S6000M3 | 2000 | 0.000 | 0.000 | 0.000 |
| D15 | 2 | 2 | S4000M3 | 1000 | 0.000 | 32.000 | -0.200 |

ETK[17]=257 (constante para todos los taladros verticales).

### 3.2 Bloque de setup de herramienta (primer uso)

```
?%ETK[6]={etk6}
%Or[0].ofX=-310000.000
%Or[0].ofY=-1515599.976
%Or[0].ofZ={DZ*1000}
MLV=1
SHF[X]=-{DX}
SHF[Y]={-1515.6+ORIGIN_Y}={-1510.6}
SHF[Z]={ORIGIN_Z}
MLV=2
MLV=2
SHF[X]={shf_x}
SHF[Y]={shf_y}
SHF[Z]={shf_z}
?%ETK[17]=257
{S{rpm}M3}   ← solo se emite si la velocidad cambia respecto a la herramienta anterior
?%ETK[0]={etk0}
```

### 3.3 Fórmula Z para taladro vertical (Q-A02)

```
Z_SECURITY = 115.000  (constante de máquina)
Z_CUT      = 95.0 - target_depth
```

Verificado:
- depth=8 → Z=87.0 ✓
- depth=10 → Z=85.0 ✓
- depth=14 → Z=81.0 ✓

La constante 95 es el Z de la superficie superior de la pieza en el marco MLV2 del cabezal vertical, para la geometría ORIGIN_Z=25, PIECE_D=18 de este jig.

### 3.4 Bloque de corte (un agujero)

```
G0 X{hole.x} Y{hole.y}
G0 Z115.000
?%ETK[7]=3
MLV=2
G1 G9 Z{95-target_depth} F{feed}
G0 Z115.000
MLV=1
SHF[Z]={DZ}+%ETK[114]/1000
?%ETK[7]=0
```

### 3.5 Segundo agujero, MISMA herramienta (Q-A03)

Sin re-setup de ETK[6], SHF, ETK[17], spindle, ETK[0]. Solo:

```
MLV=1
SHF[Z]={ORIGIN_Z}+%ETK[114]/1000
MLV=2
G17
G0 X{prev_hole.x} Y{prev_hole.y} Z115.000   ← pasar por el agujero anterior
G0 X{hole.x}      Y{hole.y}      Z115.000   ← posición del nuevo agujero
?%ETK[7]=3
G1 G9 Z{95-target_depth} F{feed}
G0 Z115.000
MLV=1
SHF[Z]={DZ}+%ETK[114]/1000
?%ETK[7]=0
```

### 3.6 Segundo agujero, DISTINTA herramienta

Re-setup completo: ETK[6] + (S...M3 solo si velocidad cambia) + SHF MLV2 + ETK[0].
Igual al primer corte de esa herramienta, sin %Or ni SHF MLV1 (ya establecidos).

```
MLV=1
SHF[Z]={ORIGIN_Z}+%ETK[114]/1000
MLV=2
G17
?%ETK[6]={new_etk6}
G0 X{prev.x} Y{prev.y} Z115.000   ← dummy move por posición anterior
MLV=2
SHF[X]={new_shf_x}
SHF[Y]={new_shf_y}
SHF[Z]={new_shf_z}
{?%ETK[17]=257  S{new_rpm}M3}   ← solo si velocidad cambia
?%ETK[0]={new_etk0}
G0 X{hole.x} Y{hole.y}
G0 Z115.000
?%ETK[7]=3
G1 G9 Z{95-target_depth} F{new_feed}
G0 Z115.000
MLV=1
SHF[Z]={DZ}+%ETK[114]/1000
?%ETK[7]=0
```

---

## 4. Taladro lateral (Side Drill)

### 4.1 Herramientas y registros por cara (Q-B01)

| Cara | ETK[6] | ETK[0] | ETK[8] | Spindle | SHF[X] MLV2 | SHF[Y] MLV2 | SHF[Z] MLV2 |
|---|---|---|---|---|---|---|---|
| Left | 61 | 2147483648 | 3 | S6000M3 | -118.000 | -32.000 | 66.300 |
| Right | 60 | 2147483648 | 2 | S6000M3 | -66.900 | -32.000 | 66.450 |
| Front | 58 | 1073741824 | 5 | S6000M3 | 32.000 | -21.750 | 66.500 |
| Back | 59 | 1073741824 | 4 | S6000M3 | 32.000 | 29.500 | 66.500 |

ETK[17]=257 (constante para todos los taladros laterales).  
ETK[0]=2147483648 = 0x80000000 (Left y Right comparten máscara).  
ETK[0]=1073741824 = 0x40000000 (Front y Back comparten máscara).

### 4.2 Fórmulas de posicionamiento (Q-B02)

Constante de máquina: **TLC_LATERAL = 37** (tool length constant lateral, de config de cabezal).  
Margen de seguridad: **SECURITY = 20** mm.

#### Left (drilling axis = X, entry from −X):

```
X_approach = -(TLC + depth + SECURITY) = -(37 + depth + 20)
X_cut      = -TLC                      = -37
Y_position = -center_x
Z_height   = center_y
```

#### Right (drilling axis = X, entry from +X):

```
X_approach = PIECE_L + TLC + depth + SECURITY = 300 + 37 + depth + 20
X_cut      = PIECE_L + TLC                    = 337
Y_position = +center_x
Z_height   = center_y
```

#### Front (drilling axis = Y, entry from −Y):

```
Y_approach = -(TLC + depth + SECURITY) = -(37 + depth + 20)
Y_cut      = -TLC                      = -37
X_position = center_x
Z_height   = center_y
```

#### Back (drilling axis = Y, entry from +Y):

```
Y_approach = PIECE_W + TLC + depth + SECURITY = 200 + 37 + depth + 20
Y_cut      = PIECE_W + TLC                    = 237
X_position = -center_x   ← NEGATIVO
Z_height   = center_y
```

Verificado con depth=28, center_x=150/100/60/140, center_y=9.

### 4.3 SHF[X] en MLV=1 para caras laterales

La working step SHF[X] en MLV=1 varía según la cara:

| Cara | SHF[X] MLV=1 | SHF[Y] MLV=1 |
|---|---|---|
| Left | -DX = -305 | -1515.6 + DY = -1310.6 |
| Right | -DX = -305 | -1515.6 + ORIGIN_Y = -1510.6 |
| Front | -DX = -305 | -1515.6 + ORIGIN_Y = -1510.6 |
| Back | -ORIGIN_X = -5 | -1515.6 + ORIGIN_Y = -1510.6 |

### 4.4 Bloque de setup de cara lateral (primer uso en el programa)

```
MLV=1
SHF[X]=-{DX}          ← (o -ORIGIN_X para Back)
SHF[Y]={shf_y_mlv1}   ← ver tabla 4.3
SHF[Z]={DZ}+%ETK[114]/1000
?%ETK[8]={etk8}
G40
MLV=1
SHF[Z]={ORIGIN_Z}+%ETK[114]/1000
MLV=2
G17
?%ETK[6]={etk6}
%Or[0].ofX=-310000.000
%Or[0].ofY=-1515599.976
%Or[0].ofZ={DZ*1000}
MLV=1
SHF[X]={shf_x_mlv1}
SHF[Y]={shf_y_mlv1}
SHF[Z]={ORIGIN_Z}
MLV=2
MLV=2
SHF[X]={shf_x_mlv2}
SHF[Y]={shf_y_mlv2}
SHF[Z]={shf_z_mlv2}
?%ETK[17]=257
S6000M3
?%ETK[0]={etk0}
```

Para el PRIMER setup de cara lateral en el programa, se emite bloque completo incluyendo %Or y SHF MLV=1.

### 4.5 Bloque de corte (un agujero lateral)

Para Left (análogo para las demás caras):
```
{G4F0.500}   ← solo si hay un agujero adicional en la misma cara (dwell)
G0 X{X_approach} Y{Y_position}
G0 Z{Z_height}
?%ETK[7]=3
MLV=2
G1 G9 X{X_cut} F2000.000
G0 X{X_approach} Z{Z_height}
MLV=1
SHF[Z]={DZ}+%ETK[114]/1000
?%ETK[7]=0
```

Nota: `G4F0.500` (dwell 0.5s) aparece antes del primer agujero cuando la cara lateral requirió una transición de repositionamiento físico (G40 entre operaciones). No aparece para el primer bloque en el programa.

### 4.6 Segundo agujero, MISMA cara

```
MLV=1
SHF[Z]={ORIGIN_Z}+%ETK[114]/1000
MLV=2
G17
G0 X{X_approach} Y{prev_Y} Z{Z_height}   ← pasar por agujero anterior
G0 X{X_approach} Y{next_Y} Z{Z_height}   ← nuevo agujero
?%ETK[7]=3
G1 G9 X{X_cut} F2000.000
G0 X{X_approach} Z{Z_height}
MLV=1
SHF[Z]={DZ}+%ETK[114]/1000
?%ETK[7]=0
```

Sin re-setup de ETK[6], SHF MLV2, spindle, ETK[0].

### 4.7 Cambio de cara lateral (Q-B03)

Transición entre caras laterales (ej. Left→Right):

```
{fin del bloque de cara anterior: MLV=1 SHF[Z]=DZ, ?%ETK[7]=0}

MLV=1
SHF[X]={new_shf_x}
SHF[Y]={new_shf_y}
SHF[Z]={DZ}+%ETK[114]/1000
?%ETK[8]={new_etk8}
G40
MLV=1
SHF[Z]={ORIGIN_Z}+%ETK[114]/1000
MLV=2
G17
?%ETK[6]={new_etk6}
MLV=0
G0 G53 Z{Z_intermediate}   ← Z absoluto de máquina, face-specific (≈149.3–149.5)
MLV=2
MLV=2
SHF[X]={new_shf_x_mlv2}
SHF[Y]={new_shf_y_mlv2}
SHF[Z]={new_shf_z_mlv2}
{?%ETK[0]={new_etk0}}   ← solo si ETK[0] cambia (Left→Front sí, Left→Right no en ETK[0])
G0 X{X_approach} Y{Y_position}
...
```

Z intermedios observados:
| Transición | G0 G53 Z |
|---|---|
| Top → Left | 149.300 |
| Left → Right | 149.450 |
| Front → Back | 149.500 |
| Left → Front | 149.500 |
| Router → Left | 149.500 |

---

## 5. Router (Line Milling E004)

### 5.1 Herramienta y registros

```
T4       ← ATC: buscar herramienta en posición 4
SYN
M06      ← cambio de herramienta
?%ETK[6]=1
?%ETK[9]=4
?%ETK[18]=1
S18000M3
```

SHF[X/Y/Z] MLV2 del router E004: X=32.050, Y=-246.650, Z=-125.300.

### 5.2 Bloque completo de una pasada lineal (Q-D01)

```
G17
MLV=2
%Or[0].ofX=-310000.000
%Or[0].ofY=-1515599.976
%Or[0].ofZ={DZ*1000}
MLV=1
SHF[X]=-{DX}
SHF[Y]=-1510.600
SHF[Z]={DZ}      ← SIN +%ETK[114] (diferencia vs taladro)
MLV=2
?%ETK[13]=1
MLV=2
SHF[X]=32.050
SHF[Y]=-246.650
SHF[Z]=-125.300
G0 X{line_x1} Y{line_y1}
G0 Z127.200           ← Z de aproximación (constante de máquina)
D1
SVL {127.200 - security_plane}   ← = 127.200 - 20.000 = 107.200
VL6={127.200 - security_plane}
SVR {tool_width / 2}             ← = 4.0 / 2 = 2.000
VL7={tool_width / 2}
G1 Z{-target_depth} F2000.000   ← plunge
?%ETK[7]=4
G1 X{line_x2} Z{-target_depth} F5000.000   ← corte
G0 Z{security_plane}    ← = 20.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
```

Para la PRIMERA pasada del programa, el bloque de ATC (`T4, SYN, M06, ETK[6]=1...`) precede al `G17`.

### 5.3 Fórmulas Z del router (Q-D01)

```
Z_approach  = 127.200   (constante de máquina, E004)
Z_cut       = -target_depth  (Z=0 es superficie superior de pieza)
Z_retract   = security_plane (del spec PGMX, = 20.000 en nuestras fixtures)
SVL         = Z_approach - security_plane = 107.200
```

Diferencia clave vs. taladro vertical: el router referencia Z=0 a la superficie de la pieza (SHF[Z]=DZ en MLV1). El taladro vertical referencia Z al fondo de la pieza (SHF[Z]=ORIGIN_Z).

### 5.4 Segunda pasada, misma herramienta (Q-D02)

```
?%ETK[7]=0   ← fin de primer corte
G17
MLV=2
G0 X{x2_prev} Y{y1_prev} Z127.200   ← posición fin de pasada anterior a altura segura
G0 X{x1_next} Y{y1_next} Z127.200   ← inicio de nueva pasada
G0 X{x1_next} Y{y1_next} Z127.200   ← se repite (comportamiento de Maestro)
D1
SVL {107.200}
VL6={107.200}
SVR {tool_width/2}
VL7={tool_width/2}
G1 Z{-target_depth} F2000.000
?%ETK[7]=4
G1 X{x2_next} Z{-target_depth} F5000.000
G0 Z{security_plane}
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
?%ETK[7]=0
```

Sin re-setup de T4/M06/ETK[6]/spindle. Sin re-setup de %Or, SHF MLV1/MLV2.  
Maestro duplica el G0 de posicionamiento antes de la segunda pasada (primera instrucción de movimiento se repite).

---

## 6. Secuencias de transición entre familias (Q-C01)

### 6.1 Top Drill → Side Drill

Después del último `?%ETK[7]=0` del bloque de top drill:

```
MLV=1
SHF[X]={face_shf_x}
SHF[Y]={face_shf_y}
SHF[Z]={DZ}+%ETK[114]/1000
?%ETK[8]={face_etk8}
G40
MLV=1
SHF[Z]={ORIGIN_Z}+%ETK[114]/1000
MLV=2
G17
?%ETK[6]={face_etk6}
MLV=0
G0 G53 Z{Z_intermediate}
MLV=2
MLV=2
SHF[X]={face_shf_x_mlv2}
SHF[Y]={face_shf_y_mlv2}
SHF[Z]={face_shf_z_mlv2}
{?%ETK[17]=257  S{rpm}M3}   ← solo si velocidad cambia
?%ETK[0]={face_etk0}
G0 X{approach_pos} Y{face_pos}
...
```

### 6.2 Router → Top Drill o Side Drill

Después del último bloque del router:

```
?%ETK[7]=0
MLV=0
G0 G53 Z201.000
MLV=2
G61
MLV=0
?%ETK[13]=0
?%ETK[18]=0
G0 G53 Z201.000
G64
MLV=1
SHF[Z]={ORIGIN_Z}+%ETK[114]/1000
MLV=2
G17
?%ETK[6]={next_etk6}
MLV=2
SHF[X]={next_shf_x}
SHF[Y]={next_shf_y}
SHF[Z]={next_shf_z}
?%ETK[17]=257
S{rpm}M3
?%ETK[0]={next_etk0}
G0 X{pos} Y{pos}
...
```

La transición Router→Side incluye también el bloque de reposicionamiento de cara (ETK[8] G40) entre `G64` y `SHF[Z]=ORIGIN_Z`.

### 6.3 Side Drill → Side Drill (cara distinta)

Ver sección 4.7 (Cambio de cara lateral).

---

## 7. Constantes de máquina identificadas

| Constante | Valor | Origen probable |
|---|---|---|
| Or[0].ofY | -1515599.976 (µm) | Posición Y de la mesa |
| SHF[Y] preamble | -1515.600 | Idem en mm |
| SHF[Y] working | -1510.600 = -1515.600 + ORIGIN_Y | |
| Z_TOP_SECURITY | 115.000 | Config cabezal vertical |
| Z_TOP_SURFACE_IN_FRAME | 95.000 | = Z_TOP_SECURITY - 20 |
| Z_SIDE_SECURITY | 9.000 | = center_y (por fixture) |
| TLC_LATERAL | 37 | Tool length constant cabezales laterales |
| Z_ROUTER_APPROACH | 127.200 | Config router E004 |
| Z_PARK | 201.000 | Park Z de máquina |
| X_PARK | -3700.000 | Park X de máquina |
| G53_Z_LATERAL_TRANSITION | ≈149.3–149.5 | Config por cara, ±0.2 |

---

## 8. Respuestas a preguntas abiertas de current-state.md

| ID | Respuesta |
|---|---|
| Q-A01 | ETK[6]: D5=5, D8=1, D15=2. ETK[0]: D5=16, D8=1, D15=2. Ver tabla 3.1. |
| Q-A02 | Z_cut = 95 − target_depth. Z_security = 115. |
| Q-A03 | Misma herramienta: solo reposicionamiento. Distinta: setup completo. Spindle solo si cambia velocidad. |
| Q-A04 | D5: S6000M3. D8: S6000M3. D15: S4000M3. |
| Q-B01 | ETK[6]: L=61, R=60, F=58, B=59. ETK[0]: L/R=2147483648, F/B=1073741824. Ver tabla 4.1. |
| Q-B02 | Eje de penetración: TLC=37, SECURITY=20. Ver fórmulas en 4.2. |
| Q-B03 | Cambio de cara: ETK[8] G40 + G0 G53 Z149.x + nuevo ETK[6]. Ver 4.7. |
| Q-C01 | Maestro reordena: Router → Top → Side. Secuencias en sección 6. |
| Q-D01 | Bloque completo en sección 5.2. Z_approach=127.200, SVL=107.200, SVR=tool_w/2. |
| Q-D02 | Sin re-setup. G17 + G0 doble a posición anterior → nueva pasada. Ver 5.4. |
