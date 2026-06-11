
# 9.7 Visualizaci�n bloques de PB
Una
vez definido un programa PGM se puede visualizar los diferentes bloques de PB
mediante el editor EPL. Presionar la tecla que se muestra en la figura a
continuaci�n para abrir el ambiente gr�fico.�

Una
vez entrados en EPL, es suficiente presionar la tecla de START ciclo,
seleccionada en la� figura, para
visualizar el primer ciclo programado. Para visualizar los otros ciclos,
presionar la misma tecla para que el sistema no restituya una advertencia de
fin de ciclos.

Selecciona ciclo

Posicionamiento del plano
El
programador puede visualizar un determinado ciclo seleccion�ndolo del
respectivo Combobox ubicado al lado del bot�n de START, por tanto presionando
el bot�n de �Posicionamiento del plano motorizado� (v�ase figura
siguiente).
El
sistema es capaz de restituir posibles errores sin necesidad de lanzar el
programa desde Panel M�quina.
Es
posible visualizar la preparaci�n de un plano motorizado tanto para utilizar
soportes de tipo ventosa como bornes.�
En ambos casos, para cada bloque de PB adem�s de la visualizaci�n de los
posicionamientos, ser� posible detectar posibles colisiones con el
recorrido de la herramienta.
### Control colisi�n dispositivos bloqueo-recorrido herramienta
El control se realiza presionando la tecla de
anticolisi�n (v�ase figura 25) y tiene un d�plice comportamiento:
1. Programaci�n
PB mediante ventosas: se realiza la colisi�n solamente si el recorrido
herramienta es pasante (figura 26) e interseca las ventosas. De hecho, las
ventosas son dispositivos de bloqueo ubicados debajo de la pieza.
2. Programaci�n
PB mediante bornes: existe colisi�n tambi�n para trabajos no
pasantes cuyo recorrido sin embargo interseca los bornes (figura 25).
El sistema restituye un mensaje de
advertencia en el que se especifica el color de los posibles dispositivos en
colisi�n.�
En los ejemplos en las figuras 25 y 26 los
dispositivos est�n coloreados de rojo porqu� colisionan con el recorrido
herramienta. En este caso, a diferencia de lo que sucede para la programaci�n
mediante� EPL, en la que es posible
mover los dispositivos en gr�fica, es necesaria la intervenci�n a nivel de
programa� PGM y modificar la posici�n
del dispositivo en colisi�n introduciendo una cota nueva.
�
Figura 25Control anticolisi�n bornes con elaboraci�n no pasante (color de la elaboraci�n
marr�n)
Figura 26Control anticolisi�n ventosas con elaboraci�n pasante (color de la elaboraci�n
roja)
### Control colisi�n dispositivo paleta-elementos del
plano
El
control colisi�n entre la paleta y los dispositivos de bloqueo (ventosas /
bornes) que se encuentran en el plano se realiza seg�n las mismas modalidades
del control colisi�n para los recorridos de las herramientas. El dispositivo
trasporta virutas (paleta) debe ser seleccionado en el interior del programa
mediante la instrucci�n SET DUSTPAN = 1: al abrir el ambiente EPL ser�
visualizado el recorrido herramienta y el correspondiente recorrido paleta
(recorrido color naranja de la Figura siguiente). El control se realiza
exclusivamente al presionar la tecla que se muestra en la Figura 25
### Visualizaci�n bloqueo de bornes
La
programaci�n de las PB con bornes, est� identificada por el valor 21/22 del
campo V del Encabezamiento del PGM. EPL permite visualizar el posicionamiento
de los travesa�os y de los bornes como se muestra en la siguiente figura:�
� El color celeste identifica el estado
borne ABIERTO;
� El color azul identifica el estado CERRADO;
� El color azul oscuro identifica el estado
CERRADO SOBRE LA PIEZA.
�En todo caso, se puede conocer
en cualquier momento el estrado del borne posicionando el rat�n sobre el dispositivo
(v�ase figura precedente).
En las nuevas m�quinas EASYSET SCM, un borne puede asumir un valor
nuevo (estado 3): de esta manera el borne es arrastrado por otros bornes ya que
desenganchado de la correa de tracci�n. Como se muestra en la figura siguiente,
el borne desenganchado de la correa tiene la propiedad de ser transparente.
### Sele### ctores
Durante
la programaci�n es posible asociar a cada borne un n�mero de identificaci�n de
la pieza.� Este n�mero se visualiza en
EPL de la siguiente manera:
Los
bornes Y2 de cada barra han sido programados cerrados sobre la pieza #1; los
bornes Y3 de las barras 2 y 3 retienen la pieza #2 y en fin los bornes Y3 de
las barras 3 y 4 la pieza #3.
### Programaci�n mediante ventos### as
La
programaci�n de las PB con ventosas est� identificada por el valor 12 del campo
V del Encabezamiento del programa. La visualizaci�n en EPL de una programaci�n
mediante ventosas se muestra de la siguiente manera:
Los
travesa�os y las ventosas se posicionan a las cotas seleccionadas. Las ventosas
no son representadas con los colores utilizados para los bornes ya que el
estado de las ventosas, despu�s de la fase de setup, se supone a vac�o
activado.
### Notas general### es
En
este contexto, el editor EPL se utiliza para la visualizaci�n de los
posicionamientos del plano y de los desplazamientos de la pieza programados en
el PGM. Como en los casos generales, es posible guardar una programaci�n EPL no
obstante la presencia de bloques de PB en el interior del programa. En este
caso, al cargar el programa en autom�tico del Panel M�quina, el sistema
se�aliza al usuario la presencia de ambas programaciones concediendo prioridad
a aquella guardada con el editor EPL.