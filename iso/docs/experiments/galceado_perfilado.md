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

## Síntesis del modelo (hipótesis a confirmar con lote propio)

| Perfil | Lado | Render ISO |
|---|---|---|
| **Pieza** (Workpiece) | Externo | OFFSET EXPLÍCITO (coords corridas r afuera) + arcos de esquina (r), SIN G41 |
| **Geometría** | Interno | NOMINAL + G42 + lead 1mm (= polilínea N042) |

**Hipótesis principal**: el estilo de render lo decide el **ContourType** (Pieza→offset
explícito con arcos; Geometría→G41/G42 nominal), o bien **Externo→offset / Interno→G42**. En
este único archivo las dos variables van juntas (Pieza+Externo vs Geometría+Interno) — NO se
pueden separar. Un lote de exploración debe aislar: **Pieza+Interno**, **Geometría+Externo**,
**Geometría+Externo con esquinas vivas** (¿G41 o offset explícito?).

## Otros datos del archivo

- Programa con DOS contornos y CAMBIO DE HERRAMIENTA (T1 E001 → T3 E003): trae la transición
  entre dos operaciones de contorno (shutdown + doble park Z + header ATC), a derivar.
- Pasante op1: `z = −(espesor + 1)` (−19 con espesor 18). Extra 1mm.
- Ambas familia ROUTER (T{n}, S18000, mismo header/teardown que fresado).

## Pendiente para implementar (Eje B etapa 4)

1. Adapter: leer `ContourFeature` (+ `ContourType`) → un spec (¿`ContourMillingSpec` nuevo, o
   `PolylineSpec` + `contour_type`/`workpiece`?). Hoy el converter lo rechazaría
   (feature desconocida).
2. Autoría: `build_contour_spec` ya existe en pgmx — revisar si autora `ContourFeature`
   o hay que extenderla; contorno = pieza (derivar de dims) o geometría.
3. Render: dos estilos (offset explícito con arcos de esquina para Pieza/Externo; G42 nominal
   para Geometría/Interno) + estrategia/leads compartidos + transición multi-contorno.
4. Lote de exploración que AÍSLE ContourType × Lado × esquinas para fijar la regla del render.
