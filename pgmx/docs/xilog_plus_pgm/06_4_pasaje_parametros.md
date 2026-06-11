
# 6.4 P# asaje
de par�metros a subprogramas y macros
Existen tres modos para pasar una serie de
par�metros de un programa principal a un subprograma o una macro.
1) Programaci�n de
una secuencia de instrucciones PAR (hasta 256) dentro del subprograma.
Si en el momento de
llamar el subprograma (en el programa principal), el nombre de los par�metros
definidos en el interior del subprograma (que pueden estar compuestos por
n�meros o letras hasta un m�ximo de 15) no es visible, los valores introducidos
mediante la sintaxis:
PAR1=valor1
PAR2=valor2 ,.., PAR256=valor256
se pasan a los par�metros que se encuentran en
el interior del subprograma. El valor definido por PAR1 se asocia al primer
par�metro del subprograma, el que est� definido por PAR2 se asocia al segundo
valor y as� sucesivamente.
Por el contrario, si
se conocen los nombres de los par�metros del subprograma, se pueden programar
los par�metros directamente por su nombre. Por ejemplo, si en el subprograma
PUERTA.PGM se ha programado el par�metro:
PAR longitud = 3
la llamada:
S /PUERTA longitud=10
realiza el
subprograma PUERTA.PGM con el par�metro longitud regulado en 10.
Lo mismo vale para
todos los niveles de animaci�n de los subprogramas (o macros), o sea, para la
llamada de un subprograma realizada dentro de otro subprograma, etc.
V�ase tambien: instrucci�n PPAR.
2) Programaci�n de
variables globales.
Todas las variables, definidas en el programa
principal antes de la llamada de un subprograma (o de una macro), pueden ser
llamadas dentro del subprograma mismo (o de la macro). En el subprograma (o en
la macro), estas variables pueden manejarse como las variables locales (que son
las definidas internamente), con la diferencia que son inicializadas
autom�ticamente con el valor que ten�an en el programa principal. En el
subprograma, la eventual modificaci�n del valor de las variables globales es
eficaz s�lo hasta la salida del mismo.
Tambi�n en este caso, el m�todo vale para
todos los niveles de animaci�n de los subprogramas (o de las macros): una
variable local de un subprograma se hace global para todos sus subprogramas y
as� sucesivamente.
Las variables
globales al m�s alto nivel son las definidas en el archivo de las variables
ambiente. El nombre de este archivo, que es un programa que contiene s�lo
algunas definiciones de variables (v�ase instrucci�n L), debe
ser declarado en el Encabezamiento de un programa.
3)
Programaci�n de variables globales con retorno del valor al solicitante.
Un programa principal dispone de un array
(vector) de 128 valores variables visibles y modificables incluso dentro de
todos los subprogramas y macros solicitados. Esto significa que se pueden
transmitir valores desde los subprogramas o macros al programa principal. Esto
es v�lido para todos los niveles de anidamiento de subprogramas y macros.
Para leer y escribir estos valores, existen
dos nuevas funciones: HeapGet y HeapPut.
L VAR = HeapGet( 0 < �ndice <=� 128 ),
copiar la posici�n �ndice del vector en VAR;
L VAR = HeapPut( 0 < �ndice <=� 128, valor),
escribir el valor en la posici�n �ndice del
vector y copiar en VAR.
Reglas:
� �ndice y valor pueden ser expresiones;
� el array de variables se pone a cero cada
vez que se interpreta el programa ya sea de modo gr�fico o ejecut�ndolo;
� HeapGet tambi�n se puede utilizar dentro
de una expresi�n.
Por ejemplo:
En el programa principal:
�
L RAGGIO = 0
S �CALCOLARAGGIO.PGM�
L RAGGIO = HeapGet(1)
�
En el programa o macro
CALCOLARAGGIO.PGM:
�
L R =
HeapPut(1,5)
�
En el programa principal, tras la funci�n
HeapGet, RAGGIO vale 5.
�ATENCI�N!
Cuando se usa una variable global, es importante cerciorarse que haya
sido definida a un nivel superior. De lo contrario, esta variable vale 0, si se
usa en las expresiones y �no definida� si se la usa como cota.
En alternativa a la
programaci�n de un subprograma al cual se pasan algunos valores en uno de los
tres modos descritos, es posible programar una macro utilizando el pasaje de
los par�metros est�ndar para las macros.
4) Paso par�metros a macro por nombre.
Adem�s de como nombre
de subprograma o mensaje general, el par�metro N de una macro puede tambi�n
utilizarse para pasar a la macro par�metros por nombre. En dicho caso el valor
del par�metro N debe ser una lista de nombres si variables separadas por una
coma o por uno o varios espacios. Los nombres deben pertenecer a variables
utilizadas en el interior del subprograma/macro que llama.
Ejemplo:
�
xMyMacro X=.. Y=..
N=�Alfa Beta Gama Delta�
xMyMacro X=.. Y=..
N=�Alfa,Beta,Gama,Delta�������
�
En el interior de la
macro los valores de las variables pueden ser leidos y/o modificados por medio
del operador ^ aplicado a pN.
Lectura n�mero de variables pasadas
La lectura del n�mero
de variables pasadas se obtiene haciendo seguir al operador ^ por �1.
L NumVar = pN^-1 ��
En el caso del
ejemplo precedente se obtiene el n�mero 4.
Lectura valor �nica variable
La lectura del valor
de una �nica variable se obtiene haciendo seguir al operador ^ por la posici�n,
a partir de 0, de la variable solicitada. La lectura del valor de una variable
no presente en la lista produce el valor 0.
L FirstVarValue =
pN^0
Lee el valor de
�Alfa� en el ejemplo precedente.
L ThirdVarValue =
pN^2
Lee el valor de
�Gama� en el ejemplo precedente.
L FifthVarValue =
pN^4
Lee 0 en el ejemplo
precedente, ya que la quinta variable no ha sido pasada.
Modificaci�n valor �nica variable
El valor de una �nica
variable del subprograma/macro que llama puede modificarse aplicando el
operador RETV a la variable solicitada.
L Res =
RETV(pN^1,123)
La variable �Beta�
asume el valor 123.
L Res =
RETV(pN^3,456)
La variable �Delta�
asume el valor 456.
Si se utiliza la coma
como separador de los nombres en el par�metro N, tambi�n es posible omitir el
paso de una o m�s variables.
xMyMacro X=.. Y=.. N=�Alfa,Beta,Gamma,�
Falta la variable
4.
xMyMacro X=.. Y=..
N=�,Beta,,�
Faltan las
variables 1, 3 y 4.
xMyMacro X=.. Y=..
N=�Alfa,,Gamma,Delta�
Falta la variable
2.
Para verificar si se
ha omitido una variable, en el subprograma/macro llamado puede utilizarse el
operador STRCMP aplicado a la variable y a la cadena de texto sin valores.
�
IF STRCMP(pN^3,��) =
0 THEN
PRINT �La cuarta
variable no ha sido pasada�
FI
�