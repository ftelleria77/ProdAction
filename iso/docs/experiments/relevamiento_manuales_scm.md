# Relevamiento de los manuales de SCM — material CRUDO

**Este documento NO saca conclusiones.** Es el material tal como aparece en la
documentación y en los archivos de la instalación, con su cita textual y su
ubicación, para estudiarlo con Fermín. Cualquier interpretación va a otro lado,
y recién después de mirarlo juntos.

Origen: relevamiento del 2026-08-10 sobre la instalación
`C:\Program Files (x86)\Scm Group\` (Maestro + Xilog Plus), la ayuda CHM extraída
(Xilog Plus Editor en español e inglés, EPL, PanelMac), el manual
`Maestro Editor.pdf` en español, y las transcripciones que ya teníamos en
`pgmx/docs/`.

Marcas: **exacto** = el término aparece igual; **parecido** = aparece algo similar
pero no idéntico, y queda a criterio de Fermín si sirve.

## EDK

### `%EDK[0].0, %EDK[1].0, %EDK[13].0`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\rebaje laterales.iso`
  ·  **Sección:** Cabecera del programa (lineas 1-21) y cierre del programa (lineas 114-133). Archivo ISO producido por el postprocesador, dentro de la carpeta PostProcessor de la instalacion (fuente 8). NO es documentacion: es una salida.
  ·  **Idioma:** n/a (codigo ISO)

```
% rebaje laterales.pgm
;H DX=704.000 DY=549.550 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
%Or[0].ofX=-704000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=43000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-704.000 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 

[... lineas 22-113 ...]

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

### `%EDK[0].0, %EDK[1].0, %EDK[13].0`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\lado_derecho1.iso`
  ·  **Sección:** Cabecera (lineas 7-21) y cierre (lineas 329-350)
  ·  **Idioma:** n/a (codigo ISO)

```
G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
%Or[0].ofX=-354549.988 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=43000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-354.550 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 

[... hasta el cierre ...]

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

### `%EDK[0].0, %EDK[1].0, %EDK[13].0`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\pieza 300x300 calxy.iso`
  ·  **Sección:** Cabecera (lineas 8-21) y cierre (lineas 129-148)
  ·  **Idioma:** n/a (codigo ISO)

```
M58 
G71 
MLV=0 
%Or[0].ofX=-305000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=50000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-305.000 
SHF[Y]=-1515.750 
SHF[Z]=50.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 

[... hasta el cierre ...]

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

### `%EDK[0].0, %EDK[1].0, %EDK[13].0`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\prubafresas.iso`
  ·  **Sección:** Cabecera (lineas 8-21) y cierre (lineas 218-237)
  ·  **Idioma:** n/a (codigo ISO)

```
M58 
G71 
MLV=0 
%Or[0].ofX=-300000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=43000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-300.000 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 

[... hasta el cierre ...]

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

### `%EDK[0].0, %EDK[1].0, %EDK[13].0`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\lado_izquierdo1.iso`
  ·  **Sección:** Cabecera (lineas 8-21) y cierre (lineas 466-485)
  ·  **Idioma:** n/a (codigo ISO)

```
M58 
G71 
MLV=0 
%Or[0].ofX=-747000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=43000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-747.000 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 

[... hasta el cierre ...]

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

### `?%%EDK[%d].0=1 / ?%%EDK[%d].0=0 / ?%%EDK[1].0=%d / ?%%EDK[0].0=%d (cadenas de formato printf)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\PostISO.dll (binario; cadenas ASCII legibles en los offsets 0x36113 y 0x36617)`
  ·  **Sección:** Tabla de cadenas del generador ISO. Transcribo el bloque contiguo de cadenas imprimibles tal cual aparece, una por linea; NO es prosa de manual, son literales del programa.
  ·  **Idioma:** n/a (cadenas de codigo; los comentarios vecinos estan en italiano)

```
Bloque en 0x36113:
G310 D1 L0 R(0) 
G310 D1 L%.3f R(%.3f)
M186
M185
M58 ;E30xxx=%ld,%ld
M39 ;E30xxx=%ld
M38 ;E30xxx=%ld
M29 ;E30xxx=%ld
M59 ;E30xxx=%ld,%ld
$KEY_M59
M28 ;E30xxx=%ld
?%%EDK[%d].0=0
$KEY_M%d
?%%ETK[132]=%d
?%%ETK[130]=%d
G300 A%.3f B%.3f C%.3f Q%.3f R%.3f U%.3f V%.3f W%.3f
G162 I%d J%d K%d
G300 S0
G120
$KEY_G80
G106 T
?%%ETK[%d]=%d
 E=0x%08X
;T%d S=%d P=%d
?%%ETK[%d]=%d
?%%ETK[%d]=201
%s%d
;G%d: CORRISPONDENZA NON TROVATA!
G162 I%d J%d K%d

Bloque en 0x36617:
;Xrel=%c%cmac,
?%%ETK[113]=VA2*1000
?%%ETK[112]=VA1*1000
?%%ETK[111]=VA0*1000
VA2=GET(Z)
VA1=GET(Y)-%g
G210 %c((-%g)+(%g))
VA1=GET(Y)
VA0=GET(X)-%g
VA0=GET(X)
G210 %c((%g)+(%g))
PRB%d
G110 T%g
G4F0
G300 S0
?%%EDK[1].0=%d
?%%EDK[0].0=%d
%%ETK[114]
%%L[%d]
%%L[%d]=
G169
?%%EDK[%d].0=1
G168
PostISO.cfg
%s%s
..\CFG\
ISO-OSAI(2)
ISO-OSAI(2) LUA
ISO-ORCHESTRA LUA
ISO-ESAGV(2) LUA
ISO-ESAGV(2)
ISO-NUM LUA
ISO-NUM ERGON
ISO-ORCHESTRA
```

### `?%%EDK[%d].0=1 / ?%%EDK[%d].0=0 (cadenas de formato printf)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\VtGenIso.dll (binario; offset 0x3AD93)`
  ·  **Sección:** Bloque de cadenas contiguo al identificador GEN_CROSSLASER_INIT / GEN_CROSSLASER_FREE. Literales del programa, no manual.
  ·  **Idioma:** n/a (comentarios embebidos en italiano: ';Testa Laser con Motore Numero %d - LKey %d', ';Angolo=%.3f', ';Motore=%d,Strobe=%u')

```
EN_CROSSLASER_ID
GEN_CROSSLASER_ORIGIN_INIT
GEN_CROSSLASER_FREE
GEN_CROSSLASER_INIT
?%%ETK[7]=%ld
;LKey
G0X%.3fY%.3f
?%%ETK[6]=%ld
;Angolo=%.3f
?%%ETK[8]=%ld
;Motore=%d,Strobe=%u
MLV=2
VL5=2
SHF[X]=%.3f
SHF[Y]=%.3f
;Testa Laser con Motore Numero %d - LKey %d
MLV=1
VL5=1
SHF[X]=%.3f
SHF[Y]=%.3f
?%%ETK[7]=0
?%%ETK[8]=0
?%%EDK[%d].0=1
?%%EDK[%d].0=0
?%%ETK[7]=0
SVL 0.000
SVR 0.000
MLV=0
VL5=0
G0G53Z%.3f
(DLY,0.2)
E1011=%ld
E1010=%ld
E1012=%ld
(UIO, X%.3f,Y%.3f)
(AXO,-Z,X)
(UTO,1,X(%.3f),Y(%.3f))
```

### `?%%EDK[%d].0=0 / ?%%EDK[%d].0=1 (cadenas de formato printf)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\PlPathFilter32.dll (binario; offset 0x29F93)`
  ·  **Sección:** Bloque de cadenas junto a $MA_END3_FILE / $MA_END5_FILE / $MA_RESTORE_END. Literales del programa, no manual.
  ·  **Idioma:** n/a (comentarios embebidos en italiano)

```
%%Area[%d].kLimPA=%ld
 %%Area[%d].kLimNA=%ld
;Limiti area di lavoro
$PM_INIT_FILE_MAC_%d
G1 X%.3f F%s
;Posizionamento Traversa %d
$MA_XY_Z
$MA_SET_POSITION
G1 X%.3f Y%.3f F%s
$MA_Z_XY
G1 Z%.3f F%s
$MA_SET_INFO
G0 Z%.3f
G0 X%.3f Y%.3f
;Posizionamento Ventosa %d della Traversa %d
?%%EDK[%d].0=0
VL6=0
VL7=0
MLV=2
SHF[X]=0
SHF[Y]=0
SHF[Z]=0
MLV=1
SHF[X]=0
SHF[Y]=0
SHF[Z]=0
?%%EDK[%d].0=1
$MA_END3_FILE
MLV=0
$MA_END5_FILE
G300 S0
G169
G333
$MA_RESTORE_END
;Cancellazione Ventosa %d della Traversa %d
$MA_CHANGE_END
MLV=0
G0G53Z%.3f
MLV=2
;Attesa conferma cambiamenti da parte dell'Operatore!
;Trascinamento Ventose della Traversa %d
$MA_RESTORE_POSITION
Standard_Manina
$MA_RESTORE_INFO
```

### `indices EDK encontrados: recuento completo de ocurrencias en toda la instalacion`

**Fuente:** `C:\Program Files (x86)\Scm Group\ (barrido recursivo, incluyendo binarios)`
  ·  **Sección:** Recuento de coincidencias del patron EDK[<n>].<bit>. Es el resultado de mi busqueda, no una cita de manual: lo incluyo para que se vea que NO hay ningun indice fuera de 0, 1 y 13.
  ·  **Idioma:** n/a

```
10 EDK[13].0
     6 EDK[1].0
     6 EDK[0].0
     6 EDK[%d].0
```

### `EDK (coincidencia de subcadena dentro de una palabra danesa)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\Languages\da-DK\ToolManager.xml`
  ·  **Sección:** Cadenas de traduccion al danes (cuttingComponentDescentSpeedHeader / technologyDescentSpeedHeader / spindleComponentDescentSpeedHeader)
  ·  **Idioma:** danes

```
<!--View del componente di taglio dell'utensile-->
	<string code="cuttingComponentDescentSpeedHeader">Nedkørings hastighed</string>
	<string code="cuttingComponentDescentSpeedMinLabel">Minimum</string>
	<string code="cuttingComponentDescentSpeedMaxLabel">Maximum</string>
[...]
<!--View dei dati tecnologici dell'utensile o aggregato-->
	<string code="technologyDescentSpeedHeader">Nedkørings hastighed</string>
[...]
	<string code="spindleComponentDescentSpeedHeader">Nedkørings hastighed</string>

PARECIDO, NO IDENTICO: 'EDK' aparece solo como las letras centrales de 'NedKørings' con busqueda insensible a mayusculas. No es el termino EDK.
```

### `eDk[ (coincidencia de bytes dentro de un .chm comprimido)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Country\{Ing,Heb,Slo,Rus,Ola,Cze,Jap,Chi}\Xilog_Plus_Editor.chm (archivo comprimido, sin descomprimir)`
  ·  **Sección:** Coincidencia cruda de bytes en el flujo comprimido del CHM. Al descomprimir esos mismos CHM (out_editor_ing, out_spa) NO hay ninguna ocurrencia de EDK en el HTML.
  ·  **Idioma:** n/a

```
eDk[

PARECIDO, NO IDENTICO: es la unica secuencia que devuelve la busqueda sobre el binario comprimido; el texto descomprimido de esas mismas ayudas no contiene EDK.
```

**No aparece en ninguna fuente:** `EDK[10] / %EDK[10] — NO APARECE en ninguna fuente. Los unicos indices literales que existen en toda la instalacion son EDK[0], EDK[1] y EDK[13] (mas el generico EDK[%d] en las cadenas de formato de los DLL).`, `%EDK — NO APARECE en la ayuda del Xilog Plus Editor en ESPAÑOL (out_spa, 1436 archivos): cero coincidencias, con y sin %, con y sin corchetes, en mayusculas y minusculas.`, `%EDK — NO APARECE en la ayuda del Xilog Plus Editor en INGLES (out_editor_ing, 1434 archivos): cero coincidencias.`, `%EDK — NO APARECE en la ayuda del modulo EPL (out_epl, 210 archivos): cero coincidencias.`, `%EDK — NO APARECE en la ayuda de PanelMac (out_panelmac, 271 archivos): cero coincidencias.`, `%EDK — NO APARECE en el manual del Maestro Editor en español (maestro_editor_es.txt, 170 paginas): cero coincidencias.`, `%EDK — NO APARECE en pgmx/docs/xilog_plus_pgm/ ni en pgmx/docs/maestro_scripting/: cero coincidencias.`, `EDK[n].0 (la notacion con el .0 al final) — NO APARECE DOCUMENTADA en ninguna ayuda. Mas aun: la notacion de sufijo ].<digito> no aparece en ningun archivo .htm de ninguna de las ayudas (las unicas coincidencias del patron estan dentro de imagenes .jpg, es decir bytes de imagen).`, `Tabla de indices de la familia EDK — NO APARECE. No hay tabla, lista ni glosario de indices EDK en ninguna de las 8 fuentes.`, `Definicion o descripcion en prosa de que es la familia EDK — NO APARECE en ninguna fuente. Solo hay usos: 5 archivos .iso de salida en Maestro\PostProcessor y cadenas de formato en 3 DLL (PostISO.dll, VtGenIso.dll, PlPathFilter32.dll).`, `%EDK — NO APARECE en las ayudas que extraje ademas de las pedidas, para descartar: Xilog_Plus_WinXiso.chm (español, ingles y la del directorio raiz), Testine.chm (español) y XilogMaestroScripting.chm (es-ES).`, `%EDK — NO APARECE en los PDF del Maestro Editor en ingles, italiano ni aleman (scratchpad/pdfs/maestro_en-US.txt, maestro_it-IT.txt, maestro_de-DE.txt).`, `%EDK — NO APARECE en ninguno de los 142 archivos .txt sueltos de la instalacion (MACRO_STD.TXT, FERRAMENTA.TXT, ERGON.txt, SCM.txt, MBD.txt, XIMULA.TXT, ASSEMBLAGGIO.TXT, cerniere.TXT y sus variantes por idioma), ni en los .msg, .cfg, .tab, .ini, ni en WINXISO.HLP. Verificado tambien con lectura UTF-16.`

## ETK

### `%%ETK[500] (y %%ax[0].pa[22], _paras)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Cfg\NCI.CFG`
  ·  **Sección:** $GEN_INIT (bloque de inicialización del generador ISO)
  ·  **Idioma:** italiano (comentarios) / código ISO

```
$GEN_ISO_FOR_EXTERNAL_APP
1
$
$GEN_INIT
?%%ETK[500]=100
;?%%ETK[500]=%%ax[0].pa[22]/1000 ;solo per zone
_paras( 0x00, X, 3, %%ax[0].pa[21]/1000, %%ETK[500] )
;
G0 G53 Z %%ax[2].pa[22]/1000
M58 ;abilita controllo vuoto
$
```

### `%%ETK[0], %%ETK[1], %%ETK[2], %%ETK[13], %%ETK[17], %%ETK[18], %%ETK[19]`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Cfg\NCI.CFG`
  ·  **Sección:** $GEN_END (bloque de cierre del generador ISO)
  ·  **Idioma:** código ISO (sin texto en prosa)

```
$GEN_END
?%%ETK[0]=0
?%%ETK[1]=0
?%%ETK[2]=0
?%%ETK[13]=0
?%%ETK[17]=0
?%%ETK[18]=0
?%%ETK[19]=0
$
```

### `%%ETK[0], %%ETK[1], %%ETK[2], %%ETK[13], %%ETK[17], %%ETK[18], %%ETK[19]`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Cfg\NCI_ORI.CFG`
  ·  **Sección:** $GEN_END (misma sección, versión _ORI del archivo)
  ·  **Idioma:** código ISO (sin texto en prosa)

```
$GEN_INIT
M150
$
$GEN_END
?%%ETK[0]=0
?%%ETK[1]=0
?%%ETK[2]=0
?%%ETK[13]=0
?%%ETK[17]=0
?%%ETK[18]=0
?%%ETK[19]=0
SYN JSR 8900
$
```

### `%ETK[500]`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Fxc\Mbd\Park.pgm (archivo binario de macro; cadena extraída en offset 10059)`
  ·  **Sección:** Macro "6g,,0,park" — último bloque de la macro. Es el ÚNICO lugar de todas las fuentes donde un ETK aparece acompañado de un comentario descriptivo.
  ·  **Idioma:** italiano

```
ISO "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )" ;Ripristino limitazione corsa positiva X di anticollisione
```

### `%ax[0].pa[21] / %ax[0].pa[22] (contraparte del %ETK[500] en la misma macro)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Fxc\Mbd\Park.pgm (cadenas extraídas del binario)`
  ·  **Sección:** Macro "6g,,0,park", ramas IF AREA=...
  ·  **Idioma:** italiano

```
IF AREA=1 OR AREA=2 OR AREA=12 OR AREA=21 OR AREA=14 THEN
ISO "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ax[0].pa[22]/1000 )" ;Ripristino corsa totale asse X
ISO "G0G53 X%ax0.pa31/1000 Y%ax1.pa22/1000"
FI
```

### `%ETK[106].0`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Fxc\Mbd\xnop.pgm (archivo binario de macro; cadenas en offsets 32846 y 32863)`
  ·  **Sección:** Macro "2g,XY,135,cyc.msg" (cabecera del archivo: '2g,XY,135,cyc.msg')
  ·  **Idioma:** código ISO (sin comentario)

```
?%ETK[106].0=1
ISO "?%ETK[106].0=1"
```

### `%%ETK[132], %%ETK[130], %%ETK[%d], %%ETK[%d]=201`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\PostISO.dll (tabla de cadenas de formato, offsets 221456–221732)`
  ·  **Sección:** Bloque de plantillas de emisión ISO, contiguo a $KEY_M59 / $KEY_G80 / G106
  ·  **Idioma:** código / italiano (mensaje de error)

```
@221456  ?%%EDK[%d].0=0
@221488  $KEY_M%d
@221500  ?%%ETK[132]=%d
@221516  ?%%ETK[130]=%d
@221532  G300 A%.3f B%.3f C%.3f Q%.3f R%.3f U%.3f V%.3f W%.3f
@221589  G162 I%d J%d K%d
@221608  G300 S0
@221624  G120
@221636  $KEY_G80
@221648  G106 T
@221657  ?%%ETK[%d]=%d
@221672   E=0x%08X
@221684  ;T%d S=%d P=%d
@221700  ?%%ETK[%d]=%d
@221716  ?%%ETK[%d]=201
@221732  %s%d
@221744  ;G%d: CORRISPONDENZA NON TROVATA!
```

### `%%ETK[114], %%ETK[113], %%ETK[112], %%ETK[111]`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\PostISO.dll (tabla de cadenas de formato, offsets 222292–222788)`
  ·  **Sección:** Bloque de plantillas G161 / G305 / palpado (PRB) y variables VA0-VA2
  ·  **Idioma:** código (sin prosa)

```
@222292  G161 X((%.3f)+(%.3f)) Y((%.3f)+(%.3f)) Z((%.3f)+(%.3f)+(%%ETK[114]/1000))
@222368  G305 I%.3f J%.3f K%.3f P%.3f Q%.3f R%.3f U%.3f V%.3f W%.3f M%.3f N%.3f O%.3f S1
@222452   Zrel=%c%cmac
@222468   Yrel=%c%cmac,
@222484  ;Xrel=%c%cmac,
@222500  ?%%ETK[113]=VA2*1000
@222524  ?%%ETK[112]=VA1*1000
@222548  ?%%ETK[111]=VA0*1000
@222572  VA2=GET(Z)
@222584  VA1=GET(Y)-%g
@222600  G210 %c((-%g)+(%g))
@222624  VA1=GET(Y)
@222636  VA0=GET(X)-%g
@222652  VA0=GET(X)
@222664  G210 %c((%g)+(%g))
@222684  PRB%d
@222704  G110 T%g
@222720  G4F0
@222728  G300 S0
@222740  ?%%EDK[1].0=%d
@222756  ?%%EDK[0].0=%d
@222776  %%ETK[114]
@222788  %%L[%d]
```

### `%%ETK[7], %%ETK[6], %%ETK[8]`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\VtGenIso.dll (tabla de cadenas de formato, offsets 240532–241131)`
  ·  **Sección:** Bloque GEN_CROSSLASER_* / H%02d_CROSSLASER_ON-OFF. Los comentarios ';LKey', ';Angolo=%.3f' y ';Motore=%d,Strobe=%u' aparecen en la cadena inmediatamente siguiente a cada ETK.
  ·  **Idioma:** italiano (comentarios) / código

```
@240532  H%02d_CROSSLASER_OFF
@240556  H%02d_CROSSLASER_ON
@240576  GEN_CROSSLASER_STANDBY
@240600  GEN_CROSSLASER_LKEY
@240620  GEN_CROSSLASER_MOVE_TO
@240644  GEN_CROSSLASER_ANG_ID
@240668  GEN_CROSSLASER_TRA_ID
@240692  GEN_CROSSLASER_ID
@240712  GEN_CROSSLASER_ORIGIN_INIT
@240740  GEN_CROSSLASER_FREE
@240760  GEN_CROSSLASER_INIT
@240780  ?%%ETK[7]=%ld
@240794  ;LKey
@240804  G0X%.3fY%.3f
@240820  ?%%ETK[6]=%ld
@240834  ;Angolo=%.3f
@240847  ?%%ETK[8]=%ld
@240861  ;Motore=%d,Strobe=%u
@240884  MLV=2
@240890  VL5=2
@240896  SHF[X]=%.3f
@240908  SHF[Y]=%.3f
@240924  ;Testa Laser con Motore Numero %d - LKey %d
@240976  MLV=1
@240982  VL5=1
@240988  SHF[X]=%.3f
@241000  SHF[Y]=%.3f
@241016  ?%%ETK[7]=0
@241028  ?%%ETK[8]=0
@241040  ?%%EDK[%d].0=1
@241059  ?%%EDK[%d].0=0
@241080  ?%%ETK[7]=0
```

### `%%ETK[904], %%ETK[903]`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\PlPathFilter32.dll (cadenas en offsets 172416 y 172446)`
  ·  **Sección:** Tabla de cadenas del filtro de trayectoria. Son los dos únicos ETK del módulo y ambos traen comentario en italiano en la misma cadena.
  ·  **Idioma:** italiano

```
?%%ETK[904]=%d ;utensile
?%%ETK[903]=%d ;traverse
```

### `%ETK[500], %ETK[114] (uso real en ISO emitido por Maestro)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\prubafresas.iso (líneas 1-32)`
  ·  **Sección:** Cabecera del programa ISO y primer cambio de herramienta
  ·  **Idioma:** código ISO

```
% prubafresas.pgm
;H DX=300.000 DY=300.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
...
SHF[X]=-300.000 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 
?%ETK[8]=1 
G40 
?%ETK[8]=1 
G40 
MLV=0 
T1 
SYN
M06
?%ETK[6]=1   
?%ETK[9]=1   
?%ETK[18]=1  
S18000M3 
G17
```

### `%ETK[13], %ETK[7], %ETK[18] (uso real en ISO emitido por Maestro)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\prubafresas.iso (líneas 42-71)`
  ·  **Sección:** Cuerpo de una pasada de fresado y su cierre
  ·  **Idioma:** código ISO

```
SHF[Z]=43.000 
MLV=2 
?%ETK[13]=1  
MLV=2 
SHF[X]=31.900 
...
VL7=9.180
G1 Z-1.000 F2000.000 
?%ETK[7]=4 
G1 X100.000 Z-1.000 F3000.000 
?%ETK[7]=0 
G0 Z20.000 
D0 
...
G0 G53 Z201.000 
MLV=2
?%ETK[13]=0   
?%ETK[18]=0 
M5 
MLV=0
```

### `%ETK[17], %ETK[0], %ETK[1] (uso real en ISO emitido por Maestro)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\lado_izquierdo1.iso (líneas 94-121, 218-224, 348-357, 383-386)`
  ·  **Sección:** Bloques de taladrado / cabezal perforador y cambios de SHF
  ·  **Idioma:** código ISO

```
SHF[X]=-64.000 
SHF[Y]=0.000 
SHF[Z]=0.000 
?%ETK[17]=257  
S6000M3 
?%ETK[0]=48 
G0 X129.000 Y36.550 
G0 Z115.000 
?%ETK[7]=3 
...
SHF[X]=-96.000 
SHF[Y]=0.000 
SHF[Z]=0.000 
?%ETK[0]=32 
G0 X329.000 Y156.550 
...
SHF[X]=-65.250 
SHF[Y]=-31.700 
SHF[Z]=66.550 
?%ETK[0]=2147483648 
G4F0.500 
G0 X827.000 Y95.550 
...
MLV=0
G0 G53 Z201.000 
MLV=2
?%ETK[0]=0
?%ETK[6]=82   
G17 
?%ETK[17]=257  
S4000M3 
?%ETK[1]=16 
MLV=2 
SHF[X]=-96.000 
...
MLV=0
G0 G53 Z201.000 
MLV=2
?%ETK[1]=0
MLV=1 
SHF[Z]=25.000+%ETK[114]/1000
```

### `%ETK[0], %ETK[1], %ETK[2], %ETK[13], %ETK[17], %ETK[18], %ETK[19] (cierre real del ISO)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\lado_izquierdo1.iso (últimas 30 líneas)`
  ·  **Sección:** Pie del programa ISO (corresponde al bloque $GEN_END de NCI.CFG)
  ·  **Idioma:** código ISO

```
?%ETK[0]=0
?%ETK[17]=0 
G4F1.200 
M5 
D0 
G0 G53 Z201.000 
G0 G53 X-2500.000 
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

### `Inventario completo de índices ETK observados (recuento de asignaciones en los 5 .iso de PostProcessor)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\*.iso (lado_derecho1.iso, lado_izquierdo1.iso, pieza 300x300 calxy.iso, prubafresas.iso, rebaje laterales.iso)`
  ·  **Sección:** Conteo textual de las líneas '?%ETK[n]=v' distintas
  ·  **Idioma:** código ISO

```
48 ?%ETK[7]=0
30 ?%ETK[7]=3
22 ?%ETK[8]=1
15 ?%ETK[18]=0
15 ?%ETK[13]=0
12 ?%ETK[17]=257
11 ?%ETK[7]=4
10 ?%ETK[18]=1
10 ?%ETK[13]=1
 8 ?%ETK[0]=0
 7 ?%ETK[17]=0
 6 ?%ETK[6]=5
 6 ?%ETK[6]=1
 6 ?%ETK[1]=0
 5 ?%ETK[500]=100
 5 ?%ETK[2]=0
 5 ?%ETK[19]=0
 5 ?%ETK[0]=16
 4 ?%ETK[9]=1
 4 ?%ETK[6]=2
 4 ?%ETK[0]=2
 3 ?%ETK[8]=2
 3 ?%ETK[6]=60
 3 ?%ETK[6]=6
 3 ?%ETK[0]=32
 3 ?%ETK[0]=2147483648
 2 ?%ETK[9]=5
 2 ?%ETK[9]=3
 2 ?%ETK[8]=5
 2 ?%ETK[6]=58
 2 ?%ETK[0]=48
 2 ?%ETK[0]=1073741824
 1 ?%ETK[9]=6
 1 ?%ETK[9]=4
 1 ?%ETK[7]=1
 1 ?%ETK[6]=82
 1 ?%ETK[1]=16
 1 ?%ETK[0]=1
```

### `EDK[n].m — PARECIDO, NO IDÉNTICO a ETK`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\PostISO.dll (offsets 221456, 222740, 222756, 222825), VtGenIso.dll (241040, 241059) y Maestro\PostProcessor\*.iso`
  ·  **Sección:** Aparece intercalado con los ETK, con sintaxis distinta: lleva sufijo '.0' (bit) en vez de valor entero simple
  ·  **Idioma:** código ISO

```
?%%EDK[%d].0=0
?%%EDK[1].0=%d
?%%EDK[0].0=%d
?%%EDK[%d].0=1
(en el ISO real:) ?%EDK[0].0=0 / ?%EDK[1].0=0 / ?%EDK[13].0=1 / ?%EDK[13].0=0
```

### `'ETK' como ocurrencia binaria dentro de los .chm y .pdf (NO es texto legible)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Country\{Ita,Ing,Fra,Spa,...}\Xilog_Plus_Editor.chm y C:\Program Files (x86)\Scm Group\Maestro\Languages\{es-ES,fr-FR}\Maestro Editor.pdf`
  ·  **Sección:** Volcado del contexto de ±60 bytes alrededor de cada coincidencia: son bytes de flujo comprimido, no prosa. Se incluye para que no se confunda el recuento de grep con un hallazgo real.
  ·  **Idioma:** n/a (binario)

```
Ita @4429567 : ....g.~).T0..<..vl'..`.Y..).b$..._-.v...e@....sGF.......&v..ETKM.Mm:.'+RF...>..5.E:r.`bKS..?\..A...zm..t...u.*O.=.%.C...
Ing @5980535 : ..Q..o.... #.@...G...:..n..M..K.7{...u.U.......yr...C...t^.xETK`....b.xZ.Pu}4.g.W..........1...=A.:....5..H^!.S.A.{.a...
Maestro Editor.pdf (es-ES) @2326066 : ..........G.y..<-.......f...^...o....E>...x.@. .B..A..8....METK...d...l2..*H.p.......m.........4Uo2..x[......(./?......o
```

### `'EtkHt3' — PARECIDO, NO IDÉNTICO (cadena suelta, no es un registro)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\PostISO.dll (offset 13965)`
  ·  **Sección:** Cadena aislada en zona de datos del PE, sin sintaxis de registro (sin '%%', sin corchetes)
  ·  **Idioma:** n/a (binario)

```
EtkHt3
```

**No aparece en ninguna fuente:** `QUÉ ES UN REGISTRO ETK — no aparece. Ninguna de las 8 fuentes define el término, ni dice qué significa la sigla, ni explica para qué sirve la familia.`, `TABLA DE ÍNDICES ETK CON SU SIGNIFICADO — no aparece. No hay en ninguna fuente una lista que asocie ETK[n] con una función. Lo más cercano son comentarios sueltos pegados a cadenas individuales dentro de DLLs: ';LKey' (ETK[7]), ';Angolo=%.3f' (ETK[6]), ';Motore=%d,Strobe=%u' (ETK[8]) en VtGenIso.dll; ';utensile' (ETK[904]) y ';traverse' (ETK[903]) en PlPathFilter32.dll; y ';Ripristino limitazione corsa positiva X di anticollisione' (ETK[500]) en Park.pgm.`, `FUENTE 1 — out_spa/ (ayuda Xilog Plus Editor en español, 1436 archivos HTML verificados): 'ETK' no aparece. Tampoco 'EDK', ni '%ax[', ni '_paras('.`, `FUENTE 2 — out_editor_ing/ (la misma ayuda en inglés, 1434 archivos): 'ETK' no aparece. Tampoco 'EDK', '%ax[' ni '_paras('.`, `FUENTE 3 — out_epl/ (ayuda del módulo EPL, 210 archivos): 'ETK' no aparece. Tampoco 'EDK', '%ax[' ni '_paras('.`, `FUENTE 4 — out_panelmac/ (ayuda de PanelMac, 271 archivos): 'ETK' no aparece. Tampoco 'EDK', '%ax[' ni '_paras('.`, `FUENTE 5 — maestro_editor_es.txt (manual del Maestro Editor en español, 170 páginas): 'ETK' no aparece. 'EDK' tampoco.`, `FUENTE 6 — pgmx/docs/xilog_plus_pgm/ (transcripciones que ya teníamos): 'ETK' no aparece (búsqueda insensible a mayúsculas).`, `FUENTE 7 — pgmx/docs/maestro_scripting/ (API de scripting): 'ETK' no aparece (búsqueda insensible a mayúsculas).`, `LOS 142 ARCHIVOS .txt SUELTOS DE LA INSTALACIÓN (Xilog Plus\Bin\*.txt, Xilog Plus\Country\<idioma>\*.txt — ASSEMBLAGGIO, cerniere, ERGON, FERRAMENTA, MACRO_STD, MBD, SCM, XIMULA, Xilog_Plus_Editor, Xilog_Plus_Epl, Xilog_Plus_PanelMac —, Xilog Plus\Fxc\*.txt): 'ETK' no aparece en ninguno.`, `'ETK' SIN CORCHETES, COMO PALABRA SUELTA EN PROSA — no aparece en ninguna fuente. Siempre aparece como '%ETK[n]' o '%%ETK[n]'.`, `'etk' EN MINÚSCULAS COMO TÉRMINO PROPIO — no aparece. Las únicas coincidencias insensibles a mayúsculas son ruido binario ('EtkHt3', 'GETKEYBOARD*', cadenas ofuscadas de .dll/.pgm/.pdf/.chm) y se listaron arriba como 'parecido, no idéntico'.`

## G del esqueleto (G0, G40, G53, G61, G64, G71)

### `G0`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm`
  ·  **Sección:** 5.2.1.3 Fresados — Inicio fresado - G0
  ·  **Idioma:** es

```
5.2.1.3 Fresados

Inicio fresado - G0

Define el punto inicial de un perfil.

Parámetros:
X   Coordenada X de inicio del perfil.
Y   Coordenada Y de inicio del perfil.
Z   Profundidad de inicio del perfil.
E   Posición de la campana de aspiración (véase el Apéndice D ).
V   Velocidad de entrada en la pieza.
S   Velocidad de rotación de la herramienta.
D   Cota de fuera trabajo.
N   Nombre del perfil (v. GREP ).
T   Herramienta.

Ejemplo:
► Origen máquina delantero
► Origen máquina trasero
```

### `G0`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/5.2_Basic_Instructions_(Text).htm`
  ·  **Sección:** 5.2.1.3 Routing — Milling Start - G0
  ·  **Idioma:** en

```
5.2.1.3 Routing

Milling Start - G0

Defines the beginning point of a profile.

Parameters:
X   Coordinate X for beginning of profile.
Y   Coordinate Y for beginning of profile.
Z   Depth of beginning of profile.
E   Position of vacuum hood (see: Appendix D ).
V   Piece entry speed.
S   Rotation speed of tool
D   Outside work quota.
N   Profile name (see GREP ).
T   Tool.

Example:
► Front machine origin
► Rear machine origin
```

### `tabla de códigos G`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm`
  ·  **Sección:** 5.2.1.3 Fresados (lista completa de encabezados de la sección)
  ·  **Idioma:** es

```
Inicio fresado - G0
Inicio fresado 3D - G03D (grupo Prisma)
Fresado lineal - G1
Fresado lineal 3D - G13D (grupo Prisma)
Fresado circular horario - G2
Fresado circular antihorario - G3
Tramo tangente al tramo precedente - G5
Entrada automática en el perfil - GIN
Salida automática del perfil - GOUT
Repetición de un perfil - GREP
Inicio fresado con herramienta inclinada - G0R
Fresado lineal con herramienta inclinada - G1R
Fresado circular horario con herramienta inclinada - G2R
Fresado circular antihoraria con herramienta inclinada - G3R
Tramo tangente al tramo precedente con herramienta inclinada - G5R

[PARECIDO, NO IDÉNTICO: esta es la lista de encabezados de instrucciones de fresado de la ayuda del Xilog Plus Editor. NO hay en ninguna de las 8 fuentes una tabla de códigos G del ISO. Los únicos códigos G que aparecen en la ayuda completa (ES e ING) son G0, G1, G2, G3, G5, G79, más las variantes 3D y R.]
```

### `G0`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm`
  ·  **Sección:** Instrucción ISO - ISO
  ·  **Idioma:** es

```
Instrucción ISO - ISO

Permite programar una instrucción en el lenguaje ISO del control numérico usado; la instrucción debe colocarse entre dobles ápices y puede ser ejecutada desde una lista de parámetros separados por lo menos por un espacio (la estructura y el significado de los parámetros están descritos en el párrafo correspondiente a la instrucción PRINT). En la instrucción no se efectúa ningún control sintáctico y a ésta no le corresponde ninguna visualización gráfica.

Grupo: instrucciones texto

Parámetros:
"<línea>"   Instrucción ISO.
(campos vacíos)   Parámetros opcionales.

Nota. Cuando existen MICRO POSICIONAMIENTOS dentro de un programa, es necesario introducir al inicio del mismo la instrucción:
ISO "%B20".

Ejemplos:
ISO "G0X1000Y740F6000"
ISO "M71"
ISO "M?d" 110+Campana
```

### `G0`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/5.2_Basic_Instructions_(Text).htm`
  ·  **Sección:** ISO Instructions - ISO
  ·  **Idioma:** en

```
ISO Instructions - ISO

Used to program an instruction in the ISO language of the numerical control used. The instructions are placed between double quotation marks and may be followed by a list of parameters separated by at least one space (the structure and meaning of the parameters are described in the paragraph on the instruction PRINT). No syntax check is performed on the instruction and no graphic view is associated to it.

Group: Main functions

Parameters:
"<string>"   ISO instructions.
(empty boxes)   Optional parameters.

Note: if in a program there are MICRO POSITIONINGS, it is necessary to insert the following instruction at the tip of the program:
ISO "%B20"

Examples:
ISO "GX1000Y740F6000"
ISO "M71"
ISO "M?d" 110+ Hood

[OJO: la versión inglesa escribe GX1000Y740F6000 (sin el 0 de G0); la española del mismo ejemplo escribe G0X1000Y740F6000. Marcado no-exacto por esa diferencia textual entre idiomas.]
```

### `G0`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/4.1_Equipamiento.htm`
  ·  **Sección:** 4.1 Equipamiento — tabla de parámetros de herramienta (fresa)
  ·  **Idioma:** es

```
Velocidad G0/B
Velocidad de bajada en el tramo que va de la cota de seguridad a la de trabajo. Este parámetro también se puede programar durante la fase de programación de la pieza mediante la instrucción G0 o XG0.

[y en la tabla del grupo perforador del mismo capítulo:]

Velocidad G0/B
Velocidad de ejecución del orificio.

[PARECIDO, NO IDÉNTICO: "Velocidad G0/B" es el nombre de un parámetro de la herramienta, no el código G0.]
```

### `G0`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/4.1_Tooling.htm`
  ·  **Sección:** 4.1 Tooling — tool parameters table
  ·  **Idioma:** en

```
Speed G0/B
Descent speed in the section which goes from the safety dimension to the machining dimension. You can set this parameter when programming the work piece with G0 or XG0.

[PARECIDO, NO IDÉNTICO: nombre de parámetro, no el código G0.]
```

### `G0`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.4_Macros_usuario.htm`
  ·  **Sección:** 5.4 Macros usuario — claves de Nci.cfg, ejemplos (cabeza prisma en H03)
  ·  **Idioma:** es

```
Ejemplos (cabeza prisma en H03):

- CN NUM :
$H03_SETHOOD_SUPP
G0 C180 ; introducir si la tapa suplementaria admitida solamente para C a 180°
E30051=%ld M111
$

Si en la cabeza puede ser montada exclusivamente la tapa suplementaria, añadir también:
$H03_SETHOOD
%
$

- CN OSAI :
$H03_SETHOOD_SUPP
G0 C180 ; introducir si la tapa suplementaria admitida solamente para C a 180°
#@GW88=2
#@GW95=%ld
G0
#M114
$
$H03_ANGLOCKHOOD_SUPP
#@GD51=%ld
$
$GEN_INIT
…
G79 G0 B0 C180
…
$

- COMUNE :
$H03_ANGBHOOD_SUPP
0
$
$H03_ANGCHOOD_SUPP
180
$
```

### `G0`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_epl/Par_metros_de_configuraci_n.htm`
  ·  **Sección:** EPL — Parámetros de configuración (definición de ventosas)
  ·  **Idioma:** es

```
[G0] X=-25,Y=75
[G1] X=100,Y=-75
[G2] X=75,Y=-100,I=75,J=-75,R=25
[G1] X=-75,Y=-100
[G2] X=-100,Y=-75,I=-75,J=-75,R=25
[G1] X=-75,Y=75
[G2] X=-50,Y=100,I=-50,J=75,R=25

Para poder utilizar estas instrucciones hay que respetar algunas condiciones:
· debe existir una sola G0;
· el perfil del apoyo debe estar definido por tres puntos como mínimo;
· todas las instrucciones utilizadas (G0, G1, G2, G3) deben introducirse de tal manera que se defina un perímetro cerrado constituido por puntos sucesivos y continuos uno respecto al otro.

La ventosa del ejemplo también puede dibujarse utilizando la instrucción G3. En tal caso, los puntos deben introducirse siguiendo el sentido contrario a las agujas del reloj a partir del origen (G0).
```

### `G0`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/Cnc.msg`
  ·  **Sección:** Mensajes de error del CN (MODULE 2) — @7, @139, @265
  ·  **Idioma:** es

```
@7,"DESPLAZAMIENTOS PARALELOS A LOS EJES INCLINADOS:/ LA PROGRAMACION NO ESTA EN EL PLANO G20/ LA INTERPOLACION NO ESTA EN G0 O G1/ X"

@139,"PROGRAMACION EN UN MISMO BLOQUE DE DOS EJES PARALELOS PORTADOS ......FUERA DE G52 Y FUERA DE G0"

@265,"FALTA UN PRIMER BLOQUE DE POSICIONADO, LA DEFINICION DE CONTORNODEBE COMENZAR POR G0 O G1"
```

### `G0`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/Nci.ini`
  ·  **Sección:** Nci.ini — sección [G0WITHSPINDLES]
  ·  **Idioma:** —

```
[G0WITHSPINDLES]
enable=0

[PARECIDO, NO IDÉNTICO: es el nombre de una sección de configuración de Nci.ini, no el código G0. No hay documentación de esta clave en ninguna de las fuentes revisadas.]
```

### `G0 / G53`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/NCI.CFG`
  ·  **Sección:** NCI.CFG — clave $GEN_INIT (archivo completo, 67 líneas)
  ·  **Idioma:** —

```
$GEN_ISO_FOR_EXTERNAL_APP
1
$
$GEN_INIT
?%%ETK[500]=100
;?%%ETK[500]=%%ax[0].pa[22]/1000 ;solo per zone
_paras( 0x00, X, 3, %%ax[0].pa[21]/1000, %%ETK[500] )
;
G0 G53 Z %%ax[2].pa[22]/1000
M58 ;abilita controllo vuoto
$
$GEN_END
?%%ETK[0]=0
?%%ETK[1]=0
?%%ETK[2]=0
?%%ETK[13]=0
?%%ETK[17]=0
?%%ETK[18]=0
?%%ETK[19]=0
$
$H03_VECTOR
C
$
$H04_VECTOR
B
$
$H03_BLOWERON
M220
$
$H03_BLOWEROFF
M221
$
$H04_BLOWERON
M222
$
$H04_BLOWEROFF
M223
$
$GEN_PGMLOG
1
$
$GEN_MAXTOOLRAD
100
$
$GEN_MAXTOOLLEN
160.1
$
$GEN_RAPID01RAD
250
$
$GEN_RAPID02RAD
250
$
$GEN_SPINTIME
0.5
$
$GEN_TSPOPEN
$
$GEN_TSPCLOSE
$
$GEN_UTMAXLEN
155
$
$GEN_RAPIDQAP
0
$
```

### `G53`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Fxc/Mbd/Park.pgm`
  ·  **Sección:** Park.pgm (macro Mbd) — cadenas ISO embebidas; comentario de cabecera: "Inserimento limitazione/ripristino corsa X di anticollisione  M.De Crescenzo 2/10/2012"
  ·  **Idioma:** it/—

```
IF AREA=1 OR AREA=2 OR AREA=12 OR AREA=21 OR AREA=14 THEN
   ISO "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ax[0].pa[22]/1000 )" ;Ripristino corsa totale asse X
   ISO "G0G53 X%ax0.pa31/1000 Y%ax1.pa22/1000"
FI
IF AREA=3 OR AREA=4 OR AREA=34 OR AREA=43 OR AREA=41 THEN
   ISO "G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000"
FI
…
ISO "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )" ;Ripristino limitazione corsa positiva X di anticollisione

[Las cuatro cadenas ISO distintas que contiene el archivo son, literalmente:
ISO "G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000"
ISO "G0G53 X%ax0.pa31/1000 Y%ax1.pa22/1000"
ISO "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )"
ISO "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ax[0].pa[22]/1000 )"]
```

### `G40`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/Cnc.msg`
  ·  **Sección:** Mensajes de error del CN (MODULE 2) — @138
  ·  **Idioma:** es

```
@138,"CAMBIO DE PLANO DE INTERPO. FUERA DE G40 "
```

### `G40`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Ing/Cnc.msg y .../Ita/Cnc.msg`
  ·  **Sección:** Mensajes de error del CN (MODULE 2) — @138
  ·  **Idioma:** en / it

```
[Ing] @138,"CHANGE OF INTERPOLATION PLANEMUST BE IN G40 "
[Ita] @138,"CAMBIO PIANO D'INTERPOLAZ. NON IN G40 "
```

### `G64`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Ing/Cnc.msg y .../Ita/Cnc.msg`
  ·  **Sección:** Mensajes de error del CN (MODULE 2) — @96
  ·  **Idioma:** en / it

```
[Ing] @96,"PRECEEDING BLOCK "LOOK AHEAD", CONFLICTS WITH EXTERNAL PARAMETER ACCESS/ L100 PROGRAMMED ... IN DEFINITION OF A PROFILE OF A G64"
[Ita] @96,"BLOCCO PREC. LA DICHIARAZ. DI UN PARAM. ESTERNO INCOMPLETO/ PROGRAMMAZIONE DI L100 .. NELLA DEFINIZIONE DEL PROFILO IN UNA G64"

[El mismo mensaje en español NO menciona G64 — queda cortado: @96,"BLOQUE PRECEDENTE A LA DECLARACION DE 1 PARAM EXTERNO,INCOMPLETO./ PROGRAMACION DE L100 ... DENTRO DE LA DEFINICION DE PERFIL DE"]
```

### `G52 (parecido a G53, no idéntico)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/Cnc.msg`
  ·  **Sección:** Mensajes de error del CN (MODULE 2) — @27 y @139
  ·  **Idioma:** es

```
@27,"VALIDACION O INVALIDACION DE UNA CORRECION DE RADIO:- EN PROGRAMACION ORIGEN MAQUINA [G52]- EN ROSCADO CONICO [G38]"
@139,"PROGRAMACION EN UN MISMO BLOQUE DE DOS EJES PARALELOS PORTADOS ......FUERA DE G52 Y FUERA DE G0"

[Ing] @27,"TOOL RADIUS CORRECTION:/ IN M/C REFERENCE MODE G52 / IN TAPERED THREADING"

[PARECIDO, NO IDÉNTICO: el manual asocia "PROGRAMACION ORIGEN MAQUINA" / "M/C REFERENCE MODE" al código G52, no a G53. G53 no aparece en Cnc.msg.]
```

### `todos los códigos G que aparecen en Cnc.msg`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/Cnc.msg y .../Ing/Cnc.msg`
  ·  **Sección:** Mensajes de error del CN (MODULE 2) — inventario completo
  ·  **Idioma:** es / en

```
Inventario textual de códigos G presentes en el archivo de mensajes:
[Spa] G0, G1, G2, G3, G20, G21, G22, G29, G38, G40, G43, G52, G59, G76, G78, G96, G97
[Ing] G0, G1, G2, G3, G20, G21, G22, G29, G40, G43, G52, G64, G73, G74, G76, G78, G96, G97

Mensajes genéricos sobre "función G":
[Spa] @2,"FUNCION G NO RECONOCIDA POR EL SISTEMA/ O AUSENCLA ARGUMENTO OBLIGATORIO DESPUES DE G"
[Spa] @3,"ARGUMENTO DE UNA FUNCION MAL POSICIANADO EN EL BLOQUE"
[Spa] @20,"FALTA M02 EN FIN DE PROGRAMA./ BLOQUES NO EJECUTABLES DENTRO DE UN CICLO LLAMADO POR F. G"
[Ing] @2,"UNKNOWN G FUNCTION/ OR A MANDATORY ARGUMENT MISSING AFTER THE G"
[Ing] @3,"ATTRIBUTE OF A G CODE WRONGLY POSITIONNED"
[Ing] @20,"M02 MISSING/ OR BLOCKS LEFT NON-EXECUTABLE BY A PERSONALIZED G CODE"

[NO hay en Cnc.msg ninguna definición de qué hace cada código; son sólo textos de alarma. NO aparecen G53, G61 ni G71.]
```

### `G0, G40, G53, G61, G64, G71`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/pieza 300x300 calxy.iso (y lado_derecho1.iso, lado_izquierdo1.iso, prubafresas.iso, rebaje laterales.iso)`
  ·  **Sección:** Archivos .iso de ejemplo que vienen en la carpeta PostProcessor de la instalación — NO son documentación
  ·  **Idioma:** —

```
Cabecera de lado_derecho1.iso (líneas 1-23, textual):
% lado_derecho1.pgm
;H DX=354.550 DY=266.550 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
%Or[0].ofX=-354549.988 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=43000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-354.550 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 
?%ETK[8]=1 
G40 

Bloque G61/G64 en lado_derecho1.iso (líneas 80-89):
G0 G53 Z201.000 
MLV=2
G61 
MLV=0 
?%ETK[13]=0   
?%ETK[18]=0 
G0 G53 Z201.000 
G64 
MLV=1 
SHF[Z]=25.000+%ETK[114]/1000

Cierre en lado_derecho1.iso (líneas 317-330):
SHF[Z]=43.000+%ETK[114]/1000
?%ETK[7]=0
G61 
MLV=0 
?%ETK[0]=0
…
G0 G53 Z201.000 
G0 G53 X-2500.000 
G64 
SYN
?%ETK[0]=0

Final de archivo (últimas 12 líneas):
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

Recuento por archivo (ocurrencias literales):
lado_derecho1.iso     — G40 x8, G53 x10, G61 x2, G64 x2, G71 x1
lado_izquierdo1.iso   — G40 x12, G53 x12, G61 x2, G64 x2, G71 x1
pieza 300x300 calxy.iso — G40 x4, G53 x6, G61 x1, G64 x1, G71 x1
prubafresas.iso       — G40 x3, G53 x11, G61 x1, G64 x1, G71 x1
rebaje laterales.iso  — G40 x5, G53 x3, G61 x1, G64 x1, G71 x1
```

### `G0 (transcripciones ya en el repo)`

**Fuente:** `c:/Dev/Repositorios/ProdAction/pgmx/docs/xilog_plus_pgm/05_2_instrucciones_basicas.md`
  ·  **Sección:** 5.2.1.3 Fresados — "fresado - G0" (línea 584); "ISO «G0X1000Y740F6000»" (línea 306)
  ·  **Idioma:** es

```
La transcripción del repo reproduce el mismo texto que el CHM español. Códigos G presentes en TODO pgmx/docs/ (xilog_plus_pgm + maestro_scripting): G0 x83, G1 x66, G2 x30, G3 x22, G5 x4, G79 x1. NO aparecen G40, G53, G61, G64 ni G71 en ningún archivo del repo bajo pgmx/docs/.
```

### `G79`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.4_Macros_usuario.htm`
  ·  **Sección:** 5.4 Macros usuario — ejemplo de clave $GEN_INIT para CN OSAI
  ·  **Idioma:** es

```
$GEN_INIT
…
G79 G0 B0 C180
…
$

[PARECIDO, NO IDÉNTICO: G79 no está en la familia buscada, pero es el ÚNICO código G de dos cifras que aparece en toda la ayuda (ES e ING), y aparece junto a G0 dentro de $GEN_INIT. No hay explicación de qué hace G79 en ninguna fuente.]
```

**No aparece en ninguna fuente:** `G40 — NO APARECE en ninguna de las fuentes documentales (fuentes 1 a 7: ayuda Xilog Plus Editor ES, ayuda Editor ING, ayuda EPL, ayuda PanelMac, manual Maestro Editor español, pgmx/docs/xilog_plus_pgm, pgmx/docs/maestro_scripting). Sólo aparece en la fuente 8 (instalación): en los archivos de mensajes de alarma Cnc.msg (@138) y en los .iso de ejemplo de Maestro/PostProcessor. En ningún lado hay una definición de qué hace G40.`, `G53 — NO APARECE en ninguna de las fuentes documentales (1 a 7). Sólo en la fuente 8: NCI.CFG (clave $GEN_INIT), Xilog Plus/Fxc/Mbd/Park.pgm (cadenas ISO) y los .iso de ejemplo. No hay definición escrita de G53 en ninguna fuente. Lo más parecido que sí está documentado es G52, descrito en Cnc.msg como "PROGRAMACION ORIGEN MAQUINA" / "M/C REFERENCE MODE" — parecido, no idéntico.`, `G61 — NO APARECE en ninguna de las fuentes documentales (1 a 7), ni en Cnc.msg, ni en NCI.CFG, ni en ningún .cfg/.ini/.str/.txt de la instalación. Aparece exclusivamente dentro de los cinco archivos .iso de ejemplo de C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/. Cero explicaciones.`, `G64 — NO APARECE en ninguna de las fuentes documentales (1 a 7). En la fuente 8 aparece sólo en Cnc.msg de los idiomas inglés e italiano (mensaje @96: "...IN DEFINITION OF A PROFILE OF A G64" / "...NELLA DEFINIZIONE DEL PROFILO IN UNA G64") — el Cnc.msg español recorta la frase y NO lo menciona — y en los cinco .iso de ejemplo. No hay definición de qué hace G64.`, `G71 — NO APARECE en ninguna de las fuentes documentales (1 a 7), ni en Cnc.msg de ningún idioma, ni en NCI.CFG ni en ningún archivo de configuración. Aparece exclusivamente dentro de los cinco archivos .iso de ejemplo de Maestro/PostProcessor/, una sola vez por archivo, en la cabecera. Cero explicaciones.`, `Tabla de códigos G — NO EXISTE en ninguna de las 8 fuentes. Se buscó "función preparatoria", "preparatory function", "código G", "G-code", "tabla de códigos": los únicos aciertos son mensajes de alarma genéricos de Cnc.msg ("FUNCION G NO RECONOCIDA POR EL SISTEMA", "ATTRIBUTE OF A G CODE WRONGLY POSITIONNED", "BLOCKS LEFT NON-EXECUTABLE BY A PERSONALIZED G CODE"). La ayuda del Editor sólo lista las instrucciones de fresado del lenguaje PGM (G0/G1/G2/G3/G5 y variantes 3D y R).`, `El manual del Maestro Editor en español (C:/Users/.../scratchpad/maestro_editor_es.txt, 170 páginas) NO CONTIENE NINGÚN código G — ni G0, ni ninguno. Lo mismo sus versiones en/it/de extraídas en scratchpad/pdfs/. Igual la ayuda de Maestro Scripting (out_scripting_es, 212 páginas HTML), la ayuda de PanelMac (out_panelmac) y la ayuda de WinXiso (out_winxiso_*): cero ocurrencias de cualquier código G.`

## M y SYN

### `M58`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (línea 7245)`
  ·  **Sección:** APÉNDICE I. Programación de los sujetadores Duomatic
  ·  **Idioma:** español

```
La selección del bloqueo por medio de los sujetadores DUOMATIC, debe realizarse al comienzo del programa, antes de solicitar el bloqueo de la pieza (M28/M39/M58) .
```

### `M58`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (línea 7344)`
  ·  **Sección:** APÉNDICE I. Programación de los sujetadores Duomatic
  ·  **Idioma:** español

```
Al comienzo del programa, antes de la solicitud del bloqueo pieza (M28/M38/M58), es necesario seleccionar los sujetadores DUOMATIC con los que se desea empezar a trabajar [delanteros (lado operador en la dirección Y) o traseros (lado contrario al operador en la dirección Y ) o ambos].
```

### `M58`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (líneas 7477-7502)`
  ·  **Sección:** APÉNDICE I. Programación de los sujetadores Duomatic — Ejemplos
  ·  **Idioma:** español

```
(H DX=… DY=… DZ=… -CD C=0 T=0 R=99 … V=51)
E30002=11
E30060=1
…
M58

Ejemplo:

(H DX=… DY=… DZ=… -AB C=0 T=0 R=99 … V=53)
E30001=11
E30059=3
…
M58
```

### `M58`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (líneas 7257 y 7519)`
  ·  **Sección:** APÉNDICE I. Programación de los sujetadores Duomatic — remisión (aparece dos veces, tras E30002 y tras M193)
  ·  **Idioma:** español

```
(Véase el manual Diagnóstico y Códigos M, que se suministra con la máquina)
```

### `M58`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/_APPENDIX.htm (líneas 6841-6845, 6858)`
  ·  **Sección:** APPENDIX I. Programming Duomatic Clamps
  ·  **Idioma:** inglés

```
Selection of hold-down using the DUOMATIC clamps must be made at the start of the program before the work piece hold-down request (M28/M39/M58).

It is selected using the usual E30xxx parameters:

E30001 (Selects the type of work piece hold-down to be used for zone 1).

E30002 (Selects the type of work piece hold-down to be used for zone 2).

(Also see: Diagnostics manual and M Codes provided with the machine)
```

### `M58`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/_APPENDIX.htm (líneas 6943-6946)`
  ·  **Sección:** APPENDIX I. Programming Duomatic Clamps
  ·  **Idioma:** inglés

```
At the start of the program, before the work piece hold-down request (M28/M38/M58), you must also select which DUOMATIC clamps are to be used to start work [front (operator side in Y direction), rear (side opposite operator in Y direction ) or both].
```

### `M58`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_panelmac/Celda_Nesting_con_la_simple_opci_n_Reverse_Flow_..htm (líneas 30-43)`
  ·  **Sección:** Celda Nesting con la simple opción «Reverse Flow».
  ·  **Idioma:** español

```
Posición 1 = modo Nesting: sólo con zona única de trabajo, posibilidad de bloquear directamente la pieza accionando el selector de bloqueo (antes hay que habilitar el bloqueo con M58) o bien, habilitar el soplido accionando el botón azul colocado en la mesa.

Al presionar el botón se enciende la lámpara azul del botón mismo y la lámpara en el púlpito inicia a parpadear, ello indica que se ha preparado para el soplido. Pulsando luego el botón de bloqueo se habilita el soplido, la lámpara en el púlpito deja de parpadear mientras la azul queda encendida; accionando luego el selector de desbloqueo, se libera el soplido por lo tanto se apaga la lámpara azul. A partir de esta operación se puede bloquear la pieza con vacío (antes hay que habiltar el bloqueo con M58) o bien, volver a habilitar el soplido accionando el botón azul. Al sucesivo desbloqueo se vuelve al punto inicial.
```

### `M58`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/NCI.CFG (líneas 4-11) — archivo de configuración de la instalación, NO es documentación`
  ·  **Sección:** $GEN_INIT
  ·  **Idioma:** italiano (comentario)

```
$GEN_INIT
?%%ETK[500]=100
;?%%ETK[500]=%%ax[0].pa[22]/1000 ;solo per zone
_paras( 0x00, X, 3, %%ax[0].pa[21]/1000, %%ETK[500] )
;
G0 G53 Z %%ax[2].pa[22]/1000
M58 ;abilita controllo vuoto
$
```

### `M58`

**Fuente:** `c:/Dev/Repositorios/ProdAction/pgmx/docs/xilog_plus_pgm/09_13_reglas_estacionamiento.md (líneas 2591, 2624, 2669, 2675, 2693, 2733)`
  ·  **Sección:** APÉNDICE I. Programación de los sujetadores Duomatic (transcripción ya existente en el repo del mismo texto del CHM español)
  ·  **Idioma:** español

```
solicitar el bloqueo de la pieza (M28/M39/M58) .
[…]
solicitud del bloqueo pieza (M28/M38/M58), es necesario seleccionar los sujetadores DUOMATIC con los que se desea empezar a trabajar
```

### `M58`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/ — los 5 archivos .iso (lado_derecho1.iso, lado_izquierdo1.iso, «pieza 300x300 calxy.iso», prubafresas.iso, «rebaje laterales.iso»), todos en la línea 8. Son SALIDAS del postprocesador, no documentación`
  ·  **Sección:** cabecera del programa ISO
  ·  **Idioma:** —

```
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71
```

### `M2`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (línea 7177)`
  ·  **Sección:** APÉNDICE (Prisma) → «Ejecución directa del programa ISO», paso 4
  ·  **Idioma:** español

```
Eliminar el caracter "%" de la última línea  e introducir la línea "M2" en su lugar.
```

### `M2`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/_APPENDIX.htm (líneas 6773-6776)`
  ·  **Sección:** Running the ISO program directly, paso 4
  ·  **Idioma:** inglés

```
Delete the "%" character in the last line and insert the "M2" string in its place.
```

### `M2`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_panelmac/Celda_Nesting_con_retorno_autom_tico_del_tablero_protector_o_con_oscilaci_n_del_mismo..htm (líneas 150-154)`
  ·  **Sección:** Celda Nesting con retorno automático del tablero protector o con oscilación del mismo.
  ·  **Idioma:** español

```
Se prodrá realizar una nueva carga sólo si habrá una disminución de pieza, es decir al final del programa. En el caso de que, aún después de una 'interrupción de programa, se desee igualmente volver a partir con el ciclo Nesting, habrá que escribir en MDI el código M2 (código de fin de programa) o bien, forzar el parámetro E30019=0.
```

### `M2`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (líneas 10538-10544)`
  ·  **Sección:** APÉNDICE N. Notas → Gestión directa de los programas ISO → M20
  ·  **Idioma:** español

```
M20

La presencia del código M20 , en lugar del M2 ( en los trabajos pendulares ), permite no cerrar la ejecución en el modo pasante y por lo tanto ganar tiempo al pasar de una área de trabajo (por ej. área A) a otra (por ej. área B). Si se está reutilizando un viejo programa CNC, editarlo e introducir manualmente el código M20 requerido.
```

### `M2`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/_APPENDIX.htm (líneas 10077-10083)`
  ·  **Sección:** APPENDIX N. Notes → Direct Management of ISO Programs → M20
  ·  **Idioma:** inglés

```
M20

The presence of code M20 instead of M2 (in pendulum machining) means that machining does not have to end in pass mode, therefore, gaining time during the passage from one machining area (e.g.: area A) to another (e.g.: Area B ). If using an old CNC program, edit it and manually enter the desired M20 code.
```

### `M2 (escrito M02)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (líneas 10525-10534)`
  ·  **Sección:** APÉNDICE N. Notas → Gestión directa de los programas ISO → M02
  ·  **Idioma:** español

```
M02

En los programas CNC todos los bloques M02 deben estar precedidos por un bloque M201; en caso de que no exista dicho bloque, el programa sigue comportándose correctamente pero al concluir, el color del área permanece  verde y el contador de las piezas producidas no decrementa; ante esta situación es necesario pulsar F10 (Reset) para informar al Panel de la máquina de Xilog Plus de que el programa ha finalizado. Si se está reutilizando un viejo programa CNC, editarlo e introducir manualmente el código M201 requerido.
```

### `M2 (escrito M02)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/_APPENDIX.htm (líneas 10064-10073)`
  ·  **Sección:** APPENDIX N. Notes → Direct Management of ISO Programs → M02
  ·  **Idioma:** inglés

```
M02

All M02 blocks in CNC programs must be preceded by an M201 block; if the M201 block is missing the program continues to run correcting, but when it terminates the color of the work area will remain green and the counter for the pieces produced will not be reset; under these condition press key [F10] (Reset) to inform the Xilog Plus Machine Panel that the program has terminated. If you are working with an old CNC program, edit it and manually write the required M201 code.
```

### `M2 (escrito M02)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/Cnc.msg (línea 21) — archivo de mensajes del control numérico`
  ·  **Sección:** mensaje @20
  ·  **Idioma:** español

```
@20,"FALTA M02 EN FIN DE PROGRAMA./ BLOQUES NO EJECUTABLES DENTRO DE UN CICLO LLAMADO POR F. G"
```

### `M2`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/Cnc.msg (línea 99) — archivo de mensajes del control numérico`
  ·  **Sección:** mensaje @131
  ·  **Idioma:** español

```
@131,"PROGRAMACION DE 1 CURVA O CHAFLAN EN UN BLOQUE CON M0,M1 O M2./ PROGR. INSUFICIENTE EN UNE CADENA DE BLOQUES,NO PERMITIENDO DE "
```

### `M2`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/prubafresas.iso (línea 237) — SALIDA del postprocesador, no documentación`
  ·  **Sección:** última línea del programa ISO
  ·  **Idioma:** —

```
?%EDK[13].0=0 
M2
```

### `M3`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (líneas 6802-6820)`
  ·  **Sección:** APÉNDICE (Grupo Hueco Cerradura con Eje Tilting) → sección a añadir en nci.cfg
  ·  **Idioma:** español/mixto

```
$H04_UP

M81

$

$H04_DOWN

M71

$

$H04_ROTCW

M65M3S%ld

M21

$

$H04_ROTCCW

M65M3S%ld

M21

$

$H04_NOROT

M50

$
```

### `M3`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/prubafresas.iso (líneas 27-34) — SALIDA del postprocesador, no documentación`
  ·  **Sección:** bloque de cambio de herramienta
  ·  **Idioma:** —

```
T1 
SYN
M06
?%ETK[6]=1   
?%ETK[9]=1   
?%ETK[18]=1  
S18000M3 
G17
```

### `M5`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/prubafresas.iso (líneas 66-73) — SALIDA del postprocesador, no documentación. NO aparece en ningún manual`
  ·  **Sección:** cierre de la operación / retorno a Z de seguridad
  ·  **Idioma:** —

```
MLV=0
G0 G53 Z201.000 
MLV=2
?%ETK[13]=0   
?%ETK[18]=0 
M5 
MLV=0
G0 G53 Z201.000
```

### `SYN`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/NCI_ORI.CFG (líneas 4-13) — archivo de configuración de la instalación, NO es documentación`
  ·  **Sección:** $GEN_END
  ·  **Idioma:** —

```
$GEN_END
?%%ETK[0]=0
?%%ETK[1]=0
?%%ETK[2]=0
?%%ETK[13]=0
?%%ETK[17]=0
?%%ETK[18]=0
?%%ETK[19]=0
SYN JSR 8900
$
```

### `SYN`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/prubafresas.iso (líneas 27-29, 76-77, 111-112, 146-147, 181-182, 216) — SALIDA del postprocesador, no documentación`
  ·  **Sección:** antes de cada M06 (cambio de herramienta) y en el cierre del programa
  ·  **Idioma:** —

```
T1 
SYN
M06
[…]
G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000  
_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )  
SYN
?%ETK[0]=0
```

### `SYN (parecido: $Hnn_QVEC_SYN / XHSYNASS / $GEN_SYNCRO_PRISMA_ENABLE)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/_APPENDIX.htm (líneas 10583, 10713-10717, 10725-10729, 10739-10742, 10793-10802)`
  ·  **Sección:** Extra functions / Macro description (cabezal Prisma en cabezales paralelos)
  ·  **Idioma:** inglés

```
$GEN_SYNCRO_PRISMA_ENABLE
[…]
To take advantage of the angular position programmed in PGM, do not alter the configuration value «Angular detection quote». Use the macro «XHSYNASS» to identify a determined angular attitude of the Prisma, linked to the value of the NCI key (file Nci.cfg) «$Hnn_QVEC_SYN».

Key description

The value format of the key «Hnn_QVEC_SYN», where «nn» represents the number of the head, is a series of 4 numbers seperated by a comma that represents the angular vector value of the Prisma head for each one of the 4 (maximum) attitudes programmed by the Prisma when machining in parallel.
[…]
    $H04_QVEC_SYN
    -100, -150, -200, -250
    $
[…]
Attitude number = «n» [n=1,..,4]: angular quote of the vector of the Prisma in parallel heads mode is that indicated in the key Hnn_QVEC_SYN depending on that indicated in the previous paragraph
```

### `SYN (parecido: parámetro «anticipo syn/cut»)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/axis.msg (línea 134; ídem Ita/axis.msg 134 y Ing/axis.msg 134)`
  ·  **Sección:** parámetros de configuración de ejes — mensaje @173
  ·  **Idioma:** español / italiano / inglés

```
@173,"Tipo anticipo syn/cut (0:NO; 1:Boot+Step; 2:Boot; 3:Step):"   [Spa y Ita, idéntico]
@173,"Type of advance syn/cut (0:NO; 1:Boot+Step; 2:Boot; 3:Step):"   [Ing]
```

### `SYN (parecido: sincronización de cabezales con operadores ISO M o G)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/axis.msg (líneas 114, 132, 135)`
  ·  **Sección:** parámetros de configuración de ejes — mensajes @153, @171, @174
  ·  **Idioma:** español

```
@153,"Tipo de operadores ISO que controlan las sincronizaciones cabezas (0=M; 1=G):"
@171,"Cota de estacionamiento en Z para sincronización:"
@174,"Código de desincronización total:"
```

### `TABLA de funciones M (única lista con significados encontrada en todas las fuentes)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_panelmac/Celda_Nesting_con_retorno_autom_tico_del_tablero_protector_o_con_oscilaci_n_del_mismo..htm (líneas 158-178)`
  ·  **Sección:** Celda Nesting con retorno automático del tablero protector o con oscilación del mismo. → «Codigos M»
  ·  **Idioma:** español

```
Codigos M

M 100 Ciclo de carga Nesting, llamada del sub-programa %8100

M 99 Ciclo de descarga Nesting, llamada del sub-programa %8100

M 37 Habilitación y bloqueo vacío

M 27 Habilitación capa de aire

M 92 Barra alta

M 93 Barra baja

M 94 Cierre pinza Nesting

M 95 Apertura pinza Nesting
```

### `Otros códigos M documentados en las mismas fuentes (inventario completo de lo que SÍ tiene texto asociado)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (líneas 7232, 7512, 7594, 7765-7770) y out_editor_ing/_APPENDIX.htm (línea 6828)`
  ·  **Sección:** APÉNDICE I. Programación de los sujetadores Duomatic / MDI
  ·  **Idioma:** español e inglés

```
[ES, línea 7232] se envían al CN a través del archivo %8197 y se ejecutan a través de M197
[EN, línea 6828] In MDI the M6Txxx tool change-over commands are sent to the NC using file %8197 and are executed using M197. Therefore, you must set the association between the program and the M code.
[ES, línea 7512] M193  (cambio entre sujetadores delanteros y traseros)
[EN, línea 7104] M193  (exchange front and rear clamps)
[ES, líneas 7765-7770] M191 = Activación Equipo
M190 = Desactivación Equipo
```

### `Contexto de la instrucción ISO del PGM (es la que permite escribir códigos M dentro de un programa PGM)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm (líneas 781-859)`
  ·  **Sección:** Instrucción ISO - ISO
  ·  **Idioma:** español

```
Instrucción ISO - ISO

Permite programar una instrucción en el lenguaje ISO del control numérico usado; la instrucción debe colocarse entre dobles ápices y puede ser ejecutada desde una lista de parámetros separados por lo menos por un espacio (la estructura y el significado de los parámetros están descritos en el párrafo correspondiente a la instrucción PRINT). En la instrucción no se efectúa ningún control sintáctico y a ésta no le corresponde ninguna visualización gráfica.

[…]

Ejemplos:

ISO "G0X1000Y740F6000"

ISO "M71"

ISO "M?d" 110+Campana
```

**No aparece en ninguna fuente:** `SYN — NO APARECE en ninguno de los manuales: ni en out_spa (1436 htm), ni en out_editor_ing (1434 htm), ni en out_epl, ni en out_panelmac, ni en out_winxiso_spa ni out_testine_spa (los dos CHM que faltaban y que extraje para este relevamiento), ni en maestro_editor_es.txt, ni en XilogMaestroScripting.chm (es-ES, que también extraje), ni en pgmx/docs/xilog_plus_pgm ni en pgmx/docs/maestro_scripting. Probé variantes: SYN, syn, %SYN, SYN[, con y sin delimitadores. Solo aparece como token real en dos lugares NO documentales: NCI_ORI.CFG y los .iso de salida del postprocesador (ambos citados arriba).`, `M5 / M05 — NO APARECE en ninguna fuente documental (ningún CHM, ningún .msg, ningún .txt de la instalación, ni el manual del Maestro Editor, ni pgmx/docs). Solo aparece como token real en los .iso de salida del postprocesador.`, `M3 / M03 como término aislado — NO APARECE en ninguna fuente documental. En los manuales solo aparece embebido dentro de la cadena de configuración «M65M3S%ld» (nci.cfg del Grupo Hueco Cerradura con Eje Tilting), y como token real en los .iso de salida («S18000M3»).`, `Una TABLA GENERAL de funciones M con su significado — NO APARECE en ninguna de las 8 fuentes. Lo único que existe es la lista de 8 códigos M del ciclo Nesting en la ayuda de PanelMac (M100, M99, M37, M27, M92, M93, M94, M95), citada arriba, que no incluye M58, M2, M3 ni M5. La ayuda del Editor remite explícitamente a un manual externo que NO está en estas fuentes: «(Véase el manual Diagnóstico y Códigos M, que se suministra con la máquina)» / «(Also see: Diagnostics manual and M Codes provided with the machine)».`, `M58 con significado explicado en un manual — NO APARECE. Los manuales lo mencionan siempre de pasada (como «solicitud del bloqueo pieza» junto a M28/M38/M39, y como «habilitar el bloqueo» en PanelMac), nunca con una entrada propia que lo defina. La única glosa literal del término está en un comentario del archivo de configuración NCI.CFG, en italiano: «M58 ;abilita controllo vuoto».`, `Inventario completo de códigos M citados en los manuales (para que veas que no hay más): out_spa → M02, M2, M20, M201, M21, M28, M31, M32, M38, M39, M50, M58, M71, M81, M111, M114, M185, M190, M191, M193, M194, M197. out_editor_ing → los mismos más M51. out_panelmac → M2, M27, M37, M58, M92, M93, M94, M95, M99, M100. out_epl → ningún código M.`

## MLV

### `MLV / MLV=0 / MLV=1 / MLV=2 — RESULTADO NEGATIVO EN TODA LA DOCUMENTACIÓN`

**Fuente:** `Fuentes 1-7 completas: out_spa/ (45 .htm + 1191 imágenes), out_editor_ing/ (46 .htm), out_epl/, out_panelmac/, maestro_editor_es.txt, pgmx/docs/xilog_plus_pgm/, pgmx/docs/maestro_scripting/`
  ·  **Sección:** (barrido completo, no una sección)
  ·  **Idioma:** español, inglés

```
NO APARECE. Barrido con las variantes: MLV, mlv, %MLV, [MLV], 'M *L *V *=', 'MLV *= *[012]' → 0 archivos en las siete fuentes documentales. Se agregaron a la búsqueda los PDF 'Maestro Editor' en en-US, it-IT y de-DE (extraídos con pdftotext) → tampoco aparece. Se contaron 0 ocurrencias en Testine.chm, Xilog_Plus_WinXiso.chm, Xilog_Plus_Epl.chm y Xilog_Plus_PanelMac.chm (Spa/Ing/Ita), en XilogMaestroScripting.chm (es-ES/en-US/it-IT), en WINXISO.HLP y en los 13 archivos ap2Osai.msg. Ninguna fuente documental define MLV ni sus niveles.
```

### `NOTA DE COBERTURA — el corpus documental extraído no contiene NINGÚN registro de nivel ISO`

**Fuente:** `out_spa/, out_editor_ing/, out_epl/, out_panelmac/, maestro_editor_es.txt, pdfs Maestro Editor en/it/de`
  ·  **Sección:** (control de método)
  ·  **Idioma:** español, inglés

```
Control ejecutado sobre términos vecinos conocidos: 'SHF' y 'ETK' tampoco aparecen en el TEXTO de ninguno de estos manuales — los únicos aciertos fueron coincidencias de bytes dentro de archivos .jpg/.gif (image025.jpg, image1053.jpg, image099.jpg, etc.). Dato estructural: de los 1436 archivos de out_spa solo 45 son .htm (1197 .jpg, 187 .gif); de out_editor_ing, 46 .htm. El corpus de texto real de la ayuda del Editor es de ~45 páginas por idioma, no 1436.
```

### `MLV=2 / MLV=1 / MLV=0 (aparición literal, SIN definición)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Bin/VtGenIso.dll — tabla de cadenas, offsets 240884 / 240976 / 241119`
  ·  **Sección:** Plantilla ISO embebida en el generador; comentarios en italiano
  ·  **Idioma:** italiano (comentarios), ISO (código)

```
?%%ETK[6]=%ld	;Angolo=%.3f
?%%ETK[8]=%ld	;Motore=%d,Strobe=%u
MLV=2
VL5=2
SHF[X]=%.3f
SHF[Y]=%.3f
;Testa Laser con Motore Numero %d - LKey %d
G17
MLV=1
VL5=1
SHF[X]=%.3f
SHF[Y]=%.3f
?%%ETK[7]=0
?%%ETK[8]=0
?%%EDK[%d].0=1
M20
?%%EDK[%d].0=0
G71
?%%ETK[7]=0
G61
SVL 0.000
SVR 0.000
MLV=0
VL5=0
G0G53Z%.3f
(DLY,0.2)
E1011=%ld
E1010=%ld
E1012=%ld
```

### `MLV=2 / MLV=1 / MLV=0 (aparición literal, SIN definición)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Bin/PlPathFilter32.dll — tabla de cadenas, 7 ocurrencias en offsets 171956, 171992, 172060, 172184, 172201, 172572, 172616`
  ·  **Sección:** Plantillas ISO embebidas para ventosas/traversas ($MA_END3_FILE, $MA_CHANGE_END, $MA_RESTORE_INFO, $MA_INIT3_FILE); comentarios en italiano
  ·  **Idioma:** italiano (comentarios), ISO (código)

```
?%%EDK[%d].0=0
VL6=0
VL7=0
M20
MLV=2
SHF[X]=0
SHF[Y]=0
SHF[Z]=0
MLV=1
SHF[X]=0
SHF[Y]=0
SHF[Z]=0
?%%EDK[%d].0=1
$MA_END3_FILE
MLV=0
$MA_END5_FILE
G300 S0
G169
G333
$MA_RESTORE_END
;Cancellazione Ventosa %d della Traversa %d
$MA_CHANGE_END
MLV=0
G0G53Z%.3f
MLV=2
;Attesa conferma cambiamenti da parte dell'Operatore!
;Trascinamento Ventose della Traversa %d
$MA_RESTORE_POSITION
Standard_Manina
$MA_RESTORE_INFO
;Ripristino Ventose della Traversa %d
?%%ETK[904]=%d ;utensile
?%%ETK[903]=%d ;traverse
;TRAZ sulla base del pianetto utensile
;RIFZ sul filo superiore delle ventose
SVL 0
VL6=0
SYN
MLV=2
SHF[X]=%.3f
SHF[Y]=%.3f
SHF[Z]=%.3f
MLV=1
SHF[X]=%.3f
SHF[Y]=%.3f
SHF[Z]=%.3f
G0G53Z%.3f
$MA_INIT3_FILE
```

### `MLV=0 / MLV=1 / MLV=2 (aparición literal en salida ISO, SIN definición)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/pieza 300x300 calxy.iso — líneas 5 a 52`
  ·  **Sección:** Encabezado y primer cambio de herramienta del programa ISO
  ·  **Idioma:** ISO

```
_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
%Or[0].ofX=-305000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=50000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-305.000 
SHF[Y]=-1515.750 
SHF[Z]=50.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 
?%ETK[8]=1 
G40 
?%ETK[7]=0 
?%ETK[8]=1 
G40 
MLV=0 
T3 
SYN
M06
?%ETK[6]=1   
?%ETK[9]=3   
?%ETK[18]=1  
S18000M3 
G17 
MLV=2 
%Or[0].ofX=-310000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=50000.000 
MLV=1 
SHF[X]=-305.000 
SHF[Y]=-1510.750 
SHF[Z]=50.000 
MLV=2 
?%ETK[13]=1  
MLV=2 
SHF[X]=31.900 
SHF[Y]=-246.850 
SHF[Z]=-125.300 
G0 X-9.520 Y-10.520 
G0 Z132.200 
D1
```

### `MLV=0 / MLV=2 (aparición literal en salida ISO, SIN definición)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/pieza 300x300 calxy.iso — líneas 71 a 99`
  ·  **Sección:** Fin de herramienta y siguiente cambio de herramienta
  ·  **Idioma:** ISO

```
SVL 0.000 
VL6=0.000
SVR 0.000 
VL7=0.000
?%ETK[7]=0 
?%ETK[7]=0 
MLV=0
G0 G53 Z201.000 
MLV=2
?%ETK[13]=0   
?%ETK[18]=0 
M5 
MLV=0
G0 G53 Z201.000 
MLV=0 
T5 
SYN
M06
?%ETK[9]=5   
?%ETK[18]=1  
S18000M3 
G17 
MLV=2 
?%ETK[13]=1  
G0 X4.000 Y5.000 
G0 Z165.900 
D1
SVL 145.900 
VL6=145.900
```

### `MLV=1 / MLV=2 / MLV=0 (aparición literal en salida ISO, SIN definición)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/lado_derecho1.iso — líneas 34 a 111`
  ·  **Sección:** Bloques con SHF y cambio de herramienta (extracto con contexto de grep)
  ·  **Idioma:** ISO

```
S18000M3 
G17 
MLV=2 
%Or[0].ofX=-359549.988 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=43000.000 
MLV=1 
[...]
SHF[Y]=-1510.750 
SHF[Z]=43.000 
MLV=2 
?%ETK[13]=1  
MLV=2 
SHF[X]=31.900 
SHF[Y]=-246.850 
SHF[Z]=-137.800 
G0 X-19.360 Y112.640 
[...]
MLV=0
G0 G53 Z201.000 
MLV=2
G61 
MLV=0 
?%ETK[13]=0   
?%ETK[18]=0 
[...]
MLV=1 
SHF[Z]=25.000+%ETK[114]/1000
MLV=2 
G17 
?%ETK[6]=58   
MLV=2 
SHF[X]=32.250 
SHF[Y]=-23.000 
SHF[Z]=66.300 
?%ETK[17]=257  
[...]
MLV=1 
SHF[Z]=25.000+%ETK[114]/1000
MLV=2
```

### `Otros archivos de la instalación que contienen MLV (lista exhaustiva con límite de palabra)`

**Fuente:** `C:/Program Files (x86)/Scm Group/ — barrido rg -a -l "\bMLV\b" sobre la instalación entera`
  ·  **Sección:** (inventario)
  ·  **Idioma:** n/a

```
.\Xilog Plus\Bin\PlPathFilter32.dll
.\Xilog Plus\Bin\VtGenIso.dll
.\Xilog Plus\Bin\Xilog_Plus_Editor.chm
.\Maestro\PostProcessor\rebaje laterales.iso
.\Maestro\PostProcessor\prubafresas.iso
.\Maestro\PostProcessor\pieza 300x300 calxy.iso
.\Maestro\PostProcessor\lado_izquierdo1.iso
.\Maestro\PostProcessor\lado_derecho1.iso
.\Maestro\OpenCascade\TKIGES.dll
.\Xilog Plus\Country\Spa\Xilog_Plus_Editor.chm
```

### `MLV en los .chm de Xilog_Plus_Editor — DESCARTADO como ruido de compresión`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/Xilog_Plus_Editor.chm (offsets 352453, 2754227, 6972813)`
  ·  **Sección:** (sección comprimida LZX, no texto de ayuda)
  ·  **Idioma:** n/a

```
Volcado de bytes alrededor del offset 352453: "...223 \t _ 262 256 M 360 027 q M L V 360 307 212 245 203 233 W 276 6 005 L 364...". Los tres aciertos caen dentro de datos comprimidos, no de texto. Los conteos por idioma no coinciden entre sí (Spa=3, Ing=2, Ita=1), y el HTML ya extraído de esos mismos .chm no contiene MLV. PARECIDO, NO IDÉNTICO: no es una ocurrencia del término.
```

### `MLV en UI00.xml (todos los idiomas) — FALSO POSITIVO`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/Languages/*/UI00.xml (es-ES, en-US, it-IT, de-DE, pt-BR, ru-RU, nl-NL, bg-BG, da-DK, fr-FR)`
  ·  **Sección:** Cadenas de la UI de Maestro
  ·  **Idioma:** español (y demás)

```
<string code="ScriptSubprogramXamlVersionComment">Número de versión</string> — la coincidencia es la subcadena "...Xam-lV-ersion..." en modo case-insensitive. La búsqueda con límite de palabra (rg -o "\bMLV\b") devuelve VACÍO en estos archivos. PARECIDO, NO IDÉNTICO: no es el término MLV.
```

**No aparece en ninguna fuente:** `MLV — no aparece en NINGUNA fuente documental (fuentes 1 a 7, ni en los PDF Maestro Editor en/it/de, ni en WINXISO.HLP, ni en ap2Osai.msg, ni en XilogMaestroScripting.chm): no hay definición del registro en ningún manual`, `MLV=0 — no aparece descrito ni definido en ninguna fuente documental; solo como literal en plantillas de código (VtGenIso.dll, PlPathFilter32.dll) y en salidas .iso`, `MLV=1 — no aparece descrito ni definido en ninguna fuente documental; solo como literal en plantillas de código (VtGenIso.dll, PlPathFilter32.dll) y en salidas .iso`, `MLV=2 — no aparece descrito ni definido en ninguna fuente documental; solo como literal en plantillas de código (VtGenIso.dll, PlPathFilter32.dll) y en salidas .iso`, `Relación MLV↔SHF — no aparece enunciada en ninguna fuente documental. La única evidencia de coexistencia es de proximidad textual dentro de las plantillas de los DLL y de los .iso; ninguna fuente la explica`

## SHF

### `SHF[X], SHF[Y], SHF[Z]`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/rebaje laterales.iso (líneas 1-21, cabecera del archivo)`
  ·  **Sección:** Archivo ISO de ejemplo que vino con la instalación (carpeta PostProcessor de Maestro). NO es documentación: es un ISO ya postprocesado.
  ·  **Idioma:** n/a (código ISO)

```
% rebaje laterales.pgm
;H DX=704.000 DY=549.550 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
%Or[0].ofX=-704000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=43000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-704.000 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
G40
```

### `SHF[X], SHF[Y], SHF[Z]`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/lado_izquierdo1.iso (líneas 1-22, cabecera)`
  ·  **Sección:** Archivo ISO de ejemplo de la instalación (carpeta PostProcessor de Maestro).
  ·  **Idioma:** n/a (código ISO)

```
% lado_izquierdo1.pgm
;H DX=747.000 DY=584.550 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
%Or[0].ofX=-747000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=43000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-747.000 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
G40
```

### `SHF[Z] con expresión aritmética`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/lado_izquierdo1.iso (líneas 17-19, 41-43, 47-49, 89, 106, 109)`
  ·  **Sección:** Mismo archivo ISO: muestra SHF[Z] escrito TANTO con expresión como con número pelado, y con distintos valores base (43.000 y 25.000).
  ·  **Idioma:** n/a (código ISO)

```
SHF[X]=-747.000 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
[...]
SHF[X]=-747.000 
SHF[Y]=-1510.750 
SHF[Z]=43.000 
[...]
SHF[X]=31.900 
SHF[Y]=-246.850 
SHF[Z]=-137.800 
[...]
SHF[Z]=25.000+%ETK[114]/1000
[...]
SHF[Z]=43.000+%ETK[114]/1000
SHF[Z]=25.000+%ETK[114]/1000
```

### `SHF[X], SHF[Y], SHF[Z]`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/pieza 300x300 calxy.iso (líneas 15-21 y 39-49)`
  ·  **Sección:** Archivo ISO de ejemplo de la instalación. Acá el valor base de SHF[Z] es 50.000, y aparece junto a %Or[0].ofZ=50000.000.
  ·  **Idioma:** n/a (código ISO)

```
?%EDK[1].0=0 
MLV=1 
SHF[X]=-305.000 
SHF[Y]=-1515.750 
SHF[Z]=50.000+%ETK[114]/1000 
?%ETK[8]=1 
G40 
[...]
%Or[0].ofZ=50000.000 
MLV=1 
SHF[X]=-305.000 
SHF[Y]=-1510.750 
SHF[Z]=50.000 
MLV=2 
?%ETK[13]=1  
MLV=2 
SHF[X]=31.900 
SHF[Y]=-246.850 
SHF[Z]=-125.300 
G0 X-9.520 Y-10.520 
G0 Z132.200
```

### `SHF[X]=0 / SHF[Y]=0 / SHF[Z]=0 (bloque de cierre)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/pieza 300x300 calxy.iso (líneas 135-145)`
  ·  **Sección:** Final del archivo ISO de ejemplo. El mismo bloque aparece en rebaje laterales.iso (líneas 120-130) y en prubafresas.iso (líneas 225-233).
  ·  **Idioma:** n/a (código ISO)

```
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
```

### `SHF[X], SHF[Y], SHF[Z]`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/lado_derecho1.iso (líneas 16-19, 40-49, 88-96, 106-107)`
  ·  **Sección:** Archivo ISO de ejemplo de la instalación. Muestra SHF[Z] con dos bases distintas (43.000 y 25.000) dentro del mismo programa, ambas con la misma expresión.
  ·  **Idioma:** n/a (código ISO)

```
MLV=1 
SHF[X]=-354.550 
SHF[Y]=-1515.750 
SHF[Z]=43.000+%ETK[114]/1000 
?%ETK[8]=1 
[...]
MLV=1 
SHF[X]=-354.550 
SHF[Y]=-1510.750 
SHF[Z]=43.000 
MLV=2 
[...]
MLV=2 
SHF[X]=31.900 
SHF[Y]=-246.850 
SHF[Z]=-137.800 
G0 X-19.360 Y112.640 
[...]
MLV=1 
SHF[Z]=25.000+%ETK[114]/1000
MLV=2 
[...]
MLV=2 
SHF[X]=32.250 
SHF[Y]=-23.000 
SHF[Z]=66.300 
?%ETK[17]=257  
[...]
MLV=1 
SHF[Z]=43.000+%ETK[114]/1000
```

### `SHF[X]=%.3f / SHF[Y]=%.3f (plantilla de formato)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Bin/VtGenIso.dll (offset ~240896, tabla de literales del binario)`
  ·  **Sección:** No es documentación: son las cadenas de formato embebidas en el DLL generador de ISO. Bloque rotulado GEN_CROSSLASER_*. Los '|' de abajo son separadores NUL/no-imprimibles entre literales, no parte del texto.
  ·  **Idioma:** literales en código (comentarios en italiano)

```
CROSSLASER_ID|||GEN_CROSSLASER_ORIGIN_INIT||GEN_CROSSLASER_FREE|GEN_CROSSLASER_INIT|?%%ETK[7]=%ld|;LKey|||||G0X%.3fY%.3f||||?%%ETK[6]=%ld|;Angolo=%.3f|?%%ETK[8]=%ld|;Motore=%d,Strobe=%u|||MLV=2|VL5=2|SHF[X]=%.3f|SHF[Y]=%.3f|||||;Testa Laser con Motore Numero %d - LKey %d|||||G17|MLV=1|VL5=1|SHF[X]=%.3f|SHF[Y]=%.3f|||||?%%ETK[7]=0|?%%ETK[8]=0|?%%EDK[%d].0=1|M20|?%%EDK[%d].0=0|@|G71|?%%ETK[7]=0|G61|D0|SVL 0.000|SVR 0.000|MLV=0|VL5=0|G0G53Z%.3f|||M0|(DLY,0.2)
```

### `SHF[X]=0 / SHF[Y]=0 / SHF[Z]=0 (plantilla de formato)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Bin/PlPathFilter32.dll (offset ~171962, tabla de literales del binario)`
  ·  **Sección:** No es documentación: cadenas embebidas en el DLL, entre las etiquetas $MA_SET_INFO, $MA_END3_FILE, $MA_END5_FILE, $MA_RESTORE_END. Los '|' son separadores no-imprimibles.
  ·  **Idioma:** literales en código (comentarios en italiano)

```
$MA_SET_INFO||||G0 Z%.3f||||G0 X%.3f Y%.3f||;|;Posizionamento Ventosa %d della Traversa %d||@|||M2||M5||?%%EDK[%d].0=0||VL6=0|VL7=0|M20|||||MLV=2|SHF[X]=0|SHF[Y]=0|SHF[Z]=0||||MLV=1|SHF[X]=0|SHF[Y]=0|SHF[Z]=0||||?%%EDK[%d].0=1||$MA_END3_FILE|||MLV=0|||$MA_END5_FILE|||G300 S0|G169|G333|||$MA_RESTORE_END|;|;Cancellazione Ventosa %d della Traversa %d
```

### `idea de "origen desplazado" — instrucción O (PARECIDO, NO IDÉNTICO: no dice SHF en ningún lado)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm, líneas 3810-3859`
  ·  **Sección:** 5.2.2 Instrucciones modales → "Desplazamiento del origen del tablero en tope - O"
  ·  **Idioma:** es

```
5.2.2 Instrucciones modales

Desplazamiento del origen del tablero en tope - O

Desplaza el origen del tablero en tope a la posición programada; todas las instrucciones que siguen se refieren al nuevo origen.

Parámetros:

X — Origen en X.
Y — Origen en Y.
Z — Origen en Z.
f — Si ha sido programado con el número de una cara (1-5), habilita la instrucción sólo para el origen de la cara planteada.
```

### `idea de "origen desplazado" — instrucción O, versión inglesa (PARECIDO, NO IDÉNTICO)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_editor_ing/5.2_Basic_Instructions_(text).htm, líneas 3768-3776`
  ·  **Sección:** 5.2.2 Modal Instructions → "Move the origin of the panel to position - O"
  ·  **Idioma:** en

```
5.2.2 Modal Instructions

Move the origin of the panel to position - O

Moves the origin of the panel to the programmed position. All the following instructions will refer to the new origin.

Parameters:
```

### `"shift" como palabra (PARECIDO, NO IDÉNTICO: habla de programación incremental, no de SHF)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_editor_ing/5.3_Extended_Instructions_(Graphic).htm, líneas 6224-6229`
  ·  **Sección:** 5.3 Extended Instructions (Graphic) — párrafo sobre programación incremental
  ·  **Idioma:** en

```
When incremental programming is enabled, the reading enabled as incremental (X or Y or both), programmed in an operative instruction, no longer refers to positioning with respect to the origin of the panel but to a shift of the value that the reading itself had undergone after carrying out the previous operative instruction.
```

### `"traslación" (PARECIDO, NO IDÉNTICO: en la ayuda significa MOVIMIENTO de los cabezales, no desplazamiento de origen)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm, líneas 10548-10573`
  ·  **Sección:** Apéndice — "Acercamiento al trabajo" y "Traslaciones sobre la mesa"
  ·  **Idioma:** es

```
Acercamiento al trabajo

En algunas máquinas el cabezal que debe realizar el primer trabajo sobre el tablero baja antes o durante la traslación; la cota Z a la cual debe efectuarse el traslado se determina únicamente en función de la dimensión Z del tablero (valor del campo DZ del encabezamiento del programa); por lo tanto, no se tiene en cuenta la dimensión total de los tableros que se hallen posiblemente en otras zonas de trabajo. En caso de choque contra los otros tableros será necesario anteponer, al primer trabajo del programa, una o varias instrucciones N o XN a través de las cuales controlar la traslación con seguridad. El mismo procedimiento deberá aplicarse también en los trabajos sucesivos, en caso de que los cabezales deban ser trasladados por encima de otros tableros.

Traslaciones sobre la mesa

Las traslaciones de los cabezales, en fase de acercamiento al punto de inicio del trabajo sucesivo, están optimizadas en función de las herramientas / grupos de la dimensión Z del tablero. Si no existe una cota de seguridad a la cual realizar el traslado sobre el tablero con las herramientas / grupos montados, se emite el error «No existe cota de seguridad sobre la pieza».
```

### `[Shift] (PARECIDO SOLO EN LA GRAFÍA: es la TECLA del teclado)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.3_Instrucciones_completas_(gr_ficas).htm (línea 1358) y scratchpad/maestro_editor_es.txt (línea 1876)`
  ·  **Sección:** Barras de mandos / selección de entidades
  ·  **Idioma:** es

```
La función también se activa pulsando las teclas [Shift]+[F1].

[maestro_editor_es.txt] Para seleccionar más de una entidad, se puede proceder como en el caso de la selección simple, manteniendo presionada la tecla "shift".
```

**No aparece en ninguna fuente:** `SHF — no aparece en scratchpad/out_spa/ (ayuda Xilog Plus Editor en español, 1436 archivos). Búsqueda sensible e insensible a mayúsculas: 0 archivos.`, `SHF — no aparece en scratchpad/out_editor_ing/ (ayuda Xilog Plus Editor en inglés, 1434 archivos). 0 archivos.`, `SHF — no aparece en scratchpad/out_epl/ (ayuda módulo EPL, 210 archivos). 0 archivos.`, `SHF — no aparece en scratchpad/out_panelmac/ (ayuda PanelMac, 271 archivos). 0 archivos.`, `SHF — no aparece en scratchpad/maestro_editor_es.txt (manual Maestro Editor español, 170 páginas). 0 coincidencias.`, `SHF — no aparece en c:/Dev/Repositorios/ProdAction/pgmx/docs/xilog_plus_pgm/ ni en pgmx/docs/maestro_scripting/. 0 archivos.`, `SHF[X] / SHF[Y] / SHF[Z] con corchetes — no aparecen en NINGUNA de las fuentes de documentación (las 4 ayudas CHM, el manual del Maestro Editor, ni pgmx/docs). Solo aparecen en archivos .iso de ejemplo y en literales embebidos en dos DLL de la instalación.`, `%SHF (con signo de porcentaje) — no aparece en ninguna fuente, ni en documentación ni en los .iso ni en los binarios.`, `SHF en los 142 .txt sueltos de C:/Program Files (x86)/Scm Group/ — no aparece: la búsqueda insensible a mayúsculas sobre *.txt devolvió 0 archivos.`, `Documentación de que SHF admita expresiones — no aparece. En ninguna fuente escrita hay una definición, sintaxis ni tabla de SHF. La única evidencia de la expresión es el texto literal de los .iso de ejemplo (SHF[Z]=43.000+%ETK[114]/1000 y SHF[Z]=50.000+%ETK[114]/1000), citado arriba.`, `ETK / %ETK — no aparece en ninguna de las 4 ayudas CHM ni en el manual del Maestro Editor. Solo aparece en los .iso, en los DLL y en material propio del scratchpad.`, `MLV / VL5 / SVL (códigos que acompañan a SHF en los .iso) — no aparecen en ninguna de las 4 ayudas CHM ni en el manual del Maestro Editor.`, `Falsos positivos descartados (NO son SHF): 'shFreqConv' en Maestro/Tlgx/def.tlgx; el nombre de archivo MSHFLXGD.OCX; y las coincidencias de 3 letras dentro de los streams comprimidos de los PDF 'Maestro Editor.pdf' (que al extraerse dan basura tipo 'sHf"', '$e$sHf', no texto legible).`

## VL

### `VL6 / VL7 (bloque de entrada, tras D1)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\rebaje laterales.iso — lineas 51-58`
  ·  **Sección:** Archivo ISO de ejemplo alojado en la carpeta PostProcessor de Maestro. No es documentacion: no hay titulo de seccion ni texto explicativo, solo codigo.
  ·  **Idioma:** n/a (codigo ISO)

```
G0 Z146.300
D1
SVL 126.000
VL6=126.000
SVR 9.180
VL7=9.180
?%ETK[7]=4
G42
```

### `VL6 / VL7 (bloque de salida, tras D0)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\rebaje laterales.iso — lineas 67-74`
  ·  **Sección:** Archivo ISO de ejemplo, carpeta PostProcessor de Maestro (sin seccion ni titulo).
  ·  **Idioma:** n/a (codigo ISO)

```
G1 X717.770 Y29.230 Z20.300 F3000.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
?%ETK[7]=0
?%ETK[7]=0
```

### `VL6 / VL7 (cierre de archivo, antes de M2)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\rebaje laterales.iso — lineas 120-133 (final del archivo, 133 lineas en total)`
  ·  **Sección:** Archivo ISO de ejemplo, carpeta PostProcessor de Maestro (sin seccion ni titulo).
  ·  **Idioma:** n/a (codigo ISO)

```
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

### `VL6 / VL7 — todas las apariciones de un archivo (tabla completa)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\prubafresas.iso — 237 lineas; VL6 y VL7 aparecen 11 veces cada uno`
  ·  **Sección:** Archivo ISO de ejemplo, carpeta PostProcessor de Maestro (sin seccion ni titulo). Se transcriben TODOS los bloques con VL, en orden.
  ·  **Idioma:** n/a (codigo ISO)

```
lineas 50-57:
G0 Z145.400
D1
SVL 125.400
VL6=125.400
SVR 9.180
VL7=9.180
G1 Z-1.000 F2000.000
?%ETK[7]=4

lineas 60-67:
G0 Z20.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
MLV=0
G0 G53 Z201.000

lineas 85-92:
G0 Z132.200
D1
SVL 112.200
VL6=112.200
SVR 4.760
VL7=4.760
G1 Z-1.000 F3000.000
?%ETK[7]=4

lineas 95-102:
G0 Z20.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
MLV=0
G0 G53 Z201.000

lineas 120-127:
G0 Z127.200
D1
SVL 107.200
VL6=107.200
SVR 2.000
VL7=2.000
G1 Z-1.000 F2000.000
?%ETK[7]=4

lineas 130-137:
G0 Z20.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
MLV=0
G0 G53 Z201.000

lineas 155-162:
G0 Z165.900
D1
SVL 145.900
VL6=145.900
SVR 38.000
VL7=38.000
G1 Z-1.000 F2000.000
?%ETK[7]=4

lineas 165-172:
G0 Z20.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
MLV=0
G0 G53 Z201.000

lineas 190-197:
G0 Z140.600
D1
SVL 120.600
VL6=120.600
SVR 40.000
VL7=40.000
G1 Z-1.000 F2000.000
?%ETK[7]=4

lineas 199-206:
G0 Z20.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
?%ETK[7]=0
G61

lineas 231-237 (final):
SHF[Y]=0
SHF[Z]=0
MLV=0
VL6=0
VL7=0
?%EDK[13].0=0
M2
```

### `VL6 / VL7`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\lado_izquierdo1.iso — lineas 51-58, 70-77, 362-369, 371-378, 479-485 (485 lineas en total)`
  ·  **Sección:** Archivo ISO de ejemplo, carpeta PostProcessor de Maestro (sin seccion ni titulo). Se transcriben TODOS los bloques con VL.
  ·  **Idioma:** n/a (codigo ISO)

```
lineas 51-58:
G0 Z146.300
D1
SVL 126.300
VL6=126.300
SVR 9.180
VL7=9.180
?%ETK[7]=4
G41

lineas 70-77:
G1 X389.360 Y598.910 Z20.000 F3000.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
?%ETK[7]=0
?%ETK[8]=1

lineas 362-369:
G0 Z80.000
D1
SVL 60.000
VL6=60.000
SVR 1.600
VL7=1.600
G1 Z-10.000 F2000.000
?%ETK[7]=1

lineas 371-378:
G0 Z20.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
?%ETK[7]=0
?%ETK[8]=1

lineas 479-485 (final):
SHF[Y]=0
SHF[Z]=0
MLV=0
VL6=0
VL7=0
?%EDK[13].0=0
M2
```

### `VL6 / VL7`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\lado_derecho1.iso — lineas 51-58, 70-77, 344-350 (350 lineas en total)`
  ·  **Sección:** Archivo ISO de ejemplo, carpeta PostProcessor de Maestro (sin seccion ni titulo). Se transcriben TODOS los bloques con VL.
  ·  **Idioma:** n/a (codigo ISO)

```
lineas 51-58:
G0 Z146.300
D1
SVL 126.000
VL6=126.000
SVR 9.180
VL7=9.180
?%ETK[7]=4
G41

lineas 70-77:
G1 X-19.360 Y149.360 Z20.300 F3000.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
?%ETK[7]=0
?%ETK[8]=5

lineas 344-350 (final):
SHF[Y]=0
SHF[Z]=0
MLV=0
VL6=0
VL7=0
?%EDK[13].0=0
M2
```

### `VL6 / VL7`

**Fuente:** `C:\Program Files (x86)\Scm Group\Maestro\PostProcessor\pieza 300x300 calxy.iso — lineas 51-58, 69-76, 96-103, 109-116, 142-148 (148 lineas en total)`
  ·  **Sección:** Archivo ISO de ejemplo, carpeta PostProcessor de Maestro (sin seccion ni titulo). Se transcriben TODOS los bloques con VL.
  ·  **Idioma:** n/a (codigo ISO)

```
lineas 51-58:
G0 Z132.200
D1
SVL 112.200
VL6=112.200
SVR 4.760
VL7=4.760
?%ETK[7]=4
G42

lineas 69-76:
G1 X-10.520 Y-9.520 Z20.000 F18000.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
?%ETK[7]=0
?%ETK[7]=0

lineas 96-103:
G0 Z165.900
D1
SVL 145.900
VL6=145.900
SVR 38.000
VL7=38.000
?%ETK[7]=4
G1 X5.000 Z-0.250 F2000.000

lineas 109-116:
G0 Z20.000
D0
SVL 0.000
VL6=0.000
SVR 0.000
VL7=0.000
?%ETK[7]=0
G61

lineas 142-148 (final):
SHF[Y]=0
SHF[Z]=0
MLV=0
VL6=0
VL7=0
?%EDK[13].0=0
M2
```

### `VL6=0 / VL7=0 (literales dentro del binario emisor)`

**Fuente:** `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\PlPathFilter32.dll — cadenas ASCII en offsets 0x29fa0, 0x29fa6 y 0x2a211`
  ·  **Sección:** No es documentacion: son cadenas de texto extraidas del binario. Se transcriben las cadenas vecinas en el orden en que estan en el archivo, sin agregar nada. Los rotulos vecinos ($MA_..., ;Posizionamento..., ;Quote di parcheggio) estan en italiano.
  ·  **Idioma:** n/a (cadenas de binario; comentarios en italiano)

```
0x29f56 ';Posizionamento Ventosa %d della Traversa %d'
0x29f90 '?%%EDK[%d].0=0'
0x29fa0 'VL6=0'
0x29fa6 'VL7=0'
0x29fac 'M20'
0x29fb4 'MLV=2'
0x29fba 'SHF[X]=0'
0x29fc3 'SHF[Y]=0'
0x29fcc 'SHF[Z]=0'
0x29fd8 'MLV=1'
0x29fde 'SHF[X]=0'
0x29fe7 'SHF[Y]=0'
0x29ff0 'SHF[Z]=0'
0x29ffc '?%%EDK[%d].0=1'
0x2a00c '$MA_END3_FILE'
0x2a01c 'MLV=0'

(y mas adelante, otro bloque:)
0x2a180 '?%%ETK[904]=%d ;utensile'
0x2a19e '?%%ETK[903]=%d ;traverse'
0x2a1b8 ';TRAZ sulla base del pianetto utensile'
0x2a1e0 ';RIFZ sul filo superiore delle ventose'
0x2a20b 'SVL 0'
0x2a211 'VL6=0'
0x2a217 'SYN'
0x2a21c 'MLV=2'
0x2a222 'SHF[X]=%.3f'
0x2a22e 'SHF[Y]=%.3f'
0x2a23a 'SHF[Z]=%.3f'
0x2a248 'MLV=1'
0x2a24e 'SHF[X]=%.3f'
0x2a25a 'SHF[Y]=%.3f'
0x2a266 'SHF[Z]=%.3f'
0x2a274 'G0G53Z%.3f'
```

### `"variables locales" / "variable local" — PARECIDO, NO IDENTICO`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:\Users\fermi\AppData\Local\Temp\claude\c--Dev-Repositorios-ProdAction\2b4a4df7-b886-481a-99e7-9a86bef428d6\scratchpad\out_spa\6.4_Pasaje_de_par_metros_a_subprogramas_y_macros.htm`
  ·  **Sección:** 6.4 Pasaje de parametros a subprogramas y macros — apartado "2) Programacion de variables globales"
  ·  **Idioma:** espanol

```
2) Programacion de variables globales.
Todas las variables, definidas en el programa principal antes de la llamada de un subprograma (o de una macro), pueden ser llamadas dentro del subprograma mismo (o de la macro). En el subprograma (o en la macro), estas variables pueden manejarse como las variables locales (que son las definidas internamente), con la diferencia que son inicializadas automaticamente con el valor que tenian en el programa principal. En el subprograma, la eventual modificacion del valor de las variables globales es eficaz solo hasta la salida del mismo.
Tambien en este caso, el metodo vale para todos los niveles de animacion de los subprogramas (o de las macros): una variable local de un subprograma se hace global para todos sus subprogramas y asi sucesivamente.
Las variables globales al mas alto nivel son las definidas en el archivo de las variables ambiente. El nombre de este archivo, que es un programa que contiene solo algunas definiciones de variables (vease instruccion L ), debe ser declarado en el Encabezamiento de un programa.
3) Programacion de variables globales con retorno del valor al solicitante.
Un programa principal dispone de un array (vector) de 128 valores variables visibles y modificables incluso dentro de todos los subprogramas y macros solicitados.
```

### `"local variables" / "local variable" — PARECIDO, NO IDENTICO`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:\Users\fermi\AppData\Local\Temp\claude\c--Dev-Repositorios-ProdAction\2b4a4df7-b886-481a-99e7-9a86bef428d6\scratchpad\out_editor_ing\6.4_Passing_Parameters_to_Subprograms_and_Macros.htm`
  ·  **Sección:** 6.4 Passing Parameters to Subprograms and Macros — version inglesa del mismo apartado
  ·  **Idioma:** ingles

```
El mismo pasaje existe en la version inglesa del capitulo 6.4, con las expresiones "local variables" y "local variable" (una aparicion de cada una). Es el unico lugar de las cuatro ayudas CHM donde figura una expresion del tipo "variable local"; NO usa en ningun momento la notacion VL ni VLn.
```

**No aparece en ninguna fuente:** `VL6 en documentacion: NO APARECE. No figura en out_spa (45 .htm), out_editor_ing (46 .htm), out_epl (40 .htm), out_panelmac (63 .htm), maestro_editor_es.txt, pgmx/docs/xilog_plus_pgm/ ni pgmx/docs/maestro_scripting/. Solo aparece como codigo en 5 archivos .iso y como cadena en 1 .dll.`, `VL7 en documentacion: NO APARECE. Mismo alcance de busqueda y mismo resultado que VL6.`, `La familia "VLn" o "variables VL" como concepto nombrado: NO APARECE en ninguna de las 8 fuentes. No hay tabla, lista, indice ni glosario que enumere una familia VL.`, `El rango de las variables VL (cuantas hay, de VL0 a VLn, valores admitidos): NO APARECE en ninguna fuente. No existe ninguna declaracion de rango.`, `VL0, VL1, VL2, VL3, VL4, VL5, VL8, VL9: NO APARECEN en ninguna fuente. El escaneo de toda la instalacion C:\Program Files (x86)\Scm Group\ (excluyendo imagenes) devolvio unicamente dos tokens distintos: VL6 (29 apariciones) y VL7 (29 apariciones).`, `"VL" suelto (como sigla, sin numero): NO APARECE. La busqueda de \bVL\b en toda la instalacion SCM Group y en las cuatro ayudas CHM no devolvio nada.`, `Variantes de escritura %VL, [VL, VL[, VL con espacio (VL 6), minusculas (vl6): NO APARECEN en ninguna fuente. Los unicos aciertos en minusculas o mezcladas (vL2, Vl7, VL6...) estan dentro de archivos .jpg y .gif, es decir bytes aleatorios de imagenes comprimidas, no texto.`, `VL en archivos de configuracion de la instalacion (.cfg, .ini, .xml, .tlgx, .pgm, .pgmx) y en los 142 .txt sueltos: NO APARECE. Se verifico que los 142 .txt existen y son legibles (13 de ellos contienen 'G0'), pero ninguno menciona VL.`, `SVL y SVR (las instrucciones que acompanan a VL6 y VL7 en los .iso): NO APARECEN en ninguna de las cuatro ayudas CHM. Se anotan aqui solo porque forman parte de las citas transcriptas; no fueron pedidas en esta familia.`

## header H

### `H (instrucción de cabecera) — DEFINICIÓN COMPLETA, español`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.1_Encabezamiento.htm`
  ·  **Sección:** 5.1 Encabezamiento
  ·  **Idioma:** español

```
5.1 Encabezamiento

H (Encabezamiento, o Header)

El encabezamiento describe el tablero. Es la primera instrucción (obligatoria) de un programa.

Parámetros básicos:

DX — Dimensión en X del tablero (longitud).
DY — Dimensión en Y del tablero (ancho).
DZ — Dimensión en Z del tablero (espesor).
/ — Nombre del archivo con los datos de equipamiento.
- — Área de trabajo en la que debe ejecutarse el programa. Valores admitidos: A, B, C, D, AB, BA, CD, DC, AD, DA.

NOTA. Si se introducen los valores 0, 0 ,0 en los campos de los parámetros DX ,DY ,DZ respectivamente, el programa se reconoce automáticamente como macro.

Parámetros completos:

* — Unidad de medida. Los valores admitidos son MM (milímetros) e IN (pulgadas); si el campo se omite, vale la unidad programada en los parámetros de la máquina.
# — Nombre del archivo con las variables ambiente.
C — Tipo de elaboración; los valores admitidos son 0 para la elaboración normal y 1 para la elaboración continua.
V — Habilita / inhabilita el bloqueo de la pieza y el control de la posición de las ventosas automáticas (si hay) según las tabla: [tabla completa citada aparte]
T — Habilita/inhabilita los elevadores (si hay) y las luces láser para el posicionamiento de la pieza (si hay) según la tabla siguiente: [tabla completa citada aparte]
R — Número de tableros iguales a producir (máx. 9999).
BX — Distancia en X del cero del tablero con respecto al cero del campo.
BY — Distancia en Y del cero del tablero con respecto al cero del campo.
BZ — Dimensión en Z de un posible espesor situado debajo del tablero.

La programación de los parámetros V y T se facilita por las tablas correspondientes, como mencionado previamente.

¡ATENCIÓN!
La dimensión en Z del tablero se utiliza para optimizar las traslaciones de los cabezales entre trabajos realizados en caras distintas; por lo tanto, es indispensable que en el campo DZ se introduzca la dimensión máxima efectiva en Z de la pieza; en caso contrario pueden ocurrir peligrosos choques entre los cabezales y la pieza.
```

### `H (instrucción de cabecera) — DEFINICIÓN COMPLETA, inglés`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/5.1_Header.htm`
  ·  **Sección:** 5.1 Header
  ·  **Idioma:** inglés

```
5.1 Header

H (Header)

The header describes the panel. It is the first instruction (mandatory) of a program.

Basic parameters:

DX — Panel X dimension (length).
DY — Panel Y dimension (width).
DZ — Panel Z dimension (thickness).
/ — Name of tooling-up configuration file.
- — Machining area on which the program must be executed. The maximum values are: A, B, C, D, AB, BA, CD, DC, AD, DA.

NOTE. If values 0, 0, 0 are entered respectively for parameters DX, DY, DZ, the program is automatically recognized as a macro.

Extended parameters:

* — Unit of measure. The allowed values are MM (millimeters) ad IN (inches); if the field is omitted, the unit of measures specified in the machine parameters will be used.
# — Name of environment variables file.
C — Machining type. The permitted values are 0 for normal machining and 1 for uninterrupted machining.
V — Activates / deactivates the clamping of the piece and the position control of the automatic suction cups, if present, according to the table below:
T — Enables/disables lifters (if present) and laser lights for positions the piece (if present) according to the following table:
R — Number of identical panels to produce (max. 9999).
BX — Distance in X between the panel zero and the field zero.
BY — Distance in Y between the panel zero and the field zero.
BZ — Dimension in Z of a shim positioned under the panel.

WARNING
The panel dimension in Z is used to optimize translation of head between machining on different surfaces. For this reason the DZ field must be compiled with the effective maximum overall dimensions of the piece in Z, otherwise the heads and the piece may collide.
```

### `BX / BY / BZ (campos de la instrucción H) — español`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.1_Encabezamiento.htm`
  ·  **Sección:** 5.1 Encabezamiento — Parámetros completos
  ·  **Idioma:** español

```
BX
Distancia en X del cero del tablero con respecto al cero del campo.

BY
Distancia en Y del cero del tablero con respecto al cero del campo.

BZ
Dimensión en Z de un posible espesor situado debajo del tablero.
```

### `BX / BY / BZ (campos de la instrucción H) — inglés`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/5.1_Header.htm`
  ·  **Sección:** 5.1 Header — Extended parameters
  ·  **Idioma:** inglés

```
BX
Distance in X between the panel zero and the field zero.

BY
Distance in Y between the panel zero and the field zero.

BZ
Dimension in Z of a shim positioned under the panel.
```

### `BX / BY / BZ (como VARIABLES PREDEFINIDAS de lectura) — español, con el texto en italiano SIN TRADUCIR`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (líneas 3281-3305; este archivo contiene además los APÉNDICES)`
  ·  **Sección:** APÉNDICE B. Variables y expresiones — Variables
  ·  **Idioma:** español (las tres definiciones quedaron en italiano)

```
Existen algunas variables predefinidas que se pueden utilizar para leer las dimensiones de la pieza, el área de trabajo y representar pi (estas variables no se pueden escribir):

DX — Dimensión en X.
DY — Dimensión en Y.
DZ — Dimensión en Z.
BX — Traslazione in X del pezzo rispetto alla battuta.
BY — Traslazione in Y del pezzo rispetto alla battuta.
BZ — Traslazione in Z del pezzo rispetto alla battuta.
FLD — Área de trabajo:
  1=A, 2=B, 3=C, 4=D
  12=AB, 21=BA, .., 41=DA
  101=E, 102=F, 103=G, 104=H
  112=EF, 121=FE, ..., 141=HE
  201=I, 202=J, 203=K, 204=L
  212=IJ, 221=JI, ..., 241=LI
  301=M, 302=N, 303=O, 304=P
  312=MN, 321=NM, ..., 341=PM
  900 = area 00, 901 = area 01
  910 = area 10, 911 = area 11
PI — Pi-greco.
```

### `BX / BY / BZ (como VARIABLES PREDEFINIDAS de lectura) — inglés`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/_APPENDIX.htm (líneas 2849-2960)`
  ·  **Sección:** APPENDIX B. Variables and Expressions — Variables
  ·  **Idioma:** inglés

```
Some variables are reserved and can be used to read the dimensions of the piece, the work area, and represent pi (these variables cannot be written):

DX — Dimension in X.
DY — Dimension in Y.
DZ — Dimension in Z.
BX — Workpiece movement in X relative to the stop.
BY — Workpiece movement in Y relative to the stop.
BZ — Workpiece movement in Z relative to the stop.
FLD — Machining area:
  1=A, 2=B, 3=C, 4=D
  12=AB, 21=BA, .., 41=DA
  101=E, 102=F, 103=G, 104=H
  112=EF, 121=FE, ..., 141=HE
  201=I, 202=J, 203=K, 204=L
  212=IJ, 221=JI, ..., 241=LI
  301=M, 302=N, 303=O, 304=P
  312=MN, 321=NM, ..., 341=PM
  900 = area 00, 901 = area 01
  910 = area 10, 911 = area 11
PI — Pi-greco.
```

### `V (campo del header) — TABLA COMPLETA de valores, español`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.1_Encabezamiento.htm`
  ·  **Sección:** 5.1 Encabezamiento — Parámetros completos, campo V
  ·  **Idioma:** español

```
V
Habilita / inhabilita el bloqueo de la pieza y el control de la posición de las ventosas automáticas (si hay) según las tabla:

Campo V | Bloqueo | Control Dispositivos en automático | Bloqueo dispositivos motorizados

Vacío | Sí, utilizando el sistema configurado con xilog3.cfg; si están previstos vacuómetros y presostatos, se habilitan los primeros | Sí | Automático
0 | Mecánico | No | No utilizado
1 | Mecánico | Sí | No utilizado
10 | Sí, utilizando los vacuómetros | No | Manual
20 | Sí, utilizando los presostatos | No | Manual
11 | Sí, utilizando vacuómetros | Sí | Automático
21 | Sí, utilizando los presostatos | Sí | Automático
12 | Sí, utilizando los vacuómetros | Sí | Semiautomático
22 | Sí, utilizando los presostatos | Sí | Semiautomático
30 | Sí, utilizando presostatos y vacuómetros | No | Manual
31 | Sí, utilizando presostatos y vacuómetros | Sí | Automático
40 | Equipamiento (dispositivos de bloqueo mecánico epeciales) | No | Manual
50 | Default | Depende del sistema configurado con Xilog3.cfg como default |
51 | DUOMATIC anteriores | No | Semiautomático
52 | DUOMATIC posteriores | No | Semiautomático
53 | DUOMATIC ant. + post. | No | Semiautomático
60 | Bornes Horizontales (para Marcos) | No | Manual
61 | Bornes Horizontales (para Marcos) | Si | Automático
62 | Bornes Horizontales (para Marcos) | Si | Semiautomático
100 – 153 (para Ergon) | Como en los casos 0 – 53 con combinación 1 de las sub-áreas de vacío | Como en los casos 0 – 53 Sub-área: 1 | Como en los casos 0 – 53 Sub-área: 1
200 – 253 (para Ergon) | Como en los casos 0 – 53 con combinación 2 de las sub-áreas de vacío | Como en los casos 0 – 53 Sub-área: 2 | Como en los casos 0 – 53 Sub-área: 2
300 – 353 (para Ergon) | Como en los casos 0 – 53 con combinación 3 de las sub-áreas de vacío | Como en los casos 0 – 53 Sub-área: 3 | Como en los casos 0 – 53 Sub-área: 3
400 – 453 (para Ergon) | Como en los casos 0 – 53 con combinación 4 de las sub-áreas de vacío | Como en los casos 0 – 53 Sub-área: 12 | Como en los casos 0 – 53 Sub-área: 12
500 – 553 (para Ergon) | Como en los casos 0 – 53 con combinación 5 de las sub-áreas de vacío | Como en los casos 0 – 53 Sub-área: 13 | Como en los casos 0 – 53 Sub-área: 13
600 – 653 (para Ergon) | Como en los casos 0 – 53 con combinación 6 de las sub-áreas de vacío | Como en los casos 0 – 53 Sub-área: 23 | Como en los casos 0 – 53 Sub-área: 23

NOTA 1: en caso de planos no motorizados, sino dotados de visualizadores con retrofit hacia Xilog Plus (es.: SIKO), el control automático de los apoyos se realiza comprobando, en el inicio programa pieza, las cotas señalizadas por los visualizadores (post posicionamiento manual del operador) con aquellas programadas. Si no hay visualizadores con dicha característica, la selección de V para el control manual o automático es irrelevante.

NOTA 2: para detalles acerca de los dispositivos DUOMATIC, remitirse al Apéndice I
```

### `V (campo del header) — TABLA COMPLETA de valores, inglés`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/5.1_Header.htm`
  ·  **Sección:** 5.1 Header — Extended parameters, field V
  ·  **Idioma:** inglés

```
V
Activates / deactivates the clamping of the piece and the position control of the automatic suction cups, if present, according to the table below:

Area V | Blockage | Automatic control device | Motorised blocking device

Empty | If, using the configured system in xilog3.cfg; if the use of vacuum switches or pressare switches are foreseen, they should be enables first | Yes | Automatic
0 | Mechanic | No | Not used
1 | Mechanic | Yes | Not used
10 | If using vacuum switches | No | Manual
20 | If using pressure switches | No | Manual
11 | If using vacuum switches | Yes | Automatic
21 | If using pressure switches | Yes | Automatic
12 | If using vacuum switches | Yes | Semiautomatic
22 | If using pressare switches | Yes | Semiautomatic
30 | If using pressare and vacuum switches | No | Manual
31 | If using pressare and vacuum switches | Yes | Automatic
40 | Equipment (special mechanical blocking devices) | No | Manual
50 | Default | Depends on the system configured in Xilog3.cfg as default |
51 | DUOMATIC front | No | Semiautomatic
52 | DUOMATIC rear | No | Semiautomatic
53 | DUOMATIC ant. + post. | No | Semiautomatic
60 | Horizontal Clamps (for Jamps) | No | Manual
61 | Horizontal Clamps (for Jamps) | Yes | Automatic
62 | Horizontal Clamps (for Jamps) | Yes | Semiautomatic
100 – 153 (for Ergon) | As in cases 0 – 53 with combination 1 of the empty subareas | As in cases 0 – 53 Subarea: 1 | As in cases 0 – 53 Subarea: 1
200 – 253 (for Ergon) | As in cases 0 – 53 with combination 2 of the empty subareas | As in cases 0 – 53 Subarea: 2 | As in cases 0 – 53 Subarea: 2
300 – 353 (for Ergon) | As in cases 0 – 53 with combination 3 of the empty subareas | As in cases 0 – 53 Subarea: 3 | As in cases 0 – 53 Subarea: 3
400 – 453 (for Ergon) | As in cases 0 – 53 with combination 4 of the empty subareas | As in cases 0 – 53 Subarea: 12 | As in cases 0 – 53 Subarea: 12
500 – 553 (for Ergon) | As in cases 0 – 53 with combination 5 of the empty subareas | As in cases 0 – 53 Subarea: 13 | As in cases 0 – 53 Subarea: 13
600 – 653 (for Ergon) | As in cases 0 – 53 with combination 6 of the empty subareas | As in cases 0 – 53 Subarea: 23 | As in cases 0 – 53 Subarea: 23
```

### `V (campo del header) — página dedicada, español`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.3_Campo_V_del_HEADER(encabezamiento)_programa.htm`
  ·  **Sección:** 9.3 Campo V del HEADER(encabezamiento) programa
  ·  **Idioma:** español

```
9.3 Campo V del HEADER(encabezamiento) programa

El campo V, que se encuentra en el encabezamiento (header) del programa, permite especificar el tipo de preparación del plano. El comportamiento operativo de la máquina varía en función de los valores previstos, así como los controles realizados por Xilog Plus en la programación de las PB.

Bornes estándares con vástago o platillo
El estado de los bornes estándares es: abierto (=1), cerrado (=0) y cerrado con pieza en toma (=2).
A continuación se muestran en detalle las características de cada valor del campo V:
1. V = 20: bloqueo manual. Durante la preparación manual Xilog Plus no genera mandos de posicionamiento ni controles de posición para los motores asociados con las barras y los bornes. En este caso el operador realiza el posicionamiento de los dispositivos manualmente
2. V = 21: bloqueo automático. Durante la preparación automática el sistema administra las posiciones y los controles de las barras y de los bornes. Después de haber lanzado el programa desde el panel máquina, el operador presiona el pulsador de set up plano
  a. primera presión: el sistema ejecuta y completa la fase de preparación plano. Se ejecuta el programa PGM hasta el bloque de PB con E = 1. Al finalizar la operación, el operador carga la pieza en la máquina
  b. segunda presión: el sistema ejecuta y completa la fase de bloqueo pieza. Se ejecuta el programa PGM hasta el bloque de PB con E = 2 y, si está presente, hasta el bloque de PB con E = 3 contiguo al precedente
  c. tercera presión: el sistema bloquea los bornes en alta presión e inicia la ejecución del programa PMG
3. V = 22: bloqueo semiautomático. Durante la preparación semiautomática el sistema administra las posiciones y los controles de las barras y bornes. Tras lanzar el programa desde panel máquina el operador presiona la tecla de set up plano
  a. primera presión: el sistema ejecuta y completa la fase de preparación plano. Se ejecuta el programa PGM hasta el bloque de PB con E = 1. Al finalizar la preparación, el operador carga la pieza en la máquina y bloquea en manual la pieza accionando los selectores ubicados en la máquina. Los bornes se cierran en presión baja. Es necesario que el bloque de PB con E = 2 sea presente en el programa con las mismas cotas del bloque con E = 1
  b. segunda presión: el sistema bloquea los bornes en alta presión e inicia la ejecución del programa PMG. Los bloques de PB con E = 3 son administrados de la misma manera de la preparación automática

Bornes horizontales para trabajos marcos
A diferencia de los bornes estándares, los estados de los bornes están abierto (=1) y cerrado (=0). Bloques de PB con E = 2 o E = 3 generan un error de programación.
1. V = 60: bloqueo manual. Durante la preparación manual Xilog Plus no genera mandos de posicionamiento ni controles de posición para los motores asociados da Xilog Plus a las barras y a los bornes. En este caso el operador posiciona los dispositivos manualmente
2. V = 61: bloqueo automático. Durante la preparación automática el sistema administra el posicionamiento y los controles de las barras y de los bornes. Después de haber lanzado el programa desde panel máquina, el operador presiona el pulsador de set up plano
  a. primera presión: el sistema ejecuta y completa la fase de preparación plano. Se ejecuta el programa PGM hasta el bloque de PB con E = 1. En cuanto termina el operado posiciona los bornes acercándolos a los topes mecánicos
  b. segunda presión: el sistema controla la correcta posición de todos los dispositivos. El operador carga la pieza en la máquina y bloquea en manual la pieza accionando los selectores ubicados en la máquina
  c. tercera presión: el sistema bloquea los bornes en alta presión e inicia a ejecutar el programa PMG
3. V = 62: bloqueo semiautomático. El sistema se comporta de la misma manera del precedente

Ventosas
A diferencia de los bornes, los estados de las ventosas no son significativos. Bloques de PB con E = 2 o E = 3 generan un error de programación.
1. V = 10: bloqueo manual. Durante la preparación manual Xilog Plus no genera mandos de posicionamiento ni controles de posición para los motores asociados a las barras y a las ventosas. En este caso el operador posiciona los dispositivos manualmente
2. V = 11: bloqueo automático. No admitido. El sistema restituye el error
3. V = 12: bloqueo semiautomático. Durante la preparación semiautomática el sistema administra el posicionamiento y los controles de las barras y ventosas. Tras haber lanzado el programa desde el panel máquina, el operador presiona el pulsador de set up plano
  a. primera presión: el sistema ejecuta y completa la fase de preparación plano. Se ejecuta el programa PGM hasta el bloque de PB con E = 1. Al finalizar la preparación, el operador carga la pieza en la máquina y bloquea en manual la pieza accionando los selectores ubicados en la máquina. Se activa el vacío.
  b. segunda presión: el sistema inicia la ejecución del programa PMG.
```

### `V (campo del header) — página dedicada, inglés`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_editor_ing/9.3_Field_V_of_the_HEADER_program.htm`
  ·  **Sección:** 9.3 Field V of the HEADER program
  ·  **Idioma:** inglés

```
9.3 Field V of the HEADER program

Field V, present in the header of the program, specifies the type of surface preparation. When functioning with the foreseen values, the operative behaviour of the machine varies and likewise the controls carried out by Xilog Plus on the programming of the PB.

Standard clamps with bar or plate
The state of the standard clamps are: open (=1), closed (=0) and closed with piece grip (=2).
The detailed features of the value in field V are:
1. V = 20: manual blocking During manual preparation the Xilog Plus, the positioning commands, the position controls for the motors associated to the bars and the clamps are not generated. In this case the operator positions the devices manually.
2. V = 21: automatic blocking. During automatic preparation, the system positions and controls the bars and clamps.
```

### `V = 40 (equipo del cliente)`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (línea 7733; el archivo contiene los apéndices)`
  ·  **Sección:** APÉNDICE J. Gestión del equipo del cliente
  ·  **Idioma:** español

```
APÉNDICE J. Gestión del equipo del cliente

Antes de activar o desactivar el equipo es obligatorio iniciar a partir de una condición de reposo en todas las zonas de la mesa de trabajo. Es posible efectuar un trabajo pendular pero no es posible manejar el equipo junto con otros sistemas de bloqueo.

Con Xilog Plus:
Para activar la gestión del equipo, hay que introducir en el campo V del encabezamiento V=40.
```

### `T (campo del header) — TABLA de valores y ventana de diálogo, español`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.1_Encabezamiento.htm`
  ·  **Sección:** 5.1 Encabezamiento — Parámetros completos, campo T
  ·  **Idioma:** español

```
T
Habilita/inhabilita los elevadores (si hay) y las luces láser para el posicionamiento de la pieza (si hay) según la tabla siguiente:

Campo T | Luces láser | Elevadores | TV Bar
0 | No | No | OFF
1 | No | Sí | OFF
10 | Sí | No | OFF
11 | Sí | Sí | OFF
100 | No | No | ON
101 | No | Sí | ON
110 | Sí | No | ON
111 | Sí | Sí | ON

Más en general, la parametrización de dicho campo puede realizarse, de manera más simple y extensa, a través de la ventana de diálogo dedicada:

Descripción de cada voz:
Láser — Solicitud uso de la luz láser para el posicionamiento de la pieza
Elevadores — Solicitud uso de los elevadores auxiliares para cargar la pieza
Barra móvil — Solicitud de posicionamiento de la barra móvil del área de trabajo master (si configurada con Fields.cfg)
Fila 1 de topes — Solicitud uso de los topes de la fila número 1 (si presentes)
Fila 2 de topes — Solicitud uso de los topes de la fila número 2 (si presentes)
Fila 3 de topes — Solicitud uso de los topes de la fila número 3 (si presentes)
Fila 4 de topes — Solicitud uso de los topes de la fila número 4 (si presentes)
Fila 5 de topes — Solicitud uso de los topes de la fila número 5 (si presentes)
Áreas asociadas — Solicitud combinación áreas de trabajo acerca de la gestión del vacío (si las áreas están asociadas, la solicitud de vacío desde el selector de una cierta área acciona el vacío también en la otra área eventualmente asociada)
Verificación posición ventosas — Vale para plano automático Easyset Morbidelli: solicitud de verificación del posicionamiento de las ventosas al final de la fase de setup
Desactiva C.U. mascarado — Vale para aplicaciones especiales: solicitud de desactivación del cambio herramienta mascarado. Nota: el uso de este campo ha sido superado con la introducción del parámetro “Cambio herramienta mascarado no admitido” asociado con cada herramienta.
Adquisición BZ y DZ de palpadura — Solicitud de adquisición de los datos de altura pieza (DZ) y colocación (BZ) desde los valores derivados de las operaciones de palpadura en modalidad MDI (véase §4.5.2 del manual del Panel Máquina: Palpador).
Barra móvil área asociada — Solicitud de posicionamiento de la barra móvil del área de trabajo asociada (si configurada con Fields.cfg)
Habilitación elevadores doble carrera — Solicitud uso de los elevadores auxiliares para cargar la pieza en modalidad “doble carrera”. Nota: actualmente inefectivo ya que implementada solución hardware dedicada.

La tabla del parámetro T permite también habilitar/inhabilitar:
• todos los ficheros de tope (la principal más los posibles topes secundarios) relativos al área especificada en el programa;
• la combinación de las áreas;
• el control de la posición de las ventosas para las mesas travesaños y ventosas motorizadas;
• el cambio herramienta encubierto.
• Palpador automático para máquina UNIX
• Optimación programa (véase punto 5.1)
• Optimación PAV (véase punto 8.7.4)
• Optimación pinzas para máquina UNIX
```

### `BZ y DZ adquiridos por palpadura (5.1.1)`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.1_Encabezamiento.htm`
  ·  **Sección:** 5.1.1 Palpación panel y “martire”
  ·  **Idioma:** español

```
5.1.1 Palpación panel y “martire”

La presencia de un dispositivo de palpación montado en la cabeza, permite realizar dos operaciones específicas, en ámbito MDI (véase §4.5.2 del manual del Panel Máquina: Palpador), para la medición del panel y del “martire”(panel de soporte al panel en elaboración). En este contexto, es posible solicitar que los valores de los campos BZ y DZ del Header sean adquiridos al cargar el programa automáticamente, directamente desde la máquina. Esto es posible configurando en “SI” el campo “T→Adquisición BZ y DZ desde palpación” y configurando en “1” el parámetro de configuración “Axis→GEN 2→Adquisición datos de palpación” o configurando en “2” este último parámetro (en dicho caso es irrelevante la programación del campo T).
```

### `Ejemplos literales de la línea H en el manual (con *MM, C=, T=, R=, V, y el guión seguido del área)`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm (línea 382); out_spa/6.3_Macros.htm (líneas 140 y 438); out_spa/7._Optimizador_de_programas.htm; out_spa/5.4_Macros_usuario.htm; out_editor_ing/_APPENDIX.htm (líneas 5623, 6231, 6268, 7089)`
  ·  **Sección:** 5.2 Instrucciones básicas (texto) / 6.3 Macros / 7. Optimizador / APPENDIX F Ergon
  ·  **Idioma:** español e inglés

```
H DX=600 DY=400 DZ=30 -A C=0 T=0 R=1 *MM /”ANDREA” V10;encabezamiento

H DX=450 DY=300 DZ=20 -A C=0 T=0 R=1 *MM /“test”

H DX=400 DY=250 DZ=20 -A C=0 T=0 R=1 *MM /“ROUTE”

H DX=450 DY=450 DZ=50 -A R=1 *MM

H DX0 DY0 DZ0 *MM /"9p,XYZDT,0,PUERTA TIPO 08"

H DX=… DY=… DZ=… BX=… BY=… BZ=… /“Def“

H DX=1000 DY=1000 DZ=50 BX=0 BY=0 BZ=0 /“Def”

(H DX=… DY=… DZ=… -AB C=0 T=0 R=99 … V=53)

H DX=1500 DY=1000 -AB
```

### `El guión “-” seguido del área — lista de áreas y zonas donde aparece HG`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/4.4_Programa_m_ltiple.htm (líneas 622, 657, 785)`
  ·  **Sección:** 4.4.2 Subdivisión de la superficie en zonas de trabajo / 4.4.3 Ejemplos
  ·  **Idioma:** español

```
4.4.2 Subdivisión de la superficie en zonas de trabajo

Máquinas con cero central
Zona 1 — Áreas A/E/I/M
Zona 2 — Áreas B/F/J/N
Zona 3 — Áreas C/G/K/O
Zona 4 — Áreas D/H/L/P
Zona 1 e 2 — Áreas AB/BA/EF/FE/IJ/JI/MN/NM
Zona 3 e 4 — Áreas CD/DC/GH/HG/KL/LK/OP/PO
Zonas 1 - 4 — Áreas AD/DA/EH/HE/IL/LI/MP/PM

Máquinas con cero central virtual
Zona 1 — Áreas AB/BA/EF/FE/IJ/JI/MN/NM
Zona 2 — Áreas CD/DC/GH/HG/KL/LK/OP/PO
Zonas 1 - 2 — Áreas AD/DA/EH/HE/IL/LI/MP/PM

Máquinas sin cero central
Zona 1 — Áreas A/E/I/M
Zona 2 — Áreas B/F/J/N
Zonas 1 - 2 — Áreas AB/BA/EF/FE/IJ/JI/MN/NM

[4.4.3 Ejemplos]
Si efectuado en área AB o BA (o bien EF o FE), el programa efectuará los subprogramas, según el orden de las instrucciones SO, en las áreas: A, E, B y F.
Si efectuado en área CD o DC (o bien GH o HG) el programa efectuará los subprogramas en las áreas: C, G, D, H.
```

### `Áreas de trabajo A/B/C/D y sus especulares E/F/G/H (contexto del campo “-” de H)`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/4.2_Programa.htm`
  ·  **Sección:** 4.2.1.4 Areas de trabajo
  ·  **Idioma:** español

```
4.2.1.4 Areas de trabajo

Cada programa se lanza dentro de un área de trabajo. La mesa de trabajo está dividida ordinariamente en 4 áreas (A, B, C, D).
Cada área tiene un origen propio de los ejes, orientado según el origen máquina.
En las mesas con cero central y cuatro topes móviles (uno a la izquierda, uno a la derecha y dos centrales), la presencia de los topes móviles centrales permite programar cada uno de los trabajos independientemente en las cuatro áreas. Además, las áreas pueden ser utilizadas también en pares: por ejemplo, si el tablero a trabajar tiene dimensiones que ocupan dos áreas, se puede utilizar en fase de programaciún un área doble, como el área AB (con origen de los ejes en A)... o BA (con origen de los ejes en B).
En las mesas sin cero central (sin topes móviles centrales) la presencia de los topes sólo en los extremos izquierdo y derecho de la mesa de trabajo permite utilizar sólo las áreas AB y DC. En este caso, no es posible plantear el programa de trabajo en las áreas B, C, BA y CD, mientras el planteo de las áreas A y D es considerado automáticamente por Xilog Plus equivalente, respectivamente, a las áreas AB y DC..

ATENCION!
Para las máquinas no equipadas con CNC OSAI vale la configuración siguiente: área izquierda=A; área derecha=B.

La mesa puede confirugarse también con áreas especulares: por ejemplo, respecto de las áreas A, B, C, D arriba detalladas se pueden tener a disposición en la mesa de trabajo las respectivas áreas especulares E, F, G, H.

Para plantear el área de trabajo de un programa véase: instrucción H.
```

### `HG entre las “zonas virtuales” (apéndice)`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm (línea 5628) y out_editor_ing/_APPENDIX.htm (línea 5257)`
  ·  **Sección:** APÉNDICE (control de topes TV) — “Con zonas virtuales” / “With virtual areas”
  ·  **Idioma:** español e inglés

```
[ES] Con zonas virtuales (AB, CD, BA, DC, AD, DA; EF, GH, FE, HG, EH, HE;...)
Análogo a las zonas estándar, pero en este caso son siempre zonas combinadas.

[EN] With virtual areas (AB, CD, BA, DC, AD, DA; EF, GH, FE, HG, EH, HE;...)
The same as described for standard areas, with the difference that the areas are always in pairs.
```

### `HG y barra móvil (campo T del Header)`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_epl/8.4_Gesti_n_autom_tica_de_la_barra_m_vil.htm`
  ·  **Sección:** 8.4 Gestión automática de la barra móvil (ayuda EPL)
  ·  **Idioma:** español

```
La gestión automática permite desplazar la barra móvil entre la posición OFF y la posición ON en dos modalidades:
A) posición OFF o bien posición ON.
B) desplazamiento en continuo entre la posición OFF y la posición ON (sólo para las barras centrales en superficies configuradas con áreas dobles del exterior al interior; por ejemplo, las superficies AB, DC, EF, HG etc.).

► Posición OFF o ON.
La posición OFF o ON puede programarse con el parámetro BARRA MOVIL del campo T del Header. En posición OFF (default) la barra móvil está posicionada en la extremidad externa de la superficie de trabajo; en posición ON la barra móvil regresa hacia el interior de la superficie de trabajo.
```

### `P (instrucción de MIX) — repite los mismos campos que H, incluidos BX BY BZ`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/4.3_Mix_de_programas.htm`
  ·  **Sección:** 4.3 Mix de programas — Parámetros
  ·  **Idioma:** español

```
El mix permite crear un archivo para ejecutar en secuencia una lista de programas ya preparados. Las instrucciones de un mix empiezan con la letra P y están formados por el nombre y el encabezamiento de los programas que se van a ejecutar.

Parámetros:
/ — Nombre del programa.
DX — Dimensión en X del tablero.
DY — Dimensión en Y del tablero.
DZ — Dimensión en Z del tablero.
- — Área de trabajo sobre la que se debe ejecutar el programa; los valores admitidos son A, B, C, D, AB, BA, CD, DC, AD, DA.
R — Número de tableros iguales a producir (máx. 9999).
* — Unidad de medida; los valores admitidos son MM (milímetros) e IN (pulgadas); si el campo se omite, vale la unidad de medida especificada en los parámetros de la máquina.
/ — Nombre del archivo con los datos de equipamiento.
# — Nombre del archivo con las variables ambiente.
BX — Distancia en X del cero del tablero con respecto al cero del campo.
BY — Distancia en Y del cero del tablero con respecto al cero del campo.
BZ — Dimensión en Z de un posible espesor situado debajo del tablero.
(vacía) — Campo para introducir los parámetros (PAR) del programa.
C — Tipo de trabajo. Valores admitidos: 0 para trabajo normal, 1 para trabajo continuo
T — Opciones mecánicas (véase §5.1 – instrucción H)
V — Habilita / inhabilita el bloqueo de la pieza y el control en la posición de las ventosas automáticas (si están presentes). Equivalente al campo V de la instrucción H (véase §5.1 – instrucción H)

Ejemplo:
H DX1000 DY500 DZ20 -AB R10 *MM /DEF
```

### `SO (subprograma optimizado) — usa BX BY BZ con la misma redacción que el header`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm (líneas 6260-6415)`
  ·  **Sección:** 5.2 Instrucciones básicas (texto) — Subprograma optimizado - SO
  ·  **Idioma:** español

```
Subprograma optimizado - SO

La instrucción SO permite llamar un subprograma asociándolo a una zona de trabajo; asimismo, durante la ejecución se mantienen las dimensiones reales de la pieza y, por lo tanto, las posiciones de sus caras.

Parámetros:
/ — Nombre del subprograma.
DX — Dimensión en X del tablero.
DY — Dimensión en Y del tablero.
DZ — Dimensión en Z del tablero.
FLD — Área de trabajo a la que se debe asociar (A, B, C, D, AB, BA, CD, DC, AD, DA).
BX — Distancia en X del cero del tablero con respecto al cero del campo.
BY — Distancia en Y del cero del tablero con respecto al cero del campo.
BZ — Dimensión en Z de un posible espesor situado debajo del tablero.

Excepto el nombre del subprograma, todos los demás parámetros son opcionales; si existen, los parámetros opcionales sustituyen a los correspondientes programados en el Encabezamiento (header) del subprograma.

· Las instrucciones SO sólo se pueden solicitar dentro del programa principal. La instrucción SO define las características de un tablero que se convierte en un espesor del tablero principal definido en el Encabezamiento (header) del programa principal; este último define las características del trabajo total (incluido el bloqueo de las piezas), y por lo tanto las dimensiones DX, DY y DZ que en él se especifican deberían contener todos los espesores.
· La dimensión en Z del panel se utiliza para optimizar las traslaciones de los cabezales entre trabajos realizados en caras distintas; por lo tanto, es indispensable que en el campo DZ se introduzca la dimensión máxima efectiva en Z de la pieza; en caso contrario pueden ocurrir peligrosos choques entre los cabezales y la pieza.
· Para llamar un programa que contiene una superficie inclinada (instrucciones PL/XPL) es preciso asignar a los parámetros BX, BY, BZ los valores X, Y, Z del origen de la superficie inclinada.
· Un trabajo SO se realiza a partir del tope del área de trabajo especificada en SO.
```

### `El Encabezamiento como primera instrucción del programa`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/4.2_Programa.htm`
  ·  **Sección:** 4.2.1.1 Estructura de un programa
  ·  **Idioma:** español

```
4.2.1.1 Estructura de un programa

El programa consiste en una secuencia de instrucciones que describe un ciclo de trabajos en el panel. Dicho ciclo se memoriza en un archivo binario en el formato principal PGM y se traduce al lenguaje ISO en el momento de su ejecución en la máquina.

La primera instrucción de todos los programas debe ser el Encabezamiento (o Header), seguida del resto de instrucciones (perfiles, perforación y movimientos).
```

### `“;” (carácter de comentario) — parecido a “;H”, NO idéntico`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm (línea 6812)`
  ·  **Sección:** 5.2.6 Instrucciones de ayuda a la programación — Comentario - ;
  ·  **Idioma:** español

```
Comentario - ;

Un comentario es una línea de texto que comienza con el carácter; o bien con el carácter *. Comentarios que inician con; pueden ponerse también al fondo de las otras instrucciones.

Grupo: instrucciones texto

[NOTA DEL RELEVAMIENTO: esto documenta el carácter “;” como comentario. NO documenta la secuencia “;H”. Se trae marcado como parecido, no idéntico.]
```

### `;H (literal) — aparece en archivos .iso reales de la instalación, NO en los manuales`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/prubafresas.iso ; …/rebaje laterales.iso ; …/pieza 300x300 calxy.iso ; …/lado_izquierdo1.iso ; …/lado_derecho1.iso`
  ·  **Sección:** Línea 2 de cada archivo .iso (contenido de la instalación, no documentación)
  ·  **Idioma:** n/a (código)

```
% prubafresas.pgm
;H DX=300.000 DY=300.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 

--- otras cuatro cabeceras encontradas, literales ---
;H DX=704.000 DY=549.550 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
;H DX=305.000 DY=305.000 DZ=50.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
;H DX=747.000 DY=584.550 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
;H DX=354.550 DY=266.550 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0
```

### `H … -HG … (literal) — aparece en archivos .Lxl y .mix reales de la instalación, con campos que el manual no documenta`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/Projects/BIBLIOTECA STANDARD 2019/… (varios archivos “OrginalLXL” y “N.Lxl”) ; C:/Program Files (x86)/Scm Group/Maestro/Projects/Biblioteca STD 2021/Comoda/… (archivo mix “Comoda 1100x840x500 4 caj”)`
  ·  **Sección:** Línea 1 de cada archivo (contenido de la instalación, no documentación)
  ·  **Idioma:** n/a (código)

```
H DX=2518.000 DY=600.000 DZ=18.000 -HG /def C=0 T=0 R=1     *MM BX=0.000 BY=0.000 BZ=0.000 ORIG=01 ROT=2 MAGX=0.000 MAGY=0.000 EDGE16=0.000 EDGE26=0.000 EDGE36=0.000 EDGE46=0.000

H DX=946.000 DY=864.000 DZ=5.000 -HG /def C=0 T=0 R=1     *MM BX=0.000 BY=0.000 BZ=0.000 ORIG=01 MAGX=0.000 MAGY=0.000

H DX=742.000 DY=560.000 DZ=18.000 -HG /def C=0 T=0 R=1     *MM BX=0.000 BY=0.000 BZ=0.000 ORIG=01 COLB2=-4144960 EDGE2=-0.450 THICKEDGE2=0.450 ROT=2 MAGX=0.000 MAGY=0.000 EDGE16=0.000 EDGE26=0.000 EDGE36=0.000 EDGE46=0.000

--- archivo mix ---
P/"P:\SCM Group\Maestro\Projects\Biblioteca STD 2021\Comoda\Comoda 1100x840x500 4 caj\Lado_izquierdo.pgmx" -HG R=1 *MM /"DEF" C0 T0 V0
```

### `H header instruction — correspondencia con la API de scripting de Maestro`

**Fuente:** `c:/Dev/Repositorios/ProdAction/pgmx/docs/maestro_scripting/04_tools_workpiece.md (líneas 750-775)`
  ·  **Sección:** SetMachiningParameters Method (IScripting, ScmGroup.XCam.Scripting)
  ·  **Idioma:** inglés

```
MachiningParameters SetMachiningParameters(
string executionFields,
int repetitions,
long tableOptions,
long mechanicalOptions,
bool continuousCycle
)

Parameters
executionFields — Type: System..::..String — Working area (same as - in the Xilog H header instruction).
repetitions — Type: System..::..Int32 — Number of repetitions (same as R in the Xilog H header instruction)
tableOptions — Type: System..::..Int64 — Settings for blobking type (same as V in the Xilog H header instruction).
mechanicalOptions — Type: System..::..Int64 — Settings for mechanical options (same as T in the Xilog H header instruction).
continuousCycle — Type: System..::..Boolean — Enable continuous cycle execution (same as C in the Xilog H header instruction).
```

### `“V” como velocidad de recorrido (campo de G0/GIN/GOUT/GREP) — parecido, NO es la V del header`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm (líneas 78, 84, 194, 200)`
  ·  **Sección:** 5.2.1.1 Funciones generales — Entrada automática en el perfil - GIN / Salida automática del perfil - GOUT / Repetición de un perfil - GREP
  ·  **Idioma:** español

```
- valor configurado para el inicio del perfil si en la instrucción de inicio perfil (G0) el campo V (velocidad de recorrido) está programado con un valor
- valor configurado en el parámetro “Velocidad G0/B (…)” de la herramienta utilizada para el perfil, si en la instrucción de inicio perfil el campo V (velocidad de recorrido) no está programado

[y en GREP:]
V — Velocidad de fresado.

[NOTA DEL RELEVAMIENTO: en el manual la letra V se usa con DOS significados distintos según la instrucción. Se trae marcado como parecido, no idéntico.]
```

### `“Campo V” del Header referido desde EPL / ejemplos de plano motorizado`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_spa/9.4_Ejemplo_de_trabajo_con_bornes_est_ndares_.htm ; out_spa/9.5_Ejemplo_de_elaboraci_n_con_bornes_horizontales_.htm ; out_spa/9.6_Ejemplo_de_elaboraci_n_con_ventosas_.htm ; out_spa/9.7_Visualizaci_n_bloques_de_PB.htm`
  ·  **Sección:** 9.4 / 9.5 / 9.6 / 9.7 (capítulo 9, Plano Motorizado)
  ·  **Idioma:** español

```
[9.4] El campo V del encabezamiento (header) del programa contiene el valor 21.
… esta instrucción describe el panel y define el tipo de bloqueo (campo V).
… valor del campo V = 21.

[9.5] El campo V del encabezamiento del programa contiene el valor 61

[9.6] El campo V del encabezamiento del programa contiene el valor 12.
… esta instrucción describe el panel y define el tipo de bloqueo (campo V).

[9.7] … campo V del Encabezamiento del PGM. EPL permite visualizar el posicionamiento …
```

### `DX, DY del Header referidos desde EPL`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_epl/8.3.3_programación_de_parámetros_(mesa_motorizada_travesaños_y_ventosas).htm (línea 292)`
  ·  **Sección:** 8.3.3 programación de parámetros (mesa motorizada travesaños y ventosas)
  ·  **Idioma:** español

```
DX, DY del Header del programa principal.
```

### `Nuevo campo del Header para PAV (Optimización PAV), vía campo T`

**Fuente:** `C:/Users/fermi/AppData/Local/Temp/claude/c--Dev-Repositorios-ProdAction/2b4a4df7-b886-481a-99e7-9a86bef428d6/scratchpad/out_epl/8.7.4Programaci_n_autom_tica_de_las_ventosas.htm (líneas 456-500)`
  ·  **Sección:** 8.7.4 Programación automática de las ventosas (ayuda EPL)
  ·  **Idioma:** español

```
En el Header del programa se ha introducido un nuevo campo que identifica o no la opción de lanzamiento de PAV antes de la ejecución del programa.
1 Clic en el botón OPCIONES T para abrir el Header del programa.
2 Aparecerá la ventana PROGRAMACIÓN DE LAS OPCIONES. Hacer doble clic en el campo OPTIMIZACIÓN PAV y desde el menú de selección seleccionar SI (para habilitar el arranque automático) NO (para inhabilitar el arranque automático).
El valor predefinido y el introducido en el nuevo parámetro “Lanzamiento PAV “ presente en Gendata.cfg.
Es posible llamar la ventana de Programación de las opciones también desde el Tablero Máquina con un clic en el botón que está dentro de la ventana modificar Header.
```

**No aparece en ninguna fuente:** `«;H» como instrucción documentada: NO APARECE en ninguno de los manuales relevados (out_spa 1436 archivos, out_editor_ing 1434, out_epl 210, out_panelmac 271, maestro_editor_es.txt, pgmx/docs/xilog_plus_pgm, pgmx/docs/maestro_scripting, out_winxiso_*, out_testine_spa, out_mscript_es/out_scripting_es). La cadena literal «;H » sólo aparece en cinco archivos .iso dentro de C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/ (citados en hallazgos). El manual documenta «;» sólo como carácter de comentario (§5.2.6), sin mencionar «;H».`, `«HG» dentro de la lista de valores admitidos del campo «-» de la instrucción H: NO APARECE. La página 5.1 Encabezamiento (ES e ING) enumera únicamente «A, B, C, D, AB, BA, CD, DC, AD, DA». HG aparece en otras secciones (§4.4.2 zonas, apéndice de zonas virtuales, ayuda EPL §8.4, §9.13) pero nunca en la lista del campo «-» de H.`, `«ORIG=» — NO APARECE en ninguna fuente documental (aparece sólo en cabeceras H de archivos .Lxl reales de C:/Program Files (x86)/Scm Group/Maestro/Projects/).`, `«ROT=» (como campo de la cabecera H) — NO APARECE en ninguna fuente documental.`, `«MAGX» / «MAGY» — NO APARECEN en ninguna fuente documental.`, `«EDGE16» / «EDGE26» / «EDGE36» / «EDGE46» / «EDGE2» / «THICKEDGE2» — NO APARECEN en ninguna fuente documental.`, `«COLB2» — NO APARECE en ninguna fuente documental.`, `El manual del Maestro Editor en español (maestro_editor_es.txt, 170 páginas) NO contiene la instrucción H ni los campos DX/DY/DZ/BX/BY/BZ del header: la búsqueda de «;H», «H DX», «BX», «cabecera», «encabezad» y «Header» no devuelve ninguna coincidencia relativa a la cabecera (sólo coincidencias de «DXF» y de variables de proyecto dx1/dy1/dz1).`, `La ayuda de PanelMac (out_panelmac, 271 archivos) NO contiene «BX», «BY», «BZ» ni «;H».`, `La ayuda de WinXiso (out_winxiso_spa / _ing / _root) NO contiene «DX», «BX» ni «;H»: describe únicamente la conversión XXL↔PGM y sus opciones de línea de comandos.`, `La página 5.1 no documenta un valor por defecto explícito para BX/BY/BZ ni indica qué ocurre si se omiten esos campos: NO APARECE tal indicación.`

## origen Or

### `%Or[0].ofX / %Or[0].ofY / %Or[0].ofZ`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/pieza 300x300 calxy.iso (líneas 1-19)`
  ·  **Sección:** Archivo .iso de ejemplo que vino en la carpeta PostProcessor de la instalación. NO es documentación: es una salida real del postprocesador.
  ·  **Idioma:** n/a (código ISO)

```
% pieza 300x300 calxy.pgm
;H DX=305.000 DY=305.000 DZ=50.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
%Or[0].ofX=-305000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=50000.000 
?%EDK[0].0=0 
?%EDK[1].0=0 
MLV=1 
SHF[X]=-305.000 
SHF[Y]=-1515.750 
SHF[Z]=50.000+%ETK[114]/1000
```

### `%Or[0].ofX / %Or[0].ofY / %Or[0].ofZ (segunda aparición en el mismo archivo)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/pieza 300x300 calxy.iso (líneas 30-45)`
  ·  **Sección:** Archivo .iso de ejemplo de la instalación
  ·  **Idioma:** n/a (código ISO)

```
S18000M3 
G17 
MLV=2 
%Or[0].ofX=-310000.000 
%Or[0].ofY=-1515750.000 
%Or[0].ofZ=50000.000 
MLV=1 
SHF[X]=-305.000 
SHF[Y]=-1510.750 
SHF[Z]=50.000 
MLV=2
```

### `%Or[n] — inventario COMPLETO de apariciones en toda la instalación`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/*.iso (salida de: grep -n '%Or' *.iso)`
  ·  **Sección:** Los 5 únicos archivos de la instalación entera que contienen la cadena '%Or['. El índice n vale SIEMPRE 0; no aparece ningún %Or[1] ni superior en ninguna fuente.
  ·  **Idioma:** n/a (código ISO)

```
lado_derecho1.iso:11:%Or[0].ofX=-354549.988 
lado_derecho1.iso:12:%Or[0].ofY=-1515750.000 
lado_derecho1.iso:13:%Or[0].ofZ=43000.000 
lado_derecho1.iso:37:%Or[0].ofX=-359549.988 
lado_derecho1.iso:38:%Or[0].ofY=-1515750.000 
lado_derecho1.iso:39:%Or[0].ofZ=43000.000 
lado_izquierdo1.iso:11:%Or[0].ofX=-747000.000 
lado_izquierdo1.iso:12:%Or[0].ofY=-1515750.000 
lado_izquierdo1.iso:13:%Or[0].ofZ=43000.000 
lado_izquierdo1.iso:37:%Or[0].ofX=-752000.000 
lado_izquierdo1.iso:38:%Or[0].ofY=-1515750.000 
lado_izquierdo1.iso:39:%Or[0].ofZ=43000.000 
pieza 300x300 calxy.iso:11:%Or[0].ofX=-305000.000 
pieza 300x300 calxy.iso:12:%Or[0].ofY=-1515750.000 
pieza 300x300 calxy.iso:13:%Or[0].ofZ=50000.000 
pieza 300x300 calxy.iso:37:%Or[0].ofX=-310000.000 
pieza 300x300 calxy.iso:38:%Or[0].ofY=-1515750.000 
pieza 300x300 calxy.iso:39:%Or[0].ofZ=50000.000 
prubafresas.iso:11:%Or[0].ofX=-300000.000 
prubafresas.iso:12:%Or[0].ofY=-1515750.000 
prubafresas.iso:13:%Or[0].ofZ=43000.000 
prubafresas.iso:36:%Or[0].ofX=-300000.000 
prubafresas.iso:37:%Or[0].ofY=-1515750.000 
prubafresas.iso:38:%Or[0].ofZ=43000.000 
rebaje laterales.iso:11:%Or[0].ofX=-704000.000 
rebaje laterales.iso:12:%Or[0].ofY=-1515750.000 
rebaje laterales.iso:13:%Or[0].ofZ=43000.000 
rebaje laterales.iso:37:%Or[0].ofX=-704000.000 
rebaje laterales.iso:38:%Or[0].ofY=-1515750.000 
rebaje laterales.iso:39:%Or[0].ofZ=43000.000
```

### `O (instrucción: desplazamiento del origen del tablero)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm (también transcrito en c:/Dev/Repositorios/ProdAction/pgmx/docs/xilog_plus_pgm/05_2_instrucciones_basicas.md, línea 1224)`
  ·  **Sección:** 5.2.2 Instrucciones modales — «Desplazamiento del origen del tablero en tope - O»
  ·  **Idioma:** español

```
5.2.2 Instrucciones modales

Desplazamiento del origen del tablero en tope - O 

Desplaza el origen del tablero en tope a la posición programada; todas las instrucciones que siguen se refieren al nuevo origen.

Parámetros:

X | Origen en X.
Y | Origen en Y.
Z | Origen en Z.
f | Si ha sido programado con el número de una cara (1-5), habilita la instrucción sólo para el origen de la cara planteada.

Ejemplo:
►Origen máquina delantero 
►Origen máquina trasero
```

### `O (instrucción, versión inglesa)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_editor_ing/5.2_Basic_Instructions_(Text).htm (línea 3513 del texto extraído)`
  ·  **Sección:** 5.2.2 Modal Instructions — «Move the origin of the panel to position - O»
  ·  **Idioma:** inglés

```
5.2.2 Modal Instructions

Move the origin of the panel to position - O 

Moves the origin of the panel to the programmed position. All the following instructions will refer to the new origin.

Parameters:

X | Origin in X.
Y | Origin in Y.
Z | Origin in Z.
f | If programmed with the number of one face (1-5), it enables the instruction only for the origin of the set face.

Example:
►Front machine origin
►Rear machine origin
```

### `XO (Cambio origen)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.3_Instrucciones_completas_(gr_ficas).htm (línea 4826 del texto extraído; también pgmx/docs/xilog_plus_pgm/05_3_instrucciones_completas.md línea 1710)`
  ·  **Sección:** 5.3.2 Instrucciones modales — «Cambio origen - XO»
  ·  **Idioma:** español

```
5.3.2 Instrucciones modales

Cambio origen - XO

Desplaza el origen del tablero en tope a la posición programada; todas las instrucciones que siguen se refieren al nuevo origen.

Grupo: Funciones principales

Parámetros básicos:

X | Origen en X.
Y | Origen en Y.
Z | Origen in Z.

Parámetros completos:

f | Si ha sido programado con el número de una cara (1-5), habilita la instrucción sólo para el origen de la cara planteada

Ejemplo:
►Origen máquina delantero 
►Origen máquina trasero
```

### `XO (Origin change, versión inglesa)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_editor_ing/5.3_Extended_Instructions_(Graphic).htm (línea 4835 del texto extraído)`
  ·  **Sección:** 5.3.2 Modal Instructions — «Origin change - XO»
  ·  **Idioma:** inglés

```
5.3.2 Modal Instructions

Origin change - XO

Moves the origin of the panel to the programmed position. All the following instructions will refer to the new origin.

Group: Main functions

Basic parameters:

X | Origin in X.
Y | Origin in Y.
Z | Origin in Z.

Extended parameters:

f | If programmed with the number of one face
```

### `origen máquina (delantero / trasero)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/4.2_Programa.htm (líneas 362-380 del texto extraído)`
  ·  **Sección:** 4.2.1.3 Origen máquina
  ·  **Idioma:** español

```
4.2.1.3 Origen máquina

Según el tipo de máquina, el punto 0 respecto al cual se miden las distancias (origen máquina) puede ser delantero o trasero.

Por ejemplo, el origen es:

· delantero, en las máquinas Record y Ergon;

· trasero, en las máquinas Author, Pratix, Tech.

El desplazamiento de la profundidad (parámetro Z) está indicado con valores positivos. Por ejemplo, para programar un taladrado de 100mm de profundidad a partir de la cota Z=0, en el parámetro Z se introducirá el valor 100. El valor -100 provocará, al contrario, el alejamiento de la fresa de la mesa de trabajo.

ATENCION!

En las máquinas Record, Ergon y Pratix no equipadas con CNC OSAI el parámetro Z está invertido (Z positivo: alejamiento de la mesa de trabajo; Z negativo: acercamiento a la mesa de trabajo).
```

### `machine origin (versión inglesa de 4.2.1.3)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_editor_ing/4.2_Program.htm (líneas 362-380 del texto extraído)`
  ·  **Sección:** 4.2.1.3 Machine Origin
  ·  **Idioma:** inglés

```
4.2.1.3 Machine Origin

Depending on the type of machine, the point 0 from which the distances are measured (machine origin) may be front or rear.

For example:

· front origin, on the Record and Ergon machines;

· rear origin, on the author, Pratix and Tech machines.

The movement in depth (parameter Z) is indicated with positive values. For example, to program a 100mm deep drilled hole, starting from position Z=0, a value of 100 is inserted into the Z parameter. To the contrary, a value of -100 will cause the miller to be moved away from the work table.
```

### `origen de los ejes por área (cuántos orígenes hay)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/4.2_Programa.htm (líneas 392-430 del texto extraído)`
  ·  **Sección:** 4.2.1.4 Areas de trabajo
  ·  **Idioma:** español

```
4.2.1.4 Areas de trabajo

Cada programa se lanza dentro de un área de trabajo. La mesa de trabajo está dividida ordinariamente en 4 áreas (A, B, C, D).

Cada área tiene un origen propio de los ejes, orientado según el origen máquina.

En las mesas con cero central y cuatro topes móviles (uno a la izquierda, uno a la derecha y dos centrales), la presencia de los topes móviles centrales permite programar cada uno de los trabajos independientemente en las cuatro áreas. Además, las áreas pueden ser utilizadas también en pares: por ejemplo, si el tablero a trabajar tiene dimensiones que ocupan dos áreas, se puede utilizar en fase de programaciún un área doble, como el área AB (con origen de los ejes en A)...

 o BA (con origen de los ejes en B).

En las mesas sin cero central (sin topes móviles centrales) la presencia de los topes sólo en los extremos izquierdo y derecho de la mesa de trabajo permite utilizar sólo las áreas AB y DC. En este caso, no es posible plantear el programa de trabajo en las áreas B, C, BA y CD, mientras el planteo de las áreas A y D es considerado automáticamente por Xilog Plus equivalente, respectivamente, a las áreas AB y DC..

ATENCION!

Para las máquinas no equipadas con CNC OSAI vale la configuración siguiente: área izquierda=A; área derecha=B.

La mesa puede confirugarse también con áreas especulares: por ejemplo, respecto de las áreas A, B, C, D arriba detalladas se pueden tener a disposición en la mesa de trabajo las respectivas áreas especulares E, F, G, H.
```

### `orígenes de los ejes (a, b, c, d…) en el programa múltiple`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/4.4_Programa_m_ltiple.htm (líneas 17-40 y 360-372 y 588-620 del texto extraído)`
  ·  **Sección:** 4.4 Programa múltiple / 4.4.1 Editor de los programas múltiples / 4.4.3 Ejemplos
  ·  **Idioma:** español

```
Cada programa introducido en el programa múltiple puede posicionarse ulteriormente en una de las áreas que forman parte de la zona escogida previamente, o bien en referencia a los posibles orígenes de los ejes.
[...]
C) Esquema de los posibles orígenes de los ejes (según el origen máquina de la superficie).
[...]
Las letras minúsculas presentes en la lista de las áreas (a, b, c, d,...) son referencias generales de la posición de los topes de apoyo-pieza. Estas referencias son independientes de las zonas de la superficie, e indican cuatro diversos posibles orígenes de los ejes, según los esquemas siguientes:
[...]
En el programa múltiple están introducidos los siguientes programas, posicionados con referencia a los posibles orígenes de los ejes (a, e, b, f):

Progr1 -a Offset X = 0 Offset Y = 0 Offset Z = 0
Progr1 -e Offset X = 0 Offset Y = 1000 Offset Z = 0
Progr2 -b Offset X = 1500 Offset Y = 0 Offset Z = 0
Progr2 -f Offset X = 1500 Offset Y = 1000 Offset Z = 0

Resulta el siguiente programa en formato .pgm:

H DX=1500 DY=1000 -AB
SO /"PROGR1" BX=0 BY=0 BZ=0 FLD=a
SO /"PROGR1" BX=0 BY=1000 BZ=0 FLD=e
SO /"PROGR2" BX=1500 BY=0 BZ=0 FLD=b
SO /"PROGR2" BX=1500 BY=1000 BZ=0 FLD=f
```

### `origen OP (= “origen panel”)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/8.8_Descripci_n_de_los_archivos.htm (líneas 135, 439, 1175 y ~20 más del texto extraído)`
  ·  **Sección:** 8.8 Descripción de los archivos — tablas de campos de los archivos de mesa
  ·  **Idioma:** español

```
300.000 | Cota referida al origen OP (=“origen panel”) del centro de la viga.
[...]
23..5 | Distancia referida al origen OP (=“origen panel”) del centro Y del tope de apoyo pieza.
```

### `OP origin (= ”panel origin”) — versión inglesa`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_editor_ing/8.8_Files_Description.htm (líneas 128-142 y 446-560 del texto extraído)`
  ·  **Sección:** 8.8 Files Description
  ·  **Idioma:** inglés

```
300.000 | Position referred to the OP origin (=”panel origin”) at the centre of the crossbeam.
[...]
referred to the OP origin (=”panel origin”) on the centre X of the base.
referred to the OP origin on the centre Y of the base.
referred to the OP origin on the centre X of the main rest.
referred to the OP origin on the centre Y of the main rest.
```

### `origen máquina (OM) / origen del tablero (OP)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_panelmac/4.3.4.7_Visualizaci_n_de_la_programaci_n_de_la_mesa_de_trabajo.htm (líneas 24-34 del texto extraído)`
  ·  **Sección:** 4.3.4.7 Visualización de la programación de la mesa de trabajo
  ·  **Idioma:** español

```
mesa de trabajo. Dichas informaciones se visualizan en tres modos:

- Modo láser. Muestra los puntos de introducción de los soportes según el origen máquina (OM) o el origen del tablero (OP);

- Modo regla métrica (visualizadores). Indica los puntos de introducción de los soportes según la regla métrica (RM);

- Modo detalles. Indica los puntos de introducción de los soportes con mayores detalles visualizados según el caso respecto de los diferentes orígenes.
```

### `Origen PGM / Origen Máquina (mandos de la barra)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_panelmac/Editor_Mesas_Trabajo.htm (líneas 80-100) y scratchpad/out_epl/APÉNDICE_A._Menú_y_barras_de_mandos.htm (líneas 205-230)`
  ·  **Sección:** Editor Mesas Trabajo (PanelMac) / APÉNDICE A. Menú y barras de mandos (EPL)
  ·  **Idioma:** español

```
Muesta/Oculta Origen PGM | Muestra/oculta los sistemas de referencia del panel. 

Muestra/Oculta Origen Máquina | Muestra/oculta el sistema de referencia de la máquina.
```

### `XORGACQ (Adquisición orígenes y rotación)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.4_Macros_usuario.htm (líneas 7111 y siguientes del texto extraído)`
  ·  **Sección:** 5.4 Macros usuario — «Adquisición orígenes y rotación - XORGACQ»
  ·  **Idioma:** español

```
Adquisición orígenes y rotación - XORGACQ

Detecta los alejamientos en X e Y y la rotación alrededor del eje Z del tablero respecto al origen del campo seleccionado. La instrucción efectúa dos palpaciones en el lado X y una en el lado Y con una herramienta de tipo palpador XYZ. 

Esta instrucción es compatible con Xilog Plus versión 1.10.003 y superiores.

Grupo: Macro usuario 5

Parámetros:

N | Nombres de las variables que se rellenarán con los valores medidos para: origen X, origen Y, rotación alrededor del eje Z.
T | Herramienta (número de una herramienta de tipo palpador).
QX1 | Cota de palpación del primer punto sobre el lado X (default = DX - 10).
QX2 | Cota de palpación del segundo punto sobre el lado X (default = 10).
QX3 | Cota de palpación sobre el lado Y (default = DY - 10).
```

### `SX / SY (Especular en X / en Y — cambio de origen)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm (líneas 3966-3972 y 4097-4102 del texto extraído)`
  ·  **Sección:** 5.2 Instrucciones básicas (texto) — «Especular en X - SX» y «Especular en Y - SY»
  ·  **Idioma:** español

```
Especular en X - SX 

Cambia el origen en X desplazándolo hacia el ángulo opuesto. Esta instrucción se activa con la entrada automática en el perfil o el inicio fresado.

Grupo: instrucciones texto

[...]

Especular en Y - SY

Cambia el origen en Y desplazándolo hacia el ángulo opuesto. Esta instrucción se activa con la entrada automática en el perfil o el inicio fresado.
```

### `PL (Plano inclinado) — coordenadas del origen del plano respecto al origen del tablero`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm (líneas 4232-4300 y 4316-4350 del texto extraído)`
  ·  **Sección:** 5.2 Instrucciones básicas (texto) — «Plano inclinado - PL»
  ·  **Idioma:** español

```
Plano inclinado - PL

Define un plano distinto de las 5 caras que Xilog Plus crea en automático. Puede girar alrededor del eje Z o del eje X. Un plano inclinado sirve para poder crear geometrías perpendiculares a dicho plano.

Parámetros:

X | Coordenada X del origen del plano (respecto al origen del tablero).
Y | Coordenada Y del origen del plano (respecto al origen del tablero).
Z | Coordenada Z del origen del plano (respecto al origen del tablero).
Q | Ángulo de rotación alrededor del eje Z (origen máquina delantero: positivo en sentido antihorario; origen máquina trasero: positivo en sentido horario).
R | Ángulo de rotación alrededor del eje X (origen máquina delantero: positivo en sentido antihorario; origen máquina trasero: positivo en sentido horario).

[...]

Programación de un plano inclinado con orígenes X=500, Y=0 , Z=0, a 45° del eje Z y a 90° del eje X. 

►Origen máquina delantero 

X=500, Y=0 y Z=0 son las coordenadas de origen del plano inclinado.

Después de cambiar los orígenes, hay que escribir el parámetro Q=ángulo deseado (Q=45) para girar el sistema de los ejes alrededor del eje Z.
```

### `X origen / Y origen / Z origen (posición de las piezas en la fase)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/maestro_editor_es.txt (líneas 3707-3726) y scratchpad/pdfs/maestro_it-IT.txt (líneas 2300-2311) y scratchpad/pdfs/maestro_en-US.txt (líneas 2286-2295)`
  ·  **Sección:** 4.10.5 Modificar la posición de las piezas en la fase / 4.10.5 Spostamento pezzi nella fase
  ·  **Idioma:** español / italiano / inglés

```
ES: «Se puede cambiar la posición de cada pieza en la fase seleccionada modificando los valores a la derecha de los parámetros:

- X origen 
- Y origen 
- Z origen 

Haga clic en el botón "Aplicar"»

IT: «Si può cambiare la posizione di ogni pezzo nella fase selezionata modificando i valori a destra dei parametri :

    - X origine
    - Y origine
    - Z origine
Cliccando poi sul bottone "Applica"»

EN: «    - X origin
    - Y origin
    - Z origin»
```

### `origen del plano inclinado (Maestro Editor)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/maestro_editor_es.txt (líneas 881, 928-935) y scratchpad/pdfs/maestro_it-IT.txt (líneas 623, 634-640)`
  ·  **Sección:** 4.7.3 Plano inclinado / 4.7.3 Piano Inclinato
  ·  **Idioma:** español / italiano

```
ES: «Un plano inclinado es un plano genérico definido por el usuario con cualquier origen e inclinación.»
[...]
«La definición del Plano inclinado se realiza desde la terna de referencia de la pieza colocada en la esquina inferior izquierda.
Al configurar los valores X origen, Y origen y Z origen se establece dónde se encontrará el origen del nuevo plano.
Al configurar los ángulos Rot. eje Z y Rot. eje X, se establece la orientación del plano.»

IT: «Un piano inclinato è un piano generico definito dall'utente con origine e inclinazione qualsiasi.»
[...]
«Impostando i valori X origine, Y origine e Z origine si stabilisce dove si troverà l'origine del nuovo piano.»
```

### `origen (cadenas de configuración de Maestro)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/Languages/es-ES/ConfigurationManager.xml (líneas 813-899; archivo en UTF-16LE)`
  ·  **Sección:** Recursos de idioma de Maestro — ConfigurationManager (WorkField, WorkingArea, MachinePropertyView)
  ·  **Idioma:** español

```
<string code="WorkFieldFirstClampX">Origen X primera mordaza</string>
<string code="WorkFieldFirstClampY">Origen Y primera mordaza</string>
<string code="WorkFieldFirstClampZ">Origen Z primera mordaza</string>
<string code="LoadUnitWorkpieceOffsetX">Offset X origen pieza</string>
<string code="LoadUnitWorkpieceOffsetY">Offset Y origen pieza</string>
<string code="LoadUnitWorkpieceOffsetZ">Offset Z origen pieza</string>
<string code="workingAreaXOriginLocation">Coordenada X</string>
<string code="workingAreaYOriginLocation">Coordenada Y</string>
<string code="workingAreaZOriginLocation">Coordenada Z</string>
<string code="workingAreaXOriginWithSideStopOff">Coordenada X con topes off</string>
<string code="machinePropertyProgrammingOriginType">Tipo de origen de programación</string>
<string code="machinePropertyProgrammingOriginTypeLow">debajo</string>
<string code="machinePropertyProgrammingOriginTypeHigh">arriba</string>
<string code="machinePropertyCentralZero">Cero central</string>
<string code="machineSupportNumberOrigin">Origen numeración soportes</string>
<string code="machinePropertyOffXBetweenParametersOriginAndMachineOrigin">Offset X O.P. - O.M.</string>
<string code="machinePropertyOffYBetweenParametersOriginAndMachineOrigin">Offset Y O.P. - O.M.</string>
<string code="machinePropertyOffZBetweenParametersOriginAndMachineOrigin">Offset Z O.P. - O.M.</string>
```

### `origin (mismas cadenas en inglés, incluye la abreviatura P.O. - M.O.)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/Languages/en-US/ConfigurationManager.xml (líneas 813-899 y 1370-1561; archivo en UTF-16LE)`
  ·  **Sección:** Recursos de idioma de Maestro — ConfigurationManager (inglés)
  ·  **Idioma:** inglés

```
<string code="WorkFieldFirstClampX">Origin X first clamp</string>
<string code="WorkFieldFirstClampY">Origin Y first clamp </string>
<string code="WorkFieldFirstClampZ">Origin Z first clamp </string>
<string code="LoadUnitWorkpieceOffsetX">Offset X workpiece origin</string>
<string code="machinePropertyProgrammingOriginType">Type of programming origin</string>
<string code="machinePropertyProgrammingOriginTypeLow">low</string>
<string code="machinePropertyProgrammingOriginTypeHigh">high</string>
<string code="machineSupportNumberOrigin">Source supports numbering</string>
<string code="machinePropertyOffXBetweenParametersOriginAndMachineOrigin">Offset X P.O. - M.O.</string>
<string code="machinePropertyOffYBetweenParametersOriginAndMachineOrigin">Offset Y P.O. - M.O.</string>
<string code="machinePropertyOffZBetweenParametersOriginAndMachineOrigin">Offset Z P.O. - M.O.</string>
<string code="CnAxis175">X motorised table origin (mm):</string>
<string code="CnAxis176">Y motorised table origin (mm):</string>
<string code="CnAxis436">General origin in X with respect to Xilog+: </string>
<string code="CnAxis437">General origin in Y with respect to Xilog+: </string>
<string code="CnAxis438"> General origin in X with respect to Xilog+:  </string>
```

### `origen (cotas seleccionables: Área / Parámetros / Regla métrica)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/Languages/es-ES/UI00.xml (líneas 3750-3755) y en-US/UI00.xml (líneas 3746-3751); archivos en UTF-16LE`
  ·  **Sección:** Recursos de idioma de Maestro — UI00, «Selezione elemento macchina»
  ·  **Idioma:** español / inglés

```
ES:
<string code="SelectionXQuoteFromAreaOrigin">X (Área)</string>
<string code="SelectionYQuoteFromAreaOrigin">Y (Área)</string>
<string code="SelectionXQuoteFromParameterOrigin">X (Parámetros)</string>
<string code="SelectionYQuoteFromParameterOrigin">Y (Parámetros)</string>
<string code="SelectionXQuoteFromMetricRodOrigin">X (Regla métrica)</string>
<string code="SelectionYQuoteFromMetricRodOrigin">Y (Regla métrica)</string>

EN:
<string code="SelectionXQuoteFromAreaOrigin">X (Area)</string>
<string code="SelectionYQuoteFromAreaOrigin">Y (Area)</string>
<string code="SelectionXQuoteFromParameterOrigin">X (Parameters)</string>
<string code="SelectionYQuoteFromParameterOrigin">Y (Parameters)</string>
<string code="SelectionXQuoteFromMetricRodOrigin">X (Metric line)</string>
<string code="SelectionYQuoteFromMetricRodOrigin">Y (Metric line)</string>
```

### `origen (guía del conversor PGM de Maestro: O, XO, SX, SY, campo A alto/bajo)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/Languages/es-ES/PgmConverter.xml (líneas 44-81) y en-US/PgmConverter.xml (líneas 50, 57, 81); archivos en UTF-16LE`
  ·  **Sección:** Recursos de idioma de Maestro — PgmConverter, «Función Importar PGM / Instrucciones gestionadas»
  ·  **Idioma:** español / inglés

```
ES:
<string code="ImportGuideManagedInstructionsDetails">\n
    taladro (B, XB, BO, XBO, BR, XBR),\n
    fresado (G, XG, GR, XGR, G3D, XG03D, XA2P, XA3P, XAR, ATP, XL2P),\n
    entrada y salida de la pieza (GIN, XGIN, GOUT, XGOUT), \n
    desplazamiento origen (O, XO), \n
    cambio referencia sin cambio de dimensión del tablero (REF), \n
    corrección (C), \n
    cara de trabajo (F), \n
    bisel y unión entre fresados (GCHA, GFIL), \n
    repetición perfil (GREP), \n
    programación incremental (IX, IY), \n
    especularidad origen (SX, SY), \n
    palpado (TA), \n
    operación nula y estacionamiento (XN, PARK), \n
    ajuste herramienta activado (XT), \n
    asignación del valor con variable (SET), \n
    rotación elaboración (ROT), \n
    mesa inclinada (PL)
  </string>
[...]
<string code="ImportGuideProcedureForSideStopAndZetaDetails">\n
    La interpretación de las instrucciones detectadas durante la importación hace referencia a las opciones de Maestro. \n
    Se consideran las opciones del Post para la notación SCM/MBD del origen del campo A (alto/bajo) y hacia Z (positivo/negativo)
  </string>

EN:
    origin movement (O, XO), \n
    origin specularity (SX, SY), \n
    The Post options are considered for the SCM/MBD notes of the origin of field A (high/low) and towards Z (positive/negative)
```

### `origen / origine (mensajes de Xilog Plus instalados)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Spa/Cyc.msg, Sys.msg, axis.msg, Cnc.msg — y sus equivalentes en Country/Ita`
  ·  **Sección:** Archivos de mensajes de la instalación (no son manual; son las etiquetas que muestra el software)
  ·  **Idioma:** español / italiano

```
Cyc.msg (Spa):
@010,"Desplazamiento origen panel en tope"
@114,"Cambio origen"
@492,"Origen pieza respecto a los topes"
@511,"Origen X de la pieza"
@512,"Origen Y de la pieza "
@513,"Origen Z de la pieza "
@521,"Cambio origen en Z (vacío=ninguno):"

Cyc.msg (Ita):
@010,"Spostamento origine pannello in battuta"
@114,"Cambio origine"
@492,"Origine pezzo rispetto alle battute"
@511,"Origine X del pezzo"
@512,"Origine Y del pezzo"
@513,"Origine Z del pezzo"
@521,"Cambio origine in Z (vuoto=nessuno):"

axis.msg (Spa):
@026,"Sentido recepción de origen: "
@175,"Origen X mesa motorizada (mm):"
@176,"Origen Y mesa motorizada (mm):"
@436,"Origen general en X respecto a Xilog+: "
@437,"Origen general en Y respecto a Xilog+: "
@438,"Origen general en Z respecto a Xilog+: "

Sys.msg (Spa):
@021,"Archivo origen Iso no hallado"
@033,"El archivo origen Iso está cerrado"
@107,"Error de lectura origen pieza, origen máquina"
@033,"Con la mesa motorizada, el parámetro 'Origen numeración soportes (0-3)' (in XILOG3.CFG) debe valer 1 o 3."

Cnc.msg (Spa):
@27,"VALIDACION O INVALIDACION DE UNA CORRECION DE RADIO:- EN PROGRAMACION ORIGEN MAQUINA [G52]- EN ROSCADO CONICO [G38]"
```

### `unidad de medida del programa (contexto de unidades; NO es la unidad de %Or)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.1_Encabezamiento.htm (líneas 82-92) y scratchpad/out_editor_ing/5.1_Header.htm (líneas 80-90)`
  ·  **Sección:** 5.1 Encabezamiento — parámetros completos, campo «*» / 5.1 Header, parameter «*»
  ·  **Idioma:** español / inglés

```
ES: «* | Unidad de medida. Los valores admitidos son MM (milímetros) e IN (pulgadas); si el campo se omite, vale la unidad programada en los parámetros de la máquina.»

EN: «* | Unit of measure. The allowed values are MM (millimeters) ad IN (inches); if the field is omitted, the unit of measures specified in the machine parameters will be used.»
```

### `origen (posicionamiento de ventosas — depende del origen máquina)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/8.7_Otras_funciones.htm (líneas 285-300 del texto extraído)`
  ·  **Sección:** 8.7 Otras funciones — origen de búsqueda para el posicionamiento automático
  ·  **Idioma:** español

```
búsqueda. Define el ángulo del tablero desde el cual se inicia el posicionamiento de las ventosas. El ángulo se define según las coordinadas X, Y mínima/máxima (el valor de default es “X mínimo, Y mínimo”, es decir el punto de origen de los ejes).

La definición del ángulo depende del sistema de referencia de los ejes (origen máquina delantero o trasero) y de la configuración de la zona de trabajo.

La selección del origen de búsqueda influye notbalemente el posicionamiento de los travesaños (en el caso de las opciones “Máxima cobertura de la superficie del tablero” y “Rectángulos definidos por el usuario”) y de las ventosas. En especial, en el caso de que estén disponibles pocas ventosas, programando orígenes diferentes es posible que cambie también el tipo de ventosa introducido.
```

### `orígenes (disponibles / libres) en PanelMac`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_panelmac/4.3.3_Lector_de_c_digos_de_barras.htm (líneas 162-175 del texto extraído)`
  ·  **Sección:** 4.3.3 Lector de códigos de barras
  ·  **Idioma:** español

```
· Si el “Tipo de funcionamiento” vale 1, el nombre del archivo recibido se carga en todos los orígenes disponibles en la máquina, teniendo en cuenta las combinaciones de los campos programados (AB, CD, AD, etc.) o determinados por las dimensiones DX de la pieza (campo programado 00, 01, 10, 11). El número de repeticiones no se tiene en cuenta y el programa queda activo hasta su sustitución. La recepción de un nuevo nombre de archivo sustituye el anterior en los orígenes libres; los cuales se consideran tales si no hay ningún tablero bloqueado, si no existe una reserva o si no se está en ejecución. Si no hay orígenes libres, el archivo se ubica en la cola y ni bien se libera, sustituye el anterior. No es posible poner más de un programa en la cola, por lo tanto las lecturas sucesivas sustituyen el último programa colocado en la cola.
```

### `origen máquina en el archivo de configuración EPL`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_epl/Par_metros_de_configuraci_n.htm (líneas 1490-1497 del texto extraído)`
  ·  **Sección:** Parámetros de configuración (EPL) — [OFFXQUOTA]
  ·  **Idioma:** español

```
[OFFXQUOTA]... | Offset en X de la cota de la mesa entre el origen máquina y el 0 de la varilla métrica aplicada sobre la base. |
```

**No aparece en ninguna fuente:** `%Or (con o sin corchetes, con o sin %, en cualquier combinación de mayúsculas/minúsculas): NO APARECE en ninguna documentación — ni en out_spa (1436 archivos), ni en out_editor_ing (1434), ni en out_epl (210), ni en out_panelmac (271), ni en out_winxiso_spa/ing/root, ni en out_scripting_es, ni en out_testine_spa, ni en maestro_editor_es.txt, ni en pdfs/maestro_it-IT|en-US|de-DE.txt, ni en pgmx/docs/xilog_plus_pgm/, ni en pgmx/docs/maestro_scripting/. Sólo aparece en los 5 archivos .iso de C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/`, `ofX: NO APARECE en ninguna documentación (mismas fuentes barridas). Sólo en los 5 .iso citados. Las coincidencias de la cadena 'ofX' en ScmGroup.XCam.Post.dll, ScmGroup.XCam.PgmConverter.dll y en los .chm son fragmentos de nombres ofuscados/comprimidos, no texto real (verificado extrayendo el contexto)`, `ofY: NO APARECE en ninguna documentación. Sólo en los 5 .iso citados`, `ofZ: NO APARECE en ninguna documentación. Sólo en los 5 .iso citados`, `origini (plural italiano): NO APARECE en ninguna fuente. En italiano sólo aparece el singular 'origine' (Cyc.msg, Sys.msg, axis.msg, app.msg de Country/Ita y pdfs/maestro_it-IT.txt)`, `%Or[1], %Or[2] o cualquier índice distinto de 0: NO APARECE en ninguna fuente. Los 5 .iso de la instalación usan exclusivamente %Or[0]`, `Or[ como token documentado: NO APARECE. Las coincidencias binarias en Xilog_Plus_Editor.chm (Ita), Xilog_Plus_Epl.chm (Ted), fajx276.pgmx y tascaret.avi son ruido de compresión (verificado)`, `Tabla, lista o capítulo que enumere los orígenes del programa ISO con su numeración: NO APARECE en ninguna de las 8 fuentes. Tampoco hay documentación del lenguaje de variables del ISO (%ETK, %EDK, %ax[], SHF[], MLV) en ninguna ayuda; esos tokens sólo aparecen como plantillas dentro del binario C:/Program Files (x86)/Scm Group/Xilog Plus/Bin/VtGenIso.dll, y ahí tampoco figura Or[ ni ofX/ofY/ofZ`, `Unidad de medida de %Or[0].ofX/ofY/ofZ: NO APARECE declarada en ninguna fuente. La única declaración de unidades hallada es el campo '*' del encabezamiento (MM/IN), que es del programa PGM, no del registro Or`

## parametros de eje

### `_paras`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/NCI.CFG`
  ·  **Sección:** clave $GEN_INIT (archivo completo, 66 lineas)
  ·  **Idioma:** italiano (comentarios) / codigo

```
$GEN_ISO_FOR_EXTERNAL_APP
1
$
$GEN_INIT
?%%ETK[500]=100
;?%%ETK[500]=%%ax[0].pa[22]/1000 ;solo per zone
_paras( 0x00, X, 3, %%ax[0].pa[21]/1000, %%ETK[500] )
;
G0 G53 Z %%ax[2].pa[22]/1000
M58 ;abilita controllo vuoto
$
$GEN_END
?%%ETK[0]=0
?%%ETK[1]=0
?%%ETK[2]=0
?%%ETK[13]=0
?%%ETK[17]=0
?%%ETK[18]=0
?%%ETK[19]=0
$
```

### `_paras`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Fxc/Mbd/Park.pgm`
  ·  **Sección:** macro de fabrica; cabecera del programa: "Inserimento limitazione/ripristino corsa X di anticollisione  M.De Crescenzo 2/10/2012"
  ·  **Idioma:** italiano (comentarios) / codigo

```
L AREA=FLD
IF AREA=1 OR AREA=2 OR AREA=12 OR AREA=21 OR AREA=14 THEN
   ISO "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ax[0].pa[22]/1000 )" ;Ripristino corsa totale asse X
   ISO "G0G53 X%ax0.pa31/1000 Y%ax1.pa22/1000"
FI
IF AREA=3 OR AREA=4 OR AREA=34 OR AREA=43 OR AREA=41 THEN
   ISO "G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000"
FI
[...]
ISO "_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )" ;Ripristino limitazione corsa positiva X di anticollisione
```

### `_paras`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/prubafresas.iso`
  ·  **Sección:** cabecera del ISO postprocesado (lineas 1-10) y cierre (lineas 211-216)
  ·  **Idioma:** codigo (ISO generado por el postprocesador)

```
% prubafresas.pgm
;H DX=300.000 DY=300.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0 
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58 
G71 
MLV=0 
[...]
D0 
G0 G53 Z201.000 
G64 
G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000  
_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )  
SYN
```

### `_paras`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/lado_derecho1.iso (idem lado_izquierdo1.iso, rebaje laterales.iso, pieza 300x300 calxy.iso)`
  ·  **Sección:** lineas 5 y 7
  ·  **Idioma:** codigo (ISO generado)

```
5:_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )
7:G0 G53 Z %ax[2].pa[22]/1000
```

### `%ax[n].pa[m] — notacion sin corchetes (%ax0.pa21, %ax1.pa22, %ax0.pa31)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Fxc/Mbd/Park.pgm`
  ·  **Sección:** cuerpo de la macro Park
  ·  **Idioma:** codigo

```
ISO "G0G53 X%ax0.pa31/1000 Y%ax1.pa22/1000"
ISO "G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000"
```

### `pa[21] / pa21`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/parax.str`
  ·  **Sección:** tabla de definicion de parametros de eje, entradas [AP_MINQUOTA] y [AP_MAXQUOTA] (lineas ~1524-1536)
  ·  **Idioma:** codigo / italiano abreviado

```
[AP_VELTACCA]
ADR = pa20
FRM = QTA, 0
HLP = AP_VELTACCA
[AP_MINQUOTA]
ADR = pa21
FRM = QTA, 3
HLP = AP_MINQUOTA
[AP_MAXQUOTA]
ADR = pa22
FRM = QTA, 3
HLP = AP_MAXQUOTA
[AP_VELMAN]
ADR = pa23
FRM = QTA, 0
HLP = AP_VELMAN
[AP_MINICS]
ADR = pa24
FRM = QTA, 0
HLP = AP_MINICS
```

### `tabla de parametros de eje por indice (nombre -> paN)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/parax.str`
  ·  **Sección:** seccion [AP_*]: pares nombre de parametro -> direccion ADR (extraccion completa de las entradas AP_)
  ·  **Idioma:** codigo

```
[AP_NAME] ADR = nam0
[AP_AXTYPE] ADR = pa0
[AP_DRVTYPE] ADR = nvel11
[AP_ROTARYMODE] ADR = pa45
[AP_ACCTIME] ADR = pa1
[AP_DECTIME] ADR = pa2
[AP_DELAYS] ADR = pa25
[AP_ACCEL] ADR = pa1
[AP_DECEL] ADR = pa2
[AP_JERK] ADR = pa25
[AP_OPZIONI0..AP_OPZIONI31] ADR = pa3
[AP_FWERRVLIM] ADR = pa4
[AP_FWERR] ADR = pa5
[AP_SSERRK] ADR = pa4
[AP_SSERR] ADR = pa5
[AP_TOLLERG] ADR = pa6
[AP_TOLLERF] ADR = pa7
[AP_TOLLER] ADR = pa8
[AP_VELMAX] ADR = pa9
[AP_GAINP] ADR = pa10
[AP_GAIND] ADR = pa11
[AP_INFWD] ADR = pa12
[AP_KPGAIN] ADR = pa10
[AP_KDGAIN] ADR = pa11
[AP_KVFFGAIN] ADR = pa12
[AP_INSPOS] ADR = pa14
[AP_FATTCONV] ADR = pa15
[AP_FATTCONVDIV] ADR = pa42
[AP_QFATTCONV] ADR = dQFattConv
[AP_QFATTCONVDIV] ADR = dQFattConvDiv
[AP_TARTYPE] ADR = pa16
[AP_SERCOSREF] ADR = pa16
[AP_CANOPENREF] ADR = pa16
[AP_INSNEG] ADR = pa17
[AP_TARQUOTA] ADR = pa18
[AP_VELMICRO] ADR = pa19
[AP_VELTACCA] ADR = pa20
[AP_MINQUOTA] ADR = pa21
[AP_MAXQUOTA] ADR = pa22
[AP_VELMAN] ADR = pa23
[AP_MINICS] ADR = pa24
[AP_ICSTIME] ADR = pa48
[AP_QCHKTARA] ADR = pa26
[AP_TIPOTSTENC] ADR = pa27
[AP_OFFSET] ADR = pa28
[AP_TIMEOFF] ADR = pa29
[AP_RECQTA] ADR = pa30
[AP_PARKQTA] ADR = pa31
[AP_EMERTIME] ADR = pa32
[AP_EMERDEC] ADR = pa32
[AP_AXMOD] ADR = pa33
[AP_QTARECG] ADR = pa34
[AP_TYPERECG] ADR = pa35
[AP_TIMCOMDIR] ADR = pa36
[AP_INERZAV] ADR = pa37
[AP_INERZIND] ADR = pa38
[AP_TIMERFRENO] ADR = pa39
[AP_AXNZONE] ADR = pa40
[AP_TIMEREG] ADR = pa41
[AP_CZMASTER] ADR = pa43
[AP_OFFSETDAC] ADR = pa44
[AP_AXNTORCIA] ADR = pa46
[AP_AXNGANTRY] ADR = pa47
[AP_GAINP_I] ADR = pa49
[AP_KPGAIN_I] ADR = pa49
[AP_SCALING] ADR = wScaling
[AP_CAL_ADC1] ADR = cal0
[AP_CAL_QTA1] ADR = cal2
[AP_CAL_ADC2] ADR = cal1
[AP_CAL_QTA2] ADR = cal3
```

### `pa[21] / pa[22] — otros prefijos de la misma tabla (POL_, SP_, NV_, PT_)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/parax.str`
  ·  **Sección:** secciones POL_ (linea ~1758), SP_ (linea ~1758), NV_ (linea ~2035), PT_ (linea ~2278)
  ·  **Idioma:** codigo

```
[POL_MINQUOTA]
ADR = pa21
FRM = DEC, 3
HLP = POL_MINQUOTA
[POL_MAXQUOTA]
ADR = pa22
FRM = DEC, 3
HLP = POL_MAXQUOTA
---
[SP_VEL10V]
ADR = pa21
FRM = DEC, 0
HLP = SP_VEL10V
[SP_ENCTYPE]
ADR = pa22
RST = 1
RNG = {0,1}
HLP = SP_ENCTYPE
---
[NV_DECSOGV1]
ADR = pa21
FRM = QTA, 3
HLP = NV_DECSOGV1
[NV_DECSOGV2]
ADR = pa22
FRM = QTA, 3
HLP = NV_DECSOGV2
---
[PT_MAXQUOTA]
ADR = pa21
FRM = QTA, 3
HLP = PT_MAXQUOTA
[PT_VELMAN]
ADR = pa22
FRM = QTA, 0
HLP = PT_VELMAN
```

### `AP_MINQUOTA / AP_MAXQUOTA (valores por eje)`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/Params.cfg`
  ·  **Sección:** bloques [ax0], [ax1], [ax2] (lineas 149-155, 207-213, 265-271)
  ·  **Idioma:** codigo / italiano (ASSE X/Y/Z)

```
[ax0]
AP_NAME = ASSE X
AP_AXTYPE = 1
AP_DRVTYPE = 1
AP_MINQUOTA = -3702000
AP_MAXQUOTA = 621000
AP_VELMAX = 25000
[...]
AP_TARQUOTA = 335550
AP_VELMICRO = 2000
AP_VELTACCA = 600
AP_MINICS = 0
AP_ICSTIME = 0
AP_QCHKTARA = 5670
AP_PARKQTA = 0

[ax1]
AP_NAME = ASSE Y
AP_AXTYPE = 1
AP_DRVTYPE = 1
AP_MINQUOTA = -1870000
AP_MAXQUOTA = 131000
AP_VELMAX = 25000

[ax2]
AP_NAME = ASSE Z
AP_AXTYPE = 1
AP_DRVTYPE = 1
AP_MINQUOTA = -53000
AP_MAXQUOTA = 201000
AP_VELMAX = 15000
```

### `tabla de parametros de eje por indice (subcodigo por eje)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/Axis.ini`
  ·  **Sección:** cabecera del formato + GRUPPO = "AXIS X" (la misma lista se repite para AXIS Y, Z, A, B, C, C1, C2)
  ·  **Idioma:** italiano

```
;PostoVideo,RiferimentoTesto,FormatoVideo,TipoParametro,...
;FormatoCN,SpegnimentoCN,CodiceParametro,Sottocodice1,...,SottocodiceN.
GRUPPO = "AXIS X"
2,46,%1.0,P,2,0,0,1    ;Quota minima
3,47,%1.0,P,2,0,0,2    ;Quota massima
4,48,%1.0,P,2,0,0,3    ;Quota di taratura
5,49,%1.0,P,2,0,0,4    ;Quota di parcheggio
6,50,%1.0,P,2,0,0,5    ;Velocità massima
7,51,%1.0,P,2,0,0,6    ;Vel. di manuale (jog)
8,54,%1.0,P,2,0,0,9    ;Tempo di accelerazione
9,55,%1.0,P,2,0,0,10   ;Tempo di decelerazione
10,60,%1.0,P,2,0,0,15  ;Max errore di inseguimento
11,63,%1.0,P,2,0,0,18  ;Recupero giochi all'inversione
12,66,%1.0,P,2,0,0,21  ;Soglia errore taratura
```

### `textos de los parametros de eje por indice (@046-@051)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Country/Ita/axis.msg  y  .../Country/Spa/axis.msg`
  ·  **Sección:** archivo de mensajes de ejes (409 lineas), indices @046 en adelante
  ·  **Idioma:** italiano / español

```
Ita/axis.msg:
@046,"Quota minima:"
@047,"Quota massima:"
@048,"Quota di taratura:"
@049,"Quota di parcheggio:"
@050,"Velocità massima:"
@051,"Vel. di manuale (jog):"

Spa/axis.msg:
@046,"Cota mínima:"
@047,"Cota máxima:"
@048,"Cota de regulación:"
@049,"Cota de aparcamiento:"
@050,"Velocidad máxima:"
@051,"Vel. desde manual (jog):"
```

### `textos de los parametros de eje por indice (Maestro)`  ⚠️ *parecido, no idéntico*

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/Languages/es-ES/ConfigurationManager.xml`
  ·  **Sección:** strings code="CnAxisNNN" (lineas 1235-1324)
  ·  **Idioma:** español

```
<string code="CnAxis001">Límite mínimo (micron): </string>
<string code="CnAxis002">Límite máximo (micron): </string>
<string code="CnAxis003">Cota de calibrado (micron): </string>
<string code="CnAxis004">Velocidad máxima (mm/min): </string>
[...]
<string code="CnAxis046">Cota mínima:</string>
<string code="CnAxis047">Cota máxima:</string>
<string code="CnAxis048">Cota de regulación:</string>
<string code="CnAxis049">Cota de aparcamiento:</string>
<string code="CnAxis050">Velocidad máxima:</string>
<string code="CnAxis051">Vel. desde manual (jog):</string>
<string code="CnAxis052">Vel. búsqueda micro cobertura:</string>
<string code="CnAxis053">Vel. búsqueda muesca de 0:</string>
<string code="CnAxis054">Tiempo de aceleración:</string>
<string code="CnAxis055">Tiempo de deceleración:</string>
<string code="CnAxis056">T. de deceler. por EMERGENCIA:</string>
<string code="CnAxis057">Tiempo de rampa en S:</string>
<string code="CnAxis058">Timer control tolerancia:</string>
<string code="CnAxis059">Ganancia P:</string>
<string code="CnAxis060">Max error de seguimiento:</string>
<string code="CnAxis061">Factor de conv. NUMERADOR:</string>
<string code="CnAxis062">Factor de conv. DENOMINADOR:</string>
<string code="CnAxis063">Recobro juegos en la inversión:</string>
<string code="CnAxis064">Límite fin:</string>
<string code="CnAxis065">Límite aproximado:</string>
<string code="CnAxis066">Límite error regulación:</string>
```

### `D0`

**Fuente:** `C:/Program Files (x86)/Scm Group/Maestro/PostProcessor/prubafresas.iso`
  ·  **Sección:** cuerpo del ISO (lineas 49-67; el patron D1 ... D0 se repite en cada elaboracion)
  ·  **Idioma:** codigo (ISO generado)

```
G0 X-15.000 Y100.000 
G0 Z145.400 
D1 
SVL 125.400 
VL6=125.400
SVR 9.180 
VL7=9.180
G1 Z-1.000 F2000.000 
?%ETK[7]=4 
G1 X100.000 Z-1.000 F3000.000 
?%ETK[7]=0 
G0 Z20.000 
D0 
SVL 0.000 
VL6=0.000
SVR 0.000 
VL7=0.000
MLV=0
G0 G53 Z201.000
```

### `D0`

**Fuente:** `C:/Program Files (x86)/Scm Group/Xilog Plus/Cfg/mdi_gl01.ini`
  ·  **Sección:** [Comando 1 1] / [Iso 1 1] (panel MDI)
  ·  **Idioma:** codigo / italiano

```
[Comando 1 1]
immagine=DEFZP.BMP
input=0
tipo_cnc_input=2
[Iso 1 1]
G110 D0

[Comando 1 2]
immagine=DEFZM.BMP
input=0
tipo_cnc_input=2
[Iso 1 2]
G110 B0
```

### `D (instruccion) — PARECIDO, NO IDENTICO: en el manual la letra D es "declaracion de un alias", no seleccion de herramienta ni corrector`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/6.1_Programaci_n_param_trica.htm (ayuda Xilog Plus Editor, español)`
  ·  **Sección:** 6.1 Programación paramétrica — "D (declaración de un alias)" (entrada "D" del indice de palabras clave, anchor IX_D)
  ·  **Idioma:** español

```
D (declaración de un alias)

El alias tiene la misma función de una variable L: permite atribuir un valor numérico a una palabra utilizando una expresión. A diferencia de una variable L, un alias puede ser definido una sola vez dentro del programa. Los alias deben ser definidos inmediatamente tras los parámetros PAR, y se pueden utilizar hasta 64 en cada programa.

Grupo: instrucciones texto

Ejemplo:
Este ejemplo muestra la programación del alias ORY a 50*2. Ahora, el parámetro puede sustituir el número de una instrucción, como si fuera una variable L.
```

### `DO — PARECIDO, NO IDENTICO (letra O, no cero): "DO (inicio ciclo)"`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/6.2_Programaci_n_estructurada.htm (ayuda Xilog Plus Editor, español)`
  ·  **Sección:** 6.2.4 Realización y ejecución de un ciclo (anchor IX_DO)
  ·  **Idioma:** español

```
6.2.4 Realización y ejecución de un ciclo

DO (inicio ciclo)

OD (fin ciclo)

Grupo: instrucciones texto

EXIT (salida de un ciclo)
```

### `D — PARECIDO, NO IDENTICO: campo D de las instrucciones del .pgm = "Cota de fuera trabajo" / "Out machining quota"`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm y scratchpad/out_editor_ing/5.2_Basic_Instructions_(Text).htm`
  ·  **Sección:** 5.2 Instrucciones básicas (texto) — tabla de campos de las instrucciones (aparece repetido en varias instrucciones)
  ·  **Idioma:** español / inglés

```
Español:
S | Velocidad de rotación de la herramienta
D | Cota de fuera trabajo.
N | Nombre del perfil (v. campo N de la instrucción G0).

Inglés:
S | Rotation speed of tool.
D | Out machining quota.
N | Name of profile (see field N of instruction G0).

(otra tabla, misma pagina)
G | Number of chip discharge steps
D | Out machining quota.
T | List of tools; in case of various tools the coordinates X, Y refer to the first tool indicated.
```

### `correccion de herramienta — PARECIDO, NO IDENTICO: en el manual se programa con la instruccion C, no con D`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/5.2_Instrucciones_b_sicas_(texto).htm`
  ·  **Sección:** 5.2 Instrucciones básicas (texto) — "Corrección herramienta - C"
  ·  **Idioma:** español

```
Corrección herramienta - C

Habilita la corrección de la trayectoria del mandril en función de las características de la fresa montada. Si la fresa es de vela (tipo F), la corrección es igual al radio declarado en la herramienta, es decir, el "diámetro útil"; si la fresa es de disco (tipo D), la corrección es igual a la mitad del espesor de la hoja declarada en el equipamiento.

Grupo: instrucciones texto

Valores admitidos:
0 | Corrección nula.
1 | Corrección derecha.
2 | Corrección izquierda.
3 | Corrección en profundidad (sólo para fresas de disco).
13 | Corrección 1 + corrección 3 (sólo para fresas de disco).
23 | Corrección 2 + corrección 3 (sólo para fresas de disco).
```

### `nci.cfg / $GEN_INIT$ (unica mencion del archivo donde vive _paras en toda la ayuda)`  ⚠️ *parecido, no idéntico*

**Fuente:** `scratchpad/out_spa/9.13_Reglas_de_estacionamiento.htm y scratchpad/out_editor_ing/_APPENDIX.htm`
  ·  **Sección:** apartado sobre trabajos 3D y velocidad de envío de bloques ISO al CN
  ·  **Idioma:** español / inglés

```
Español: "Introducir en la clave $GEN_INIT$ del archivo de configuración nci.cfg el bloque: %%Bxx donde xx debe ser un número comprendido entre 5 y 20; el campo de validez de la instrucción está extendido a todos los programas, incluso a aquellos que no contienen trabajos 3D."

Inglés: "Insert block %%Bxx in the key $GEN_INIT$ of the configuration file nci.cfg, where xx must be a number between 5 and 20. The instruction validity range extends to all programs, even those which do not contain 3D machining."
```

**No aparece en ninguna fuente:** `_paras — NO APARECE en ninguna documentación: buscado (case-insensitive, con y sin guión bajo, con y sin paréntesis) en out_spa (1436 arch.), out_editor_ing (1434), out_epl (210), out_panelmac (271), out_scripting_es (324), out_winxiso_ing/spa/root, out_testine_spa, maestro_editor_es.txt, pdfs/ (maestro en-US, it-IT, de-DE), pgmx/docs/xilog_plus_pgm/ y pgmx/docs/maestro_scripting/. Cero coincidencias. Sólo aparece en archivos de la instalación (NCI.CFG, Park.pgm) y en los .iso generados.`, `%ax[n].pa[m] — NO APARECE en ninguna documentación: buscadas las variantes '%ax', 'ax[', 'ax[0].pa[', '.pa[', 'pa[' en las mismas 7 fuentes documentales. Cero coincidencias. Sólo en NCI.CFG, Park.pgm y los .iso generados.`, `pa[21] — NO APARECE en ninguna documentación (buscado 'pa[21]', 'pa[2', 'pa21' en las 7 fuentes documentales). Sólo en parax.str (mapeo AP_MINQUOTA), Park.pgm, NCI.CFG y los .iso.`, `pa[22] — NO APARECE en ninguna documentación (mismas búsquedas). Sólo en parax.str (mapeo AP_MAXQUOTA), Park.pgm, NCI.CFG y los .iso.`, `D0 — NO APARECE en ninguna documentación. Búsquedas '\bD0\b', 'D0', '[^A-Za-z0-9_]D0[^0-9]', 'D0=' en las 7 fuentes documentales: los únicos hits fueron falsos positivos dentro de GUIDs hexadecimales en out_scripting_es. En la instalación aparece sólo en mdi_gl01.ini ('G110 D0') y en los .iso generados.`, `instrucción D como selección de herramienta o corrector — NO APARECE con ese significado en ninguna fuente. El índice de la ayuda española sólo tiene 'D (declaración de un alias)' y 'DO (inicio ciclo)'; el campo D de las instrucciones del .pgm es 'Cota de fuera trabajo'; la corrección de herramienta se programa con la instrucción C.`, `tabla de parámetros de eje por índice en la DOCUMENTACIÓN — NO APARECE. Buscados 'axis parameter', 'par(á)metro(s) de eje', 'parametri asse' en las 7 fuentes documentales: cero coincidencias. Las únicas tablas de parámetros de eje por índice están en archivos de la instalación (parax.str, Axis.ini, axis.msg, Params.cfg, ConfigurationManager.xml), no en manuales.`, `G53 — NO APARECE en ninguna de las ayudas/manuales (búsqueda literal 'G53' en las 7 fuentes documentales: cero coincidencias), aunque sí en NCI.CFG, Park.pgm y los .iso.`, `ETK — NO APARECE en ninguna de las ayudas/manuales (los únicos hits fueron bytes coincidentes dentro de imágenes .jpg). Sí aparece en NCI.CFG y en los .iso.`
