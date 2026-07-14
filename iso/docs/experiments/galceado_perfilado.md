# Galceado / Perfilado / Escuadrado — análisis previo (Eje B etapa 4)

Operación de la UI: botón **Galceado**, panel **Perfilado**. Fresado de un CONTORNO CERRADO
(el borde de la pieza o una geometría dibujada). Estado: **EN INVESTIGACIÓN** — analizado el
programa manual real `S:\Maestro\Projects\ProdAction\Programas Manuales\Galceado.pgmx` + su ISO
`P:\...\Programas Manuales\galceado.iso`. Aún NO implementado en el converter.

## La UI (capturas Fermín 2026-07-10)

Panel "Perfilado", casi igual al de Fresado, con DOS cosas propias:
- **Perfil: Pieza / Geometría** — origen del contorno. Con **Pieza**, Maestro toma el borde de
  la propia pieza (sin dibujar). Con **Geometría**, una geometría cerrada dibujada.
- **Lado: Externo / Interno** — vocabulario de corrección propio del contorno cerrado.

Resto compartido con el fresado: Profundidad / Pasante / Rebaba / Anchura; Datos tecnológicos
(Avanz./Rotación); **Estrategia** (Unidireccional / Bidireccional / ZigZag — IDÉNTICAS a las
ya derivadas, mismo vocabulario: Profundidad hueco / Último hueco / Pasada avance-retorno /
Conexión entre huecos Salida-a-cota / En-la-pieza); Acercamiento/Alejamiento; Datos avanzados/
máquina. ⇒ el Perfilado REUSA toda la maquinaria compartida; lo nuevo es Perfil + Lado.

## Representación en el .pgmx (Galceado.pgmx — pieza 300×300×18, DOS operaciones)

Feature type NUEVO: **`ContourFeature`** (no `GeneralProfileFeature`). Campo distintivo
**`ContourType`**:
- `ContourType=Workpiece` ⟺ Perfil: **Pieza**.
- `ContourType=Geometry` ⟺ Perfil: **Geometría**.

**Externo/Interno NO es un campo**: ambos features tienen `SideOfFeature=Right`. La distinción
sale de `SideOfFeature` + el SENTIDO (winding) del contorno:
- op1 pieza = contorno CCW (150,0→300,0→300,300→0,300→0,0→150,0) + Right ⇒ el offset cae AFUERA.
- op2 interna = contorno CW (250,150→250,50→50,50→50,250→250,250→250,150) + Right ⇒ ADENTRO.
Confirma lo que dijo Fermín: por debajo es izquierda/derecha; Externo/Interno es la etiqueta
amigable para un lazo cerrado.

La geometría de la pieza (ContourType=Workpiece) es el rectángulo del panel, cerrado, arrancando
en el MEDIO del borde inferior (150,0) — derivable de las dimensiones (dx1,dy1).

## El ISO — DOS estilos de render distintos (¡clave!)

### op1 "Perfilado pieza" (Pieza / Externo / PASANTE, E001 Ø18.36 r=9.18) — OFFSET EXPLÍCITO

```
G0 X150.000 Y-9.180            ← arranque = medio del borde inf, YA offseteado afuera (−r)
G0 Z155.400                    ← TLC(125.4)+sec(30)
D1 / SVL 125.400 / SVR 9.180
G1 Z30.000 F2000.000           ← baja a security a feed de PLUNGE (patrón CAD/estrategia)
?%ETK[7]=4
G1 Z-19.000 F5000.000          ← plunge a −(18+1)=−19 (pasante+1) a feed de CORTE
G1 X300.000 Z-19.000 F5000     ← borde inferior offseteado (Y=−9.18)
G3 X309.180 Y0.000 I300 J0     ← ARCO de esquina, radio = r (9.18), centro en la esquina (300,0)
G1 Y300.000 Z-19.000           ← lado derecho offseteado (X=309.18)
G3 X300.000 Y309.180 I300 J300 ← arco esquina (300,300)
G1 X0.000 Z-19.000             ← borde superior (Y=309.18)
G3 X-9.180 Y300.000 I0 J300    ← arco esquina (0,300)
G1 Y0.000 Z-19.000             ← lado izquierdo (X=−9.18)
G3 X0.000 Y-9.180 I0 J0        ← arco esquina (0,0)
G1 X150.000 Z-19.000           ← vuelve al arranque por el borde inferior
G1 Z30.000 F5000               ← retrae a security
?%ETK[7]=0
G0 Z30.000
```
**Modelo Pieza/Externo**: coordenadas de OFFSET EXPLÍCITO (centro de fresa corrido r hacia
AFUERA), con un CUARTO DE ARCO en cada esquina convexa (radio = radio de fresa, centrado en la
esquina nominal, sentido G3), SIN G41/G42. Es el estilo CAD (N023 CAD) generalizado a un
rectángulo cerrado. Sin acercamiento (plunge recto en el arranque ya offseteado). Z estilo
estrategia (security a plunge feed, corte a cut feed). La traza almacenada (TrajectoryPath) YA
trae ese offset con arcos.

### op2 "Perfilado interno" (Geometría / Interno / ciego −9, E003 Ø9.52 r=4.76) — G42 NOMINAL

```
G0 X250.000 Y170.040           ← arranque (250,150) + lead-in 1mm sobre el 1er segmento (−y ⇒ +y? Y170)
G0 Z141.500
D1 / SVL 111.500 / SVR 4.760
?%ETK[7]=4
G42                            ← corrección C.N. (¡NO offset explícito!)
G1 X250.000 Y169.040 Z30.000 F3000   ← engancha G42 al arranque en security
G1 Y150.000 Z-9.000 F3000            ← plunge + 1er segmento
G1 Y50.000 Z-9.000 F18000
G1 X50.000 / G1 Y250.000 / G1 X250.000 / G1 Y150.000   ← cuadrado NOMINAL 50..250
G1 Y130.960 Z30.000            ← lead-out (1mm sobre el último segmento)
G40
G1 X250.000 Y129.960 Z30.000
```
**Modelo Geometría/Interno**: coordenadas NOMINALES + G41/G42 + lead-in/out de 1mm — IDÉNTICO
al fresado de polilínea cerrada (N042). El control empalma las esquinas.

## Síntesis del modelo — CORREGIDA (2026-07-14)

⚠️ **La primera versión de este análisis se equivocó de variable.** Yo había escrito que el
estilo de render lo decidía el `ContourType` (Pieza→offset / Geometría→G42) o el Lado. Al leer
el XML apareció la variable que ya conocíamos y que no había mirado:

| Operación | Perfil | Lado | **ActivateCNCCorrection** | Estilo ISO |
|---|---|---|---|---|
| Perfilado pieza | Workpiece | Externo | **false** (Corrección CAD) | offset explícito + arcos de esquina, SIN G41 |
| Perfilado interno | Geometry | Interno | **true** (Corrección C.N.) | NOMINAL + G42 + lead 1mm |

**Hipótesis principal (nueva)**: los "dos estilos de render del galceado" NO son propios del
galceado — son la **misma dicotomía CAD vs C.N.** ya derivada para el fresado LINEAL (N023 `_CAD`,
N036 `cad_*`): con `ActivateCNCCorrection=false` Maestro calcula la trayectoria al eje de la
herramienta y la hornea en coordenadas (estilo CAD); con `true` emite nominal + G41/G42 y deja
que el control compense. Acá está aplicada a un LAZO CERRADO.

Si se confirma, el galceado es en su mayor parte **REUSO**:
- C.N. (ACC=true) ⇒ es exactamente la **polilínea cerrada de N042**, que ya emitimos byte-idéntica.
- CAD (ACC=false) ⇒ es el estilo CAD del lineal, MÁS lo único genuinamente nuevo: el **arco de
  esquina** (radio = radio de fresa, centro en la esquina nominal) que aparece en cada vértice
  convexo de un lazo cerrado — una recta sola no tiene esquinas, por eso nunca lo vimos.

Y confirma la trayectoria almacenada: con ACC=false el `TrajectoryPath` YA trae el offset con
arcos (se ve el `309.18` = 300 + r(E001) en el XML). Con ACC=true trae la traza NOMINAL.

**El confound es de TRES variables**, no de dos: en el único archivo real, `ContourType`, `Lado`
y `ACC` van todas juntas (Workpiece+Externo+CAD vs Geometry+Interno+C.N.). El lote de exploración
tiene que romper las tres — y la primera que hay que romper es ACC, porque si decide ella, las
otras dos no tocan el estilo.

## Otros datos del archivo

- Programa con DOS contornos y CAMBIO DE HERRAMIENTA (T1 E001 → T3 E003): trae la transición
  entre dos operaciones de contorno (shutdown + doble park Z + header ATC), a derivar.
- Pasante op1: `z = −(espesor + 1)` (−19 con espesor 18). Extra 1mm.
- Ambas familia ROUTER (T{n}, S18000, mismo header/teardown que fresado).

## Lote de exploración N043_contour — diseño

**Los hace Fermín en Maestro**, no el sintetizador. Motivo: con `ACC=false` la trayectoria
almacenada YA trae el offset — o sea, la traza guardada ES la incógnita. Si yo autorara esos
fixtures tendría que inventar el offset hacia adentro (¿arcos cóncavos? ¿esquinas vivas?) y
Maestro postprocesaría MI hipótesis: derivaría de mí mismo. Circular. En cambio, tocar
Lado/Corrección en la UI son dos clics y la traza la calcula Maestro.

Base: pieza 300×300×18 (la de `Galceado.pgmx`). **Un contorno por archivo.** Para que las
diferencias sean atribuibles SOLO a las tres variables, todos con la MISMA fresa y profundidad:
**E003 Ø9.52, ciego −9, sin estrategia (una pasada), sin acercamiento/alejamiento.**

### Grupo A — romper el confound de ACC (lo primero: si decide ella, B y C no tocan el estilo)

| archivo | Perfil | Lado | Corrección | qué contesta |
|---|---|---|---|---|
| `N_GC_piece_ext_cad` | Pieza | Externo | CAD | baseline (= op1 del manual, aislada) |
| `N_GC_piece_ext_cnc` | Pieza | Externo | **C.N.** | ¿pasa a NOMINAL + G41? |
| `N_GC_geom_int_cnc` | Geometría | Interno | C.N. | baseline (= op2 del manual, aislada) |
| `N_GC_geom_int_cad` | Geometría | Interno | **CAD** | ¿pasa a OFFSET explícito? |

Si `_cnc` y `_cad` invierten el estilo ⇒ **ACC decide**, y ContourType/Lado no tienen nada que
ver con él. Hipótesis confirmada y el galceado pasa a ser casi todo reuso.

### Grupo B — el Lado (Externo/Interno), ya con el estilo fijado

| archivo | Perfil | Lado | Corrección | qué contesta |
|---|---|---|---|---|
| `N_GC_piece_int_cnc` | Pieza | Interno | C.N. | ¿G41 en vez de G42? ¿o invierte el winding? |
| `N_GC_geom_ext_cnc` | Geometría | Externo | C.N. | idem, del otro lado |
| `N_GC_piece_int_cad` | Pieza | Interno | CAD | offset hacia ADENTRO: ¿arcos cóncavos o esquinas vivas? |

### Grupo C — la curva

| archivo | Perfil | Lado | Corrección | qué contesta |
|---|---|---|---|---|
| `N_GC_geom_arc_cnc` | Geometría con un ARCO | Interno | C.N. | cómo trata un contorno no poligonal |

`Galceado.pgmx` (dos contornos + cambio de herramienta) queda como el caso de TRANSICIÓN, a
derivar después de fijar el render de un contorno solo.

## Pendiente para implementar (Eje B etapa 4)

1. Adapter: leer `ContourFeature` (+ `ContourType`) → un spec (¿`ContourMillingSpec` nuevo, o
   `PolylineSpec` + `contour_type`/`workpiece`?). Hoy el converter lo rechazaría
   (feature desconocida).
2. Autoría: `build_contour_spec` ya existe en pgmx — revisar si autora `ContourFeature`
   o hay que extenderla; contorno = pieza (derivar de dims) o geometría.
3. Render: dos estilos (offset explícito con arcos de esquina para Pieza/Externo; G42 nominal
   para Geometría/Interno) + estrategia/leads compartidos + transición multi-contorno.
4. Lote de exploración que AÍSLE ContourType × Lado × esquinas para fijar la regla del render.
