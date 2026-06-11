
# 9.12# Ojales
Aplicaciones
especiales prev�n la presencia de dispositivos de anclaje mec�nico de las
barras del plano motorizado (todas o solamente algunas) a la estructura fija
del plano mismo, cuya programaci�n en editor PGM y EPL de Xilog, se basa sobre
el concepto del ojal.
El
ojal representa un punto importante de la m�quina, caracterizado por una
coordenada X,� en la que una barra puede
posicionarse autom�ticamente y ser luego bloqueada con un sistema mec�nico
suplementario al freno que la vincula de manera extremadamente firme al plano
de la m�quina.
### Configura### ci�n
La
configuraci�n de los� �ojales� que se
encuentran en el plano se distribuye en la secci�n HOLEPLANE de AXIS.CFG, en
las �reas de trabajo en FIELDS.CFG y en las barras en SUPPORTS.CFG.
Remitiendo
al documento relativo a la configuraci�n, se muestran a continuaci�n, como
referencia, los par�metros que aparecen en las secciones mencionadas:
AXIS.CFG�HOLEPLANE:
Las
cotas est�n expresadas haciendo referencia al cero- par�metros (es decir al
cero de Xilog).
FIELDS.CFG:
Determina
si y seg�n qu� numeraci�n l�gica, en cada �rea de trabajo se encuentran o no
ojales para el bloqueo de las barras.
SUPPORTS.CFG
Determina
si la barra puede se enganchada en un �nico ojal.
### Programa### ci�n
Para
la programaci�n en t�rminos de editor texto PGM, remitirse al cap.5.2.5.
Para
la programaci�n en t�rminos de editor gr�fico EPL, se muestra a continuaci�n,
la pantalla de la ventana con la casilla editable prevista en el ambiente EPL
en la que puede ser especificada el n�mero de ojal en el que una barra
determinada, que seg�n la configuraci�n prev� el bloqueo sobre el ojal, debe
ser posicionada.
Se el
campo en cuesti�n no ha sido compilado, entonces el posicionamiento en X est�
�libre�; si en cambio se introduce un valor compatible con la configuraci�n de
los �ojales�, la barra en cuesti�n ser� posicionada gr�ficamente a la cota
X� calculada de manera adecuada en
relaci�n al n�mero de ojal y al �rea de trabajo.