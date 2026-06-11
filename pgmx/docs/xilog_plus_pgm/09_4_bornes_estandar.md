
# 9.4 Ejemplo de trabajo con bornes est�ndares # ��
En el
siguiente ejemplo se muestra a continuaci�n la programaci�n de un plano
autom�tico con dispositivos de tipo bornes.��

### Ejemplo 1: Bloqueo autom�tico
El
campo V del encabezamiento (header) del programa contiene el valor 21.
1. Fase preparaci�n plano
Figura
1: PB para barra 1
Figura
2: PB para barra 2
La primera fase de programaci�n de un plano motorizado es la preparaci�n
plano. La preparaci�n de un plano motorizado �est� constituida por UN SOLO
bloque de PB. Un bloque de PB est� constituido por un conjunto de PB, cada una
de las cuales representa una barra individual. La �ltima PB del bloque contiene
el valor E = 1. La Figura 1 muestra la programaci�n de la PB para la barra n�mero 1: en el campo X
se introduce la cota a la que se quiere llevar la barra, mientras en los campos
Y1, Y2 y Y3 las cotas respectivamente del borne 1, 2, y 3. Al lado de las cotas
de los bornes se muestra el estado de los mismos bornes.
Durante la fase de preparaci�n plano se introduce generalmente
el valor 1: borne abierto. La Figura 2 muestra la programaci�n de la PB para la barra n�mero 2.
La fase de preparaci�n del plano es obligatoria. El sistema restituye
el error si el operador omite la programaci�n.
Al finalizar la fase de preparaci�n del plano las barras no programadas
son llevadas a una posici�n de fuera de dimensi�n. Las nuevas cotas, nombradas cotas
de estacionamiento, son calculadas autom�ticamente por el sistema y
dependen del �rea de ejecuci�n. Para mayor informaci�n remitirse al p�rrafo Reglas
de estacionamiento.
�����������
2. Fase bloqueo pieza
Figura
3: PB para barra 1
Figura
4: PB para barra 2
La segunda fase de programaci�n de un plano motorizado es la fase di bloqueo
pieza. La fase di bloqueo pieza est� constituida por UN SOLO
bloque de PB. La �ltima PB del bloque contiene el valor E = 2. La Figura 3 muestra la
programaci�n de la PB para la barra n�mero 1: al lado de la cotas de los bornes
se muestra el valor del nuevo estado de los mismos bornes. El borne 1 y el
borne 2 se cierran (=0) mientras el borne 3 se cierra pero con la pieza en toma
(=2). La Figura 4 muestra la programaci�n de la PB para la barra n�mero 2.
La fase de bloqueo pieza es obligatoria. El sistema restituye error si
el operador omite la programaci�n.
2.a Bloqueo de PB con E = 3 contigua a E = 2
Existe una segunda fase de bloqueo, no obligatoria,
caracterizada por un bloque de PB con campo E = 3.
Esta fase permite un nuevo posicionamiento y un sucesivo bloqueo de los
bornes.
Figura
5: posicionamiento
en fase de bloqueo de la barra 1
Figura
6: posicionamiento
en fase de bloqueo de la barra 2
La Figura 5 muestra el posicionamiento del borne 2 de la barra 1 a la cota de 500.
La Figura 6 muestra el posicionamiento del borne 2 de la barra 2 a la cota de 500.
El bloque de PB termina con el valor del campo E = 3. Como se puede observar
los bornes 2 y 3 est�n cerrados y con la pieza en toma (=2).
3. Fase de posicionamiento intermedio
La fase de posicionamiento intermedio se realiza despu�s de una
elaboraci�n y le sigue una nueva elaboraci�n. En esta fase se pueden mover las
barras o los bornes a otra cota.� Cabe
se�alar que es posible realizar nuevos posicionamientos solamente cuando los
bornes se encuentran en el estado de abierto�
(=1) o de cerrado (=0); en caso contrario el sistema restituye el error.
Figura
7: apertura borne
Y3 de la barra 1
Figura
8: apertura borne
Y3 de la barra 2
Figura
9: posicionamiento
intermedio borne Y3 de la barra 1
Figura
10: posicionamiento
intermedio borne Y3 de la barra 2
La fase de posicionamiento intermedio est� constituida por UNO
O M�S bloques de PB. La �ltima PB del bloque contiene el valor E = 3. La Figura 7 muestra la
programaci�n de la PB para la barra n�mero 1: en este ejemplo el borne Y3 se
abre. La Figura 8 muestra la programaci�n de la PB para la barra n�mero 2: en este
ejemplo el borne Y3 se abre.
La Figura 9 y 10 �muestran la nueva cota del borne Y3 y el estado sucesivo (=0).
El ejemplo demuestra como un nuevo posicionamiento est� caracterizado
por dos bloques contiguos de PB: un primer bloque en el que se desbloquean los
bornes de inter�s para el movimiento y un segundo bloque en el que realmente se
posicionan.
Bloques de PB de posicionamiento intermedio no son obligatorios y
pueden ser repetidos m�s de una vez durante la elaboraci�n.�
4. Fase de desplazamiento con la pieza bloqueada
La fase de desplazamiento con la pieza bloqueada puede ser repetida m�s
veces en el interior del mismo PGM. En esta fase se pueden mover las barras o
los bornes a otra cota. Los desplazamientos pueden ser realizados solamente si
los bornes se encuentran en el estado de cerrado y con la pieza en toma (=2); en
caso contrario el sistema restituye el error.
Figura
11: desplazamiento
con la pieza bloqueada del borne 2 barra 1
�����
figura 12:
desplazamiento con la pieza bloqueada del borne 2 barra 2
La fase de desplazamiento con la pieza bloqueada est� constituida por
UNO O M�S bloques de PB. En el ejemplo de las figuras 11 y 12 se desplazan
contempor�neamente los bornes 2 de ambas las barras programadas desde la cota
de 500 mm a� una cota de 800 mm. Este
desplazamiento puede ser realizado porque el estado de los bornes es cerrado y
con pieza en toma (estado E = 2)
Suponiendo que la pieza sea �nica y se parezca a un paralelep�pedo,
XilogPlus vincula los movimientos de piezas bloqueadas a l�mites que podr�an
resultan incompatibles con las exigencias de programaci�n.
Estos l�mites pueden ser superados mediante el uso de la instrucci�n
SET DONTCARE=1, que, introducida antes del desplazamiento con la pieza
bloqueada que viola los l�mites de XilogPlus, anula todos los controles
est�ndares de incongruencia[6]; en estas condiciones el programador debe garantizar que los
desplazamientos "libres" non generen colisiones.
La validez de la SET DONTCARE=1 se anula inmediatamente tras haber
realizado el desplazamiento asociado; por tanto, si es necesario, la
instrucci�n debe ser repetida antes de cada desplazamiento.
Las instrucciones SET DONTCARE=1 tienen efecto solamente sobre las
sesiones de desplazamiento con la pieza bloqueada (grupo de PB con E=4).

Ejemplo:
aproximaci�n de dos piezas bloqueadas,
respectivamente, de las filas 1 y 2 de bornes.
; la fila 1 est� a cota Y=200, la fila 2 a cota Y=1000
;
PB B=1 Y1=400 Y2=800
PB B=2 Y1=400 Y2=800
PB B=3 Y1=400 Y2=800 E=4
XilogPlus sanciona este fragmento de programa porque lo interpreta como
un intento de restringir la dimensi�n Y de la (�nica) pieza.
; la fila 1 est� a cota Y=200, la fila 2 a cota Y=1000
;
SET DONTCARE = 1
PB B=1 Y1=400 Y2=800
PB B=2 Y1=400 Y2=800
PB B=3 Y1=400 Y2=800 E=4
En este caso, en cambio, XilogPlus no detecta errores porque el
desplazamiento se declara "libre" de la presencia de la
instrucci�n� SET DONTCARE=1.
5. Fase de desbloqueo pieza mascarada
La fase de desbloqueo pieza mascarada �se realiza al finalizar el programa PGM. En esta fase se pueden
abrir los bornes con la pieza en toma y eventualmente mover barras o bornes a
otra cota.
Figura
13: desbloqueo
borne 2 barra 1
�
Figura
14: desbloqueo
borne 2 barra 2
La Figura 13 muestra la programaci�n de la PB para la barra n�mero 1: en este
ejemplo el borne Y2 se abre porque es el �nico cerrado y con la pieza en toma.
La Figura 14 muestra la programaci�n de la PB para la barra n�mero 2: en este
ejemplo el borne Y2 se abre porque es el �nico cerrado y con la pieza en toma.
Figura
15: PGM
La Figura 15 muestra la programaci�n de un simple programa pieza. La primera
instrucci�n describe el panel y define el tipo de bloqueo (campo V).
Las instrucciones sucesivas representan los diferentes bloques de PB
previamente analizados:
- fase de preparaci�n plano (bloque de instrucciones 2 - 3)
- fase de bloqueo pieza (bloque de instrucciones 5 - 6 , 8 -
9 )
Al finalizar la fase de set up del plano se realiza una simple
elaboraci�n (bloque de instrucciones de 11 - 12).
- fase de posicionamiento intermedio (bloque de instrucciones
14 - 18)
Al finalizar la fase de posicionamiento intermedio del plano se
realiza una simple elaboraci�n (bloque de instrucciones de 20 - 21).
- fase de desbloqueo pieza mascarada (bloque de instrucciones
23 - 24)
### Ejemplo 1: Elaboraci�n marco ventana
En el ejemplo a continuaci�n se muestra la
elaboraci�n de un marco para ventana. Como en el caso anterior configurar el
valor del campo V = 21.
Figura
16
El
primer bloque con campo E = 1 define la fase de setup plano en el que se
posicionan las barras y los bornes (v�ase figura siguiente). En particular los
bornes Y1 de las barras B = 1 y B = 3 son llevados a una cota Y = 0; estos
dispositivos ser�n utilizados en otro momento.
El
segundo bloque de PB con campo E = 2 define la fase de bloqueo pieza en
la que vuelven a ser posicionadas las barras B = 1 y B = 3 (v�ase figura
siguiente) y modificados los estados de los bornes de inter�s al trabajo. En
particular los bornes Y1, Y2 de las barras B = 1 y B = 3 y Y1, Y3 de la barra B
= 2 se cierran con la pieza en toma.
Despu�s
de haber trabajado el exterior de la ventana (l�neas 10 � 14) es necesario
realizar algunos trabajos en el interior del marco de la misma. En todo caso,
es indispensable volver a posicionar algunos bornes; en particular el ejemplo
de la Figura 16 muestra en el tercero bloque de PB con campo E = 3 una
variaci�n en el estado del borne Y1 de la barra B = 2 , as� como un nuevo
posicionamiento de los bornes Y1 de las barras B = 1 y B = 3 (v�ase figura
siguiente). El estado del borne Y1 de barra B = 2 es llevado en el estado� = 0 para permitir el sucesivo desplazamiento
del mismo: de hecho cabe se�alar que no se pueden mover los dispositivos que
han sido programados cerradors y con pieza en toma.
El
�ltimo bloque de PB (l�nea 20 - 22) identifica el desplazamiento del borne Y1
de barra B = 2; este bloque permite realizar la elaboraci�n en el interior del
marco (v�ase figura siguiente).
Ejemplo 2: Bloqueo semiautom�tico
El campo V del encabezamiento (header) del programa contiene el valor
22.
El bloqueo semiautom�tico se diferencia del bloqueo autom�tico
solamente por la fase de bloqueo pieza. Al finalizar la fase de preparaci�n
del plano el operador debe cerrar los bornes en modalidad manual
mediante los selectores correspondientes ubicados en la m�quina. La
programaci�n de los bloques individuales de PB queda inalterada respecto al
caso precedente. La fase de preparaci�n plano es obligatoria. El sistema
restituye el error si el operador omite la programaci�n.
La fase de bloqueo pieza es obligatoria. El sistema restituye el error
si el operador omite la programaci�n.
Bloques de PB de posicionamiento intermedio no son obligatorios y
pueden ser repetidos m�s de una vez durante el trabajo.