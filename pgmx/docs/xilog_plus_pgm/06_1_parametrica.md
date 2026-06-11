
# 6.1 Programaci�n
param�trica
### 6.1.1 Introducci�n a la programaci�n
param�trica
La programaci�n param�trica permite introducir
par�metros (largo, ancho, espesor), cuyo valor puede cambiar seg�n las
necesidades. De este modo, un �nico programa permite gestionar piezas con el
mismo perfil y distintas dimensiones.
Las instrucciones de la programaci�n
param�trica se pueden utilizar en el editor de texto del mismo modo que las
dem�s instrucciones. En el editor gr�fico se pueden utilizar las instrucciones
PAR y D; su introducci�n se lleva a cabo con el Editor par�metros. En un
programa se pueden introducir en total hasta 512 variables (PAR, L, D).
Para visualizar c�modamente los par�metros PAR
de un programa y modificar los valores est� disponible, ya sea para el Editor
texto como para el Editor gr�fico, el Wizard par�metros.
Los par�metros introducidos en un programa se
pueden modificar f�cilmente antes de ejecutar el programa: las modificaciones
son v�lidas s�lo para dicha ejecuci�n. De este modo, el mismo programa puede
ser �personalizado� cada vez que se ejecuta.
► Como abrir
el Editor par�metros (s�lo en el editor gr�fico).
Hacer clic en
el men� HERRAMIENTAS/editor
par�metrOS�

� o en
el bot�n.

El Editor par�metros est� preparado para la
introducci�n de las instruccioens PAR (Lista par�metros) y D (Lista
definiciones). Para introducir un dato, haga clic dos veces en la casilla,
introduzca el dato y confirme con la tecla [ENVIAR].
► Como abrir
el Wizard par�metros.
Hacer clic en
el men� HERRAMIENTAS/wizard
par�metrOS�

� o en
el bot�n.

El Wizard par�metros muestra los par�metros
PAR agrupados en p�ginas seg�n la secci�n de pertenencia (v�ase: instrucci�n PARSECTION) y permite modificar el valor:
para modificar un valor, haga clic en el valor que va a modificar, introduzca
el nuevo valor y confirme con la tecla [ENVIAR].
El bot�n OK + GRAFICA
(habilitado en editor texto y en editor gr�fico) confirma los par�metros y
actualiza el editor debajo sin salir del ambiente.
En el modo editor gr�fico la gr�fica se
actualiza autom�ticamente, mientras en el modo editor texto se abre
autom�ticamente la ventana de visualizaci�n gr�fica.

### 6.1.2 Instrucciones
param�tricas
PAR�(declaraci�n par�metro)
Permite
atribuir un valor num�rico a una palabra (par�metro). El par�metro puede
sustituir el valor de cualquier coordenada, cota, velocidad, etc. En cada
programa se pueden introducir hasta 256 caracteres, todos ellos detr�s de la
instrucci�n de Encabezamiento.
Grupo:
instrucciones texto

Ejemplo:
El ejemplo muestra la programaci�n del
par�metro a 5000 mm/min.
La cuarta casilla del editor de texto
(�Descripci�n�) y los campos �Descripci�n� y �Comentario� del Editor par�metros
pueden utilizarse para documentar el par�metro.
Ahora, el par�metro puede sustituir a una
instrucci�n, por ejemplo, para indicar la velocidad de acercamiento en una
instrucci�n XG0:
En lugar de
podemos escribir
Nota: no se puede atribuir a un par�metro los nombres reservados a los
campos de instrucciones est�ndar, por ejemplo, un par�metro no se puede llamar
�X�, �Y�, o �Z�, pero se puede llamar �W� o �CUOTA�.
PARSECTION�(configuraci�n de una secci�n para los par�metros)
Agrupa en una
secci�n los par�metros PAR que la siguen.
Grupo:
instrucciones texto

Para crear una secci�n solo hay que asignar un
nombre.
En el editor de texto, la secci�n creada
incluye los par�metros introducidos sucesivamente, hasta la instrucci�n
PARSECTION siguiente.
En el editor gr�fico, la secci�n debe
asignarse directamente a cada uno de los par�metros en la casilla �Secci�n� del
Editor par�metros.
Ejemplo:
H DX=1200 DY=600 ...

PAR LMax.=750

Par�metros no pertenecientes a una secci�n.
PAR LStep=3

PARSECTION / �DIMENSIONES�

Par�metros de la secci�n �DIMENSIONES�.
PAR Larghezza=100

PAR Lunghezza=300

PARSECTION / �SECT2�

Par�metros de la secci�n �SECT2�.
PAR Par1=1

PAR Par2=2

En el Wizard par�metros las secciones aparecen
como p�ginas separadas; los par�metros no pertenecientes a alguna secci�n se
agrupan bajo la secci�n PAR.
PPAR�(configuraci�n de los par�metros para subprograma o o macro)
Agrupa
par�metros para pasar a subprogramas y macro.
Grupo:
instrucciones texto

La instrucci�n PPAR es �til en el caso de que
los par�metros para pasar a subprogramas o macro sean demasiado numerosos para
ser escritos en la l�nea de instrucci�n de llamada del subprograma/macro.
Ejemplo:
La llamada de subprograma
...
S /�MySubroutine�
X=1200 Y=350 Lmax.=740 Lstep=2 Type=2 Cycle=30
...
puede escribirse tambi�n en la forma
...
PPAR Lmax.=740 Lstep=2 Type=2
PPAR Cycle=30
S /�MySubroutine� X=1200 Y=350
...
Las instrucciones PPAR deben ser introducidas antes de la introducci�n de llamada a
la cual se refieren; si un par�metro introducido en una instrucci�n PPAR se
repite en la instrucci�n de llamada siguiente, prevalece el valor introducido
en la instrucci�n de llamada.
L�(atribuir un valor a variable)
Permite
atribuir un valor num�rico a una palabra (variable), utilizando tambi�n una
expresi�n. La variable puede sustituir el valor de cualquier coordenada, cuota,
velocidad, etc. En cada programa se pueden introducir hasta 512 variables, en
cualquier punto del programa. Las variables pueden redefinirse varias veces dentro
del programa.
Grupo:
instrucciones texto

Ejemplo:
El ejemplo muestra la programaci�n de la
variable RAGGIO (= �Radio�) a 100 mm, como resultado de la expresi�n
(300-200)/2. Las expresiones pueden utilizar no s�lo n�meros, sino tambi�n otras
variables establecidas precedentemente.
Por ejemplo:
DX/2
(VARIABLE1 � DY)*2
�
Ahora, la variable puede sustituir el n�mero
en una instrucci�n, por ejemplo, para indicar el arco del radio de una
instrucci�n XAR2:
En lugar de
podemos escribir

D�(declaraci�n de un alias)
El alias tiene
la misma funci�n de una variable L: permite atribuir un valor num�rico a una
palabra utilizando una expresi�n. A diferencia de una variable L, un alias
puede ser definido una sola vez dentro del programa. Los alias deben ser
definidos inmediatamente tras los par�metros PAR, y se pueden utilizar hasta 64
en cada programa.
Grupo:
instrucciones texto

Ejemplo:
Este ejemplo muestra la programaci�n del alias
ORY a 50*2. Ahora, el par�metro puede sustituir el n�mero de una instrucci�n,
como si fuera una variable L.