
# 9.5 Ejemplo de elaboraci�n con bornes horizontales# �
El
ejemplo a continuaci�n� muestra la
programaci�n de un plano autom�tico con dispositivos de bornes horizontales.
### Ejemplo
1: Bloqueo autom�tico y semi-autom�tico
El campo V del encabezamiento del programa contiene el valor 61
(autom�tico) o 62 (semi-autom�tico).
La �nica fase de programaci�n admitida es la preparaci�n plano.
La preparaci�n de un plano motorizado est� constituida por UN SOLO
bloque de PB. La �ltima PB del bloque contiene el valor E = 1. A diferencia de
los bornes est�ndares, los bornes horizontales est�n caracterizados solamente
por dos estados: abierto (=1) y cerrado (=0).
Durante esta fase el sistema posiciona las barras los bornes a las
cotas definidas en el bloque de� PB. Es
necesaria la intervenci�n del operador para que los bornes sean llevados en
modalidad manual en apoyo a los topes mec�nicos de precisi�n. Para
elaboraciones con bornes horizontales deben ser garantizadas las cotas Y1, Y2 y
Y3 etc...
El sistema controla la correcta posici�n de los bornes y permite la
intervenci�n del operador sobre las plataformas y el posicionamiento de la
pieza en la m�quina.
Se realiza el mismo procedimiento para el tipo de bloqueo autom�tico y
para el bloqueo semi- autom�tico.
El sistema se�aliza como error los bloques de PB con campo E = 2 o E =
3.
�����������