
# 9.6
Ejemplo de elaboraci�n con ventosas# �
El
ejemplo a continuaci�n� muestra la
programaci�n de un plano autom�tico con dispositivos de tipo� ventosas. La programaci�n de las ventosas no
admite el bloqueo de tipo autom�tico.
### Ejemplo
1 Bloqueo semi-autom�tico
El campo V del encabezamiento del programa contiene el valor 12.
Una fase de programaci�n admitida es la preparaci�n plano. preparaci�n
de un plano motorizado est� constituido por UN SOLO bloque de
PB. La �ltima PB del bloque contiene el valor E = 1. A diferencia de los
bornes, las ventosas est�n caracterizadas solamente por dos estados: abierto
(=1) y cerrado (=0).
Figura
17: preparaci�n plano
para barra 1
Figura 18: preparaci�n plano
para barra 2
La Figura 17 muestra la programaci�n de la PB para la barra 1: en este
ejemplo se programan las ventosas Y1 y Y3. El sistema lleva la base de la
ventosa Y2, no programada, a una posici�n de fuera de dimensi�n. Come se puede
observar en las figuras, el estado de las ventosas no est� especificado: de
hecho al finalizar la fase de preparaci�n plano, el operador posiciona la pieza
sobre el plano y lo bloquea accionando los selectores ubicados en la m�quina.
Se supone que� todas las ventosas
programadas tengan el vac�o activado. La Figura 18 muestra la PB para la barra
2.
El sistema se�aliza como error los bloques de PB con campo E = 2 o E =
3.
Figura
19: PGM
La Figura 19 muestra la programaci�n de un simple programa pieza. La primera
instrucci�n describe el panel y define el tipo de bloqueo (campo V).
Las instrucciones a continuaci�n representan el bloque de PB
previamente analizado:�
- fase de preparaci�n plano (bloque de instrucciones de 2 -
3)
Finalizada la fase de set up del plano, se realiza una
elaboraci�n simple (bloque de instrucciones�
5 - 6 ).
Al final de la elaboraci�n, es posible, por ejemplo, separar el panel
tanto en X como en Y (plano motorizado tipo EASYSET).
Para tal prop�sito a�adimos una parte nueva de c�digo (v�ase figura
20) en la que las instrucciones 7 - 8 permiten realizar un corte a lo largo
de Y mientras las instrucciones 9 - 10 constituyen el bloque de PB de
separaci�n panel trabajado.
Figura
20: PGM
Figura
21: separaci�n del
panel barra 1 ventosa 3
Figura
22: separaci�n del
panel barra 2 ventosa 3
En las figuras 21 y 22 ha sido programada la separaci�n en X (cota 100
para la barra 1 y 1600 para la barra 2) y en Y (ventosa 3 de 800 a 1000 para
ambos los travesa�os).
�
Figura
23 Plano PRE -
separaci�n ������������������������������� Figura
24 Plano POST -
separaci�n
La Figura
23 muestra el posicionamiento del plano antes de la PB con E = 4; la Figura
24 muestra el posicionamiento del plano despu�s del bloque de PB de
separaci�n.