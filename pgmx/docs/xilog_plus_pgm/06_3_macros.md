
# 6.3
Macro# s
Una macro es un subprograma especial
cuyo nombre se convierte en una instrucci�n del lenguaje. Las instrucciones de Xilog Plus son macros: como, por
ejemplo, la instrucci�n de perforaci�n B que el programa interpreta como un
simple comando aunque sirve para ejecutar funciones complejas. Las macros est�n
agrupadas en la barra de las instrucciones; ya sea por grupos de macro o por
macro sencillas representadas gr�ficamente mediante im�genes bitmap.
►Para escribir una macro, se puede utilizar el editor macro,
seleccionable en el men� Opciones/Editor macro. El
editor macro se puede utilizar como el editor de texto, pero algunas funciones,
disponibles en el editor de texto, no est�n habilitadas (por ejemplo, la
visualizaci�n del editor de ventosas).
►Despu�s de haber seleccionado el editor macro, hay que crear un nuevo
programa param�trico. Al guardar el programa creado, Xilog Plus solicita la asociaci�n del programa a una imagen
bitmap (extensi�n BMP), que debe tener las dimensiones 120 x 90 pixel. La
bitmap, que puede generarse con cualquier programa de dise�o, debe representar
gr�ficamente la funci�n de la macro. �sta se guarda con extensi�n PGM (por
ejemplo, BISAGRA.PGM).
►Para integrar correctamente la macro en el entorno de programaci�n,
habilit�ndola en la barra de instrucciones, hay que definir el grupo de macro
al que pertenece. Por ejemplo, las instrucciones de Xilog Plus XB, XBO y XBR pertenecen al grupo de perforaci�n,
representado por una de las im�genes bitmap de la barra de instrucciones. Para
definir un nuevo grupo de macro e introducir una nueva macro como elemento, hay
que:
1. crear una carpeta dentro de la carpeta FXC (que est� dentro de la
carpeta SCM GROUP/XILOG PLUS), cuyo nombre no puede tener extensiones (por
ejemplo, �HOJA�);
2. generar una imagen bitmap de 32 x 32 pixel, que represente gr�ficamente
el grupo y que tenga el mismo nombre de la carpeta (por ejemplo, �HOJA.BMP�), y
guardarla dentro de la carpeta FXC;
3. copiar el archivo PGM que�
representa la macro creada (como, por ejemplo, �BISAGRA.PGM�) en la
carpeta del grupo de pertenencia (por ejemplo, la carpeta HOJA creada dentro de
la carpeta FXC);
4. reiniciar el editor de Xilog
Plus.
En el grupo de macros creado podremos
introducir hasta 100 macros; se pueden crear hasta 40 grupos como m�ximo.
�ATENCI�N!
No
modificar el contenido de la carpeta �\FXC\PRIVATE!
La programaci�n de una macro sigue las mismas
reglas v�lidas para un programa param�trico normal, incluida la posibilidad de solicitar
subprogramas u otras macros; con todo, es necesario, respetar algunas
indicaciones que se describen a continuaci�n.
Encabezamiento
Los campos DX, DY y DZ
deben ser puestos a cero, mientras el campo /, que normalmente indica el
equipamiento,� debe asumir el siguiente
formato:
"<acelerador>,<par�metros>,<�ndice
descripci�n>,<descripci�n>"
� <acelerador> consiste en un par de
caracteres utilizados para la selecci�n veloz del ciclo fijo en la lista
general de instrucciones; el primer car�cter debe ser un n�mero comprendido
entre 5 y 9, mientras el segundo debe ser una de las letras del alfabeto.
� <par�metros> es la lista de
par�metros de la macro.
� <�ndice descripci�n> debe ser
puesto a cero.
� <descripci�n> es la l�nea que
describe la macro.
Ejemplos:
����������� H DX0 DY0 DZ0 *MM
/"9p,XYZDT,0,PUERTA TIPO 08"
Par�metros de la macro
Los par�metros
son datos que el usuario debe pasar a la macro para que pueda desarrollar la
funci�n para la que se ha creado.
Los par�metros
deben seleccionarse entre los indicados en la lista siguiente. Algunos de ellos
tienen un significado preciso que debe ser respetado, otros son libre,
eventualmente con un significado recomendado.
X
Libre (coordenada X)
Y
Libre (coordenada Y)
Z
Libre (coordenada Z)
A
�ngulo de rotaci�n
H
Libre (coordenada H)
E
Libre
(posici�n envoltura)
I
Libre
(coordenada I)
J
Libre
(coordenada J)
V
Velocidad de
avance
S
Velocidad de
rotaci�n del mandril
T
Lista de
herramientas
F
Cara de
trabajo
C
Correcci�n
herramienta
K
Incremental
P
Referencia panel
Q
Libre
(cuadrante)
R
Libre
(repeticiones)
x
Libre (cota
final X, step en X, ...)
y
Libre (cota
final Y, step en Y, ...)
a
Libre
B
Libre
(�ngulo, ...)
r
Libre
(radio, ...)
D
Libre
(di�metro, fuera trabajo, ...)
s
Libre (step,
...)
l
Libre (longitud,
...)
G
Libre
(sentido fresado circular, direcci�n herramienta m�ltiple, ...)
L
Libre
(longitud, ...)
N
Nombre del
subprograma
No existe un
orden concreto para indicar los par�metros. La ausencia del valor para un
par�metro al llamar la macro, asigna al par�metro el valor previsto por la
macro.
Uso de los
par�metros
En el Ciclo Fijo, los valores de los
par�metros pueden ser le�dos utilizando las variables reservadas pX, pY, pZ,
pA, pH, pE, pI, pJ, pV, pS, pT, pF, pC pK, pP, pQ, pR, px, py, pa, pB, pr, pD,
ps, pl, pG, pL, pN, denominadas variables p.
Las variables p (excepto pT) pueden ser
utilizadas tambi�n en las expresiones, siempre que su par�metro est� definido;
de lo contrario el resultado no es determinado. Para conocer el estado de una variable
p se puede utilizar el operador NDEF que da Verdadero (1) si la
variable no est� definida y Falso (0) si lo est�.
Ejemplos:
H DX0 DY0 DZ0 *MM /"9p,XYZDT,0,PUERTA
TIPO 08"
L BASE=100;base que debe utilizarse si el
valor del par�metro X no ha sido especificado
IF NDEF pX GOTO TESTpY
L BASE=pX;base pasada como valor del par�metro
X
.TESTpY
...
Variables
especiales
En las macros existen a
disposici�n algunas variables especiales, s�lo para lectura, que pueden ser
utilizadas tambi�n en las expresiones:
X
Coordenada X corriente
Y
Coordenada Y corriente
Z
Coordenada Z corriente
C
Correcci�n del radio corriente (la �ltima
aportada)
Cp
Correcci�n del radio programada
F
Cara corriente
Ejemplos:
����������� L
oldF = F
����������� L
curC = C
����������� L
QY = Y+32
����������� B
X=X Y=QY Z=Z
Instrucciones
especiales
Existen algunas instrucciones especiales:
PRINT �mensaje�
determina la visualizaci�n del mensaje
C=<variable>
asigna el tipo de correcci�n del radio
F=<variable>
asigna la cara
Ejemplos:
����������� F=oldF
����������� C=curC
����������� IF NOT NDEF pX GOTO Inicio
����������� PRINT �falta el
valor del par�metro X�
����������� GOTO
Fin
����������� .Inicio
����������������������� ...
����������� .Fin
Organizaci�n
herramientas y operador ^
La variable especial T� contiene las herramientas corrientes.
Mediante el operador ^ es posible:
1. anular las herramientas en T
2. agregar una herramienta a� T
3. copiar pT y T en variables normales, que adquieren significado
4. de variables herramientas;
5. copiar pT y las variables herramienta en T
6. leer el n�mero de herramientas en pT o en las variables herramienta
7. leer una a una las herramientas en pT o en las variables herramienta
Anulaci�n
herramientas corrientes
La anulaci�n de las herramientas corrientes se
obtiene sumando el valor cero a T.
Ejemplos:
����������� L
T = T+0
Agregado
de una herramienta corriente
El agregado de una herramienta corriente se
obtiene sumando el n�mero de la herramienta a T.
Ejemplos:
����������� L
T = T+6
����������� L
T = T+101
Copia
herramientas
La copia de las herramientas se obtiene
colocando -2 a continuaci�n del operador ^.
Ejemplos:
����������� L
CopiaDiT = T^-2���������������� ;copia las
herramientas corrientes
����������� L
CopiaDipT = pT^-2;copia pT
����������� L
T = T + 0
����������� L
T = CopiaDiT^-2���������������� ;asigna
una variable herramienta a T
�����������
����������� L T = T + 0
����������� L T = CopiaDipT^-2
�����������
����������� L T = T + 0
����������� L T = pT^-2��������������������������� ;asigna pT a T
Lectura
n�mero herramientas
La lectura del n�mero de las herramientas se
obtiene colocando -1 a continuaci�n del operador ^.
Ejemplos:
����������� L
NumUt = pT^-1
����������� L
NumT = CopiaDiT^-1
Lectura
de cada herramienta
La lectura de cada herramienta se obtiene
colocando la posici�n de la herramienta solicitada, a partir de 0, a continuaci�n
del operador ^.
Ejemplos:
����������� L
PrimeroUt = pT^0
����������� L
SegundoUt = CopiaDiT^1
����������� L
PosUt = 3
����������� L
Pr�ximoUt = pT^PosUt