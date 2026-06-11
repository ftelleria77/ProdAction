
# 6.6 Importaci�n de un
archivo DXF
### 6.6.1
Proceso de importaci�n
El editor de Xilog Plus convierte archivos DXF, creados con un programa CAD,
en programas con extensi�n PGM, ejecutables en la m�quina perforadora -
taladradora. La modalidad de importaci�n de las geometr�as de los archivos DXF
y las caracter�sticas est�ndar de trabajo se definen en el archivo de configuraci�n
cad.cfg. A continuaci�n se detallan los diferentes par�metros definidos en este
fichero y sus correspondientes opciones:
C�digo
xISO/xISOE (0,1).
0 = Se generan instrucciones "base"
(ej. G0, G1, etc.).
1 = Se generan instrucciones
"extensas" (XG0, XL2P, etc.).
N�mero herramienta est�ndar.�����������������������
Xilog Plus asignar� por default este n�mero
herramienta a todos los trabajos importados.
Entradas/salidas
vac�as (0=NO).
0 = Todas las instrucciones de entrada en el /
salida del perfil (XGIN, XGOUT) se generan con los valores definidos en los
par�metros sucesivos.
1 = Las instrucciones arriba indicadas se
generan con todos los par�metros en cero (inhabilitadas).
Salidas
= entradas (0=NO).
0 = Las instrucciones arriba indicadas (xGIN,
xGOUT) se generan con los par�metros definidos a continuaci�n, que por lo
tanto, pueden ser diferentes.
1 = Las instrucciones de salida del perfil
(xGOUT) se generan con los mismos par�metros definidos para las de entrada del
mismo (xGIN)
Valores
para los par�metros C, G, Q, R de las instrucciones xGIN y xGOUT.
V�ase: Cap. 5 - Instrucciones de programaci�n.
M�x.
distancia empalmes (para Auto-Join).
Si dos elementos gr�ficos importados (ej.
l�neas, arcos, etc.) terminan a una distancia inferior a este par�metro, Xilog
Plus los considera conectados entre si en fase de agrupaci�n geometr�as
("Autojoin") y por lo tanto le asigna el mismo trabajo.
Al contrario, si distan m�s del valor
introducido, entonces se consideran pertenecientes a perfiles diferentes, para
los cuales se generar�n luego las correspondientes instrucciones XGIN y XGOUT.
El significado de este par�metro es el de
compensar posibles imprecisiones en la generaci�n de los perfiles dentro del
CAD: si su valor es demasiado peque�o, es posible que la importaci�n se produzca
de modo errado, generando demasiados perfiles disjuntos que tendr�n luego que
ser conectados "a mano". De lo contrario, si su valor es demasiado
grande, perfiles que deben quedar diferentes podr�an, indebidamente ser
"encolados".
Normalmente el valor est�ndar [0.01mm] resulta
satisfactorio.
Valores
DCH, DY, DZ del tablero.
Dimensiones predefinidas del tablero a
trabajar, que se reproducir�n en el header del programa Xilog Plus. Estos
valores constituyen los default usados cuando el fichero DXF no contiene estas
informaciones. Si en el fichero DXF est� presente el layer "tablero"
(v�ase abajo), las dimensiones definidas en �l sustituyen los valores de estos
par�metros.
Profundidad
est�ndar de los fresados (Z).
Valor est�ndar del campo Z generado para todas
las instrucciones de fresado. Este valor constituye el default que puede
modificarse en la fase de importaci�n. Este par�metro se ignora si el valor de
"Z fresados" es distinto de 0.
Velocidad� de fresado (m/min)
y Vel. di rotaci�n motor (g/min).
Son los valores de default asignados a los
fresados en la fase de import (que se pueden modificar m�s adelante seg�n sea
necesario).
Di�metro
m�ximo de los taladrados.
En fase de importaci�n de DXF, las gr�ficas
primitivas de tipo �CIRCLE� (�circulo�) se comparan con este valor: si el
di�metro del c�rculo es inferior o igual que el par�metro, se controla como
agujero (se genera una instrucci�n de taladrado optimado XBO); de lo contrario,
el mismo se controla como fresado.
Profundidad
est�ndar de los taladrados (Z).
An�logamente a todo los visto para los
fresados, este par�metro define la profundidad de default de los agujeros. Este
par�metro es ignorado cuando el valor de "Z taladrados" es diferente
de 0 o cuando est� programado el "Layer orificios verticales" (v�ase
p�gina siguiente).
Velocidad
de taladrado (m/min).
Velocidad de avance herramienta en taladrado
(default).
Tipo de
optimiz. (0=A., 1=X, 2=Y).
0 = ABSOLUTA- el recorrido del cabezal de
taladrado se minimiza siguiendo la diagonal.
1= EJE X - El recorrido del cabezal de
taladrado se minimiza antes seg�n el eje X y luego seg�n el eje Y.
2 = EJE Y - Como arriba, pero el recorrido se
optimiza antes seg�n el eje Y.
Prec.
de optimizaci�n (%).
Par�metro de control del algoritmo de
optimizaci�n: mayor es este valor, m�s elevado es el tiempo de c�lculo pero
mejor es la optimizaci�n. Normalmente el valor 80% da ya buenos resultados.
Tipo
brocas orificio (0=P, 1=L, 2=S).
Constituye el tipo de broca a usar para
default en la generaci�n de las instrucciones de taladrado (0 = plana, 1 =
lanza, 2 = punta con avellanador).
Altura
avellanador.
Para usar s�lo si el tipo de broca est�
regulado en 2.
Nr.
Arcos por cuadrante en la interpolaci�n elipsis.
Se usa para la generaci�n de las elipses,
mayor es este valor, mejor ser� la interpolaci�n de geometr�as de tipo
"ELLIPSE" (elipses). Normalmente valores entre 3 y 6 se consideran
aceptables, pero para alcanzar una mayor precisi�n de interpolaci�n podr�a ser
necesario incrementar este valor.
Directorio.
No usado.
Layer
dimensiones tablero.
"Ra�z" del nombre del layer que
define las dimensiones del tableros.
Layer
trabajos pant�grafo.
Nombre del layer que define todas las
geometr�as relativas a fresados.
Layer
orificios� verticales.
�Ra�z" de los nombres de layer que
definen operaciones de taladrado "verticales" (cara 1).
Layer
orificios horizontales.
"Ra�z" de los nombres de layer que
definen operaciones de taladrado "horizontales".
Z
taladrados (0=CFG, 1=THK, 2=ELEV).
Criterio de definici�n de la profundidad de
taladrado. Este par�metro se ignora cuando est� definido el "Layer
orificios� verticales".
0 = La profundidad de taladrado se deduce del
par�metro de configuraci�n �Profundidad est�ndar de los taladrados (Z)�.
1 = La profundidad de taladrado se deduce de
la propiedad THICKNESS de la geometr�a, tal como definida en el fichero DXF.
2 = La profundidad de taladrado se deduce de
la propiedad ELEV de la geometr�a, tal como definida en el fichero DXF.
Z
fresados (0=CFG, 1=THK, 2=ELEV).
Criterio de definici�n de la propiedad de
trabajo para los fresados. Si este par�metro est� regulado en 1 � 2, no ser�
posible modificar, en fase de importaci�n, la cota Z de los trabajos y los
puntos de entrada en el perfil (tales regulaciones podr�n ser modificadas s�lo
sucesivamente editando el fichero PGM importado).
0 = La profundidad de taladrado se deduce del
par�metro de configuraci�n �Profundidad est�ndar de los fresados (Z)�.
1 = La profundidad de taladrado se deduce de
la propiedad THICKNESS de la geometr�a, tal como definida en el fichero DXF.
2 = La profundidad de taladrado se deduce de
la propiedad ELEV de la geometr�a, tal como se define en el fichero DXF.
►El archivo DXF se abre con el comando archivo/Abrir. Una
vez abierto, aparece una ventana de Programaci�n datos generales, en la que se
introducen o modifican los datos �tiles para el Encabezamiento del programa
PGM.
Longitud, ancho, espesor. Dimensiones del tablero (campos DX / DY / DZ).
Offset X/Y.
Eventuales traslaciones del origen del tablero (campos BX / BY).
Factor de escala.
Factor por el que se multiplican todas las coordenadas X e Y presentes en el
archivo DXF.
Lado. Lado del
tablero al que se refieren las geometr�as importadas.
Di�metro m�x. Todos
los c�rculos que tienen un di�metro inferior o igual al programado se
convierten en perforaciones (de di�metro igual al del c�rculo: XBO), mientras
que los de di�metro superior se convierten en fresados (XG0, XA2P).
Herramental.
Nombre del archivo de equipamiento que debe ser utilizado.
Zona de trabajo.
Zona de trabajo del programa.
Auto-Join. Permite
unir los trazos disjuntos antes de la conversi�n a PGM.
Fin programa.
Permite programar cotas X e Y para la instrucci�n N/XN de fin del programa.
El bot�n CONVIERTE EN PGM E ABRIR PGM
Acciona autom�ticamente la conversi�n a formato PGM usando los datos est�ndar y
los que se han programado y visualizados en la ventana de Introducci�n datos
generales y luego abre el programa PGM contenido.
En cualquier momento del control del
fichero DXF es posible volver a abrir esta ventana y accionar el mando arriba
indicado.
►Tras configurar los datos generales, aparece la representaci�n gr�fica
del archivo DXF y se activan algunas funciones espec�ficas para convertir el
archivo, presentes en el men� Modificar y en los botones
de la barra de funciones.
Las geometr�as se pueden seleccionar con el
rat�n. Como en el editor gr�fico de los programas, los elementos seleccionados
pueden ser de color verde (los perfiles despu�s de la operaci�n de auto-join,
v�anse las p�ginas siguientes) y rojo (los tramos de un perfil); el cuadrado azul
se�ala el punto final del tramo. Para seleccionar los perfiles y los tramos
tambi�n se pueden utilizar las teclas flecha del teclado: las flechas
horizontales, para pasar de un perfil a otro; las flechas verticales, para
desplazarse por los tramos de un perfil.
►En primer lugar, hay que eliminar los tramos que no corresponden a
trabajos del tablero (por ejemplo, cotas y perfiles) y eventuales tramos
superpuestos y/o cruzados, que podr�an provocar una interpretaci�n incorrecta
de las geometr�as. Para eliminar una geometr�a, hay que seleccionarla y hacer
clic en el men� Modificar/Eliminar.
►A continuaci�n, hay que agrupar las geometr�as del archivo DXF en
recorridos de herramienta, es decir, crear perfiles caracterizados por la
continuidad de recorrido entre los tramos contiguos. Esta operaci�n se realiza
de modo autom�tico en todas las geometr�as del dise�o al hacer clic en el men� Modificar/Auto Join.
►Adem�s, en todas las geometr�as es posible:
� modificar el sentido de avance
(horario-antihorario) en el men� Modificar/Inversi�n recorrido perfil;
� modificar el punto de entrada en un
perfil y las caracter�sticas de un orificio en el men� Modificar, en la opci�n entrada/datos orificio.

Programaci�n� entrada en el perfil
Offset. Definici�n
del punto de entrada en el perfil con respecto al punto de inicio de la
geometr�a seleccionada.
Si el valor es positivo (sin superar la
longitud de la geometr�a), la geometr�a se divide en dos geometr�as distintas
desde el punto inicial equivalente al offset especificado. El resultado es
distinto seg�n el tipo de recorrido �til original:
� En el recorrido �abierto� (con puntos de
entrada y salida distintos), �ste se �divide� en dos recorridos distintos que
tendr�n final e inicio respectivamente en el punto de �separaci�n�. Estos
nuevos recorridos son independientes entre s� y se pueden gestionar por
separado.
� En el recorrido de la herramienta
�cerrado� (el inicio y el final coinciden), las geometr�as se reorganizan de
modo que el punto de entrada y salida de la herramienta corresponda al punto de
�separaci�n� programado; por tanto, se obtiene un solo recorrido de la
herramienta.
Profundidad. Cota
de trabajo.
Vel. rotaci�n y Vel.
de trabajo. Velocidad de rotaci�n y de trabajo de la herramienta
seleccionada.
Herramienta.
Herramienta seleccionada para el trabajo.
Programaci�n� par�metros del� orificio
►Tambi�n se puede cambiar el orden de la secuencia de trabajos.
Seleccionando el men� Modificar/Ordenaci�n de las geometr�as, en los puntos iniciales de cada trabajo aparece un n�mero que indica
la secuencia en curso. Para modificarla:
1. Seleccionar el trabajo a realizar en primer lugar.
2. Pulsar la tecla [env�o] para confirmar: el
n�mero que aparece al lado del perfil seleccionado es 1.
3. Repetir los puntos 1 y 2 para modificar los dem�s trabajos.
NOTA. Todos los
trabajos presentes deben ser confirmados, aunque est�n en el orden deseado.
Para salir de la funci�n Orden de geometr�as,
hay que hacer clic en el men� Modificar/salida de la ordinaci�n.
►El men� ModificaR/Sistema
dE REFERENCIA permite modificar el sentido de los
fresados circulare y programar la especularidad de los ejes X e Y.
►Ahora, es posible guardar el archivo en formato PGM (o XXL). Un mismo
archivo DXF se puede guardar varias veces en distintos archivos. Los archivos
PGM obtenidos se pueden modificar con el editor de texto o gr�fico de Xilog Plus.
### 6.6.2
Layer
#### 6.6.2.1 Layer dimensiones tablero
Indica las dimensiones totales del panel bruto
a partir del cual lograr el panel acabado (par�metros DX, DY, DZ).
� En el archivo DXF, el layer debe contener
4 l�neas (LINE) unidas que forman el rect�ngulo de dimensi�n total (los
elementos LINE de este layer definen s�lo las dimensiones en X e Y del panel y
no son interpretados como fresados lineales).
� El nombre del layer debe estar seguido
por un n�mero el cual representa la dimensi�n en Z de dicho panel.
Si el par�metro �Layer dimensiones tablero� no
est� programado, son v�lidas las dimensiones del panel programadas en los
par�metros DX, DY, DZ de la ventana Programaci�n
datos generales.
Ejemplo:
Configuraci�n cad.cfg
Archivo DXF
Valor DZ

�Layer dimensiones tablero� = PANN

PANN25
25 mm

PANN25_5
25.5
mm
#### 6.6.2.2 Layer trabajos pant#### �#### grafo
Indica el perfil que se desea crear partiendo
de la pieza bruta. En este caso no resulta necesario especificar un par�metro
num�rico puesto que� l�neas, arcos o
c�rculos de este layer est�n convertidos en fresados. La profundidad de estas
elaboraciones est� determinada por el par�metro �Z fresados� del archivo de configuraci�n cad.cfg.
Atenci�n! Todos los elementos geom�tricos que no pertenecen a otros layer
tambi�n se consideran elementos de este layer.
#### 6.6.2.3 Layer orificios verticales
Definen los taladrados verticales como
alternativa al m�todo est�ndar basado en la programaci�n del par�metro Di�metro
M�ximo Taladrados (in Programaci�n datos
generales) el cual corresponde a todos� los CIRCLE presentes en el archivo DXF. Si
ha sido programado, el layer de los taladrados verticales establece que s�lo los c�rculos de este layer son
interpretados como orificios verticales; el di�metro de estos �ltimos es el
di�metro del c�rculo programado en el archivo DXF.
En el archivo DXF el nombre del layer debe
estar seguido por un n�mero que representa la dimensi�n en Z de los orificios
(respecto a la superficie del panel) pertenecientes a dicho layer. Con
taladrados de di�metro distinto se obtendr�n varios layer.
Ejemplo:
Configuraci�n cad.cfg
Archivo DXF
Valor Z en XBO

�Layer orificios verticales� = FV

FV-25
-25
mm

FV25_5
25.5
mm
#### 6.6.2.4 Layer orificios horizontales
Define los orificios horizontales importados
como instrucciones BR o XBR.
Para poder programar estos orificios resulta
necesario caracterizar el archivo DXF (mediante el C.A.D.) del siguiente modo:
1. Introducir el dibujo de una broca con l�neas cerradas y con los lados unitarios (1 x 1) en un bloque de
nombre HORIZ.
2. Crear un layer con nombre HO. En el archivo DXF el nombre del layer
debe estar seguido por un n�mero que corresponde con la distancia desde el
centro del orificio a la mesa de trabajo (lado inferior del panel � v�ase el
par�metro H de la instrucci�n XBR).
Ejemplo:
Configuraci�n cad.cfg
Archivo DXF
Valor H en XBR

�Layer orificios horizontales� = HO

HO25
25 mm

HO25_5
25.5
mm
3. Introducir el bloque HORIZ en el layer HO especificando:
� Coordenada
X del punto P de inserci�n del bloque. Equivale a la
cota X de la instrucci�n XBR.
� Coordenada
Y del punto P de inserci�n del bloque. Equivale a la
cota Y de la instrucci�n XBR.
� Coordenada
Z del punto P de inserci�n del bloque. Introducir 0.
� Escala
en X. Introducir el di�metro del orificio.
� Escala
en Y. Introducir la profundidad del orificio.
� �ngulo
de rotaci�n (v�ase fig. siguiente).

### 6.6.3
Secciones DXF importables
Se reconocen las siguientes secciones:
� Header
� Tables
� Entities
� Blocks (s�lo
para las perforaciones horizontales mediante layer)
Se importan los siguientes elementos:
� Line
� Arc
� Circle
� Polyline
� Ellipse
� Lwpolyline (Rectangle, Polygon)
� Insert (s�lo
para las perforaciones horizontales mediante layer)
Los valores $EXTMIN y $EXTMAX
presentes en la secci�n HEADER establecen la amplitud de elaboraci�n en
funci�n de la que se realiza el dibujo de las elaboraciones sobre el tablero.
Si estas cotas no se encuentran en el archivo DXF, no es posible garantizar la
correcta visualizaci�n de las geometr�as.
El importador DXF s�lo tiene en cuenta las
geometr�as producidas con el CAD mencionadas anteriormente.
�ATENCI�N!
El
archivo DXF debe contener siempre la secci�n Header
(para
mayor informaci�n consultar los manuales del CAD)
�����������������������