
# 5.1
Encabezamiento
H�(Encabezamiento, o Header)
El
encabezamiento describe el tablero. Es la primera instrucci�n (obligatoria) de
un programa.
Par�metros b�sicos:
DX
Dimensi�n en X del tablero (longitud).
DY
Dimensi�n en Y del tablero (ancho).
DZ
Dimensi�n en Z del tablero (espesor).
/
Nombre
del archivo con los datos de equipamiento.
-
�rea de
trabajo en la que debe ejecutarse el programa. Valores admitidos: A, B, C, D,
AB, BA, CD, DC, AD, DA.
NOTA. Si se
introducen los valores 0, 0 ,0 en los campos de los par�metros DX ,DY ,DZ
respectivamente, el programa se reconoce autom�ticamente como macro.
Par�metros completos:
*
Unidad de medida. Los valores admitidos son
MM (mil�metros) e IN (pulgadas); si el campo se omite, vale la unidad
programada en los par�metros de la m�quina.
#
Nombre del archivo con las variables
ambiente.
C
Tipo de elaboraci�n; los valores admitidos
son 0 para la elaboraci�n normal y 1 para la elaboraci�n continua.
V
Habilita / inhabilita el bloqueo de la pieza
y el control de la posici�n de las ventosas autom�ticas (si hay) seg�n las
tabla:
Campo V
Bloqueo
Control
Dispositivos� en autom�tico
Bloqueo dispositivos
motorizados
Vac�o
S�, utilizando el sistema configurado con
xilog3.cfg; si est�n previstos vacu�metros y presostatos, se habilitan los
primeros
S�
Autom�tico
0
Mec�nico
No
No utilizado
1
Mec�nico
S�
No utilizado
10
S�, utilizando los vacu�metros
No
Manual
20
S�, utilizando los presostatos
No
Manual
11
S�, utilizando vacu�metros
S�
Autom�tico
21
S�, utilizando los presostatos
S�
Autom�tico
12
S�, utilizando los vacu�metros
S�
Semiautom�tico
22
S�, utilizando los presostatos
S�
Semiautom�tico
30
S�, utilizando presostatos y vacu�metros
No
Manual
31
S�, utilizando presostatos y vacu�metros
S�
Autom�tico
40
Equipamiento
(dispositivos de bloqueo mec�nico epeciales)
No
Manual
50
Default
Depende
del sistema configurado con�
Xilog3.cfg como default

51
DUOMATIC anteriores
No
Semiautom�tico
52
DUOMATIC posteriores
No
Semiautom�tico
53
DUOMATIC ant. + post.
No
Semiautom�tico
60
Bornes Horizontales (para Marcos)
No
Manual
61
Bornes Horizontales (para Marcos)
Si
Autom�tico
62
Bornes Horizontales (para Marcos)
Si
Semiautom�tico
100 � 153
(para Ergon)
Como en los casos 0 � 53 con combinaci�n 1
de las sub-�reas de vac�o
Como en los casos 0 � 53
Sub-�rea: 1
Como en los casos 0 � 53
Sub-�rea: 1
200 � 253
(para Ergon)
Como en los casos 0 � 53 con combinaci�n 2
de las sub-�reas de vac�o
Como en los casos 0 � 53
Sub-�rea: 2
Como en los casos 0 � 53
Sub-�rea: 2
300 � 353
(para Ergon)
Como en los casos 0 � 53 con combinaci�n 3
de las sub-�reas de vac�o
Como en los casos 0 � 53
Sub-�rea: 3
Como en los casos 0 � 53
Sub-�rea: 3
400 � 453
(para Ergon)
Como en los casos 0 � 53 con combinaci�n 4
de las sub-�reas de vac�o
Como en los casos 0 � 53
Sub-�rea: 12
Como en los casos 0 � 53
Sub-�rea: 12
500 � 553
(para Ergon)
Como en los casos 0 � 53 con combinaci�n 5
de las sub-�reas de vac�o
Como en los casos 0 � 53
Sub-�rea: 13
Como en los casos 0 � 53
Sub-�rea: 13
600 � 653
(para Ergon)
Como en los casos 0 � 53 con combinaci�n 6
de las sub-�reas de vac�o
Como en los casos 0 � 53
Sub-�rea: 23
Como en los casos 0 � 53
Sub-�rea: 23
Campo V
Bloqueo
Control
�Dispositivos en autom�tico
Bloqueo
dispositivos motorizados
NOTA 1: en caso de planos no motorizados, sino
dotados de visualizadores con retrofit hacia Xilog Plus
(es.: SIKO), el control autom�tico de los apoyos se realiza comprobando, en el
inicio programa pieza, las cotas se�alizadas por los visualizadores
(post posicionamiento manual del operador) con aquellas programadas. Si no hay
visualizadores con dicha caracter�stica, la selecci�n de V para el control
manual o autom�tico es irrelevante.
NOTA 2: para detalles acerca de los
dispositivos DUOMATIC, remitirse al Ap�ndice I
T
Habilita/inhabilita los elevadores (si hay)
y las luces l�ser para el posicionamiento de la pieza (si hay) seg�n la tabla
siguiente:
Campo T
Luces l�ser
Elevadores
TV Bar
0
No
No
OFF
1
No
S�
OFF
10
S�
No
OFF
11
S�
S�
OFF
100
No
No
ON
101
No
S�
ON
110
S�
No
ON
111
S�
S�
ON
M�s en general, la parametrizaci�n de dicho
campo puede realizarse, de manera m�s simple y extensa, a trav�s de la ventana
de di�logo dedicada:
Descripci�n de cada voz:
Par�metro
Significado
L�ser
Solicitud uso de la luz l�ser para el
posicionamiento de la pieza
Elevadores
Solicitud uso de los elevadores auxiliares
para cargar la pieza
Barra m�vil
Solicitud de posicionamiento de la barra
m�vil del �rea de trabajo master[1]
(si configurada con Fields.cfg)
Fila 1 de topes
Solicitud uso de los topes de la fila n�mero
1 (si presentes)
Fila 2 de topes
Solicitud uso de los topes de la fila n�mero
2 (si presentes)
Fila 3 de topes
Solicitud uso de los topes de la fila n�mero
3 (si presentes)
Fila 4 de topes
Solicitud uso de los topes de la fila n�mero
4 (si presentes)
Fila 5 de topes
Solicitud uso de los topes de la fila n�mero
5 (si presentes)
�reas asociadas
Solicitud combinaci�n
�reas de trabajo acerca de la gesti�n del vac�o (si las �reas est�n
asociadas, la solicitud de vac�o desde el selector de una cierta �rea acciona
el vac�o tambi�n en la otra �rea eventualmente asociada)
Verificaci�n posici�n ventosas
Vale para plano autom�tico Easyset
Morbidelli: solicitud de verificaci�n del posicionamiento de las ventosas al
final de la fase de setup
Desactiva C.U. mascarado
Vale para aplicaciones especiales: solicitud
de desactivaci�n del cambio herramienta mascarado.
Nota: el uso de este campo ha sido superado
con la introducci�n del par�metro �Cambio herramienta mascarado no
admitido� asociado con cada herramienta.
Adquisici�n BZ y DZ de palpadura
Solicitud de adquisici�n de los datos de
altura pieza (DZ) y colocaci�n (BZ) desde los valores derivados de las
operaciones de palpadura en modalidad MDI (v�ase �4.5.2 del manual del Panel
M�quina: Palpador).
Barra m�vil �rea asociada
Solicitud de posicionamiento de la barra
m�vil del �rea de trabajo asociada[2]
(si configurada con Fields.cfg)
Habilitaci�n elevadores doble carrera
Solicitud uso de los elevadores auxiliares para cargar la pieza en modalidad �doble carrera�.
Nota: actualmente inefectivo ya que
implementada soluci�n hardware dedicada.
R
N�mero de tableros iguales a producir (m�x.
9999).
BX
Distancia en X del cero del tablero con
respecto al cero del campo.
BY
Distancia en Y del cero del tablero con
respecto al cero del campo.
BZ
Dimensi�n en Z de un posible espesor situado
debajo del tablero.
La programaci�n de los par�metros V y T se
facilita por las tablas correspondientes, como mencionado previamente.
La tabla del par�metro T permite tambi�n
habilitar/inhabilitar:
�
� todos los ficheros de tope (la principal
m�s los posibles topes secundarios) relativos al �rea especificada en el
programa;
� la combinaci�n de las �reas;
� el control de la posici�n de las ventosas
para las mesas travesa�os y ventosas motorizadas;
� el cambio herramienta encubierto.
� Palpador autom�tico para m�quina UNIX
� Optimaci�n programa (v�ase punto 5.1)
� Optimaci�n PAV (v�ase punto 8.7.4)
� Optimaci�n pinzas para m�quina UNIX
En el editor texto, las tablas pueden estar
abiertas utilizando dos botones que est�n en la barra de las funciones.

Abrir la tabla para la introducci�n del
par�metro T.

Abrir la tabla para la introducci�n del
par�metro V.
Ejemplo:
�ATENCI�N!
La
dimensi�n en Z del tablero se utiliza para optimizar las traslaciones de los
cabezales entre trabajos realizados en caras distintas; por lo tanto, es
indispensable que en el campo DZ se introduzca la dimensi�n m�xima efectiva en
Z de la pieza; en caso contrario pueden ocurrir peligrosos choques entre los
cabezales y la pieza.
### 5.1.1 Palpaci�n panel y �martire### �
La
presencia de un dispositivo de palpaci�n montado en la cabeza, permite realizar
dos operaciones espec�ficas, en �mbito MDI (v�ase �4.5.2 del manual del Panel
M�quina: Palpador), para la medici�n del panel y del �martire�(panel de
soporte al panel en elaboraci�n). En este contexto, es posible solicitar que
los valores de los campos BZ y DZ del Header sean adquiridos al cargar el
programa autom�ticamente, directamente desde la m�quina. Esto es posible
configurando en �SI� el campo �T�
Adquisici�n BZ y DZ desde palpaci�n� y configurando en
�1� el par�metro de configuraci�n �Axis�GEN 2�
Adquisici�n datos de palpaci�n� o� configurando en �2� este �ltimo par�metro
(en dicho caso es irrelevante la programaci�n del campo T).