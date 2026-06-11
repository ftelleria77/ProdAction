
# 4.1 Equipamiento
### 4.1.1
Editor de equipamiento
El equipamiento contiene los par�metros
de todas las herramientas disponibles en la m�quina. Xilog Plus permite crear y memorizar distintos archivos de
equipamiento, que pueden utilizarse, indicando el nombre en el encabezamiento
de un programa.
Cuando se ejecuta un programa, hay que activar
el archivo de equipamiento previsto, seleccion�ndolo en el panel de la m�quina
de Xilog Plus (v�ase el
Manual de uso del Panel de la m�quina) y verificar si las herramientas montadas
en la m�quina corresponden con las descritas en el archivo activado. El equipamiento
seleccionado se denomina equipamiento activo o corriente.
El equipamiento est�ndar de la m�quina, que
corresponde con el equipamiento actual est�ndar, es el archivo def.tlg que
debe estar siempre en la carpeta principal de equipamientos .....\XILOG PLUS\JOB.

�ATENCI�N!
Las
caracter�sticas de las herramientas montadas en la m�quina deben coincidir
siempre con las descritas en el archivo de equipamiento activo.
Un
archivo de equipamiento puede ser habilitado como equipamiento activo s�lo si
se encuentra en la carpeta principal y si su nombre no supera los 12 caracteres
(incluida la extensi�n .tlg).
Durante
la ejecuci�n de un programa, el archivo de equipamiento introducido en el
programa debe coincidir con el activo.
El editor de equipamientos presenta dos �reas
principales:
A) �rea para
seleccionar la herramienta.
B) Ventana para
editar los par�metros relativos a la herramienta seleccionada.
► Como
configurar una herramienta.
1

Hacer
clic en el cuadrado con el signo + que hay a la izquierda del nombre de un
grupo de herramientas.
La
lista se abre mostrando las herramientas. El signo + es sustituido por el
signo� -. Para cerrar la lista, hay
que volver a hacer clic en el cuadrado.

2

Seleccionar
una herramienta de la lista.
En
el �rea B aparece la lista de los par�metros de la herramienta seleccionada.
Si la herramienta es NO DECLARADO, s�lo aparece el campo �Tipo�: en este caso
hay que pulsar la tecla [ENV�O] para
confirmar.

3

Introducir
o modificar los par�metros de la herramienta en los campos de la lista que
aparece en el �rea B.
Todos
los par�metros introducidos han de ser confirmados pulsando la tecla [Env�o].

Las configuraciones de las herramientas se
pueden copiar f�cilmente arrastr�ndolas con el rat�n. Por ejemplo, arrastrando
el icono de la herramienta fija 1 sobre el icono de la herramienta fija 2, los
par�metros de la herramienta 1 se copian autom�ticamente en la tabla de
configuraci�n de la herramienta 2.
Las herramientas se dividen en dos grupos:
� Fijas. Son
las herramientas que est�n montadas sobre el cabezal perforador de la m�quina.
El archivo de equipamiento permite la descripci�n de 96 herramientas fijas,
numeradas de 1 a 96. El n�mero y las caracter�sticas de las herramientas fijas
dependen de la configuraci�n del cabezal perforador montado en la m�quina y ya
han sido programadas por el fabricante en el archivo de configuraci�n
spindles.cfg.
� Externas. �Las herramientas externas son las que se
encuentran en el almac�n de la m�quina para efectuar el cambio de herramientas.
El archivo de equipamiento permite describir 96 herramientas externas,
numeradas de E1 a E96.
Seg�n su Tipo, las herramientas (fijas y
externas) se clasifican a su vez en seis categor�as:
� herramientas tipo P (puntas de orificio);
� herramientas tipo F (fresas de vela);
� herramientas tipo D (fresas de disco);
� herramientas tipo T (palpaduras);
� herramientas tipo S (herramientas especiales);
� herramientas tipo L (patines).
Por los tipos M (cabeza con pala
transporta-virutas), N (cabeza flotante radial), O (cabeza con soplador de
aire) v�ase: Cabezas especiales Benz, en Manual de configuraci�n de las
cabezas.
La categor�a a la que pertenece una
herramienta est� indicada en el campo �Tipo�. En el caso de las
herramientas fijas, el campo Tipo se encuentra en el archivo de configuraci�n
spindles.cfg y ya ha sido programado por el fabricante de la m�quina. En el
caso de las herramientas externas, el campo Tipo, que se encuentra en el
archivo de equipamiento, debe ser programado en base a las exigencias del
operador.
Una herramienta (de 1 a 96 y de E1 a E96) se
considera configurada si se ha definido su �Tipo�. El editor de Xilog Plus considera herramientas
v�lidas (y, a continuaci�n interpreta cualquier caracter�sticas de
equipamiento) todas las que est�n configuradas.
NOTA. Xilog Plus interpreta el valor de la
velocidad en metros por minuto si es menor de 100 y en mil�metros por minuto, si
es igual o mayor de 100.
NOTA. En la tabla de equipamiento de cada herramienta se encuentra el
par�metro �Cambio herramienta camuflado no admitido� (valor de default=NO) que
act�a en cada uso de la herramienta independientemente del trabajo. De este modo
se pueden controlar tambi�n los grupos de herramientas en los cuales algunas
herramientas (o partes de herramienta) est�n destinadas al desbaste y otras al
acabado.
�ATENCI�N!
Si
se programa un tipo de herramienta, �sta se considera presente en la m�quina;
en este caso, tambi�n� hay que
introducir correctamente los dem�s par�metros.

### 4.1.2 Configuraci�n de
las herramientas
#### 4.1.2.1 Herramientas
fijas: ejemplo con puntas de orificio
Longitud
broca
Longitud de la herramienta (v�ase en la
figura: L).
Di�metro
broca
Di�metro de la herramienta (v�ase en la
figura: D).
Longitud
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: U).
Di�metro
herramienta
Di�metro de la herramienta (v�ase en la
figura: D). Debe coincidir con
el �Di�metro broca�; si vale 0, cuenta el �Di�metro broca�.
En el caso de una punta montada como herramienta
externa, representa el di�metro del orificio; si vale 0, el �Di�metro
broca� es tambi�n el di�metro del orificio.
Tipo
broca
Tipo de herramienta que se desea configurar:

S = broca con avellanador
P = broca plana
L = broca lanza
Altura
avellanador
Distancia entre el extremo inferior de la
broca y el inicio del avellanador (v�ase en la figura: A).
Coeficiente
desgaste en longitud
No habilitado.
Coeficiente
desgaste en di�metro
No habilitado.
M�x
desgaste en longitud
No habilitado.
M�x
desgaste en di�metro
No habilitado.
Longitud
correcta�����
No habilitado.
Di�metro
correcto
No habilitado.
Velocidad
m�xima
Par�metro no v�lido para el grupo perforador.
Velocidad
est�ndar
Par�metro no v�lido para el grupo perforador
Rotaci�n
m�xima
La velocidad del grupo perforador es fija
(este par�metro no es determinante).
Rotaci�n
est�ndar
La velocidad del grupo perforador es fija
(este par�metro no es determinante).
Direcci�n
de rotaci�n
La rotaci�n del grupo perforador es fija
(dejar vac�o).
Velocidad
G0/B
Velocidad de ejecuci�n del orificio.
Cambio
herramienta mascarado no admitido
Cambio de la
herramienta en el mandril principal mientras trabaja la taladradora (valor de
default=NO).
Herramienta
contrapuesta en X
N�mero de la herramienta utilizada para
taladros especulares en X.
Herramienta
contrapuesta en Y
N�mero de la herramienta utilizada para
taladros especulares en Y.
����������������������������������������������

#### 4.1.2.2 Herramientas fijas:
ejemplo con hoja/disco
Radio
Disco
Radio del disco (v�ase en la figura: R).
Corona
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: C).
Espesor
cuchilla
Espesor de la hoja (v�ase en la figura: S).
Direcci�n
de trabajo
- A
favor de avance: la cuchilla avanza empujando los dientes hacia abajo.
- Contra-avance:
la cuchilla avanza empujando los dientes hacia arriba.
La direcci�n de trabajo se programa con los
valores + y -. La direcci�n de trabajo que resulta tambi�n depende del
sentido de montaje de la cuchilla y de las condiciones mec�nicas de la
transmisi�n. V�ase: Ap�ndice L - Control de los
cortes con hoja.
Coeficiente
desgaste disco en el radio
No habilitado.
Coeficiente
desgaste disco en espesor
No habilitado.
M�x
desgaste en el radio
No habilitado.
M�x
desgaste En espesor
No habilitado.
Radio
correcto
No habilitado.
Espesor
correcto
No habilitado.
Velocidad
m�xima
Velocidad m�xima de trabajo de la
herramienta.
Velocidad
est�ndar
Velocidad de trabajo de la herramienta. No
puede ser superior a la velocidad m�xima. Este par�metro tambi�n se puede
programar durante la fase de programaci�n de la pieza.
Rotaci�n
m�xima
Revoluciones por minuto m�ximas a las que
gira la herramienta. Atenci�n:
controlar la velocidad grabada en el cabezal. Para modificar este par�metro
se necesita la introducci�n de una constrase�a: contacte el servicio de
asistencia para informaciones.
Rotaci�n
est�ndar
Revoluciones por minuto a las que gira la
herramienta durante la fase de uso. No puede ser superior a la rotaci�n
m�xima. Este par�metro se puede programar�
durante la fase de programaci�n de la pieza.
Direcci�n
de rotaci�n
Sentido de rotaci�n de la herramienta:
+rotaci�n
horaria (herramienta derecha)
- rotaci�n antihoraria (herramienta
izquierda)
Velocidad
G0/B
Velocidad de bajada en el tramo que va de la
cota de seguridad a la de trabajo. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza mediante la instrucci�n G0 o XG0.
Cambio
herramienta mascarado no admitido
Cambio de la herramienta en el mandril
principal mientras trabaja la taladradora (valor de default=NO).
Herramienta
contrapuesta en X
N�mero de la herramienta para fresados
especulares en X.
Herramienta
contrapuesta en Y����
N�mero de la herramienta para fresados
especulares en Y.

#### 4.1.2.3 Herramientas
externas
##### 4.1.2.3.1 Ejemplo de
una herramienta de tipo F cil�ndrica
Longitud
fresa
Longitud de la herramienta utilizada para
calcular la cota en Z durante la programaci�n (v�ase en la figura: L).
Di�metro
fresa
Di�metro m�ximo de la herramienta (v�ase en
la figura: D).
Longitud
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: U).
Di�metro
herramienta
Di�metro de la herramienta utilizado para
calcular la compensaci�n (v�ase en la figura: D). En este caso, es igual al di�metro fresa. Si vale 0, cuenta
el �Di�metro fresa�.
Coeficiente
desgaste en longitud
No habilitado.�
Coeficiente
desgaste en di�metro
No habilitado.
M�x
desgaste en longitud
No habilitado.
M�x
desgaste en di�metro
No habilitado.
Longitud
correcta�����
No habilitado.
Di�metro
correcto
No habilitado.
Velocidad
m�xima
Velocidad m�xima de trabajo de la
herramienta.
Velocidad
est�ndar
Velocidad de trabajo de la herramienta. No
puede ser superior a la velocidad m�xima. Este par�metro tambi�n se puede
programar en fase de programaci�n de la pieza.
Rotaci�n
m�xima
Revoluciones por minuto m�ximas a las que
gira la herramienta. Atenci�n:
controlar la velocidad grabada en el cabezal. Para modificar este par�metro
se necesita la introducci�n de una constrase�a: contacte el servicio de
asistencia para informaciones.
Rotaci�n
est�ndar
Revoluciones por minuto a las que gira la
herramienta durante la fase de uso. No puede ser superior a la rotaci�n
m�xima. Este par�metro tambi�n se puede programar durante la fase de
programaci�n de la pieza.
Direcci�n
de rotaci�n
Sentido de rotaci�n de la herramienta:
+ rotaci�n horaria (herramienta derecha)
- rotaci�n antihoraria (herramienta
izquierda)
Velocidad
G0/B
Velocidad de bajada en el tramo que va de la
cota de seguridad a la de trabajo. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza mediante la instrucci�n G0 o XG0.
Cambio
herramienta mascarado no admitido
Cambio de la herramienta en el mandril
principal mientras trabaja la taladradora (valor de default=NO).
Herramienta
contrapuesta en X����
N�mero de herramienta para fresados
especulares en X.
Herramienta
contrapuesta en Y
N�mero de herramienta para fresados
especulares en Y.
N�mero
almac�n
N�mero del almac�n donde se encuentra la
herramienta. Debe ser 0 si la m�quina tiene un solo almac�n. No habilitado
para m�quinas NWT.
Plaza
almac�n
Posici�n de la herramienta en el almac�n. No
habilitado para m�quinas NWT.
Lado
de trabajo
Cara sobre la que puede trabajar la
herramienta.
Dimensi�n
Longitud de la herramienta desde la
referencia del cono hasta el extremo opuesto.
C�digo
C�digo de reconocimiento de la herramienta
(m�ximo 11 caracteres).
Comentario
Comentario libre (m�ximo 40 caracteres).
Nota: Los par�metros que no se describen en el ejemplo no se utilizan en las
herramientas verticales

##### 4.1.2.3.2 Ejemplo de
una herramienta de tipo F perfilada
�����������
Longitud
fresa
Longitud de la herramienta utilizada para
calcular la cota en Z durante la programaci�n (v�ase en la figura: L).
Di�metro
fresa
Di�metro m�ximo de la herramienta (v�ase en
la figura: D).
Longitud
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: U).
Di�metro
herramienta
Di�metro de la herramienta utilizado para
calcular la compensaci�n (v�ase en la figura: DU). Si vale 0, cuenta el �Di�metro fresa�.
Coeficiente
desgaste en longitud
No habilitado.
Coeficiente
desgaste en di�metro
No habilitado.
M�x
desgaste en longitud
No habilitado.
M�x
desgaste en di�metro
No habilitado.
Longitud
correcta
No habilitado.
Di�metro
correcto
No habilitado.
Velocidad
m�xima
Velocidad m�xima de trabajo de la
herramienta.
Velocidad
est�ndar
Velocidad de trabajo de la herramienta. No
puede ser superior a la velocidad m�xima. Este par�metro tambi�n se puede
programar en fase de programaci�n de la pieza.
Rotaci�n
m�xima
Revoluciones por minuto m�ximas a las que
gira la herramienta. Atenci�n:
controlar la velocidad grabada en el cabezal. Para modificar este par�metro
se necesita la introducci�n de una constrase�a: contacte el servicio de
asistencia para informaciones.
Rotaci�n
est�ndar
Revoluciones por minuto a las que gira la
herramienta durante la fase de uso. No puede ser superior a la rotaci�n
m�xima. Este par�metro tambi�n se puede programar durante la fase de
programaci�n de la pieza.
Direcci�n
de rotaci�n
Sentido de rotaci�n de la herramienta:
+ rotaci�n horaria (herramienta derecha)
�-
rotaci�n antihoraria (herramienta izquierda)
Velocidad
G0/B
Velocidad de bajada en el tramo que va de la
cota de seguridad a la de trabajo. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza mediante la instrucci�n G0 o XG0.
Cambio
herramienta mascarado no admitido
Cambio de la herramienta en el mandril
principal mientras trabaja la taladradora (valor de default=NO).
Herramienta
contrapuesta en X����
N�mero de herramienta para fresados
especulares en X.
Herramienta
contrapuesta en Y
N�mero de herramienta para fresados
especulares en Y.
N�mero
almac�n
N�mero del almac�n donde se encuentra la
herramienta. Debe ser 0 si la m�quina tiene un solo almac�n. No habilitado
para m�quinas NWT.
Plaza
almac�n
Posici�n de la herramienta en el almac�n. No
habilitado para m�quinas NWT.
Lado
de trabajo
Cara sobre la que puede trabajar la
herramienta; si es igual a 0 puede trabajar todas las caras, incluso sobre
planos inclinados (para transmisi�n angular y ejes vector).
Dimensi�n
Longitud de la herramienta desde la
referencia del cono hasta el extremo opuesto (v�ase en la figura: I).
C�digo
C�digo de reconocimiento de la herramienta
(m�ximo 11 caracteres).
Comentario
Comentario libre (m�ximo 40 caracteres).
�����������������������������������������������������������������������������������������������������������
Nota: Los
par�metros que no se describen en el ejemplo no se utilizan en las herramientas
verticales.

##### 4.1.2.3.3
Ejemplo de una herramienta de tipo F montada sobre una transmisi�n angular
Longitud
fresa
Longitud de la herramienta (v�ase en la
figura: L).
Di�metro
fresa
Di�metro m�ximo de la herramienta (v�ase en
la figura: D).
Longitud
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: U).
Di�metro
herramienta
Di�metro de la herramienta utilizado para
calcular la compensaci�n (v�ase en la figura: D). Si vale 0, cuenta el �Di�metro fresa�.
Coeficiente
desgaste en longitud
No habilitado.
Coeficiente
desgaste en di�metro
No habilitado.
M�x
desgaste en longitud
No habilitado.
M�x
desgaste en di�metro
No habilitado.
Longitud
correcta
No habilitado.
Di�metro
correcto
No habilitado.
Velocidad
m�xima
Velocidad m�xima de trabajo de la
herramienta.
Velocidad
est�ndar
Velocidad de trabajo de la herramienta. No
puede ser superior a la velocidad m�xima. Este par�metro tambi�n se puede
programar en fase de programaci�n de la pieza.
Rotaci�n
m�xima
Revoluciones por minuto m�ximas a las que
gira la herramienta. Atenci�n:
controlar la velocidad grabada en el cabezal. Para modificar este par�metro
se necesita la introducci�n de una constrase�a: contacte el servicio de
asistencia para informaciones.
Rotaci�n
est�ndar
Revoluciones por minuto a las que gira la
herramienta durante la fase de uso. No puede ser superior a la rotaci�n
m�xima. Este par�metro tambi�n se puede programar durante la fase de
programaci�n de la pieza.
Direcci�n
de rotaci�n
Sentido de rotaci�n del electromandril:
+ rotaci�n horaria (herramienta derecha)
�-
rotaci�n antihoraria (herramienta izquierda)
Velocidad
G0/B
Velocidad de bajada en el tramo que va de la
cota de seguridad a la de trabajo. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza mediante la instrucci�n G0 o XG0.
Cambio
herramienta mascarado no admitido
Cambio de la herramienta en el mandril
principal mientras trabaja la taladradora (valor de default=NO).
Herramienta
contrapuesta en X����
N�mero de herramienta para fresados
especulares en X.
Herramienta
contrapuesta en Y
N�mero de herramienta para fresados
especulares en Y.
N�mero
almac�n
N�mero del almac�n donde se encuentra la
herramienta. Debe ser 0 si la m�quina tiene un solo almac�n. No habilitado
para m�quinas NWT.
Plaza
almac�n
5 � 10; posici�n de la
herramienta (las transmisiones angulares tienen una posici�n fija). No
habilitado para m�quinas NWT.
Lado
de trabajo
Cara sobre la que puede trabajar la
herramienta; si es igual a 0 puede trabajar todas las caras, incluso sobre
planos inclinados (para transmisi�n angular y ejes vector).
Dimensi�n
Longitud de la herramienta desde la
referencia del cono hasta el extremo opuesto (v�ase en la figura: I).
Offset
X
Debe ser 0.
Offset
Y
Debe ser 0.
Distancia
Z
Longitud desde la referencia del cono hasta
el eje de rotaci�n de la herramienta (v�ase en la figura: DZ).
Offset
R
�ngulo de la herramienta (con eje vector=0
si est� presente) con respecto al cero trigonom�trico (v�ase en la figura
siguiente).
Distancia
D
Distancia entre el eje de rotaci�n del
electromandril y el final del cuerpo del cabezal (v�ase en la figura: DD).
�ngulo
A (B por tipo �D�)
�ngulo entre la perpendicular de la mesa y
el eje de rotaci�n de la herramienta (v�ase en la figura: A).
N�mero
adicional
N�mero con el que se identifican varias
herramientas montadas en la misma transmisi�n angular.
�ATENCI�N!
S�lo
para el almac�n de tipo Tool Room, y si todos los campos �T3(0=NO)�
de
los lugares pares del almac�n de tipo D - Rapid est�n programados (en el
archivo de configuraci�n� storepos.cfg) con el valor �1; el valor -2 significa que esta herramienta ser� autom�ticamente
considerada de tipo 2 (dimD=2).
Por lo tanto no se descargar� autom�ticamente del RAPID.
C�digo
C�digo de reconocimiento de la herramienta
(m�ximo 11 caracteres).
Comentario
Comentario libre (m�ximo 40 caracteres).

##### 4.1.2.3.4
Ejemplo de una herramienta de tipo F montada sobre una transmisi�n angular
inclinada
Longitud
fresa
Longitud de la herramienta (v�ase en la
figura: L).
Di�metro
fresa
Di�metro m�ximo de la herramienta (v�ase en
la figura: D).
Longitud
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: U).
Di�metro
herramienta
Di�metro de la herramienta utilizado para
calcular la compensaci�n (v�ase en la figura: D). Si vale 0, cuenta el �Di�metro fresa�.
Coeficiente
desgaste en longitud
No habilitado.
Coeficiente
desgaste en di�metro
No habilitado.
M�x
desgaste en longitud
No habilitado.
M�x
desgaste en di�metro
No habilitado.
Longitud
correcta�����
No habilitado.
Di�metro
correcto
No habilitado.
Velocidad
m�xima
Velocidad m�xima de trabajo de la
herramienta.
Velocidad
est�ndar
Velocidad de trabajo de la herramienta. No
puede ser superior a la velocidad m�xima. Este par�metro tambi�n se puede
programar en fase de programaci�n de la pieza.
Rotaci�n
m�xima
Revoluciones por minuto m�ximas a las que
gira la herramienta. Atenci�n:
controlar la velocidad grabada en el cabezal. Para modificar este par�metro
se necesita la introducci�n de una constrase�a: contacte el servicio de
asistencia para informaciones.
Rotaci�n
est�ndar
Revoluciones por minuto a las que gira la
herramienta durante la fase de uso. No puede ser superior a la rotaci�n
m�xima. Este par�metro tambi�n se puede programar durante la fase de
programaci�n de la pieza.
Direcci�n
de rotaci�n
Sentido de rotaci�n de la herramienta:
+ rotaci�n horaria (herramienta derecha)
�-
rotaci�n antihoraria (herramienta izquierda)
Velocidad
G0/B
Velocidad de bajada en el tramo que va de la
cota de seguridad a la de trabajo. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza mediante la instrucci�n G0 o XG0.
Cambio
herramienta mascarado no admitido
Cambio de la herramienta en el mandril
principal mientras trabaja la taladradora (valor de default=NO).
Herramienta
contrapuesta en X
N�mero de herramienta para fresados
especulares en X.
Herramienta
contrapuesta en Y����
N�mero de herramienta para fresados
especulares en Y.
N�mero
almac�n:
N�mero del almac�n donde se encuentra la
herramienta. Debe ser 0 si la m�quina tiene un solo almac�n. No habilitado
para m�quinas NWT.
Plaza
almac�n
5 � 10; posici�n de la
herramienta (las transmisiones angulares tienen una posici�n fija). No
habilitado para m�quinas NWT.
Lado
de trabajo
Cara sobre la que puede trabajar la
herramienta; si es igual a 0 puede trabajar todas las caras, incluso sobre
planos inclinados (para transmisi�n angular y ejes vector).
Dimensi�n
Longitud de la herramienta desde la
referencia del cono hasta el extremo opuesto (v�ase en la figura: I).
Offset
X
Debe ser 0.
Offset
Y
Debe ser 0.
Distancia
Z
Longitud desde la referencia del cono hasta
el eje de
rotaci�n de la herramienta (v�ase en la
figura: DZ).
Offset
R��������
�ngulo de la herramienta (con eje vector=0
si est� presente) con respecto al cero trigonom�trico (v�ase en la figura
siguiente).
Distancia
D
Distancia entre el eje de rotaci�n del
electromandril y el final del cuerpo del cabezal (v�ase en la figura: DD).
�ngulo
A (B por tipo �D�)
�ngulo entre la perpendicular de la mesa y
el eje de rotaci�n de la herramienta (v�ase en la figura: A).
N�mero
adicional
N�mero con el que se identifican varias
herramientas montadas en la misma transmisi�n angular.
�ATENCI�N!
S�lo
para el almac�n de tipo Tool Room, y si todos los campos �T3(0=NO)�
de
los lugares pares del almac�n de tipo D - Rapid est�n programados (en el
archivo de configuraci�n� storepos.cfg) con el valor �1; el valor -2 significa que esta herramienta ser� autom�ticamente
considerada de tipo 2 (dimD=2).
Por
lo tanto no se descargar� autom�ticamente del RAPID.
C�digo
C�digo de reconocimiento de la herramienta
(m�ximo 11 caracteres).
Comentario
Comentario libre (m�ximo 40 caracteres).

##### 4.1.2.3.5
Ejemplo de una herramienta de tipo D montada sobre una transmisi�n angular
Radio
Disco
Radio del disco (v�ase en la figura: R).
Corona
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: C).
Espesor
cuchilla
Espesor de la hoja (v�ase en la figura: S).
Direcci�n
de trabajo
- A
favor de avance: la cuchilla avanza empujando los dientes hacia abajo.
- Contra-avance:
la cuchilla avanza empujando los dientes hacia arriba.
La direcci�n de trabajo se programa con los
valores + y -. La direcci�n de trabajo que resulta tambi�n depende del
sentido de montaje de la cuchilla y de las condiciones mec�nicas de la
transmisi�n. V�ase: Ap�ndice L - Control de los
cortes con hoja.
Coeficiente
desgaste disco en el radio
No habilitado.
Coeficiente
desgaste disco en espesor
No habilitado.
M�x
Desgaste en el radio
No habilitado.
M�x
desgaste en espesor
No habilitado.
Radio
correcto
No habilitado.
Espesor
correcto
No habilitado.
Velocidad
m�xima
Velocidad m�xima de trabajo de la
herramienta.
Velocidad
est�ndar
Velocidad de trabajo de la herramienta. No
puede ser superior a la velocidad m�xima. Este par�metro tambi�n se puede
programar durante la fase de programaci�n de la pieza.
Rotaci�n
m�xima
Revoluciones por minuto m�ximas a las que
gira la herramienta. Atenci�n:
controlar la velocidad grabada en el cabezal. Para modificar este par�metro
se necesita la introducci�n de una constrase�a: contacte el servicio de asistencia
para informaciones.
Rotaci�n
est�ndar
Revoluciones por minuto a las que gira la
herramienta durante la fase de uso. No puede ser superior a la rotaci�n
m�xima. Este par�metro se puede programar durante la fase de programaci�n de
la pieza.
Direcci�n
de rotaci�n
Sentido de rotaci�n de la herramienta:
+rotaci�n
horaria (herramienta derecha)
�-
rotaci�n antihoraria (herramienta izquierda)
Velocidad
G0/B
Velocidad de bajada en el tramo que va de la
cota de seguridad a la de trabajo. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza mediante la instrucci�n G0 o XG0.
Cambio
herramienta mascarado no admitido
Cambio de la herramienta en el mandril
principal mientras trabaja la taladradora (valor de default=NO).
Herramienta
contrapuesta en X
N�mero de la herramienta para fresados
especulares en X.
Herramienta
contrapuesta en Y����
N�mero de la herramienta para fresados
especulares en Y.
N�mero
almac�n
N�mero del almac�n donde se encuentra la
herramienta. Debe ser 0 si la m�quina tiene un solo almac�n. No habilitado
para m�quinas NWT.
Plaza
almac�n
5 � 10; posici�n de la
herramienta (las transmisiones angulares tienen una posici�n fija). No
habilitado para m�quinas NWT.
Lado
de trabajo
Cara sobre la que puede trabajar la
herramienta; si es igual a 0 puede trabajar todas las caras, incluso sobre
planos inclinados (para transmisi�n angular y ejes vector)..
Dimensi�n
Longitud de la herramienta desde la
referencia del cono hasta el extremo opuesto (v�ase en la figura: I).
Offset
X��������
Debe ser 0.
Offset
Y���������
Debe ser 0.
Distancia
Z
Longitud desde la referencia del cono hasta
el eje de rotaci�n de la herramienta (v�ase en la figura: DZ).
Offset
R
�ngulo de la herramienta (con eje vector=0
si est� presente) con respecto al cero trigonom�trico (v�ase en la figura
siguiente).
�ATENCI�N!
El
cero del offset R es distinto del de las herramientas de tipo F.
Distancia
D
Distancia entre el eje de rotaci�n del
electromandril y la hoja (v�ase en la figura: DD).
�ngulo
A (B por tipo �D�)
�ngulo entre la perpendicular de la mesa y
el eje de rotaci�n de la herramienta (v�ase en la figura: B).
N�mero
adicional
N�mero con el que se identifican varias
herramientas montadas en la misma transmisi�n angular.
�ATENCI�N!
S�lo
para el almac�n de tipo Tool Room, y si todos los campos �T3(0=NO)�
de
los lugares pares del almac�n de tipo D - Rapid est�n programados (en el
archivo de configuraci�n� storepos.cfg) con el valor �1; el valor -2 significa que esta herramienta ser� autom�ticamente
considerada de tipo 2 (dimD=2).
Por
lo tanto no se descargar� autom�ticamente del RAPID.
C�digo
C�digo de reconocimiento de la herramienta
(m�ximo 11 caracteres).
Comentario
Comentario libre (m�ximo 40 caracteres).

##### 4.1.2.3.6
Ejemplo de una herramienta de tipo D montada sobre transmisi�n angular
inclinada
Radio
Disco
Radio del disco (v�ase en la figura: R).
Corona
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: C).
Espesor
cuchilla
Espesor de la hoja (v�ase en la figura: S).
Direcci�n
de trabajo
- A
favor de avance: la cuchilla avanza empujando los dientes hacia abajo.
- Contra-avance:
la cuchilla avanza empujando los dientes hacia arriba.
La direcci�n de trabajo se programa con los
valores + y -. La direcci�n de trabajo que resulta tambi�n depende del
sentido de montaje de la cuchilla y de las condiciones mec�nicas de la
transmisi�n. V�ase: Ap�ndice L - Control de los
cortes con hoja.
Coeficiente
desgaste disco en el radio
No habilitado.
Coeficiente
desgaste disco en espesor
No habilitado.
M�x
desgaste� en el radio
No habilitado.
M�x
desgaste en espesor
No habilitado.
Radio
correcto
No habilitado.
Espesor
correcto������
No habilitado.
Velocidad
m�xima
Velocidad m�xima de trabajo de la
herramienta.
Velocidad
est�ndar
Velocidad de trabajo de la herramienta. No
puede ser superior a la velocidad m�xima. Este par�metro tambi�n se puede
programar durante la fase de programaci�n de la pieza.
Rotaci�n
m�xima
Revoluciones por minuto m�ximas a las que
gira la herramienta. Atenci�n:
controlar la velocidad grabada en el cabezal. Para modificar este par�metro
se necesita la introducci�n de una constrase�a: contacte el servicio de
asistencia para informaciones.
Rotaci�n
est�ndar
Revoluciones por minuto m�ximas a las que
gira la herramienta durante la fase de uso. No puede ser superior a la
rotaci�n m�xima. Este par�metro se puede programar� durante la fase de programaci�n de la pieza.
Direcci�n
de rotaci�n
Sentido de rotaci�n de la herramienta:
+��������� rotaci�n horaria (herramienta
derecha)
�-��������� rotaci�n
antihoraria (herramienta izquierda)
Velocidad
G0/B
Velocidad de bajada en el tramo que va de la
cota de seguridad a la de trabajo. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza mediante la instrucci�n G0 o XG0.
Cambio
herramienta mascarado no admitido
Cambio de la herramienta en el mandril
principal mientras trabaja la taladradora (valor de default=NO).
Herramienta
contrapuesta en X
N�mero de la herramienta para fresados
especulares en X.
Herramienta
contrapuesta en Y
N�mero de la herramienta para fresados
especulares en Y.
N�mero
almac�n
N�mero del almac�n donde se encuentra la
herramienta. Debe ser 0 si la m�quina tiene un solo almac�n. No habilitado
para m�quinas NWT.
Plaza
almac�n
5 � 10; posici�n de la
herramienta (las transmisiones angulares tienen una posici�n fija). No
habilitado para m�quinas NWT.
Lado
de trabajo
Cara sobre la que puede trabajar la
herramienta; si es igual a 0 puede trabajar todas las caras, incluso sobre
planos inclinados (para transmisi�n angular y ejes vector).
Dimensi�n
Longitud de la herramienta desde la
referencia del cono hasta el extremo opuesto (v�ase en la figura: I).
Offset
X
Debe ser 0.
Offset
Y
Debe ser 0.
Distancia
Z
Longitud desde la referencia del cono hasta
el eje de rotaci�n de la herramienta (v�ase en la figura: DZ).
Offset
R
�ngulo de la herramienta (con eje vector=0
si est� presente) con respecto al cero trigonom�trico (v�ase en la figura
siguiente).
�ATENCI�N!
El
cero del offset R es distinto del de las herramientas de tipo F.
���
Distancia
D
Distancia entre el eje de rotaci�n del
electromandril y la hoja (v�ase en la figura: DD).
�ngulo
A (B por tipo �D�)
�ngulo entre la perpendicular de la mesa y
el eje de rotaci�n de la herramienta (v�ase en la figura: B).
N�mero
adicional
N�mero con el que se identifican varias
herramientas montadas en la misma transmisi�n angular.
�ATENCI�N!
S�lo
para el almac�n de tipo Tool Room, y si todos los campos �T3(0=NO)�
de
los lugares pares del almac�n de tipo D - Rapid est�n programados (en el
archivo de configuraci�n� storepos.cfg) con el valor �1; el valor -2 significa que esta herramienta ser� autom�ticamente
considerada de tipo 2 (dimD=2).
Por
lo tanto no se descargar� autom�ticamente del RAPID.
C�digo
C�digo de reconocimiento de la herramienta
(m�ximo 11 caracteres).
Comentario
Comentario libre (m�ximo 40 caracteres).

##### 4.1.2.3.7##### Ejemplo
de una herramienta de tipo L
Longitud
pat�n
Longitud de la herramienta utilizada para
calcular la cota en Z durante la programaci�n (v�ase en la figura: L).
Di�metro
pat�n
Di�metro m�ximo de la herramienta (v�ase en
la figura: D).
Longitud
herramienta
Espesor m�ximo que la herramienta puede
trabajar (v�ase en la figura: U).
Di�metro
herramienta
Di�metro de la herramienta utilizado para
calcular la compensaci�n (v�ase en la figura: D). En este caso, es igual al di�metro pat�n. Si vale 0, cuenta el �Di�metro pat�n�.
Velocidad
m�xima
Velocidad m�xima de trabajo de la herramienta.
Velocidad
est�ndar
Velocidad de trabajo de la herramienta. No
puede ser superior a la velocidad m�xima. Este par�metro tambi�n se puede
programar en fase de programaci�n de la pieza.
Rotaci�n
m�xima
Revoluciones por minuto m�ximas a las que gira
la herramienta. Atenci�n:
controlar la velocidad grabada en el cabezal. Para modificar este par�metro
se necesita la introducci�n de una constrase�a: contacte el servicio de
asistencia para informaciones.
Rotaci�n
est�ndar
Revoluciones por minuto a las que gira la
herramienta durante la fase de uso. No puede ser superior a la rotaci�n
m�xima. Este par�metro tambi�n se puede programar durante la fase de
programaci�n de la pieza.
Direcci�n
de rotaci�n
Sentido de rotaci�n de la herramienta:
+ rotaci�n horaria (herramienta derecha)
- rotaci�n antihoraria (herramienta
izquierda)
Velocidad
G0/B
Velocidad de bajada en el tramo que va de la
cota de seguridad a la de trabajo. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza mediante la instrucci�n G0 o XG0.
Cambio
herramienta mascarado no admitido
Cambio de la herramienta en el mandril
principal mientras trabaja la taladradora (valor de default=NO).
Herramienta
contrapuesta en X����
N�mero de herramienta para fresados especulares
en X.
Herramienta
contrapuesta en Y
N�mero de herramienta para fresados
especulares en Y.
N�mero
almac�n
N�mero del almac�n donde se encuentra la
herramienta. Debe ser 0 si la m�quina tiene un solo almac�n. No habilitado
para m�quinas NWT.
Plaza
almac�n
Posici�n de la herramienta en el almac�n. No
habilitado para m�quinas NWT.
Lado
de trabajo
Cara sobre la que puede trabajar la
herramienta.
Dimensi�n
Longitud de la herramienta desde la
referencia del cono hasta el extremo opuesto.
Offset
X
V�ase: 4.1.2.3.3, 4.1.2.3.4.
Offset
Y
V�ase: 4.1.2.3.3, 4.1.2.3.4.
Distancia
Z
V�ase: 4.1.2.3.3, 4.1.2.3.4.
Offset
R
V�ase: 4.1.2.3.3, 4.1.2.3.4.
Distancia
D
V�ase: 4.1.2.3.3, 4.1.2.3.4.
�ngulo A (B por tipo �D�)
V�ase: 4.1.2.3.3, 4.1.2.3.4.
N�mero adicional
V�ase: 4.1.2.3.3, 4.1.2.3.4.
C�digo
C�digo de reconocimiento de la herramienta
(m�ximo 11 caracteres).
Comentario
Comentario libre (m�ximo 40 caracteres).
##### 4.1.2.3.8 Ejemplo de una herramienta de
tipo M
Longitud
fresa
Longitud
de la herramienta utilizada en programaci�n para calcular la cota en Z (v�ase
en la figura: L).
Di�metro
fresa
Di�metro
m�ximo de la herramienta (v�ase en la figura: D).
Longitud
�til
Espesor
m�ximo que la herramienta puede trabajar (v�ase en la figura: U).
Di�metro
�til
Di�metro
de la herramienta utilizado para calcular la compensaci�n (v�ase en la
figura: D). En este caso, es
igual al di�metro fresa. Si vale 0, cuenta el �Di�metro fresa�.
Coeficiente desgaste en longitud
No
habilitado.�
Coeficiente desgaste en di�metro
No
habilitado.�
M�x desgaste en longitud
No
habilitado.�
M�x desgaste en di�metro
No
habilitado.�
Longitud correcta
No
habilitado.�
Di�metro correcto
No
habilitado.�
Velocidad m�xima
Velocidad
m�xima de trabajo de la herramienta.
Velocidad est�ndar
Velocidad
de trabajo de la herramienta. No puede ser superior a la velocidad m�xima.
Este par�metro tambi�n se puede programar en fase de programaci�n de la
pieza.
Rotaci�n m�xima
Revoluciones
por minuto m�ximas a las que gira la herramienta �Atenci�n! Controlar la velocidad grabada en el cabezal. Para
modificar este par�metro se necesita la introducci�n de una contrase�a:
contacte el servicio de asistencia para informaciones
Rotaci�n est�ndar
Revoluciones
por minuto a las que gira la herramienta durante la fase de uso. No puede ser
superior a la rotaci�n m�xima. Este par�metro tambi�n se puede programar
durante la fase de programaci�n de la pieza.
Direcci�n de rotaci�n
Sentido
de rotaci�n de la herramienta:
+
rotaci�n horaria (herramienta derecha)
-
rotaci�n antihoraria (herramienta izquierda)
Velocidad G0/B
Velocidad
de bajada en el tramo que va de la cota de seguridad a la de trabajo. Este
par�metro tambi�n se puede programar durante la fase de programaci�n de la
pieza mediante la instrucci�n G0 o XG0.
Cambio herramienta mascarado no admitido
Cambio
herramienta mascarado quiere
decir anticipar el cambio herramienta en caso de trabajos con mandriles
diferentes
1 =
cambio herramienta mascarado no admitido
0
cambio herramienta mascarado admitido
Herramienta contrapuesta en X����
N�mero
de herramienta para fresados especulares en X.
Herramienta contrapuesta en Y
N�mero
de herramienta para fresados especulares en Y.
N�mero almac�n
N�mero
del almac�n donde se encuentra la herramienta. Debe ser 0 si la m�quina tiene
un solo almac�n. No habilitado para m�quinas NWT.
Plaza almac�n
Posici�n
de la herramienta en el almac�n. No habilitado para m�quinas NWT.
Lado de trabajo
Cara
sobre la que puede trabajar la herramienta; si est� en 0 puede trabajar todas
las caras y tambi�n planos inclinados (para transmisiones angulares y ejes
vector).
Dimensi�n
Longitud
de la herramienta desde la referencia del cono hasta el extremo opuesto.
Gesti�n
autom�tica
de la
longitud
1=indica
la predisposici�n de la herramienta para la medici�n autom�tica de la
longitud (Nota: el dispositivo de medici�n debe necesariamente estar
presente).
�ngulo
perno pala
�ngulo
formado por el perno de conexi�n con el mandril y la punta de la pala V�ase
Figura.
Radio pala
Distancia
entre el centro herramienta y la punta pala. V�ase Figura.
C�digo
C�digo
de reconocimiento de la herramienta (m�ximo 11 caracteres).
Comentario
Comentario
libre (m�ximo 40 caracteres).
##### 4.1.2.3.9 Par�metros General##### es
N�mero
pernos de referencia
Indica
el n�mero de pernos de referencia que se encuentran en la herramienta y se
utiliza para controlar si la herramienta puede ser cargada o no en
determinados cabezales. Si el valor del par�metro es �0�, entonces no se
asumen l�mites para la carga de la herramienta.
Gesti�n
autom�tica de la longitud
1=
indica la predisposici�n de la herramienta para la medici�n autom�tica de la
longitud (Nota: el dispositivo de medici�n debe necesariamente estar
presente).

#### 4.1.2.4 Notas
Velocidad G0/B.
Cuando la herramienta se utiliza para
perforar, corresponde a la velocidad por defecto a la que se realiza el
orificio (s�lo si no se han programado instrucciones B y BR en el campo V). Si
la herramienta se utiliza para fresar, corresponde a la velocidad de entrada en
la madera (s�lo si es superior a cero, si no lo es la velocidad de entrada es
igual a la de avance). La velocidad de entrada tambi�n se puede programar en el
campo V de la instrucci�n G0/G0R.
Velocidad m�xima.
Vale s�lo si la herramienta se utiliza para fresar.
Si es superior a cero corresponde a la velocidad m�xima de avance de la
herramienta.
Velocidad est�ndar.
Vale s�lo si la herramienta se utiliza para
fresar. Si es superior a cero corresponde a la velocidad est�ndar de avance de
la herramienta (si no est� programada en el campo V de la G0). No debe superar
la �Velocidad m�xima�.
NOTA. Estos campos
se utilizan s�lo si su valor es superior a cero. Si lo es, funcionan del
siguiente modo:
� Taladrado sin par�metro V: se utiliza el
valor menor entre el de �Velocidad G0/B� y el de �Velocidad m�xima�.
� Taladrado con par�metro V: se utiliza el
valor menor entre el de V y el de �Velocidad m�xima�.
� Fresado sin par�metro V en la instrucci�n
G0/G0R: para la entrada en la pieza se utiliza el valor menor entre el de �Velocidad
G0/B� y el de �Velocidad m�xima�.
� Fresado sin par�metro V en las
instrucciones sucesivas a la G0/G0R: para el avance se utiliza el valor menor
entre el de �Velocidad est�ndar� y el de �Velocidad m�xima�.
� Fresado con par�metro V en la instrucci�n
G0/G0R: para la entrada en la pieza se utiliza el valor menor entre el de V y
el de �Velocidad m�xima�.
� Fresado con par�metro V en las
instrucciones sucesivas a la G0/G0R: para el avance se utiliza el valor menor
entre el de V y el de �Velocidad m�xima�.
Rotaci�n m�xima. En
el caso de herramientas fijas no es necesario programarla. Para las
herramientas externas, corresponde a la velocidad de rotaci�n del mandril
programada durante la fase de perforaci�n o fresado s�lo si la velocidad
programada en el campo S es superior.
#### 4.1.2.5
Grupo Hoja
El grupo Hoja se puede configurar en cualquier
posici�n del archivo de configuraci�n� pheads.cfg comprendida entre 4 y 11,
escribiendo 6 en el campo �Actuador�. La configuraci�n de la herramienta
montada en el grupo Hoja es la misma que la de las herramientas externas.
Ninguna Rotaci�n
En elarchivo de configuraci�n pheads.cfg, el campo �Fin de carrera+
(positivo) del Vector (grados)� relativo al grupo Hoja debe valer -1. La
herramienta asociada al grupo puede estar comprendida entre E1 y E96.
Rotaci�n neum�tica
En el archivo de configuraci�n pheads.cfg, el campo �Fin de carrera+ (positivo)
del Vector (grados)� relativo al grupo Hoja debe valer -90; hay que configurar
dos herramientas diferentes seleccionadas entre E1 y E96 con la convenci�n de
que las herramientas impares hagan girar el grupo, las pares no. Todas las
herramientas deben tener el mismo n�mero de grupo; el par�metro �Offset R� del
equipamiento debe configurarse correctamente (ver: ejemplos de configuraci�n de
las herramientas en cabezas de contramarcha angular).
Rotaci�n motorizada (Vector)
En el archivo de configuraci�n pheads.cfg, el campo �Fin de carrera+ (positivo)
del Vector (grados)� relativo al grupo Hoja debe ser igual o mayor que cero. La
herramienta asociada al grupo puede estar comprendida entre E1 y E96.
#### 4.1.2.6
Grupo de Vaciado cerradura
El grupo de Vaciado cerradura se puede
configurar en cualquier posici�n del
archivo de configuraci�n pheads.cfg comprendida entre 4 y 11,
escribiendo 5 en el campo �Actuador� del
archivo de configuraci�n pheads.cfg y puede� albergar una (en el grupo de un saliente) o dos (en el
grupo de dos salientes) herramientas. La configuraci�n de la herramienta
montada en el grupo de vaciado cerradura es la misma que la de las herramientas
externas.
Ninguna Rotaci�n
En el archivo de configuraci�n pheads.cfg, el campo �Fin de carrera+ (positivo)
del Vector (grados)� relativo al grupo de Vaciado cerradura debe valer �1. Las
herramientas asociadas al grupo pueden estar comprendidas entre E1 y E96.
Rotaci�n neum�tica
En el archivo de configuraci�n pheads.cfg, el campo �Fin de carrera+ (positivo)
del Vector (grados)� debe valer -90; hay que configurar dos (en el grupo de un
saliente) o cuatro (en el grupo de dos salientes) herramientas
diferentes que est�n comprendidas entre E1 y E96 con la convenci�n de que las
herramientas impares hagan girar el grupo, las pares no. Todas las herramientas
deben tener el mismo n�mero de grupo; el par�metro �Offset R� del equipamiento
debe configurarse correctamente (ver: ejemplos de configuraci�n de las
herramientas en cabezas de contramarcha angular).
Rotaci�n motorizada (Vector)
En el archivo de configuraci�n pheads.cfg, el campo �Fin de carrera+ (positivo)
del Vector (grados)� debe ser igual o mayor que cero; las herramientas
asociadas al grupo pueden estar comprendidas entre E1 y E96.
#### 4.1.2.7
Grupo vertical
El grupo Vertical se puede configurar en una
posici�n cualquiera del archivo de
configuraci�n� pheads.cfg
comprendida entre 4 y 11, escribiendo 7 en el campo �Actuador� del archivo de configuraci�npheads.cfg. La configuraci�n de la herramienta montada en el grupo Vertical es
la misma que la de las herramientas externas. La herramienta asociada al grupo
puede estar comprendida entre E1 y E96.
#### 4.1.2.8
Perforadora sobre eje independiente#### �
La perforadora sobre eje independiente se configura
escribiendo 1 en el campo �Actuador�del cabezal n�mero 1 (perforadora) del
archivo de configuraci�n pheads.cfg.
#### 4.1.2.9#### Control
de una �herramienta gruesa�#### �
Control
autom�tico
Para controlar una �herramienta gruesa� (por
ejemplo una cabeza de transmisi�n angular con una hoja de 300 mm), que en
cualquier caso sea compatible con los cambios de herramienta que hay en la
m�quina, y que sea tal donde sea posible pensar en un control autom�tico
mediante cambios de herramienta autom�ticos, se necesitan las siguientes
modificaciones.
1. Archivo de configuraci�n:
� gendata.cfg: la distancia eje Z de la
mesa tendr� que ser tomada con la neum�tica del cabezal de referencia alto
(mandril).
� xilog3.cfg: el origen en Z tendr� que ser
tomado con la neum�tica del cabezal de referencia alto (mandril).
� pheads.cfg: en el cabezal 3 de referencia
(mandril) introducir en el par�metro �Colocaci�n 0 (Eje Z mm)� y �Colocaci�n 1
(Eje Z mm)� la carrera efectiva del pist�n en mm.
� cfg.cfg: introducir una nueva clave para
controlar el nuevo mando de subida del cabezal principal de modo que haga
siempe FH.
$H 03_UPFH
E10015=0
M 81
E10015=1
$
� axis.cfg. habilitar el control final de
carrera ejes.
2. Programa PGM:
Introducir la instrucci�n SETDONTCARE=1 al
inicio de cada perfil en el cual se se desea utilizar la cabeza de transmisi�n
angular con hoja de 300 mm. En este caso no se controlan m�s las distancias de
seguridad desde la pieza.
3. %8086 (Tool Changer Program; Record
240-142):
Habilitar la variable [UTBIG]=1 (control
UT>300 mm grande)
Control
con carga manual en el mandril
Si la �herramienta gruesa� no es compatible
con los cambios de herramienta que hay en la m�quina, debido a dimensiones
especiales (di�metro) o espacios ocupados (por ejemplo, en el caso de algunas
cabezas de transmisi�n angular), no es posible pensar en un control autom�tico.
En estos casos, el operador puede realizar un cambio herramienta manual en modo
MDI (v�ase: Manual de uso del Panel de la m�quina), utilizando los c�digos M 51
(habilitaci�n desbloqueo mandril principal) y M 171 (memorizaci�n n�mero
herramienta presente en el mandril; para realizar exclusivamente despu�s de un
M 51). Para el uso de estos c�digos v�ase: diagn�stico m�quina.
Para realizar un cambio herramienta manual hay
que tener en cuenta algunas advertencias:
� La operaci�n est� permitida s�lo en el
mandril principal de m�quina y viceversa no es posible en caso de mandriles
suplementarios.
� Hay que prever la generaci�n de un
programa pieza especial que utilice s�lo una herramienta (la que se ha
introducido manualmente en modo MDI), para evitar que la m�quina se bloquee en
la primera llamada de un cambio herramietna autom�tico, incompatible con el
manual. Otros trabajos con otras herramientas en la misma pieza tendr�n por
tanto que introducirse en un programa diferente a realizar en un segundo
momento con los procedimientos normales de cambio herramienta controlados en
autom�tico.
### 4.1.3 Campos
significativos para el optimizador de taladros
El algoritmo de optimizaci�n de los taladros
s�lo tiene en cuenta las herramientas fijas de tipo P (Punta de
orificio). Para que una serie de perforaciones sea efectuada en una sola vez
(con una sola instrucci�n), la misma debe estar constituida por elementos de
igual profundidad, una misma velocidad de ejecuci�n y una misma cara de
trabajo.�
Para crear una instrucci�n que comprenda esta
serie de orificios, el optimizador opera de la siguiente manera:
� considera s�lo las brocas montadas en los
mandriles activos en la cara de trabajo programada;
� excluye todas las brocas con �Longitud
herramienta� inferior a la profundidad programada;
� analiza s�lo las herramientas con la
misma �Longitud broca�.
Para poder efectuar un determinado orificio,
una broca debe reunir las siguientes condiciones:
� El �Di�metro broca� debe coincidir con el di�metro del orificio (hay
que tener en cuenta que, en las herramientas fijas, el �Di�metro herramienta�
coincide con el �Di�metro broca�).
� El �Tipo broca� (L=lanza,
P=plana, S=avellanada) de broca debe coincidir con el tipo de
orificio programado. El orificio programado con un determinado �Tipo broca� no puede ser ejecutado por
una broca con el campo �Tipo broca�no programado.
� Si el orificio ha sido programado de tipo
avellanado con un valor diferente de 0, la Altura avellanador de la herramienta debe coincidir con la
del orificio.
### 4.1.4
Cambio de herramienta suplementario (Tool Room)
Si la m�quina est� dotada de cambio
herramienta suplementario de tipo Tool Room (T) el control de las herramientas
y de sus sitios en el almac�n es completamente autom�tico, por lo tanto no hay
que programar los campos �N�mero
almac�n� y �Plaza almac�n�
de la configuraci�n de las herramientas exteriores.
Si el campo �N�mero adicional�, est� programado con un valor
comprendido entre 1 y 96, busca la manera para que dicha herramienta se
considere (junto con las dem�s herramientas que tienen el mismo n�mero
agregado) perteneciente a un solo portabroca. Dicho portabroca est�
representado por la escrita An con n que va de 1 a 96 en la tabla de
control del cambio herramienta adicional en el ambiente de MDI (v�ase el Manual
de uso del Panel de la m�quina).
Tras haber programado los datos de
equipamiento, hay que cargar las herramientas en los almacenes de la m�quina,
dicha carga se debe efectuar necesariamente mediante la tabla de control del
cambio herramienta en el ambiente de MDI. A continuaci�n, el sistema actualiza
autom�ticamente los dos par�metros de equipamiento mencionados anteriormente y
siguen siendo v�lidos durante el uso de la m�quina. De esta manera, se puede
programar y controlar m�s de un archivo de equipamiento: la activaci�n de un
equipamiento diferente, ya usado antes, configura en modo autom�tico el sistema
con los datos memorizados en dicho archivo (por lo tanto la tabla de control
del cambio herramienta presenta la vieja configuraci�n) pero el usuario debe
restaurar f�sicamente esta condici�n, colocando manualmente las herramientas en
los almacenes de la m�quina seg�n la configuraci�n.
### 4.1.5 Referencia a las
herramientas en el programa
Durante la programaci�n, es posible programar
el campo correspondiente al n�mero de la herramienta (que es el campo T, si la
instrucci�n lo prev�) con un n�mero m que
identifica un�vocamente una herramienta configurada n en base a la siguiente regla:
a) Si m est� comprendido entre 1 y 96, indica
el n�mero de la herramienta fija.
Ejemplo:
T=3 Herramienta fija 3 del
cabezal perforador.
b) En el caso de perforaci�n con las
herramientas fijas, tambi�n se puede regular una perforaci�n m�ltiple. Al
programar varias herramientas al mismo tiempo, (separadas por un espacio o por
una coma, si los n�meros no son contiguos y con un gui�n si se desea toda la
secuencia de herramientas que va del primero al segundo) la perforaci�n se
realiza con una sola bajada del cabezal de la perforadora de la m�quina. En
este caso las cotas X, Y y Z introducidas en la instrucci�n de perforaci�n
valen para el orificio que realiza la primera herramienta de la lista
programada. Los orificios sucesivos pasan por un desplazamiento en X, Y, Z)
respecto del primer orificio equivalente al offset en X, Y, Z de las
herramientas programas referidas a la primera herramienta de la lista.
Ejemplos:
T = 5 2
1 Herramientas 5, 2 y 1 del cabezal perforador, en una
sola bajada
T = 1 �
4 Herramientas 1, 2, 3 y 4 del cabezal perforador, en
una sola bajada.
c) Para indicar una herramienta exterior, se
usa un grupo de tres cifras, de las cuales la primera indica el electromandril
o grupo en el que est� montada la herramienta (por ejemplo, el grupo 100
corresponde a la cifra 1) y las dos siguientes indican el n�mero de la
herramienta (de 01 a 96).
Ejemplos:
T = 101 Herramienta externa 1 (E1), sobre el electromandril principal 1.
T = 280 Herramienta externa 80 (E80), sobre el grupo Universal.
d) La introducci�n de "NULL" en el
campo T permite indicar una herramienta "nula", es decir no
configurada en el herramental.
La herramienta nula no puede ser utilizada
para trabajos sobre la pieza, pero puede ser �til, por ejemplo, en las
instrucciones de ribeteado o en las utilizadas s�lo para la representaci�n
gr�fica.
La herramienta nula no puede utilizarse con la
instrucci�n XT.

### 4.1.6 Visualizaci�n
gr�fica cabezas operadoras
La Visualizaci�n gr�fica cabezas operadoras
visualiza gr�ficamente los cabezales operadores y la informaci�n relativa a
cada herramienta.
A) Barra de herramientas (v�ase el Ap�ndice A). La casilla de texto a la deracha muestra el
fichero de equipamiento seleccionado.
B) Representaci�n gr�fica de los cabezales
operadores.� Las herramientas fijas se
pueden seleccionar con el rat�n.
C) Lista de las herramientas externas
configuradas. Las herramientas de la lista se pueden seleccionar con el rat�n.
D) Representaci�n gr�fica de la cara de
trabajo para la herramienta seleccionada.
E) Tabla de par�metros de la herramienta
seleccionada. En la parte alta se indican: el n�mero de herramienta, el tipo de
herramienta y los posibles comentarios introducidos en la casilla
"Comento".
F) Imagen del tipo de herramienta
seleccionada.
► Como visualizar la Visualizaci�n gr�fica cabezas operadoras.
Hacer
clic en el men� HERRAMIENTAS / GR�FICa mandriles y herramientas.

� o en
el bot�n.

### 4.1.7
Configuraci�n de las cabezas
V�ase: Manual de configuraci�n de las cabezas.
### 4.1.8 Funci�n cortar
- copiar - pegar herramental para m�quinas multigrupo
Para las m�quinas multigrupos como por ejemplo
ERGON y PLANET, los datos de herramental est�n subdivididos en un n�mero de
archivos equivalente al n�mero de grupos configurados. Por tanto las funciones
de cortar, copiar, pegar, cambiar nombre, deben necesariamente aplicarse
manualmente a todos los archivos relativos a un mismo herramental. Por ejemplo
para cambiar el nombre del herramental DEF con TEST, para una m�quina ERGON con
2 grupos de cabezas, es necesario cambiar el nombre del archivo DEF.TLG con
TEST.TLG as� como el nombre del archivo DEF.TL2 con TEST.TL2.