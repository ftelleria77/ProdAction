
# 4.4# Programa
m�ltiple
### 4.4.1### Editor de los
programas m�ltiples
Los programas m�ltiples permiten asociar
diversos programas de trabajo (de dos a ocho) en un �rea de la superficie
compuesta por una o varias �zonas�. La divisi�n de la superficie en zonas
depende de la configuraci�n de la m�quina; cada zona puede comprender varias
�reas. Cada programa introducido en el programa m�ltiple puede posicionarse ulteriormente
en una de las �reas que forman parte de la zona escogida previamente, o bien en
referencia a los posibles or�genes de los ejes.
El programa m�ltiple despu�s se salva en un
programa normal de trabajo, eventualmente optimizado. El nuevo programa hereda
la programaci�n de los soportes presente en los diversos programas del programa
m�ltiple; puede ser efectuado y modificado, incluida la programaci�n de los
soportes. Si los programas introducidos han sido posicionados con referencia a
un origen de los ejes, el programa que resulta puede ser efectuado en todas las
zonas de la superficie.
A) Programaci�n de la zona.
B) Areas disponibles para la zona
seleccionada.
C) Esquema de los posibles or�genes de
los ejes (seg�n el origen m�quina de la superficie).
D) Pulsadores para la composici�n y
optimizaci�n del programa m�ltiple.
E) Lista de los programas introducidos
en el programa m�ltiple.
F) Encabezamiento del programa
seleccionado en la lista de los programas.
G) Modo de programaci�n:
Con el modo de
programaci�n PIEZAS EN PARALELO seleccionado, se programa el campo REPETICIONES, con una
cantidad de repeticiones mayor que cero junto a un Offset X en el campo DistanCIA se obtiene que:
Seleccionando el
primer programa la lista se rellena autom�ticamente con un n�mero de programas
equivalente al n�mero de repeticiones determinadas m�s uno.
Los programas son
todos iguales excepto la cota programada en la columna OffsetX la cual
es cero para el primer programa y se incrementa del valor programado en el
campo DistanCIA para cada programa sucesivo al primero (Ej. Distancia, para el
segundo, Distancia*2, para el tercero y as� sucesivamente).
► Creamos un
programa m�ltiple. (Modo est�ndar)
1

Seleccionar la
zona.

2

Pulsar en el
pulsador a�adir pgm.

3

Seleccionar un
programa y pulsar el pulsador Abre para introducirlo.

Para eliminar un programa de la lista,
seleccionar el programa y pulsar en el pulsador Eliminar pgm.
Es posible crear directamente el fichero de
programaci�n de los soportes del Editor de las mesas de trabajo; el fichero se
crea autom�ticamente seg�n la programaci�n de las mesas de trabajo de cada uno
de los programas PGM a�adidos en el programa m�ltiple.
Adem�s es posible modificar varias veces el
fichero de programaci�n de los soportes antes de que haya sido introducido, en
el momento de la memorizaci�n, en el programa PGM.
Para crear o modificar, en el caso de que se
haya producido antes, el fichero de programacion de los soportes del Editor de
las mesas de trabajo hacer clic en los botones presentes en la Barra de las
funciones.
► Creamos un
programa m�ltiple. (Modo Piezas en paralelo)
1

Selecciona el
modo Piezas en paralelo

2

Programa el
n�mero de repeticiones.

3

Programa el
Offset X en el campo Distancia.

4

Seleccionar la
zona.

5

Pulsar en el
pulsador a�adir pgm.

6

Seleccionar un
programa y pulsar el pulsador Abre para introducirlo.

El programa creado contendr� una lista
rellenada con un n�mero de programas equivalente al n�mero de repeticiones
introducidas m�s uno.
Los programas a�adidos son iguales excepto
para la cota programada en el campo OffsetX la cual es cero
para el primer programa y se incrementa el valor programado en el campo DistanCIA para cada programa sucesivo al primero.
Para eliminar un programa de la lista,
seleccionar el programa y pulsar en el pulsador Eliminar pgm.
Es posible crear directamente el fichero de
programaci�n de los soportes del Editor de las mesas de trabajo; el fichero se
crea autom�ticamente seg�n la programaci�n de las mesas de trabajo de cada uno
de los programas PGM a�adidos en el programa m�ltiple.
Adem�s es posible modificar varias veces el
fichero de programaci�n de los soportes antes de que haya sido introducido, en
el momento de la memorizaci�n, en el programa PGM.
Para crear o modificar, en el caso de que se
haya producido antes, el fichero de programacion de los soportes del Editor de
las mesas de trabajo hacer clic en los botones presentes en la Barra de las
funciones.
► Como
variar la posici�n de un programa.
1

Para variar la
posici�n de un programa, pulsar en las casillas offset x, offset Y y offset Z e introducir los valores de offset
(respecto al origen de los ejes del �rea en la que el programa est�
introducido).

2

Para
posicionar el programa en un �rea de la zona seleccionada diversa del �rea de
default, pulsar en el men� de bajada y seleccionar el �rea.

Las letras min�sculas presentes en la lista de
las �reas (a, b, c, d,...) son referencias generales de la posici�n de los
topes de apoyo-pieza. Estas referencias son independientes de las zonas de la
superficie, e indican cuatro diversos posibles or�genes de los ejes, seg�n los
esquemas siguientes:
Si los programas se posicionan utilizando
dichas referencias, el programa que resulta del programa m�ltiple puede ser
efectuado tambi�n en otras zonas (ver: 4.4.3
- Ejemplos).
► Como
guardar el programa m�ltiple como programa de trabajo.
Hacer clic en
el men� Fichero/SalvaR.

El programa m�ltiple se memoriza
autom�ticamente a�n en el formato PGM realizando la relativa conversi�n.
Si se desea crear un programa PGM optimizado
es suficiente hacer clic en el bot�n oPTIMIZACIONES antes de
memorizar el programa. En el momento m�s conveniente se solicitar� el tipo de
optimaci�n deseada.
Si hay otro programa abierto en editor gr�fico
con un equipamiento diverso del programa multiple, el programa m�ltiple no
puede salvarse como programa de trabajo, porque no es posible cargar m�s de un
equipamiento en memoria para la interpretaci�n de los programas.

### 4.4.2### Subdivisi�n
de la superficie en zonas de trabajo
M�quinas
con cero central
Zona 1
�reas A/E/I/M
Zona 2
�reas B/F/J/N
Zona 3
�reas C/G/K/O
Zona 4
�reas D/H/L/P
Zona 1 e 2
�reas AB/BA/EF/FE/IJ/JI/MN/NM
Zona 3 e 4
�reas
CD/DC/GH/HG/KL/LK/OP/PO
Zonas 1 - 4
�reas
AD/DA/EH/HE/IL/LI/MP/PM
M�quinas
con cero central virtual
Zona 1
�reas AB/BA/EF/FE/IJ/JI/MN/NM
Zona 2
�reas CD/DC/GH/HG/KL/LK/OP/PO
Zonas 1 - 2
�reas
AD/DA/EH/HE/IL/LI/MP/PM
M�quinas
sin cero central
Zona 1
�reas A/E/I/M
Zona 2
�reas B/F/J/N
Zonas 1 - 2
�reas AB/BA/EF/FE/IJ/JI/MN/NM
Mesa de
vigas y ventosas
Los programas introducidos en la misma zona y
que condividen los mismos travesa�os deben ser iguales.
Para cada zona el n�mero total de los
travesa�os no puede ser superior de los f�sicamente disponibles. El n�mero de
los soportes de un dato tipo no debe superar el n�mero m�ximo especificado en el archivo de configuraci�n libsupp.cfg.
### 4.4.3
E### jemplos
Los ejemplos se refieren al caso de una
m�quina con cero central virtual.
El programa Progr1.pgm est� definido en �rea A
con dimensiones DX = 700 y DY = 500; el programa Progr2.pgm est� definido en
�rea B con dimensiones DX = 500 y DY = 500. El programa m�ltiple est�
programado en la zona 1.
Ejemplo
1
En el programa m�ltiple est�n introducidos los
siguientes programas, posicionados con referencia a los posibles or�genes de
los ejes (a, e, b, f):
Progr1 -a
Offset X = 0 Offset Y = 0 Offset Z = 0
Progr1 -e
Offset X = 0 Offset Y = 1000 Offset Z = 0
Progr2 -b
Offset X = 1500 Offset Y = 0 Offset Z = 0
Progr2 -f
Offset X = 1500 Offset Y = 1000 Offset Z = 0
Resulta el siguiente programa en formato .pgm:
H DX=1500 DY=1000
-AB
SO /"PROGR1"
BX=0 BY=0 BZ=0 FLD=a
SO
/"PROGR1" BX=0 BY=1000 BZ=0 FLD=e
SO
/"PROGR2" BX=1500 BY=0 BZ=0 FLD=b
SO
/"PROGR2" BX=1500 BY=1000 BZ=0 FLD=f
Si efectuado en �rea AB o BA (o bien EF o FE),
el programa efectuar� los subprogramas, seg�n el orden de las instrucciones SO,
en las �reas: A, E, B y F.
Si efectuado en �rea CD o DC (o bien GH o HG)
el programa efectuar� los subprogramas en las �reas: C, G, D, H.
Ejemplo
2
En el programa m�ltiple est�n introducidos los
siguientes programas, con indicaci�n de las �reas donde efectuarles (A, E, B,
F):
Progr1 -A
Offset X = 0 Offset Y = 0 Offset Z = 0
Progr1 -E
Offset X = 0 Offset Y = 0 Offset Z = 0
Progr2 -B
Offset X = 0 Offset Y = 0 Offset Z = 0
Progr2 -F
Offset X = 0 Offset Y = 0 Offset Z = 0
Resulta el siguiente programa en formato .pgm:
H DX=1500 DY=1000
-AB
SO
/"PROGR1" BX=0 BY=0 BZ=0 FLD=A
SO
/"PROGR1" BX=0 BY=0 BZ=0 FLD=E
SO
/"PROGR2" BX=0 BY=0 BZ=0 FLD=B
SO
/"PROGR2" BX=0 BY=0 BZ=0 FLD=F
Los programas introducidos en la lista del
programa m�ltiple son los mismos del ejemplo 1 pero, en este caso, el programa
.pgm que resulta no puede efectuarse en las �reas CD y DC.
Ejemplo 3 (Modo piezas en paralelo seleccionada)
En el programa m�ltiple se introduce el
programa Progr1 con tres repeticiones y distancia equivalente a 100:
Progr1 -AB Offset X = 0 Offset Y = 0 Offset Z
= 0
Progr1 -AB
Offset X = 100 Offset Y = 0 Offset Z = 0
Progr1 -AB
Offset X = 200 Offset Y = 0 Offset Z = 0
Progr1 -AB
Offset X = 300 Offset Y = 0 Offset Z = 0
Resulta el siguiente programa en formato .pgm:
H DX=1500 DY=1000
-AB
SO
/"PROGR1" BX=0 BY=0 BZ=0 FLD=AB
SET NOISO =
1
SO
/"PROGR1" BX=0 BY=0 BZ=0 FLD=AB
SO
/"PROGR1" BX=100 BY=0 BZ=0 FLD=AB
SO
/"PROGR1" BX=200 BY=0 BZ=0 FLD=AB