
# 9.3
Campo V del HEADER(encabezamiento) programa
El
campo V, que se encuentra en el encabezamiento (header) del programa, permite
especificar el tipo de preparaci�n del plano. El comportamiento operativo de la
m�quina var�a en funci�n de los valores previstos, as� como los controles
realizados por Xilog Plus en la programaci�n de las PB.
### Bornes est�ndares con v�stago o p### latillo
El
estado de los bornes est�ndares es: abierto (=1), cerrado (=0) y cerrado con
pieza en toma (=2).
A
continuaci�n se muestran en detalle las caracter�sticas de cada valor del campo
V:
1. V = 20: bloqueo manual. Durante la
preparaci�n manual Xilog Plus no genera mandos de posicionamiento ni controles
de posici�n para los motores asociados con las barras y los bornes. En este
caso el operador realiza el posicionamiento de los dispositivos manualmente
2. V = 21: bloqueo autom�tico.
Durante la preparaci�n autom�tica el sistema administra las posiciones y los
controles de las barras y de los bornes.�
Despu�s de haber lanzado el programa desde el panel m�quina , el
operador presiona el pulsador de� set
up plano
a. primera presi�n: el sistema ejecuta y completa la fase de preparaci�n plano. Se
ejecuta el programa PGM hasta el bloque de PB con E� = 1. Al finalizar la operaci�n, el operador carga la pieza en la
m�quina
b. segunda presi�n: el sistema ejecuta y completa la fase de bloqueo pieza. Se
ejecuta el programa PGM hasta el bloque de PB con E = 2 y, si est� presente,
hasta el bloque de PB con E = 3 contiguo al precedente
c. tercera presi�n: el sistema bloquea los bornes en alta presi�n e inicia la ejecuci�n
del programa PMG
3. V = 22: bloqueo semiautom�tico.
Durante la preparaci�n semiautom�tica el sistema administra las posiciones y
los controles de las barras y bornes. Tras lanzar el programa desde panel� m�quina �el operador presiona la tecla de set up plano
a. primera presi�n: el sistema ejecuta y completa la fase de preparaci�n plano. Se
ejecuta el programa PGM hasta el bloque de PB con E = 1. Al finalizar la
preparaci�n, el operador carga la pieza en la m�quina y bloquea en manual la
pieza accionando los selectores ubicados en la m�quina. Los bornes se
cierran en presi�n baja. Es necesario que el bloque de PB con E = 2 sea
presente en el programa con las mismas cotas del bloque con E = 1
b. segunda presi�n: el sistema bloquea los bornes en alta presi�n e inicia la ejecuci�n
del programa PMG. Los bloques de PB con E = 3 son administrados de la misma
manera de la preparaci�n autom�tica
### Bornes horizontales para trabajos marcos
A
diferencia de los bornes est�ndares,�
los estados de los� bornes est�n
abierto (=1) y cerrado (=0). Bloques de PB con E = 2 o E = 3 generan un error
de programaci�n.
A
continuaci�n se muestran en detalle las caracter�sticas de cada valor del campo
V:
1. V = 60: bloqueo manual. Durante la
preparaci�n manual Xilog Plus no genera mandos de posicionamiento ni controles
de posici�n para los motores asociados da Xilog Plus a las barras y a los
bornes. En este caso el operador posiciona los dispositivos manualmente
2. V = 61: bloqueo autom�tico.
Durante la preparaci�n autom�tica el sistema administra el posicionamiento y
los controles de las barras y de los bornes. Despu�s de haber lanzado el
programa desde� panel m�quina, el
operador presiona el pulsador de set up plano
a. primera presi�n: el sistema ejecuta y completa la fase de preparaci�n plano. Se
ejecuta el programa PGM hasta el bloque de PB con E� = 1. En cuanto termina el operado posiciona los bornes
acerc�ndolos a los topes mec�nicos
b. segunda presi�n: el sistema controla la correcta posici�n de todos los dispositivos.
El operador carga la pieza en la m�quina y bloquea en manual la pieza
accionando los selectores ubicados en la m�quina
c. tercera presi�n: el sistema bloquea los bornes en alta presi�n e inicia a ejecutar el
programa PMG
3. V = 62: bloqueo semiautom�tico. El
sistema se comporta de la misma manera del precedente
### Ventos### as
A
diferencia de los bornes, los estados de las ventosas no son significativos.
Bloques de PB con E = 2 o E = 3 generan un error de programaci�n.
A
continuaci�n se muestran en detalle las caracter�sticas de cada valor del campo
V:
1. V = 10: bloqueo manual. Durante la
preparaci�n manual Xilog Plus no genera mandos de posicionamiento ni controles
de posici�n para los motores asociados a las barras y a las ventosas. En este
caso el operador posiciona los dispositivos manualmente
2. V = 11: bloqueo autom�tico. No
admitido. El sistema restituye el error��������������������
3. V = 12: bloqueo semiautom�tico.
Durante la preparaci�n semiautom�tica el sistema administra el posicionamiento
y los controles de las barras y ventosas. Tras haber lanzado el programa desde
el� panel m�quina, �el operador presiona el pulsador de set up
plano
a. primera presi�n: el sistema ejecuta y completa la fase de preparaci�n� plano. Se ejecuta el programa PGM hasta
el bloque de PB con E = 1. Al finalizar�
la preparaci�n, el operador carga la pieza en la m�quina y bloquea en
manual la pieza accionando los selectores ubicados en la m�quina.� Se activa el vac�o.
b. segunda presi�n: el sistema inicia la ejecuci�n del programa PMG.