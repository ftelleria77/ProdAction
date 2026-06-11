
# 6.2 Programaci�n
estructurada
### 6.2.1 Salto
incondicionado
GOTO�(salto
incondicionado)
Grupo:
instrucciones texto

. (definici�n de etiqueta)�����������
Grupo:
instrucciones texto

El salto
incondicionado permite saltar algunas instrucciones, pasando directamente de
una parte a otra del programa. La instrucci�n GOTO indica el punto al que debe
saltar el programa, definido por una etiqueta. En un programa pueden insertarse
varios saltos.
Ejemplo:
H ���
����
GOTO QUI;
salto a la etiqueta QUI
����
����
. QUI; etiqueta
QUI
����
Las dos instrucciones deben estar siempre
combinadas.
La instrucci�n GOTO indica que el programa
debe saltar a la etiqueta QUI (introducida en el segundo campo). La instrucci�n
se inserta en la l�nea precedente al inicio del salto: posicionarse en la l�nea
y pulsar la tecla [INS].
La instrucci�n para definir la etiqueta define
la etiqueta QUI (a insertar en la l�nea en la que debe volver a iniciar la
ejecuci�n del programa).
### 6.2.2 Salto
condicionado
IF�(salto
condicionado)
Grupo:
instrucciones texto

. (definici�n de
etiqueta)
Grupo:
instrucciones texto

El salto
condicionado permite saltar algunas instrucciones, pasando directamente de una
parte a otra del programa, cuando se cumple una condici�n. Las instrucciones de
control de la condici�n verifican expresiones compuestas, tambi�n
contempor�neamente, de valores constantes, par�metros, variables y alias. En un
programa se pueden insertar varios saltos.
Ejemplo:
H ���
PAR PROVA=1; programaci�n
del par�metro PROVA=1
����
����
IF������ PROVA=1� GOTO QUI; salto a la etiqueta
QUI, si PROVA=1
����
����
. QUI; etiqueta
QUI
����
Las dos instrucciones deben estar siempre
combinadas.
La instrucci�n IF GOTO indica que el programa
debe saltar a la etiqueta QUI (del campo GOTO) cuando el par�metro PROVA (del
segundo campo; el par�metro PROVA ha sido declarado tras el encabezamiento del
programa) vale 1. La instrucci�n debe insertarse en la l�nea precedente al
inicio del salto: posicionarse en la l�nea y pulsar la tecla [INS].
La etiqueta se define como el salto
incondicionado. Si el par�metro PROVA es distinto de 1, el programa no salta a
la etiqueta QUI.
### 6.2.3 Realizaci�n y
ejecuci�n de un bloque
IF THEN�(ejecuci�n
condicionada)
FI�(fin ejecuci�n
condicionada)
ELSE�(alternativa de la ejecuci�n condicionada)
La instrucci�n
IF THEN permite verificar una condici�n. La instrucci�n ELSE permite dividir el
bloque en dos partes alternativas. En un programa pueden insertarse varias
condiciones y es posible encastrar hasta 16 bloques uno dentro de otro.
Grupo:
instrucciones texto

Para insertar la instrucci�n IF THEN, hay que
escribir IF THEN en el campo de texto y pulsar la tecla [Env�o]. Se visualiza la ventana siguiente, en la que la palabra THEN aparece
delante del segundo campo, donde se introduce la condici�n para la ejecuci�n
(por ejemplo, que el par�metro DX sea menor que 2000).
Las instrucciones FI y ELSE no necesitan
par�metros.
1) Ejemplo con condici�n verdadera (sin
instrucci�n ELSE).
H�
DX=1900 �.; programaci�n del par�metro DX=1900 en el Encabezamiento
���..��������������������������������������������
���..
IF������� DX<2000 THEN;
inicio del bloque. Si el par�metro DX es menor que 2000
(como en el ejemplo
de Encabezamiento), se ejecuta el bloque de instrucciones que inicia en este
punto y termina con la instrucci�n FI
����
����
FI; fin del bloque
condicionado
����
2) Ejemplo con condici�n falsa (sin
instrucci�n ELSE).
H�
DX=2100 �.; programaci�n del par�metro DX=2100 en el Encabezamiento
����������������������������������������������
����
IF DX<2000 THEN;
inicio del bloque. Si el par�metro DX es igual o superior a 2000 (como en el
ejemplo de Encabezamiento), el bloque de instrucciones que inicia en este punto
y finaliza con la instrucci�n FI no se ejecuta. El flujo del programa se
interrumpe y vuelve a iniciarse en la instrucci�n siguiente a la instrucci�n FI
de fin de bloque
����
����
FI; fin del bloque
condicionado
����
3) Ejemplo con condici�n verdadera e
instrucci�n ELSE
H� DX=1900 �.; programaci�n del par�metro
DX=1900 en el Encabezamiento
���...�������������������������������
����
IF DX<2000 THEN; inicio del bloque. Si el par�metro DX es
inferior a 2000 (como en el ejemplo de Encabezamiento), se ejecuta s�lo la
primera parte del bloque, de la instrucci�n IF THEN a la instrucci�n ELSE
����
����
ELSE; la segunda parte del bloque, que inicia por la instrucci�n ELSE y
termina por la instrucci�n FI, no se ejecuta. El flujo del programa se
interrumpe y vuelve a iniciar en la instrucci�n sucesiva a la instrucci�n FI de
fin de bloque
����
����
FI; fin del bloque
condicionado
����
4) Ejemplo con condici�n falsa e
instrucci�n ELSE.
H� DX=2100 �.; programaci�n del par�metro
DX=2100 en el Encabezamiento
����������������������������������������������
����
IF DX<2000 THEN; inicio del bloque. Si el par�metro DX es igual
o superior a 2000 (como en el ejemplo de Encabezamiento), el bloque de
instrucciones que inicia en este punto y finaliza con la instrucci�n ELSE no se
ejecuta. El flujo del programa se interrumpe y vuelve a iniciar en la
instrucci�n sucesiva a la instrucci�n ELSE
����
����
ELSE; la segunda parte del bloque, que inicia por la instrucci�n ELSE y
finaliza con la instrucci�n FI, se ejecuta
����
����
FI; fin del bloque
condicionado
����
5) Ejemplo con varias condiciones e
instrucci�n ELSE: primera condici�n verdadera, segunda condici�n falsa.
H�
DX=1400 �.; programaci�n del par�metro DX=1400 en el Encabezamiento
����..����������������������������������������������������
����.
IF DX<2000 THEN; inicio del primer bloque. Si el par�metro DX
es inferior a 2000 (como en el ejemplo de Encabezamiento), se ejecuta el primer
bloque, que inicia en el primer IF THEN y finaliza en el segundo IF THEN
����.�����������������������������������������
����.�����������������
�����������������������
IF DX>1500� THEN; inicio
del segundo bloque. Si el par�metro DX es igual o inferior a 1500 (como en el
ejemplo de Encabezamiento), el flujo del programa se interrumpe y vuelve a
iniciar en la instrucci�n sucesiva a la instrucci�n ELSE
�������������������������������
��������
�����������������������
ELSE; la segunda parte del segundo bloque, que inicia en la instrucci�n
ELSE y finaliza en la instrucci�n FI, se ejecuta
�����
�����
FI; fin del
segundo bloque condicionado
�����
�����
FI; fin del primer
bloque condicionado
�����
6) Ejemplo con varias condiciones e
instrucci�n ELSE: la primera y la segunda condici�n verdaderas.
H� DX=1800 �.; programaci�n del par�metro
DX=1800 en el Encabezamiento
����.�����������������������������������������
����.
IF DX<2000 THEN; inicio del primer bloque. Si el par�metro DX
es inferior a 2000 (como en el ejemplo de Encabezamiento), se ejecuta el primer
bloque, que inicia en el primer IF THEN y finaliza en el segundo IF THEN
����.�����������������������������������������
����.�����������������
�����������������������
IF DX>1500� THEN; inicio
del segundo bloque. Si el par�metro DX es superior a 1500 (como en el ejemplo
de Encabezamiento), se ejecuta la primera parte del segundo bloque, que inicia
en el segundo IF THEN y termina en ELSE
�������������������������������
��������
�����������������������
ELSE; la segunda parte del segundo bloque, que inicia en la instrucci�n
ELSE y finaliza en la instrucci�n FI, no se ejecuta. El flujo del programa se
interrumpe y vuelve a iniciar en la instrucci�n trasero a la siguiente
instrucci�n FI de fin de bloque
�����
�����
FI; fin del
segundo bloque condicionado
�����
�����
FI; fin del primer
bloque condicionado
�����
7) Ejemplo con varias condiciones e
instrucci�n ELSE: la primera condici�n falsa.
H� DX=2100 �.; programaci�n del par�metro
DX=2100 en el Encabezamiento
����.�����������������������������������������
����.
IF DX<2000 THEN; inicio del primer bloque. Si el par�metro DX
es superior a 2000 (como en el ejemplo de Encabezamiento), el primer bloque no
se ejecuta. El flujo del programa se interrumpe y vuelve a iniciar en la
instrucci�n sucesiva a la instrucci�n FI de fin de bloque (al final del
ejemplo)
����.�����������������������������������������
����.�����������������
�����������������������
IF DX>1500� THEN; inicio
del segundo bloque. Como el segundo bloque est� dentro del primero, es saltado
�������������������������������
��������
�����������������������
ELSE; la segunda parte del primer bloque tambi�n es saltado
�����
�����
FI; fin del
segundo bloque condicionado
�����
�����
FI; fin del primer bloque condicionado. El programa vuelve a comenzar a
partir de aqu�.
�����

### 6.2.4 Realizaci�n y ejecuci�n de un ciclo
DO�(inicio ciclo)
OD�(fin
ciclo)
Grupo:
instrucciones texto

EXIT�(salida de un ciclo)
Grupo:
instrucciones texto

IF EXIT�(salida condicionada desde un ciclo)
Grupo:
instrucciones texto

Un ciclo es una
serie de instrucciones comprendidas entre el comando DO (inicio ciclo) y el
comando OD (fin ciclo), que el centro de trabajo repite hasta que encuentra el
comando EXIT (salida incondicionada del ciclo) o el comando IF EXIT (salida
condicionada del ciclo). Sin la instrucci�n EXIT o IF EXIT, el ciclo se repite
de modo infinito. Un programa puede incluir varios ciclos.
El ciclo inicia con una instrucci�n DO y se le
puede asignar un nombre en el campo N, no es obligatorio.
Tras introducir todas las instrucciones que
componen el ciclo, hay que insertar la instrucci�n OD de fin de ciclo.
Para salir de un ciclo, hay que insertar una
instrucci�n EXIT o IF EXIT antes de la instrucci�n OD de fin de ciclo.
�El
comando IF EXIT (se activa escribiendo IF EXIT en el campo de texto) sale del
ciclo PROVA si se cumple la condici�n PROF=-20.
Si el nombre del ciclo no se especifica, las
instrucciones EXIT e IF EXIT salen del ciclo m�s interno.
1) Ejemplo de un ciclo con salida
incondicionada.
H ...�� ������������������� �
���..��������� ����������������������������������������������
DO����� N=PROVA; inicio del ciclo PROVA
����
���....
EXIT�� N= PROVA; salida del ciclo PROVA
OD; fin del ciclo PROVA
�����
En este ejemplo el ciclo PROVA se repite una
sola vez.
2) Ejemplo de un ciclo con salida
condicionada.
H ...�...���������������������
���..��������������������
L��
PROF=-1; variable para la profundidad de salida condicionada
���..
���..
DO����� N= PROVA; inicio del ciclo PROVA
���...
XG0��
X=� Y=� Z=PROF
����
����
L PROF=-1+PROF; a�ade a la variable PROF el
valor -1 con cada paso
IF��
PROF=-20�� EXIT ��N= PROVA; condici�n para salir del ciclo
PROVA
OD����� ; fin
del ciclo PROVA
����
En este ejemplo el ciclo PROVA se repite 19
veces porque la condici�n para salir del ciclo impone que la variable PROF
alcance la cota de �20 mm y el decremento es de 1 mm con cada lectura de ciclo.
La variable PROF programada antes del DO vale -1 y la instrucci�n L� PROF=-1+PROF antes del comando IF EXIT
quiere decir �a�adir a la variable PROF el valor �1 cada vez que se lee esta
l�nea�. Al salir del ciclo, el flujo del programa vuelve a iniciar en la l�nea
sucesiva al comando OD.
3) Ejemplo de
un ciclo dentro de otro
H ...��� ��������������� �
����..����� ����������������������������������������������
DO����� N=1; inicio del ciclo 1
�����
�����
DO N=2; inicio del
ciclo 2
�����
�����
EXIT N=2����� ;
salida del ciclo 2
OD; fin del ciclo
2
�����
�����
EXIT N=1; salida
del ciclo 1
OD����� ; fin del ciclo 1
�����

### 6.2.5 Repetici�n de un
ciclo
REPEAT�(repetici�n de un ciclo)
Grupo:
instrucciones texto

IF REPEAT�(repetici�n
condicionada de un ciclo)
Grupo:
instrucciones texto

La instrucci�n
REPEAT permite regresar del punto en se introduce a la instrucci�n DO de inicio
ciclo. La instrucci�n IF REPEAT permite regresar del punto en que se introduce
a la instrucci�n DO de inicio de ciclo, si se cumple la condici�n introducida.
Ambas instrucciones permiten repetir una parte del ciclo o el ciclo completo.
Ejemplos:
La instrucci�n REPEAT habilita la repetici�n
del ciclo PRUEBA (cuyo nombre se introduce en el campo N).
La instrucci�n IF REPEAT (que se activa
escribiendo IF REPEAT en el campo de texto) habilita la repetici�n del ciclo
PROVA si la condici�n ALT (introducida en el segundo campo) es inferior a 100.
Ejemplo:
H���
L CX=0
L CY=0
����
����
DO N= PROVA1; inicio
ciclo PROVA1
IF CY=3*50 EXIT N= PROVA1; salir del ciclo
PROVA1 si la variable CY es igual a 3*50
� ��������� DO N= PROVA2; inicio ciclo PROVA 2
����� ����
�����
����
L CY=CY+50; cada
paso la variable CY aumenta 50
� ��������� REPEAT N= PROVA1; repetir el
ciclo PROVA1
� ��������� �������
�� OD; fin del ciclo PROVA2
OD; fin del ciclo PROVA1
En este ejemplo, cuando se lee el mando REPEAT
N= PROVA1 el flujo vuelve a empezar en la instrucci�n DO N= PROVA1 (inicio del
ciclo PROVA1) y se repite hasta que se cumple la condici�n de la l�nea IF
CY=3*50 EXIT N= PROVA1, es decir, �salir del ciclo PROVA1 cuando la variable CY
es igual a 150�. Cada paso la variable CY aumenta 50.