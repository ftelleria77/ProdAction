# El emisor: quién escribe materialmente el ISO

**Documento vivo.** Nació el 2026-08-12 de una pregunta que quedó abierta en
`anatomia_iso.md`: hay líneas del esqueleto que no salen del programa, ni de la
configuración de máquina, ni de la ventana Opciones — **las escribe el binario que genera
el ISO**. La pregunta era si eso constituye un cuarto origen. La copia completa de la PC
del CNC la respondió el mismo día.

## ⭐⭐ El postproceso tiene DOS etapas, y casi todo lo que investigamos vive en la segunda

**2026-08-12.** El paso 0 —postprocesar el programa base en la PC de oficina técnica— no
produjo ningún `.iso`. Produjo **otros tres archivos**, y ahí estaba el hallazgo:

| Archivo | Qué es |
|---|---|
| `R_PV_manual_base_Of_Tec.xxl` | el programa en **XXL**, formato de texto de Xilog |
| `R_PV_manual_base_Of_Tec.pgm` | el mismo, **compilado a binario** (`BMB … Xilog3-9.0`) |
| `R_PV_manual_base_Of_Tec.inf` | el log del compilador: `XXL/PGM Compiler Version 9.0`, `[LINES]=16`, `[ERRORS]=0` |

⇒ La cadena es **`.pgmx` → XXL → PGM → ISO**, y lo que se detuvo fue el último tramo. Los
tres archivos están versionados en `evidencia/paso0_oficina_tecnica/`.

### El XXL del programa vacío, entero

```
H DX=400.000 DY=400.000 DZ=18.000 -HG C=0 T=0 R=1 *MM /"def" BX=0.000 BY=0.000 BZ=0.000 V=0
;**********************************************************
; >> Post P. Release...
;Versione : 1.00.006.1010;
; >> Descrizione del programma...
; Data di creazione: 8/12/2026 8:19:19 PM
;
; >> Utensili utilizzati...
;
; >> Inizio Programma...
;**********************************************************
.END
;**********************************************************
F=1
O X=0 Y=0 Z=0 F=1 ;ChangePlane
;FINEPROG
```

**Dieciséis líneas contra las 43 del ISO.** Y la comparación de los dos headers dice dónde
ocurre cada cosa:

| | XXL (lo que produce Maestro) | ISO (lo que produce el generador) |
|---|---|---|
| forma | `H DX=…` — **instrucción** | `;H DX=…` — **comentario** |
| orden | `DX DY DZ -HG C T R *MM /"def" BX BY BZ V` | `DX DY DZ BX BY BZ -HG V *MM C T` |
| `R=1` | **está** | **no está** |
| `/"def"` (equipamiento) | **está** | **no está** |
| origen | `O X=0 Y=0 Z=0 F=1 ;ChangePlane` — **sin resolver** | `%Or[0].ofX=-400000.000` · `SHF[X]=-400.000` — **resuelto** |

Tres cosas quedan derivadas de una:

1. ✅ **`R` (repeticiones) se pierde en la segunda etapa.** Estaba anotado como hipótesis
   («el emisor omite la letra cuando vale el default»). Ahora se ve: Maestro **sí** lo
   escribe (`R=1`) y el ISO no lo lleva. La omisión no es de Maestro.
2. ✅ **El nombre del equipamiento (`/"def"`) tampoco sobrevive** al paso a ISO.
3. ⭐ **El origen se resuelve en la SEGUNDA etapa.** Maestro emite `O X=0 Y=0 Z=0`, el
   origen del programa tal cual; los `−400.000` y `−1515.600` de `fields.cfg` **los pone el
   generador de Xilog**, no Maestro. Toda la fórmula de B1c pertenece a esa etapa.

### Por qué esto reordena el modelo de orígenes

| Etapa | Quién | Qué aporta |
|---|---|---|
| 1 · `.pgmx` → XXL | **Maestro** | el programa (origen 1) y su configuración de aplicación (origen 3) |
| 2 · XXL/PGM → ISO | **el generador de Xilog** | `fields.cfg`, `NCI.CFG`, el `SHF`, los `%Or`, el teardown de mesa (origen 2 + el emisor) |

**Esto explica el resultado que más se repitió en el barrido**: de 17 opciones de la ventana
Opciones, sólo una llega al ISO. No es que el ISO las ignore — es que esas opciones actúan
en la **etapa 1**, y sólo llegan al ISO las que Maestro alcanza a escribir en el XXL. El
estacionamiento automático llega porque Maestro lo escribe; las de traza no llegan **en un
programa vacío** porque no hay trayectoria que escribir.

### El XXL como intermedio observable

Hasta hoy la investigación tenía dos puntos: el `.pgmx` (entrada) y el `.iso` (salida). El
XXL es **el paso del medio, en texto legible**. Cuando una línea del ISO no se entienda, se
puede preguntar si ya estaba en el XXL — y eso dice en cuál de las dos etapas nace.

## Por qué oficina técnica no llega al ISO

Lo que se sabe:

- **`PostFileFormat` vale `ISO` en las dos PCs** — no es la opción.
- **El compilador XXL/PGM terminó sin errores** (`[ERRORS]=0`) y dejó sus temporales en
  `<Xilog Plus>\WinXisoTemp\` (`.pgm`, `.r00`, `_AGRep.grp`, `_EIODataStep.sds`).
- `Winxiso.exe` y los DLL del generador **están** en las dos instalaciones.
- Toda la configuración de Xilog (`Cfg\`, 82 archivos) es **byte-idéntica** entre las dos, y
  `NCI.CFG` —con su `$GEN_ISO_FOR_EXTERNAL_APP = 1`— también.
- En `WinXisoTemp\` hay un caso anterior, de **marzo de 2025**, con exactamente el mismo
  patrón y sin `.iso` ⇒ **esta instalación no generó ISO nunca**, no es algo que se rompió
  hoy.

Lo que queda como candidato, por descarte: la diferencia está en **los binarios del
generador** (que difieren entre las dos PCs, ver abajo) o en algo fuera de `Cfg\` —
habilitación, licencia o instalación. Que la versión de oficina técnica sea justamente la
que tiene las plantillas del header **en formato PGM** encaja con lo observado, pero
contigüidad no es prueba.

### La consecuencia práctica, que importa hoy

**El barrido de opciones no se puede mudar a oficina técnica**: hay que seguir haciéndolo en
el CNC. Era la pregunta que el paso 0 venía a responder, y quedó respondida — con un «no»,
que también es respuesta.

Y el experimento de las dos PCs para las claves de traza (`RadiusMultiplier`,
`SecurityDistance`) **no se puede hacer como estaba planteado**: si una de las dos no emite
ISO, no hay dos ISO que comparar. Habría que compararlos en XXL, que es lo que las dos sí
producen — y ahí se vería si esas claves se congelan en la etapa 1.

## Quién genera el ISO

No lo genera Maestro por su cuenta: usa el **generador de Xilog Plus**, y la clave que lo
habilita está en el `NCI.CFG` de la máquina, en la primera línea del archivo:

```
$GEN_ISO_FOR_EXTERNAL_APP
1
```

Los módulos que aportan las líneas del esqueleto (`anatomia_iso.md`, B1g) son:

| Binario | Qué aporta |
|---|---|
| `PostISO.dll` | el bloque de puesta a punto, `SYN`, los `?%EDK[…]`, la tabla de códigos G y M |
| `PlPathFilter32.dll` | el teardown (`MLV`/`SHF`/`VL6`/`VL7`), dentro de su bloque de **mesa** |
| `VtGenIso.dll` | plantillas de `MLV`/`SHF` y el bloque del láser de cruce |
| `nci32.dll` | códigos G y las plantillas del header |

## ⭐ Las dos PCs NO tienen el mismo emisor (2026-08-12)

Comparación por sha256 entre la copia completa del CNC (`S:\Copia CNC`) y la instalación de
oficina técnica. **Los seis binarios difieren.**

| Binario | CNC | Oficina técnica |
|---|---|---|
| `PostISO.dll` | 262.144 B · **2011-11-18** | 262.144 B · 2011-10-14 |
| `PlPathFilter32.dll` | 184.320 B · **2011-11-18** | 184.320 B · 2011-10-14 |
| `VtGenIso.dll` | 262.144 B · **2011-11-18** | 262.144 B · 2011-10-14 |
| `nci32.dll` | **319.488 B** · **2011-11-18** | **315.392 B** · 2011-10-14 |
| `Nci.dll` · `ChkPgm32.dll` | difieren | difieren |

**El CNC tiene la build más nueva**, de un mes después. Y la diferencia no es cosmética:
`nci32.dll` además **pesa 4 KB más** y su tabla de cadenas cambió. Las plantillas del
header en formato PGM (`(H DX%.*f`, ` BX%.*f`, ` BY%.*f`, …) están **sólo en la versión de
oficina técnica**; la del CNC no las tiene.

> ⚠️ **Ninguno de estos DLL tiene número de versión** (`FileVersion` vacío: son de 2011).
> Su identidad sólo puede ser **fecha + tamaño + hash**, como el `manifest.csv`.

### Qué se sigue de esto

1. **El emisor es un origen.** No es «el binario hace siempre lo mismo»: hay dos emisores
   distintos conviviendo en el taller, y difieren justamente en plantillas de emisión.
2. **Toda evidencia queda fechada contra un emisor.** Un ISO de referencia prueba lo que
   emite *esa* build. Los ISO de la serie R salieron todos del CNC, así que son
   consistentes entre sí — pero no son transferibles a la otra PC sin verificar.
3. **Sube el valor del paso 0** (postprocesar el programa base en oficina técnica). Ya no
   es confirmar lo esperado: ahora hay un motivo concreto para que pueda dar distinto, y
   el resultado importa igual en los dos sentidos.

### Lo que este hallazgo NO dice

Que los binarios difieran **no prueba** que el ISO difiera. Las diferencias podrían estar
en rutas de código que este esqueleto no ejercita, y la evidencia disponible apunta a que
buena parte del preámbulo y del cierre viene de `NCI.CFG` —que **sí es idéntico en las dos
PCs**, igual que `Nci.ini`—. El paso 0 es exactamente el experimento que lo separa.

## El matiz que ordena todo esto: config vacía, no constante

De B1h: los binarios consultan **30 claves `$…`** que ningún archivo de la instalación
define (`$MA_*` de mesa, `$PM_*` de macros de archivo/bloque/ciclo, y `$KEY_G%d`/`$KEY_M%d`
para la traducción de cada código G y M).

⇒ Casi todo lo que parecía «constante del binario» es en realidad **el valor por defecto de
una clave de configuración que nadie escribió**. El mecanismo es el mismo de `NCI.CFG`, no
uno nuevo: el emisor lee configuración, y cuando no la encuentra tiene un default.

El emisor incluso trae su propio fail-loud: si no encuentra la clave de un código G escribe
`;G%d: CORRISPONDENZA NON TROVATA!` **dentro del ISO**.

## Decisión pendiente

**¿El snapshot incluye al emisor?** Hoy el snapshot guarda configuración (93 archivos) y no
guarda los binarios que la consumen. Con dos emisores distintos en el taller, la opción
conservadora es registrar al menos **su identidad** (nombre, tamaño, fecha y sha256) junto
al resto del manifest, sin necesariamente versionar 1 MB de DLL.

Es decisión de Fermín. Lo que cambia: con el emisor registrado, el converter puede declarar
contra qué build se derivó cada regla y **fallar ruidosamente** si el ISO de referencia
salió de otra. Sin registrarlo, esa diferencia es invisible.

## Herramienta

```
py -m iso.machining_lab.buscar_en_binarios barrer "VL[67]=" "SHF\[Z\]"
py -m iso.machining_lab.buscar_en_binarios contexto <binario> "^SYN$"
```
