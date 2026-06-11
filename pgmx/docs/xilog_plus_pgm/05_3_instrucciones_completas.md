
# 5.3 Instrucciones completas (gr�ficas)
### 5.3.1 Instrucciones
operativas
#### 5.3.1.1 Funciones
generales
Entrada autom�tica en el perfil - XGIN
Define una
recta o un arco de c�rculo tangente al perfil en el punto de entrada. Tiene
efecto si se programa antes de una instrucci�n de inicio perfil (XG0).
Grupo:
instrucciones texto

Par�metros b�sicos:
G
Tipo de entrada: 1=recta, 2=arco (el arco es
v�lido s�lo cuando est� habilitada la compensaci�n del radio de la herramienta).
Se habilita la entrada con hoja en recta tangente.
Par�metros completos:
R
Factor de multiplicaci�n del radio de la
herramienta (por defecto=2).
Q
Tipo de acercamiento: 0=en cota, 1=en
bajada.
La velocidad de recorrido utilizada para el tramo de
entrada en el perfil es la siguiente:
- valor configurado para el inicio del perfil si en la instrucci�n de
inicio perfil (XG0) el campo V (velocidad de recorrido) est� programado con un
valor
- valor configurado en el par�metro �Velocidad G0/B (�)� de la
herramienta utilizada para el perfil, si en la instrucci�n de inicio perfil el
campo V (velocidad de recorrido) no est� programado
Ejemplos: formas para ejecutar una entrada
autom�tica.
1) Entrada lineal
vertical
2) Entrada en arco
vertical

3) Entrada lineal
inclinada
4) Entrada en arco
inclinada.
�ATENCI�N!
La
entrada autom�tica no est� habilitada si: C=3 o C=31 o bien C=32. Si C=0 y G=2,
el sentido de entrada del arco est� determinado por el signo de R
(positivo=arco horario; negativo=arco antihorario)

Salida autom�tica desde perfil - XGOUT
Define una
recta o un arco de c�rculo tangente al perfil en el punto de salida. Tiene
efecto si ha sido programada despu�s de la �ltima instrucci�n del perfil.
Grupo:
Operaciones en el perfil

Par�metros b�sicos:
G
Tipo de salida: 1=recta, 2=arco (el arco es
v�lido s�lo cuando est� habilitada la compensaci�n del radio de la
herramienta). Se habilita la salida con hoja en recta tangente (G=1).
Par�metros completos:
R
Factor de multiplicaci�n del radio de la
herramienta (por defecto=2)
Q
Tipo de alejamiento: 0=en cota, 1=en subida.
L
Sobreposici�n en el perfil. Si el valor de L
est� regulado en -1, el trabajo se realiza a lo largo de todo el �ltimo tramo
del perfil, si L vale -2, adem�s de asumir el comportamiento antes detallado,
la salida se realiza en forma perpendicular a la superficie del tablero (como
en la instrucci�n N), ignorando el valor del par�metro Q.
Ejemplos: formas de realizar una salida autom�tica.
1) Salida lineal vertical
�
2) Salida en arco vertical

3) Salida lineal inclinada
4) Salida en arco inclinada
�ATENCI�N!
La
salida autom�tica no est� habilitada si: C=3 o C=31, o bien C=32.

Repetici�n
de un perfil - XGREP
Efect�a la
repetici�n de un perfil. La instrucci�n GREP no est� influenciada por las
instrucciones SX y SY.
Grupo:
Operaciones en el perfil

Par�metros b�sicos:
N
Nombre del perfil (v. campo N de la
instrucci�n XG0).
X
Coordenada X del punto inicial del perfil u
offset X del perfil (v.Q).
Y
Coordenada Y del punto inicial del perfil u
offset Y del perfil (v. Q).
Z
Offset del perfil en profundidad Z.
Q
0 = cotas X,Y absolutas; 1 = offset.
T
Herramienta.
Par�metros completos
A
�ngulo de rotaci�n (origen m�quina
delantero: positivo en sentido antihorario; origen m�quina trasero: positivo
en sentido horario).
x
Cota x del centro de rotaci�n.
y
Cota y del centro de rotaci�n.
G
Inversi�n del sentido de recorrido
(0=NO,1=SI).
V
Velocidad de fresado.
S
Velocidad de rotaci�n de la herramienta.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
D
Cota de fuera trabajo.
s
Cota de sobremetal (s�lo intrucciones texto).
El ejemplo siguiente muestra el fresado de
formas del tablero de la figura (30 mm de espesor) con una herramienta llamada
E1, el perfilado interno del rect�ngulo A con una herramienta llamada E2, la
repetici�n del perfil A en la posici�n B con coordenadas absolutas, la
repetici�n del perfil A en la posici�n C con offset y la repetici�n del perfil
A en la posici�n D con offset e inversi�n de recorrido con una herramienta
llamada E3.
►Origen
m�quina trasero
H DX=600 DY=400 DZ=30 -A C=0 T=0 R=1 *MM
/�ANDREA� V10;encabezamiento
;fresado externo del tablero
XGIN Q=0 R=2 G=1 C=� (origen m�quina
delantero: C=1; origen m�quina
trasero: C=2); entrada autom�tica en el perfil
con recta en cota
XG0 X=0 Y=0 Z=� T=101 V=4000 S=18000 E=1
D=20;inicio perfil con fresado de formas
XL2P X=600
XL2P Y=400
XL2P X=0
XL2P Y=0
XGOUT Q=0 R=2 G=1 C=0;salida autom�tica del
perfil con recta en cota
;inicio trabajo rect�ngulo A
XGIN Q=1 R=2 G=1 F=1 C=0;entrada con recta en
bajada sin compensaci�n del radio XG0 X=150 Y=50 Z=� E=1 V=5 S=18000 D=20
N=�PRUEBA� T=101 inicio del perfil llamado �prueba�
XL2P X=250
XL2P Y=150
XL2P X=50
XL2P Y=50
XL2P X=150
XGOUT Q=1 R=2 G=1 L=10;salida del perfil con
recta inclinada
�
;repetici�n del rect�ngulo A llamado �prueba�
en la posici�n B con cotas absolutas
XGREP X=450 Y=50
Q=0 G=0 N=�PRUEBA�;misma herramienta y cota de trabajo
;repetici�n del rect�ngulo A llamado �prueba�
en la posici�n C con cota offset
XGREP Y=200 Q=1
G=0� N=�PRUEBA�;cotas con referencia al
punto inicial del primer rect�ngulo
�
;repetici�n del rect�ngulo A llamado �prueba�
en la posici�n D con cotas offset
XGREP X=300 Y=200
Q=1 G=1 N=�PRUEBA� T=103;herramienta E3 inversi�n de recorrido
XN X=0 Y=0 T=101 F=1;parada mandril en cero
m�quina y carga herramienta E1

Modificar velocidad - XGSET
La instrucci�n
XGSET describe algunas nuevas caracter�sticas de un perfil llamado con XGREP
sucesiva.
Grupo:
Fresado est�ndar

Par�metros:
V
Velocidad de avance.
T
Herramienta.
B�������� �����������
Tipo de perfil. El tipo de perfil B asocia
las caracter�sticas de la XGSET a la herramienta o al proceso activo al
momento de la interpretaci�n de la geometr�a.
B=1���� Fresado
(con herramienta de tipo fresa �F�)
B=2���� Corte
con hoja (con herramienta de tipo disco �D�)
Todos los par�metros de la instrucci�n son
opcionales.
La instrucci�n XGSET debe introducirse antes
de cualquier otra instrucci�n G de movimiento; la instrucci�n G de movimiento
influenciada por una XGSET asume las nuevas caracter�sticas durante una
repetici�n del perfil con XGREP.
La instrucci�n XGSET est� habilitada solamente
si la herramienta especificada es igual a la especificada en XGREP o bien si el
identificador del tipo de perfil est� representado por la herramienta activa
durante la repetici�n del perfil.
Ejemplos:
1.�������� XGSET
sin efecto puesto que la herramienta especificada en la XGREP no es 101
�.
XG0 X..Y.. Z.. V=1 S E T=101 N=�Prof�
G1 X.. Y.. Z.. V=5
XGSET V=10 T=101
G1 X.. Y.. Z.. V=6
�.
XGREP V=2 T=102 N=�Prof�
�.
2.�������� XGSET
significativa puesto que la herramienta especificada en la XGREP coincide con
la de la XGSET
�.
XG0 X.. Y.. Z.. V=1 S E T=101 N=�Prof�
G1 X.. Y.. Z.. V=5
XGSET V=10 T=102
G1 X.. Y.. Z.. V=6
�.
XGREP V=2 T=102 N=�Prof�
�.
3.�������� La
XGSET tiene efecto solamente si la herramienta E2 es una fresa
�.
XG0 X.. Y.. Z.. V=1 S E T=101 N=�Prof�
G1 X.. Y..
Z.. V=5
XGSET V=10
B=1
G1 X.. Y.. Z.. V=6
�.
XGREP V=2 T=102 N=�Prof�
�.
4.�������� La
XGSET tiene efecto solamente si E2 es una fresa (por la presencia de B=1)
�.
XG0 X.. Y.. Z.. V=1 S E T=101 N=�Prof�
G1 X.. Y.. Z..
V=5
XGSET V=10 T=101
B=1
G1 X.. Y.. Z..
V=6
�.
XGREP V=2 T=102
N=�Prof�
�.
Puesto que es posible repetir el perfil varias
veces, tambi�n es posible especificar varias XGSET antes de una instrucci�n XG
de movimiento. La repetici�n en curso determina la XGSET asociada a la
instrucci�n XG. Si existen XGSET repetitivas, se tiene en cuenta la �ltima.
5.
�.
XG0 X.. Y.. Z.. V=1 S E T=101 D N=�Prof�
G1 X.. Y.. Z..
V=5
XGSET V=10 T=102
XGSET V=15 T=103
G1 X.. Y.. Z.. V=6
�.
XGREP V=2 T=102 N=�Prof�; Tiene efecto s�lo la
XGSET con T=102
XGREP V=2 T=103 N=�Prof�; Tiene efecto s�lo la
XGSET con T=103
�.
6.
�.
XG0 X.. Y.. Z.. V=1 S E T=101 D N=�Prof�
G1 X.. Y.. Z..
V=5
XGSET V=10 T=102
XGSET V=15 T=103
XGSET V=20
B=1
G1 X.. Y.. Z.. V=6
�.
XGREP V=2 T=102 N=�Prof�; si E2 y E3 son
fresas la instrucci�n XGSET
XGREP V=2 T=103 N=�Prof�; con B=1 las XGSET
precedentes no tienen efecto
�.

Operaci�n nula - XN
Apaga las
rotaciones y coloca los electromandriles en posici�n de reposo.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Posici�n del cabezal en el eje X.
Y
Posici�n del cabezal en el eje Y.
Q
El significado del campo Q es el siguiente:
si no est� programado o vale 0, las cotas X e Y se refieren al cero m�quina;
si est� programado a 1, las cotas X e Y se refieren al cero tablero.
T
N�mero de una herramienta externa.
Par�metros completos:
V
Velocidad de desplazamiento.
S
Velocidad de rotaci�n de la herramienta El
significado del campo S es el siguiente: si no est� programado o vale 0 los
mandriles se apagan; si est� programado a 1 los mandriles permanecen
encendidos.
Las cotas X e Y se refieren al cero m�quina;
la herramienta especificada en el campo T se toma del almac�n de herramientas.

Palpaci�n tablero - XTA
La palpaci�n es
una operaci�n que permite detectar irregularidades en los tableros y corregir
consecuentemente las elaboraciones.
Grupo:
Funciones principales

Par�metros:
X
Coordenada X del punto a palpar referido al
lado corriente (de 1 a 5).
Y
Coordenada Y del punto a palpar referido al
lado corriente (de 1 a 5).
Q
Define el tipo de palpaci�n.

(default)
El cabezal sube hasta el final de carrera +
de Z.

0
El cabezal sube hasta el final de carrera +
de Z.

1
El cabezal permanece a la cota Z de la
palpaci�n.

2
El cabezal sube hasta la cota de rozamiento
sobre la pieza.

G
Controla la subida del cabezal despu�s de la
palpaci�n.

(default)
Palpaci�n de las caras del tablero.

0
Palpaci�n de las caras del tablero.

1
Palpaci�n de un punto del panel.

T
Herramienta.
Tras haber detectado la diferencia (D) entre
dimensi�n real del tablero y dimensi�n te�rica, la palpaci�n modifica el
comportamiento del control num�rico en relaci�n con el lado sobre el cual ha
sido efectuada:
Cara 1: D se suma alg�bricamente a la
dimensi�n Z del tablero (DZ)
Cara 2: D se suma alg�bricamente a la
dimensi�n X del tablero (DX)
Cara 3: D se suma alg�bricamente al offset X
del tablero (BX)
Cara 4: si la cara est� opuesta al tope, D se
suma alg�bricamente a la dimensi�n Y del tablero (DY); en caso contrario, D se
suma alg�bricamente al offset Y del tablero (BY)
Cara 5: la misma regla que en la Cara 4
Una o varias palpaciones generalmente
determinan una variaci�n en las dimensiones (te�ricas) del tablero
especificadas en la instrucci�n H; las nuevas dimensiones (reales) se memorizan
en las variables @DX, @DY y @DZ que pueden ser utilizadas en la param�trica;
asimismo, las dimensiones reales se utilizan autom�ticamente cuando los trabajos
son programados con las instrucciones de especularidad SX y SY; para terminar,
se permite palpar varias caras antes de llevar a cabo los trabajos. Para leer
la traslaci�n de la pieza respecto al tope pueden utilizarse las variables
predefinidas @BX, @BY, @BZ.
En caso de palpaci�n de un punto del panel (G
= 1), las coordenadas del punto palpado quedan memorizadas en las variables @X,
@Y y @Z.
Ejemplos:
H DX1000 DY800 DZ20 �A /DEF
F 2
XTA X10 Y400 T91
F 3
XTA X10 Y500 T91
F 1
XB X100 Y400 Z8 T2
XB X = @DX -50 Y500 Z8 T2
SX 1
XB X200 T1
#### 5.3.1.2 Perforaciones
Perforaci�n - XB
Ejecuta uno o
m�s orificios.
Grupo:
Perforaci�n

Par�metros b�sicos:
X
Coordenada X del primer orificio.
Y
Coordenada Y del primer orificio.
Z
Profundidad de los orificios.
R
N�mero de orificios programados (incluido el
orificio de origen).
x
Paso en X para las repeticiones.
y
Paso en Y para las repeticiones.
T
Lista de las herramientas; en caso de varias
herramientas las coordenadas X, Y se refieren a la primera herramienta
indicada.
Q
Repetici�n de los orificios seg�n el
especular en X/Y (0=No, 1=SX, 2=SY, 3=SXSY).
Par�metros completos:
V
Velocidad de perforaci�n.
S
Velocidad de rotaci�n de la herramienta.
G
N�mero de pasos para descarga de virutas.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
D
Cota de fuera trabajo.
a
Offset del cabezal de perforaci�n flotante
en Y (eje E, s�lo si est� presente).

Ejemplos:
1) Programaci�n de un orificio.
Los par�metros X, Y, Z, T, F son obligatorios
para realizar un orificio. La posibilidad de realizar un orificio con descarga
de virutas se activa mediante el par�metro G=n�mero de pasadas (se divide en
partes iguales).
►Origen
m�quina delantero

►Origen m�quina
trasero
2) Programaci�n de una secuencia de orificios
Los par�metros X, Y, Z, R, x, y, T, F son
obligatorios para realizar una secuencia de orificios. Programar el primer
orificio con coordenadas X=9, Y=9, Z=..; el segundo con coordenadas X=9, Y=41,
Z=.. se programa con R=n�mero de orificios, y=32 (distancia entre el primer
orificio y el segundo).
►Origen
m�quina delantero �
►Origen
m�quina trasero
�����������
3)
Programaci�n de dos orificios y del especular en X.
Los par�metros X, Y, Z, R, x, y, T, Q, F son
obligatorios para ejecutar dos orificios y el especular en X. Programar el
primer orificio con coordenadas X=9, Y=9, Z=..;� el segundo con coordenadas X=9, Y=41, Z=.. se programa con
R=n�mero de orificios, y=32 (distancia entre el primer orificio y el segundo) y
su especular con Q=1.
►Origen
m�quina delantero �
►Origen
m�quina trasero
4) Programaci�n de dos orificios y del
especular en Y.
Los par�metros X, Y, Z, R, x, y, T, Q, F son
obligatorios para ejecutar dos orificios y el especular en Y. Programar el
primer orificio con coordenadas X=9, Y=9, Z=..;� el segundo con coordenadas X=9, Y=41, Z=.. se programa con
R=n�mero de orificios, y=32 (distancia entre el primer orificio y el segundo) y
su especular con Q=2.
►Origen
m�quina delantero �
► Origen m�quina trasero
5)
Programaci�n de dos orificios y del especular en X, Y.
Los par�metros X, Y, Z, R, x, y, T, Q, F son
obligatorios para ejecutar dos orificios y el especular en X, Y. Programar el
primer orificio con coordenadas X=9, Y=9, Z=..;� el segundo con coordenadas X=9, Y=41, Z=.. se programa con
R=n�mero de orificios, y=32 (distancia entre el primer orificio y el segundo) y
su especular con Q=3.
►Origen
m�quina delantero
►Origen
m�quina trasero
6) Programaci�n de un serie de orificios con
la perforadora en paso 32 utilizando varios husos.
Los par�metros X, Y, Z, T, F son obligatorios.
Programar el primer orificio; para programar el resto a una distancia de 32mm,
hay que seleccionar varios husos mediante el par�metro T (entre un n�mero y
otro hay que dejar un espacio).
►Origen
m�quina delantero �
►Origen
m�quina trasero

Perforaci�n optimizada - XBO
Realiza uno o
varios orificios sirvi�ndose del algoritmo de optimizaci�n de las
perforaciones. Todas las instrucciones XBO programadas en sucesi�n entran en la
misma secci�n de optimizaci�n; en un programa pueden existir varios bloques de
instrucciones XBO.
Grupo:
Perforaci�n

Par�metros b�sicos:
X
Coordenada X del primer orificio.
Y
Coordenada Y del primer orificio.
Z
Profundidad de los orificios.
D
Di�metro de los orificios.
R
N�mero de orificios programados (incluido el
orificio de origen).
x
Paso en X para las repeticiones.
y
Paso en Y para las repeticiones.
N
Tipo de broca de perforaci�n (P=plana,
L=lanza, S=avellanada).
Par�metros complejos:
L
Altura avellanador (s�lo si N=S).
V
Velocidad de perforaci�n.
G
N�mero de pasos para descarga de virutas.
Ejemplos:
1) Programaci�n de un orificio
Los par�metros X, Y, Z, D, N, F son
obligatorios para realizar un orificio.
►Origen
m�quina delantero �
►Origen
m�quina trasero
2) Programaci�n de una serie de orificios
Los par�metros X, Y, Z, R, x, y, D, N, F son
obligatorios para programar una serie de orificios. Programar el primer
orificio, los orificios restantes se programan mediante R=n�mero de
repeticiones (incluido el orificio de origen), x=distancia entre los orificios
(puede ser distinta de 32mm).
►Origen
m�quina delantero �
►Origen
m�quina trasero

Perforaci�n
inclinada - XBR
Permite efectuar uno o varios orificios inclinados respecto de la forma
ortogonal de la superficie de trabajo. La instrucci�n XBR se refiere siempre a la cara 1, por ello la cara
corriente debe ser siempre esa.
Grupo:
Perforaci�n

Par�metros b�sicos:
X
Coordenada X del primer orificio.
Y
Coordenada Y del primer orificio.
Z
Profundidad de los orificios.
H
Altura del orificio desde la mesa de trabajo
(cota a la que debe bajar la herramienta con referencia a la mesa de trabajo
de la m�quina). Si no se programa vale DZ.
A
�ngulo de rotaci�n de la perforaci�n (origen
m�quina delantero: positivo en sentido antihorario; origen m�quina trasero:
positivo en sentido horario).
T
Lista de las herramientas; en caso de varias
herramientas las coordenadas X, Y se refieren a la primera herramienta
indicada.
B
Angulo de inclinaci�n de la herramienta
respecto a la vertical (s�lo para el grupo Prisma).
Par�metros completos:
Q�������� �����������
Si el �ngulo A vale 0, se suma
alg�bricamente al offset R de la herramienta. Si el �ngulo A vale 1,
sustituye el offset R de la herramienta.
V
Velocidad de perforaci�n.
S
Velocidad de rotaci�n de la herramienta.
G
N�mero de pasos para descarga virutas.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
D
Cota de fuera trabajo.
Ejemplo:
Programaci�n de un orificio con par�metro Q=1
►Origen
m�quina delantero �

►Origen
m�quina trasero
�ATENCI�N!
Dado
que si las elaboraciones con las herramientas inclinadas no se encuentran
perfectamente programadas pueden provocar da�os a la estructura de la m�quina,
es oportuno efectuarlas antes EN MODO SIMULADO.

#### 5.3.1.3 Fresado
Inicio
fresado - XG0
Define el punto
inicial de un perfil.
Grupo:
Fresaso est�ndar

Par�metros b�sicos:
X
Coordenada X de inicio del perfil.
Y
Coordenada Y de inicio del perfil.
Z
Profundidad de inicio del perfil.
T
Herramienta.
Par�metros complejos:
N
Nombre del perfil (v. XGREP).
V
Velocidad de entrada de la pieza.
S
Velocidad de rotaci�n de la herramienta.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
D
Cota de fuera trabajo.
s
Cota de sobremetal (s�lo intrucciones
texto).
Ejemplo:
►Origen
m�quina delantero �
►Origen
m�quina trasero

Inicio fresado 3D - XG03D (grupo Prisma)
Permite empezar
un fresado lineal en un plano inclinado con respecto a la ortogonalidad de las
superficies del tablero; controla la entrada/salida de la herramienta en la
pieza imaginando una profundidad de trabajo nula. No admite XGIN/XGOUT; no se
puede introducir la campana. Puede utilizarse s�lo con el grupo Prisma,
�nicamente con el lado 1 activo y con la correcci�n del radio desactivada.
V�ase: Ap�ndice H - Grupo Prisma.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de inicio perfil.
Y
Coordenada Y de inicio perfil.
Q
�ngulo de rotaci�n alrededor del eje Z.
R
�ngulo de rotaci�n alrededor del eje X.
H
Altura del trabajo desde la mesa de trabajo
(cota a la que debe descender la herramienta referida a la mesa de trabajo de
la m�quina; si no ha sido programada vale DZ).
T
Herramienta.
Par�metros completos:
N
Nombre del perfil (v. XGREP).
V
Velocidad de fresado.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
S
Velocidad de rotaci�n de la herramienta.
D
Cota de fuera de trabajo (s�lo con Q y R no
programados).
Segmento para dos puntos - XL2P
Define un
segmento de recta.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de fin de segmento.
Y
Coordenada Y de fin de segmento.
Z
Profundidad de fin de segmento.
Par�metros completos:
L
Longitud del segmento.
B
�ngulo del segmento con respecto al eje X
(origen m�quina delantero: positivo en sentido antihorario; origen m�quina
trasero: positivo en sentido horario).
A
�ngulo de rotaci�n (origen m�quina
delantero: positivo en sentido antihorario; origen m�quina trasero: positivo
en sentido horario).
V
Velocidad de fresado.
Valen las siguientes combinaciones:
1) cota X (Y=�ltimo valor programado);
2) cota Y (X= �ltimo valor programado);
3) cota X y cota Y;
4) �ngulo B y una de las dos cotas X e Y;
5) �ngulo B y longitud L.
�ATENCI�N!
Si
se programa la longitud L sin el �ngulo B, �ste vale 0 grados.

Ejemplo:
Programaci�n de un segmento con punto inicial
X=100, Y=50. El punto inicial de fresado se toma de la instrucci�n precedente.
Con
coordenadas cartesianas� X, Y, Z.
►Origen
m�quina delantero �

►Origen
m�quina trasero
Con
coordenadas polares B, L, Z.
►Origen
m�quina delantero �

►Origen
m�quina trasero
Con
coordenadas mixtas B
y
una coordenada cartesiana X o Y.
►Origen
m�quina delantero �
►Origen
m�quina trasero

Fresado lineal 3D - XG13D (grupo Prisma)
Permite realizar
un fresado lineal en un plano inclinado con respecto a la ortogonalidad de las
superficies del tablero. Puede utilizarse s�lo con el grupo Prisma, �nicamente
con el lado 1 activo y con la correcci�n del radio desactivada. V�ase: Ap�ndice H - Grupo Prisma.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de final del tramo.
Y
Coordenada Y de final del tramo.
H
Altura del trabajo respecto a la mesa de
trabajo (cota a la que descender la herramienta referida a la mesa de trabajo
de la m�quina; si no ha sido programada vale DZ).
Q
�ngulo de rotaci�n alrededor del eje Z.
R
�ngulo de rotaci�n alrededor del eje X.
Par�metros completos:
V
Velocidad de fresado.

Segmentos para tres puntos (o Dividida) - XSP
Define dos
segmentos de recta.
Grupo:
Fresado complejo

Par�metros:
X
Coordenada X de fin de segundo segmento.
Y
Coordenada Y de fin de segundo segmento.
Z
Profundidad de fin de segundo segmento.
A
�ngulo de rotaci�n (origen m�quina
delantero: positivo en sentido antihorario; origen m�quina trasero: positivo
en sentido horario).
V
Velocidad de fresado.
B
�ngulo del primer segmento con respecto al
eje X (origen m�quina delantero: positivo en sentido antihorario; origen m�quina
trasero: positivo en sentido horario).
D
�ngulo del segundo segmento con respecto al
eje X (origen m�quina delantero: positivo en sentido antihorario; origen
m�quina trasero: positivo en sentido horario).
Los par�metros X, Y, B, D son obligatorios.
Ejemplo:
►Origen
m�quina delantero �
Programaci�n de dos segmentos con punto
inicial X=400, Y=300. El punto inicial de fresado se toma de la instrucci�n
precedente.
►Origen
m�quina trasero
Programaci�n de dos segmentos con punto
inicial X=400, Y=300. El punto inicial de fresado se toma de la instrucci�n
precedente.

Arco dados dos puntos - XA2P
Define un arco
de c�rculo dados dos puntos.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de fin de arco.
Y
Coordenada Y de fin de arco.
Z
Profundidad de fin de arco.
I
Coordenada X del centro de la
circunferencia.
J
Coordenada Y del centro de la
circunferencia.
G
Sentido de recorrido: 2=horario,
3=antihorario.
Par�metros complejos:
L
Longitud del arco: 1=menor, 2=mayor.
B
�ngulo del arco.
A
�ngulo de rotaci�n (origen m�quina
delantero: positivo en sentido antihorario; origen m�quina trasero: positivo
en sentido horario).
V
Velocidad de fresado.
Los par�metros I, J, G son obligatorios.
Adem�s debe programarse una de las siguientes combinaciones de par�metros:
1) �ngulo B;
2) cotas finales X e Y;
3) cota final X (como cota Y final se
considera la corriente);
4) cota final Y (como cota X final se
considera la corriente);
5) cota X y largo L;
6) cota Y y largo L.
Ejemplos:
►Origen
m�quina delantero �
1) Programaci�n de fresado circular con punto
inicial X=100, Y=50. El punto inicial de fresado se toma de la instrucci�n
precedente.

2) Programaci�n de fresado circular horario
(circunferencia) con punto inicial X=100 Y=150. El punto inicial de fresado se
toma de la instrucci�n precedente.

►Origen
m�quina trasero
1) Programaci�n de fresado circular horario
con punto inicial X=100, Y=50. El punto inicial de fresado se toma de la instrucci�n
precedente.

2) Programaci�n de fresado circular horario
(circunferencia) con punto inicial X=100 Y=150. El punto inicial de fresado se
toma de la instrucci�n precedente.

Arco dados 3 puntos - XA3P
Define un arco
de c�rculo dados tres puntos. La profundidad del punto intermedio puede ser
diferente de la del punto final.
Grupo:
Fresado complejo

Iniciando en el punto corriente, se realiza un
fresado circular por el punto de coordenadas (x, y, H) hasta el extremo de
coordenadas (X, Y, Z). Es necesario programar los siguientes datos: x, cota X
del punto intermedio; y, cota Y del punto intermedio; X, cota X del punto final
e Y, cota Y del punto final. La cota H puede omitirse; en este caso toda la
operaci�n de fresado se realiza a la misma profundidad de trabajo Z. Los
par�metros X, Y, x, y son obligatorios.
Par�metros:
X
Coordenada X de fin de arco.
Y
Coordenada Y de fin de arco.
Z
Profundidad de fin de arco.
A
�ngulo de rotaci�n (origen m�quina
delantero: positivo en sentido antihorario; origen m�quina trasero: positivo
en sentido horario).
H
Profundidad intermedia.
V
Velocidad de fresado.
x
Coordenada X intermedia.
y
Coordenada Y intermedia.
Ejemplo:
Programaci�n de fresado circular por tres
puntos con punto inicial X=100, Y=50. El punto inicial de fresado se toma de la
instrucci�n precedente.

►Origen
m�quina delantero �
►Origen
m�quina trasero

Arco dado el radio - XAR
Define un arco
de c�rculo dado el radio. El radio r puede tener valores positivos y negativos.
Si el radio es positivo, el centro cae a la izquierda de la l�nea imaginaria
que va desde el punto inicial al punto final del arco, de otro modo el centro
cae a la derecha de dicha l�nea.
Grupo:
Fresado est�ndar

Par�metros base:
X
Coordenada X de fin de arco.
Y
Coordenada Y de fin de arco.
Z
Profundidad de fin de arco.
r
Radio.
G
Sentido de recorrido: 2=horario,
3=antihorario.
Par�metros completos:
A
�ngulo de rotaci�n (origen m�quina
delantero: positivo en sentido antihorario; origen m�quina trasero: positivo
en sentido horario).
V
Velocidad de fresado.
Los par�metros X, Y, r, G son obligatorios
Ejemplos:
1) Programaci�n de fresado circular horario
con punto inicial X=100, Y=50 (arco de c�rculo con centro a la derecha de la
cuerda). El punto de inicial del fresado se toma de la instrucci�n precedente.
►Origen
m�quina delantero �
►Origen
m�quina trasero
2) Programaci�n de fresado circular
antihorario con punto inicial X=200, Y=150 (arco de c�rculo con el centro a la
izquierda de la cuerda). El punto inicial de fresado se toma de la instrucci�n
precedente.
►Origen
m�quina delantero �
►Origen
m�quina trasero

Arco dado el radio 2 - XAR2
Define un arco
de c�rculo dado el radio. El radio r puede tener valores positivos y negativos.
Si el radio es positivo, se considera siempre el arco de menor longitud, de lo
contrario, se toma el arco de mayor longitud.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de fin de arco.
Y
Coordenada Y de fin de arco.
Z
Profundidad de fin de arco.
r
Radio.
G
Sentido de recorrido: 2=horario,
3=antihorario.
��������������������������������������������������������������������
Par�metros complejos:
A
�ngulo de rotaci�n (origen m�quina
delantero: positivo en sentido antihorario; origen m�quina trasero: positivo
en sentido horario).
V
Velocidad de fresado.
����������������������������������
Los par�metros X, Y, r, G son obligatorios.
Ejemplos:
►Origen
m�quina delantero �
1) Programaci�n de fresado circular horario
con punto inicial X=200, Y=50 (arco de c�rculo inferior a 180�). El punto
inicial de fresado se toma de la instrucci�n precedente.
2) Programaci�n de fresado circular horario
con punto inicial X=200, Y=50 (arco de c�rculo superior a 180�). El punto
inicial de fresado se toma de la instrucci�n precedente.
►Origen
m�quina trasero
1) Programaci�n de fresado circular horario
con punto inicial X=200, Y=50 (arco de c�rculo inferior a 180�). El punto
inicial de fresado se toma de la instrucci�n precedente.
2) Programaci�n de fresado circular horario
con punto inicial X=200, Y=50 (arco de c�rculo superior a 180�). El punto
inicial de fresado se toma de la instrucci�n precedente.

Tramo tangente al tramo precedente - XG5
Define un tramo
de fresado tangente al tramo precedente.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de fin de fresado (s�lo si G=2
o bien G=3).
Y
Coordenada Y de fin de fresado (s�lo si G=2
o bien G=3).
Z
Profundidad de fin de fresado.
Par�metros completos:
G
Tipo de tangente:

1
Segmento a favor del sentido de recorrido
del tramo precedente.

-1
Segmento opuesto al sentido de recorrido del
tramo precedente.

2
Fresado circular horario.

3
Fresado circular antihorario.

V
Velocidad de fresado.
L
Longitud del segmento (s�lo si G = 1 o bien
G = -1).
Los par�metros X, Y, G, L son obligatorios.
Ejemplos:
1) Programaci�n de un tramo de fresado lineal
tangente a un arco a favor del sentido de recorrido. El punto inicial de
fresado se toma de la instrucci�n precedente. Los par�metros L, G son
obligatorios.
►Origen
m�quina delantero �
►Origen
m�quina trasero
2) Programaci�n de un tramo de fresado lineal
tangente a un arco en sentido opuesto al de recorrido. El punto inicial de
fresado se toma de la instrucci�n precedente. Los par�metros L, G son
obligatorios.
►Origen
m�quina delantero �
►Origen m�quina
trasero
3) Programaci�n de un tramo de fresado
circular horario tangente a un tramo precedente. El punto inicial de fresado se
toma de la instrucci�n precedente. Los par�metros X, Y, G son obligatorios.
►Origen
m�quina delantero �
►Origen m�quina
trasero
4) Programaci�n de un tramo de fresado
circular antihorario tangente a un tramo precedente. El punto inicial de
fresado se toma de la instrucci�n precedente. Los par�metros X, Y, G son
obligatorios.
►Origen
m�quina delantero �
►Origen
m�quina trasero

Arco de elipse - XEA
Define un arco
de elipse generando la instrucci�n de inicio de fresado.
Grupo:
Fresado complejo

Par�metros:
X
Coordenada X del centro de la elipse.
Y
Coordenada Y del centro de la elipse.
Z
Profundidad de fresado.
A
�ngulo de rotaci�n con respecto al centro
(origen m�quina delantero: positivo en sentido antihorario; origen m�quina
trasero: positivo en sentido horario).
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
V
Velocidad de entrada en la pieza.
S
Velocidad de rotaci�n de la herramienta.
Q
N�mero de arcos de c�rculo con los cuales
aproximar la elipse para cuadrante.
R
�ngulo respecto al eje X del punto inicial
(origen m�quina delantero: positivo en sentido antihorario; origen m�quina
trasero: positivo en sentido horario).
a
Velocidad de avance.
B
�ngulo respecto al eje X del punto final
(origen m�quina delantero: positivo en sentido antihorario; origen m�quina
trasero: positivo en sentido horario).
I
Longitud del semieje menor.
G
Sentido de recorrido del arco: 2=horario,
3=antihorario.
L
Longitud del semieje mayor.
T
Herramienta.
Los par�metros X, Y, R, B, l, L, G son
obligatorios. El par�metro I no puede ser mayor que el par�metro L.
�ATENCI�N!
La macro XEA es una aproximaci�n geom�trica
para arcos de una curva el�ptica. Los �ngulos inicial y final se refieren a la
circunferencia que circunscribe el arco de elipse por lo tanto corresponden
perfectamente a los representados por las perpendiculares a las tangentes solo
la elipse en los puntos de intersecci�n con los ejes cartesianos: 0, 90, 180,
270. Para los dem�s casos en los cuales es necesario que correspondan los
puntos inicial o final del arco de elipse con el punto inicial o final de otro
trabajo hay que corregir manualmente los �ngulos de modo que se obtenga el
resultado deseado.

Ejemplos:
1) Programaci�n de una elipse completa en
sentido horario con punto inicial hacia X positivo
►Origen
m�quina delantero �
►Origen
m�quina trasero

2) Programaci�n de una elipse completa en
sentido horario con punto inicial hacia X positivo, pero girada a 90 grados. Se
programa en horizontal y se gira mediante el par�metro �rotaci�n (A)�.
►Origen
m�quina delantero �
►Origen
m�quina trasero

3) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia X negativo y punto final hacia X
positivo.
►Origen
m�quina delantero
►Origen
m�quina trasero

4) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia X positivo y punto final hacia X
negativo, pero girada a 180 grados. Se programa en horizontal y se gira
mediante el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
► Origen m�quina trasero

5) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia Y negativo y punto final hacia Y
positivo, pero girada a 90 grados. Se programa en horizontal y se gira mediante
el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
�
► Origen m�quina trasero

6) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia Y positivo y punto final hacia Y
negativo, pero girada a 270 grados. Se programa en horizontal y se gira
mediante el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
► Origen m�quina trasero
7) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia X negativo y punto final hacia X
positivo.
►Origen
m�quina delantero
►Origen
m�quina trasero

8) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia X positivo y punto final hacia X
negativo, pero girada a 180 grados. Se programa en horizontal y se gira
mediante el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
► Origen m�quina trasero

9) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia Y negativo y punto final hacia Y
positivo, pero girada a 90 grados. Se programa en horizontal y se gira mediante
el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
�
► Origen m�quina trasero

10) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia Y positivo y punto final hacia Y
negativo, pero girada a 270 grados. Se programa en horizontal y se gira
mediante el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
► Origen m�quina trasero
11) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia X negativo y punto final hacia X
positivo.
►Origen
m�quina delantero
►Origen m�quina
trasero

12) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia X positivo y punto final hacia X
negativo, pero girada a 180 grados. Se programa en horizontal y se gira
mediante el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
► Origen m�quina trasero

13) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia Y negativo y punto final hacia Y
positivo, pero girada a 90 grados. Se programa en horizontal y se gira mediante
el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
�
► Origen m�quina trasero

14) Programaci�n de un arco de elipse en
sentido horario con punto inicial hacia Y positivo y punto final hacia Y
negativo, pero girada a 270 grados. Se programa en horizontal y se gira
mediante el par�metro �rotaci�n (A)�.
► Origen m�quina delantero
► Origen m�quina trasero

Inicio fresado con herramienta inclinada - XG0R
Permite
comenzar el fresado con una herramienta inclinada sobre un plano no ortogonal a
las superficies del panel. La instrucci�n XG0R se refiere siempre a la cara 1,
por ello la cara corriente debe ser siempre esa.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de inicio del perfil.
Y
Coordenada Y de inicio del perfil.
Z
Profundidad de inicio del perfil (medida
seg�n la inclinaci�n de la herramienta).
H
Altura de trabajo desde la mesa de trabajo
(cota a la que debe bajar la herramienta con referencia a la mesa de trabajo
de la m�quina). Si no se programa vale DZ.
T
Herramienta.
B
Angulo de inclinaci�n de la herramienta
respecto a la vertical (s�lo para el grupo Prisma).
�����������������������������
Par�metros completos:
N
Nombre del perfil (v. XGREP).
I
Lado de entrada (0, 1, 2, 3, 4).
S
Velocidad de rotaci�n de la herramienta.
V
Velocidad de entrada en la pieza.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
D
Cota de fuera trabajo.
A��������
�ngulo de rotaci�n de fresado.
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
Con
par�metro I=0.
Con el par�metro I=0 y el par�metro A=0la herramienta se posiciona en paralelo con el eje X positivo. Valores del par�metro A distintos de 0 provocan
la desviaci�n angular de la orientaci�n de la herramienta. La posici�n angular
de la herramienta permanece fija durante la elaboraci�n (posici�n fija).
Con
par�metro I=1.
Con el par�metro I=1 y el par�metro A=0la herramienta se posiciona perpendicular a la trayectoria programada en el
lado derecho con referencia al avance. Valores del par�metro A distintos de 0 provocan la desviaci�n angular de la orientaci�n de la
herramienta. La posici�n angular de la herramienta permanece perpendicular al
recorrido durante la elaboraci�n (posici�n interpolada).
Con
par�metro I=2.
Con el par�metro I=2 y el par�metro A=0la herramienta se posiciona perpendicular a la trayectoria programada en el
lado izquierdo con referencia al avance. Valores del par�metro A distintos de 0 provocan la desviaci�n angular de la orientaci�n de la
herramienta. La posici�n angular de la herramienta permanece perpendicular al
recorrido durante la elaboraci�n (posici�n interpolada).
Con
par�metro I=3.
Con el par�metro I=3 y el par�metro A=0la herramienta se posiciona en paralelo a la trayectoria programada. Valores
del par�metro A distintos de 0 provocan la desviaci�n angular de la
orientaci�n de la herramienta. La posici�n angular de la herramienta permanece
fija durante la elaboraci�n (posici�n fija).
Con
par�metro I=4.
Con el par�metro I=4 y el par�metro A=0la herramienta se posiciona en paralelo a la trayectoria programada. Valores
del par�metro A distintos de 0 provocan la desviaci�n angular de la
orientaci�n de la herramienta. La posici�n angular de la herramienta permanece
paralela al recorrido durante la elaboraci�n (posici�n interpolada).
Ejemplo:
►Origen
m�quina delantero �
Programaci�n de un inicio fresado con
herramienta perpendicular y en el lado derecho con respecto a la trayectoria a
seguir.
►Origen
m�quina trasero
Programaci�n de inicio fresado con herramienta
perpendicular y en el lado izquierdo con respecto a la trayectoria a seguir.
Nota: la entrada y
la salida autom�ticas no est�n previstas en los fresados inclinados.
Detr�s de la instrucci�n XG0R s�lo podr� haber
instrucciones XG1R, XG2R, XG3R, XG5R.
�ATENCI�N!
Dado que si las elaboraciones con las herramientas inclinadas no se
encuentran perfectamente programadas pueden provocar da�os a la estructura de
la m�quina, es oportuno efectuarlas antes EN MODO SIMULADO.

Fresado lineal con herramienta inclinada - XG1R
Permite
efectuar un fresado lineal sobre un plano inclinado respecto de la forma
ortogonal de las superficies del tablero; debe utilizarse con herramientas
inclinadas. La instrucci�n XG1R se refiere a la cara 1; por este motivo, la
cara de trabajo debe ser siempre la cara 1.
Esta
instrucci�n debe estar precedida por un inicio fresado con herramienta
inclinada o bien por otra instrucci�n de fresado con herramienta inclinada.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de final de fresado.
Y
Coordenada Y de final de fresado.
Z
Profundidad de final de fresado (medida
seg�n la inclinaci�n de la herramienta).
H
Altura del punto final de trabajo desde la
mesa de trabajo (cota a la que debe bajar la herramienta con referencia a la
mesa de trabajo de la m�quina).
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
Par�metros completos:
A
�ngulo de rotaci�n de fresado.
V
Velocidad de fresado.
Ejemplo:
Programaci�n de fresado lineal inclinado con
punto inicial X=0, Y=0.
►Origen
m�quina delantero �
►Origen
m�quina trasero
�ATENCI�N!
Dado que si las elaboraciones con las
herramientas inclinadas no se encuentran perfectamente programadas pueden
provocar da�os a la estructura de la m�quina, es oportuno efectuarlas antes EN
MODO SIMULADO.

Fresado circular horario con herramienta inclinada - XG2R
Define un tramo
de fresado circular (o arco de c�rculo) sobre un plano inclinado respecto de la
forma ortogonal de las superficies del tablero, con avance en sentido horario.
Como alternativa a la definici�n del centro es posible definir el radio del
arco seg�n la siguiente convenci�n: si el radio es positivo, el centro cae a la
izquierda de la l�nea imaginaria que va desde el punto inicial al final, de
otro modo el centro cae a la derecha de dicha l�nea. La instrucci�n XG2R se
refiere a la cara 1; por este motivo, la cara de trabajo corriente debe ser
siempre la cara 1.
Esta
instrucci�n debe estar precedida por un inicio fresado con herramienta
inclinada o bien por otra instrucci�n de fresado con herramienta inclinada.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de fin de fresado.
Y
Coordenada Y de fin de fresado.
Z
Profundidad de fin de fresado (medida seg�n
la inclinaci�n de la herramienta).
I
Coordenada X del arco del centro.
J
Coordenada Y del arco del centro.
H
Altura del punto final de trabajo desde la
mesa de trabajo (cota a la que debe bajar la herramienta con referencia a la
mesa de trabajo de la m�quina).
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
Par�metros complejos:
r
Radio del arco.
A
�ngulo de rotaci�n de fresado.
V
Velocidad de fresado.
Ejemplo:
►Origen
m�quina delantero �
Programaci�n de fresado circular horario
inclinado con punto inicial X=450, Y=100.
►Origen
m�quina trasero
Programaci�n de fresado circular horario
inclinado con punto inicial X=350, Y=0.
�ATENCI�N!
Dado
que si las elaboraciones con las herramientas inclinadas no se encuentran
perfectamente programadas pueden provocar da�os a la estructura de la m�quina,
es oportuno efectuarlas antes EN MODO SIMULADO.

Fresado circular antihorario con herramienta inclinada -
XG3R
Define un tramo
de fresado circular (o arco de c�rculo) sobre un plano inclinado respecto de la
forma ortogonal de las superficies del tablero, con avance en sentido
antihorario. Como alternativa a la
definici�n del centro es posible definir el radio del arco seg�n la siguiente
convenci�n: si el radio es positivo, el centro cae a la izquierda de la l�nea
imaginaria que va desde el punto inicial al final, de otro modo el centro cae a
la derecha de dicha l�nea. La instrucci�n XG3R se refiere a la cara 1; por este
motivo, la cara de trabajo corriente debe ser siempre la cara 1.
Esta instrucci�n debe estar precedida por un inicio fresado con
herramienta inclinada o bien por otra instrucci�n de fresado con herramienta
inclinada.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de fin de fresado.
Y
Coordenada Y de fin de fresado.
Z
Profundidad de fin de fresado (medida seg�n
la inclinaci�n de la herramienta).
I
Coordenada X del centro del arco.
J
Coordenada Y del centro del arco.
H
Altura del punto final de trabajo desde la
mesa de trabajo (cota a la que debe bajar la herramienta con referencia a la
mesa de trabajo de la m�quina).
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
�������������������������������������������������������������������������������������������������
Par�metros complejos:
r
Radio del arco.
A
�ngulo de rotaci�n de fresado.
V
Velocidad de fresado.
Ejemplo:
►Origen
m�quina delantero �
Programaci�n de fresado circular antihorario
inclinado con punto inicial X=350, Y=0.
► Origen m�quina trasero
Programaci�n de fresado circular antihorario
inclinado con punto inicial X=450, Y=100.
�ATENCI�N!
Dado que si las elaboraciones con las herramientas inclinadas no se
encuentran perfectamente programadas pueden provocar da�os a la estructura de
la m�quina, es oportuno efectuarlas antes EN MODO SIMULADO.

Tramo tangente al tramo precedente con herramienta inclinada
- XG5R
Define un tramo
de fresado tangente al tramo precedente, con herramienta inclinada. La
instrucci�n XG5R se refiere a la cara 1; por este motivo, la cara de trabajo
corriente debe ser siempre la cara 1.
Esta instrucci�n debe estar precedida por un inicio fresado con
herramienta inclinada o bien por otra instrucci�n de fresado con herramienta
inclinada.
Grupo:
Fresado est�ndar

Par�metros b�sicos:
X
Coordenada X de fin de fresado (s�lo si G=2
o bien G=3).
Y
Coordenada Y de fin de fresado (s�lo si G=2
o bien G=3).
Z
Profundidad de fin de fresado (medida seg�n
la inclinaci�n de la herramienta).
H
Altura del punto final de trabajo desde la
mesa de trabajo (cota a la que debe bajar la herramienta con referencia a la
mesa de trabajo de la m�quina).
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
Par�metros completos:
G
Tipo de tangente:

1
Segmento a favor del sentido de recorrido
del tramo precedente.

-1
Segmento opuesto al sentido de recorrido del
tramo precedente.

2
Fresado circular horario.

3
Fresado circular antihorario.

V
Velocidad de fresado.
A
�ngulo de rotaci�n de fresado.
L
Longitud del segmento (s�lo si G = 1 o bien
G = -1).
Los par�metros X, Y, H, G, L son obligatorios

Ejemplos:
►Origen
m�quina delantero �
1) Programaci�n de un tramo de fresado
inclinado tangente a un segmento con punto inicial X=450, Y=100.
2) Programaci�n de un tramo de fresado
inclinado tangente a un segmento con punto inicial X=350, Y=0.
3) Programaci�n de un tramo de fresado
inclinado tangente a un arco con punto inicial X=370, Y=50.
►Origen
m�quina trasero
1) Programaci�n de un tramo de fresado
inclinado tangente a un segmento con punto inicial X=350, Y=0.
2) Programaci�n de un tramo de fresado
inclinado tangente a un segmento con punto inicial X=450, Y=100.
3) Programaci�n de un tramo de fresado
inclinado tangente a un arco con punto inicial X=370, Y=50.
�ATENCI�N!
Dado que si las
elaboraciones con las herramientas inclinadas no se encuentran perfectamente
programadas pueden provocar da�os a la estructura de la m�quina, es oportuno
efectuarlas antes EN MODO SIMULADO.
Conexi�n entre fresados - XGFIL
Realiza un
fresado circular de conexi�n entre el fresado programado antes de esta
instrucci�n y el fresado programado despu�s de esta instrucci�n. Esta
instrucci�n conecta cualquier fresado lineal o circular con cualquier fresado
lineal o circular.
Grupo:
Fresado complejo

Par�metros:
r
Radio de conexi�n.
V
Velocidad de fresado.
La secuencia de programaci�n es la siguiente:
1. escribir el primer tramo;
2. escribir el segundo tramo;
3. insertar una l�nea con XGFIL entre las dos precedentes.
El sistema calcula el punto inicial y final de
la conexi�n en autom�tico.
Ejemplos:
1) Programaci�n de una conexi�n con radio de
50 mm entre dos fresado lineales.
Encabezamiento
H DX=450 DY=300
DZ=20 -A C=0 T=0 R=1 *MM /�test�
Inicio fresado
XG0 X=0 Y=0 Z=10 T=101 V=5000 S=16000 E=1
D=30
Primer segment
XL2P X=150 Y=250
Conexi�n�������
XGFIL r=50
Segundo segmento
XL2P X=300 Y=50
►Origen
m�quina delantero �
►Origen
m�quina trasero
2) Programaci�n de una conexi�n con radio de
100 mm entre dos fresados circulares.
Encabezamiento
H DX=450 DY=300
DZ=20 -A C=0 T=0 R=1 *MM /�test�
Inicio fresado
XG0 X=280 Y=235 Z=10 T=101 V=5000 S=16000
E=1 D=30
Primer arco
XAR2 X=150 Y=150 r=150 G=3
Conexi�n�������
XGFIL r=100
Segundo arco
XAR2 X=50 Y=50 r=75 G=2
►Origen
m�quina delantero �
►Origen
m�quina trasero

Chafl�n entre fresados - XGCHA
Realiza un
fresado circular de chafl�n entre el fresado programado antes de esta
instrucci�n y el programado despu�s de esta instrucci�n. Las instrucciones
anterior y posterior a la instrucci�n de biselado pueden ser un fresado
cualquiera lineal o circular.
Grupo:
Fresado complejo

Par�metros:
I
Longitud del primer tramo a achaflanar.
L
Longitud del segundo tramo a achaflanar.
V
Velocidad de fresado.
Ejemplo:
Programaci�n de chafl�n entre dos fresados
lineales.
►Origen
m�quina delantero �
►Origen
m�quina trasero
La secuencia de programaci�n es la siguiente:
1. escribir el primer tramo;
2. escribir el segundo tramo;
3. insertar una l�nea con XGCHA entre las dos precedentes.
El sistema calcula el punto inicial y final de
la conexi�n en autom�tico.
Encabezamiento
H DX=400 DY=250 DZ=20
-A C=0 T=0 R=1 *MM /�CORSO�
Inicio fresado
XG0 X=0 Y=0 Z=10 T=101
Segmento��������
XL2P X=400 Y=0
Chafl�n
XGCHA l=100 L=50
Segmento
XL2P X=400 Y=250

### 5.3.2 Instrucciones
modales
Cambio origen - XO
Desplaza el
origen del tablero en tope a la posici�n programada; todas las instrucciones
que siguen se refieren al nuevo origen.
Grupo:
Funciones principales

Par�metros b�sicos:
X
Origen en X.
Y
Origen en Y.
Z
Origen in Z.
Par�metros completos:
f
Si ha sido programado con el n�mero de una
cara (1-5), habilita la instrucci�n s�lo para el origen de la cara planteada
Ejemplo:

►Origen
m�quina delantero �
►Origen
m�quina trasero

F�(Cara de trabajo)
Define la cara
de trabajo activa.
F
Valores admitidos:

1
Cara superior.

2
Cara derecha.

3
Cara izquierda.

4
Cara delantera.

5
Cara trasera.
Referencias para el origen m�quina delantero:
Referencias para el origen m�quina trasero:
Nota: para
interpolar las caras laterales (F2, F3, F4, F5), Xilog Plus mira el tablero de la cara delantera (F4) a la
trasera (F5) y de la cara izquierda (F3) a la derecha (F2); de este modo, se
invierten los arcos del c�rculo (si en F4 es horario, en F5 es antihorario y si
en F3 es horario, en F2 es antihorario) y la correcci�n del radio (si en F4 es
Izq. en F5 es Der. y si en F3 es Izq. en F3 es Der.).
Ejemplo:
C�(Correcci�n del radio de la herramienta)
Habilita la
correcci�n de la trayectoria del mandril en funci�n de las caracter�sticas de
la fresa montada. Si la fresa es de vela (tipo F), la correcci�n es igual al
radio declarado en la herramienta, es decir, el �di�metro �til�; si la fresa es
de disco (tipo D), la correcci�n es igual a la mitad del espesor de la hoja
declarada en el equipamiento.
C
Valores admitidos:

0
Correcci�n nula.

1
Correcci�n derecha.

2
Correcci�n izquierda.

3
Correcci�n en profundidad (s�lo para fresas
de disco).

13
Correcci�n 1 + correcci�n 3 (s�lo para fresas
de disco).

23
Correcci�n 2 + correcci�n 3 (s�lo para
fresas de disco).
Ejemplos:

K�(Incremental)
Cuando se
activa el incremental, la cota activada como incremental (X o Y o ambas),
programada en una instrucci�n operativa, asume un significado que no es m�s de
posicionamiento respecto del origen del tablero sino de diferencia del valor
que dicha cota hab�a asumido despu�s de la ejecuci�n de la anterior instrucci�n
operativa.
K
Valores admitidos:

0
Ning�n incremental.

1
Incremental en X, correspondiente a la
instrucci�n IX = 1 en el lenguaje b�sico.

2
Incremental en Y, correspondiente a la
instrucci�n IY = 1 en el lenguaje b�sico.

3
Incremental en X e Y, correspondiente a la
secuencia de las dos instrucciones IX = 1 e IY = 1, en el lenguaje b�sico.

Ejemplo:
Referencias para el origen m�quina delantero:
Referencias para el origen m�quina trasero:

P�(Origen de referencia)
Habilita al
trabajo especular con posibilidad de inversi�n del sentido de los fresados circulares.

P
Valores admitidos:

0
Ning�n especular.

1
Especular en X, correspondiente a la
instrucci�n SX = 1 en el lenguaje b�sico.

2
Especular en Y, correspondiente a la
instrucci�n SY = 1 en el lenguaje b�sico.

3
Especular en X e Y, correspondiente a la
secuencia de las dos instrucciones SX = 1 y SY = 1, en el lenguaje b�sico.

11
Como 1 con inversi�n del sentido de los
arcos de c�rculo, correspondiente a la instrucci�n SX=1 M=1 en el lenguaje
b�sico.

12
Como 2 con inversi�n del sentido de los
arcos de c�rculo G2 <-> G3, correspondiente a la instrucci�n SY=1 M=1
en el lenguaje b�sico.

13
Como 3 con inversi�n del sentido de los
arcos de c�rculo G2 <-> G3, correspondiente a la secuencia de las dos
instrucciones SX=1 M=1 y SY=1 M=1 en el lenguaje b�sico.

En la figura siguiente se se�alan las nuevas
referencias de las cotas X e Y con el especular activado:
Referencias para el origen m�quina delantero:
Referencias para el origen m�quina trasero:

Plano inclinado - XPL
Define un plano
distinto de las 5 caras que Xilog Plus crea en autom�tico. Puede girar
alrededor del eje Z o del eje X. Un plano inclinado sirve para poder crear
geometr�as perpendiculares a dicho plano.
Grupo:
Funciones principales

Par�metros:
X
Coordenada X del origen del plano (respecto
al origen del tablero).
Y
Coordenada Y del origen del plano (respecto
al origen del tablero).
Z
Coordenada Z del origen del plano (respecto
a la base del tablero).
Q
�ngulo de rotaci�n sobre al eje Z (origen
m�quina delantero: positivo en sentido antihorario; origen m�quina trasero:
positivo en sentido horario).
R
�ngulo de rotaci�n sobre al eje X (origen
m�quina delantero: positivo en sentido antihorario; origen m�quina trasero:
positivo en sentido horario).
El par�metro F debe valer siempre 1 con la
instrucci�n modal F. Los par�metros X, Y, Q, R son obligatorios.
Una instrucci�n XPL queda anulada por:
� otra instrucci�n XPL; la llamada de una
cara est�ndar.
Para restablecer un plano inclinado, hay que
insertar otra instrucci�n XPL con todos los par�metros a 0 como se indica en el
ejemplo siguiente.
Si todos los par�metros valen cero se
restablece la cara 1;
Ejemplo:
Programaci�n de un plano inclinado con
or�genes X=500, Y=0, Z=0, a 45� del eje Z y a 90� del eje X.
►Origen
m�quina delantero �
X=500, Y=0 y Z=0� son las coordenadas de origen del plano inclinado.
Despu�s de cambiar los or�genes, hay que
escribir el par�metro Q=�ngulo deseado (Q=45) para girar el sistema de los ejes
alrededor del eje Z.
A continuaci�n, hay que escribir el par�metro
R=�ngulo deseado (R=90) para girar el sistema de ejes alrededor del eje X..
El resultado final es un plano inclinado como
indica la figura siguiente.
Nota: la direcci�n
del eje Z debe ser siempre negativa
hacia el exterior del tablero.
►Origen
m�quina trasero
Programaci�n de un plano inclinado con
or�genes X=500, Y=0,� a 45� del eje Z y
90� del eje X.
X=500, Y=0 y Z=0 son las coordenadas de origen
del plano inclinado.
Despu�s de cambiar los or�genes, hay que
escribir el par�metro Q=�ngulo deseado (Q=45) para girar el sistema de ejes
alrededor del eje Z.
A continuaci�n, hay que escribir el par�metro
R=�ngulo deseado (R=-90) para girar el sistema de ejes alrededor del eje X..
El resultado final es un plano inclinado como
indica la figura siguiente.
Nota: la direcci�n
del eje Z debe ser siempre negativa
hacia el exterior del tablero.

### 5.3.3
Instrucciones de gesti�n de los subprogramas
Apertura de subprograma - XS
Solicita como
subprograma un programa normal.
Grupo:
Funciones principales

Par�metros:
X
Origen en X del subprograma.
Y
Origen en Y del subprograma.
Z
Origen en Z del subprograma.
A
�ngulo de rotaci�n del subprograma (origen
m�quina delantero: positivo en sentido antihorario; origen m�quina trasero:
positivo en sentido horario).
N
Nombre del subprograma.
Los par�metros del subprograma/macro lanzado
se pueden modificar directamente en las respectivas casillas: haga clic dos
veces en la casilla, escriba el nuevo valor y confirme con la tecla [ENVIO].
Para X, Y, Z no programados valen los valores
corrientes (para Z vale la �ltima cota de trabajo).
Un programa abierto mantiene en memoria sus
subprogramas: para activar las modificaciones gr�ficas de estos �ltimos hay que
cerrar y volver a abrir el programa principal.
�Atenci�n! La instrucci�n XS no es id�nea para llamar programas que contienen
superficies inclinadas (instrucci�n XPL), porque la traslaci�n se aplica s�lo a
las elaboraciones y no al origen de la superficie inclinada. Para esta finalidad
es necesario utilizar la instrucci�n SO.
�Atenci�n! Si el subprograma depende de un fichero de las variables entorno, para
un funcionamiento correcto del programa principal (que lo lanza) es necesario
que tambi�n en el encabezamiento del programa principal se haya programado el
mismo fichero de las variables entorno del subprograma.
Ejemplo:
►Origen
m�quina delantero �
Obtener de un tablero de grandes dimensiones
cuatro piezas (subprogramas) como en la figura:
Para ello, hay que realizar las siguientes
operaciones:
crear en el editor un nuevo programa,
escribiendo en el Encabezamiento los datos del tablero.
Ahora, solicitar el primer subprograma
mediante la instrucci�n XS.
NOTA. Al insertar
la instrucci�n XS con la barra de instrucciones, el programa se puede
seleccionar en la ventana Abrir directamente con el rat�n.
A continuaci�n, solicitar por segunda vez el
primer subprograma, introduci�ndolo en la segunda posici�n.
Solicitar el segundo subprograma, programar el
origen como indica la figura y girarlo 90�.
Repetir la operaci�n para introducir el �ltimo
subprograma.
►Origen
m�quina trasero
Obtener de un tablero de grandes dimensiones
cuatro piezas (subprogramas) como en la figura:
Para ello, hay que realizar las siguientes
operaciones:
crear en el editor un nuevo programa,
escribiendo en el Encabezamiento los datos del tablero.
Ahora, solicitar el primer subprograma
mediante la instrucci�n XS.
NOTA. Al insertar
la instrucci�n XS con la barra de instrucciones, el programa se puede
seleccionar en la ventana Abrir directamente con el rat�n.�
A continuaci�n, solicitar una segunda vez el
primer subprograma, introduci�ndolo en la segunda posici�n.
Solicitar el segundo subprograma, introducir
el origen como en la figura y girarlo 90�.
Repetir las operaciones para introducir el
�ltimo subprograma.
### 5.3.4 Env�o de mensajes al operador
Impresi�n mensaje - XMSG
Los mensajes al
operador son informaciones enviadas al operador durante la elaboraci�n de la
pieza.
Grupo:
Funciones principales

Par�metros b�sicos:
Mensaje/N
Mensaje.
Par�metros completos:
SBYQ
Tipo de standby a efectuar.
I
Habilitaci�n de la solicitud de introducci�n
datos.
Lista par�metros/(campo vac�o)
Introducir par�metros.
Una XMSG sin par�metros determina la
cancelaci�n del mensaje precedente.
El mensaje puede contener la indicaci�n de
valores variables (contramarcados con la llave ?); a cada uno de estos valores
debe corresponder un par�metro introducido en la lista de los par�metros. Los
par�metros admitidos son como m�ximo 7, de nombre P1, P2 etc.: P1 est� siempre
asociado al valor variable m�s a la izquierda del mensaje, P2 al sucesivo a la
derecha, y as� sucesivamente.
A cada mensaje puede asociarse una petici�n de
introducci�n datos (parametro I=1); en dicho caso, el valor introducido se
copia en la variable reservada xMSGInVal. Despu�s del env�o de un mensaje el
programa pieza puede seguir o detenerse en espera de que el operador introduzca
el dato posiblemente solicitado y/o accione el pulsador de Start.
La indicaci�n de standby (par�metro SBY/Q a 1
� 2) determina la parada del programa pieza en espera de que se presione el
pulsador de Start; en caso de petici�n datos el programa pieza se
detendr� en cualquier caso simulando la indicaci�n de SBY/Q=1.
Las instrucciones XMSG se cargan
individualmente y aparecen con l�gica en funci�n del tipo:
XMSG sin INPUT
El mensaje aparece en la ventana de los
mensajes; en presencia de standby el mensaje se cancela presionando el pulsador
de Start; en caso contrario, el mensaje se cancela tras la llegada de
una nueva XMSG, posiblemente sin mensaje. En ambos casos la cancelaci�n tambi�n
tiene lugar al aceptar un Reset.
XMSG con INPUT
El mensaje aparece en la ventana de los
mensajes y se visualiza un icono para se�alar la necesidad de introducci�n
datos (men� mandos/entrada
mensaje operador). El mensaje se borra con la
presi�n del pulsador de Start y al aceptar un Reset.
Ejemplo:
�
XMSG N=� Esperar hasta que se complete el
ciclo de descarga�
�
XMSG
�
XMSG N=��Quitar las virutas y pulsar
start-ciclo!� Q=1
�
XMSG N=� Introducir el �ngulo de corte a la
derecha� I=1
L ADX=xMSGInVal
XMSG N=� Introducir el �ngulo de corte a la
izquierda� I=1
L
ASX=xMSGInVal
IF ADX >
90 AND ASX=0 THEN
�
FI
�
L Min = 0
L Max = 4
XMSG N=� Posici�n de la campana (de ?d a ?d)�
P1=Min. P2=Max. I=1
L Campana=xMSGInVal
IF Campana
>= Min AND Campana <= Max THEN
ISO �M?d� 110+Campana
ELSE
PRINT �Posici�n de la campana=?d err�nea!�
Cuffia
FI