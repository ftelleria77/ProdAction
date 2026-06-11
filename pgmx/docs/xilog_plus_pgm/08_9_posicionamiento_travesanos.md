
# 8.9 Reglas de posicionamiento de los travesa�os en
las# �reas
Con
respecto a la restauraci�n de una configuraci�n de EPL en �reas diferentes a la
de programaci�n inicial, el comportamiento de EPL sigue los criterios que se
muestran a continuaci�n.�
S�mbolos
Los travesa�os que se toman
en consideraci�n en elaboraci�n, son aquellos que se encuentran debajo del
panel, aunque parcialmente:�
������

Las
l�neas punteadas representan los ejes de origen del �rea.

Los
ejes en azul representan el origen de programaci�n.
Reglas
� Trasladando una configuraci�n de un �rea
a la otra,� los travesa�os en
elaboraci�n �son posicionados a las
mismas cotas respecto al �rea de trabajo, se�alizando si hay l�mites de final
de carrera que no se han respetado:� o:
��
Con
respecto a los travesa�os fuera de elaboraci�n, el comportamiento es el
siguiente:
� Si el Layout de EPL ha sido guardado en
un �rea en la cual el origen de programaci�n coincide con el origen del �rea
y vuelto a proponer en un �rea con las mismas caracter�sticas, los
travesa�os fuera de elaboraci�n ser�n vueltos a proponer a la misma cota a la
que estaban.
Como
se muestra en la figura:
��
� si el Layout di EPL ha sido guardado en
un �rea en la que el origen de programaci�n no coincide con el origen del
�rea y vuelto a proponer en un �rea con las mismas caracter�sticas, los
travesa�os fuera de elaboraci�n ser�n vueltos a proponer a la misma cota a la
que estaban.
Como
se muestra en la figura:
��
� si el Layout de EPL ha sido guardado en
un �rea en la que el origen de programaci�n coincide con el origen del �rea y
vuelto a proponer en un �rea en la que el origen de programaci�n no coincide
con el origen del �rea o viceversa, los travesa�os fuera de elaboraci�n
ser�n vueltos a proponer a posiciones de fuera de elaboraci�n que se encuentran
a la misma distancia del panel en el que estaban posicionados en el momento del
almacenamiento. Si estas cotas no respetan los l�mites de movimentaci�n del
travesa�o �para aquello �rea, el
usuario ser� avisado que el travesa�o ser� vuelto a posicionar dentro de estos
l�mites. o:
�
������
L�mites de movimentaci�n del travesa�o
�������� Si el �rea es doble, entonces
los l�mites mencionados arriba coinciden con los Fin de Carrera M�nimo y M�ximo
del Travesa�o.
Si el
�rea es individual, entonces los l�mites de movimentaci�n del travesa�o
dependen de la� de la combinaci�n de los
valores m�s internos entre los valores de los L�mites del �rea y los Fin de
carrera del travesa�o. Por L�mites del �rea se entiende el origen del �rea +/-
las dimensiones izquierda y derecha del travesa�o (seg�n el �rea) y la amplitud
del �rea +/- las dimensiones izquierda y derecha del travesa�o (seg�n el �rea).
Ejemplo
: