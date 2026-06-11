
# 4.3
Mix de programas
El mix permite crear un archivo para
ejecutar en secuencia una lista de programas ya preparados. Las instrucciones
de un mix empiezan con la letra P y est�n formados por el nombre y el
encabezamiento de los programas que se van a ejecutar. El editor de los mix es
el mismo que el de programas en modalidad de texto.
► Como crear
un mix.
1

Para
crear un mix hay que indicar a Xilog Plus los programas a ejecutar.
Hacer
clic en el men� herramientas/Lista programas.

� o en
el bot�n.
Aparece la ventana
para abrir programas.

2

Seleccionar el programa a insertar en el mix y hacer clic en el bot�n
Abrir.

Las instrucciones del mix tambi�n se pueden
escribir directamente. En modalidad de texto libre las instrucciones se deben
escribir en el campo para introducir texto; en modalidad de texto guiado, hay
que escribir la sigla P en el campo de texto para visualizar la ventana de
introducci�n de par�metros.
Par�metros:
/
Nombre del programa.
DX
Dimensi�n
en X del tablero.
DY
Dimensi�n
en Y del tablero.
DZ
Dimensi�n
en Z del tablero.
-���������������������������
�rea de trabajo sobre la que se debe
ejecutar el programa; los valores admitidos son A, B, C, D, AB, BA, CD, DC,
AD, DA.
R
N�mero de tableros iguales a producir (m�x.
9999).
*��������� �����������
Unidad de medida; los valores admitidos son
MM (mil�metros) e IN (pulgadas); si el campo se omite, vale la unidad de
medida especificada en los par�metros de la m�quina.
/
Nombre
del archivo con los datos de equipamiento.
#
Nombre del archivo con las variables
ambiente.
BX
Distancia en X del cero del tablero con
respecto al cero del campo.
BY
Distancia
en Y del cero del tablero con respecto al cero del campo.
BZ
Dimensi�n
en Z de un posible espesor situado debajo del tablero.
(vac�a)
Campo para introducir los par�metros (PAR)
del programa.
C
Tipo de
trabajo. Valores admitidos:
0 para trabajo normal
1 para trabajo continuo
T��������
Opciones mec�nicas (v�ase �5.1 � instrucci�n
H)
V
Habilita / inhabilita el bloqueo de la pieza
y el control en la posici�n de las ventosas autom�ticas (si est�n presentes).
Equivalente al campo V de la instrucci�n�
H (v�ase �5.1 � instrucci�n H)
Ejemplo:
H DX1000 DY500 DZ20 -AB R10 *MM /DEF