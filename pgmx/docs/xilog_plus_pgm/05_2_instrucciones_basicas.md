
# 5.2 Instrucciones b�sicas (texto)
### 5.2.1 Instrucciones
operativas
#### 5.2.1.1 Funciones
generales
Entrada autom�tica en el perfil -
GIN
Define una
recta o un arco de c�rculo tangente al perfil en el punto de entrada. Tiene
efecto si ha sido programa antes de la instrucci�n de inicio perfil (G0).
Par�metros:
G
Tipo de entrada: 1=recta, 2=arco (el arco vale
s�lo si se habilita la compensaci�n del radio herramienta). Se habilita la
entrada con hoja en recta tangente.
R
Factor de multiplicaci�n del radio de la
herramienta (por defecto=2).
Q
Tipo de acercamiento: 0=en cota, 1=en
bajada.
La velocidad de recorrido utilizada para el tramo de
entrada en el perfil es la siguiente:
- valor configurado para el inicio del perfil si en la instrucci�n de
inicio perfil (G0) el campo V (velocidad de recorrido) est� programado con un
valor
- valor configurado en el par�metro �Velocidad G0/B (�)� de la
herramienta utilizada para el perfil, si en la instrucci�n de inicio perfil el
campo V (velocidad de recorrido) no est� programado
Ejemplos: formas de realizar la entrada
autom�tica.
1) Entrada lineal
vertical
2) Entrada en arco vertical
3) Entrada lineal
inclinada
4) Entrada en arco
inclinada
�ATENCI�N!
La
entrada autom�tica no est� habilitada si se ha programado la instrucci�n C=3 o
C=31 o C=32. Si C=0 y G=2, el sentido de entrada del arco est� determinado por
el signo de R (positivo=arco horario; negativo=arco antihorario)

Salida autom�tica del perfil - GOUT
Define una
recta o un arco de c�rculo tangente al perfil en el punto de salida. Tiene
efecto si ha sido programada despu�s de la �ltima instrucci�n del perfil.
Par�metros:
G
Tipo de salida: 1=recta, 2=arco (el arco
vale s�lo si se ha habilitado la compensaci�n del radio de la herramienta). Se
habilita la salida con hoja en recta tangente (G=1).
L
Tipo de salida: 1=recta, 2=arco (el arco
vale s�lo si se ha habilitado la compensaci�n del radio de la herramienta). Se
habilita la salida con hoja en recta tangente (G=1).
R
Factor de multiplicaci�n del radio de la
herramienta (por defecto=2).
Q
Tipo de alejamiento: 0=en cota, 1=en subida.
La velocidad de recorrido utilizada para el tramo de
salida del perfil es la siguiente:
- valor configurado en el �ltimo tramo del perfil si en la �ltima
instrucci�n del perfil el campo V (velocidad de recorrido) est� programado con
un valor
- valor configurado en el par�metro �Velocidad Est�ndar (�)� de la
herramienta utilizada para el perfil, si en la �ltima instrucci�n del perfil el
campo V (velocidad de recorrido) no est� programado
Ejemplos: formas de realizar la salida
autom�tica.
1) Salida lineal vertical
2) Salida en arco vertical
3) Salida lineal inclinada
4) Salida en arco inclinada
�ATENCI�N!
La salida autom�tica no se habilita si se programa la instrucci�n C=3 o
C=31 o bien C=32.

Repetici�n
de un perfil - GREP
Efect�a la
repetici�n de un perfil. La instrucci�n GREP no est� influenciada por las
instrucciones SX y SY.
Par�metros:
X
Coordenada X del punto de partida del perfil
u offset X del perfil (v.Q).
Y
Coordenada Y del punto de partida del perfil
u offset Y del perfil (v. Q).
Z
Offset del perfil en profundidad Z.
Q
0 = cotas X,Y absolutas; 1 = offset.
G
Inversi�n sentido de recorrido (0=NO,1=SI).
V
Velocidad de fresado.
S
Velocidad de rotaci�n de la herramienta
D
Cota de fuera trabajo.
N
Nombre del perfil (v. campo N de la instrucci�n G0).
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
T
Herramientas.
El ejemplo siguiente contiene el fresado de
formas del tablero de la figura (30 mm de espesor) con una herramienta llamada
E1, el fresado interno del rect�ngulo A con una herramienta llamada E2, la
repetici�n del perfil A en la posici�n B con coordenadas absolutas, la
repetici�n del perfil A en la posici�n C con offset, la repetici�n del perfil A
en la posici�n D con offset e inversi�n del sentido de reccorrido con una
herramienta llamada E3.
►Origen
m�quina delantero

►Origen
m�quina trasero
H DX=600 DY=400 DZ=30 -A C=0 T=0 R=1 *MM
/�ANDREA� V10;encabezamiento
;fresado externo del tablero
GIN Q=0 R=2 G=1 C=... (origen m�quina delantero: C=1; origen m�quina trasero: C=2); entrada autom�tica en el perfil con recta en cota
G0 X=0 Y=0 Z=� T=101 V=4000 S=18000 E=1
D=20;inicio perfil de fresado de formas
G1 X=600 Y=0
G1 X=600 Y=400
G1 X=0 Y=400
G1 X=0 Y=0
GOUT Q=0 R=2 G=1 C=0;salida autom�tica del
perfil con recta en cota
;inicio trabajo rect�ngulo A
GIN Q=1 R=2 G=1 F=1 C=0;entrada con recta en
bajada sin compensaci�n del radio
G0 X=150 Y=50 Z=� E=1 V=5 S=18000 D=20
N=�PRUEBA� T=101 inicio del perfil nombre �prueba�
G1 X=250 Y=50
G1 X=250 Y=150
G1 X=50 Y=150
G1 X=50 Y=50
G1 X=150 Y=50
GOUT Q=1 R=2 G=1 L=10;salida del perfil con
recta inclinada
;repetici�n del rect�ngulo A llamado �prueba�
en la posici�n B con cotas absolutas
GREP X=450 Y=50
Q=0 G=0 N=�PRUEBA�;la misma herramienta y la misma cota de trabajo
;repetici�n del rect�ngulo A llamado �prueba�
en la posici�n C con cotas offset
GREP Y=200 Q=1
G=0� N=�PRUEBA�;cotas referidas al punto
inicial del primer rect�ngulo
;repetici�n del rect�ngulo A llamado �prueba�
en la posici�n D con cotas offset
GREP X=300 Y=200
Q=1 G=1 N=�PRUEBA� T=103;herramienta E3 inversi�n sentido de recorrido
N X=0 Y=0 T=101 F=1; parada mandril en el cero
m�quina y carga de la herramienta E1

Modificar velocidad - GSET�
La instrucci�n
GSET describe algunas nuevas caracter�sticas de un perfil llamado con GREP
sucesiva.
Par�metros:
V
Velocidad de avance.
T
Herramientas.
B�������� �����������
Tipo de perfil. El tipo de perfil B asocia
las caracter�sticas de la GSET a la herramienta o al proceso activo al
momento de la interpretaci�n de la geometr�a: 1=recorrido a fresar,
2=recorrido a cortar.
Todos los par�metros de la instrucci�n son
opcionales.
La instrucci�n GSET debe introducirse antes de
cualquier otra instrucci�n G de movimiento; la instrucci�n G de movimiento
influida por una GSET asume las nuevas caracter�sticas durante una repetici�n
del perfil con GREP.
La instrucci�n GSET est� habilitada solamente
si la herramienta especificada es igual a la especificada en GREP o bien si el
identificador del tipo de perfil est� representado por la herramienta activa durante
la repetici�n del perfil.
Ejemplos:
1.�������� GSET
sin efecto puesto que la herramienta especificada en la GREP no es 101
�.
G0������ X..Y..
Z.. V=1 S E T=101 N=�Prof�
G1������ X.. Y.. Z.. V=5
GSET V=10 T=101
G1������ X.. Y.. Z.. V=6
�.
GREP V=2 T=102
N=�Prof�
�.
2.�������� GSET
significativa puesto que la herramienta especificada en la GREP coincide con la
de la GSET
�.
G0������ X.. Y.. Z.. V=1 S E T=101 N=�Prof�
G1������ X.. Y.. Z.. V=5
GSET V=10 T=102
G1������ X.. Y.. Z.. V=6
�.
GREP V=2 T=102 N=�Prof�
�.
3.�������� La
GSET tiene efecto solamente si la herramienta E2 es una fresa
�.
G0������ X.. Y.. Z.. V=1 S E T=101 N=�Prof�
G1������ X.. Y.. Z.. V=5
GSET V=10
B=1
G1������ X.. Y.. Z.. V=6
�.
GREP V=2 T=102 N=�Prof�
�.
4.�������� La
GSET tiene efecto solamente si E2 es una fresa (por la presencia de B=1)
�.
G0������ X.. Y.. Z.. V=1 S E T=101 N=�Prof�
G1������ X.. Y.. Z.. V=5
GSET V=10 T=101
B=1
G1������ X.. Y.. Z.. V=6
�.
GREP V=2 T=102
N=�Prof�
�.
Puesto que es posible repetir el perfil varias
veces, tambi�n es posible especificar varios GSET antes de una instrucci�n G de
movimiento. La repetici�n en curso determina la GSET asociada a la instrucci�n
G. Si existen GSET repetitivas, se tiene en cuenta la �ltima.
5.
�.
G0������ X.. Y.. Z.. V=1 S E T=101 D N=�Prof�
G1������ X.. Y.. Z.. V=5
GSET V=10 T=102
GSET V=15 T=103
G1������ X.. Y.. Z.. V=6
�.
GREP V=2 T=102 N=�Prof�; Tiene efecto s�lo la
GSET con T=102
GREP V=2 T=103 N=�Prof�; Tiene efecto s�lo la
GSET con T=103
�.
6.
�.
G0������ X.. Y.. Z.. V=1 S E T=101 D N=�Prof�
G1������ X.. Y.. Z.. V=5
GSET V=10 T=102
GSET V=15 T=103
GSET V=20 B=1
G1������ X..
Y.. Z.. V=6
�.
GREP V=2 T=102 N=�Prof�; si E2 y E3 son fresas
la instrucci�n GSET
GREP V=2 T=103 N=�Prof�; con B=1 las GSET
precedentes no tienen efecto
�.
Rotaci�n del panel - ROT�
Gira el trabajo
de una macro. El funcionamiento de la instrucci�n ROT est� garantizado s�lo
para las macros.
Grupo:
Funciones principales

Par�metros:
A
�ngulo de rotaci�n (origen m�quina
delantero: positivo en sentido antihorario; origen m�quina trasero: positivo
en sentido horario).
X
Cota X del centro de rotaci�n.
Y
Cota Y del centro de rotaci�n.
�����������������������

Instrucci�n ISO - ISO
Permite
programar una instrucci�n en el lenguaje ISO del control num�rico usado; la
instrucci�n debe colocarse entre dobles �pices y puede ser ejecutada desde una
lista de par�metros separados por lo menos por un espacio (la estructura y el
significado de los par�metros est�n descritos en el p�rrafo correspondiente a
la instrucci�n PRINT). En la instrucci�n no se efect�a ning�n control
sint�ctico y a �sta no le corresponde ninguna visualizaci�n gr�fica.
Grupo:
instrucciones texto

Par�metros:
�<l�nea>�
Instrucci�n ISO.
(campos vac�os)
Par�metros opcionales.
Nota. Cuando existen MICRO POSICIONAMIENTOS dentro de un programa, es
necesario introducir al inicio del mismo la instrucci�n:
ISO �%B20�.
Ejemplos:
ISO �G0X1000Y740F6000�
ISO �M71�
ISO �M?d� 110+Campana

Operaci�n nula - N
Apaga las
rotaciones y coloca los electromandriles en posici�n de reposo.
Par�metros:
X
Posici�n del cabezal en el eje X.
Y
Posici�n del cabezal en el eje Y.
V
Velocidad de desplazamiento.
S
Velocidad de rotaci�n de la herramienta. El
significado del campo S es el siguiente: si no est� programado o vale 0, los
mandriles se apagan; si est� programado a 1, los mandriles permanecen
encendidos.
Q
El significado del campo Q es el siguiente:
si no est� programado o vale 0, las cotas X e Y se refieren al cero m�quina;
si est� programado a 1, las cotas X e Y se refieren al cero tablero.
T
N�mero de una herramienta externa.
��������������������������������������������������������������������
La herramienta especificada en el campo T se
toma del almac�n de herramientas.

Palpaci�n panel - TA�
La palpaci�n es
una operaci�n que permite detectar irregularidades en los tableros y corregir
consecuentemente las elaboraciones.
Par�metros:
X
Coordenada X del punto a palpar referido al
lado corriente (de 1 a 5).
Y
Coordenada Y del punto a palpar referido al
lado corriente (de 1 a 5).
G
Controla la subida de la cabeza despu�s de
la palpaci�n.

(default)
El cabezal sube hasta el final de carrera + de
Z.

0
El cabezal sube hasta el final de carrera +
de Z.

1
El cabezal permanece a la cota Z de la
palpaci�n.

2
El cabezal sube hasta la cota de rozamiento
sobre la pieza.

Q
Define el tipo de palpaci�n.

(default)
Palpaci�n de las caras del tablero.

0
Palpaci�n de las caras del tablero.

1
Palpaci�n de un punto del panel.

T
Herramienta.
��������������������������������������
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
asimismo, las dimensiones reales se utilizan autom�ticamente cuando los
trabajos son programados con las instrucciones de especularidad SX y SY; para
terminar, se permite palpar varias caras antes de llevar a cabo los trabajos.
Para leer la traslaci�n de la pieza respecto al tope pueden utilizarse las
variables predefinidas @BX, @BY, @BZ.
En caso de palpaci�n de un punto del panel (G
= 1), las coordenadas del punto palpado quedan memorizadas en las variables @X,
@Y y @Z.
IMPORTANTE
El par�metro �G=1�, o la solicitud de mantener
la cabeza a la cota de palpaci�n, debe ser utilizado con mucha cautela. Su uso
est� orientado hacia aplicaciones especiales, como la palpaci�n consecutiva de
m�s puntos en el interior de un �bolsillo� que se encuentra en la pieza a
trabajar. En dicha circunstancia, las palpaciones se programan especificando
las diferentes caras laterales y� �G=1�,
as� que la cabeza, no volviendo nunca a subir en Z, efect�a de manera m�s
r�pida todas las operaciones. Si se realizan dos palpaciones consecutivas en
dos caras laterales diferentes y externas (las cl�sicas de la pieza) indicando
�G=1�, el pasaje entre las dos, causa la colisi�n del dispositivo palpador con
la madera, ya que la cabeza desplaz�ndose no se encuentra por encima de la
pieza (en virtud del valor �1� requerido para �G�), sino m�s abajo.
Ejemplos:
�����������
H DX1000 DY800 DZ20 �A /DEF
F 2
TA X10 Y400 T91
F 3
TA X10 Y500 T91
F 1
B X100 Y400 Z8 T2
B X = @DX -50 Y500 Z8 T2
SX 1
B X200 T1
#### 5.2.1.2 Perforaciones
Perforaci�n - B�
Ejecuta uno o
m�s orificios.
Par�metros:
X
Coordenada X del primer orificio.
Y
Coordenada Y del primer orificio.
Z
Profundidad de los orificios.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
a
Offset del cabezal de perforaci�n flotante
en Y (eje E, s�lo si est� presente).
V
Velocidad de perforaci�n.
S
Velocidad de rotaci�n de la herramienta.
G
N�mero de pasos para descarga virutas.
D
Cota de fuera trabajo.
T
Lista de las herramientas; en caso de varias
herramientas las coordenadas X, Y se
refieren a la primera herramienta indicada.
Ejemplos:
1) Programaci�n de un orificio
Para ejecutar un orificio, los par�metros X,
Y, Z, T son obligatorios. La posibilidad de realizar un orificio con descarga
de virutas se activa mediante el par�metro G=n�mero de pasadas (se divide en
partes iguales).
►Origen
m�quina delantero �
► Origen m�quina trasero
2) Programaci�n de un serie de orificios con
la perforadora en paso 32 utilizando varios husos.
Los par�metros X, Y, Z, T son obligatorios.
Programar el primer orificio; para programar los orificios restantes a una
distancia de 32mm, hay que seleccionar varios husos mediante el par�metro T
(entre un n�mero y otro hay que dejar un espacio).
►Origen
m�quina delantero �
► Origen m�quina trasero

Perforaci�n
optimizada - BO�
Realiza uno o
varios orificios sirvi�ndose del algoritmo de optimizaci�n de las
perforaciones. Todas las instrucciones BO programadas en sucesi�n entran en la
misma secci�n de optimizaci�n; en un programa pueden existir varios bloques de
instrucciones BO.
Par�metros:
X
Coordenada X del primer orificio.
Y
Coordenada Y del primer orificio.
Z
Profundidad de los orificios.
D
Di�metro de los orificios.
N
Tipo de broca de perforaci�n (P=plana,
L=lanza, S=avellanada).
R
N�mero de orificios programados (incluido el
orificio de origen).
x
Paso en X para las repeticiones.
y
Paso en Y para las repeticiones.
G
N�mero de pasos para descarga virutas.
V
Velocidad de perforaci�n.
L
Altura avellanador (s�lo si N=S).
Ejemplos:
1) Programaci�n de un orificio
Los par�metros X, Y, Z, D, N son obligatorios
para realizar un orificio.
►Origen
m�quina delantero �
► Origen m�quina trasero
2) Programaci�n de una serie de orificios
Los par�metros X, Y, Z, R, x, y, D, N son
obligatorios para realizar una serie de orificios. Programar el primer
orificio, los orificios restantes se programan mediante R=n�mero de orificios
(incluido el orificio de origen), x=distancia entre los orificios (puede ser
distinta de 32mm).
►Origen
m�quina delantero �
► Origen m�quina trasero

Perforaci�n inclinada - BR
Permite
efectuar uno o varios orificios inclinados respecto de la forma ortogonal de la
superficie de trabajo. La instrucci�n BR se refiere siempre a la cara 1, por
ello la cara corriente debe ser siempre esa.
Par�metros:
X
Coordenada X del primer orificio.
Y
Coordenada Y del primer orificio.
Z
Profundidad de los orificios.
H�������� �����������
Altura del orificio desde la mesa de trabajo
(cota a al que debe bajar la herramienta con referencia a la mesa de trabajo
de la m�quina). Si no se programa vale DZ.
A��������
�ngulo de rotaci�n de la perforaci�n (origen
m�quina delantero: positivo en sentido antihorario; origen m�quina trasero:
positivo en sentido horario).
Q�������� �����������
Si vale 0, el �ngulo A se suma
alg�bricamente al offset R de la herramienta. Si vale 1, el �ngulo A
sustituye el offset R de la herramienta
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
V
Velocidad de perforaci�n.
S
Velocidad de rotaci�n de la herramienta.
G
N�mero de pasos para descarga virutas.
D
Cota de fuera trabajo.
B
Angulo de inclinaci�n de la herramienta
respecto a la vertical (s�lo para el grupo Prisma).
T
Lista de las herramientas; en caso de varias
herramientas las coordenadas X, Y se refieren a la primera herramienta
indicada.
Ejemplo:
Programaci�n de un orificio con par�metro Q=1.
► Origen
m�quina delantero
► Origen m�quina trasero
�ATENCI�N!
Dado
que si las elaboraciones con las herramientas inclinadas no se encuentran
perfectamente programadas pueden provocar da�os a la estructura de la m�quina,
es oportuno efectuarlas antes EN MODO SIMULADO.

#### 5.2.1.3 Fresados
Inicio
fresado - G0
Define el punto
inicial de un perfil.
Par�metros:
X
Coordenada X de inicio del perfil.
Y
Coordenada Y de inicio del perfil.
Z
Profundidad de inicio del perfil.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
V
Velocidad de entrada en la pieza.
S
Velocidad de rotaci�n de la herramienta.
D
Cota de fuera trabajo.
N
Nombre del perfil (v. GREP).
T
Herramienta.
Ejemplo:
► Origen
m�quina delantero

► Origen m�quina trasero

Inicio fresado 3D - G03D (grupo Prisma)
Permite empezar
un fresado lineal en un plano inclinado con respecto a la ortogonalidad de las
superficies del tablero; controla la entrada/salida de la herramienta en la
pieza imaginando una profundidad de trabajo nula. No admite GIN/GOUT; no se
puede introducir la campana. Puede utilizarse s�lo con el grupo Prisma,
�nicamente con el lado 1 activo y con la correcci�n del radio desactivada.
V�ase: Ap�ndice H - Grupo Prisma.
Par�metros:
X
Coordenada X de inicio perfil.
Y
Coordenada Y de inicio perfil.
H
Altura del trabajo desde la mesa de trabajo
(cota a la que debe descender la herramienta referida a la mesa de trabajo de
la m�quina; si no ha sido programada vale DZ).
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
V
Velocidad de fresado.
S
Velocidad de rotaci�n de la herramienta.
D
Cota de fuera de trabajo (s�lo con Q y R no
programados).
Q
�ngulo de rotaci�n alrededor del eje Z.
N
Nombre del perfil (v. GREP).
R
�ngulo de rotaci�n alrededor del eje X.
T
Herramienta.

Fresado lineal - G1�
Define un
segmento de recta.
Par�metros:
X
Coordenada X de fin de segmento.
Y
Coordenada Y de fin de segmento.
Z
Profundidad de fin de segmento.
V
Velocidad de fresado.
Ejemplo:
El punto inicial (X=100, Y=50) est� definido
por la instrucci�n precedente.
►Origen
m�quina delantero
► Origen m�quina trasero

Fresado lineal 3D - G13D (grupo Prisma)
Permite
realizar un fresado lineal en un plano inclinado con respecto a la
ortogonalidad de las superficies del tablero. Puede utilizarse s�lo con el
grupo Prisma, �nicamente con el lado 1 activo y con la correcci�n del radio
desactivada. V�ase: Ap�ndice H - Grupo Prisma.
Par�metros:
X
Coordenada X de final del tramo.
Y
Coordenada Y de final del tramo.
H
Altura del trabajo respecto a la mesa de
trabajo (cota a la que descender la herramienta referida a la mesa de trabajo
de la m�quina; si no ha sido programada vale DZ).
V
Velocidad de fresado.
Q
�ngulo de rotaci�n alrededor del eje Z.
R
�ngulo de rotaci�n alrededor del eje X.

Fresado circular horario - G2�
Define un arco
de c�rculo en sentido horario. Como alternativa a la definici�n del centro es
posible definir el radio del arco seg�n la siguiente convenci�n: si el radio es
positivo, el centro cae a la izquierda de la l�nea imaginaria que va desde el
punto inicial al final, de otro modo el centro cae a la derecha de dicha l�nea.

Par�metros:
X
Coordenada X de fin de arco.
Y
Coordenada Y de fin de arco.
Z
Profundidad de fin de arco.
I
Coordenada X del centro del arco.
J
Coordenada Y del centro del arco.
V
Velocidad de fresado.
r
Radio del arco.
Ejemplos:
1) Arco dado el radio. El punto inicial
(x=100, Y=50) est� definido por la instrucci�n precedente.
►Origen
m�quina delantero
► Origen m�quina trasero
2) Arco dado el centro. El punto inicial
(x=100, Y=50) est� definido por la instrucci�n precedente.
►Origen
m�quina delantero
► Origen m�quina trasero

Fresado circular antihorario - G3�
Define un arco
de c�rculo en sentido antihorario. Como alternativa a la definici�n del centro
es posible definir el radio del arco seg�n la siguiente convenci�n: si el radio
es positivo, el centro cae a la izquierda de la l�nea imaginaria que va desde
el punto inicial al final, de otro modo el centro cae a la derecha de dicha
l�nea.
Par�metros:
X
Coordenada X de fin de arco.
Y
Coordenada Y de fin de arco.
Z
Profundidad de fin de arco.
I
Coordenada X del centro del arco.
J
Coordenada Y del centro del arco.
V
Velocidad de fresado.
r����������
Radio del arco.
Ejemplos:
1) Arco dado el radio. El punto inicial
(X=200, Y=150) est� definido por la instrucci�n precedente.
►Origen
m�quina delantero
► Origen m�quina trasero
2) Arco dado el centro. El punto inicial
(X=200, Y=150) est� definido por la instrucci�n precedente.
►Origen
m�quina delantero
► Origen m�quina trasero

Tramo tangente al tramo precedente - G5
Define un tramo
de fresado tangente al tramo precedente.
Par�metros:
X
Coordenada X de fin de fresado (s�lo si G=2
o bien G=3).
Y
Coordenada Y de fin de fresado (s�lo si G=2
o bien G=3).
Z
Profundidad de fin de fresado.
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

L
Longitud del segmento (s�lo si G = 1 o bien
G = -1).
V
Velocidad de fresado.
Ejemplos:
1) Programaci�n de un tramo de fresado lineal
tangente a un arco a favor del sentido de recorrido. Los par�metros L, G son
obligatorios. El punto inicial de fresado est� definido por la instrucci�n
precedente.
►Origen
m�quina delantero

► Origen m�quina trasero
2) Programaci�n
de un tramo de fresado lineal tangente a un arco con sentido opuesto al de
recorrido. Los par�metros L, G son obligatorios. El punto inicial de fresado
est� definido por la instrucci�n precedente.
►Origen
m�quina delantero
► Origen m�quina trasero

3) Programaci�n de un tramo de fresado
circular horario tangente a un tramo precedente. Los par�metros X, Y, G son
obligatorios. El punto inicial de fresado est� definido por la instrucci�n
precedente.
►Origen
m�quina delantero
► Origen m�quina trasero

4) Programaci�n de un tramo de fresado circular antihorario tangente a un tramo
precedente. Los par�metros X, Y, G son obligatorios. El punto inicial de
fresado est� definido por la instrucci�n precedente.
►Origen
m�quina delantero
► Origen m�quina trasero

Inicio fresado con herramienta inclinada - G0R
Permite
comenzar el fresado con una herramienta inclinada sobre un plano no ortogonal a
las superficies del tablero. La instrucci�n G0R se refiere siempre a la cara 1;
por ello la cara de trabajo corriente debe ser siempre esa.
Par�metros:
X
Coordenada X de inicio perfil.
Y
Coordenada Y de inicio perfil.
Z
Profundidad de inicio perfil (medida seg�n
la inclinaci�n de la herramienta).
A��������
�ngulo de rotaci�n de fresado.
H�������� �����������
Altura de trabajo desde la mesa de trabajo
(cota a la que debe bajar la herramienta con referencia a la mesa de trabajo
de la m�quina). Si no se programa vale DZ.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
V
Velocidad de entrada en la pieza.
S
Velocidad de rotaci�n de la herramienta.
D
Cota de fuera trabajo.
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
N
Nombre del perfil (v. GREP).
IC
Lado de entrada (0, 1, 2, 3, 4).
B
Angulo de inclinaci�n de la herramienta
respecto a la vertical (s�lo para el grupo Prisma).
T
Herramienta.
Con
par�metro IC=0.
Con el par�metro IC=0 y el par�metro A=0la herramienta se posiciona en paralelo con el eje X positivo. Valores del par�metro A distintos de 0 provocan
la desviaci�n angular de la orientaci�n de la herramienta. La posici�n angular
de la herramienta permanece fija durante la elaboraci�n (posici�n fija).
Con
par�metro IC=1.
Con el par�metro IC=1 y el par�metro A=0la herramienta se posiciona perpendicular a la trayectoria programada en el
lado derecho con referencia al avance. Valores del par�metro A distintos de 0 provocan la desviaci�n angular de la orientaci�n de la herramienta.
La posici�n angular de la herramienta permanece perpendicular al recorrido
durante la elaboraci�n (posici�n interpolada).
Con
par�metro IC=2.
Con el par�metro IC=2 y el par�metro A=0la herramienta se posiciona perpendicular a la trayectoria programada en el
lado izquierdo con referencia al avance. Valores del par�metro A distintos de 0 provocan la desviaci�n angular de la orientaci�n de la
herramienta. La posici�n angular de la herramienta permanece perpendicular al
recorrido durante la elaboraci�n (posici�n interpolada).
Con
par�metro IC=3.
Con el par�metro IC=3 y el par�metro A=0la herramienta se posiciona en paralelo a la trayectoria programada. Valores
del par�metro A distintos de 0 provocan la desviaci�n angular de la
orientaci�n de la herramienta. La posici�n angular de la herramienta permanece
fija durante la elaboraci�n (posici�n fija).
Con
par�metro IC=4.
Con el par�metro IC=4 y el par�metro A=0la herramienta se posiciona en paralelo a la trayectoria programada. Valores
del par�metro A distintos de 0 provocan la desviaci�n angular de la
orientaci�n de la herramienta. La posici�n angular de la herramienta permanece
paralela al recorrido durante la elaboraci�n (posici�n interpolada).
Ejemplo.
►Origen
m�quina delantero
Programaci�n de un inicio fresado inclinado
con herramienta perpendicular y sobre el lado derecho con respecto a la
trayectoria a seguir.
► Origen m�quina trasero
Programaci�n de un inicio fresado inclinado
con herramienta perpendicular y en el lado izquierdo con respecto a la
trayectoria a seguir.
Nota: la entrada y la salida autom�ticas no est�n previstas en los fresados
inclinados.
Detr�s de la instrucci�n G0R s�lo podr� haber
instrucciones G1R, G2R, G3R, G5R.
�ATENCI�N!
Dado
que si las elaboraciones con las herramientas inclinadas no se encuentran
perfectamente programadas pueden provocar da�os a la estructura de la m�quina,
es oportuno efectuarlas antes EN MODO SIMULADO.

Fresado lineal con herramienta inclinada - G1R
Permite
efectuar un fresado lineal sobre un plano inclinado respecto de la forma
ortogonal de las superficies del tablero; debe utilizarse con herramientas
inclinadas. La instrucci�n G1R se refiere a la cara 1; por este motivo, la cara
de trabajo debe ser siempre la cara 1.
Esta instrucci�n debe estar precedida por un
inicio fresado con herramienta inclinada o bien por otra instrucci�n de fresado
con herramienta inclinada.
Par�metros:
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
V
Velocidad de fresado.
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
�����������������������������������������������������
Ejemplo:
Programaci�n de fresado lineal inclinado con
punto inicial X=0, Y=0.
►Origen
m�quina delantero
► Origen m�quina trasero
�ATENCI�N!
Dado
que si las elaboraciones con las herramientas inclinadas no se encuentran
perfectamente programadas pueden provocar da�os a la estructura de la m�quina,
es oportuno efectuarlas antes EN MODO SIMULADO.

Fresado circular horario con herramienta inclinada - G2R
Define un tramo
de fresado circular (o arco de c�rculo) sobre un plano inclinado respecto de la
forma ortogonal de las superficies del tablero, con avance en sentido horario.
Como alternativa a la definici�n del centro es posible definir el radio del
arco seg�n la siguiente convenci�n: si el radio es positivo, el centro cae a la
izquierda de la l�nea imaginaria que va desde el punto inicial al final, de
otro modo el centro cae a la derecha de dicha l�nea. La instrucci�n G2R se
refiere a la cara 1; por este motivo, la cara de trabajo corriente debe ser
siempre la cara 1.
Esta
instrucci�n debe estar precedida por un inicio fresado con herramienta
inclinada o bien por otra instrucci�n de fresado con herramienta inclinada.
Par�metros:
X
Coordenada X de fin de fresado.
Y
Coordenada Y de fin de fresado.
Z
Profundidad de fin de fresado (medida seg�n
la inclinaci�n de la herramienta).
H
Altura del punto final de trabajo desde la
mesa de trabajo (cota a la que debe bajar la herramienta con referencia a la
mesa de trabajo de la m�quina).
I
Coordenada X del centro del arco.
J
Coordenada Y del centro del arco.
V
Velocidad de fresado.
r
Radio del arco.
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
�Ejemplo:
►Origen
m�quina delantero
Programaci�n de fresado circular horario
inclinado con punto inicial X=450, Y=100.
► Origen m�quina trasero
Programaci�n de fresado circular horario
inclinado con punto inicial X=350, Y=0.
�ATENCI�N!
Dado
que si las elaboraciones con las herramientas inclinadas no se encuentran
perfectamente programadas pueden provocar da�os a la estructura de la m�quina,
es oportuno efectuarlas antes EN MODO SIMULADO.

Fresado circular antihoraria con herramienta inclinada -
G3R
Define un tramo
de fresado circular (o arco de c�rculo) sobre un plano inclinado respecto de la
forma ortogonal de las superficies del tablero, con avance en sentido
antihorario. Como alternativa a la definici�n del centro es posible definir el
radio del arco seg�n la siguiente convenci�n: si el radio es positivo, el
centro cae a la izquierda de la l�nea imaginaria que va desde el punto inicial
al final, de otro modo el centro cae a la derecha de dicha l�nea. La
instrucci�n G3R se refiere a la cara 1; por este motivo la cara de trabajo
corriente debe ser siempre la cara 1.
Esta
instrucci�n debe estar precedida por un inicio fresado con herramienta
inclinada o bien por otra instrucci�n de fresado con herramienta inclinada.
Par�metros:
X
Coordenada X de fin de fresado.
Y
Coordenada Y de fin de fresado.
Z
Profundidad de fin de fresado (medida seg�n
la inclinaci�n de la herramienta).
H
Altura del punto final de trabajo desde la
mesa de trabajo (cota a la que debe bajar la herramienta con referencia a la
mesa de trabajo de la m�quina) .
I
Coordenada X del centro del arco.
J
Coordenada Y del centro del arco.
V
Velocidad de fresado.
r
Radio del arco.
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
Ejemplo:
►Origen
m�quina delantero
Programaci�n de fresado circular antihorario
con punto inicial X=350, Y=0

► Origen m�quina trasero
Programaci�n de fresado circular antihorario con
punto inicial X=450, Y=100
�ATENCI�N!
Dado que si las elaboraciones con las herramientas inclinadas no se
encuentran perfectamente programadas pueden provocar da�os a la estructura de
la m�quina, es oportuno efectuarlas antes EN MODO SIMULADO.

Tramo tangente al tramo precedente con herramienta
inclinada - G5R
Define un tramo
de fresado tangente al tramo precedente, con herramienta inclinada. La
instrucci�n G5R se refiere a la cara 1; por este motivo, la cara de trabajo
debe ser siempre la cara 1.
Esta
instrucci�n debe estar precedida por un inicio fresado con herramienta
inclinada o bien por otra instrucci�n de fresado con herramienta inclinada.
Par�metros:
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

L
Longitud del segmento (s�lo si G = 1 o bien
G = -1).
V
Velocidad de fresado.
Q
Offset angular respecto al par�metro A (para
cabezas especiales Benz configuradas como herramental con tipo M, N, O; v�ase
Manual de configuracion de las cabezas).
Ejemplos:
►Origen
m�quina delantero
1) Programaci�n de un tramo de fresado
inclinado tangente a un segmento con punto inicial X=450, Y=100.
2) Programaci�n de un tramo de fresado
inclinado tangente a un segmento con punto inicial X=350, Y=0.
3) Programaci�n a un tramo de fresado
inclinado tangente a un arco con punto inicial X=370, Y=50.
► Origen m�quina trasero
1) Programaci�n de un tramo de fresado inclinado tangente a un segmento
con punto inicial X=350, Y=0.
2) Programaci�n de un tramo de fresado inclinado
tangente a un segmento con punto inicial X=450, Y=100.
3) Programaci�n de un tramo de fresado
inclinado tangente a un arco con punto inicial X=370, Y=50.
�ATENCI�N!
Dado
que si las elaboraciones con las herramientas inclinadas no se encuentran
perfectamente programadas pueden provocar da�os a la estructura de la m�quina,
es oportuno efectuarlas antes EN MODO SIMULADO.

Conexi�n entre fresados - GFIL
Realiza un
fresado circular de conexi�n entre el fresado programado antes de esta
instrucci�n y el fresado programado despu�s de esta instrucci�n. Esta
instrucci�n conecta cualquier fresado lineal o circular con otro fresado
cualquiera, lineal o circular.
Par�metros:
r
Radio de conexi�n.
V
Velocidad de fresado.
La secuencia de programaci�n es la siguiente:
1. teclear el primer tramo;
2. teclear el segundo tramo;
3. insertar un l�nea con GFIL entre las dos precedentes.
El sistema calcula el punto inicial y final de
la conexi�n en autom�tico.
Ejemplos:
1) Programaci�n de una conexi�n con radio de
50 mm entre dos fresados lineales
Encabezamiento
H DX=450 DY=300 DZ=20 -A C=0 T=0 R=1 *MM
/�prueba�
Inicio fresado
G0 X=0 Y=0 Z=10 T=101 V=5000 S=16000 E=1
D=30
Primer segmento
G1 X=150 Y=250
Conexi�n�������
GFIL r=50
Segundo segmento
G1 X=300 Y=50
►Origen
m�quina delantero

► Origen m�quina trasero
2) Programaci�n de una conexi�n con radio de
100 mm entre dos fresados circulares
Encabezamiento
H DX=450 DY=300 DZ=20 -A C=0 T=0 R=1 *MM
/"prueba"
Inicio fresado��
G0 X=280 Y=235 Z=10 T=101 V=5000 S=16000 E=1
D=30
Primer arco
G3 X=150 Y=150 r=150
Conexi�n�������
GFIL r=100
Segundo arco
G2 X=50 Y=50 r=-75
►Origen
m�quina delantero

► Origen m�quina trasero
�������������������������������������������������������������������

Chafl�n entre fresados - GCHA
Realiza un
fresado circular de chafl�n entre el fresado programado antes de esta
instrucci�n y el programado despu�s de esta instrucci�n. Las instrucciones
anterior y posterior a la instrucci�n de biselado pueden ser un fresado
cualquiera lineal o circular.
Par�metros:
I
Longitud del primer tramo a achaflanar.
L
Longitud del segundo tramo a achaflanar.
V
Velocidad de fresado.
�����������������������������������������������������
Ejemplo:
Programaci�n de chafl�n entre dos fresados
lineales.
►Origen
m�quina delantero
► Origen m�quina trasero
La secuencia de programaci�n es la siguiente:
1. escribir el primer tramo;
2. escribir el segundo tramo;
3. insertar un l�nea con GCHA entre las dos precedentes.
El sistema calcula el punto inicial y final en
autom�tico.
Encabezamiento
H DX=400 DY=250 DZ=20
-A C=0 T=0 R=1 *MM /�corso�
Inicio fresado
G0 X=0 Y=0 Z=10 T=101
Segmento��������
G1 X=400 Y=0
Chafl�n����������
GCHA l=100 L=50�������
Segmento
G1 X=400 Y=250

### 5.2.2 Instrucciones
modales
Desplazamiento del origen del tablero en tope - O�
Desplaza el
origen del tablero en tope a la posici�n programada; todas las instrucciones
que siguen se refieren al nuevo origen.
Par�metros:
X
Origen en X.
Y
Origen en Y.
Z
Origen en Z.
f
Si ha sido programado con el n�mero de una
cara (1-5), habilita la instrucci�n s�lo para el origen de la cara planteada.
Ejemplo:
►Origen
m�quina delantero
►Origen
m�quina trasero

Cara de trabajo - F
Define la cara
de trabajo activa.
Grupo:
instrucciones texto

=
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
Ejemplo:
Referencias para el origen m�quina delantero:
Referencias para el origen m�quina trasero:
Nota: para interpolar
las caras laterales (F2, F3, F4, F5), Xilog
Plus mira el tablero de la cara delantera (F4) a la trasera (F5) y de la
cara izquierda (F3) a la derecha (F2) como si fuera transparente; de este modo,
se invierten los arcos del c�rculo (si en F4 es horario, en F5 es antihorario y
si en F3 es horario, en F2 es antihorario) y la correcci�n del radio (si en F4
es Izq. en F5 es Der. y si en F3 es Izq. en F3 es Der.).
Ejemplo:

Correcci�n herramienta - C
Habilita la
correcci�n de la trayectoria del mandril en funci�n de las caracter�sticas de
la fresa montada. Si la fresa es de vela (tipo F), la correcci�n es igual al
radio declarado en la herramienta, es decir, el �di�metro �til�; si la fresa es
de disco (tipo D), la correcci�n es igual a la mitad del espesor de la hoja
declarada en el equipamiento.
Grupo:
instrucciones texto

=
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
Correcci�n 1 + correcci�n 3 (s�lo para
fresas de disco).

23
Correcci�n 2 + correcci�n 3 (s�lo para
fresas de disco).

S
Cota de sobremetal.
Ejemplo:

Incremental en X - IX
Habilita la
programaci�n incremental en la direcci�n X. La cota activada como incremental,
programada en una instrucci�n operativa, asume un significado que no es m�s de
posicionamiento respecto del origen del tablero, sino de diferencia del valor
que dicha cota hab�a asumido despu�s de la ejecuci�n de la anterior instrucci�n
operativa.
Grupo:
instrucciones texto

=
Valores admitidos:

0
Inhabilita la programaci�n incremental en X.

1
Habilita la programaci�n incremental en X.
Ejemplo:
Incremental en Y - IY�
Habilita la
programaci�n incremental en la direcci�n Y. La cota activada como incremental,
programada en una instrucci�n operativa, asume un significado que no es m�s de
posicionamiento respecto del origen del tablero, sino de diferencia del valor
que dicha cota hab�a asumido despu�s de la ejecuci�n de la anterior instrucci�n
operativa.
Grupo:
instrucciones texto

=
Valores admitidos:

0
Inhabilita la programaci�n incremental en Y.

1
Habilita la programaci�n incremental en Y.
Ejemplos:

Especular en X - SX�
Cambia el
origen en X desplaz�ndolo hacia el �ngulo opuesto. Esta instrucci�n se activa
con la entrada autom�tica en el perfil o el inicio fresado.
Grupo:
instrucciones texto

Par�metros:
=
Valores admitidos:

0
Recupera la referencia normal en X.

1
Desplaza la referencia en X.

M
Invierte el sentido de los fresados
circulares.

0
Para no invertir.

1
Para invertir.
Ejemplo:
Especular en Y - SY
Cambia el
origen en Y desplaz�ndolo hacia el �ngulo opuesto. Esta instrucci�n se activa
con la entrada autom�tica en el perfil o el inicio fresado.
Grupo:
instrucciones texto

Par�metros:
=
Valores admitidos:

0
Recupera la referencia normal en Y.

1
Desplaza la referencia en Y.

M
Invierte la direcci�n de los fresados
circulares.

0
Para no invertir

1
Para invertir
Ejemplo:

Plano inclinado - PL
Define un plano
distinto de las 5 caras que Xilog Plus crea en autom�tico. Puede girar
alrededor del eje Z o del eje X. Un plano inclinado sirve para poder crear
geometr�as perpendiculares a dicho plano.
Par�metros:
X
Coordenada X del origen del plano (respecto
al origen del tablero).
Y
Coordenada Y del origen del plano (respecto
al origen del tablero).
Z
Coordenada Z del origen del plano (respecto
al origen del tablero).
Q
�ngulo de rotaci�n alrededor del eje Z
(origen m�quina delantero: positivo en sentido antihorario; origen m�quina
trasero: positivo en sentido horario).
R
�ngulo de rotaci�n alrededor del eje X
(origen m�quina delantero: positivo en sentido antihorario; origen m�quina
trasero: positivo en sentido horario).
El par�metro F debe valer siempre 1 con la
instrucci�n modal F. Los par�metros X, Y, Q, R son obligatorios.
Una instrucci�n PL queda anulada por:
� otra instrucci�n PL;
� la llamada de una cara est�ndar.
Para restablecer un plano inclinado, hay que
insertar otra instrucci�n PL con todos los par�metros a 0 como se indica en el
ejemplo siguiente.
Si todos los par�metros valen cero se
restablece la cara 1.
Ejemplo:
Programaci�n de un plano inclinado con
or�genes X=500, Y=0 , Z=0, a 45� del eje Z y a 90� del eje X.
►Origen
m�quina delantero
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

Asigna un valor a variable - SET
Con esta
instrucci�n es posible modificar temporalmente (s�lo en el programa donde se ha
insertado) algunos par�metros de sistema establecidos por el fabricante del
centro de trabajo. Adem�s de la instrucci�n SET, hay que escribir un nombre
predefinido con el que se determina el par�metro a modificar.
Grupo:
instrucciones texto

Los nombres predefinidos de la instrucci�n SET
son:
AUTOTOOL
Habilita/inhabilita el cambio de herramienta
en tiempo oculto (cambio de herramienta en el mandril principal mientras la
perforadora trabaja), si el modelo y la configuraci�n de la m�quina lo
permiten.

0 = inhabilita el cambio de herramienta en
tiempo oculto

1 = habilita el cambio de herramienta en tiempo
oculto con movimiento� en X y en Y

2 = habilita el cambio de herramienta en
tiempo oculto con movimiento� s�lo en
X

DONTCARE
La instrucci�n SET DONTCARE=1 fuerza Xilog
Plus a no emitir el mensaje �No existe cota de seguridad encima de la pieza�
para el siguiente trabajo.
La instrucci�n s�lo tiene efecto en los
casos recuperables (v�ase: Ap�ndice N � Notas: Traslaciones
sobre la mesa) y s�lo sobre el trabajo siguiente; entre SET DONTCARE=1 y
trabajo no deben existir otras instrucciones. Con el uso de la instrucci�n
SET DONTCARE=1 el programador se asume la responsabilidad de controlar
directamente las traslaciones (mediante N o XN) de modo que se eviten choques
contra los tableros y se garantice que las posibles rotaciones del Vector se
realicen fuera de la pieza.
La instrucci�n SET DONTCARE=1 obliga
XilogPlus a no controlar la coherencia de la programaci�n de las
instrucciones �PB � E=4� utilizadas en el �mbito de los planos motorizados
para el movimiento de los dispositivos de bloqueo con la pieza bloqueada.
Remitirse al c�p.9.4 para mayor informaci�n.

JERK
Para optimizar la utilizaci�n de la m�quina
en sus fases de trabajo, se ha habilitado una funci�n software especial
(denominada Jerk) para la modificaci�n de la respuesta de la m�quina (y por
lo tanto su comportamiento din�mico) conforme a la pieza trabajada. Dicha
funci�n es capaz de ejercitar una aplicaci�n progresiva de la aceleraci�n de
la m�quina regulando la ley de evoluci�n.
De este modo, se consiguen tiempos de parada
y aceleraci�n considerablemente reducidos, permitiendo ahorrar notablemente
los tiempos totales de ejecuci�n de la pieza reduciendo el esfuerzo de la
m�quina. Los resultados que pueden obtenerse est�n relacionados con el tipo
de pieza en ejecuci�n, y, son m�s sensibles cuanto m�s elevadas son las fases
de desplazamiento r�pido (G0) y de aceleraci�n y deceleraci�n;� por ejemplo, se obtiene un ahorro m�ximo
en los ciclos de taladrado, en cambio el ahorro es m�nimo en los ciclos s�lo
de fresado con desplazamientos consecutivos lentos (G1).
Se brinda al usuario con experiencia, la
posibilidad de optimizar la respuesta de la m�quina,� cambiando como mejor le parezca la
din�mica seg�n el compromiso velocidad-precisi�n. El operador puede programar
el �nivel� de regulaci�n de la funci�n Jerk, si prefiere una con respecto a
la otra, o seleccionar una situaci�n neutra que tenga en cuenta las dos
exigencias.
Estamos hablando de usuario con experiencia, puesto que la utilizaci�n de esta
funci�n requiere un conocimiento profundo de las distintas exigencias de
trabajo adem�s de los varios instrumentos de programaci�n (se solicita la
edici�n manual del programa, la capacidad de lectura del listado ISO o XISO
en presencia de Xilog Plus, y el conocimiento de los instrumentos de edici�n
del listado mismo).
Si el operador no desea, o no se siente
capacitado para realizar dichas modificaciones, puede abstenerse
tranquilamente de utilizarlas, manteniendo los valores programados por
defecto de SCM Group S.p.A., que de todas maneras garantizan un digno
compromiso entre las exigencias de acabado y de desbaste, sin exasperar la
regulaci�n en cada caso.
Dicha instrucci�n, debe introducirse rigurosamente antes de la �G0� de
acercamiento a la pieza para el inicio del trabajo.
Valores aconsejados:

60: taladro.

90: desbaste.

>=160: acabado.

Detalladamente, m�quina por m�quina, los
valores t�picos registrados en SCM Group S.p.a. (m�quina neutra - default),
son:

Serie RECORD familia 100-121-130
>= 180 (acabado)

Serie RECORD familia 240
>= 180 - 200 (acabado)

Serie RECORD familia 260
>= 260 (acabado)

Serie Ergon
>= 90 (acabado)

0 = restablecimiento valores por defecto, en
un programa en el que se hab�an cambiado intencionadamente con anterioridad
(tambi�n un reset de CNC, restablece las condiciones por defecto).

Activaci�n
macro para niveles Jerk, a cargo del operador
La regulaci�n se efect�a por medio de la
consultaci�n en el part-program, de la siguiente l�nea de instrucci�n ISO, en
la que, especificando el valor deseado para los par�metros �XXX�, se
conseguir� la regulaci�n deseada.
G120EJxxx (por medio de esta l�nea de instrucci�n, consulto el programa ISO de
sistema� %10120 y pido la
activaci�n� de las JERK)
Donde: �XXX� = valor de regulaci�n de las
JERK (valor m�nimo programable =60).
NOTA. �nicamente la realizaci�n de los tests preventivos de trabajo y la
experiencia, podr�n aconsejar el correcto valor que hay que utilizar en cada
programa. La l�nea de programa en objeto, podr� repetirse varias veces en el
mismo programa, cada vez que el operador lo considere oportuno. Por el
momento, la gesti�n de esta optimizaci�n no est� prevista en los
post-processor distribuidos por SCM Group S.p.A., por lo tanto la activaci�n
y la selecci�n de la posici�n de la l�nea de programaci�n en el programa,
deber� efectuarla totalmente el operador por medio de la edici�n manual del
mismo. �En caso de incertidumbre dejar el valor por defecto!

�ATENCI�N!
No modificar
ni borrar:
� el
programa %11000 (archivo reservado SCM Group S.p.a. para configuraci�n
m�quina)
� el
programa %10120 (archivo reservado SCM Group S.p.a. para habilitaci�n Jerk)

JERK3D
(gruppo
Prisma)
Programa el nivel de correcci�n de los
cantos en una macro.

0 = disabilitato.

1 = desbaste.

2 = inhabilitado.

3 = acabado.

V�ase: Ap�ndice H - Grupo
Prisma.

NOPF45
Realiza una subida, a cota de rozamiento,
entre trabajos sucesivos (llevando a cota de rozamiento el eje Z). �til en
los centros de trabajo con barras y ventosas para evitar que las herramientas
y las barras choquen al desplazarse lateralmente. V�ase tambi�n: instrucci�n XNOP.

-1 = realiza siempre una subida a cota de
rozamiento entre trabajos sucesivos.

23 = realiza una subida a cota de rozamiento
entre trabajos sucesivos en el lado 2 o en el lado 3.

1 = realiza una subida a cota de rozamiento
entre trabajos sucesivos en el lado 4 o en el lado 5.

0 = anula la �ltima condici�n programada
(con valores mayores o menores que 0) sin ninguna subida entre trabajos
sucesivos.

PRU
Permite utilizar el prensor mec�nico, si se
encuentra presente y es de tipo modal.

0 = prensor alto

1 = prensor bajo (activo)� en la posici�n vertical n�1
2 = prensor bajo (activo) en la posici�n
vertical n�2
3 = prensor bajo (activo) en la posici�n
vertical n�3
4 = prensor bajo (activo) en la posici�n
vertical n�4
El prensor puede ser programado activo
eligiendo entre cuatro diferentes posiciones mec�nicas (1-4); la dimensi�n
total en Z que asume el dispositivo para cada posici�n (un valor negativo o
nulo indica que no hay dimensiones totales a considerar) est� definido en los
par�metros correspondientes de configuraci�n en Pheads.cfg� (�Dimensi�n total en Z del dispositivo
especial para posici�n 1�N�). Si el par�metro �Tipo de dispositivo
especial� en Pheads.cfg es diferente de �4�, los valores de� PRU superiores a 1 no tienen efecto
(tratados como el valor 1).
El comportamiento del dispositivo, en caso
de m�s trabajos consecutivos con la misma herramienta y con el prensor
siempre activo, puede ser de dos tipos:
a) el prensor se� excluye
neum�ticamente en el pasaje entre la fin del trabajo corriente y el inicio
del sucesivo, y la cota de seguridad en Z para el pasaje por encima de la
pieza est� determinada solamente por la dimensi�n total vertical de la
herramienta�
b) el prensor se mantiene siempre bajo y el pasaje entre dos trabajos
sucesivos se realiza a una cota calculada en base al valor m�ximo entre la
dimensi�n total vertical de la herramienta y aquella del prensor configurado
en Pheads.cfg (�Dimensi�n total en Z del dispositivo especial para
posici�n 1�N� � que se muestra en el manual de los par�metros de
configuraci�n).
El primer comportamiento (a) es el est�ndar
y se realiza cuando no se especifica la presencia del prensor en Pheads.cfg,
no asignando por tanto el valor �4� al par�metro �Tipo de dispositivo
especial�.
El segundo comportamiento (b) se realiza
cuando se especifica la presencia del prensor en Pheads.cfg asignando el
valor �4� al par�metro �Tipo de dispositivo especial�.

DUSTPAN
Permite utilizar el dispositivo transporta
virutas (pala) montado sobre una cabeza operadora.

0= dispositivo transporta virutas alto
(inactivo)

1= dispositivo transporta virutas bajo
(activo) en la posici�n vertical n�1
2= dispositivo transporta virutas bajo
(activo) en la posici�n vertical n�2
3= dispositivo transporta virutas bajo
(activo) en la posici�n vertical n�3
4= dispositivo transporta virutas bajo
(activo) en la posici�n vertical n�4
Remitirse al AP�NDICE O. para todos los
detalles acerca de la programaci�n del dispositivo transporta virutas.

STANDBY
Determina una parada temporal durante la
elaboraci�n. Para seguir la elaboraci�n a partir del punto en el que se ha
interrumpido, hay que pulsar la tecla Start.

0 = sin parada

1 = parada sin posibilidad de desbloquear la
pieza (�til para quitar las virutas)

2 = parada con posibilidad de desbloquear la
pieza

TAU
Mando del palpador. Admite los siguientes
valores:
0 = inhabilita el dispositivo.
> 0 = ganancia del dispositivo.
No se admiten valores negativos.
Para el uso de la instrucci�n SET TAU con
las m�quinas Ergon, v�ase: Ap�ndice F - M�quinas Ergon.

TRACEMODE
Preside la generaci�n del archivo de trace
(v�ase: instrucci�n TRACE).
(default)/0 = el archivo de trace s�lo se
genera en el ambiente de edici�n de los programas.
1 = el archivo de trace s�lo se genera en el
ambiente de ejecuci�n.
2 = el archivo de trace se genera en ambos
ambientes.
El nombre del archivo de report generado en
ambiente de ejecuci�n proviene del nombre del programa, al cual se a�ade la
fecha y la hora corriente.
Ejemplo:
CheckPositions 2004-11-23 14-24-44.log
El archivo de report se memoriza en la
carpeta indicada en la secci�n [TRACE] del archivo Xilog3.ini.
Ejemplo:
...
[TRACE]
reportDir=c:\TraceDir\
�
Si en el archivo Xilog3.ini no aparece la
indicaci�n de la carpeta, el archivo de report se memoriza en la misma
carpeta del programa.

TWIN
(m�quinas
Ergon)
El uso de la TWIN no obliga a especificar en
el campo T la lista de las herramientas de todas las cabezas que deben
trabajar en sincr�nico, ser� suficiente indicar la herramienta (en caso de
electromandril) o de los husos (en caso de taladradora) s�lo para la cabeza
�master�, o bien para la cabeza respecto a la cual se elaboran las cotas del
programa.
► El valor asignado al par�metro TWIN debe estar compuesto por cifras
crecientes, ya que el PLC, tal y como se especific� arriba, impone que la
cabeza �master�, respecto a la cual se alinean las otras cabezas a
sincronizar, pertenezca siempre al grupo-zeta de menor peso:
Ejemplos: �������
SET
TWIN=1234; per para indicar la sincronizaci�n de los
grupos 1, 2, 3 y 4.
SET
TWIN=34; para indicar la sincronizaci�n de los
grupos 3 y 4.
SET
TWIN=23; para indicar la sincronizaci�n de los
grupos 2 y 3.
► La herramienta indicada en el campo T de las instrucciones, deber�
referirse a una cabeza que pertenezca a un grupo-zeta y cuyo n�mero sea igual
a la primera o a la �ltima cifra del valor de TWIN:
�
Ejemplos:
SET
TWIN=1234; T=1nn o T=11nn o T=4nn o T=14nn.
SET
TWIN=34; T=3nn o T=13nn o T=4nn o T=14nn.
SET
TWIN=23; T=2nn o T=12nn o T=3nn o T=13nn.
�����������
Lo �nico que cambia es respecto a qu� cabeza
se realizar�n los c�lculos a los que referir las cotas X/Y/Z.
► Dicha instrucci�n, por su naturaleza, debe necesariamente
introducirse en el inicio del perfil en el cual se desea que se aplique.
Luego, por ejemplo, se introduce antes de una posible XGIN presente:
H ������� DX=�
DY=� DZ=� BX=� BY=� BZ=� /�Def�
SET
TWIN=13
XGIN
XG0 �� X=� Y=� Z=� T=305;
Trabajan 300 y 100 (herr. 5 � ref. T3)
XG1 �� X=�
Y=� Z=�
XGOUT
SET TWIN=24
XGIN
XG0 �� X=� Y=� Z=� T=205;
Trabajan 200 y 400 (herr. 5 � ref. T2)
XG1 �� X=�
Y=� Z=�
XGOUT
�
► La SET TWIN es modal, es decir, su programaci�n considera �v�lido su valor, en caso de una nueva
reprogramaci�n.� Por ejemplo:
H DX=� DY=� DZ=� BX=� BY=� BZ=� / � Def �
SET TWIN=13
XG0 X=� Y=� Z=� T=305; Trabajan 300 y
100 (herr. 5)
XG1 X=� Y=� Z=�
SET TWIN=24
XB X=� Y=� Z=� T=1407 1408; Trabajan 1400 y 1200 (husos 7, 8)
XB X=� Y=� Z=� T=1401 1402 1403; Trabajan 1400 y 1200 (husos 1, 2, 3)
SET TWIN=0; Anula TWIN
XG0 X=� Y=� Z=� T=305; Trabaja
300, sola
XB X=� Y=� Z=� T=1407 1408; Trabaja 1400, sola
XG0 X=� Y=� Z=� T=306 115; Trabajan 300 (herr.6) y 100 herr.15)

V�ase: Ap�ndice F �
M�quinas Ergon.

UNROLLMODE
(gruppo
Prisma)
Habilita la funci�n de autodesenrollado de
la cabeza prisma durante los recorridos de fresado en G03D y G0R. La cabeza
al no poder continuar el tramo de perfil, sube, se desenrolla, baja y
reemprende el recorrido del perfil suspendido. La entrada y la salida pueden
ser personalizadas con tramos en arcotangencia para
permitir una conexi�n a la pieza lo m�s suave posible. El valor de este
par�metro es modal.
Los valores admitidos son:
0 = Autodesenrollado deshabilitado.
1 = Autodesenrollado con entrada y salida
perpendiculares.
2 = Autodesenrollado con entrada en
tangencia y salida perpendicular.
3 = Autodesenrollado con entrada
perpendicular y salida en tangencia.
4 = Autodesenrollado con entrada y salida en
tangencia.

UNROLLRMUL
(gruppo
Prisma)
Factor de multiplicaci�n del radio
herramienta durante el estado de entrada salida en arcotangencia durante la
fase de autodesenrrollado de la cabeza Prisma. V�ase la SET UNROLLMODE. El
valor de default es 1; el valor programado es modal.

USAW
Modal, permite definir un desplazamiento s de la cuchilla, -0.5 mm <= s <= 0.5 mm, octogonal a la
trayectoria lineal programada. Se aplica s�lo a las� elaboraciones con cuchilla y s�lo para fresados lineales que
poseen las mismas coordenadas X,Y que el fresado lineal precedente.

MIRRORHEADSPOS�

(grupo
Prisma)
Solicitud de �reflejo� del �ngulo B
seleccionado por el sistema para el posicionamiento de la cabeza Prisma. Instrucci�n
no modal.
Explicaci�n: el aumento de la carrera de B
ofrece la posibilidad de alcanzar inclinaciones de la herramienta con B
positivo y B negativo.
El enfoque tradicional de alcanzar la
posici�n solicitada con el menor alcance posible ha sido superado con la
nueva, por tanto se prefiere el alcance menor con B positivo y solo si esto
no es posible, se recupera, si existe, la soluci�n con menor desbrace de B
negativo.
Para los trabajos de perforaci�n y fresado
en caras est�ndar, B positivo existe siempre, mientras para los perfiles de
tipo� R o 3D entra en juego el final
de carrera de C en todo el recorrido herramienta del perfil. Esto puede
significar no tener en cuenta enfoques a la pieza con B positivos y llevar a definir un �ngulo B de default positivo,
y por tanto determinar a priori c�mo
posicionar la dimensi�n total del mandril.
Para los casos particulares est� prevista la
SET correspondiente che permita selecci�n opuesta, reflejada de B.
Ejemplo: si aquella particular soluci�n
positiva de B causa la colisi�n del mandril con la pieza, la SET
MIRRORHEADPOS=1 impone la soluci�n reflejada de B.

�ATENCI�N!
Si
se ha programado la instrucci�n SET USAW, comprobar siempre que todos los
fresados lineales con cuchilla que se suceden a otro fresado lineal� con las mismas coordenadas X e Y del
precedente (que corresponden a todos los fresados lineales �en el lugar� )
est�n programados FUERA DE LAS DIMENSIONES TOTALES DEL TABLERO.

ZFAST�����������
A�ade otro posicionamiento intermedio a la
cota Z programada, para todos los trabajos programados despu�s de esta
instrucci�n.
Ejemplo:
si r�pido/lento eje Z = 20 (en los
par�metros GENDATA) la m�quina funciona en R�PIDO hasta z =20 y luego
funciona en LENTO a la cota de trabajo.
Si se programa zfast = 100 se
detiene a 100 en R�PIDO luego funciona a�n en R�PIDO a 20 y luego funciona en
LENTO a la cota de trabajo.
Si se programa D = 100 se detiene en 100 en
R�PIDO luego funciona en LENTO a la cota de trabajo.
Si se programa ZFAST=100 y D =
80 se detiene en 100 en R�PIDO luego funciona a�n en R�PIDO a 80 y
sucesivamente en LENTO a la cota de trabajo.

Ejemplo:

Cambiar referencia - REF�
La instrucci�n
REF modifica las caracter�sticas del panel definidas en el encabezamiento
(header) del programa; por lo tanto, los trabajos siguientes se refieren a las
nuevas caracter�sticas.
Grupo:
instrucciones texto

Par�metros:
DX
Dimensi�n en X del tablero.
DY
Dimensi�n en Y del tablero.
DZ
Dimensi�n en Z del tablero.
FLD
�rea de trabajo a la que se debe asociar (A,
B, C, D, AB, BA, CD, DC, AD, DA).
BX
Distancia en X del cero del tablero con
respecto al cero del campo.
BY
Distancia en Y del cero del tablero con
respecto al cero del campo.
BZ
Dimensi�n en Z de un posible espesor situado
debajo del tablero.
�����������������������������������������������������������
Todos los par�metros son opcionales; si
existen, sustituyen a los correspondientes programados en el encabezamiento
(header) del programa.
Una instrucci�n REF sin par�metros reestablece
las caracter�sticas especificadas en el encabezamiento (header) del programa.
�ATENCI�N!
La
dimensi�n en Z del panel se utiliza para optimizar las traslaciones de los
cabezales entre trabajos realizados en caras distintas; por lo tanto, es
indispensable que en el campo DZ se introduzca la dimensi�n m�xima efectiva en
Z de la pieza; en caso contrario pueden ocurrir peligrosos choques entre los
cabezales y la pieza.
Los trabajos sucesivos a una instrucci�n REF
son efectuados a partir del tope del �rea de trabajo especificada en la REF.

### 5.2.3 Instrucciones de
gesti�n de subprogramas
Apertura de subprograma - S
Solicita como
subprograma un programa normal.
Grupo:
instrucciones texto

Par�metros:
/
Nombre del subprograma.
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
����������������������������������������������������������
En la casilla vac�a de la derecha se puede
introducir una lista de par�metros cuyo valor debe ser modificado en el
interior del subprograma/macro lanzado (v�ase: cap�tulo 6.4 - Pasaje de
par�metros a subprogramas y macros).
Para X, Y, Z no programados valen los valores
corrientes (para Z vale la �ltima cota de trabajo).
Un programa abierto mantiene en memoria sus
subprogramas: para activar las modificaciones gr�ficas de estos �ltimos hay que
cerrar y volver a abrir el programa principal.
�Atenci�n! La instrucci�n S no es id�nea para llamar programas que contienen
superficies inclinadas (instrucci�n PL), porque la traslaci�n se aplica s�lo a
las elaboraciones y no al origen de la superficie inclinada. Para esta
finalidad es necesario utilizar la instrucci�n SO.
�Atenci�n! Si el subprograma depende de un fichero de las variables entorno, para
un funcionamiento correcto del programa principal (que lo lanza) es necesario
que tambi�n en el encabezamiento del programa principal se haya programado el
mismo fichero de las variables entorno del subprograma.
Ejemplo:
►Origen
m�quina delantero
Obtener de un tablero de grandes dimensiones
cuatro piezas (subprogramas) como en la figura:
Para ello, hay que realizar las siguientes
operaciones:
crear en el editor un programa nuevo,
escribiendo en el Encabezamiento los datos del tablero.
Ahora, solicitar el primer subprograma
mediante la instrucci�n S.
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
crear en el editor un programa nuevo,
escribiendo en el Encabezamiento los datos del tablero.
Ahora, solicitar el primer subprograma
mediante la instrucci�n S.
A continuaci�n, solicitar una segunda vez el
primer subprograma, introduci�ndolo en la segunda posici�n.
Solicitar el segundo subprograma, introducir
el origen como en la figura y girarlo 90�.
Repetir las operaciones para introducir el
�ltimo subprograma.

Subprograma optimizado - SO�
La instrucci�n
SO permite llamar un subprograma asoci�ndolo a una zona de trabajo; asimismo,
durante la ejecuci�n se mantienen las dimensiones reales de la pieza y, por lo
tanto, las posiciones de sus caras.
Grupo:
instrucciones texto

Par�metros:
/
Nombre del subprograma.
DX
Dimensi�n en X del tablero.
DY
Dimensi�n en Y del tablero.
DZ
Dimensi�n en Z del tablero.
FLD
�rea de trabajo a la que se debe asociar (A,
B, C, D, AB, BA, CD, DC, AD, DA).
BX
Distancia en X del cero del tablero con
respecto al cero del campo.
BY
Distancia en Y del cero del tablero con
respecto al cero del campo.
BZ
Dimensi�n en Z de un posible espesor situado
debajo del tablero.
En la casilla vac�a de la derecha se puede
introducir una lista de par�metros cuyo valor debe ser modificado en el
interior del subprograma/macro lanzado (v�ase: cap�tulo 6.4 - Pasaje de
par�metros a subprogramas y macros).
Excepto el nombre del subprograma, todos los
dem�s par�metros son opcionales; si existen, los par�metros opcionales
sustituyen a los correspondientes programados en el Encabezamiento (header) del
subprograma.
� Las instrucciones SO s�lo se pueden
solicitar dentro del programa principal. La instrucci�n SO define las
caracter�sticas de un tablero que se convierte en un espesor del tablero
principal definido en el Encabezamiento (header) del programa principal; este
�ltimo define las caracter�sticas del�
trabajo total (incluido el bloqueo de las piezas), y por lo tanto las
dimensiones DX, DY y DZ que en �l se especifican deber�an contener todos los
espesores.
� La dimensi�n en Z del panel se utiliza
para optimizar las traslaciones de los cabezales entre trabajos realizados en
caras distintas; por lo tanto, es indispensable que en el campo DZ se
introduzca la dimensi�n m�xima efectiva en Z de la pieza; en caso contrario
pueden ocurrir peligrosos choques entre los cabezales y la pieza.
� Para llamar un programa que contiene una
superficie inclinada (instrucciones PL/XPL) es preciso asignar a los par�metros
BX, BY, BZ los valores X, Y, Z del origen de la superficie inclinada.
� Un trabajo SO se realiza a partir del
tope del �rea de trabajo especificada en SO.
� Para los programas que contienen
instrucciones SO puede solicitarse la optimaci�n de los cambios herramienta
(v�ase el cap�tulo 7 �Optimizador de programas�);
la optimizaci�n consiste en reordenar los trabajos con el fin de minimizar el
n�mero de cambios de herramienta entre un trabajo y otro. La optimizaci�n de
los cambios de herramienta s�lo tiene efecto sobre las instrucciones SO
presentes en el programa principal.
�Atenci�n! Si el subprograma depende de un fichero de las variables entorno, para
un funcionamiento correcto del programa principal (que lo lanza) es necesario
que tambi�n en el encabezamiento del programa principal se haya programado el
mismo fichero de las variables entorno del subprograma.
### 5.2.4 Env�o de
mensajes al operador
Impresi�n mensaje - MSG
Los mensajes al
operador son informaciones enviadas al operador durante la elaboraci�n de la
pieza.
Par�metros:
�<l�nea>�
Mensaje.
(campos vac�os)
Introducir par�metros.
SBY���
Tipo de standby a efectuar.
INP
Nombre de la variable para el valor en
entrada.
Una MSG sin par�metros determina la
cancelaci�n del mensaje precedente.
A cada mensaje puede asociarse una petici�n de
introducci�n datos (par�metro INP).
Despu�s del env�o de un mensaje el programa
pieza puede seguir o detenerse en espera de que el operador introduzca el dato
posiblemente solicitado y/o accione el pulsador de Start.
La indicaci�n de standby (par�metro SBY a 1 �
2) determina la parada del programa pieza en espera de que se presione el
pulsador de Start; en caso de petici�n datos el programa pieza se
detendr� en cualquier caso simulando la indicaci�n de SBY=1.
Las instrucciones MSG se cargan
individualmente y aparecen con l�gica en funci�n del tipo:
MSG sin INPUT
El mensaje aparece en la ventana de los
mensajes; en presencia de standby el mensaje se cancela presionando el pulsador
de Start; en caso contrario, el mensaje se cancela tras la llegada de
una nueva MSG, posiblemente sin mensaje. En ambos casos la cancelaci�n tambi�n
tiene lugar al aceptar un Reset.
MSG con INPUT
El mensaje aparece en la ventana de los
mensajes y se visualiza un icono para se�alar la necesidad de introducci�n
datos (men� mandos/entrada
mensaje operador). El mensaje se borra con la
presi�n del pulsador de Start y al aceptar un Reset.
�
Ejemplo:
�
MSG �Esperar hasta que se complete el ciclo de
descarga�
�
MSG
�
MSG ��Quitar las virutas y pulsar
start-ciclo!� SBY=1
�
L ADX = 0
L ASX = 90
MSG �Introducir el �ngulo de corte a la
derecha� INP=ADX
MSG �Introducir el �ngulo de corte a la
izquierda� INP=ASX
IF ADX >
90 THEN
�
FI
�
L M�n = 0
L M�x = 4
L Campana = 0
MSG �Posici�n de la campana (de ?d a ?d)� M�n
M�x INP=Campana
IF Campana >=M�n AND Campana <= M�x THEN
ISO �M?d� 110+Campana
ELSE
PRINT �Posici�n de la campana=?d err�nea!�
Campana
FI

### 5.2.5### Programaci�n
de la mesa motorizada
PB
La instrucci�n
PB permite programar la mesa motorizada.
Par�metros:
B
N�mero de la barra. Este campo tambi�n puede
no programarse: si se lo programa, indica la barra que hay que desplazar; si
no est� programado, Xilog Plus seleccionar� cu�l barra hay que desplazar al
valor indicado en el campo� X.
X��������
Cota en X en la cual posicionar la barra.
En la casilla que sigue precedida por �,�
(cuando presente y editable seg�n las versiones y de las configuraciones)
debe indicarse el estado de la barra:
0 = posici�n barra libre (default)
1 = posici�n barra fija
Posici�n barra libre: el valor del campo �X� representa la cota en mm (o pulgadas) a la
cual debe ser posicionada la barra
Posici�n barra fija: el valor del campo �X� representa el n�mero de posici�n fija
(conocido tambi�n como �n�mero de ojal� - rango: da 1 a 16) al que
debe ser posicionada la barra - la cota que corresponde a la posici�n fija
est� determinada por la configuraci�n de los par�metros de la secci�n� AXIS.CFG�HOLEPLANE (v�ase c�p.9.12) � el n�mero de ojal se refiere a la
numeraci�n l�gica local al �rea de trabajo donde se ejecuta el programa (como
para el n�mero de barra).
Y1,
Y2�
Los valores Y1, Y2 etc. indican la posici�n
en Y del primero, segundo etc. borne o ventosa. Para cada valor indicar, en
la siguiente casilla precedida por �,�, la condici�n de estado del borne o
ventosa, representado por la cifra �unidad� del valor num�rico:

0 = borne cerrado.

1 = borne abierto.

2 = borne cerrado en bloqueo (con pieza� bloqueada).
El valor num�rico puede estar compuesto
tambi�n por las cifras decenas� y centenas� (formato
completo: Yn=xyz con �xy� de 1 a 64) que representan el n�mero de la
pieza/selector asociado con el borne Yn.
Ejemplo: Y1=120 significa que el borne n�1
est� cerrado en la pieza� (y por lo
tanto asociado al selector) n�mero 12.

E
Indica el tipo de operaci�n que se est�
haciendo en la mesa de trabajo:

0 = se ignora.

1 = operaciones de equipamiento mesa (una
sola en un programa pieza).

2 = operaciones de bloqueo de la pieza (una
sola en un programa pieza).

3 = bloqueo de PB que debe ser realizado
como movimiento intermedio durante el programa pieza (valor opcional si a la
instrucci�n PB sigue una instrucci�n�
de movimiento).
4 = bloqueo de PB que manda los movimientos
de los dispositivos con la pieza bloqueada
Todos los bloques de PB E=3 contiguos al de
PB E=2 (bloqueo) y contiguos entre si se asocian a la fase de bloqueo de la
pieza. La contiguidad no puede ser interrumpida por ninguna instrucci�n, ni
siquiera por las no operativas. En el caso de que un bloqueo de PB E=3 pueda
asignarse ya sea a la fase de bloqueo como a la de desbloqueo, se le asigna
la de bloqueo.
La m�scara de la instrucci�n, en su versi�n
m�s extensa, puede aparecer de la siguiente manera:
La programaci�n de las barras no necesita un
orden determinado. Si se especifica el n�mero de barra, dicho n�mero nunca
puede ser modificado. Si se especifica en cambio el n�mero del borne y hay un
error al programar las cotas Y, los bornes se invierten autom�ticamente (con
tres bornes, las inversiones posibles son s�lo borne 1 � borne 2 o bien borne 2
� borne 3).
La informaci�n correspondiente a las operaciones
de equipamiento de la mesa es importante, porque el equipamiento de la mesa en
una zona f�sica puede producirse al mismo tiempo que la ejecuci�n de otras
operaciones, por ejemplo, el trabajo de una pieza en otra zona f�sica. Por
consiguiente, el campo E permite anticipar el equipamiento de la mesa para el
trabajo siguiente.
NOTA: remitirse al
c�p. 9 para una descripci�n m�s amplia de las funciones que Xilog tiene para el
control del plano motorizado.

### 5.2.6 Instrucciones de
ayuda a la programaci�n
Comentario - ;�
Un comentario
es una l�nea de texto que comienza con el car�cter; o bien con el car�cter *.
Comentarios que inician con; pueden ponerse tambi�n al fondo de las otras
instrucciones.
Grupo:
instrucciones texto

Visualizaci�n mensaje - PRINT�
Permite la
visualizaci�n de un mensaje de diagn�stico, tras la visualizaci�n se bloquea
toda interpretaci�n ulterior del programa.
Grupo:
instrucciones texto

La instrucci�n est� formada por una cadena
entre dos puntas; eventualmente seguida por una lista de par�metros separados
por, al menos, un espacio. Los par�metros se asocian en sucesi�n a los formatos
de impresi�n introducidos en el mensaje; por lo tanto, el programador debe
poner atenci�n para introducir un formato por par�metro.
Un formato de impresi�n inicia con un punto
interrogativo (?); cuando PRINT encuentra el primer formato (de izquierda a
derecha), convierte el valor del primer par�metro despu�s del mensaje y lo
introduce en el mensaje en el lugar del formato, el segundo formato determina
la conversi�n del segundo par�metro y as� sucesivamente.
Los eventuales par�metros que sobren,
comparados a los formatos, se ignoran; los posibles formatos que sobren,
comparados a los par�metros, tambi�n se ignoran.
Un formato de impresi�n debe tener una de las
siguientes formas, cada una de las cuales est� asociada a un tipo de
visualizaci�n del par�metro correspondiente:
?x
n�mero hexadecimal comprendido entre 0000 y
FFFF;
?d
N�mero entero decimal comprendido entre
-32768 y 32767
?u
N�mero entero decimal comprendido entre 0 y
65535;����������
?D
N�mero entero
decimal comprendido entre -2147483648 y 2147483647;;�
?U
N�mero entero decimal comprendido entre 0 y
4294967295;
?f
N�mero comprendido entre 1.7E-308 y 1.7E+308
visualizado en la forma [-] dddd.dddd;
?e
N�mero comprendido entre 1.7E-308 y 1.7E+308
visualizado en la forma [-] d.ddd y [+/-] ddd;
?g�������
N�mero comprendido entre 1.7E-308 y 1.7E+308
visualizado en el formato ?f � ?e que produce la visualizaci�n
m�s compacta;
?c
Car�cter;
?s
Cadena de caracteres.
Si un punto interrogativo est� seguido por un
car�cter que no individualiza ning�n formato de impresi�n, dicho car�cter se
visualiza. Por lo tanto, para visualizar un punto interrogativo es necesario
usar la forma ??.
Ejemplo:
Memorizaci�n
mensaje - TRACE�
Permite
escribir un mensaje en un archivo dedicado; despu�s de la escritura, la
interpretaci�n del programa contin�a normalmente.
Grupo:
instrucciones texto

La instrucci�n est� formada por una cadena
entre dos puntas; eventualmente seguida por una lista de par�metros separados
por, al menos, un espacio.
Los par�metros se asocian seg�n la posici�n de
formados de impresi�n introducidos en el mensaje. Los formatos de impresi�n son
los mismos que valen para la instrucci�n PRINT.
La instrucci�n TRAZAS es efectiva s�lo en el
editor en el momento del dibujo completo de la pieza, por lo tanto, no tiene
efecto durante la memorizaci�n del programa ni durante las diferentes fases de
autom�tico.
Ejemplo: