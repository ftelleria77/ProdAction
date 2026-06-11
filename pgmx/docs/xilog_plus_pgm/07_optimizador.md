
# 7. Optimizador de programas
El optimizador de programas de Xilog Plus optimiza los
programas de trabajo para reducir al m�nimo las operaciones del cambio de
herramienta.
►Tras haber abierto el programa que se va a optimizar, el optimizador
puede activarse haciendo clic en el men� INSTRUMENTOS /OPTIMIZADOR programAS. Aparecer� la ventana de memorizaci�n del fichero para seleccionar un
programa existente o un nuevo programa que ser� el programa resultante de la
optimizaci�n del programa corriente. Si hacemos clic en el bot�n Ok se abrir� la siguiente ventana que permite seleccionar dos tipos de
optimizaci�n: secuencial y cambio herramientas (v�ase tambi�n: Ap�ndice
F � M�quinas Ergon).
► El resultado es un nuevo programa optimado (precedentemente
establecido) que se puede guardar en memoria como un programa normal. El
programa original no se modifica.
La optimizaci�n de programas responde a dos
exigencias:
1) Trabajos que requieren una secuencia
precisa de utilizaci�n de las herramientas. Por
ejemplo: madera maciza, hojas, carpinter�a. En este caso:
� el programa debe estar compuesto s�lo por
instrucciones SO (Llamada optimizada de subprograma), que sirven para solicitar
los programas como subprogramas;
� es necesario seleccionar con el rat�n la
casilla Cambio
HERRAMIENTAS.
La optimizaci�n del cambio de herramienta
tiene dos efectos:
� optimiza las operaciones de cambio de
herramienta;
� optimiza los recorridos (la m�quina
realiza los trabajos previstos para cada herramienta ejecutando en secuencia
las m�s cercanas)
Ejemplo:
El programa TEST_1 efect�a el perfilado del
tablero en dos fases: desbaste mediante la herramienta E1 y acabado mediante la
herramienta E2.
H DX=400 DY=300
DZ=20 -A C=0 T=0 R=1 *MM /"def"
;Desbaste
C =2
GIN G=2
G0 X=DX/2 Y=0
N="PROF" T=101
G1 X=DX
G1 Y=DY
G1 X=0
G1 Y=0
G1 X=DX/2
GOUT
;Acabado
GREP N="PROF" T=102
Crear el programa MAIN_1, para solicitar dos
veces el programa TEST_1 para perfilar dos tableros distintos.
H DX=1100 DY=500
DZ=20 -A C=0 T=0 R=1 *MM /"def"
SO
/"test_1" BX=100 BY=100
SO
/"test_1" BX=600 BY=100
Ejecutado sin optimizaci�n, el programa MAIN_1
trabaja el tablero de la izquierda primero con la herramienta E1 y, a
continuaci�n, con la herramienta E2; sucesivamente trabaja el tablero de la
derecha primero con la herramienta E1 y, a continuaci�n, con la herramienta E2.
En total se requieren 4 cambios de herramienta (3 si al partir E1 ya est� en el
mandril).
El programa optimizado ejecuta la secuencia:
1. Desbaste del tablero de la izquierda con la herramienta E1
2. Desbaste del tablero de la derecha con la herramienta E1
3. Acabado del tablero de la derecha con la herramienta E2
4. Acabado del tablero de la izquierda con la herramienta E2
precisando 2 cambios de herramienta (1 si al
partir E1 ya est� en el mandril); adem�s, gracias al optimizador del recorrido,
el primer trabajo de acabado (punto 3) se realiza sobre el tablero m�s cercano,
es decir, el de la derecha.
2) Trabajos que permiten alterar la
secuencia de utilizaci�n de las herramientas. Por
ejemplo: trabajos c�clicos repetidos (decoraci�n), nesting. En este caso:
� el programa no debe estar compuesto por
instrucciones SO; debe contener instrucciones XS, macros, etc.
� hay que seleccionar la casilla Secuencial; se recomiena seleccionar tambi�n la casilla Cambio herramientaS.
La optimizaci�n secuencial ordena la secuencia
de trabajo optimizando las operaciones de cambio de herramienta. Si adem�s se
habilita la casilla de Cambio herramientaS, se optimizan
tambi�n los recorridos.
Ejemplo:
El programa TEST_2 efect�a el perfilado de
cuatro tableros en dos fases: desbaste mediante la herramienta E1 y acabado
mediante la herramienta E2.
H DX=2000 DY=400
DZ=20 -AB C=0 T=0 R=1 *MM /"def"
PAR Num =4
PAR OffsetY =0
" "
L MyDX =400
L MyDY =300
L Cnt� =0
DO
�� O X=50+500*Cnt Y=50+OffsetY
� ;Desbaste
�� C =2
�� GIN G=2#
�� G0 X=MyDX/2 Y=0
N="PROF" T=101
�� G1
X=MyDX
�� G1
Y=MyDY
�� G1
X=0
�� G1
Y=0
�� G1
X=MyDX/2
�� GOUT
�
;Acabado
�� GREP
N="PROF" T=102
� ;
�� L
Cnt =Cnt+1
�� IF
Cnt=Num EXIT
OD
Ejecutado sin optimizaci�n, el programa TEST_2
trabaja los tableros de izquierda a derecha utilizando para cada herramienta
primero la herramienta E1 y despu�s con la herramienta E2; en total se
requieren 8 cambios herramientas (7 si al partir E1 ya est� en el mandril).
El programa con optimizaci�n secuencial
ejecuta la secuencia de trabajo:
1. Desbaste de todos los tableros de izquierda a derecha con la
herramienta E1
2. Acabado de todos los tableros de izquierda a derecha con la herramienta
E2
precisando en total 2 cambios herramienta (1
si al partir E1 ya est� en le mandril).
Si tambi�n est� prevista la optimizaci�n del
cambio de herramienta, el acabado de los tableros inicua desde la derecha, no
desde la izquierda.