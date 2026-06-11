
# 8.3 Programaci�n de la
mesa
### 8.3.1 Programaci�n de
la mesa con el rat�n
#### 8.3.1.1 Mesa de vigas
y ventosas
► Como posicionar una viga.
Las vigas se pueden posicionar arrastr�ndolas
con el rat�n: coloque el cursor del rat�n sobre una viga, mantenga presionado
el bot�n izquierdo del rat�n y arrastre la viga.
► Como posicionar una base (mesa de vigas y
ventosas con motor).
Para mover una base sobre una mesa de vigas
con motor, coloque el cursor del rat�n sobre la base, mantenga presionado el
bot�n izquierdo del rat�n y arrastre la base. Junto con la base tambi�n puede
arrastrar la viga sobre la que est� montada.
► Como insertar un soporte o un elemento de la mesa.
1. Seleziona la p�gina de los
soportes o de los elementos de la mesa.
2. Abra la lista de soportes o
de los elementos de la mesa haciendo clic en el signo +.
3. Coloque el cursor del rat�n
sobre el soporte que desea insertar, mantenga presionado el bot�n izquierdo del
rat�n y arrastre el soporte o el elemento de la mesa hasta la posici�n deseada.

En las
vigas y ventosas con motor, el soporte se ha de insertar en una de las bases de
las vigas.
Los
topes de apoyo-pieza pueden introducirse s�lo si est� presente la barra m�vil.
► Como borrar un soporte o un elemento de la mesa.
Seleccione el
soporte o el elemento de la mesa y haga clic en el men� MODIFICAR/CANCELAR.
► Como mover un soporte o un elemento de la mesa.
Coloque el cursor
del rat�n sobre el soporte o el elemento de la mesa, mantenga presionado el
bot�n izquierdo del rat�n y arrastre el soporte.
► Como girar un soporte (ventosas).
1. Seleccione una ventosa que se pueda girar y haga clic en el men� MANDOS/GIRAR SOPORTE.
El eje
de rotaci�n de la ventosa se visualiza gr�ficamente como un c�rculo verde.
2. Mantenga pulsado el bot�n izquierdo del rat�n y arrastre la ventosa
para orientarla.
Para
salir del modo rotaci�n vuelva a hacer clic en el men� MANDOS/girar soporte o pulse la tecla [esc] del teclado.
Reglas de rotaci�n de las ventosas
Cada ventosa, si seleccionada sin
girarla,� introducida en el plano a
pesar de como est� configurado, indica un �ngulo de 0�.
Por tanto si por ejemplo, se introduce una
ventosa cualquiera sobre un plano de EPL, si seleccionada aparece con un �ngulo
de 0�.
Para todos los soportes a pesar de su
configuraci�n, el �ngulo de rotaci�n se considera entre el centro de
rotaci�n y el centro del apoyo

�����

En Libsupp.cfg estos puntos est�n definidos
por las claves siguientes:�
[OFFX_OVR] �
[OFFY_OVR] �
Que definen el centro de rotaci�n
respecto al centro de la base de la Ventosa.
[OFFX_OVAPP] �
[OFFY_OVAPP] �
Que definen el centro de apoyo respecto
al centro de rotaci�n de la Ventosa.
(para m�s detalles v�ase el documento Configuraciones
EPL y de Libsupp.cfg )
El valor del �ngulo de rotaci�n que visualiza EPL
aumenta de manera positiva desde el eje X hacia el eje Y de la Origen Pieza
(OP) aplicada al centro de rotaci�n de la Ventosa.
Por ejemplo tomando en consideraci�n las
Ventosas configuradas de la siguiente manera:
Ventosa1:������������������������������� Ventosa2
seg�n la direcci�n de los ejes de la origen de
programaci�n, a continuaci�n se muestra como aparecen las rotaciones
siguientes:�
Especularidad �rea
�ngulo de 0�
�ngulo de 45�
�ngulo de 90�

Ventosa1
Ventosa1
�Ventosa1
Ventosa2
���
Ventosa2
Ventosa2

Ventosa1
���
��
Ventosa1
Ventosa1
Ventosa2
Ventosa2
Ventosa2

Ventosa1
����
�����

Ventosa1
Ventosa1
Ventosa2
��
�����

Ventosa2
Ventosa2

Ventosa1
���
Ventosa1
Ventosa1
Ventosa2
�
���
Ventosa2
Ventosa2
#### 8.3.1.2 Mesa
multifuncional
► Como insertar un soporte (ventosa o modulset) o
un elemento de la mesa (tope de apoyo).
1. Seleziona la p�gina de los soportes o de los elementos de la mesa.
2. Abra la lista de los soportes o de los elementos de la mesa haciendo
clic en el signo +.
3. Coloque el cursor del rat�n sobre el soporte o el tope de apoyo que
desea insertar, mantenga presionado el bot�n izquierdo del rat�n y arrastre el
soporte o el tope de apoyo hasta la posici�n deseada.
El
programa ubicar� el soporte sobre la rejilla de la mesa de forma autom�tica.
► Como insertar una junta.
1. Haga clic en el men� HERRAMIENTAS/COLOCAR LA� JUNTA para activar la funci�n.
2. Para insertar la junta, haga clic en el punto de inicio y mueva el
rat�n para trazar el primer segmento.
El
segmento trazado se puede orientar cada 90� moviendo el rat�n. Para eliminarlo,
pulse la tecla [Esc]
del teclado.
3. Para trazar el segmento siguiente, haga clic en un punto y, a
continuaci�n, mueva el rat�n en la direcci�n del nuevo segmento.
4. Para terminar de insertar la junta, haga clic dos veces sobre el punto
final del segmento.
Al
terminar un segmento haciendo doble clic, el sistema lo considera
independiente. Si los segmentos independientes son adyacentes (forman un perfil
continuo), se pueden unir haciendo clic en el men� herramientas/Unir LAS
polil�neas adyacentes. El programa une los segmentos independientes adyacentes de forma
autom�tica al guardar el archivo.
Para
salir del modo insertar la junta, vuelva a hacer clic en el men� HERRAMIENTAS/COLOCAR LA
JUNTA o pulse
la tecla [esc]
del teclado.
En modo insertar junta no se pueden introducir otros tipos de soporte.
► Como borrar un soporte o un tope de apoyo.
Seleccione un
soporte o un tope de apoyo y haga clic en el men� MODIFICAR/CANCELAR.
Para seleccionar todos los segmentos de un perfil de una
junta, haga clic en la junta pulsando al mismo tiempo la tecla [ctrl] del teclado.
► Como mover un soporte (ventosa o modulset) o un
tope de apoyo.
Seleccione el
soporte o el tope de apoyo y arr�strelo con el rat�n hasta la posici�n deseada.
► Como girar un soporte (ventosa o modulset).
1. Seleccione un soporte que se pueda girar y haga clic en el men� MANDOS/GIRAR sOPORTE.
El
modulset gira al rededor del punto de encaje macho.
2. Mantenga presionado el bot�n izquierdo del rat�n y arrastre el soporte
para orientarlo.
Los
modulset s�lo se pueden girar de 90 en 90�.
Para
salir del modo rotaci�n, vuelva a hacer clic en el men� MANDOS/GIRAR SOPORTE o pulse la tecla [esc] del teclado.
### 8.3.2 Programaci�n de
la mesa introduciendo los datos desde el teclado
La introducci�n, desplazamiento o rotaci�n de
un soporte (excepto las guarniciones en las mesas multifuncionales) o la
introducci�n de un elemento de la mesa se puede programar introduciendo los
datos desde el teclado. Para mover y girar un soporte programado sobre una mesa
de trabajo existe una barra de desplazamiento de los soportes.
A) Campos de posicionamiento del soporte seleccionado:
- campos OP (X, Y):
muestran las coordenadas X e Y del soporte seleccionado respecto al origen en
tablero. En estos campos puede introducir las coordenadas del punto al que
desea desplazar el soporte.
- campos RM (X, Y): muestran las coordinadas X y Y del �visor� del soporte seleccionado
referidas a los renglones m�tricos presentes en la superficie. El visor
representa un punto de referencia alternativo respecto al centro del apoyo del
soporte. Las coordinadas del visor coinciden por default con las del centro de
la base del soporte, pero pueden configurarse diversamente para los soportes
individuales. En las superficies vigas y ventosas, en estas casillas es posible
introducir las coordinadas del punto en el que se quiere desplazar el soporte,
en base a la posici�n del visor.
- campos OM (X, Y):
muestran las coordenadas X e Y del soporte seleccionado respecto al origen en
m�quina. En estos campos no puede modificar las coordenadas para desplazar el
soporte.
Las coordenadas X e Y indican un punto
distinto para cada tipo de soporte. Si desea m�s informaci�n, consulte el
apartado 8.6 (Tipos de soporte).
B) Botones para desplazar el soporte seleccionado; se habilitan al
introducir la distancia en el campo paso x/y.
C) Campo para introducir los grados de rotaci�n de los soportes
giratorios.
Para
visualizar el origen en tablero y el origen en m�quina, haga clic en el men� VISUALIZAR /
MUESTRA/OCULTA origEn PGM y VISUALIZAR
/ MUEstra/OCULTA origEn M�QUINA.
A) Origen en tablero
B) Origen en m�quina
► Como insertar un soporte o un elemento de la
mesa.
1. Abra la lista de los soportes o de los elementos de la mesa y haga
clic en el soporte o en el elemento de la mesa que desea insertar, pulsando el
bot�n derecho del rat�n.
2. Haga clic en la opci�n InTRODUCIR SOPORTE del
men� de selecci�n r�pida.
3. Defina la posici�n en la ventana Introducir
soporte o en la ventana Introducir
elemento de la mesa, seg�n las opciones disponibles.
4. Hacer clic en el bot�n OK para confirmar la introducci�n del soporte o del elemento de la mesa.
► Como desplazar un soporte introduciendo las
coordenadas.
1. Seleccione el soporte de la mesa de trabajo que desea desplazar.
2. Introduzca las nuevas coordenadas X e Y en los campos OP.
Los
campos OP y OM muestran las coordenadas actuales del soporte seleccionado. Para
ver las coordenadas de un punto de la mesa de trabajo, coloque el cursor del
rat�n sobre el punto que le interesa: las coordenadas se visualizan en la parte
derecha de la barra de estado.
3. Pulse la tecla [Env�o] del
teclado.
► Como desplazar un soporte introduciendo la
distancia.
1. Seleccione el soporte de la mesa de trabajo que desea desplazar.
2. Introduzca la distancia en el campo Paso X/Y.
3. Desplace el soporte en la direcci�n que desea, haciendo clic en los
botones de direcci�n.
El
soporte seleccionado se puede desplazar varias veces y en distintas direcciones
seg�n la distancia introducida.
El
soporte tambi�n se puede desplazar pulsando las flechas del teclado .
► Como desplazar o duplicar un soporte.
Los soportes insertados se puede desplazar o
duplicar por medio de las funciones CORTAR/copiaR y PEGAR. Dichas funciones sirven para desplazar o duplicar un soporte
insertado y modificado, por ejemplo, con una rotaci�n.
1. Seleccione un soporte de la mesa de trabajo.
2. Haga clic en el men� modificar/cortar (para
mover el soporte) o modificar /Copiar (para duplicar el
soporte). El soporte seleccionado, o la copia, se memoriza en el portapapeles.
3. Haga clic en el men� modificar /PEGAR.
4. Introduzca en la ventana Pegar
soporte los datos solicitados.
5. Haga clic en OK: el sistema inserta el
soporte memorizado en el portapapeles en la posici�n seleccionada.
► Como girar un soporte.
1. Seleccione un soporte de la mesa de trabajo que se pueda girar .
2. Introduzca el �ngulo de rotaci�n en el campo �ngulo.
Si el
valor es positivo, el soporte gira desde el eje X hacia el eje Y en sentido de
las agujas del reloj o viceversa en funci�n de la posici�n del origen en
tablero (origen pieza � OP) , como muestra el siguiente esquema.
3. Pulse la tecla [Env�o] del teclado.
### 8.3.3### Programaci�n
de par�metros (mesa motorizada travesa�os y ventosas)
#### 8.3.3.1#### Introducci�n
a la programaci�n de par�metros
La programaci�n de par�metros permite
introducir en un programa algunos par�metros cuyo valor puede cambiar seg�n sea
necesario. De este modo tendremos un solo programa que nos permitir� controlar
piezas que tienen dimensiones diferentes.
La programaci�n de par�metros de las cotas de
los soportes puede llevarse a cabo en el interior de la barra de desplazamiento
de los soportes, introduciendo directamente las f�rmulas de los par�metros
dentro de las celdas OP correspondientes a las coordinadas X e Y de los
soportes seleccionados.
Se encuentra tambi�n otro valor m�s, offset
num�rico, que sumado algebraicamente al valor param�trico define un valor
absoluto num�rico que constituir� la cota efectiva de programaci�n aplicada
al soporte.
El offset num�rico ha sido introducido
para poder asegurar que las sucesivas modificaciones de la posici�n del soporte
(por Ej. Mediante el desplazamiento con el rat�n) permitan mantener inalterada
la f�rmula de par�metros correspondiente.
Confirmando la programaci�n, dicho valor
absoluto se vuelve propiedad del soporte y se visualiza en la barra de desplazamiento
de los soportes como si fuese un valor digitado directamente.
Valor
absoluto num�rico = Valor Param�trico + Offset Num�rico
El punto param�trico es el centro del apoyo
del soporte.
En el caso de programaci�n de varios
soportes dentro de un mismo travesa�o, respecto del eje X, la modificaci�n de
la coordinada X del �ltimo soporte parametrizado modifica todos los que hemos
introducido antes.
►
Parametricemos un soporte ventosa.
1 seleccionamos un soporte ventosa haciendo
clic con el bot�n izquierdo del rat�n.
2 Seleccionamos la casilla OP correspondiente
a la coordinada X del soporte ventosa e introducimos la f�rmula param�trica
DX-200. Presionamos el bot�n [ENVIAR] del teclado para
confirmar.
La coordinada X del soporte seleccionado
contiene su par�metro. El Editor de las mesas de trabajo en el caso de que las
dimensiones del tablero se modifiquen volver� a posicionar el travesa�o seg�n las
nuevas dimensiones del tablero.
►
Modifiquemos la posici�n del soporte ventosa precedentemente parametrizado.
1 Seleccionamos y desplazamos el travesa�o con
el rat�n.
2 El Editor de las mesas de trabajo mantiene
inalterada la f�rmula param�trica modificando el valor del offset num�rico;
el valor cambiar� (al positivo o al negativo) seg�n la diferencia entre el
valor inicial y el valor final de la coordinada X del soporte
► Abrimos la
barra de par�metros del programa.

Clic en el
men� visualiza/barra de PAR�METROS.

� o en
el bot�n.

La Barra de par�metros se compone de tres
ventanas:
A) Ojo m�gico
B) Preferidos
C) Categor�a
A) La ventana Ojo m�gico permite
parametrizar los soportes mediante la aplicaci�n de f�rmulas predefinidas por
el Editor de las mesas de trabajo.
►
Parametricemos un soporte utilizando el Ojo m�gico.
1 seleccionar un soporte.
2 Introducimos la f�rmula param�trica (DX,0)
haciendo clic en el bot�n especial.
La coordinada X del soporte seleccionado
contiene los par�metros.
A las f�rmulas param�tricas seleccionadas se
le sumar�n de modo autom�tico los correspondientes offset (X,Y) que le
permitir�n al soporte parametrizado mantener su posici�n.
Dichos offset sucesivamente ser�n
modificables.
Antes de la definici�n de los par�metros:
Despu�s de la definici�n de los par�metros:
B) La ventana Favoritos permite
visualizar los par�metros precedentemente seleccionados como favoritos.
Se puede copiar la variable seleccionada de la
ventana en el interior de la celda OP de la coordinada (X,Y) del soporte.
Para copiar la f�rmula es necesario
seleccionar la casilla OP en la cual se desea introducir la f�rmula param�trica
y sucesivamente hacer doble clic con el bot�n izquierdo del rat�n en la f�rmula
dentro de la venta Favoritos.
C) La ventana Categor�a permite
visualizar dentro de la lista de variables disponibles agrupadas por categor�a.
Las variables disponibles son las siguientes:
DX, DY del Header
del programa principal.
Variables PAR del
programa principal.
Constantes D del
programa principal.
Variables L del
programa principal.
Es posible copiar la variable seleccionada de
la ventana dentro de la celda OP de la coordinada (X,Y) del soporte.
Para copiar la f�rmula es necesario
seleccionar la celda OP en la cual se desea introducir la f�rmula param�trica y
sucesivamente hacer doble clic con el bot�n izquierdo del rat�n en la f�rmula
en el interior de la ventana Categor�a.