
# 9.2
Descripci�n Fas# es
### Fase 1: preparaci�n plano (E = 1)
Figura
1 PB con E = 1
La
programaci�n de un plano motorizado empieza con el primer bloqueo de PB que
tiene el campo E = 1. Como se maestra en la tabla, el campo E representa el
tipo de operaci�n que se desea realizar: la primera fase, la preparaci�n del
plano, est� evidenciada por el valor 1 y permite mover las barras y los
dispositivos en posiciones espec�ficas.
En la
Figura 1 �se indica la programaci�n de la barra 1,
especificada por el campo B = 1, al valor X = 100. Esto implica el
desplazamiento de la primera barra desde el punto corriente al punto
especificado en X.�� Contextualmente al
movimiento en X de la primera barra, se realizan los movimientos en Y de los
dispositivos 1, 2 y 3 seg�n los valores especificados en los campos Y1, Y2, Y3.
Especialmente, el dispositivo 1 es llevado a la cuota Y1 de 200, el dispositivo
2 a la cota Y2 de 300 y el dispositivo 3 a la cota Y3 de 500. En el interior
del mismo bloque, en este caso la preparaci�n del plano, se especifican todas
las barras y los dispositivos que se desean posicionar en el inicio del
programa. Cabe se�alar que el valor del campo E se declara al final de todo el
bloque: un bloque est� caracterizado por m�s l�neas, cada una de las cuales
representa una barra.� Cada l�nea del
bloque se realiza en paralelo. Al finalizar la primera fase, tras haber lanzado
el programa desde el tablero m�quina, activando el (Stara) inicio del operador,
las barras y los dispositivos ser�n posicionados simult�neamente, como
programado, en el plano.
La fase de preparaci�n del plano es
obligatoria. El sistema restituye el error si el operador omite la
programaci�n.
### Fase 2: bloqueo pieza (E = 2)
La
fase sucesiva a la preparaci�n del plano, es el bloqueo pieza que individua el
valor del campo E = 2. En esta fase se puede definir en la casilla vac�a al
lado de las cotas de los bornes (casilla Y1, Y2, Y3...), el tipo de bloqueo
deseado para cada dispositivo programado. Como se maestra en la tabla, el valor
0 permite el cierre del borne sin pieza en toma, el valor 1 permite la apertura
del borne mientras el valor 2 especifica que el cierre del borne se realiza con
la pieza en toma.
En el
interior del programa PGM, se puede especificar un bloque �nico de preparaci�n
del (E = 1) y un bloque �nico de bloqueo pieza (E = 2). En cuanto termine la
fase 2, se puede insertar un bloque nuevo de PB con valor E = 3 o iniciar la
elaboraci�n de la pieza.
CASO:
1. Especificar un
bloque de PB con E = 3 consecutivamente al bloqueo pieza, significa mover
barras o bornes que no han sido todav�a bloqueados. Solamente en este caso el
bloque de PB con E = 3 se une a la fase de bloqueo pieza
2. Introducir una
elaboraci�n al final del bloqueo de PB con E = 2, significa que la fase de
preparaci�n ha sido terminada correctamente. Despu�s de las elaboraciones
individuales, ser� posible introducir bloques de PB con E = 3 que permiten
realizar fases de posicionamiento intermedios (E = 3)
### Fase 3: posicionamiento intermedio (E = 3)
Durante
las elaboraciones de la pieza, es oportuno mover barras o dispositivos
programados con el objetivo de realizar nuevas elaboraciones. Los nuevos
posicionamientos son administrados por uno o m�s bloques de PB que tienen el
campo E = 3. Como para los otros bloques, tambi�n en esta fase, se pueden
modificar las cotas X y Y y los valores de bloqueo de los bornes. Se pueden
realizar desplazamientos de barras o bornes solamente si lo bornes est�n
abiertos o cerrados, pero en todo caso sin la pieza en toma (=1, =0). Cada
l�nea del bloque de PB con E = 3 es ejecutada por el control en paralelo;
bloques contiguos de PB son ejecutados en secuencia.
A
diferencia de la fase 1 y de la fase 2,�
la fase 3 se puede introducir en el programa m�s de una vez.
### Fase 4: desbloqueo pieza mascarada� (E = 3)
En
cuanto terminan todos los trabajos sobre la pieza, se puede introducir un nuevo
bloque de PB de PB que tiene como campo E = 3. Como para los otros bloques,
tambi�n en esta fase, se pueden modificar las cotas X y Y y los valores de
bloqueo de los bornes: se abren todos los bornes cuyo estado es = 2. La fase de
desbloqueo pieza mascarada permite al operador acceder a las plataformas de la
m�quina y quitar la pieza acabada mientras la m�quina est� trabajando en un
�rea diferente.�
La
fase de desbloqueo pieza mascarada aparece EXCLUSIVAMENTE al final del programa
PGM.
### Fase 5: desplazamiento con la pieza bloqueada� (E = 4)
Durante
los trabajos de la pieza,� es posible
separar el panel que ha sido trabajado mediante un bloque de PB con campo E =
4. Esta fase permite separar la pieza introduciendo cotas nuevas en el campo X
y/o Y. La fase de desplazamiento con la pieza bloqueada, puede ser efectuada
solamente si el estado del borne est� cerrado y la pieza en toma.
El
desplazamiento con la pieza bloqueada, como para la fase 3, puede ser
introducido en el programa m�s de una vez.�