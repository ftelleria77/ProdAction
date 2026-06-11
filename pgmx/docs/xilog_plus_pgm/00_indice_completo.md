 Xilog Plus
Para
perforadoras fresadoras del Grupo SCM
Manual de uso
y programaci�n del editor de Xilog Plus
v. 4.0� � Marzo 2008
c�d. 0000574270G
SCM GROUP

Este manual est�
dirigido a quienes desean conocer y usar las m�quinas perforadoras fresadoras del
Grupo SCM.
Las
informaciones contenidas en el manual son propiedad del Grupo SCM y no pueden
ser reproducidas o divulgadas sin autorizaci�n.
El Grupo SCM
declina cualquier responsabilidad por el uso no correcto de las informaciones
contenidas en el manual.
Realizzazione editoriale a cura di SCM GROUP � Ufficio S.i.T

�ndice de contenido
ĺndice de
instrucciones. 12
ĺndice. 14
1. Instalaci�n e
inicio.. 15
2. Configuraci�n.. 17
3. Introducci�n a la
programaci�n.. 19
4. Programaci�n
b�sica. 22
4.1 Equipamiento. 22
4.1.1 Editor de equipamiento. 22
4.1.2 Configuraci�n de las herramientas. 25
4.1.2.1 Herramientas fijas: ejemplo con
puntas de orificio. 25
4.1.2.2 Herramientas fijas: ejemplo con
hoja/disco. 27
4.1.2.3 Herramientas externas. 29
4.1.2.3.1 Ejemplo de una herramienta de tipo
F cil�ndrica. 29
4.1.2.3.2 Ejemplo de una herramienta de tipo
F perfilada. 31
4.1.2.3.3 Ejemplo de una herramienta de tipo
F montada sobre una transmisi�n angular 33
4.1.2.3.4 Ejemplo de una herramienta de tipo
F montada sobre una transmisi�n angular inclinada. 36
4.1.2.3.5 Ejemplo de una herramienta de tipo
D montada sobre una transmisi�n angular 39
4.1.2.3.6 Ejemplo de una herramienta de tipo
D montada sobre transmisi�n angular inclinada. 42
4.1.2.3.7 Ejemplo de una herramienta de tipo
L. 45
4.1.2.3.8 Ejemplo de una herramienta de tipo
M.. 47
4.1.2.3.9 Par�metros Generales. 49
4.1.2.4 Notas. 50
4.1.2.5 Grupo Hoja. 50
4.1.2.6 Grupo de Vaciado cerradura. 51
4.1.2.7 Grupo vertical 52
4.1.2.8 Perforadora sobre eje independiente. 52
4.1.2.9 Control de una �herramienta gruesa� 52
4.1.3 Campos significativos para el
optimizador de taladros. 53
4.1.4 Cambio de herramienta suplementario
(Tool Room) 54
4.1.5 Referencia a las herramientas en el
programa. 54
4.1.6 Visualizaci�n gr�fica cabezas
operadoras. 56
4.1.7 Configuraci�n de las cabezas. 57
4.1.8 Funci�n cortar - copiar - pegar
herramental para m�quinas multigrupo. 57
4.2 Programa. 58
4.2.1 Introducci�n a los programas de trabajo. 58
4.2.1.1 Estructura de un programa. 58
4.2.1.2 Editor de los programas. 59
4.2.1.3 Origen m�quina. 61
4.2.1.4 Areas de trabajo. 61
4.2.2 Editor de texto. 64
4.2.2.1 Interfaz. 64
4.2.2.2 Modalidad bloques. 70
4.2.2.3 Visualizaci�n gr�fica. 72
4.2.3 Editor gr�fico. 73
4.3 Mix de programas. 83
4.4 Programa m�ltiple. 85
4.4.1 Editor de los programas m�ltiples. 85
4.4.2 Subdivisi�n de la superficie en zonas
de trabajo. 90
4.4.3 Ejemplos. 91
5. Instrucciones de
programaci�n.. 93
5.1 Encabezamiento. 93
H (Encabezamiento, o
Header) 93
5.1.1 Palpaci�n panel y �martire� 98
5.2 Instrucciones b�sicas (texto) 99
5.2.1 Instrucciones operativas. 99
5.2.1.1 Funciones generales. 99
Entrada autom�tica en el perfil - GIN.. 99
Salida autom�tica del perfil - GOUT. 102
Repetici�n de un perfil - GREP.. 104
Modificar velocidad - GSET. 107
Rotaci�n del panel - ROT. 109
Instrucci�n ISO - ISO.. 110
Operaci�n nula - N.. 111
Palpaci�n panel - TA.. 112
5.2.1.2 Perforaciones. 113
Perforaci�n - B.. 113
Perforaci�n optimizada - BO.. 116
Perforaci�n inclinada - BR.. 118
5.2.1.3 Fresados. 120
Inicio fresado - G0. 120
Inicio fresado 3D - G03D (grupo Prisma) 122
Fresado lineal - G1. 123
Fresado lineal 3D - G13D (grupo Prisma) 124
Fresado circular horario - G2. 125
Fresado circular antihorario - G3. 127
Tramo tangente al tramo precedente - G5. 129
Inicio fresado con herramienta inclinada -
G0R.. 133
Fresado lineal con herramienta inclinada -
G1R.. 137
Fresado circular horario con herramienta
inclinada - G2R.. 139
Fresado circular antihoraria con herramienta
inclinada - G3R.. 141
Tramo tangente al tramo precedente con
herramienta inclinada - G5R�� 143
Conexi�n entre fresados - GFIL. 147
Chafl�n entre fresados - GCHA.. 150
5.2.2 Instrucciones modales. 152
Desplazamiento del
origen del tablero en tope - O.. 152
Cara de trabajo - F.. 153
Correcci�n
herramienta - C.. 155
Incremental en X - IX.. 156
Incremental en Y - IY. 156
Especular en X - SX.. 157
Especular en Y - SY. 157
Plano inclinado - PL. 159
Asigna un valor a
variable - SET. 162
Cambiar referencia -
REF.. 171
5.2.3 Instrucciones de gesti�n de
subprogramas. 172
Apertura de
subprograma - S.. 172
Subprograma
optimizado - SO.. 177
5.2.4 Env�o de mensajes al operador 178
Impresi�n mensaje -
MSG.. 178
5.2.5 Programaci�n de la mesa motorizada. 180
PB.. 180
5.2.6 Instrucciones de ayuda a la
programaci�n. 182
Comentario - ; 182
Visualizaci�n mensaje
- PRINT. 182
Memorizaci�n mensaje
- TRACE.. 183
5.3 Instrucciones completas (gr�ficas) 184
5.3.1 Instrucciones operativas. 184
5.3.1.1 Funciones generales. 184
Entrada autom�tica en el perfil - XGIN.. 184
Salida autom�tica desde perfil - XGOUT. 188
Repetici�n de un perfil - XGREP.. 192
Modificar velocidad - XGSET. 195
Operaci�n nula - XN.. 198
Palpaci�n tablero - XTA.. 199
5.3.1.2 Perforaciones. 200
Perforaci�n - XB.. 200
Perforaci�n optimizada - XBO.. 208
Perforaci�n inclinada - XBR.. 211
5.3.1.3 Fresado. 214
Inicio fresado - XG0. 214
Inicio fresado 3D - XG03D (grupo Prisma) 216
Segmento para dos puntos - XL2P.. 217
Fresado lineal 3D - XG13D (grupo Prisma) 222
Segmentos para tres puntos (o Dividida) - XSP.. 223
Arco dados dos puntos - XA2P.. 225
Arco dados 3 puntos - XA3P.. 231
Arco dado el radio - XAR.. 233
Arco dado el radio 2 - XAR2. 236
Tramo tangente al tramo precedente - XG5. 240
Arco de elipse - XEA.. 245
Inicio fresado con herramienta inclinada -
XG0R.. 260
Fresado lineal con herramienta inclinada -
XG1R.. 265
Fresado circular horario con herramienta
inclinada - XG2R.. 267
Fresado circular antihorario con herramienta
inclinada - XG3R.. 270
Tramo tangente al tramo precedente con
herramienta inclinada - XG5R�� 273
Conexi�n entre fresados - XGFIL. 278
Chafl�n entre fresados - XGCHA.. 281
5.3.2 Instrucciones modales. 283
Cambio origen - XO.. 283
F (Cara de trabajo) 285
C (Correcci�n del
radio de la herramienta) 286
K (Incremental) 287
P (Origen de
referencia) 288
Plano inclinado - XPL. 289
5.3.3 Instrucciones de gesti�n de los
subprogramas. 293
Apertura de
subprograma - XS.. 293
5.3.4 Env�o de mensajes al operador 298
Impresi�n mensaje -
XMSG.. 298
5.4 Macros usuario. 301
5.4.1 Macros usuario para trabajos para m�vil
(Windows XP) 301
Perforaci�n uni�n con
camlock - CAMLOCK.. 301
Barrera fitting -
FITTING_32. 302
Barrera fitting doble
- FITTING_32_D.. 303
Toe kick - TOEKICK.. 304
Perforaci�n de
conexi�n horizontal - UNIONE_O.. 305
Perforaci�n de
conexi�n vertical cara 1 - UNIONE_V.. 306
Perforaci�n placas de
bornes tipo 1 - BASET_1. 307
Doble perforaci�n
placa de bornes tipo 1 - BASET_1_D.. 308
Triple perforaci�n
placa de bornes tipo 1 - BASET_1_T. 309
Perforaci�n placa de
bornes tipo 2 - BASET_2. 310
Doble perforaci�n
placa de bornes tipo 2 - BASET_2_D.. 311
Triple perforaci�n
placa de bornes tipo 2 - BASET_2_T. 312
Perforaci�n bisagra
tipo 1 - CERNIE_1. 313
Doble perforaci�n
bisagra tipo 1 - CERNIE_1_D.. 314
Triple perforaci�n
bisagra tipo 1 - CERNIE_1_T. 315
Perforaci�n bisagra
tipo 2 - CERNIE_2. 316
Doble perforaci�n
bisagra tipo 2 - CERNIE_2_D.. 317
Triple perforaci�n
bisagra tipo 2 - CERNIE_2_T. 318
Perforaci�n bisagra
tipo 3 - CERNIE_3. 319
Doble perforaci�n
bisagra tipo 3 - CERNIE_3_D.. 320
Triple perforaci�n
bisagra tipo 3 - CERNIE_3_T. 321
Perforaci�n bisagra
tipo 4 - CERNIE_4. 322
Doble perforaci�n
bisagra tipo 4 - CERNIE_4_D.. 323
Triple perforaci�n
bisagra tipo 4 - CERNIE_4_T. 324
Perforaci�n bisagra
tipo 5 - CERNIE_5. 325
Doble perforaci�n
bisagra tipo 5 - CERNIE_5_D.. 326
Triple perforaci�n
bisagra tipo 5 - CERNIE_5_T. 327
Taladrado bisagra
tipo 6 - CERNIE_6. 328
Doble taladrado
bisagra tipo 6 - CERNIE_6_D.. 329
Triple taladrado
bisagra tipo 6 - CERNIE_6_T. 330
Soporte para colgante
- AGGANCIO_PP.. 331
Orificios para
fijaci�n de foco forma circular - FORI_FARETTO.. 332
Orificio para foco -
FORO_FARETTO_C.. 333
Orificio para foco
rectangular - FORO_FARETTO_R.. 334
Taladrado para gu�a
de los cajones - GUIDA_CASSETTI 335
Taladrado
pomo/manilla - MANIGLIA_1. 336
Punto de apoyo
manilla circular - MANIGLIA_C.. 337
Punto de apoyo
manilla rectangular - MANIGLIA_R.. 338
Canal para respaldo
direcci�n X - CANALE.. 339
Perfiladura pieza -
DESPERFILADO.. 340
5.4.2 Macros usuario para m�quinas Ergon. 341
Selecci�n sub-�reas
de bloqueo pieza - XSUBAREA.. 341
Selecci�n filas de
topes para sub-�reas de bloqueo pieza - XBATTON.. 341
Limpieza mesas con
cepillo - XCLEAN.. 343
Posicionamiento gu�as
motorizadas en el plano - XGUIDEM.. 343
Programaci�n de la
posici�n gu�a horizontal - XGUIDEH.. 344
Programaci�n
distancia en X entre cabezas para trabajo acoplado - XINTAX.. 345
Delta entre longitud
herramienta real y corregida por el palpador - XDELTAPALPATORE�� 345
Programaci�n Ciclos
L�ser - XLASERC.. 346
Seleci�n Ventosas ON/OFF - XSELCUPS.. 346
Movimento Planos a
Velocidad Controlada - XSLOW... 347
5.4.3 Macros usuario varios. 347
Soplo - XBLOWER.. 347
Taladrado m�ltiple -
XMULTIDRILL. 349
Operaci�n nula entre
trabajos - XNOP.. 350
Adquisici�n or�genes
y rotaci�n - XORGACQ.. 350
xT - XT. 351
TvOnOff - XTVONOFF.. 352
TVSIDE - XTVSIDE.. 353
Posicionamiento tapa
de aspiraci�n del plano - XHOODPLANE.. 353
Posicionamiento de la
tapa de aspiraci�n suplementaria en la cabeza - XHOODSUPP�� 355
Frenos - XBRAKE.. 358
Clavado - XNAIL. 358
Ciclo de descarga
pieza - PUNLOAD.. 361
6. Programaci�n
avanzada. 363
6.1 Programaci�n param�trica. 363
6.1.1 Introducci�n a la programaci�n
param�trica. 363
6.1.2 Instrucciones param�tricas. 365
PAR (declaraci�n
par�metro) 365
PARSECTION
(configuraci�n de una secci�n para los par�metros) 366
PPAR (configuraci�n
de los par�metros para subprograma o o macro) 367
L (atribuir un valor
a variable) 368
D (declaraci�n de un
alias) 369
6.2 Programaci�n estructurada. 370
6.2.1 Salto incondicionado. 370
6.2.2 Salto condicionado. 371
6.2.3 Realizaci�n y ejecuci�n de un bloque. 372
6.2.4 Realizaci�n y ejecuci�n de un ciclo. 377
6.2.5 Repetici�n de un ciclo. 380
6.3 Macros. 382
6.4 Pasaje de par�metros a subprogramas y
macros. 387
6.5 Programa ISO.. 391
6.6 Importaci�n de un archivo DXF.. 392
6.6.1 Proceso de importaci�n. 392
6.6.2 Layer 398
6.6.2.1 Layer dimensiones tablero. 398
6.6.2.2 Layer trabajos pant�grafo. 399
6.6.2.3 Layer orificios verticales. 399
6.6.2.4 Layer orificios horizontales. 399
6.6.3 Secciones DXF importables. 401
7. Optimizador de
programas. 402
8. Editor de mesas de
trabajo.. 406
8.1 Descripci�n de la interfaz. 406
8.2 Tipos de mesas. 408
8.2.1 Mesa de vigas y ventosas autom�tica. 408
8.2.2 Mesa de vigas y ventosas manual 408
8.2.3 Mesa de vigas y ventosas con motor 409
8.2.4 Mesa multifuncional 409
8.3 Programaci�n de la mesa. 410
8.3.1 Programaci�n de la mesa con el rat�n. 410
8.3.1.1 Mesa de vigas y ventosas. 410
8.3.1.2 Mesa multifuncional 415
8.3.2 Programaci�n de la mesa introduciendo
los datos desde el teclado. 417
8.3.3 Programaci�n de par�metros (mesa
motorizada travesa�os y ventosas) 420
8.3.3.1 Introducci�n a la programaci�n de
par�metros. 420
8.4 Gesti�n autom�tica de la barra m�vil 426
8.5 Memorizaci�n. 428
8.6 Tipos de soporte. 429
8.7 Otras funciones. 431
8.7.1 Modos de visualizaci�n. 431
8.7.2 Barra de propiedades. 432
8.7.3 Control antichoque. 433
8.7.4 Programaci�n autom�tica de las ventosas. 434
8.7.5 Adaptaci�n especular de la programaci�n
de la superficie. 438
8.7.5.1 Reglas con las cuales las Ventosas
son especularizadas. 441
8.7.5.2 Casos particulares. 443
8.7.5.3 Clave [NONSPEC] en Libsupp.cfg. 443
8.7.5.4 Esquema sin�ptico de especularizaci�n
ventosas. 446
8.7.6 Separador de grados. 450
8.7.7 Prohibiciones. 451
8.7.8 Reglas de desplazamiento y
especularizaci�n de las mesas travesa�os y ventosas. 452
8.7.8.1 Desplazamiento de los travesa�os. 452
8.7.8.2 Desplazamiento de los soportes (mesa
motorizada travesa�os y ventosas) 454
8.7.8.3 Restauro de configuraciones en �reas
diferentes. 454
8.7.8.4 Rotaci�n de las ventosas. 455
8.7.8.5 Simetr�a y especularizaci�n de las
ventosas. 458
8.7.8.5.1 Simetr�a de las ventosas. 458
8.7.8.5.2 Especularizaci�n de las ventosas. 460
8.7.8.5.3 Posicionamientos indeseados de los
soportes ventosa. 464
8.7.9 Control ciclos (mesa motorizada
travesa�os y ventosas) 466
8.7.10 Topes de fondo. 467
8.8 Descripci�n de los archivos. 469
8.9 Reglas de posicionamiento de los
travesa�os en las �reas. 471
9. Plano Motorizado.. 477
9.1 Instrucci�n PB.. 477
9.2 Descripci�n Fases. 478
Fase 1: preparaci�n plano (E = 1) 478
Fase 2: bloqueo pieza (E = 2) 478
Fase 3: posicionamiento intermedio (E = 3) 479
Fase 4: desbloqueo pieza mascarada� (E = 3) 479
Fase 5: desplazamiento con la pieza
bloqueada� (E = 4) 479
9.3 Campo V del HEADER(encabezamiento)
programa. 480
Bornes est�ndares con v�stago o platillo. 480
Bornes horizontales para trabajos marcos. 480
Ventosas. 481
9.4 Ejemplo de trabajo con bornes est�ndares. 481
Ejemplo 1: Bloqueo autom�tico. 481
Ejemplo 1: Elaboraci�n marco ventana. 488
9.5 Ejemplo de elaboraci�n con bornes
horizontales. 490
Ejemplo 1: Bloqueo autom�tico y
semi-autom�tico. 490
9.6 Ejemplo de elaboraci�n con ventosas. 491
Ejemplo 1 Bloqueo semi-autom�tico. 491
9.7 Visualizaci�n bloques de PB.. 494
Control colisi�n dispositivos bloqueo-recorrido
herramienta. 494
Control colisi�n dispositivo paleta-elementos
del plano. 496
Visualizaci�n bloqueo de bornes. 497
Selectores. 499
Programaci�n mediante ventosas. 500
Notas generales. 501
9.10 Preparaci�n del plano motorizado. 502
9.11 Autoaprendido. 505
9.12 Ojales. 507
Configuraci�n. 507
Programaci�n. 508
9.13 Reglas de estacionamiento. 509
Reglas de estacionamiento para barras no
programadas. 509
Reglas de estacionamiento de dispositivos no
programados. 511
AP�NDICE
A. Men� y barras de mandos. 513
Ventana principal, del editor de programas y
del editor de equipamientos. 513
Visualizaci�n gr�fica cabezas operadoras. 518
Visualizaci�n gr�fica. 518
Ambiente de importaci�n de los archivos DXF.. 519
Editor Mesas Trabajo. 520
AP�NDICE
B. Variables y expresiones. 524
AP�NDICE
C. Formatos de archivo. 530
Formatos. 530
Ventana para abrir y convertir archivos. 531
WinXiso. 531
AP�NDICE
D. Programaci�n de la campana de aspiraci�n. 535
AP�NDICE
E. Programaci�n de los topes m�viles. 537
AP�NDICE
F. M�quinas Ergon. 540
AP�NDICE
G. Grupo Universal (en RD220) con eje de rotaci�n paralelo al eje Y de la
m�quina� 552
AP�NDICE
H. Grupo Prisma. 556
AP�NDICE
I. Programaci�n de los sujetadores Duomatic. 559
AP�NDICE
J. Gesti�n del equipo del cliente. 562
AP�NDICE
K. Configuraci�n de los soportes y de los elementos de la mesa del Editor de
mesas de trabajo. 563
El archivo libsupp.cfg. 563
Introducci�n del n�mero de soportes/elementos
de la mesa disponibles. 563
Par�metros de configuraci�n. 563
AP�NDICE
L. Control de los cortes con hoja. 574
Configuraci�n de las herramientas. 574
Programaci�n. 575
Direcci�n de trabajo. 575
AP�NDICE
M. Funciones adicionales. 577
Calculadora. 577
Funciones de backup y restore. 577
AP�NDICE
N. Notas. 578
Gesti�n de los programas PGM.. 578
Gesti�n directa de los programas ISO.. 578
Acercamiento al trabajo. 579
Traslaciones sobre la mesa. 579
Selector NO EDIT. 580
AP�NDICE
O. Paleta (dispositivo transporta-virutas rotatorio) 580
Programaci�n. 580
Configuraci�n. 583
Gesti�n de paleta con Routolink Carpinter�a. 584
AP�NDICE
P. Tecno: elaboraciones de cabezas paralelas. 586
Generalidades. 586
Limitaciones. 586
Configuraci�n. 586
Programaci�n. 587
Prestaciones extra. 588
Descripci�n macro. 589
Ejemplo de programa. 590

ĺndice
de instrucciones

. (definici�n de etiqueta); 370; 371
; (comentario); 182
B; 113
BO; 116
BR; 118
C; 155; 286
D; 369
DO; 377
ELSE; 372
EXIT; 377
F; 153; 285
FI; 372
G0; 120
G03D; 122
G0R; 133
G1; 123
G13D; 124
G1R; 137
G2; 125
G2R; 139
G3; 127
G3R; 141
G5; 129
G5R; 143
GCHA; 150
GFIL; 147
GIN; 99
GOTO; 370
GOUT; 102
GREP; 104
GSET; 107
H; 93
IF; 371
IF EXIT; 377
IF REPEAT; 380
IF THEN; 372
ISO; 110
IX; 156
IY; 156
K; 287
L; 368
MSG; 178
N; 111
O; 152
OD; 377
P; 288
PAR; 365
PARSECTION; 366
PB; 180
PL; 159
PPAR; 367
PRINT; 182
REF; 171
REPEAT; 380
ROT; 109
S; 172
SET; 162
SO; 177
SX; 157
SY; 157
TA; 112
TRACE; 183
XA2P; 225
XA3P; 231
XAR; 233
XAR2; 236
XB; 200
XBATTON; 341
XBLOWER; 346; 347
XBO; 208
XBR; 211
XCLEAN; 343
XDELTAPALPATORE; 345
XEA; 245
XG0; 214
XG03D; 216
XG0R; 260
XG13D; 222
XG1R; 265
XG2R; 267
XG3R; 270
XG5; 240
XG5R; 273
XGCHA; 281
XGFIL; 278
XGIN; 184
XGOUT; 188
XGREP; 192
XGSET; 195
XGUIDEH; 344
XGUIDEM; 343
XINTAX; 345
XL2P; 217
XMSG; 298
XMULTIDRILL; 349
XN; 198
XNOP; 350
XO; 283
XORGACQ; 350
XPL; 289
XS; 293
XSP; 223
XSUBAREA; 341
XT; 351; 358
XTA; 199
XTVONOFF; 352
XTVSIDE; 353; 355

ĺndice

Backup; 579
Borne; 429
Calculadora; 579
Campana de aspiraci�n; 537
Control antichoque; 433
Duomatic; 561
DXF
importaci�n; 392; 401
layer dimensiones tablero; 398
layer orificios horizontales; 399
layer orificios verticales; 399
layer trabajos pant�grafo; 399
Editor
de equipamiento; 23
de los par�metros; 363
de mesas de trabajo; 406
de texto; 65
gr�fico; 73
macros; 382
Ergon; 94; 542
Grupo
de Vaciado cerradura; 52
Hoja; 51
Perforadora sobre eje independiente; 53
Prisma; 558
Universal; 554
vertical; 53
Junta; 430
Macros; 382
Mesa de trabajo
multifuncional; 409
vigas y ventosas autom�tica; 408
vigas y ventosas manual; 408
vigass y ventosas con motor; 409
Mix de programas; 83
Modulset; 430
Origen m�quina; 62
Programa m�ltiple; 85
Programaci�n
autom�tica de las ventosas; 434
con Xilog Plus; 20
instrucciones; 59
param�trica; 363
Tool Room; 55
Topes m�viles; 539
Ventosa; 429
Visualizadores de los travesa�os; 431