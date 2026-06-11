
# 5.4 Macros usuario
### 5.4.1### Macros
usuario para trabajos para m�vil (Windows XP)
Perforaci�n uni�n con camlock - CAMLOCK
Efect�a en los
lados derecho, superior e izquierdo una perforaci�n para unir lados y base.
Grupo:
Ensamblaje

Requisitos
minimos:
� Cara izquierda y cara derecha: punta
plana di�metro 8 mm; profundidad max. 23 mm.
� Cara superior: punta plana di�metro 15
mm; profundidad 13 mm.
Par�metros:
X
Coordinada X del orificio camlock (default*:
32).
Y
Coordinada Y del orificio camlock (default*:
50).
Z
Profundidad del orificio camlock (default*:
13).
H
Coordinada X de los orificios horizontales
(default*: DZ/2).
I
Profundidad del orificio para el perno.
J
Profundidad del orificio para las clavijas
(default*: 18).
Q
Presencia del orificio central en la
superficie derecha e izquierda (1 = s�, 0 = no) (default*: 1).
D
Di�metro del orificio camlock (default*:
15).
S
Intereje entre los orificios horizontales
(default*: 32).
G
Di�metro de los orificios horizontales
(default*: 8).
*en editor grafico.
Barrera fitting - FITTING_32
Efectuar una
barrera de orificios a paso para la introducci�n de repisas. La barrera de
orificios se centra en base a la longitud del panel.
Grupo:
Ensamblaje

Requisitos
minimos:
� Cara superior.
� Punta plana di�metro 5 mm.
� Profundidad 10 mm.
Par�metros:
X
Coordinada X del primer orificio (default*:
80).
Y
Coordinada Y de los orificios (default*:
30).
Z
Profundidad de los orificios (default*: 10).
S
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 5).
*en Editor grafico.

Barrera fitting doble - FITTING_32_D
Efectuar una
barrera de orificios a paso doble para la introducci�n de repisas. La barrera
de orificios se centra en base a la longitud del panel.
Grupo:
Ensamblaje

Requisitos
minimos:
� Cara superior.
� Punta plana di�metro 5 mm.
� Profundidad 10 mm.
Par�metros:
X
Coordinada X del primer orificio (default*:
80).
Y
Coordinada Y de los orificios (default*:
30).
Z
Profundidad de los orificios (default*: 10).
S
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Toe kick - TOEKICK
Efectuar un
fresado sacando una arista.
Grupo:
Ensamblaje

Requisitos
minimos:
� Cara superior.
� Fresa T=101.
� Profundidad max. DZ+2mm.
Par�metros:
X
Longitud del fresado en X (default*: 50).
Y
Longitud del fresado en Y (default*: 50).
Z
Profundidad del fresado (default*: DZ+2).
H
Tipo de salida (1 = recta, 2 = arco)
(default*: 1).
I
Tipo de entrada (1 = recta, 2 = arco)
(default*: 1).
T
N�mero de la herramienta (default: 101).
a
Arista por sacar (0, 1, 2, 3) (default*: 0).
R
Radio de
la uni�n (default*: 0).
D
Factor de multiplicaci�n del radio
herramienta (default*: 2).
s
Tipo de acercamiento de la herramienta en
entrada y en salida (0 = en cota, 1 = en bajada) (default*: 0).
G
Sentido de recorrido (2 = horario, 3 = antihorario)
(default*: 2).
*en editor grafico.

Perforaci�n de conexi�n horizontal - UNIONE_O
Efectuar un
taladrado horizontal para orificios de conexi�n lado-base.
Grupo:
Ensamblaje

Requisitos
minimos:
� Cara izquierda y cara derecha: punta di�metro
8 mm; profundidad max. 15 mm.
Par�metros:
Z
Profundidad de los orificios (default*: 15).
I
Intereje entre los orificios centrados en DY
(default*: 32).
R
N�mero de orificios centrados en DY
(default*: 1).
x
Coordinada X de los orificios (default*:
DZ/2).
y
Coordinada Y del orificio inicial (default*:
20).
B
Di�metro de los orificios centrados en DY
(default*. 8).
r
N�mero de orificios externos por parte
(default*: 2).
D
Di�metro de los orificios externos
(default*: 8).
s
Intereje entre los orificios externos
(default*: 32).
*en editor grafico.

Perforaci�n de conexi�n vertical cara 1 - UNIONE_V
Efectuar un
taladrado vertical para orificios de conexi�n lado-base.
Grupo:
Ensamblaje

Requisitos
minimos:
� Cara superior.
� Punta di�metro 8 mm.
� Profundidad max. 12 mm.
Par�metros:
Z
Profundidad de los orificios (default*: 12).
I
Intereje entre los orificios centrados en DY
(default*: 32).
Q
Taladrado doble izquierda/derecha (1 = s�, 0
= no) (default*: 1).
R
N�mero de orificios centrados en DY
(default*: 1).
x
Coordinada X de los orificios (default*:
DZ/2).
y
Coordinada Y del orificio inicial (default*:
20).
B
Di�metro de los orificios centrados en DY
(default*: 8).
r
N�mero de orificios externos por parte
(default*: 2).
D
Di�metro de los orificios externos
(default*: 8).
s
Intereje entre los orificios externos
(default*: 32).
*en editor grafico.

Perforaci�n placas de bornes tipo 1 - BASET_1
Efectuar un
taladrado horizontal para tableros.
Grupo:
Bisagras/tableros

Requisitos
minimos:
� Cara superior.
� Punta di�metro 5 mm.
� Profundidad max. 12 mm.
Par�metros:
X
Coordinada X del centro del intereje entre
los orificios (default*: 110).
Y
Coordinada Y de los orificios (default*:
37).
Z
Profundidad de los orificios (default*: 12).
V
Velocidad de taladrado (default*: 3).
B
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Doble perforaci�n placa de bornes tipo 1 - BASET_1_D
Efectuar un
taladrado horizontal doble sim�trico para tableros.
Grupo:
Bisagras/tableros

Requisitos
minimos:
� Cara superior.
� Punta di�metro 5 mm.
� Profundidad max. 12 mm.
Par�metros:
X
Coordinada X del centro del intereje entre
los orificios (default*: 110).
Y
Coordinada Y de los orificios (default*:
37).
Z
Profundidad de los orificios (default*: 12).
V
Velocidad de taladrado (default*: 3).
B
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Triple perforaci�n placa de bornes tipo 1 - BASET_1_T
Efectuar un
taladrado horizontal triple para tableros.
Grupo:
Bisagras/placa de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 5 mm.
� Profundidad max. 12 mm.
Par�metros:
X
Coordinada X del centro del intereje entre
los orificios (default*: 110).
Y
Coordinada Y de los orificios (default*:
37).
Z
Profundidad de los orificios (default*: 12).
V
Velocidad de taladrado (default*: 3).
B
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Perforaci�n placa de bornes tipo 2 - BASET_2
Efectuar un
taladrado vertical para tableros.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 5 mm.
� Profundidad max. 12 mm.
Par�metros:
X
Coordinada X de los orificios (default*:
110).
Y
Coordinada Y del primer orificio (default*:
21).
Z
Profundidad de los orificios (default*: 12).
V
Velocidad de taladrado (default*: 3).
B
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Doble perforaci�n placa de bornes tipo 2 - BASET_2_D
Efectuar un
taladrado vertical doble sim�trico para tableros.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 5 mm.
� Profundidad max. 12 mm.
Par�metros:
X
Coordinada X de los orificios (default*:
110).
Y
Coordinada Y del primer orificio (default*:
21).
Z
Profundidad de los orificios (default*: 12).
V
Velocidad de taladrado (default*: 3).
B
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Triple perforaci�n placa de bornes tipo 2 - BASET_2_T
Efectuar un
taladrado vertical triple para tableros.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 5 mm.
� Profundidad max. 12 mm.
Par�metros:
X
Coordinada X de los orificios (default*:
110).
Y
Coordinada Y del primer orificio (default*:
21).
Z
Profundidad de los orificios (default*: 12).
V
Velocidad de taladrado (default*: 3).
B
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Perforaci�n bisagra tipo 1 - CERNIE_1
Efectuar un
taladrado para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 21.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 24).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Doble perforaci�n bisagra tipo 1 - CERNIE_1_D
Efectuar un
taladrado doble sim�trico para bisagras.
Grupo:
Bisagras/placa de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 21.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 24).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Triple perforaci�n bisagra tipo 1 - CERNIE_1_T
Efectuar un
taladrado triple para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 21.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 24).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Perforaci�n bisagra tipo 2 - CERNIE_2
Efectuar un
taladrado para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 6).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 48).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Doble perforaci�n bisagra tipo 2 - CERNIE_2_D
Efectuar un
taladrado doble sim�trico para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 6).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 48).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Triple perforaci�n bisagra tipo 2 - CERNIE_2_T
Efectuar un
taladrado triple para bisagras.
Grupo:
Bisagras/placa de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 6).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 48).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Perforaci�n bisagra tipo 3 - CERNIE_3
Efectuar un
taladrado para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 6 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
6).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 6).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 48).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Doble perforaci�n bisagra tipo 3 - CERNIE_3_D
Efectuar un
taladrado doble sim�trico para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 6 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
6).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 6).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 48).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Triple perforaci�n bisagra tipo 3 - CERNIE_3_T
Efectuar un
taladrado triple para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 6 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
6).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 6).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 48).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Perforaci�n bisagra tipo 4 - CERNIE_4
Efectuar un
taladrado para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad del orificio menor (default*:
13).
a
Di�metro del orificio menor (default*: 10).
B
Intereje entre el orificio mayor y el
orificio menor (default*: 32).
D
Di�metro del orificio mayor (default*: 35).
L
Velocidad de taladrado y del orificio menor
(default*: 3).
*en editor grafico.

Doble perforaci�n bisagra tipo 4 - CERNIE_4_D
Efectuar un
taladrado doble sim�trico para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad del orificio menor (default*:
13).
a
Di�metro del orificio menor (default*: 10).
B
Intereje entre el orificio mayor y el
orificio menor (default*: 32).
D
Di�metro del orificio mayor (default*: 35).
L
Velocidad de taladrado del orificio menor
(default*: 3).
*en editor grafico.

Triple perforaci�n bisagra tipo 4 - CERNIE_4_T
Efectuar un
taladrado triple para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad del orificio menor (default*:
13).
a
Di�metro del orificio menor (default*: 10).
B
Intereje entre el orificio mayor y el
orificio menor (default*: 32).
D
Di�metro del orificio mayor (default*: 35).
L
Velocidad de taladrado del orificio menor
(default*: 3).
*en editor grafico.

Perforaci�n bisagra tipo 5 - CERNIE_5
Efectuar un
taladrado para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 9.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 45).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Doble perforaci�n bisagra tipo 5 - CERNIE_5_D
Efectuar un
taladrado doble sim�trico para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 9.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 45).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Triple perforaci�n bisagra tipo 5 - CERNIE_5_T
Efectuar un
taladrado triple para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 10 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
10).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 9.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 45).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Taladrado bisagra tipo 6 - CERNIE_6
Efectuar un
taladrado para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 6 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
6).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 9.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 45).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Doble taladrado bisagra tipo 6 - CERNIE_6_D
Efectuar un
taladrado doble sim�trico para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 6 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
6).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 9.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 45).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Triple taladrado bisagra tipo 6 - CERNIE_6_T
Efectuar un
taladrado triple para bisagras.
Grupo:
Bisagras/placas de bornes

Requisitos
minimos:
� Cara superior.
� Punta di�metro 35 mm, profundidad max. 13
mm.
� Punta di�metro 6 mm, profundidad max. 13
mm.
Par�metros:
X
Coordinada X del centro del orificio mayor
(default*: 110).
Y
Distancia m�nima en Y entre borde del panel
y orificio mayor (default*: 4).
Z
Profundidad del orificio mayor (default*:
13).
V
Velocidad de taladrado del orificio mayor
(default*: 1).
S
Profundidad de los orificios menores
(default*: 13).
a
Di�metro de los orificios menores (default*:
6).
B
Intereje entre el orificio mayor y los
orificios menores (default*: 9.5).
D
Di�metro del orificio mayor (default*: 35).
G
Intereje entre los orificios menores
(default*: 45).
L
Velocidad de taladrado de los orificios
menores (default*: 3).
*en editor grafico.

Soporte para colgante - AGGANCIO_PP
Efectuar un
taladrado para soporte para colgantes.
Grupo:
Herraje/varios

Requisitos
minimos:
� Cara superior.
� Punta di�metro 8 mm, profundidad max. 12
mm.
Par�metros:
X
Coordinada X de los orificios (default*:
41).
Y
Distancia del borde en Y por restar al valor
DY (default*: 31).
Z
Profundidad de los orificios (default*: 12).
V
Velocidad de taladrado (default*: 3).
B
Intereje entre los orificios (default*: 32).
D
Di�metro de los orificios (default*: 8).
*en editor grafico.

Orificios para fijaci�n de foco forma circular -
FORI_FARETTO
Efectuar una
serie de orificios distribuidos en c�rculo para la fijaci�n de un foco.
Grupo:
Herraje/varios

Requisitos
minimos:
� Cara superior.
� Herramienta de default 101.
� Profundidad max. 13 mm.
Par�metros:
Z
Profundidad de los orificios (default*: 13).
H
N�mero de orificios (default*: 4).
T
N�mero de la herramienta (default: 101).
R
Coordinada Y del centro del cerco (default*:
DY/2).
D
Coordinada X del centro del cerco (default*:
DX/2).
L
Radio del cerco (default*: 25).
*en editor grafico.

Orificio para
foco - FORO_FARETTO_C
Efectuar un
punto de apoyo circular para foco.
Grupo:
Herraje/varios

Requisitos
minimos:
� Cara superior.
� Herramienta de default 101.
� Profundidad max. DZ-1 mm.
Par�metros:
X
Coordinada X del centro del punto de apoyo
(default*: DX/2).
Y
Coordinada Y del centro del punto de apoyo
(default*: DY/2).
Z
Profundidad del punto de apoyo (default*:
DZ-1).
H
Tipo de salida (1 = recta, 2 = arco)
(default*: 1).
I
Tipo de entrada (1 = recta, 2 = arco)
(default*: 2).
T
N�mero de la herramienta (default: 101).
x
Di�metro del punto de apoyo (default*: 80).
D
Factor de multiplicaci�n del radio
herramienta (default*: 2).
s
Tipo de acercamiento de la herramienta en
entrada y en salida (0 = en cota, 1 = en bajada)
G
Sentido de recorrido (2 = horario, 3 =
antihorario) (default*: 2).
L
Longitud de sobreposici�n (default*: 0).
*en editor grafico.

Orificio para foco rectangular - FORO_FARETTO_R
Efectuar un
punto de apoyo rectangular para faro.
Grupo:
Herraje/varios

Requisitos
minimos:
� Cara superior.
� Herramienta de default 101.
� Profundidad max. DZ+2 mm.
Par�metros:
X
Coordinada X del centro del punto de apoyo
(default*: DX/2).
Y
Coordinada Y del centro del punto de apoyo
(default*: DY/2).
Z
Profundidad del punto de apoyo (default*:
DZ+2).
H
Tipo de salida (1 = recta, 2 = arco)
(default*: 1).
I
Tipo de entrada (1 = recta, 2 = arco)
(default*: 2).
T
N�mero de la herramienta (default: 101).
x
Longitud del punto de apoyo (default*: 80).
y
Anchura del punto de apoyo (default*: 80).
r
Radio de uni�n (default*: 0).
D
Factor de multiplicaci�n del radio
herramienta (default*: 2).
s
Tipo de acercamiento de la herramienta en
entrada y en salida (0 = en cota, 1 = en bajada) (default*: 1).
G
Sentido de recorrido (2 = horario, 3 =
antihorario) (default*: 2).
L
Longitud de sobreposici�n (default*: 2).
*en editor grafico.

Taladrado para gu�a de los cajones - GUIDA_CASSETTI
Efectuar
orificios a paso para la gu�a de los cajones.
Grupo:
Herraje/varios

Requisitos
minimos:
� Cara superior.
� Herramienta de default punta plana
di�metro 5 mm.
� Profundidad 12 mm.
Par�metros:
X
Coordinada X de los orificios (default*:
120).
Y
Coordinada Y del orificio inicial (default*:
28).
Z
Profundidad de los orificios (default*: 12).
V
Velocidad de fresado (default*: 3).
x
Intereje entre el segundo y el tercer
orificio (default*: 128).
y
Intereje entre el tercero y el cuarto
orificio (default*: 0).
b
Intereje entre el primero y el segundo
orificio (default*: 128).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Taladrado pomo/manilla - MANIGLIA_1
Efectuar un
taladrado para manilla en puerta peque�a/panel.
Grupo:
Herraje/varios

Requisitos
minimos:
� Cara superior.
� Herramienta de default punta plana
di�metro 5 mm.
� Profundidad DZ-1.
Par�metros:
X
Coordenada X del primer orificio (default*:
(DX/2)-64).
Y
Coordinada Y de los orificios (default*:
32).
Z
Profundidad de los orificios (default*:
DZ-1).
V
Velocidad de taladrado (default*: 3).
B
Intereje entre los orificios (default*:
128).
D
Di�metro de los orificios (default*: 5).
*en editor grafico.

Punto de apoyo manilla circular - MANIGLIA_C
Efectuar un
punto de apoyo circular para manilla.
Grupo:
Herraje/varios

Requisitos
minimos:
� Cara superior.
� Herramienta de default 101.
� Profundidad max. 15 mm.
Par�metros:
X
Coordinada X del centro de la manilla
(default*: 300).
Y
Coordinada Y del centro de la manilla
(default*: 1/4DY).
Z
Profundidad de la manilla (default*: 15).
I
Distancia de sobrepasada (default*: 2).
V
Velocidad de trabajo (default*: 4).
T
N�mero de la herramienta (default: 101).
Q
Longitud de sobreposici�n (default*: 2).
D
Di�metro de la fresa (default*: 12).
s
N�mero de giros de la herramienta (default*:
18000).
L
Di�metro de la manilla (default*: 30).
*en editor grafico.

Punto de apoyo manilla rectangular - MANIGLIA_R
Efectuar un
punto de apoyo rectangular para manilla.
Grupo:
Herraje/varios

Requisitos
minimos:
� Cara superior.
� Herramienta de default 101.
� Profundidad max. 15 mm.
Par�metros:
X
Coordinada X del centro de la manilla
(default*: DX/2).
Y
Coordinada Y del centro de la manilla
(default*: 1/4 DY).
Z
Profundidad de la manilla (default*: 15).
I
Anchura de la manilla (default*: 50).
V
Velocidad de trabajo (default*: 3).
T
N�mero de la herramienta (default: 101).
D
Di�metro de la fresa (default*: 12).
s
N�mero de giros de la herramienta (default*:
18000).
L
Longitud de la manilla (default*: 80).
*en editor grafico.

Canal para respaldo direcci�n X - CANALE
Efectuar un
fresado para respaldo/fondo.
Grupo:
Macro est�ndar

Requisitos
minimos:
� Cara superior.
� Herramienta de default 101.
� Profundidad max. 4 mm.
� Se recomienda utilizar una fresa de
disco.
Par�metros:
X
Coordinada X de inicio fresado (default*:
0).
Y
Coordinada Y de inicio fresado (default*:
10).
Z
Profundidad del fresado (default*: 4).
I
Tipo de acercamiento de la herramienta en
entrada y en salida (0 = en cota, 1 = en bajada) (default*: 0).
V
Velocidad de trabajo.
S
N�mero de giros de la herramienta.
T
N�mero de la herramienta (default: 101).
r
Factor de multiplicaci�n del radio
herramienta (default*: 2).
s
Coordinada X de fin fresado (default*: DX).
l
Correcci�n herramienta (0=ninguna
correcci�n, 1=correcci�n derecha, 2=correcci�n izquierda, 3=correcci�n en
profundidad) (default*: 0).
G
Entrada/salida de la herramienta (1=s�, =no)
(default*: 1).
*en editor grafico.

Perfiladura pieza - DESPERFILADO
Efectuar un
fresado contorneando la pieza de forma rectangular.
Grupo:
Macro est�ndar

Requisitos
minimos:
� Cara superior.
� Herramienta de default 101.
� Profundidad max. DZ+2 mm.
Par�metros:
X
Coordinada X de inicio fresado (default*:
DX/2).
Y
Coordinada Y de inicio fresado (default*:
0).
Z
Profundidad del fresado (default*: DZ+2).
I
Tipo de entrada (1 = recta, 2 = arco)
(default*: 2).
V
Velocidad de trabajo.
S
N�mero de giros de la herramienta.
T
N�mero de la herramienta (default: 101).
R
Radio de uni�n (default*: 0).
a
Longitud de sobreposici�n (default*: 5).
r
Factor de multiplicaci�n del radio
herramienta (default*: 2).
D
Sentido de recorrido (2 = horario, 3 =
antihorario) (default*: 1).
s
Cota de sobremetal (default*: 0).
*en editor grafico.

### 5.4.2
Macros usuario para m�quinas Ergon
Selecci�n sub-�reas de bloqueo pieza - XSUBAREA
Esta macro se
utiliza para definir qu� sub-�rea de vac�o debe utilizarse para� bloquear la o las piezas situadas sobre la
mesa de trabajo.
Grupo:
Ergon

Par�metros:
a
�
Combinaci�n sub-�reas.

0
Todas las sub-�reas presentes.

(n)
Sub-�rea n�mero n (de 1 a 3).

12, 23,
etc.
Combinaci�n sub-�reas: sub-�reas n�mero 1 y
2, sub-�reas n�mero 2 y 3, etc.
�����������
Nota. Las sub�reas de vac�o pueden programarse tambi�n con el par�metro V de
la instrucci�n H. Si se utiliza este par�metro, cuando el programa se lanza
desde el Panel M�quina ser� posible modificar ulteriormente la selecci�n de las
sub�reas en la m�scara de los par�metros de la instrucci�n H.
Selecci�n filas de topes para sub-�reas de bloqueo pieza
- XBATTON
Esta macro se
utiliza para seleccionar la combinaci�n de filas de topes a activar para
m�quinas Ergon equipadas con mesa TV.
Grupo:
Ergon

Par�metros:
a
Sub-�reas de bloqueo pieza.

0
Todas las sub-�reas de bloqueo de la mesa de
la maquina.

1
Indica la sub-�rea de bloqueo n�mero 1.

2
Indica la sub-�rea de bloqueo n�mero 2.

3
Indica la sub-�rea de bloqueo n�mero 3.

B
Elecci�n filas de topes.

-1
No se precisa ning�n tope.

0
Todas las filas de topes.

(n)
Selecciona fila de topes n�mero n (de 1 a
4).

12, 123,
etc.
Selecciona fila de topes: n�mero 1 y 2,
n�mero 1, 2 y 3, etc.

�����������
Recordar que el sistema controla que la fila
vertical de topes (n�1 del gr�fico) no se suba, ni siquiera si se la solicita,
para la zona combinada en caso de que el campo �a� est� programado en �0�.
Ejemplo
1:
H � -AD
XBATTON a=0 B=12
En una m�quina con una sola sub-zona de vac�o
por mesa, se suben las filas de topes n�1 y n�2 de la mesa Y (AB) y solo la n�2
de la mesa V (CD), porque se supone que se bloquear� una pieza larga y la fila
de topes verticales n�1 en la mesa V ser�a un obst�culo si estuviese subida.
Ejemplo
2:
H � -AB
XBATTON a=0 B=12
En una m�quina con dos sub-zonas de vac�o para
cada mesa, se suben las filas de topes n�1 y n�2 de la mesa Y1 (A) y s�lo la
n�2 de la mesa Y2 (B), porque se supone que se bloquear� una pieza tan larga
que ocupar� toda la mesa Y y la fila de topes verticales n�1 en la mesa Y2 (B)
ser�a un obst�culo si estuviese subida.
Ejemplo
3:
H � -AB
XBATTON a=0 B= -1
En una m�quina con un n�mero cualquier de
sub�reas de vac�o para mesa, no se sube ninguna fila de topes porque el valor
del par�metro B es �-1�.
Para dar pero mayor espacio a la programaci�n
de las filas de topes para controlar casos especiales, se puede forzar la
combinaci�n de filas de topes que se desean subir en cada sub-zona de vac�o
configurada (hasta ahora como m�ximo 4 suddivididos en 2 para cada mesa). Con
dicho fin v�ase el ejemplo siguiente.
Ejemplo
4:
H � -AB
XBATTON a=1 B=12
XBATTON a=2 B=12
En una m�quina con dos sub-zonas de vac�o para
cada mesa, se suben las filas de topes n�1 y n�2 de la mesa Y1 (A) y tambi�n la
n�1 y n�2 de la mesa Y2 (B), porque el campo �a� no es �0�, es decir no se
requiere el uso simult�neo de todas las sub-zonas de vac�o.
NOTA: M�quinas con una sola sub-zona de bloqueo pieza para cada mesa, pueden
utilizar, como alternativa a esta macro, el campo T del header, con la ventaja
de que es posible modificar, en el momento de la ejecuci�n del programa en el
Cuadro M�quina, la programaci�n de las files de topes, sin tener que hacerlo en
la fase de editing. En caso de que haya varias sub-zonas de bloqueo de la pieza
para cada mesa, es obligatorio el uso de la macro puesto que, en el estado
actual de Xilog Plus, el campo T del header no permite especificar la
combinaci�n de filas de topes dentro de cada sub-zona.
Limpieza mesas con cepillo - XCLEAN
Esta macro se
usa para solicitar, dentro del programa pieza, un ciclo de limpieza de la mesa
de trabajo con o sin reserva a trav�s del pulsador correspondiente.
Grupo:
Ergon

Par�metros:
a
Petici�n reserva limpieza.

1
Precisa la reserva a trav�s de pulsador.

2
Limpieza autom�tica (sin reserva).
�����������
Posicionamiento gu�as motorizadas en el plano - XGUIDEM
Esta macro se
usa para el posicionamiento de las gu�as motorizadas (si existen).
Grupo:
Ergon

Par�metros:
Q
Cota de posicionamiento (cota en �mm� a la
que enviar la gu�a).
a
Mesa de la gu�a.

1
Mesa Y.

2
Mesa V.

3
Mesa Y e V.

s
Velocidad de posicionamiento (velocidad a la
que mover la gu�a).
�����������
Programaci�n de la posici�n gu�a horizontal - XGUIDEH
Esta macro se
usa para el posicionamiento de las gu�as motorizadas (en caso de que est�n
presentes).
Grupo:
Ergon

Par�metros:
a
Cota gu�a. Es la posici�n de la gu�a para el
step corriente programado seg�n la escala Y definida (origen y sentido).

B
Combinaci�n sub-zonas (combinaci�n sub-zonas
de vac�o interesadas en el step de posicionamiento gu�a corriente
programada).
Esta macro debe programarse tantas veces como
sea la cantidad de piezas que se desean posicionar en la mesa a lo largo de la
direcci�n Y. Cada vez que se recurre a la macro representa un step en el ciclo
de posicionamiento de la gu�a motorizada. Ello corresponde al bloqueo de una
pieza en una determinada posici�n Y en la mesa; las sub-zonas implicadas en el
bloqueo est�n definidas en el campo B.
Tomar como ejemlo el caso siguiente en el cual
se desea bloquear, en secuencia, una pieza en el par de sub-zonas 1 y 2 en la
cota Y=500, uno en la sub-zona 3 en la cota Y=2000 e uno en la sub-zona 4 en la
cota Y=3000.
Para programar esta situaci�n, ser� necesario,
despu�s de la instrucci�n de Header, la introducci�n de 3 instrucciones XGUIDEH
construidas de la siguiente manera:
H �
XGUIDEH
a=500������ �� B=12
XGUIDEH
a=2000���� �� B=3
XGUIDEH a=3000���� �� B=4
�
Se recuerda que, para el funcionamiento
correcto del ciclo de posicionamiento de la gu�a motorizada horizontal, se
requiere una programaci�n coherente de la serie de claves �$� dispuestas en la
descripci�n de la misma:
� GEN_PARK_QUOTE_GUIDE_H
� GEN_OFFSET_QUOTE_GUIDE_H
� GEN_N_MAX_POS_GUIDE_H
� GEN_SUBAREA_MIN_LIMIT
� GEN_SUBAREA_MAX_LIMIT
para su significado detallado v�ase la secci�n
especial dedicada al archivo de
configuraci�n� nci.cfg del manual
de par�metros.
Programaci�n distancia en X entre cabezas para trabajo
acoplado - XINTAX
Esta macro se
utiliza para definir a qu� distancia deben sincronizarse dos cabezas
desplazadas a lo largo de dos ejes X independientes.
Grupo:
Ergon

Par�metros:
a
Distancia en X (cota en �mm� a la cual
sincronizar las dos cabezas).
Delta entre longitud herramienta real y corregida por el
palpador - XDELTAPALPATORE
Esta macro se
usa para corregir, de un valor arbitrario, el valor del largo herramiena en el
cual debe tomarse como referencia el palpador, es decir, m�s precisamente, el
sistema de operadores din�micos del CN, dispuestos en la correcci�n de la cota
Z del cabezal-herramienta en trabajo en la pieza.
Grupo:
Ergon

Par�metros:
a
Delta largo (valor del cual difiere el largo
herramienta real respecto de la presentada en el sistema de correcci�n
run-time de la cota Z).
En caso de que el programa requiera el uso del
palpador (presencia de una instrucci�n SET TAU) y no haya ninguna instrucci�n
XDELTAPALPATORE, el valor de correcci�n en Z, asumido por el sistema de los
operadores din�micos, ser� igual al largo real de la herramienta. En cualqueir
otro caso en el que est� presente la macro en examen con asignaci�n, en su
par�metro �a�, de un valor no nulo, el arriba indicado valor de correcci�n en Z
estar� dado por la suma algebraica (es decir con signo) entre el largo real de
la herramienta y el valor de �a�.� De
esta manera es posible trabajar con la misma herramienta y el palpador
introducido, a diferentes profundiades y, en cualqueir caso, en perfiles
herramienta diferentes.
La macro debe considerarse modal en el �mbito
de la misma herramienta; por lo tanto, despu�s de un cambio herramienta, se
resetea el valor de correcci�n longitud herramienta para palpador.
Programaci�n Ciclos L�ser
- XLASERC
Permite individuar conjuntos de trabajos que se
pueden proyectar v�a laser sobre el plano de trabajo� en modo selectivo y alternativo a otros trabajos; la selecci�n de
los �ciclos� de trabajos del programa activado que el l�ser proyecta, est�
determinada por pulsadores software (interfaz en PC del proveedor del l�ser) o
de hardware (ubicados en la m�quina).
Grupo:
Ergon

�
Par�metros:
Q
N�mero ciclo (>0).
a
Tipo mando ciclo (1=inicio � 0=fin).
�����������
Los par�metros deben ser de manera obligatoria
compilados y la programaci�n de los ciclos debe ser realizada cumpliendo con
las siguientes reglas:
� un ciclo debe ser siempre definido por un
mando de inicio y por uno de fin
� est�n admitidos ciclos indentados, es
decir un ciclo �n� puede contener uno (o m�s) ciclos �m� enteros y parciales
(es decir el ciclo �m� empieza en el ciclo �n� y termina afuera de este �ltimo)
� trabajos que pertenecen al mismo ciclo
pueden no ser consecutivos, o se pueden programar m�s ciclos con el mismo
n�mero que comprenden diferentes trabajos en el programa
Seleci�n Ventosas ON/OFF -
XSELCUPS
Permite seleccionar grupos de ventosas On/Off que
pueden ser mandados en posici�n alta o baja durante la ejecuci�n del programa
pieza.
Grupo:
Ergon

�
Par�metros:
Q
Tipo de mando (vac�o=BAJADA - 0=BAJADA -
1=SUBIDA)
T
Selecci�n ventosas (vac�o=error -
val.correctos de 1 a 20 ej:3 18..)
�����������
La selecci�n de las ventosas, que debe
realizarse en el campo T, puede ser m�ltipla y se realiza como serie de n�meros
separados por un espacio en el cual cada valor va de 1 a 20 y representa el
n�mero de la ventosa (o del banco de ventosas) a seleccionar.
La macro trabaja correctamente cuando en el
archivo file Nci.cfg se encuentran configuradas las siguientes cuatro claves
(la ausencia de una de �stas est� se�alizada por un mensaje de error):
$GEN_SELCUPS_Y1 ���������� : mando para selecci�n ventosas en el plano Y1 (�rea
CD/DC)
$GEN_SELCUPS_Y2 ���������� : mando para selecci�n ventosas en el plano Y2 (�rea
AB/BA)
$GEN_CMDCUPS_UP ������� : mando de neum�tica ALTA para las ventosas seleccionadas
$GEN_CMDCUPS_DOWN : mando de neum�tica BAJA
para las ventosas seleccionadas
Movimento Planos a Velocidad
Controlada - XSLOW
Permite especificar la velocidad a la cual deben
moverse los planos de trabajo de la m�quina Ergon� en los traslados fuera de la pieza, normalmente realizadas con
velocidad y aceleraci�n m�ximas (G0).
Grupo:
Ergon

�
Par�metros:
a
Activaci�n velocidad programable (1=SI -
0=NO)
B
Velocidad programada (mm/min)
�����������
La macro es modal y como default, en caso de
par�metros �a� y �B� no programados, asume el valor cero para ambas.
El uso de dicha macro est� destinado para
particulares condiciones de trabajo en las cuales eventuales equipos de bloqueo
pieza, montadas en el plano de la m�quina, tienen una dimensi�n total que
determina colisiones no irrelevantes, para la
estanqueidad de la pieza, entre el sistema equipamiento/pieza y las tapas de
protecci�n ubicadas en PORTALE de la m�quina.
.
### 5.4.3 Macros usuario varios
Soplo - XBLOWER
Aire de refrigeraci�n y
lubricaci�n para las herramientas.
Grupo:
Macro usuario 5

�
Par�metros:
E
Habilitaci�n.
T
Lista de herramientas con el mandril
correspondiente (103,145,206,�).
���
Combinaciones de par�metros admitidas:
1.
E=no programado
T=lista herramientas

E=1
T=lista herramientas

Habilita el aire de
refrigeraci�n para las herramientas indicadas.

2.
E=0����������������
T=lista herramientas

Inhabilita el aire
de refrigeraci�n para las herramientas indicadas.

3.
E=no programado
T=no programado

E=1
T=no programado

Habilita el aire de
refrigeraci�n general.

4.
E=0����������������
T=no programado

Inhabilita el aire de refrigeraci�n general
y/o de las herramientas habilitadas.

Taladrado m�ltiple - XMULTIDRILL
Visualiza
gr�ficamente el resultado de una operaci�n de taladrado con transmisi�n angular
de varias salidas.
Esta instrucci�n
es compatible con las versiones de Xilog Plus 1.10.007 o superiores. Los
taladrados sobre la cara 1, con rotaci�n alrededor de Z, son compatibles con
las versiones de Xilog Plus 1.11.xx o superiores.
Grupo:
Macro usuario 5

�
Par�metros:
X
Coordenada X del orificio realizado con la
herramienta programada en el campo T.
Y
Coordenada Y del orificio realizado con la
herramienta programada en el campo T.
Z
Profundidad de los orificios.
R
N�mero de orificios (incluido el orificio de
origen).
x
Paso en X para las repeticiones.
y
Paso en Y para las repeticiones.
T
Herramienta.
Q
Repetici�n de los orificios seg�n el
especular en X/Y (0=No, 1=SX, 2=SY, 3=SXSY).
V
Velocidad de perforaci�n.
S
Velocidad de rotaci�n de la herramienta.
G
N�mero de pasos para descarga de virutas.
E
Posici�n de la campana de aspiraci�n (v�ase
el Ap�ndice D).
D
Cota de fuera trabajo.
a
Rotaci�n de los taladrados alrededor del eje
Z (s�lo para cara 1).

Para utilizar esta instrucci�n es necesario
configurar individualmente todas las herramientas que forman parte de la
transmisi�n angular, asignando a cada una el mismo n�mero de grupo que la
herramienta programada en el campo T. Para cada herramienta tienen que
configurarse los offset X, Y y Z detectados con la transmisi�n angular montada
sobre el mandril y con eje Vector a 0�.
La instrucci�n puede introducirse en cualquier
punto del programa.
Ejemplo:
00001�
H DX=450 DY=450 DZ=50 -A R=1 *MM
/"DEF"
00002� XMULTIDRILL X=100 Y=25 Z=10 T=101 F=4
00005�
�

Operaci�n
nula entre trabajos - XNOP
Realiza una
subida, a cota de rozamiento, entre trabajos sucesivos (llevando a cota de
rozamiento el eje Z). �til en los centros de trabajo con barras y ventosas para
evitar que las herramientas y las barras choquen al desplazarse lateralmente.
Grupo:
Macro usuario 5

�
Par�metros:
f
Valores admitidos:

(n.d.)
Realiza siempre una subida a cota de
rozamiento entre trabajos sucesivos (equivale a la instrucci�n SET NOPF45 =
-1).

0
Anula la �ltima condici�n programada (con
valores mayores o menores que 0) sin ninguna subida entre trabajos sucesivos
(equivale a la instrucci�n SET NOPF45 = 0).

23
Realiza una subida a cota de rozamiento
entre trabajos sucesivos en el lado 2 o en el lado 3 (equivale a la
instrucci�n SET NOPF45 = 23).

45
Realiza una subida a cota de rozamiento
entre trabajos sucesivos en el lado 4 o en el lado 5 (equivale a la
instrucci�n SET NOPF45 = 1).
Adquisici�n or�genes y rotaci�n - XORGACQ
Detecta los
alejamientos en X e Y y la rotaci�n alrededor del eje Z del tablero respecto al
origen del campo seleccionado. La instrucci�n efect�a dos palpaciones en el
lado X y una en el lado Y con una herramienta de tipo palpador XYZ.
Esta
instrucci�n es compatible con Xilog Plus versi�n 1.10.003 y superiores.
Grupo:
Macro usuario 5

�
Par�metros:
N
Nombres de las variables que se rellenar�n
con los valores medidos para: origen X, origen Y, rotaci�n alrededor del eje
Z.
T
Herramienta (n�mero de una herramienta de
tipo palpador).
QX1
Cota de palpaci�n del primer punto sobre el
lado X (default = DX - 10).
QX2
Cota de palpaci�n del segundo punto sobre el
lado X (default = 10).
QX3
Cota de palpaci�n sobre el lado Y (default =
DY - 10).
QZ
Cota Z de palpaci�n para todos los puntos
(default = DZ/2).

Los par�metros N y T son obligatorios. La
instrucci�n requiere la configuraci�n de una herramienta de tipo palpador XYZ.
La instrucci�n XORGACQ puede introducirse una
sola vez, despu�s del encabezamiento y antes de cualquier otra instrucci�n
operativa, y debe estar seguida por una instrucci�n ROT, a la cual deber�n
haberse pasado los valores del origen (la instrucci�n XORGACQ aplica s�lo la
translaci�n y no la rotaci�n a los trabajos que la siguen).
Ejemplo:
00001�
H DX=450 DY=450 DZ=50 -A R=1 *MM
/"DEF"
00002� XORGACQ
N="ORGX ORGY ANG"� T=180
00003� ROT X=ORGX Y=ORGY A=ANG
00004�
XB X=100 Y=50 T=101
00005�
�
xT - XT
Habilita una
herramienta.
Grupo:
Macro est�ndar

Par�metros:
G
Electromandril + herramienta.
N
Mando.
1. Si no hay ninguna herramienta programada,
todas las herramientas que pueden estar habilitadas se anulan.
2. Si hay una herramienta programada y no el
mando, la herramienta se convierte en la �nica herramienta habilitada.
Ejemplo:
XB X=1200 Y=350 Z=10 T=101
puede escribirse en la forma
XT
G=101
XB X=1200 Y=350 Z=10
3. Si est� programada la herramienta y el
mando es �+� (en editor texto guiado introducir s�lo el caracter +), la
herramienta se a�ade a la lista de herramientas habilitadas.
Ejemplo:
XB X=1200 Y=350 Z=10 T=1,2,3
puede escribirse en la forma
XT G=1
XT G=2
N=�+�
XT G=3
N=�+�
XB X=1200 Y=350 Z=10
4. La herramienta puede estar indicada con una
expresi�n.
Ejemplo:
XB X=1200 Y=350 Z=10 T=145
puede escribirse en la forma
PAR mySpindle = 1
PAR myTool = 45
XT G=mySpindle*100+myTool
XB X=1200 Y=350
Z=10
TvOnOff - XTVONOFF
Separador de
escalones.
Grupo:
Macro usuario 5

Par�metros:
E
Habilitaci�n (0 o 1).
Antes de desplazar las barras, la macro
posiciona los grupos en la posici�n de reposo.
Insertar la informaci�n siguiente, relativa al
separador de escalones, en el archivo de
configuraci�n nci.cfg:
� $GEN_GENTVON$
c�digos para habilitar el separador

� $GEN_GENTVOFF$
c�digos para inhabilitar el separador
TVSIDE - XTVSIDE
Macro modal para definir la semipieza en trabajo
despu�s de una separaci�n escalones: trasla el origen en el sentido y seg�n la
distancia programados.
Grupo:
Macro usuario 5

�
Par�metros:
D
Recorrido
del separador escalones.
N
Sentido
en X de la traslaci�n (- o +; por el contrario se confirma el origen
corriente).
Si el
par�metro D est� omitido, la distancia del recorrido es la programada en el archivo de configuraci�n fields.cfg.
El
nuevo origen es anulado por otro XTVSIDE o por la instrucci�n O/XO.
Posicionamiento
tapa de aspiraci�n del plano - XHOODPLANE
Macro modal para definir la posici�n de la tapa de
aspiraci�n del plano de trabajo montada en el montante de la m�quina y no
asociada a una determinada cabeza operadora.
Grupo:
Ergon-Tecno

Par�metros:
Q�������� Posici�n tapa:
- valor no
compilado � el sistema realiza un c�lculo autom�tico que
permite� posicionar la tapa lo m�s cerca
posible a la cara superior de la pieza (que t�cnicamente se encuentra en el
valor BZ+DZ seg�n lo programado por el Header del programa PGM)
- valor cero � la
tapa se excluye (posici�n alta)
- valor positivo �
indica la cota en mm (motorizada) o la posici�n (neum�tica) de la tapa
a��������� Ciclo de limpieza:
- valor 0
(default) � se posiciona la tapa y no se efect�a ning�n
ciclo de limpieza (movimiento eje X para Record o Y para Ergon) � quedando
baja, durante la elaboraci�n la pieza se mantiene constantemente limpio
- valor 1 � la
tapa se posiciona y se efect�a el ciclo de limpieza de la pieza, al finalizar
el cual la tapa vuelve a ser posicionada en la posici�n de exclusi�n (alta).
- valor 2 � la
tapa se posiciona y se efect�a el ciclo del �martire�, al finalizar el cual la
tapa vuelve a ser posicionada en la posici�n de exclusi�n (alta) � en cualquier
posici�n del programa PGM se posiciona la macro con solicitud ciclo �2� y
tambi�n si se solicita m�s de una vez en el programa, el ciclo ser� activado
solamente al fin del programa, con solicitud previa de descarga de la pieza (en
forma de desbloqueo de la pieza) y hold del programa.
s��������� Velocidad de ejecuci�n del ciclo:
- Default
propuesto � 25m/min
- Valor
programado � valor en m/min
Configuraci�n:
-
AXIS.CFG
La
tapa (o las tapas para Ergon) de aspiraci�n del plano debe ser ante todo
configurada en la secci�n AXIS�HOODPLANE de Xilog Plus, con el objetivo de especificar el tipo,
carrera en Z y posiciones intermedias si neum�tica:
Se
asume que la tapa, cuando se encuentra en posici�n de exclusi�n (alta), se
encuentra en su propio cero-Z. Valores positivos (ya sean estos mismos mm en el
caso de cota para tapa motorizada, o posiciones neum�ticas en el cado de tapa
neum�tica) de la posici�n de la tapa llevan la misma a bajar hacia el plano de
trabajo.
-
NCI.CFG
Configurar
las claves de Nci.cfg que identifican el ISO que debe ser generado para mandar
la tapa del plano n�1 (Y1 para Ergon o la �nica que hay para Record) y del
plano n�2 (Y2 para Ergon) desde programa PGM:
Posicionamiento
de la tapa de aspiraci�n suplementaria en la cabeza - XHOODSUPP
Macro no modal para definir la posici�n de la tapa
de aspiraci�n suplementaria de una cabeza operadora.
Grupo:
Macro SCM

Par�metros:
Q�������� Posici�n tapa:
- en mm si tapa motorizada o n�mero de
posici�n en caso de tapa neum�tica
La
macro act�a sobre la cabeza ocupada en el trabajo que sigue la misma macro y no
es modal, o sea al final del trabajo la tapa suplementaria quedar� excluida y
se solicita una nueva programaci�n de la macro para volverla a solicitar en el
trabajo sucesivo,� como se muestra en el
siguiente ejemplo:
Configuraci�n:
Los
datos de configuraci�n de la tapa en cuesti�n se encuentran en el archivo Nci.cfg
y est�n definidos por cinco claves:
1. $Hxx_SETHOOD_SUPP� (�xx�=n�cabeza)
-
contiene el c�digo ISO que manda el movimiento de la tapa suplementaria � si no
est� presenta,� entonces la cabeza �xx�
no tiene tapa suplementaria
2. $Hxx_TYPEHOOD_SUPP (�xx�=n� cabeza)
- tipo
de tapa: 1 = neum�tica (default si la clave est� ausente)
���������������������������������� ������ 2 = motorizada
3. $Hxx_NPOSHOOD_SUPP (�xx�=n� cabeza)
-
n�mero posiciones tapa si motorizada: 4 si la clave est� ausente
4. $Hxx_ANGBHOOD_SUPP (�xx�=n�cabeza)
-
posici�n angular eje B (si prisma) que permite la introducci�n de la tapa suplementaria: cualquiera si la
clave est� ausente
5. $Hxx_ANGCHOOD_SUPP (�xx�=n� cabeza)
-
posici�n angular eje C que permite la introducci�n de la tapa suplementaria:
cualquiera si la clave est� ausente
6. $Hxx_ANGLOCKHOOD_SUPP (�xx�=n� cabeza) [� vale para CN OSAI]
-
mando que permite la habilitaci�n o no del control de movimiento de los ejes
rotatorios para los cuales ha sido configurada una posici�n fija que admite la
introducci�n de la tapa suplementaria
Si la
introducci�n de la tapa suplementaria est� vinculada a una cierta posici�n del
eje C, adem�s que B (el eje B debe encontrarse siempre en la cota �0�) y esta
posici�n es diferente de aquella prevista para el cambio herramienta en el
almac�n principal de la cabeza, es necesario configurar el par�metro� �Cota angular de toma (grados):�
presente en Pheads.cfg� con el
valor de la clave �$Hxx_ANGCHOOD_SUPP� de la cabeza �xx�
correspondiente. La posici�n de estacionamiento de la cabeza por tanto no
coincide con aquella de cambio herramienta (a la cual el PLC posiciona C
pro-cambio herramienta) , sino con aquella que permite la introducci�n de la
tapa suplementaria. Adem�s, la clave �$Hxx_SETHOOD_SUPP� debe contener,
no solamente el c�digo ISO de posicionamiento de la tapa, sino tambi�n el
c�digo de movimiento del eje C en el valor de �$Hxx_ANGCHOOD_SUPP�, para
garantizar que, tras un cambio herramienta que modifica la posici�n de C, la
introducci�n de la tapa suplementaria se realice con el eje C en la posici�n
admitida. En caso de m�quinas que presentan el posicionamiento expl�cito del
eje A y B en el interior de la clave $GEN_INIT (v�ase m�quinas con
control OSAI), es oportuno que el valor para C coincida con el valor �$Hxx_ANGCHOOD_SUPP�,
para evitar movimientos in�tiles del vector.
Solamente
para las m�quinas dotadas de CN OSAI, est� previsto un mando ISO que indica al
PLC si controlar o no el movimiento de los ejes B y C en determinados momentos
del programa. En particular, si la tapa suplementaria est� introducida, dicho
mando se activa para pedir al PLC que no controle el movimiento eventual de los
ejes B y C; esto porque el CN OSAI se�aliza si se ha realizado el movimiento de
un eje controlado, tambi�n si se manda un movimiento a la cota en la cual el
eje se encuentra. El valor asignado al mando est� codificado en bit; la
posici�n de cada bit (a partir del bit 0) corresponde al peso del eje seg�n la
ordenaci�n est�ndar (ej.: bit 7 = eje B � bit 8 = eje C).
Caso
particular
Si la
tapa suplementaria es tambi�n la �nica tapa prevista en la cabeza (es decir
falta la tapa principal), en el caso de m�quinas NUM� es necesario en todo caso configurar en Pheads.cfg, para la
cabeza en cuesti�n, la tapa principal de tipo neum�tico para Prisma, es decir
deben ser configurados los siguientes par�metros en correspondencia del n�mero
de cabeza correspondiente:
Adem�s
en el archivo Nci.cfg, es necesario a�adir tambi�n la siguiente clave:
$Hxx_SETHOOD� (�xx�=n�testa)
%
$
Ejemplos
(cabeza prisma en H03):
- CN NUM:
$H03_SETHOOD_SUPP

G0
C180 ; introducir si la
tapa suplementaria admitida solamente para C a 180�
E30051=%ld
M111
$
Si en
la cabeza puede ser montada exclusivamente la tapa suplementaria, a�adir
tambi�n:
$H03_SETHOOD
%
$
- CN OSAI:
$H03_SETHOOD_SUPP
G0
C180 ; introducir si la
tapa suplementaria admitida solamente para C a 180�
#@GW88=2
#@GW95=%ld
G0
#M114
$
$H03_ANGLOCKHOOD_SUPP

#@GD51=%ld
$
$GEN_INIT
�
G79 G0 B0 C180
�
$
- COMUNE:
$H03_ANGBHOOD_SUPP
0
$
$H03_ANGCHOOD_SUPP
180
$
Frenos
- XBRAKE
Macro no modal que controla los frenos montados en
los ejes de movimentaci�n de una cabeza operadora (t�picamente los ejes
rotatorios de las cabezas prisma).
Grupo:
Macro est�ndar

Par�metros:
N
Ejes
a frenar separados por comas.
Ejemplos:
����������� xBRAKE N = �B�
����������� xBRAKE N = �C�
����������� xBRAKE N = �C,B�
Configuraci�n:
En el
archivo NCI.CFG se incorporan dos claves
espec�ficas:
$GEN_BRAKE$������������������� mando de gesti�n de los
frenos
$GEN_BRAKETIME$���������� tiempo de espera
Clavado
- XNAIL
Macro que controla la operaci�n de clavado.
Grupo:
Macro SCM

Par�metros:
X
Cota X del primer clavo a
introducir
Y
V
T
Q
R
x
y
D
Cota Y del primer clavo a
introducir
Velocidad de trabajo
N�mero de la/s cabeza/s
clavadora/s (vac�o=primera cabeza clavadora disponible)
Especularidad de la repetici�n
(si programada)
N�mero de repeticiones de
clavado
Paso en X con el cual
realizar las repeticiones (si necesarias)
Paso en Y con el cual
realizar las repeticiones (si necesarias)
Cota de fuera trabajo en Z
Configuraci�n:
Para cada
clavadora que se encuentra en la m�quina, es necesario configurar un
electromandril de �Actuador� que corresponde a 13.
Las
clavadoras pueden estar asociadas a todas las cabezas que en Pheads.cfg tengan
un n�mero comprendido entre 3 y 32 (a los que corresponden selecciones en el
PGM comprendidas entre 1 y 30).
El �Sub-tipo
de Cabeza� de cada electromandril debe compilarse con el valor que
corresponde a la clavadora en cuesti�n entre aquellas actualmente
administradas:
0 : clavadora modelo SCM (clavo expulsado mediante presi�n mec�nica)
1 : clavadora modelo SENCO (clavo expulsado mediante mando electr�nico[3])
El �Orden
0� de cada electromandril debe compilarse con los offset medidos en la
punta de la clavadora correspondiente (es decir la parte que toca la pieza).
La �Carrera
H1� de cada electromandril debe compilarse con la distancia en mil�metros
que la clavadora debe recorrer, despu�s que ha tocado la pieza, para determinar
la salida del clavo.
El valor de
este par�metro es funci�n del subtipo de clavadora seleccionado. En el caso
de� clavadora modelo SENCO, introducir
un valor negativo; esto para llevar la cabeza clavadora cerca de la pieza sin
que hunda adentro (come en el caso de las clavadoras modelo SCM). Por ejemplo,
si el valor asignado es de -1mm, la cabeza, desde la posici�n de rozamiento
alcanzada en� G0 (veloz), se coloca a
1mm desde la cara superior de la madera en�
G1 (lento) para luego realizar la expulsi�n del clavo.
La �Velocidad
de clavado est�ndar�, es decir la velocidad est�ndar a la cual la clavadora
presiona la pieza, es un dato independiente del dispositivo y, por tanto se
encuentra en la secci�n� �GEN 2�
de los par�metros m�quina de tipo AXIS.
Se puede
asociar a cada proceso de clavado, una velocidad espec�fica que sustituye
provisionalmente la est�ndar (v�ase par�metro V de la macro XNAIL).
A cada
disparo de clavo se generan en el programa ISO los c�digos previstos por la
clave $Hxx_SHOT$ contenida en el archivo NCI.CFG[4].
Test
Manuales:
Para evitar
que se produzcan situaciones en las cuales la seguridad no est� garantizada,
los �Test manuales�(v�ase Panel M�quina) tienen solamente los iconos
para la bajada/subida neum�tica de la cabeza clavadora.
Adem�s, se
encuentran dos iconos mediante los cuales el operador, informa el sistema
acerca del n�mero y de la longitud de los clavos que se encuentran en el
cargador de la clavadora[5]. A estos iconos est�n asociados dos campos: el de arriba
permite introducir un nuevo valor, el de abajo visualiza el valor corriente.
La longitud
de los clavos es de un valor comprendido entre 0 y 655.35 si la unidad de
medida es el mil�metro, un valor comprendido entre� 0 y 65.535 si la unidad de medida es la pulgada.
No se
cuentan los posibles clavos disparados en Mdi utilizando los mandos ISO espec�ficos.
Se�alizaciones diagn�sticas:
Al disparo
de cada clavo, el sistema disminuye el n�mero de clavos que se encuentran en el
cargador.
Al lanzar el
programa pieza,� se controla que el
n�mero de clavos todav�a en el cargador sea mayor o igual al n�mero de clavos
requeridos por el programa y que la longitud de los clavos no sea superior al
espesor de la pieza (DZ);� si la
comparaci�n es negativa, se emite una se�al de advertencia para el operador y
el programa pieza se suspende moment�neamente; el operador puede en todo caso
volver a iniciar la ejecuci�n del programa volviendo a presionar el pulsador Start-Programa.�
El mensaje
de advertencia queda en la pantalla hasta el final de la ejecuci�n del programa
pieza, despu�s desaparece.
Nota:
La
reejecuci�n de un programa sobre la misma pieza, por ejemplo despu�s de una
interrupci�n por parte del operador,�
puede causar �disparos� de clavos en puntos donde ya hay un clavo.
Para evitar
el �clavo sobre clavo�, cada disparo est� identificado por un n�mero de
orden seg�n el �rea de trabajo corriente; si el programa vuelve a ser
ejecutado, los clavos que tienen un n�mero de orden menor o igual al valor de
dicha variable no se toman en cuenta y por tanto no se disparan.
Ciclo
de descarga pieza - PUNLOAD
Macro que controla la operaci�n de descarga de las
piezas y de limpieza del plano en los trabajos en celdas-nesting.
Grupo:
Macro SCM

Par�metros:
A
Cota de toma de la pieza
(default=DX)
B
c
Ciclo de limpieza (0=no �
1=semiautom�tico � 2=autom�tico)
Cota de inicio limpieza
(0=desde cota pieza � 1=todo el plano)
El
par�metro A es la cota (en mm) desde la cual empezar la descarga de la
pieza. La cota se refiere al �rea seleccionada en el PGM (ej. 100mm no indica
una coordenadaX absoluta, sino� un
offset de la origen del �rea, es decir desde el tope de apoyo de la pieza). Si
el campo queda vac�o, la cota de inicio descarga coincide con el BX configurado
en el header programa.
El
par�metro B establece la modalidad de limpieza del plano despu�s de la
operaci�n de descarga:
� B=0: desactiva el ciclo de limpieza
[default]
� B=1: activa el ciclo en modalidad
semiautom�tica (al final descarga/reactivaci�n, esperar la presi�n del pulsador
start limpieza)
� B=2: activa el ciclo en modalidad
autom�tica (al final descarga/ reactivaci�n, empieza inmediatamente el ciclo de
limpieza)
El
par�metro c establece la cota desde la cual empezar el ciclo de limpieza
del plano/ �martire�(panel de soporte):
� c=0: la limpieza inicia desde la cuota de
descarga (par�metro A) [default]
� c=1: la limpieza comprende todo el plano
Nota
La
macro se activa en el punto del PGM en que ha sido programada y no al final de
la ejecuci�n.