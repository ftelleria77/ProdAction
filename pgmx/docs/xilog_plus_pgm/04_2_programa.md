
# 4.2 Programa
### 4.2.1 Introducci�n a los programas de
trabajo
#### 4.2.1.1 Estructura de
un programa
El programa consiste en una secuencia de
instrucciones que describe un ciclo de trabajos en el panel. Dicho ciclo se
memoriza en un archivo binario en el formato principal PGM y se traduce al
lenguaje ISO en el momento de su ejecuci�n en la m�quina.
La primera instrucci�n de todos los programas
debe ser el Encabezamiento (o Header), seguida del resto de
instrucciones (perfiles, perforaci�n y movimientos).
El programa puede contener varios perfiles (o
recorridos geom�tricos que la herramienta ejecuta en modo continuo) y
perforaciones. La primera instrucci�n de los perfiles es la Entrada
autom�tica (GIN o XGIN),
seguida del Inicio fresado (G0 o XG0). A continuaci�n, aparecen todas las instrucciones
geom�tricas y al final la instrucci�n Salida autom�tica (GOUT o XGOUT).
Ejemplo esquem�tico de un perfil:
GIN
entrada
autom�tica
G0
inicio
fresado
�
geometr�a

�
geometr�a
GOUT
salida
autom�tica
Ejemplo esquem�tico de un programa con
instrucciones de fresado y taladro:
H
encabezamiento
GIN
entrada autom�tica
G0
inicio fresado
�
geometr�a
�
geometr�a
GOUT
salida autom�tica
B
perforaci�n
GIN
entrada autom�tica
G0
inicio fresado
�
geometr�a
�
geometr�a
GOUT
salida autom�tica
�����������������������
Las instrucciones se
dividen en:
� Instrucciones
operativas. Son instrucciones que definen los trabajos
efectivos de la pieza. En la fase de ejecuci�n del programa, a cada una de
estas instrucciones le puede corresponder un movimiento �nico o una serie de
movimientos del grupo operador de la m�quina. Por ejemplo, en el caso de la
perforaci�n, el cabezal operador de la m�quina realiza la operaci�n en varias
fases predeterminadas.
� Instrucciones
modales. Las instrucciones modales se pueden escribir
varias veces en el interior de un programa pero de ninguna manera la introducci�n
sucesiva de una instrucci�n modal anula la introducci�n anterior a dicha
instrucci�n. Estas instrucciones, ejercen su funci�n sobre el significado de
las cotas X, Y y Z que se encuentran en todas las instrucciones operativas
sucesivas a la llamada de la instrucci�n modal. Por ejemplo, la introducci�n de
una cara diferente de trabajo permite que las cotas X, Y, Z de todas las
instrucciones operativas sucesivas se refieran al origen de la nueva cara
introducida. En las instrucciones operativas del lenguaje completo, que no
corresponden al trabajo intermedio de un perfil, la ventana para introducir los
datos de los cuatro campos est�ndar para las instrucciones F, C, K y P (en el
editor de texto) y los botones de la barra de datos modales (en el editor
gr�fico) facilita la programaci�n de las instrucciones modales. En el editor
gr�fico se activan s�lo los botones para efectuar el cambio de cara
(equivalente a la instrucci�n F) y la correcci�n de la herramienta (equivalente
a la instrucci�n C); para poderlos utilizar, hay que seleccionar el cambio de
cara o la correcci�n de la herramienta antes de introducir una instrucci�n
nueva. NOTA. Las instrucciones PL/XPL y la instrucci�n de cambio de cara F se
anulan entre si.
� Instrucciones
de gesti�n de los subprogramas. Permiten llamar hacia
el interior de un programa otro programa introducido anteriormente. A este
�ltimo programa se le pueden pasar nuevos par�metros mediante la programaci�n
param�trica.
� Env�o
de mensajes al operador. Los mensajes al operador son informaciones
enviadas al operador durante la elaboraci�n de la pieza.
� Instrucciones
de ayuda a la programaci�n. Permiten introducir
cualquier secuencia de caracteres ASCII que ayude al programador en la
redacci�n del programa. Adem�s, puede visualizar o memorizar los mensajes de
diagn�stico durante la visualizaci�n gr�fica del programa. Estas instrucciones
se ignoran en fase de ejecuci�n del programa.
Xilog Plus dispone de dos tipos de editor para escribir y modificar los
programas:
� editor de texto
� editor gr�fico
#### 4.2.1.2
Editor de los programas
El tipo de editor ha de ser seleccionado antes
de crear o abrir un programa.
► Como seleccionar el tipo de editor.
Hacer
clic en el men� OPcIONes, poner el puntero del rat�n
sobre el tipo de editor deseado y hacer clic para seleccionarlo.

Las instrucciones de programaci�n de los
trabajos pueden ser de dos tipos:
� instrucciones b�sicas (o texto);
� instrucciones completas (o
gr�ficas), con una X inicial para distinguirlas de las instrucciones b�sicas
correspondientes.
En el editor de texto se pueden introducir
instrucciones de ambas clases, mientras que en el editor gr�fico se introducen
principalmente instrucciones completas, aunque tambi�n puede interpretar
gr�ficamente instrucciones b�sicas.
Para facilitar la introducci�n de
instrucciones completas (y de algunas instrucciones b�sicas en el editor de texto), la barra de instrucciones de
ambos editores dispone de iconos que representan gr�ficamente los principales
grupos de instrucciones. Haciendo clic en el icono de un grupo con el bot�n derecho
del rat�n se visualiza la lista de instrucciones que componen ese grupo.
����������������������
El editor de texto, en modalidad guiada,
tambi�n dispone de una ventana para introducir par�metros, que se puede
utilizar como alternativa a la barra de instrucciones.
Al introducir una instrucci�n utilizando la
barra de instrucciones, aparece una ventana gr�fica para introducir datos.
En la mayor�a de los casos, al abrirse la
ventana aparecen s�lo los par�metros principales o �b�sicos�; para visualizar
los par�metros �completos�, hay que hacer clic en el bot�n
Haciendo clic por segunda vez en este bot�n
(si la ventana est� completa las flechas se�alan hacia arriba), los par�metros
completos desaparecen de la pantalla.
Adem�s se habilitan los botones:
� OK, para confirmar la introducci�n de la
instrucci�n;
� anular, para deseleccionar la instrucci�n;
� Par�, para abrir la tabla de par�metros;
� ?, para acceder a la Gu�a en l�nea de Xilog Plus.
#### 4.2.1.3#### Origen
m�quina
Seg�n el tipo de m�quina, el punto 0 respecto
al cual se miden las distancias (origen m�quina) puede ser delantero o trasero.
Por
ejemplo, el origen es:
� delantero, en las m�quinas Record y
Ergon;
� trasero, en las m�quinas Author, Pratix,
Tech.
El desplazamiento de la profundidad (par�metro
Z) est� indicado con valores positivos. Por ejemplo, para programar
un taladrado de 100mm de profundidad a partir de la cota Z=0, en el par�metro Z
se introducir� el valor 100. El valor -100 provocar�, al contrario, el alejamiento
de la fresa de la mesa de trabajo.
ATENCION!
En las m�quinas
Record, Ergon y Pratix no equipadas con CNC OSAI el par�metro Z est� invertido
(Z positivo: alejamiento de la mesa de trabajo; Z negativo: acercamiento a la
mesa de trabajo).
#### 4.2.1.4#### Areas
de trabajo
Cada programa se lanza dentro de un �rea de trabajo. La mesa de trabajo
est� dividida ordinariamente en 4 �reas (A, B, C, D).
Cada �rea tiene un origen propio de los ejes,
orientado seg�n el origen m�quina.
En las mesas
con cero central y cuatro topes m�viles (uno a la izquierda, uno a la
derecha y dos centrales), la presencia de los topes m�viles centrales permite
programar cada uno de los trabajos independientemente en las cuatro �reas.
Adem�s, las �reas pueden ser utilizadas tambi�n en pares: por ejemplo, si el
tablero a trabajar tiene dimensiones que ocupan dos �reas, se puede utilizar en
fase de programaci�n un �rea doble, como el �rea AB (con origen de los ejes en
A)...
�o BA
(con origen de los ejes en B).
En las mesas
sin cero central (sin topes m�viles centrales) la presencia de los topes
s�lo en los extremos izquierdo y derecho de la mesa de trabajo permite utilizar
s�lo las �reas AB y DC. En este caso, no es posible plantear el programa de
trabajo en las �reas B, C, BA y CD, mientras el planteo de las �reas A y D es
considerado autom�ticamente por Xilog Plus equivalente, respectivamente, a las
�reas AB y DC..
ATENCION!
Para las
m�quinas no equipadas con CNC OSAI vale la configuraci�n siguiente: �rea
izquierda=A; �rea derecha=B.
La mesa puede confirugarse tambi�n con �reas
especulares: por ejemplo, respecto de las �reas A, B, C, D arriba detalladas se
pueden tener a disposici�n en la mesa de trabajo las respectivas �reas
especulares E, F, G, H.
Para plantear el �rea de trabajo de un
programa v�ase: instrucci�n H.

### 4.2.2 Editor de texto
#### 4.2.2.1
Interfaz
La ventana del editor de testo est� dividida
en cuatro �reas (A, B, C, D):
A) En esta �rea se
visualiza el Encabezamiento del programa.
B) Ventana de
visualizaci�n de los pasos del programa.
C) �rea reservada
para introducir o modificar las instrucciones del programa.
D) �rea para
visualizar informaci�n de ayuda.
Existe dos modalidades en el editor de texto:
� Libre (editor
libre). En esta modalidad el �rea C presenta un solo campo, en cuyo interior se
pueden escribir y eliminar datos (en el campo derecho del �rea D aparece
�LIBRE�).
� Guiada (editor
guiado). En esta modalidad, en lugar del campo aparece una ventana para
introducir los par�metros (en el campo derecho del �rea D aparece �GUIADO�).

► Como seleccionar la modalidad libre o guiada del editor de texto.
Hacer
clic en el men� Visualizar, colocar el puntero del rat�n
sobre la modalidad del editor deseada y hacer clic para seleccionarla.
Es
posible pasar de la modalidad libre a la guiada en todo momento, excepto
cuando el editor est� en modo de error (v�anse las p�ginas siguientes).

�
► Como
insertar una instrucci�n nueva en modalidad libre.
1

Tras
escribir el Encabezamiento, pulsar la tecla [Flecha abajo].
El
editor pasa a la modalidad insertar: en el �rea B aparece el n�mero de una
instrucci�n nueva y el campo C vac�o.
En
el �rea D aparece la indicaci�n INS.
Para
insertar una instrucci�n nueva en el cuerpo del programa, hay que pulsar el
bot�n o la tecla [INS]: la instrucci�n nueva se inserta
despu�s de la seleccionada.

2

Escribir
la instrucci�n nueva en el campo del �rea C.
Sugerencia
Para
evitar que un valor num�rico se convierta en mm o pulgadas, escribir el
n�mero seguido del car�cter #.

3

Pulsar
la tecla [ENV�O] para insertar la instrucci�n nueva en el programa.
Despu�s de haber confirmado una instrucci�n, Xilog Plus regresa a la modalidad
insertar.

�Atenci�n!
Cuando
se inserta una instrucci�n incorrecta, el editor habilita el modo de error
(en el �rea D aparece la indicaci�n BLK)
Para
poder insertar una nueva instrucci�n, hay que corregir el error.
► Como
insertar una instrucci�n nueva en modalidad guiada.
1

Tras
escribir el Encabezamiento, pulsar la tecla [Flecha abajo].
El
editor pasa a modalidad insertar: en el �rea B aparece el n�mero de una nueva
instrucci�n y en la ventana de los par�metros aparece un campo vac�o.
En el �rea D se visualiza la indicaci�n INS.

Para
insertar una instrucci�n nueva en el cuerpo del programa, hay que pulsar el
bot�n o la tecla [INS]: la nueva instrucci�n se inserta
despu�s de la seleccionada.

2

Escribir la sigla de una instrucci�n en el campo.

3

Pulsar la tecla [ENV�O].
4

Aparecen los
campos para escribir los par�metros relativos a la instrucci�n.
Escribir los par�metros en los campos. Al finalizar, pulsar la tecla [ENV�O] para insertar la nueva instrucci�n en el programa.
Despu�s de haber confirmado la instrucci�n, Xilog Plus regresa a la
modalidad de introducci�n.
Sugerencia
Para evitar
que un valor num�rico se convierta en mm o pulgadas, escribir el n�mero
seguido del car�cter #.

�Atenci�n!
Cuando
se inserta una instrucci�n incorrecta, el editor habilita el modo de error
(en el �rea D aparece la indicaci�n BLK). Para poder insertar una nueva
instrucci�n, hay que corregir el error.

NOTA. Las
instrucciones tambi�n se pueden insertar utilizando la barra de instrucciones,
v�ase el cap�tulo 4.2.3 - Editor gr�fico.
► Como modificar una instrucci�n (en modalidad libre o guiada).
1

Pulsar
las teclas [FLECHA
ARRIBA] o [FLECHA ABAJO] para pasar de una instrucci�n a otra del
programa.
El editor
pasa a la modalidad modificar.

2

Modificar
los par�metros en el campo de texto del editor� libre o en los campos del editor guiado.
3

Pulsar
la tecla [ENV�O] para confirmar las modificaciones.
4

Para
eliminar la instrucci�n seleccionada, hay que hacer clic en el men� MODIFICAr/ELIMINAR.

#### 4.2.2.2 Modalidad bloques
Con el editor de texto de Xilog Plus, es posible cortar
y copiar un bloque de l�neas del programa y pegarlo en otro lugar o dentro de
otro programa.
► Como cortar y copiar un bloque de l�neas y pegarlo en otra posici�n.
1

Seleccionar
la primera l�nea a cortar y pulsar las teclas [FLECHA ABAJO] o
[FLECHA
ARRIBA] para mover la barra de selecci�n por el
programa. Pulsar las teclas [May�s] + [Flecha
abajo], para seleccionar l�neas hacia abajo; [may�s] + [Flecha
arriba], para seleccionar l�neas hacia arriba. �
2

Hacer
clic en el men� MODIFICAR/cortar�

� o en
el bot�n cortar.
Las
l�neas cortadas desaparecen de la pantalla.

3

Seleccionar
una l�nea del programa.
Hacer
clic en el men� MODIFICAr/pegar�

� o en
el bot�n pegar.
Las
l�neas cortadas se insertan tras la instrucci�n seleccionada.

4

Para
salir de la modalidad bloques, hay que pulsar la tecla [ESC].
5

Repetir los pasos 1-3, pero, al llegar al paso 2, seleccionar el
comando cortar y, a continuaci�n, hacer clic en el men� MODIFICAr/COPIAr

� o en
el bot�n COPIAR.
Las
l�neas copiadas permanecen en su posici�n original y se pueden pegar igual
que las l�neas cortadas.

Sugerencia
Las
l�neas cortadas o copiadas se pueden pegar varias veces.
Las funciones
Cortar/Copiar y Pegar tambi�n se pueden utilizar en el editor de texto aunque
no est� en modalidad bloques, pero sobre una sola l�nea de instrucciones.

#### 4.2.2.3 Visualizaci�n
gr�fica
Esta funci�n sirve para visualizar
gr�ficamente el trabajo que se est� programando en el editor de texto. En caso
de programas que requieren subprogramas (con la instrucci�n S/XS), es necesario
cerrar y volver a abrir el programa principal para actualizar la gr�fica de los
subprogramas.
► Como
visualizar gr�ficamente un trabajo programado con el editor de texto.
Hacer
clic en el men� herramientas/ GR�FICa PROGRAMa.

� o en
el bot�n.

### 4.2.3
Editor gr�fico
El editor gr�fico representa gr�ficamente las
instrucciones de trabajo. La imagen gr�fica se actualiza mientras se introducen
las instrucciones del programa; en caso de programas que requieren subprogramas
(con la instrucci�n S/XS), es necesario cerrar y volver a abrir el programa
principal para actualizar la gr�fica de los subprogramas.
En este ambiente es posible introducir todas
las instrucciones enumeradas en el cap�tulo 5.3 (instrucciones completas) � que
representan un subgrupo de las instrucciones disponibles en el editor de texto
(instrucciones b�sicas � v�ase el cap�tulo 5.2) � utilizando las ventanas
gr�ficas de la barra de instrucciones (v�anse las p�ginas siguientes). El
editor gr�fico tambi�n representa el resto de instrucciones disponibles en el
editor de texto, pero s�lo es posible insertarlas o modificarlas en modalidad
de texto libre.
Nota: Se aconseja
no insertar instrucciones b�sicas en el editor gr�fico, salvo instrucciones
especiales (como las instrucciones ISO y SET).
La ventana del editor gr�fico est� dividida en
tres �reas (C, D, F); en esta modalidad del editor se activan dos nuevas barras
(A, B). Para introducir datos, hay que utilizar la barra de instrucciones (E).
A) Barra de herramientas gr�ficas (v�ase
el Ap�ndice A).
B) Barra de datos modales (v�ase el Ap�ndice A).
C) En este �rea siempre se visualiza el
Encabezamiento del programa. En los campos de la derecha aparecen la escala de
visualizaci�n y el valor del zoom de aumento.
D) En este �rea aparece la visualizaci�n
gr�fica de las instrucciones de trabajo. En la pantalla se visualiza la cara
superior del tablero y, alrededor, los perfiles de los lados. Las instrucciones
seleccionadas se representan gr�ficamente con varios colores:
- rojo, para los
tramos simples;
- verde, para los
perfiles;
- fucsia, para los
tramos pasantes (es decir, los que superan el espesor del tablero);
- azul, para los
perfiles pasantes.
E) En el tramo seleccionado se visualiza
un cuadrado azul, que se�ala el punto final del tramo, y un c�rculo, al inicio
del tramo, que representa gr�ficamente la correcci�n del radio de la
herramienta.
F) Barra de instrucciones.
G) �rea que visualiza informaciones de
ayuda.
► Como insertar una instrucci�n nueva.
1

Las
instrucciones est�n agrupadas en la barra de instrucciones.
Como
introducir una instrucci�n de perforaci�n.
Hacer
clic en el bot�n Taladrado.

2

Aparece
la ventaba que muestra las instrucciones disponibles en el grupo
seleccionado.
Pulsar
las teclas [Flecha
DErecha] y [Flecha IZQUIERDA] para recorrer las im�genes de la lista de instrucciones.
La
imagen de la instrucci�n seleccionada se visualiza dentro de un cuadrado
amarillo.

3

�Hacer clic en el bot�n OK para confirmar la instrucci�n seleccionada.

��

Sugerencia
�
Para
confirmar la instrucci�n seleccionada, hacer clic sobre la imagen o pulsar la
tecla [eNV�O].

4

Aparecen
los campos para introducir los par�metros de la instrucci�n.
Escribir
los par�metros en los campos. Para insertar una instrucci�n en el programa,
hay que hacer clic en el bot�n OK o pulsar la tecla [eNV�O].
Sugerencia
Para
evitar que un valor num�rico se convierta en mm o pulgadas, escribir el
n�mero seguido del car�cter #.

�Atenci�n!
Cuando
se inserta una instrucci�n incorrecta, el editor habilita el modo de error
(en el �rea D aparece la indicaci�n BLK) y la representaci�n gr�fica no se
actualiza. Xilog Plus solicita la correcci�n del error para poder proseguir. Si no se corrige el
error, el programa restablece la �ltima condici�n sin errores.

► Como modificar una instrucci�n.
1

Para
seleccionar las instrucciones del programa, hay que pulsar las teclas [Flecha arriba] o [Flecha abajo].
El
nombre de la instrucci�n seleccionada aparece en el campo de la izquierda del
�rea C; en el campo de la derecha aparecen los par�metros X, Y, Z, I, J.

2

Pulsar
la tecla [eNV�O].
Aparece
la ventana para introducir los par�metros relativos a la instrucci�n
seleccionada.

Las instrucciones se pueden seleccionar
tambi�n directamente en la representaci�n gr�fica, haciendo clic en la l�nea
o c�rculo correspondiente; un clic doble o la presi�n de la tecla [ENVIAR] provoca la apertura de la plantilla de modificaci�n de los
par�metros.
Si no se ha seleccionado ninguna instrucci�n
todav�a, la presi�n de la tecla [ENVIAR] abre la ventana
de los par�metros del heading (para deseleccionar una instrucci�n haga clic
en el men� MODIFICAR/REINTERPRETAR).

3

Modificar los par�metros. Pulsar la tecla [eNV�O] para
confirmar las modificaciones.

4

Para
eliminar la instrucci�n seleccionada, hay que hacer clic en el men� MODIFICAr/ELIMINAr.
Por
default se elimina cada trecho seleccionado. Y tambi�n es posible eliminar
todo el perfil del cual forma parte el trecho seleccionado: seleccionar la
opci�n especial en la ventana que aparece antes de la confirmaci�n de la
eliminaci�n.

Para las instrucciones dotadas de par�metros
modales hay una ventana disponible de programaci�n de las Propiedades con diferenes opciones. Seleccionar la instrucci�n y
hacer clic en el men� MODIFICAR/PROPIEDADES.
�
En el caso de los fresados, tambi�n hay
botones disponibles que permiten acceder directamente a las p�ginas de los
par�metros de las instrucciones XG0, XGIN y XGOUT.

► Como mover o duplicar una
instrucci�n.
1

Las
instrucciones representadas gr�ficamente se pueden mover o duplicar con el
men� de selecci�n r�pida.
Seleccionar
un tramo con el bot�n izquierdo del rat�n y, a continuaci�n, hacer
clic sobre el tramo con el bot�n derecho del rat�n para que aparezca
el men� de selecci�n r�pida.

2

Hacer
clic en mover.

3

Aparece
la ventana Desplazar trabajo.
Introducir
las cotas (absolutas u offset) de la nueva posici�n y hacer clic en el bot�n Ok para confirmar.

4

En
la instrucci�n seleccionada se pueden aplicar los comandos Cortar (para
mover) y Copiar (para duplicar), tambi�n disponibles en el men� de selecci�n
r�pida.
Cortar
o copiar la instrucci�n seleccionada.

La copia de una instrucci�n gr�fica de
taladrado, de una instrucci�n XEA o de un sub-programa puede realizarse de dos
modos: como uno o varios trabajos simples (valor de default) o como instrucci�n
�nica.
�ATENCI�N!
El primer modo NO MANTIENE LOS PAR�METROS
porque el trabajo no se copia como un conjunto de instrucciones (cada uno con
sus par�metros) pero como trabajo representado por instrucciones de base
programadas con las cotas (X, Y, Z, �) absolutas. Este modo es el �nico que
asegura que el trabajo, en cualquier parte del programa sea encolado, mantenga
sus caracter�sticas.
De lo contrario, el trabajo podr�a modificar
sus caracter�sticas porque el valor de los caracteres puede diferir de un punto
a otro de un programa.
Por ejemplo, una instrucci�n XB de taladrado
que prev� 5 repeticiones del mismo agujero, ser� copiada (y si es necesario
reproducida con el mando pegar):
� en el primer caso (valor de default),
como 5 instrucciones diferentes;
� en el segundo caso, como una sola
instrucci�n..
5

Hacer
clic en pegar

6

Aparece
la ventana Colocaci�n� nuevo trabajo.
Introducir
las cotas offset de la nueva posici�n y el eventual posicionamiento
especular; hacer clic en el bot�n Ok para confirmar.
Si
se selecciona las opciones Especular X/Y o Inversi�n del sentido de los
fresados, Xilog Plus se ocupa autom�ticamente de seleccionar otras opciones
recomendadas para el posicionamiento del trabajo.

► Visualizamos la estructura del
programa.
Para
trabajar con mayor facilidad en un programa complejo, es posible visualizar
la estructura del programa.
Hacer clic en el men� visualizar/estructura
del programa�

� o sul pulsante.

El trabajo seleccionado se evidencia en la
representaci�n gr�fica. Los trabajos representados en la estructura pueden
seleccionarse y desplazarse corriendo el rat�n; adem�s, est�n disponibles los
mandos del men� de selecci�n r�pida. La estructura visualiza los comentarios
introducidos en el campo �Comentario� de las instrucciones (de G0/XG0 en el
caso de los perfiles).
NOTA 1.
�
Programas viejos generados con versiones
precedentes de Xilog3/Routolink: la modificaci�n de programas elaborados con
Xilog3/Routolink que contengan errores del tipo �Velocidades no programadas �
Herramientas no definidas � Ejes en el final de carrera - etc.� Est�
garantizada al 100% de la operatividad s�lo si est�n reeditados con el editor
de texto.
NOTA 2.
En el editor gr�fico
los comentarios del tipo �AFX_BEGIN ... AFX_END� no se deben modificar.