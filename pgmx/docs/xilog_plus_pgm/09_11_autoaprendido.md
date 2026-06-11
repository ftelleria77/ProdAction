
# 9.11 Autoap# rendido
La
exigencia de conocer con precisi�n la posici�n de los dispositivos del plano
motorizado (travesa�os y soportes) ha llevado a la introducci�n en Editor de
Xilog y en EPL de una nueva funci�n para la adquisici�n de tales cotas. Esta
nueva funci�n ha sido definida como �autoaprendido� de las cotas de los
elementos del plano.
En
ambos los ambientes EPL de Editor, es suficiente iniciar el panel m�quina y
cliquear sobre el� icono ��(posicionada arriba
a la derecha) para lanzar la funci�n de autoaprendido.
El
precedente icono se encuentra actualmente activado solamente si el en el
archivo de configuraci�n� Nci.cfg ha
sido programado al valor �1� la clave $GEN_APPPB.
En
Editor el clic del rat�n sobre el pulsador de autoaprendido genera la escritura
de un bloque de PB en el programa pieza (en la l�nea siguiente a aquella
seleccionada).
���������������������������������������
���������������������������������������� �������Antes del autoaprendido (Parsifal)
�����������������������������������������������������
Despu�s del
autoaprendido (Parsifal)
Las
instrucciones PB se introducen debajo de la l�nea del programa en la que se
encuentra el foco (es decir aquella evidenciada en azul) y forman un bloque de
SetUp.
Dado
que se encuentra en las �Notas�, el bloque de PB puede ser pegado nuevamente
para introducir la sesi�n de bloqueo de la pieza, necesaria si los dispositivos
son bornes; en este caso, despu�s debe ser programado el estado de los bornes y
el tipo E=2 (Bloqueo).
Es
tambi�n posible interpretar las posiciones le�das come intermedias entre dos
elaboraciones; en este caso despu�s debe ser programado el tipo E=3
(intercambio bornes) o E=4 (separaci�n pieza) y el posibles estado de los
bornes.
En EPL
el lanzamiento de la funci�n de autoaprendido genera un nuevo posicionamiento
gr�fico de los travesa�os y de los soportes a las nuevas cotas recibidas.
Ejemplo
de secuencia de adquisici�n cotas en EPL:
�������������������� Antes del autoaprendido, travesa�os y los
dispositivos en estacionamiento (EPL)
������������������ Despu�s del autoaprendido, travesa�os y dispositivos
a las cotas recibidas (EPL)
Actualmente
la implementaci�n de la funci�n de autoaprendido no
prev�, ni en EPL ni en EDITOR, ning�n tipo de control acerca de la correcci�n
de los valores recibidos.