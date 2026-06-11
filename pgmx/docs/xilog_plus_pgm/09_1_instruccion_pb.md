
# 9.1 Instrucci�n PB
Como
descrito en el manual del Editor de Xilog Plus, se muestra el formato de la
instrucci�n XXL relativo a la PB, teniendo en cuenta que los campos relativos a
las cotas de posicionamiento barra (X) y soportes (Y1, Y2, Y3 ed Y4) aceptan
tanto los valores num�ricos como los par�metros.
Par�metros:
B
N�mero
de la barra. Este campo puede tambi�n no ser programado: si est� programado,
indica la barra a desplazar; si no est� programado, Xilog Plus elige qu�
barra desplazar al valor que se muestra en el campo X
X��������
Cota
en X a la cual debe ser posicionada la barra
Y1, Y2�
Los
valores Y1, Y2 etc. indican la posici�n en Y del primero, segundo etc. borne
o ventosa.
Para
cada borne programado indicar, en la casilla vac�a sucesiva, la condici�n de
uso del mismo (unidad) y eventualmente el n�mero de la pieza asociada
(decenas 1 - n):

0 =
borne cerrado

1 =
borne abierto

2 =
borne cerrado en bloqueo (con la pieza bloqueada)

3 =
solo para EASYSET permite desenganchar el borne de la correa de remolque en
el caso de de PB con E = 4

1x =
n�mero pieza asociada 1 m�s estado borne 0 - 2

2x =
n�mero pieza asociada 2 m�s estado borne 0 - 2

Para
dispositivos de tipo ventosa la programaci�n del estado no es significativo
E
Indica
el tipo de operaci�n que se est� realizzando en el plano de trabajo:

0 =
se ignora

1 =
operaciones de preparaci�n plano (solamente una en un programa pieza)

2 =
operaciones de bloqueo de la pieza (solamente una en un programa pieza)

3 =
operaci�n de posicionamiento intermedio (una o m�s en un programa pieza.
Importante si a la instrucci�n PB sigue una instrucci�n de movimiento).

4 =
operaci�n de desplazamiento con pieza bloqueada (una o m�s en un programa
pieza)