
# 9.13 Reglas de estacionamiento
Al
finalizar la fase de preparaci�n plano las barras no programadas son
llevadas a una posici�n de fuera de dimensi�n. Las cotas nuevas, nombradas cotas
de estacionamiento, son calculadas autom�ticamente por el sistema y
dependen del �rea de ejecuci�n del programa.�

### Reglas de estacionamiento para barras no programadas
En
general, para las barras no programadas, valen las siguientes reglas:
1) Barras pertenecientes al �rea de trabajo
a. las barras no programadas presentes en el
�rea de ejecuci�n son llevadas en direcci�n del �ngulo opuesto a la origen del
�rea f�sica
2) Barras pertenecientes a las �rea
adyacentes al �rea de trabajo
a. si la barra supera el llamado umbral y se
encuentra en el �rea de trabajo, se realiza el estacionamiento de todas las
barras del �rea
b. si la barra no supera la cota de umbral,
entonces no se realiza el estacionamiento de las barras del �rea adyacente

Figura
27: Estacionamiento
barras si �REA de EJECUCI�N �REA AB
La Figura 27 muestra el
estacionamiento de barras no programadas cuando el �rea de ejecuci�n� es el �rea AB. Las barras que se muestran en
la figura representan las barras no programadas� en las que es necesario comprobar el estacionamiento.� En la primera prima figura se observa� que el �rea AB est� ocupada por tres barras:
la primera y la segunda barra desde la izquierda pertenecen al �rea de trabajo,
por tanto deben ser llevadas hacia el l�mite opuesto� respecto al origen del �rea f�sica (v�ase segunda figura),
mientras la tercera barra pertenece al �rea�
DC; en este caso es necesario efectuar el estacionamiento de las barras
del �rea� DC ya que la barra tiene una
cota superior al umbral (en la figura el umbral est� representado por la
separaci�n de las �reas f�sicas). Luego, la tercera y la cuarta barra son
llevadas hacia el �rea de trabajo�
(v�ase segunda figura).

Figura
28: Estacionamiento
barras si �REA de EJECUCI�N� �REA CD
La Figura 28 muestra el
estacionamiento de barras no programadas cuando el �rea de� ejecuci�n es el �rea CD. En la primera
figura se observa que el �rea CD est� ocupada solamente por dos barras: estas
deben ser llevadas hacia el l�mite opuesto respecto al origen del �rea f�sica
(v�ase segunda figura). Las barras presentes en el �rea AB no superan el
umbral, por tanto no es necesario realizar sobre las mismas ning�n movimiento
(v�ase segunda figura).�
### Reglas de estacionamiento de dispositivos no
programa### dos
A
diferencia de las barras, las bases de soporte a los dispositivos no
programados son SIEMPRE estacionadas en el lado opuesto respecto al
origen del �rea f�sica. En este caso existen dos posibilidades:
1. el origen de
programaci�n est� configurada en bajo: �rea AB, BA, CD, DC. Las bases son
llevadas al lado opuesto� respecto al
origen del �rea f�sica, por tanto en alto
2. el origen de
programaci�n est� configurada en alto: �rea EF, FE, GH, HG. Las bases son
llevadas al lado opuesto respecto al origen del �rea f�sica, por tanto en bajo.

Figura
29: estacionamiento
bases para dispositivos �rea AB: ejemplo de la figura 17

Figura
30:estacionamiento
bases para dispositivos �rea HG
La Figura 29 muestra el
estacionamiento de las base presentes en las barras no programadas en el �rea
AB y DC. Come se puede observar las bases son llevadas en alto. En caso
contrario, si el origen del �rea f�sica ha sido configurada en alto, como en el
caso de la Figura 30: las bases son estacionadas en bajo. En esta figura se observa que las
bases de los dispositivos presentes� en
las barras del �rea EF no se estacionan; como en el caso de la figura 18. De
hecho, estas barras no necesitan desplazamiento.

AP�NDICES
AP�NDICE
A. Men� y barras de mandos
Ventana
principal, del editor de programas y del editor de equipamientos
Men� Archivo
Nuevo

Abre un nuevo
documento.
Abrir

Abre un documento
existente.
Cerrar

Cierra un
documento abierto.
Cerrar todo

Cierra todos los
documentos abiertos.
SalvarH

Guarda un
documento.
Salvar como...

Permite guardar
un documento con otro nombre.
Guardar en formato p.m.

Guarda el
documento en el formato pgm.
Salvar todo

Guarda todos los
documentos abiertos.
Configurar M�quina

Abre el editor de
los archivos de configuraci�n.
Impresi�n

Imprime un
documento.
Vista preliminar

Visualiza la
vista preliminar de un documento (hacer clic en Cerrar para
regresar al documento).
Configurar impresora

Permite
configurar la impresora.
Salir

Salir de Xilog Plus.
Men� Modificar
Anular

Deshace la �ltima
modificaci�n.
Cortar

Elimina datos seleccionados en el documento
en los memoriza en el Portapapeles.
Copiar

Copia los datos seleccionados en el
Portapapeles.
Pegar

Inserta el contenido del Portapapeles
(cortado o copiado) en el punto deseado.
Eliminar

Elimina los datos
seleccionados.
Desplazar

(Editor gr�fico)
Mueve el trabajo seleccionado.
B�squeda

(Editor de texto
y macro) Busca un texto.
Substituir

(Editor de texto
y macro) Busca un texto y lo sustituye por otro especificado.
Refresh

(Editor gr�fico)
Actualiza la representaci�n gr�fica de un programa.
Reinterpretar

(Editor gr�fico)
Reinterpreta un programa.
Propiedad

(Editor gr�fico)
Visualiza los par�metros del trabajo seleccionado.

Men� Visualizar
Barra...

Muestra/oculta la
barra seleccionada de la lista.
Restablecer original

Restablece la visualizaci�n original de las
ventanas de Xilog Plus.
Editor libre

(Editor de texto y macro) Pasa a la
modalidad de Editor libre.
Editor guiado

(Editor de texto y macro) Pasa a la
modalidad de Editor guiado.
Di�metro herramientas

Habilita/inhabilita la visualizaci�n de los
di�metros herramienta en fresado.
Referencias

Muestra/oculta los sistemas de referencia
del tablero.
Estructura del programa

Muestra/oculta la estructura del programa.
Men� Herramientas
Calculadora

Visualiza la
calculadora cient�fica (v�ase el Ap�ndice M).
Backup

Hace una copia de seguridad de los datos
(v�ase el Ap�ndice M).
Restore

Recupera los datos de la copia de seguridad
(v�ase el Ap�ndice M).
Actualizar lista macro

Actualiza los iconos de la barra de
instrucciones cuando se a�aden nuevas macros.
Gr�fica mandriles y herramientas

(Editor de texto
y grafico) Abre la ventana de Visualizaci�n gr�fica cabezas operadoras.
Gr�fica programa

(Editor de texto
y macro) Visualiza la representaci�n gr�fica del programa.
Editor par�metros

(Editor gr�fico y
mix) Abre el Editor par�metros.
Wizard par�metros

(Editor de texto
y grafico) Abre el Wizard par�metros.
Editor vigas y ventosas

(Editor de texto
y gr�fico) Abre la ventana del Editor de mesas de trabajo.
Eliminar programaci�n mesa

Cancela la
programaci�n de la mesa de
trabajo.
Visualisaci�n archivo de �trace�

Abre la tabla de
mensajes programados con la instrucci�n TRACE.
Optmizador programa

(Editor de texto
y gr�fico) Activa la funci�n de optimizaci�n de los programas.
Lista programas

(Mix)
Introducci�n de uno o varios pasos de mix desde lista programas.
Zoom +

Aumenta la zona
seleccionada con el cursor (arrastrar con el rat�n el rect�ngulo de zoom
sobre el punto que se desea aumentar y pulsar la tecla [env�o]).
Zoom -

Reduce el zoom.
OK Zoom

Habilita el zoom.
Anular Zoom

Inhabilita el zoom.
Cambiar vista gr�fica

(Editor gr�fico)
Modifica el tipo de visualizaci�n grafica.
Opciones

(Editor de texto guiado, mix y macro) Abre
la tabla para la introducci�n del par�metro T de Encabezamiento.
Tipo de bloqueo

(Editor de texto guiado, mix y macro) Abre
la tabla para la introducci�n del par�metro V de Encabezamiento.
Men� Opciones
Programaciones
internacionales

Abre la ventana
para seleccionar el idioma o la unidad de medida (mil�metros o pulgadas)
utilizados por Xilog Plus.
Fecha/Hora

Abre la ventana para introducir la fecha y
la hora.
Editor texto

Activa el editor de texto de un programa.
Editor gr�fico

Activa el editor gr�fico de un programa.
Editor macro

Activa el editor
de macros.
Avanzadas

Abre la ventana
para definir algunas caracter�sticas de la interfaz de Xilog Plus (fondo, ventanas,
tablas de instrucciones).
Men� Ventana
Superponer

Superpone las
ventanas abiertas.
Flanquear

Muestra todas las ventanas abiertas.
Dispones
iconos

Muestra los iconos en la parte inferior de
la ventana.
Men� Ayuda
Temas de la
Gu�a

Abre la ventana
de la Gu�a en l�nea. Tambi�n se puede activar pulsando la tecla [F1]: aparece el contenido de la gu�a disponible para el elemento
seleccionado.
Informaciones
sobre Xilog Plus

Abre la ventana de informaci�n sobre el
editor Xilog Plus (copyright
y n�mero de versi�n).
Barra de
herramientas

Abre un nuevo documento.

Abre un documento ya existente.

Guarda un documento.

Corta datos seleccionados en el documento y
los memoriza en el Portapapeles.

Copia los datos seleccionados en el
Portapapeles.

Pega el contenido del Portapapeles (cortado
o copiado) en el punto deseado.

Deshace la �ltima operaci�n.

Imprime el documento activo.

Abre el editor de los archivos de
configuraci�n.

Visualiza la calculadora cient�fica (v�ase
el Ap�ndice M).

Activa la funci�n de copia de seguridad
(v�ase el Ap�ndice M).

Activa la funci�n de recuperaci�n de la
copia de seguridad (v�ase el Ap�ndice M).

Abre la ventana de informaci�n sobre el
editor Xilog Plus (copyright
y n�mero de versi�n).

Habilita la b�squeda por argumentos en la
Gu�a en l�nea. El puntero del rat�n se convierte en una flecha y un punto
interrogativo: haciendo clic en el punto deseado aparece el argumento de la
gu�a. La funci�n tambi�n se activa pulsando las teclas [Shift]+[F1].
Barra de funciones

(Editor de texto y gr�fico) Abre la ventana
de de Visualizaci�n gr�fica cabezas operadoras.

Carga la ventana de Visualizaci�n gr�fica.

(Editor texto y gr�fico y Twin) Abre el
Editor de las mesas de trabajo.

(Editor texto y
gr�fico y Twin) Cancela la programaci�n de la mesa de trabajo. Si no ha sido
programada la mesa para el programa corriente este mando est� inhabilitado.

(Mix) Abre la
ventana para introducir un programa en un mix.

(Editor gr�fico y mix) Abre el Editor
par�metros.

(Editor de texto
y grafico) Abre el Wizard par�metros.

(Editor de texto y macro) Inserta/elimina
una nueva l�nea en un programa.

(Editor de texto guiado, mix y macro). Abre
la tabla para la introducci�n del par�metro T de Encabezamiento.

(Editor de texto guiado, mix y macro). Abre
la tabla para la introducci�n del par�metro V de Encabezamiento.
Al trabajar con
archivos DXF se habilitan los siguientes comandos:

Abre la ventana para introducir datos
generales.

Abre la ventana para definir el modo
gr�fico.

Une perfiles separados (auto-join).

Abre la ventana para definir la entrada en
el perfil.

Invierte el perfil.

Visualiza el orden de geometr�as.
Barra de datos del
programa

Abre la ventana para modificar Header.

(Editor de texto guiado, mix y macro). Abre
la tabla para la introducci�n del par�metro T de Encabezamiento.

(Editor de texto guiado, mix y macro). Abre
la tabla para la introducci�n del par�metro V de Encabezamiento.

(Editor gr�fico y mix) Abre el Editor
par�metros.
�
(Editor de texto
y grafico) Abre el Wizard par�metros.
Barra de herramientas gr�ficas (editor gr�fico)

Aumenta el �rea seleccionada con el cursor
(arrastrar con el rat�n el rect�ngulo de zoom sobre el punto que se desea
aumentar y pulsar la tecla [Env�o]).

Reduce el zoom.

Cambia la visualizaci�n de la cara gr�fica.

Visualiza la correcci�n del radio de la
herramienta.

Muestra/oculta los sistemas de referencia
del tablero.

Muestra/oculta la estructura del programa.
Barra de datos modales (editor gr�fico)

Habilita la cara 1.

Habilita la cara 2.

Habilita la cara 3.

Habilita la cara 4.

Habilita la cara 5.

Correcci�n herramienta nula.

Correcci�n derecha.

Correcci�n izquierda.

Correcci�n en profundidad.

Incremental inhabilitado.

Incremental en X.

Incremental en Y.

Especular inhabilitado.

Especular en X.

Especular en Y

Sentido G2/G3 original.

Inversi�n sentido G2/G3.
Barra de estado
La barra de estado se visualiza en la parte
inferior de la ventana de Xilog Plusy permite al operador controlar el estado de la m�quina en todo momento, ya que
en ella se visualizan inmediatamente los cambios de estado y funci�n de la
m�quina:
� ayuda de las operaciones que se est�n
realizando (�rea izquierda);
� estado de la interfaz (�rea central);
� estado del C.N. (�rea central);
� estado del teclado f�sico (�rea
derecha);
En el �rea izquierda de la barra de
estado se describen las funciones del men� y los botones de las barras cuando
el rat�n est� sobre ellas.
Las �reas centrales de la barra de
estado suministran la siguiente informaci�n:
����

Unidad de medida (mm = mil�metros;� in. = pulgadas).

Editor gr�fico habilitado.

Editor de texto habilitado.

Editor macro habilitado.
Las �reas derechas de la barra de
estado indican si las teclas siguientes est�n bloqueadas:
MA
La tecla Caps Lock est� bloqueada.
NUM
La tecla Num Lock est� bloqueada.
BS
La tecla Scroll Lock est� bloqueada.
Visualizaci�n gr�fica cabezas operadoras
Barra de
herramientas

Selecciona una herramienta.

Deselecciona una herramienta.

B�squeda por longitud de la herramienta.

B�squeda por di�metro de la herramienta.

B�squeda por longitud y di�metro.

Bot�n para visualizar el archivo de
equipamiento corriente.

Bot�n para introducir herramientas fijas y
externas en el editor de programas.

Grupo de ejes CN (para Ergon).
Visualizaci�n
gr�fica
Men� Archivo
Cerrar

Salir de la
visualizaci�n gr�fica.
Men� Visualizar
Correcci�n herramienta

Habilita/inhabilita
la visualizaci�n de la correcci�n de la herramienta.
Otro tipo de
gr�fica

Visualiza las proyecciones sobre las caras
laterales (s�lo si el gr�fico corresponde a cada una de las caras).
Gr�fica lados laterales

Visualiza las caras.
Men� Zoom
Zoom +

Aumenta la zona
seleccionada con el cursor (arrastrar con el rat�n el rect�ngulo de zoom
sobre el punto que se desea aumentar y pulsar la tecla [env�o]).
Zoom -

Reduce el zoom.
OK Zoom

Habilita el zoom.
Anular Zoom

Inhabilita el zoom.
Men� Opciones
Refresh

Actualiza la
representaci�n gr�fica.
Stop

Bloquea ciclos infinitos (v�ase el cap�tulo 6.2.4 � Realizaci�n y ejecuci�n de un ciclo).
Ambiente de importaci�n de los archivos
DXF
Al importar a Xilog Plus un archivo en formato DXF, en el men� Modificar
se habilitan los siguientes comandos espec�ficos:
Men� Modifier
Auto Join

Une perfiles separados
(auto-join).
Entrada/datos orificio

Abre la ventana para definir la entrada en el perfil.
Inversi�n recorrido perfil

Invierte el perfil.
Sistema de referencia

Abre la ventana para definir el modo gr�fico.
Programaciones generales

Abre la ventana para programar los datos generales.
Ordenaci�n de las geometr�as

Visualiza el orden de las geometr�as.
OK pr�xima geometr�a

Pasa a la pr�xima geometr�a.
Salida de la ordinaci�n

Sale de la ventana de visualizaci�n del orden de geometr�as.

�

Editor Mesas Trabajo
Men� Archivo
Abrir
layout...

Abre un archivo
de programaci�n ya existente.
Guardar
layout

Memoriza la
programaci�n de la mesa junto con el programa de trabajo.
Guardar
layout como...

Memoriza la
programaci�n de la mesa en un archivo distinto al del programa de trabajo.
Guardar
y cerrar

Memoriza la
programaci�n de la mesa junto con el programa de trabajo y cierra el editor.
Exportar/Hoja
de Excel

Exporta la
programaci�n de la mesa a una hoja de c�lculo de Excel.
Exportar/Esquema
XML

Exporta la
programaci�n de la mesa a un archivo XML.
Impresi�n...

Imprime la
programaci�n de la mesa activa.
Vista
preliminar

Muestra el
documento antes de imprimirlo.
Configurar
impresora...

Modificar los
valores de impresi�n establecidos.
Salir

Cierra el editor.
Men� Modificar
Anular

Anula la �ltima
acci�n.
Cortar

Corta el soporte seleccionado.
Copiar

Copia el soporte seleccionado.
Pegar

Abre la ventana para introducir el soporte
cortado o copiado.
Cancelar

Elimina el
soporte seleccionado.
Men� Visualizar
Barra...

Muestra/oculta la
barra de la lista seleccionada.
Restablecer
Toolbar originales

Restablece la disposici�n original de las
barras.
Muesta/Oculta
Origen PGM

Muestra/oculta el sistema de referencia del
panel.
Muestra/Oculta
Origen M�quina

Muestra/oculta el sistema de referencia de
la m�quina.
Mostrar/Ocultar
Ver Viguetas

Muestra/oculta los visualizadores viguetas.
Panel
en primer plano

Muestra el panel en primer plano.
Activar
Dibujo Light

Muestra la mesa de trabajo en un gr�fico
esquem�tico.
Pantalla
Entera

Activa/desactiva la visualizaci�n en
pantalla entera de la ventana.
Men� Seleccionar
Soporte anterior

Visualiza la
posici�n del soporte anterior.
Soporte siguiente

Visualiza la posici�n del soporte siguiente.
Men� Mandos
Desplazar
soporte hacia izq

Mueve el soporte
seleccionado hacia la izquierda (es necesario introducir la distancia en el
campo Paso X/Y de la Barra
desplazamiento soportes).
Desplazar
soporte hacia dch

Mueve el soporte seleccionado hacia la
derecha (es necesario introducir la distancia en el campo Paso X/Y de la Barra desplazamiento
soportes).
Desplazar
soporte hacia arriba

Mueve el soporte seleccionado hacia arriba
(es necesario introducir la distancia en el campo Paso X/Y de la Barra desplazamiento soportes).
Desplazar
soporte hacia abajo

Mueve el soporte seleccionado hacia abajo
(es necesario introducir la distancia en el campo Paso X/Y de la Barra desplazamiento soportes).
Introducir
soporte

Inserta un soporte de la lista de soportes
ya seleccionado, introduciendo los datos desde el teclado.
Girar
soporte

Activa/desactiva la rotaci�n del soporte
seleccionado.
Invertir soporte

Gira el soporte seleccionado de 180�.
Abrir/cerrar el separador de grados

Muestra la posici�n abierta/cerrada del
separador de grados.
Men� Herramientas
Control
Anticolisi�n

Controlar si
existe el riesgo de choque.
Progr.
Autom�tica Ventosas/ Nuova Progr. Autom�tica Ventosas

Posiciona
autom�ticamente las ventosas (s�lo para mesas de travesa�os y ventosas).
Zoom/Zoom
en tiempo real

Aumenta o reduce la imagen de la mesa de
trabajo:
- hacer clic en un punto pulsando el bot�n
izquierdo del rat�n para aumentar la imagen;
- hacer clic en un punto pulsando el bot�n
derecho del rat�n para reducir la imagen.
El zoom enfoca el punto se�alado con el
cursor del rat�n.
Zoom/�rea
de zoom

Traza un rect�ngulo arrastrando el cursor
del rat�n sobre la representaci�n gr�fica. Al soltar el rat�n, la zona
incluida en el rect�ngulo aumenta.
Zoom/Zoom
programa pieza

Aumenta la zona ocupada por el tablero.
Zoom/Restablecer
zoom original

Restablece las dimensiones originales de la
representaci�n gr�fica.
Colocar
la junta

Activa/desactiva la funci�n para insertar
juntas (s�lo para mesas multifuncionales).
Unir
las polil�neas adyacentes

Unir los segmentos de juntas independientes
pero adyacentes para formar un �nico perfil (s�lo para mesas
multifuncionales).
Men� ?
Argumentos
de la Gu�a

Abre la ventana
de ayuda en l�nea.
Informaciones
sobre EPL�

Muestra
informaci�n sobre el programa, el n�mero de versi�n y el copyright.
Barra de herramientas

Abre un archivo de programa existente.

Memoriza la programaci�n de la mesa junto
con el programa de trabajo.

Memoriza la
programaci�n de la mesa junto con el programa de trabajo y cerrar el editor.

Muestra/oculta el sistema de referencia del
panel.

Muestra/oculta el sistema de referencia de
la m�quina.

Muestra/oculta los visualizadores viguetas.

Muestra el panel en primer plano.

Muestra la mesa de trabajo en un gr�fico
esquem�tico.

Activa/desactiva la visualizaci�n en
pantalla entera de la ventana.

Aumenta o reduce la imagen de la mesa de
trabajo:
- hacer clic en un punto presionando el
bot�n izquierdo del rat�n para aumentar la imagen;
- hacer clic en un punto presionando el
bot�n derecho del rat�n para reducir la imagen.
El zoom enfoca el punto se�alado con el
cursor del rat�n.

Traza un rect�ngulo arrastrando el cursor
del rat�n sobre la representaci�n gr�fica. Al soltar el rat�n, la zona
incluida en el rect�ngulo aumenta.

Aumenta la zona ocupada por el tablero.

Restablece las dimensiones originales de la
representaci�n gr�fica.

Controla si existe riesgo de choque.

Posiciona
autom�ticamente las ventosas (s�lo para mesas de travesa�os y ventosas).

Imprime la programaci�n de la mesa activa.

Muestra
informaci�n sobre el programa, el n�mero de versi�n y copyright.

Habilita el men� de ayuda en l�nea por
argumentos. En el cursor del rat�n aparece una flecha con un signo de
interrogaci�n. Al hacer clic en el punto deseado, el men� de ayuda muestra el
argumento relativo. Esta funci�n tambi�n se puede habilitar pulsando al mismo
tiempo las teclas [Shift]+[F1].

Muestra la posici�n abierta/cerrada del
separador de grados.
Barra de herramientas especiales

Corta el soporte seleccionado.

Copia el soporte seleccionado.

Abre la ventana para insertar el soporte
cortado o copiado.

Inserta un
soporte de la lista seleccionado desde el teclado.

Elimina el soporte seleccionado.

Activa/desactiva la rotaci�n del soporte
seleccionado.

Gira el soporte seleccionado de 180�.

Selecciona el
soporte anterior.

Selecciona el soporte siguiente.

Activa/desactiva la funci�n para insertar
juntas (s�lo para mesas multifuncionales).

Unir segmentos de juntas independientes pero
adyacentes para formar un perfil (s�lo para mesas multifuncionales).

Muestra la ventana de propiedades del
soporte o del tablero seleccionado.
Barra de estado
En la zona
izquierda de la barra de estado se describen las acciones de las opciones
del men� y de los botones de las barras al colocar el cursor del rat�n sobre
ellas.
A la derecha
est�n los campos que muestran las coordenadas del punto en el que se encuentra
el cursor del rat�n respecto al origen en tablero (OP) y al origen en m�quina
(OM).
En el extremo
derecho de la barra est�n los tres campos en los que se indican que las
siguientes teclas est�n activadas .
MA
Bloq May�s activado.
NUM
Bloq Num activado.
BS
Bloq Despl activado.

AP�NDICE
B. Variables y expresiones
Variables
En los programas, subprogramas y macros se
pueden definir hasta un m�ximo de 512 variables (v�ase la instrucci�n
L).
Las variables son
objetos que se utilizan para memorizar valores num�ricos, los cuales pueden ser
simplemente n�meros o bien el resultado de una expresi�n aritm�tica o l�gica;
los valores memorizables est�n comprendidos entre 1.7E-308 y 1.7E+308.
Cada variable posee un nombre un�voco, que se
elige en base a las siguientes reglas:
� no debe superar los 15 caracteres
� los caracteres pueden ser las letras del
alfabeto (min�sculas y/o may�sculas), los n�meros y el car�cter �_�
(underscore)
� el primer car�cter no puede ser un n�mero
Existen algunas variables predefinidas que se
pueden utilizar para leer las dimensiones de la pieza, el �rea de trabajo y
representar pi (estas variables no se pueden escribir):
DX
Dimensi�n en X.
DY
Dimensi�n en Y.
DZ
Dimensi�n en Z.
BX
Traslazione in X del
pezzo rispetto alla battuta.
BY
Traslazione in Y del
pezzo rispetto alla battuta.
BZ
Traslazione in Z del
pezzo rispetto alla battuta.
FLD
�rea de trabajo:

1=A, 2=B, 3=C, 4=D
12=AB, 21=BA, .., 41=DA
101=E, 102=F, 103=G,
104=H
112=EF,
121=FE, ..., 141=HE
201=I,
202=J, 203=K, 204=L
212=IJ, 221=JI, ...,
241=LI
301=M, 302=N, 303=O,
304=P
312=MN,
321=NM, ..., 341=PM
900 =
area 00, 901 = area 01
910 = area 10, 911 = area 11
PI
Pi-greco.
�ATENCI�N!
Una variable no definida toma el valor 0 si se usa en las
expresiones, pero se expresa como �no definida� si se usa como cota.
Expresiones
Las expresiones consisten en reglas para leer
el valor de los operandos y calcular nuevos valores mediante la aplicaci�n de
operadores.
Los operandos pueden ser valores constantes
(n�meros) y nombres de variables; los operadores son los convencionales con el
agregado de expresiones aritm�ticas y l�gicas. Las expresiones aritm�ticas dan
un resultado num�rico; las expresiones l�gicas dan un resultado l�gico del tipo
Verdadero o Falso. Xilog Plus considera el valor 0
(cero) como correspondiente a Falso y cualquier otro valor como correspondiente
a Verdadero; Xilog Plus genera
el valor 1 como Verdadero.
Las reglas de composici�n de las expresiones
clasifican los operadores en clases de precedencia; los operadores unarios
tienen la m�xima precedencia, siguen los operadores de multiplicaci�n, los de
adici�n, los de comparaci�n y los l�gicos.
La siguiente tabla
contiene la lista de operadores clasificados en niveles de precedencia. Las
l�neas separan los niveles; el m�ximo nivel de precedencia es el primero de la
lista.
-
Menos unario.
+
M�s unario.
DEF
Control definici�n variable/par�metro (0=no
definido,1=definido).
NDEF
Control definici�n variable/par�metro (0=
definido,1=no definido).
ABS
Valor absoluto.
ACOS
Arco coseno.
ASIN
Arco seno.
ATAN
Arco tangente.
COS
Coseno.
SIN
Seno.
TAN
Tangente.
RD
Redondeo hacia el valor entero inferior.
RU
Redondeo hacia el valor entero superior.
EXP
Exponencial.
LN
Logaritmo natural.
LOG
Logaritmo en base 10.
SQR
Ra�z cuadrada.
TLRAD
Radio m�ximo herramienta.
TLURAD
Radio �til herramienta.
TLLEN
Longitud herramienta.
TLULEN
Longitud �til herramienta.
TLROT
Sentido de rotaci�n herramienta (0=ninguno,
1=+, 2=-).
TLOPPSTX
Herramienta contrapuesta en X.
TLOPPSTY
Herramienta contrapuesta en Y.
NXTNUMTOTAL
(a,n)
Restituye el n�mero de la herramienta
sucesiva a n (n=1, ...96,
101...196, ..., 801, ..., 896) que pertenezca al grupo a (a=1...999). Si n=0, 100, 200, ..., 800 retorna el n�mero de la
primera herramienta que pertenece al grupo a. Un valor de retorno igual a 0 indica que no hay ulteriores
herramientas que pertenecen al grupo a.
_ORGVAL(1)
Restituye el valor del origen X.
_ORGVAL(2)
Restituye el valor del origen Y.
_ORGVAL(3)
Restituye el valor del origen Z.
HEADER(n)
Restituye los datos especificados en el
Encabezamiento del programa:
HEADER(1)
valor del par�metro DX;
HEADER(2)
valor del par�metro DY;
HEADER(3)
valor del par�metro DZ;
HEADER(4)
valor del par�metro -;
HEADER(5)
valor del par�metro C;
HEADER(6)
valor del par�metro T;
HEADER(7)
valor del par�metro R;
HEADER(8)
valor del par�metro *;
HEADER(9)
valor del par�metro V;
HEADER(10)
reservado;
HEADER(11)
valor del par�metro BX;
HEADER(12)
valor del par�metro BY;
HEADER(13)
valor del par�metro BZ.
RETV
(�NombreDeVariable�, Expresi�n).
Puede utilizarse en un subprograma o en una
macro para restituir un valor al subprograma/macro que llama. El valor
constituido por la Expresi�n se copia en la variable NombreDeVariable que
pertenece al subprograma/macro que llama. NombreDeVariable puede ser una
variable est�ndard (L), un par�metro (PAR), un alias (D). El operador retorna
0 si la variable NombreDeVariable no est� definida en el subprograma/macro
que llama o bien si no existe subprograma/macro que llama; 1 en caso
contrario.
Ejemplo:
...
L Pos = 1200
L Res = RET(�Alfa�, Pos*1000)
...
Si existe, la variable Alfa del
subprograma/macro que llama asume el valor 1200000.
El operador RETV puede aplicarse como m�ximo
una vez por cada variable, independientemente del subprograma/macro en el que
est� aplicado a la variable. Las variables ambiente no pueden en ning�n caso
ser modificadas por el operador RETV.
TLSERIES
Serie de pertenencia herramienta (0=ninguna,
1=X, 2=Y).
OPROG
Reservado.
FCKP(1)
Restituye el valor de la cara activada (F=1
� 2 � 3 � 4 � 5).
FCKP(2)��������
Regresa la correcci�n C programada
(0=no,1,2,3,13,23,31,32) (que puede ser diferente de la activada si la
primera est� programada en la mitad del perfil).
FCKP(3)
Restituye el valor del incremental K activo
(0=no, 1=X, 2=Y, 3=X+Y).
FCKP(4)��������
Restituye el valor del especular P activo
(0=no, 1=X, 2=Y, 3=X+Y, 10=G2G3, 11=X+G2G3, 12=Y+G2G3, 13=X+Y+G2G3).
FMAC
Reservado.
TMAC
Reservado.
ZMAC
Reservado.
TOOL
Detecta los datos del file de equipamiento
especificado en el programa corriente.
TOOL(n, 1)���
Restituye a tipo (0=N.D., 1=P, 2=F, 3=D,
4=T, 5=S) de la herramientan (n=1,�, 96,101,�,196,�,801,�,896).
TOOL(n,
2)
Restituye al subtipo (0=N.P., 1=L, 2=P,
3=S).
TOOL(n,
3)
Restituye al n�mero almac�n.
TOOL(n,
4)
Restituye al tipo almac�n.
TOOL(n,
5)
Restituye al alojamiento almac�n.
TOOL(n,
6)
Restituye el n�mero herramienta contrapuesta
en X.
TOOL(n,
7)
Restituye el n�mero herramienta contrapuesta
en Y.
TOOL(n,
8)
Restituye la serie (0=N.D., 1= eje X, 2= eje
Y).
TOOL(n,
9)
Restituye al radio.
TOOL(n,
10)
Restituye al radio �til.
TOOL(n,
11)
Restituye a la longitud/al radio hoja.
TOOL(n,
12)
Restituye a la longitud �til.
TOOL(n,
13)
Restituye al sentido de rotaci�n (0=N.D.,
1=+, 2=-).
TOOL(n,
14)
Restituye la direcci�n de trabajo (0=N.D.,
1=+, 2=-).
TOOL(n,
15)
Restituye el n�mero de grupo.
TOOL(n,
16)
Restituye la cara de trabajo
(0=todas,1=F1,..,5=F5).
TOOL(n,
17)
Restituye la altura barrena.
TOOL(n,
18)
Restituye la velocidad de giro est�ndar.
TOOL(n,
19)
Restituye la velocidad de giro m�xima.
TOOL(n,
20)
Restituye la velocidad est�ndar.
TOOL(n,
21)
Restituye la velocidad m�xima.
TOOL(n,
22)
Restituye la velocidad G0/B.
TOOL(n,
23)
Restituye el offset X.
TOOL(n,
24)
Restituye el offset Y.
TOOL(n,
25)
Restituye�
el offset Z.
TOOL(n,
26)
Restituye el offset D.
TOOL(n,
27)
Restituye el offset R.
TOOL(n,
28)
Restituye el �ngulo A (B para tipo Disco).
TOOL(n,
29)
Restituye la dimensi�n.
TOOL(n,
30)
Restituye el coeficiente de desgaste en
longitud.
TOOL(n,
31)
Restituye el coeficiente de desgaste en
di�metro.
TOOL(n,
32)
Restituye el m�ximo desgaste en longitud.
TOOL(n,
33)
Restituye el m�ximo desgaste en di�metro.
STRCMP(s1,s2)

Compara la l�nea s1 con la l�nea s2 (s�lo en
los ciclos fijos).

Restituye: -1 si s1 < s2; 0 si s1=s2; 1
si s1 > s2. s1 y s2 pueden ser cadenas inmediatas entre �pices dobles o
bien la variable parent pN.
FIELD(a,1)���
Restituye el valor de la especularidad X del
campo de trabajo a (los valores admitidos para a son todos aquellos que puede
asumir lavariable FLD).
FIELD(a,2)
Restituye el valor de la especularidad Y del
campo de trabajo a.
FIELD(a,3)
Restituye el n�mero de travesa�os del campo
de trabajo a.
FIELD(a,4)
Restituye el n�mero de la primera viga del
campo de trabajo a.
FIELD(a,5)
Restituye el valor del origen X del campo de
trabajo a.
FIELD(a,6)
Restituye el valor del origen Y del campo de
trabajo a.
FIELD(a,7)
Restituye el valor del origen Z del campo de
trabajo a.
FIELD(a,8)
Restituye la dimensi�n X del campo de
trabajo a.
FIELD(a,9)
Restituye la dimensi�n Y del campo de trabajo
a.
FIELD(a,10)
Restituye el offset Y del centro tope.
FIELD(a,11)
Restituye el offset X de los topes de la
superficie multifuncional.
FIELD(a,12)
Restituye el offset Y de los topes de la
superficie multifuncional.
FIELD(a,13)
Restituye el origen X con tope m�vil OFF.
FIELD(a,14)
Restituye la anchura del �rea con tope m�vil
OFF.
FIELD(a,15)
Opcional escal�n.
FIELD(a,16)
Topes frontales y laterales unidos.
FIELD(a,17)
Gesti�n autom�tica offset tope m�vil.
FIELD(a,18)
Recorrido del separador escalones.
EPL_TV(t,v,d)
Restituye informaciones en la mesa
transversal y ventosas programado mediante el Editor de las mesas de trabajo.

1. Si t
y v est�n en 0: se restituyen
datos generales.
Ejemplo:
EPL_TV(0,0,1)
indica la posici�n de la barra central continuada
referida al origen de la pieza.
2. Si t
est� comprendido entre 1 y el �ndice del �ltimo travesa�o:
a) si v
est� en 0, se restituyen los datos del travesa�o t;
b) si v
est� comprendido entre 1 y el �ndice del �ltimo dispositivo, se restituyen
los datos del dispositivo v del travesa�o t.

^
Seleccionar herramientas (s�lo para macro).

**
Potencia.

*
Multiplicaci�n.
/
Divisi�n.

MOD
Resto de la divisi�n (m�dulo).

+
Suma.
-
Resta.

<
Menor.
<=
Menor o igual.
>
Mayor.
>=
Mayor o igual.
=
Igual.
<>
Diverso.

NOT
Negaci�n l�gica.

AND
And l�gico.
OR
Or l�gico.
XOR
Xor l�gico.

Las reglas de precedencia pueden ser
modificadas, puesto que cada expresi�n encerrada entre par�ntesis es
considerada independientemente del operador precedente y del sucesivo.
Ejemplos:
����������� L
BASE = 300
����������� L
CIMA = 200
����������� L
LADO = 200
����������� L
CENTRO = 50
����������� L
L1 = DY-(LADO*2)-CENTRO
����������� L
L1 = L1/2
����������� L
R1 = CENTRO*SIN 45
����������� L
R2 = (DY/2)-(LADO+CENTRO+R1)
����������� L L2 = DX-BASE-CIMA-R2-R1
����������� L L4 = L1-CENTRO
����������� L L3 = L2-L4

AP�NDICE
C. Formatos de archivo
Formatos
CFG
Formato de
los archivos de configuraci�n de Xilog Plus.
CNC
Formato de los programas ISO. Los programas
ISO tambi�n se pueden editar con un editor ASCII externo. En algunas m�quinas
con controlador NUM�, los programas ISO se pueden gestionar directamente (v�ase el apartado
Gesti�n directa de los programas ISO del Ap�ndice
M: Notas). Los programas en formato CNC se pueden importar con formato PGM
(s�lo si no contienen instrucciones de salto) a la ventana Abrir archivo.
DXF
Formato de los programas generados por CAD.
Los archivos DXF se pueden importar al editor de Xilog Plus en formato PGM y XXL (v�ase el cap�tulo 6.6 �
Importaci�n de un archivo DXF).
EPL
Formato de los archivos
del Editor de mesas de trabajo.
FRZ
Formato de los mix interrumpidos durante la
ejecuci�n en modalidad Autom�tico mix (v�ase el Manual de uso del Panel de la
m�quina). Estos archivos se puede ejecutar, pero no se pueden editar.
MIX
Formato est�ndar de los mix.
PGM
Formato est�ndar de los programas. Los
programa en formato PGM se pueden exportar en formato XXL a la ventan Abrir archivo; en esta ventana es
posible convertir la unidad de medida de un archivo PGM de mil�metros a pulgadas
y viceversa.
TLG
Formato de los archivos de equipamiento.
TWN
Formato de los archivos del Editor de los
programas m�ltiples.
XXL
Formato ASCII de los programas. Los programas
guardados con este formato se pueden editar en cualquier editor de texto. Los
archivos con formato XXL se pueden guardar en formato PGM.
Ventana para abrir y convertir archivos
La ventan Abrir archivo de Xilog Plus se diferencia de la
ventana est�ndar de Windows por al presencia de algunos botones con funciones
espec�ficas.
� ?: visualiza
la Gu�a en l�nea del editor de Xilog
Plus;
� MM/IN: convierte la unidad de medida de un archivo PGM, de mil�metros a
pulgadas y viceversa (se activo s�lo al seleccionar Programas en el
campo Tipo
archivo). Los n�meros seguidos del car�cter # que
se introducen en los campos num�ricos de una instrucci�n no pueden ser
convertidos.
� IMPORTAR: convierte un archivo CNC en un archivo PGM (se activa s�lo al
seleccionar Programas ISO en el campo Tipo archivo).
� EXPORTAR: convierte un archivo PGM en un archivo XXL (activo s�lo al
seleccionar Programas en el campo Tipo archivo).
� INVIA A: permite copiar el programa seleccionado en otro directorio del
ordenador o en una unidad externa (por ejemplo, en un disquete).
WinXiso
El programa WinXiso transforma un programa
creado en formato ASCII (con extensi�n XXL) en un programa en formato PGM, y
viceversa.
Desde la versi�n 1.1 de WinXiso (disponible
inicialmente en la distribuci�n de Xilog V2.01.957) se puede tambi�n realizar
la conversi�n de los equipamientos de herramientas para volverlos compatibles
con las versiones anteriores de�
XilogPlus.
M�s precisamente, WinXiso 1.1 permite realizar
las siguientes conversiones:
- Conversi�n de equipamientos de 96
herramientas en formato XML [TLG-V2.1] (utilizado por Xilog en la versi�n
2.01.xxx) en equipamientos de 999 herramientas en formato no XML [TLG-V2]
(utilizado en xilog a partir de la versi�n 1.13.993)
- Conversi�n de equipamientos de 999
herramientas en formato no XML [TLG-V2] en equipamientos de 96 herramientas en
formato no XML [TLG-V1] (utilizado en xilog pos todas las versiones anteriores
a la 1.13.993)
WinXiso se puede utilizar directamente o
activar desde un programa externo, por ejemplo desde un Cad o Cam. El programa
externo puede activar WinXiso por medio de funciones API, como, por ejemplo
WinExec y ShellExecute.
►Para iniciar directamente WinXiso, haga clic en el men� Start/TODOS LOS
PROGRAMAS/GRUPO Scm/WinXiso.
El programa abre la siguiente ventana:
Haga clic en el bot�n
Es posible seleccionar el programa en formato
XXL a compilar, la macro (en formato PGM) a decompilar o el archivo de
equipamiento en formato TLG ( o .TL1, .TL2, .TL� para las m�quinas multigrupo
como las Ergon) a convertir. Despu�s de haber seleccionado el archivo, es
suficiente hacer clic en el bot�n
para iniciar la
compilaci�n/decompilaci�n/conversi�n.
En la conversi�n de los archivos TLG, la regla
seguida es aquella de producir el equipamiento en el formato anterior al
formato del equipamiento pasado al convertidor.
Se obtienen por tanto dos tipos de
conversiones autom�ticas:
- si el equipamiento pasado es de 96
herramientas en formato XML [TLG-V2.1] � ser�
generado un equipamiento de 999 herramientas en el formato no XML [TLG-V2]
- si el equipamiento pasado es de
herramientas en formato no XML [TLG-V2] � ser�
generado un equipamiento de 96 herramientas en el formato no XML [TLG-V1]
Existen algunos par�metros para configurar el
funcionamiento del programa. Estos par�metros son c�digos que est�n precedidos
por el s�mbolo �-� y que se pueden insertar despu�s del nombre del programa en
la casilla Command.
-o <nomefile>
Convertir un programa con formato ASCII
(extensi�n XXL) en un programa con formato PGM y asignar nombre
<nomefile> (obligatorio).
-x <nomefile>
Convertir un programa con formato PGM en un
programa con formato ASCII (extensi�n XXL).
Esta opci�n excluye las opciones -o y -l.
-i <nomefile>
Generar un archivo con formato ASCII
(extensi�n .INF) con los resultados de la traducci�n:
- [LINES]=<n�mero de instrucciones
convertidas>
- [ERRORS]=<n�mero de errores
detectados>
-l <nomefile>
Generar el listado del programa con formato
ASCII (extensi�n .LST).
-s
No abrir ventanas en la pantalla.
-v
Junto con la opci�n �x, compilar o
descompilar la secci�n EPL de un programa. Para descompilar, seleccionar el
archivo .PGM: el sistema crea un archivo.XXL y otro .EPL por separado. Para
compilar, seleccionar un archivo .XXL e insertar despu�s de la opci�n -v el
nombre del archivo .EPL. El sistema crea un archivo .PGM que contiene la secci�n
EPL.
-t
Junto con la opci�n -l, a�adir al listado
del programa la tabla de s�mbolos.
-f <bitmap>
A�adir al programa la imagen bitmap
especificada.
� WinXiso siempre intenta traducir los
archivos ASCII en PGM, salvo que se especifique la opci�n -x.
� <nomefile> puede ser cualquier
nombre de archivo compuesto por 8 caracteres como m�ximo m�s los 3 caracteres
de la extensi�n. En algunos casos puede estar precedido por una ruta. En la
opci�n -o es obligatorio indicar el nombre del archivo; en el resto de opciones
es facultativo. Si no se especifica, el sistema vuelve a utilizar el nombre del
archivo seleccionado cambiando la extensi�n.
Ejemplo de solicitud de WinXiso desde una
aplicaci�n externa:
...��������
WinExec("c:\\tools\\WinXiso.exe
..\\test\\sample.xxl -s -i",SW_SHOW);
...
�����������
Cuando el control llega a este punto la
traducci�n ha terminado y es posible controlar el archivo ..\test\sample.inf.

AP�NDICE D. Programaci�n de la campana de
aspiraci�n
Campana neum�tica
a)
Campana programada trabajando (par�metro E)
E=-1
Campana alta
E=0
Campana alta
E=1
Campana baja en posici�n 1
E=2
Campana baja en posici�n 2
E=3
Campana baja en posici�n 3
E=4
Campana baja en posici�n 4
El n�mero de posiciones m�ximo corresponde al
n�mero de cuotas (en secuencia) distintas de cero programadas en la secci�n
�Hood� del archivo de configuraci�n axis.cfg y depende del tipo de m�quina.
b)
Campana no programada trabajando
Se optimiza la posici�n en funci�n del trabajo
que se est� ejecutando, de las caracter�sticas de la herramienta utilizada y de
las cuotas programadas para la campana en la secci�n �Hood� del archivo de
configuraci�n axis.cfg.
Campana con motor
La cuota programada en el par�metro E
corresponde con la cuota real (en mm o pulgadas) de bajada de la campana. Atenci�n: en este caso no se realizan
controles antichoque de la campana.
Si E no est� programado, la campana se
posiciona de modo autom�tico en funci�n del trabajo que se est� realizando y de
las caracter�sticas de la herramienta utilizada.
Campana externa
cabeza Basic RD260 - Prisma
Sobre la cabeza Basic de la Record 260 Prisma,
adem�s de la campana est�ndar (con motores de cota programable), existe tambi�n
otra segunda campana externa de posicionamiento neum�tico (ON-OFF).
A) Campana externa (OFF).
B) Campana interna con cota de
posicionamiento programable.
C) Campana externa (ON).
La programaci�n de la posici�n de esta campana
se obtiene interviniendo directamente sobre el valor del par�metro E.
E=0
Ambas campanas est�n excluidas.
E=cota
deseada
La campana externa est� excluida (OFF); la
campana est�ndar se sit�a a la cota deseada.
E=no
programado
La campana externa est� excluida (OFF); la
campana est�ndar se sit�a a una cota calculada en funci�n de las dimensiones
de la herramienta presente en el mandril.
E=-1
La campana externa est� programada baja
(ON); la campana est�ndar est� excluida.
E=-2
La campana externa est� programada baja
(ON); la campana est�ndar se sit�a a una cota calculada en funci�n de las
dimensiones de la herramienta presente en el mandril.
�

AP�NDICE E.
Programaci�n de los topes m�viles
Los topes m�viles se programan por medio del
campo T de la instrucci�n H (barra TV ON/OFF).
Por convenci�n, la posici�n de reposo (OFF) de
todos los topes m�viles se encuentra fuera de la zona de trabajo; normalmente
(siempre por convenci�n) las barras est�n en posici�n OFF. El PLC efect�a todos
los controles antes de iniciar el posicionamiento de las barras. En el caso de
topes m�viles� manuales, el
accionamiento equivale al control de posici�n.
El tope m�vil accionado y el control de la
posici�n de reposo (OFF) de los restantes topes efectuados por el PLC dependen
de la configuraci�n de la m�quina y de la zona del programa que se est� ejecutando.
M�quina sin cero
central (2 zonas de trabajo: A,B; E,F;...) y con dos topes m�viles
Si la zona de referencia es A o E o I o M, se
acciona la barra TV que est� a la izquierda de la m�quina (mirando la m�quina
por delante); si la zona de referencia es B o F o J o N, se acciona la barra TV
que est� a la derecha de la m�quina (mirando la m�quina por delante).
En caso de zonas sencillas, se excluye la barra TV que no se ha accionado.
Ejemplos:
Zona
TV izq.
TV der.
A
Activa
-
B
-
Activa
En caso de zonas dobles (a lo largo de toda la superficie de la m�quina), se
acciona la barra TV de la zona de referencia (que corresponde a la primera
letra de la lista de las zonas). La otra barra TV ha de estar fuera de la zona
de trabajo. Si no lo est�, el PLC visualiza un mensaje de error antes de
ejecutar el programa.
Ejemplos:
Zona
TV izq.
TV der.
AB
Activa
Control
OFF
BA
Control
OFF
Activa
M�quina con cero
central (4 zonas de trabajo: A, B, C, D; E, F, G, H;...) y cuatro topes m�viles
Con
zonas est�ndar
Para las zonas de referencia A o E o I o M e D
o H o L o P sin referencia central, consultar el apartado anterior en el que se
describen las zonas D o H o L o P en lugar de B o F o J o N. En concreto la
condici�n de la barra TV1 corresponde con la condici�n de la barra TV arriba
descrita. Si la zona es sencilla, se ignora la programaci�n de la barra TV2.
En las zonas de referencia B o F o J o N y C o
F o J o N (que comparten una referencia central) se acciona siempre la barra
TV2 y la condici�n de la barra TV1, si la zona es sencilla, queda excluida.
Ejemplos:
Zona
TV1 izq.
TV2 izq.
TV2 der.
TV1 der.
A
Activa
-
-
-
B
-
Activa
-
-
C
-
-
Activa

D
-
-
-
Activa
Si la zona es doble, se acciona la barra TV de
la zona de referencia (TV1 o TV2 seg�n el nombre de la zona). La otra barra TV
(TV1 o TV2 opuesta a la primera) ha de estar fuera de la zona de trabajo. Si no
lo est�, el PLC visualiza un mensaje de error.
Ejemplos:
Zona
TV1 izq.
TV2 izq.
TV2 der.
TV1 der.
AB
Activa
Control
OFF
-
-
BA
Control
OFF
Activa
-
-
CD
-
-
Activa
Control
OFF
DC
-
-
Control
OFF
Activa
Si la zona es m�ltiple (comprende toda la
m�quina), consultar el apartado anterior en el que se describen las zonas
dobles con D o H o L o P en lugar de B o F o J o N, con los topes TV2 fuera de
la zona de trabajo. En este caso, para efectuar el c�lculo sobre el movimiento
de las barras s�lo se tienen en cuenta los l�mites de carrera programados en el
archivo de configuraci�n supports.cfg.
Ejemplos:
Zona
TV1 izq.
TV2 izq.
TV2 der.
TV1 der.
AD
Activa
Control
OFF
Control
OFF
Control
OFF
DA
Control
OFF
Control
OFF
Control
OFF
Activa
Con zonas virtuales
(AB, CD, BA, DC, AD, DA; EF, GH, FE, HG, EH, HE;...)
An�logo a las zonas est�ndar, pero en este
caso son siempre zonas combinadas.

AP�NDICE F. M�quinas Ergon
Este ap�ndice del manual est� dedicado al uso
de Xilog Plus instalado sobre m�quinas de tipo Ergon. Debido a la configuraci�n
especial de este tipo de taladradoras-fresadoras, ha sido necesario introducir
nuevos par�metros de configuraci�n, nuevas instrucciones y nuevas reglas de
programaci�n.
Para una mejor comprensi�n del contenido de
este documento, h�gase referencia al siguiente esquema, que representa una
m�quina Ergon con cuatro ejes zeta (o grupos) independientes, sobre cada uno de
los cuales se encuentra montado un electromandril como cabeza principal y un
grupo (cabeza secundaria), que puede ser de varios tipos (ej.: taladradora,
Universal, cuchilla,�).
Fig. 1
Equipamiento
El herramental de una Ergon es an�logo a un
herramental est�ndar, a excepci�n de que en el primero se visualizan varios
grupos de par�metros para las herramientas fijas y externas, tantos como zetas
(grupos) independientes componen la m�quina.
Fig. 2
Abriendo el �rbol correspondiente a cada
grupo, se visualizaran 96 herramientas programables distintas. Las herramientas
del grupo n�1, se caracterizan por la posibilidad de modificar todos sus
par�metros, tanto si se trata de herramientas fijas (es decir, de cabezas de
taladrado) como externas (es decir, cabezas mandril). Observar, en la figura
que se ofrece a continuaci�n, el ejemplo correspondiente a las herramientas
externas para el grupo n�1:
Fig. 3
Sin embargo, para las herramientas de los
grupos distintos al n�1, s�lo se podr� modificar una parte de los par�metros, o
sea, aquellos que, para cada dato de la herramienta, cambian seg�n el
grupo-zeta al que pertenecen.
En la figura siguiente se muestra el ejemplo
de la herramienta externa n�1 para el grupo n�2, en dicha figura puede
observarse que s�lo algunos de los par�metros existentes pueden modificarse,
mientras todos los dem�s (los que est�n en gris), son herencia de los
programados por la herramienta n�1 en el grupo n�1. Obviamente, para configurar
una herramienta nueva, antes hay que editar sus par�metros correspondientes al
grupo n�1 (aunque para dicho grupo la herramienta en cuesti�n podr�a no estar
presente f�sicamente) y despu�s modificar los par�metros, no comunes a todos
los grupos, para los grupos en los que la herramienta est� f�sicamente
presente.
Fig. 4
Por ejemplo, si se desea a�adir la herramienta
externa n�5 al herramental, se seleccionar� la posici�n n�5 del grupo n�1 y se
modificar�n todos sus par�metros a partir del tipo de herramienta.
Tras concluir la parametrizaci�n de la
herramienta en el grupo n�1, se proceder� a modificar los par�metros
espec�ficos en los otros grupos. Si la herramienta no est� presente en un
determinado grupo, no es obligatorio introducir sus par�metros, excepto en caso
de que se trate del grupo n�1, para el cual la programaci�n de los par�metros
herramienta es obligatoria.
Para memorizar los herramentales asociados a
los varios grupos-zeta, el sistema genera tantos archivos como grupos-zeta
tiene la m�quina. Si por ejemplo el herramental es �def� y la m�quina tiene 4
grupos-zeta, entonces el sistema generar� y administrar� los siguientes 4
archivos:
def.tlg
Equipamiento �def� para las herramientas
(fijas y externas) del grupo n�1.
def.tl2
Equipamiento �def� para las herramientas (fijas
y externas) del grupo n�2.
def.tl3
Equipamiento �def� para las herramientas
(fijas y externas) del grupo n�3.
def.tl4
Equipamiento �def� para las herramientas
(fijas y externas) del grupo n�4.
�����������
Lo mismo ocurre para la configuraci�n de los
husos de las taladradoras (archivo de
configuraci�n spindles.cfg); si la m�quina tiene 4 grupos-zeta, entonces
el sistema generar� y administrar� los siguientes archivos:
spindles.tlg
Parametrizaci�n husos taladradora presente
en el grupo n�1.
spindles.tl2
Parametrizaci�n husos taladradora presente
en el grupo n�2.
spindles.tl3
Parametrizaci�n husos taladradora presente
en el grupo n�3.
spindles.tl4
Parametrizaci�n husos taladradora presente
en el grupo n�4.
Esto significa que para llevar a cabo un
backup correcto y completo de los herramentales, as� como una correcta
configuraci�n de la m�quina, es necesario guardar siempre estos archivos (y no
s�lo el archivo def.tlg o
spindles.cfg).
Programaci�n
Las reglas de programaci�n b�sicas de un
programa PGM son las mismas que las de cualquier otra m�quina SCM controlada
mediante sistema Xilog Plus. Sin embargo, por las caracter�sticas, la m�quina
Ergon precisa un mecanismo que permita indicar, para cada trabajo a realizar
con el programa, no s�lo la herramienta que debe utilizarse, si no tambi�n
cu�ntas cabezas deben trabajar juntas, caso que se deba realizar un trabajo
sobre varias piezas al mismo tiempo y por lo tanto una sincronizaci�n de varias
cabezas operadoras. En el caso utilizado como ejemplo para este documento,
puede que se desee trabajar con los electromandriles principales de los
grupos-zeta 1 y 2 o bien con las taladradoras de los grupos-zeta 2 y 4 etc.
Para localizar estas combinaciones, es suficiente especificar, en el campo
herramientas (T) de cualquier instrucci�n operativa PGM (ej.: XB, XBR, XG0�),
una lista de varias herramientas, cada una de las cuales representa la cabeza
que debe trabajar y la herramienta requerida para dicho trabajo.
Con el fin de facilitar la asociaci�n nem�nica
del n�mero de cabeza a programar con el n�mero de grupo-zeta al que pertenece
la cabeza, la configuraci�n de dichas cabezas (secci�n �pheads�) se realiza de
modo que el n�mero de la herramienta a utilizar en las instrucciones operativas
siga la siguiente regla:
� de 100
a 900 se indican las cabezas
principales de la m�quina;
� de 1100
a 1900 se indican las cabezas
secundarias de la m�quina (primer grupo);
� de 2100
a 2900 se indican las cabezas
terciarias de la m�quina (segundo grupo).
De este modo el valor de las centenas del
n�mero de la herramienta representa el grupo-zeta que se desea localizar,
mientras el valor de los millares representa el tipo de cabeza que se desea
utilizar (0: principal; 1: primer grupo; 2: segundo grupo).
Excepto en casos especiales, que pueden presentarse
con m�quinas especiales, esta convenci�n deber� considerarse como el est�ndar.
Ejemplo de
programa.
Pongamos, por ejemplo, que se desean trabajar
dos piezas contempor�neamente, colocadas entre s� a la distancia existente
entre los grupos-zeta 1 y 3 (damos por supuesto que dicha distancia es igual la
distancia entre los grupos-zeta 2 y 4); se desea, por ejemplo, realizar un
fresado con la herramienta 5 de los electromandriles principales de los
grupos-zeta 1 y 3 y un taladrado con los husos 7 y 8 de las taladradoras
auxiliares de los grupos-zeta 2 y 4. Supongamos asimismo, que se desea trabajar
sobre la mesa Y, con referencia de origen piezas abajo a la izquierda (�rea
AB). La disposici�n de las dos piezas ser� como la que se indica en la fig. 5:
Fig. 5
Tal y como indican las flechas, en este
trabajo participar�n los dos pares de cabezas 100/300 (electromandriles) y
1200/1400 (taladradoras).
Haciendo referencia a las fig.1 y 5, ser�
suficiente escribir, en el programa, las siguientes instrucciones:
H DX=� DY=� DZ=� BX=� BY=� BZ=�
/�def�
XG0 X=� Y=� Z=� T=305 105
XG1 X=� Y=� Z=�
XB X=� Y=� Z=� T=1407 1408 1207 1208
Analizando las dos listas de herramientas que
aparecen junto con las instrucciones XG0 y XB, tenemos que :
� T=305 105. El sistema entiende que se
requiere el uso sincr�nico de las cabezas 100 y 300 que, en el ejemplo en
curso, identifican el mandril principal respectivamente del grupo-zeta 1 y 3 y
que para ambas es necesario montar la herramienta 5, cuyas caracter�sticas se
describen en el grupo de las herramientas externas del herramental def.tlg
(elegido en el header del programa); finalmente que todas las cotas X e Y
indicadas para este trabajo se refieren a la cabeza 300, puesto que la primera
herramienta de la lista es 305.
� T=1407
1408 1207 1208. El sistema entiende que se requiere el
uso sincr�nico de las cabezas 1200 y 1400 que, en el ejemplo en curso,
identifican la taladradora auxiliar (secundaria) respectivamente del grupo-zeta
2 y 4 y que para ambas se requiere la extracci�n de los husos 7 y 8 cuyas
caracter�sticas se describen en el grupo de las herramientas fijas del
herramental def.tlg (elegido en el header del programa) y finalmente que todas
las cotas X e Y indicadas para este trabajo se refieren a la cabeza 1400, puesto
que la primera herramienta de la lista es 1407.
Es importante subrayar que en el caso de
electromandriles para las cabezas operadoras pueden especificarse varios
n�meros de herramienta, mientras en el caso de taladradoras es obligatorio que
para las cabezas programadas para trabajar sincr�nicamente se especifiquen los
mismos husos. As� pues, se admite la instrucci�n� XG0 X=�Y=�Z=�T=305 121,
pero NO la instrucci�n XB X=�Y=�Z=�T=1407
1408 1207 1215.
A tal punto es �til analizar el comportamiento
de la m�quina respecto al movimiento en X/Y/Z de las cabezas sincronizadas, en
relaci�n con la programaci�n que se realiza.
Movimiento en Z
Examinemos el trabajo realizado con los dos
electromandriles, el cual debe efectuarse con la instrucci�n XG0 X=�Y=�Z=�T=305
105. Supongamos que la herramienta 5 es una fresa de dos ranuras, que la
herramienta montada en la cabeza 100 tiene 80 mm. de longitud y la montada
sobre la cabeza 300 es de 80,5 mm. En tal caso, antes de iniciar a trabajar la
pieza, la cabeza 300� realizar� un
movimiento vertical (eje Z3) de 0.5 mm. hacia arriba, de modo que las �puntas�
de las dos herramientas, montadas sobre las dos cabezas 100 y 300, queden
perfectamente alineadas (la sincronizaci�n de dos o m�s cabezas siempre se
efect�a manteniendo sujeta la cabeza que pertenece al grupo-zeta de n�mero m�s
bajo y moviendo las otras cabezas verticalmente sobre el propio eje Z). Despu�s
de esta operaci�n, todas las instrucciones del programa que requieran
movimientos en Z, tendr�n como efecto el movimiento contempor�neo de las
cabezas 100 y 300.
Lo mismo vale para las cabezas de taladrado
1200 y 1400, exceptuando las taladradoras, en las que, actualmente, el PLC no
realiza la alineaci�n vertical (en Z). En general cabe tener presente que
cuando se trabaja con cabezas distintas de electromandriles (taladradoras,� Universal, �) el PLC realiza siempre la
sincronizaci�n, pero no la alineaci�n en Z, en funci�n de las distintas
longitudes de las herramientas montadas.
Movimiento en X e Y
Tras la sincronizaci�n y la alineaci�n en Z de
las cabezas, el desplazamiento en X e Y se realiza tomando, como cabeza de
referencia, la primera que aparece en la lista de herramientas. As� pues, para
el trabajo XG0 X=�Y=�Z=�T=305 105, el sistema calcular� todas las cotas X/Y haciendo
referencia a la cabeza 305. Obviamente, si las dos� piezas situadas sobre la mesa de trabajo est�n alineadas en Y y
su distancia en X es igual a la distancia entre ejes de las cabezas 100 y 300,
los trabajos realizados por la cabeza 300 sobre la pieza P1 y por la cabeza 100
sobre la pieza P2 (v�ase fig. 5), ser�n absolutamente id�nticos.
Lo mismo vale para los trabajos realizados con
cabezas de taladrado; as� pues, para el trabajo� XB X=�Y=�Z=�T=1407 1408 1207 1208, tras la sincronizaci�n de las
cabezas 1200 y 1400 (no alineaci�n � v�ase arriba), todos los movimientos en
X/Y ser�n efectuados con referencia al huso 7 de la cabeza 1400, puesto que la
primera herramienta de la lista es 1407. El resultado ser�, una vez m�s, el de
dos trabajos absolutamente id�nticos, realizados por la cabeza 1400 sobre la
pieza P1 y por la cabeza 1200 sobre la pieza P2.
Instrucci�n SET
TWIN
Para agilizar la programaci�n, sobretodo en
los trabajos realizados con cabezas de taladrado, puede utilizarse la
instrucci�n SET en el par�metro TWIN para indicar cuales son los grupos-zeta
que deber�n trabajar en sincr�nico (v�ase: instrucci�n SET).
Por ejemplo, el programa:
H DX=� DY=�
DZ=� BX=� BY=� BZ=� /�def�
XG0 X=� Y=� Z=� T=305 105
XG1 X=� Y=� Z=�
XB X=� Y=� Z=� T=1407 1408 1207 1208
se transformar�a del siguiente modo
H DX=� DY=�
DZ=� BX=� BY=� BZ=� /�def�
SET
TWIN=13
XG0 X=� Y=� Z=� T=305
XG1 X=� Y=� Z=�
SET
TWIN=24
XB X=� Y=� Z=� T=1407 1408
Pr�cticamente, el uso de la TWIN no obliga a
especificar en el campo T la lista de las herramientas de todas las cabezas que
deben trabajar en sincr�nico, ser� suficiente indicar la herramienta (en caso
de electromandril) o de los husos (en caso de taladradora) s�lo para la cabeza
�master�, o bien para la cabeza respecto a la cual se elaboran las cotas del
programa.
Para aclarar la utilidad de la SET TWIN,
supongamos que se desea trabajar con las taladradoras de los grupos 2 y 4 y que
se quieren utilizar los husos 1, 2, 3, 4, 5, 6 y 7. Siguiendo el primer modo de
programaci�n presentado, el programa asumir� esta forma:
H DX=� DY=�
DZ=� BX=� BY=� BZ=� /�def�
XB� T=1401
1402 1403 1404 1405 1406 1407 1201 1202 1203 1204 1205 1206 1207
Sin embargo, utilizando la SET TWIN, el
programa asumir�a esta forma:
H DX=� DY=�
DZ=� BX=� BY=� BZ=� /�def�
SET
TWIN=24
XB� T=1401
1402 1403 1404 1405 1406 1407
La comodidad en el uso de la SET TWIN crece al
aumentar el n�mero de cabezas que se desean sincronizar y el n�mero de husos
(en el caso de taladradoras) que se desean usar.
Instrucci�n SET TAU
La instrucci�n SET TAU permite controlar el
palpador montado en los cabezales electromandril. En el caso de las m�quinas
Ergon, el uso de esta instrucci�n sigue reglas especiales.
�SET TAU = 0
Si se introduce en el programa, tras por lo
menos un trabajo que requiere el uso del palpador, informa el sistema que a
partir del trabajo sucesivo no ser� solicitada la operaci�n de palpaci�n.
El resultado se traduce a nivel operativo
seg�n la casu�stica que se muestra a continuaci�n:
- Caso de cambio herramienta presente
SET TAU=1
XG0 T=101
�
SET TAU=0
XG0 T=102
El segundo trabajo
requiere el cambio herramienta, por tanto dado el TAU=0 mencionado previamente,
en la parte anterior del cargo de la herramienta n�2 en la cabeza, no ser�
introducido el palpador y la ganancia de los operadores din�micos ser�
desactivada.
- Caso de cambio herramienta ausente
SET TAU=1
XG0 T=101
�
SET TAU=0
XG0 T=101
opp.
XG0 T=102
(herramienta 2 incorporado a herramienta 1)
El segundo trabajo NO
requiere un cambio herramienta, por tanto, dado el TAU=0 previamente
especificado, sucede que:
1. si la clave $GEN_GAINZERO_PALPOFF
(Nci.cfg) vale 0, el palpador no ser� desconectado
f�sicamente, sino que ser� solamente desactivada la ganancia de los operadores
din�micos. El efecto que se produce es trabajar con el palpador conectado sin
correcciones din�micas sobre el eje Z debidas a posibles irregularidades de la
superficie de la pieza.
2. si la clave $GEN_GAINZERO_PALPOFF
(Nci.cfg) vale 1, el palpador ser� desconectado
f�sicamente, adem�s de la desconexi�n de la ganancia de los operadores
din�micos. El efecto que se produce es de trabajar sin el palpador conectado y
sin correcciones din�micas sobre el eje Z debidos a posibles irregularidades de
la superficie de la pieza.
SET TAU = -1
Si se introduce en el programa, tras por lo
menos un trabajo que requiere el uso del palpador, informa el sistema que a
partir del trabajo sucesivo no ser� solicitada la operaci�n de palpaci�n.
El resultado se traduce a nivel operativo
seg�n la casu�stica que se muestra a continuaci�n:
- Caso de cambio herramienta presente
SET TAU=1
XG0 T=101
�
SET TAU=-1
XG0 T=102
El segundo trabajo
requiere un cambio herramienta, por tanto, dado el TAU=-1 previamente
especificado, en la parte anterior del cargo de la herramienta n�2 en la
cabeza, no ser� introducido el palpador y la ganancia de los operadores
din�micos ser� desactivada (id�ntico a TAU=0).
- Caso de cambio herramienta ausente
SET TAU=1
XG0 T=101
�
SET TAU=-1
XG0 T=101
opp.
XG0 T=102
(herramienta 2 incorporada a herramienta 1)
El segundo trabajo NO requiere un cambio
herramienta, por tanto, dado el TAU=-1 previamente especificado, el palpador
ser� desconectado f�sicamente,� adem�s
de la desconexi�n de la ganancia de los operadores din�micos. El efecto que se
produce es de trabajar sin el palpador conectado y sin correcciones din�micas
sobre el eje Z debidas a posibles irregularidades de la superficie de la pieza.

SET TAU = 0
Si se la introduce en el programa a
continuaci�n de por lo menos un trabajo que requer�a el uso del palpador,
informa al sistema que a partir del pr�ximo trabajo el mismo no lo solicitar�
m�s, pero solo desde el punto de vista f�sico. Ello quiere decir que el anillo
del palpador deber� desconectarse y los operadores din�micos �adormecidos�,
pero en cualquier caso siempre habilitados.
SET TAU = -1
Si se la introduce en el programa a
continuaci�n de por lo menos un trabajo que requer�a el uso del palpador,
informa al sistema que a partir del trabajo siguiente el mismo no se solicitar�
m�s ni desde el punto de vista f�sico, ni desde el punto de vista din�mico,
para los cabezales corrientemente sincronizados (o para el �nico cabezal m�ster
corriente si no hay ning�n otro cabezal sincronizado con �l). Ello quiere decir
que el anillo del palpador ser� desconectado por los cabezales seleccionados de
este modo y los operadores din�micos �descargados� (subprograma H9051) del
ciclo de ejecuci�n del CN.
SET TAU = -2
Si se introduce en el programa a continuaci�n
de por lo menos un trabajo que requer�a el uso del palpador, informa al sistema
que a partir del trabajo siguiente el mismo no se solicitar� m�s ni desde el
punto de vista f�sico, ni desde el punto de vista din�mico, para todos los
cabezales presentes en la m�quina con el palpador activado, ya sea que est�n
sincronizados, m�ster o �inhabilitados�. Ello quiere decir que el anillo del
palpador se desconectar� de los cabezales seleccionados de este modo y los
operadores din�micos �descargados� (subprograma H9051) del ciclo de ejecuci�n
del CN.
SET TAU = -3
Se usa al inicio del programa (despu�s del
Header) de modo equivalente a SET TAU=-1 o bien necesariamente en medio del
programa (aqu� no se puede usar m�s SET TAU=-1 con el mismo fin) para hacer de
modo que, si la herramienta est� ya montada en el cabezal que deber� trabajar,
por seguridad se requiere expl�citamente la generaci�n del mando de exclusi�n
mec�nica del anillo del palpador, porque el programa precedente podr�a haber
terminado el trabajo con el palpador activado, mientras en el inicio del nuevo
programa el cabezal debe trabajar sin el palpador mismo.
Se recuerda que esto vale s�lo en el primer
trabajo (con el respectivo cambio de herramienta) asociada a cada cabezal,
porque representa la transici�n del estado m�quina corriente (desconocido para
el traductor) al del inicio programa. Si no se usa uno de estos SET TAU (-1 �
-3), todo funciona como antes y no se genera ning�n c�digo inherente al
palpador que, si no se requiere un cambio de herramienta, quedar� en la �ltima
posici�n adoptada (habilitado o no habilitado).
Ejemplo:
H ...

SET
TAU = -3
Solicitud de exclusi�n f�sica palpador si
CUT ausente (M31 M185). En este caso se puede usar tambi�n -1.
XG0 ... T=101
Trabajo de T101 sin palpador.
SET
TAU = �1
Solicitud palpador en trabajo en en el
pr�ximo trabajo.
XG0 ... T=101
Trabajo de T101 con palpador.
SET
TAU = -3
Solicitud exclusi�n f�sica palpador si CUT
ausente (M32 M185). En este caso no
se puede usar -1.
XG0 ... T=201
Trabajo con T201 sin palpador.
SET
TAU =� 1
Solicitud palpador en trabajo en el pr�ximo
mecanizado.
XG0 ... T=201
Mecanizado de T201 con palpador.
Si en el el lugar de la segunda �SET TAU = -3�
se utilizara una �SET TAU = -1�, el sistema producir�a una exclusi�n f�sica de
los palpadores para el cabezal 200, pero tambi�n la �descarga� de los
operadores din�micos, puesto que �stos �ltimos han sido �cargados� por el
mecanizado anterior indicado por �SET TAU = 1�.
NOTAS
Considerando la
evoluci�n en el uso de los palpadores,�
para un control flexible y completo de la operatividad de dichos
dispositivos, a continuaci�n se proponen las siguientes indicaciones de
trabajo:
1. eliminar del archivo Nci.cfg o configurar
en �0� la clave $GEN_GAINZERO_PALPOFF
2. utilizar siempre la �SET TAU = -1� cuando se desea excluir f�sicamente el anillo del
palpador
3. utilizar la �SET TAU = 0� solo cuando se pasa entre trabajos que no requieren el
uso del cambio herramienta (ej.: herramientas incorporadas), pero no se quiere
extraer f�sicamente el anillo del palpador porque en colisi�n con la pieza
(verificaci�n realizada por el operador); esto evidentemente garantiza una
fuerte reducci�n de los tiempos de trabajo.
Macros
Con el fin de facilitar la programaci�n de
algunas funciones de las m�quinas Ergon, se han preparado algunas macros a
utilizar en fase de edici�n del programa PGM, las cuales podr�n ser
visualizadas accionando el pulsador de las macros asociadas a las m�quinas con
cabezas paralelas.
� Selecci�n sub-�reas
de bloqueo pieza � XSUBAREA.
� Selecci�n� filas de topes para sub-�reas de bloque
pieza � XBATTON.
� Limpieza mesas con
cepillo � XCLEAN.
� Posicionamiento gu�as
motorizadas sobre la mesa � XGUIDEM.
� Programaci�n cota gu�a
horizontal � XGUIDEH.
� Programaci�n distancia
en X entre cabezas para trabajo combinado � XINTAX.
� Delta entre longitud
herramienta real y corregida por palpador � XDELTAPALPATORE.
V�ase: cap. 5.4.2 � Macro usuario para
m�quinas Ergon.
��������

Optimizadores
El editor de Xilog Plus pone a disposici�n dos
algoritmos de optimizaci�n
� Optimizador cambios herramienta
(algoritmo SO; v�ase: cap. 7 � Optimizador de
programas).
� Optimizador taladrado (v�ase: instrucci�n BO).
El uso de estos algoritmos puede aplicarse a
m�quinas Ergon siguiendo las advertencias que se indican a continuaci�n.
Optimizador
cambios herramienta (algoritmo SO)
El algoritmo, para realizar un programa com�n
PGM, sigue las reglas definidas y explicadas en el manual, a�adiendo una opci�n
espec�fica que se encuentra disponible en la correspondiente ventana de di�logo:

Solicitando la optimizaci�n Sincronizaci�n cabezas
paralelas se activa autom�ticamente el check-box Cambio herramientas; con esta combinaci�n de check-box activos, el algoritmo de
optimizaci�n, adem�s de intentar optimizar el n�mero de cambios de herramientas
de las cabezas, intenta minimizar el n�mero de sincronizaciones y
de-sincronizaciones sucesivas. Esta segunda operaci�n va en detrimento de la
primera, es decir, limitando las de-sincronizaciones no se obtiene,
normalmente, un menor n�mero de cambios de herramientas; sin embargo,
considerando cuanto tiempo precisa la m�quina para la operaci�n de
sincronizaci�n de las cabezas, se obtendr�n mejores prestaciones en cuanto a
reducci�n de los tiempos de trabajo.
El algoritmo SO precisa que los programas PGM,
al cual est� aplicado, no contengan instrucciones SET TWIN para indicar las
combinaciones sincr�nicas. As� pues, para cualquier instrucci�n operativa del
lenguaje, deber� especificarse la lista de las herramientas.
Optimizador
taladrado (algoritmo BO)
El algoritmo sigue las reglas definidas y
explicadas en el manual para un programa com�n PGM. Adem�s, si se desea
trabajar con m�s cabezas taladradoras en sincr�nico para Ergon ser� obligatorio
utilizar la instrucci�n SET TWIN, para indicar la combinaci�n de las cabezas a
sincronizar
Ejemplo:
H DX=1000
DY=1000 DZ=50 BX=0 BY=0 BZ=0 /�def�
SET
TWIN = 24
BO X=100 Y=100 Z=-5 D=8 N=�P� R=2 x=32 V=10
En este ejemplo el algoritmo de optimizaci�n
taladrado generar� una serie de instrucciones de taladrado que se llevar�n a
cabo con las dos cabezas de taladrado 1200 y 1400 sincronizadas.
Sin embargo, si se desea trabajar con una sola
cabeza de taladrado (ej.: la 1200), ser� suficiente especificar, para el valor
TWIN, el n�mero del grupo-zeta al cual pertenece la cabeza:
Ejemplo:
H DX=1000
DY=1000 DZ=50 BX=0 BY=0 BZ=0 /�def�
SET
TWIN = 2
BO X=100 Y=100 Z=-5 D=8 N=�P� R=2 x=32 V=10
Si la SET TWIN no est� presente, el algoritmo
trabajar�, por defecto, sobre la cabeza de taladrado configurada en el archivo de configuraci�n pheads.cfg
perteneciente al grupo-zeta n�mero 1. Si no existen se generar� un error.

AP�NDICE
G. Grupo Universal (en RD220) con eje de rotaci�n paralelo al eje Y de la
m�quina
Configuraci�n del
Grupo
� xilog3.cfg
Programar el par�metro �Universal� = 0.
� pheads.cfg (testa 4)
Programar el par�metro �Actuador� = 5.
Medir la distancia en X entre el centro de
rotaci�n del mandril principal y el eje de rotaci�n del mandril del grupo en
posici�n horizontal, tal y como se muestra en la Fig. 1, y programar el
par�metro �Configuraci�n 0 X� con dicho valor, respetando el signo.
Fig. 1
Medir la distancia en Y entre el centro de
rotaci�n del mandril principal y el eje de rotaci�n del mandril del grupo en
posici�n vertical, tal y como se muestra en la Fig. 2, y programar el par�metro
�Configuraci�n 0 Y� con dicho valor, respetando el signo.
Fig. 2
Medir la distancia en Z entre el punto de
referencia para la medida de las herramientas del mandril principal y el eje de
rotaci�n del mandril del grupo en posici�n baja-horizontal, tal y como se
muestra en la Fig. 3, y programar el par�metro �Configuraci�n 0 Z� con dicho
valor, respetando el signo.
Fig. 3
Programar el par�metro �Final de carrera+
(positivo) del Vector� = 0.
� nci.cfg
Editar el archivo con un programa com�n de
edici�n de textos y a�adir la siguiente secci�n en caso de que no estuviera
presente:
{Grupo Hueco Cerradura con Eje Tilting}
{Inicio Secci�n}
$H04_XVECTOR
B
$
$H04_XFCVECTOR
43
$
$H04_UP
M81
$
$H04_DOWN
M71
$
$H04_ROTCW
M65M3S%ld
M21
$
$H04_ROTCCW
M65M3S%ld
M21
$
$H04_NOROT
M50
$
{Final Secci�n}
Creaci�n de una
herramienta para el Grupo
Editar una herramienta cualquiera comprendida
entre E1 y E96 de tipo FRESA o PUNTA.
Programar la longitud de la herramienta como
la distancia entre el plano de referencia del grupo y el punto de la fresa que
se ha de controlar (v�ase la Fig. 4).
Fig. 4
Programar los siguientes par�metros �Di�metro�
(Fresa o Punta), �Longitud herramienta�, �Di�metro herramienta�, �Velocidad�
(m�xima y est�ndar), �Rotaci�n� (m�xima y est�ndar) y �Velocidad G0/B�.
Programar el par�metro �Dimensi�n� como la
distancia entre el eje de rotaci�n de la herramienta y la dimensi�n m�xima Z
del grupo en posici�n horizontal (Fig.5).
Programar el par�metro �Distancia Z� = 0.
Programar el par�metro �Offset R� con el
�ngulo en el plano XY que toma la herramienta con el grupo posicionado a 0� de
rotaci�n.
Programar el par�metro �Distancia D� como la
distancia entre el centro de rotaci�n del grupo y el plano de referencia para
la medida de la longitud de la herramienta del grupo (Fig. 5).
Fig. 5
Programar el par�metro ��ngulo A� con el
�ngulo que toma la herramienta respecto al eje vertical cuando el grupo est�
posicionado a 0� de rotaci�n.
Modo de
programaci�n del Grupo
Para programar el grupo en cuesti�n, se
utilizan las instrucciones est�ndar de la interfaz Xilog Plus, recordando que
hay que introducir la orden de posicionamiento del eje tilting antes de iniciar
el trabajo en caso de operaciones de tipo inclinado:
;Posicionamiento de la herramienta del grupo B a 110� respecto a la vertical.
XAXROT
R=110 N=�B �
;Instrucci�n de taladrado inclinado con �ngulo
de taladrado igual a 270� en el plano XY con la herramienta E1 del cabezal 2.
BR X=800
Y=50 Z=-10 A=270 Q=1 T=201
NOTA. El �ngulo programado en la XAXROT debe ser siempre positivo.
Para variar el �ngulo respecto a la vertical
del trabajo hay que introducir de nuevo la instrucci�n XAXROT y repetir el trabajo, esta operaci�n no es necesaria si no
hay que cambiar el �ngulo.
No se puede variar el �ngulo de rotaci�n del
grupo una vez iniciado el perfil, ya que la instrucci�n XAXROT prev� �nicamente
el posicionamiento del grupo antes de iniciar el trabajo y no la interpolaci�n
del grupo durante el mismo.
Ejemplo:
XAXROT
R=90 N=�B�
-------------------------------------------------------- CORRECTO
G0R
X=0 Y=0 Z=-10 A=90 H=20 N=�profile� T=201
G1R
X=100
XAXROT
R=110 N=�B�
-------------------------------------------------------- CORRECTO
G0R
X=0 Y=0 Z=0 A=90 H=20 N=�profile� T=201
G1R
X=100 Z=-10
XAXROT
R=90 N=�B� ---------------- L�NEA INCORRECTA
G1R
X=0 Z=-20
G1R
X=100
Se puede trabajar tanto en todas las caras del
tablero (las que el grupo pueda trabajar), en correcci�n del radio de la
herramienta o en el centro de la herramienta, utilizando las normales
instrucciones B, XG0, XL2p etc. especificando la cara de trabajo deseada, como
con planos inclinados compatibles, utilizando la instrucci�n XPL X... Y... Z...
etc.
En estos casos no es necesario mandar el
posicionamiento del eje tilting con el comando XAXROT, ya que el compilador de
Xilog3 utilizar� el �ngulo compatible con el plano de trabajo seleccionado:
;Activaci�n de un plano paralelo a la cara 4
del tablero.
XPL X=0
Y=10 Z=0 Q=0 R=90
XG0
X=100 Y=20 Z=-10 T=201 N=�profile� C=2
XL2P
X=300������������������������������������
Para repetir el perfil apenas creado cambiando
el plano de trabajo, se puede utilizar la instrucci�n XGREP especificando el nombre del perfil:
;Activaci�n de un plano paralelo a la cara 4 del
tablero.
XPL X=0
Y=0 Z=0 Q=0 R=80
;Repetici�n del perfil en un plano inclinado
con herramienta 202.
XGREP
N=�profile� T=202

AP�NDICE
H. Grupo Prisma
Prisma es un grupo constituido por dos ejes
rotatorios: C (Vector) y B (Tilting). Adem�s de los trabajos normales
realizables sobre el panel, Prisma permite efectuar trabajos 3D.
Equipamiento
Las herramientas deben configurarse siguiendo
los criterios normales basados en el aspecto despu�s de la carga del mandril;
para determinar el sentido de trabajo, la cuchilla debe orientarse hacia el
lado 1 y dirigirse hacia el operador. El lado de trabajo debe ponerse a 0 para
las fresas y a 1 para las cuchillas.
Trabajos est�ndar
La programaci�n de los trabajos est�ndar se
realiza a trav�s de las instrucciones (X)B, (X)BR, (X)G0,� (X)G0R.
Trabajos 3D
La programaci�n de los trabajos 3D se realiza
a trav�s de las instrucciones (X)G03D y (X)G13D.
En caso de trabajos 3D especialmente
fraccionados (numerosos tramos (X)G13D muy peque�os) se podr�an producir pausas
indeseadas en el trabajo, debidas a que el Xilog Plus env�a los bloques ISO al
CN con mayor lentitud respecto a la que el CN precisa para la ejecuci�n de
dichos trabajos; para aumentar la velocidad de traslado de los bloques ISO al CN
se pueden seguir dos m�todos distintos:
� Introducir al inicio del programa la
instrucci�n: ISO �%ISOBLOCKSIZE=xx� donde xx debe ser un n�mero comprendido
entre 5 y 20; el campo de validez de la instrucci�n est� limitado al programa
en el cual est� introducida.
� Introducir en la clave $GEN_INIT$ del archivo de configuraci�n nci.cfg el
bloque: %%Bxx donde xx debe ser un n�mero comprendido entre 5 y 20; el campo de
validez de la instrucci�n est� extendido a todos los programas, incluso a
aquellos que no contienen trabajos 3D.
Ambas instrucciones (pero sobretodo la
segunda) deben ser utilizadas con atenci�n y s�lo en casos en los que resulte
estrictamente necesario, puesto que disminuyen la velocidad de todas las
actividades del Xilog Plus no
conectadas al env�o de los bloques ISO al CN; por norma el valor xx=10 no
deber�a superarse nunca.
V�ase tambi�n: instrucci�n SET
JERK3D.
Ejemplo de programaci�n 3D
...
G03D X=85.148 Y=100 H=20.544 Q=90.054 R=59.036
T=101 D=30 V=1000 S=9000
G13D X=87.675 Y=91.2 H=20.544 Q=89.964
R=59.031 V=4000
G13D X=87.666 Y=82.709 H=20.544 Q=89.935
R=59.047
G13D X=87.676 Y=74.292 H=20.543 Q=90.324
R=59.066
G13D X=87.746 Y=65.234 H=20.569 Q=89.433
R=58.87
G13D X=87.4 Y=57.109 H=20.569 Q=85.129
R=58.764
G13D X=86.491 Y=50.424 H=20.569 Q=78.984
R=58.852
...
Ejecuci�n directa del programa ISO
Los programas especialmente largos (como los
que incluyen trabajos de tipo 3D) pueden precisar un largo tiempo de
elaboraci�n, a fin de que el Panel M�quina de Xilog Plus los convierta en archivos ISO y los transmita al Control Num�rico para que puedan ser ejecutados.
En estos casos se aconseja crear el archivo
ISO en el ordenador personal utilizado para la programaci�n, para despu�s poder
pasarlo al Panel M�quina y ejecutarlo directamente.
Para poder realizar esta operaci�n es
necesario:
� Instalar el Panel M�quina en el ordenador
personal utilizado para la programaci�n.
� Comprobar que el herramental y la
configuraci�n de la m�quina programada en el editor de Xilog Plus sean iguales
a los de la m�quina.
►Para crear el archivo ISO (con extensi�n .CNC) a utilizar con el Panel
M�quina:
1. Poner en marcha el Panel M�quina.
2. Importar el archivo PGM del programa a trav�s del men� Archivo / EJECUCI�N
autom�tica (v�ase: Manual
de uso del Panel de la m�quina).
3. Abrir el archivo ISO generado por el
Panel M�quina con un editor de texto (el editor del Panel M�quina o un editor
externo). El archivo ISO es en la carpeta APC (.../SCM
Group/Xilog Plus/APC) - en la carpeta A, B, C o D,
seg�n el �rea de la carga del programa. El nombre del archivo es
<nombre>.inn, donde nn es un n�mero comprendido entre 00 y 99.
4. Eliminar el caracter "%" de la �ltima l�nea� e introducir la l�nea "M2" en su
lugar.
5. Guardar el archivo cambiando la extensi�n original por .CNC (por
ejemplo, el archivo ejemplo.i00 se
transformar� en ejemplo.cnc).
El archivo .CNC, generado de este modo, se
importar� al Panel M�quina instalado en la m�quina a trav�s del men� Archivo / ABRIR archivo
CNC.
Notas
Sobre el grupo Prisma se realizan los
controles normales de presencia equilibro y de no superaci�n de los finales de
carrera software; los posibles errores debidos a las traslaciones generadas por
el Control Num�rico no son se�aladas por Xilog Plus.
Todos los controles efectuados por Xilog Plus
en modalidad Editor y en modalidad Autom�tico pueden inhabilitarse poniendo a
cero el campo �Control microinterruptor de tope ejes� en la secci�n �GEN 2� del archivo de configuraci�n� axis.cfg.
La rotaci�n del grupo Prisma se produce
siempre a una cota de seguridad determinada por encima de la pieza; dicha cota
se utiliza para posicionar el grupo para el primer trabajo,� para las traslaciones entre un trabajo y el
sucesivo, y al final del �ltimo trabajo para situar el grupo en la posici�n de
estacionamiento.
La cota de seguridad es variable, puesto que
est� unida a las posiciones de trabajo del grupo y a las dimensiones totales de
la herramienta y de dicho grupo. Si no existe cota de seguridad por encima de
la pieza, no ser� posible realizar ning�n trabajo.
En caso de trabajos 3D con la herramienta que
posee las dimensiones m�s reducidas del grupo, conviene entrar en la pieza y
salir de la pieza con la herramienta a 0�.�

El campo �Di�metro cilindro seguro� en el archivo de configuraci�n pheads.cfg
debe calcularse de modo que, girando los ejes B y C con el grupo Prisma
completamente arriba, no haya choques de ning�n tipo.
En MDI los mandos de cambio herramienta M6Txxx
se env�an al CN a trav�s del archivo %8197 y se ejecutan a trav�s de M197; as�
pues, debe programarse la asociaci�n entre el programa y el c�digo M.

AP�NDICE
I. Programaci�n de los sujetadores Duomatic
La selecci�n del bloqueo por medio de los
sujetadores DUOMATIC, debe realizarse al comienzo del programa, antes de
solicitar el bloqueo de la pieza (M28/M39/M58) .
Esta selecci�n debe efectuarse por medio de
los usuales par�metros E30xxx :
E30001 (Selecci�n del tipo de bloqueo pieza a utilizar en la zona 1).
E30002 (Selecci�n del tipo de bloqueo pieza a utilizar en la zona 2).
(V�ase el manual Diagn�stico y C�digos M, que
se suministra con la m�quina)
Concretamente:
E30001
=11�
: DAB
(Duomatic zona AB)

E30002
=11�
: DCD
(Duomatic zona CD)
1) La correcta programaci�n del par�metro �V� en el Encabezamiento del programa PGM de Xilog Plus,� permite plantear autom�ticamente los valores
para E30001 y E30002 seg�n la zona de vac�o (A,B,C,D etc.) seleccionada:
V=5x
(Selecci�n de los sujetadores DUOMATIC)
Ejemplo:
(H DX=�
DY=� DZ=� -A C=0 T=0 R=99 � V=5x)
E30001=11
�
M28
Ejemplo:
(H DX=� DY=� DZ=� -B C=0 T=0 R=99 � V=5x)
E30001=11
�
M38
Al comienzo del programa, antes de la
solicitud del bloqueo pieza (M28/M38/M58), es necesario seleccionar los
sujetadores DUOMATIC con los que se desea empezar a trabajar [delanteros (lado
operador en la direcci�n Y) o traseros (lado contrario al operador en la
direcci�n Y ) o ambos].
E30059
(Selecci�n delanteros / traseros / ambos
DUOMATIC zona 1)
E30060
(Selecci�n delanteros / traseros / ambos
DUOMATIC zona 2)

E30059
= 1: Delanteros zona 1
E30060
= 1:
Delanteros zona 2

= 2: Traseros zona 1���

= 2:
Traseros zona 2
= 3: Ambos zona 1�����

= 3:
Ambos zona 2
2) La correcta programaci�n del par�metro �V� permite plantear autom�ticamente estos valores con relaci�n a
la zona interesada.
�
V=50
(Ning�n efecto)
V=51
(Selecci�n de los sujetadores DUOMATIC
delanteros)
V=52
(Selecci�n de los sujetadores DUOMATIC
traseros)
V=53
(Selecci�n de los sujetadores DUOMATIC
delanteros y traseros)
Ejemplo:
(H DX=�
DY=� DZ=� -CD C=0 T=0 R=99 � V=51)
E30002=11
E30060=1
�
M58
Ejemplo:
(H DX=� DY=� DZ=� -AB C=0 T=0 R=99 � V=53)
E30001=11
E30059=3
�
M58
En cualquier punto del programa es posible
(durante la ejecuci�n del trabajo) cambiar entre sujetadores delanteros y
traseros mediante el c�digo:
M193� (cambio entre
sujetadores delanteros y traseros)
(V�ase el manual Diagn�stico y C�digos M, que
se suministra con la m�quina)
3) En Xilog Plus existe una macro instrucci�n dedicada que puede ejecutar
esta operaci�n directamente mediante el programa (instrucci�n XISO):
DUOMATIC
G=0 (cambio entre sujetadores delanteros y traseros)
Ejemplo:
(H DX=�
DY=� DZ=� -AB C=0 T=0 R=99 � V=53)
E30001=11
E30059=3
�
M58
�
(DUOMATIC G=0)
M193
En cualquier punto del programa se puede optar
por desenganchar los sujetadores delanteros o traseros si se ha seleccionado
previamente la opci�n V=53 (ambos).
E30059
(Selecci�n sujetadores delanteros / traseros
DUOMATIC zona 1)
E30060
(Selecci�n sujetadores delanteros / traseros
DUOMATIC zona 2)
M194
(Exclusi�n de los sujetadores seleccionados)

E30059
= 4 : Delanteros

= 5 : Traseros

E30060
= 4 : Delanteros

= 5 : Traseros
Cuando los sujetadores delanteros est�n
desenganchados no ser� posible desenganchar los traseros y viceversa o decidir
el restablecimiento del bloqueo con ambos.
4) La instrucci�n mencionada en el punto anterior permite ejecutar esta
operaci�n directamente mediante el programa (instrucci�n XISO):
DUOMATIC
G=1 (exclusi�n sujetadores delanteros)
DUOMATIC
G=2 (exclusi�n sujetadores traseros)
Ejemplo:
(H DX=� DY=� DZ=� -AB C=0 T=0 R=99 �
V=53)
E30001=11
E30059=3
�
M58
�
(DUOMATIC����������� G=1)
E30059=4
M194

AP�NDICE
J. Gesti�n del equipo del cliente
Antes de activar o desactivar el equipo es
obligatorio iniciar a partir de una condici�n de reposo en todas las zonas de
la mesa de trabajo. Es posible efectuar un trabajo pendular pero no es posible
manejar el equipo junto con otros sistemas de bloqueo.
Con
Xilog Plus:
Para activar la gesti�n del equipo, hay que
introducir en el campo V del encabezamiento V=40.
En ISO:
a) gesti�n de 2 zonas:
E30001=1��
Zona A
E30002=1��
Zona B

M191 = Activaci�n Equipo
M190 = Desactivaci�n Equipo
Estos c�digos deber�n estar seguidos por los
c�digos habituales de petici�n de vac�o.
b) gesti�n de 4 zonas:
E30001=1��
Zona A
E30001=2��
Zona B
E30001=3�� Zona AB o BA
E30002=1��
Zona C
E30002=2��
Zona D
E30002=3�� Zona CD or DC

M191 = Activaci�n Equipo
M190 = Desactivaci�n Equipo
Estos c�digos deber�n estar seguidos por los
c�digos habituales de petici�n de vac�o.

AP�NDICE K.
Configuraci�n de los soportes y de los elementos de la mesa del Editor de mesas
de trabajo
El archivo libsupp.cfg
Los
soportes y los elementos de la mesa utilizables en el Editor de mesas de
trabajo, pueden configurarse con el archivo de configuraci�n M�quina/Librer�a soportes EPL (LIBSUPP). El archivo correspondiente se llama libsupp.cfg y est� en formato
texto, por lo tanto puede modificarse libremente, incluso utilizando un editor
externo al Xilog Plus.
El
archivo contiene una sola secci�n para cada tipo de soporte o elemento de la
mesa, dentro de la cual est�n definidos separadamente los soportes o elementos
de la mesa (exceptuando la guarnici�n para superficies multifuncionales, que es
�nica).
Introducci�n del n�mero de
soportes/elementos de la mesa disponibles
El
archivo de configuraci�n libsupp.cfg instalado con Xilog Plus contiene ya todos
los par�metros necesarios para la configuraci�n de los soportes y de los
elementos de la mesa. Los soportes y elementos de la mesa no se ven
inmediatamente en el Editor de mesas de trabajo, puesto que hay que introducir
el n�mero de los mismos, en funci�n del n�mero de piezas efectivamente
disponibles sobre la m�quina. Esta informaci�n se introduce a trav�s del
par�metro [MAXNUMTYPE], si est� disponible para ese tipo de soporte/elemento de
la mesa.
Par�metros de configuraci�n
Si la
l�nea de un par�metro de un soporte o elemento de la mesa est� ausente, Xilog
Plus considera su valor igual a 0 (o nulo, caso que se requiera la introducci�n
de un texto).
Ventosas
Las
ventosas est�n contenidas entre los siguientes marcadores:
[INIT_LIBVT]
Inicio
de la secci�n.
...

[END_LIBVT]
Fin
de la secci�n.
Definici�n de una ventosa
[INIT_VT]
Inicio
de la definici�n.

[GEOMBASE]...
Geometr�a
de la base. Valores: C (circular), R (rectangular).

[WBASE]...��������������������������������������������

Anchura
de la base (si la base es rectangular).

[LBASE]...
Longitud
de la base (si la base es rectangular).

[RBASE]...
Radio
de la base (si la base es circular).

[WBASEAGG]...
Anchura
del rect�ngulo de enganche de la base a la superficie multifuncional.

[LBASEAGG]...
Longitud
del rect�ngulo de enganche de la base a la superficie multifuncional.

[GEOMAPP]...
Geometr�a
del apoyo. Valores: C (circular); R (rectangular); G (gen�rico).

[WAPP]...
Anchura
del apoyo (si el apoyo es rectangular).

[LAPP]...
Longitud
del apoyo (si el apoyo es rectangular).

[RAPP]...
Radio
del apoyo (si el apoyo es circular).

[HAPP]...
Altura
del apoyo.

[EN_ROTAZ]...
Habilitaci�n
de la rotaci�n del apoyo respecto a la base. Valores: 0 (no habilitada), 1
(habilitada).

[OFFX_OVR]...
Offset
en X del centro de rotaci�n del apoyo respecto al centro de la base.

[OFFY_OVR]...
Offset
en Y del centro de rotaci�n del apoyo respecto al centro de la base.

[OFFX_OVAPP]...
Offset
en X del centro del apoyo respecto al centro de rotaci�n del apoyo.

[OFFY_OVAPP]...
Offset
en Y del centro del apoyo respecto al centro de rotaci�n del apoyo.

[HTOT]...
Altura
de la ventosa (base+apoyo).

[ALFAROT]...
�ngulo
de rotaci�n inicial del apoyo (par�metro actualmente no utilizable).

[FILEBMP]...
Recorrido/NombreArchivo
de la imagen bitmap a visualizar en la ventana de las propiedades de la
ventosa.

[MAXNUMTYPE]...
N�mero
de ventosas disponibles.

[OFFRLASER]...
Inclinaci�n
de la cruz l�ser asim�trica en caso de l�ser 0�-360� con el apoyo en su
configuraci�n por defecto.

[OFFX_MIR]...
Offset en X entre el centro de la base y el visor de la ventosa.

[OFFY_MIR]...
Offset en Y entre el centro de la base y el visor de la ventosa.

[GEOMAPP2]...
Geometr�a del apoyo secundario. Valores: C (circular), R
(rectangular).

[WAPP2]...
(Ventosas con dos apoyos). Anchura del apoyo secundario (si el apoyo
es rectangular).

[LAPP2]...
(Ventosas con dos apoyos). Longitud del apoyo secundario (si el apoyo
es rectangular).

[RAPP2]...
(Ventosas con dos apoyos). Radio del apoyo secundario (si el apoyo es
circular).

[HAPP2]...
(Ventosas con dos apoyos). Altura del apoyo secundario.

[EN_ROTAZ2]...
(Ventosas con dos apoyos). Habilitaci�n de la rotaci�n del apoyo
secundario respecto a la base. Valores: 0 (no habilitada); 1 (habilitada).

[OFFX_OVR2]...
(Ventosas con dos apoyos). Offset en X del centro de rotaci�n del
apoyo secundario respecto al centro de la base.

[OFFY_OVR2]...
(Ventosas con dos apoyos). Offset en Y del centro de rotaci�n del
apoyo secundario respecto al centro de la base.

[OFFX_OVAPP2]...
(Ventosas con dos apoyos). Offset en X del centro del apoyo secundario
respecto al centro de rotaci�n del apoyo secundario.

[OFFY_OVAPP2]...
(Ventosas con dos apoyos). Offset en Y del centro del apoyo
secundario respecto al centro de rotaci�n del apoyo secundario.

[ALFAROT2]...
(Ventosas con dos apoyos). �ngulo de rotaci�n inicial del apoyo
secundario (par�metro actualmente no utilizable).

[OFFRLASER2]...
(Ventosas con dos apoyos). Inclinaci�n de la cruz l�ser asim�trica en
caso de l�ser 0�-360� con el apoyo secundario en configuraci�n por defecto.

[DELTAAPP]...
(Ventosas con dos apoyos). Par�metro v�lido s�lo si el apoyo
principal y el apoyo secundario tienen el punto de rotaci�n coincidente:
indica el �ngulo m�nimo entre los dos apoyos.

[SIMAPP]...
(Ventosas
con apoyo de tipo gen�rico). Tipo de simetr�a del apoyo �respecto al propio centro. Valores: NDEF
(ninguna simetr�a), SIMX (simetr�a en X), SIMY (simetr�a en Y), SIMXY
(simetr�a en X e Y).

[G0]
X=...,Y=...
(Ventosas
con apoyo de tipo gen�rico). V�ase m�s adelante.

[G1]
X=...,Y=...
(Ventosas
con apoyo de tipo gen�rico). V�ase m�s adelante.

[G2]
X=...,Y=...,I=...,J=...,R=...
(Ventosas
con apoyo de tipo gen�rico). V�ase m�s adelante.

[G3]
X=...,Y=...,I=...,J=...,R=...
(Ventosas
con apoyo de tipo gen�rico). V�ase m�s adelante.

[NOME]...
Nombre
de la ventosa (debe ser �nico dentro del archivo).

[NONSPEC]...
Define
las �reas en las cuales no se especulariza la ventosa.
Valores:
SIMX_ (no especularizable en �reas con Simetr�a en X), SIMY_(no
especularizable en �reas con Simetr�a en Y), SIMXY(no especularizable en
�reas con Simetr�a en XY).
Estos
valores pueden estar presentes tambi�n contempor�neamente separados por una
coma ([NONSPEC]:SIMX_ ,SIMY_ ,SIMXY).
[END_VT]
Fin
de la definici�n.
Configuraci�n de un apoyo de tipo gen�rico para ventosa
Si la
ventosa est� equipada con un apoyo de tipo gen�rico (por ejemplo, de forma
triangular con cantos achaflanados), hay que introducir algunos par�metros
espec�ficos, tal y como se indica en la lista de los par�metros para la
definici�n de una ventosa.
En
especial, para definir el perfil del apoyo se encuentran disponibles las
siguientes instrucciones:
[G0]
X=...,Y=...
Punto
de inicio del perfil del apoyo.
X =
coordenada X;
Y = coordenada Y.
[G1]
X=...,Y=...
Segmento
de recta.
X =
coordenada X del punto final;
Y = coordenada Y del punto final.
[G2]
X=...,Y=...,I=...,J=...,R=...
Arco
de c�rculo en sentido horario.
X =
coordenada X del punto final;
Y =
coordenada Y del punto final;
I =
coordenada X del centro del arco;
J =
coordenada Y del centro del arco;
R =
radio del arco.
[G3]
X=...,Y=...,I=...,J=...,R=...
Arco de c�rculo en sentido contrario a las agujas del reloj.
X =
coordenada X del punto final;
Y =
coordenada Y del punto final;
I =
coordenada X del centro del arco;
J =
coordenada Y del centro del arco;
R = radio del arco.
Ejemplo:

[GEOMAPP]
G
[SIMAPP]
NDEF
[OFFX_OVR]
0
[OFFY_OVR]
0
[OFFX_OVAPP] 0
[OFFY_OVAPP] 0
[EN_ROTAZ]
1
[HAPP]
63.5
[G0] X=-25,Y=75
[G1] X=100,Y=-75
[G2]
X=75,Y=-100,I=75,J=-75,R=25
[G1] X=-75,Y=-100
[G2] X=-100,Y=-75,I=-75,J=-75,R=25
[G1] X=-75,Y=75
[G2]
X=-50,Y=100,I=-50,J=75,R=25
Para
poder utilizar estas instrucciones hay que respetar algunas condiciones:
� debe existir una sola G0;
� el perfil del apoyo debe estar definido
por tres puntos como m�nimo;
� todas las instrucciones utilizadas (G0,
G1, G2, G3) deben introducirse de tal manera que se defina un per�metro cerrado
constituido por puntos sucesivos y continuos uno respecto al otro.
La
ventosa del ejemplo tambi�n puede dibujarse utilizando la instrucci�n G3. En
tal caso, los puntos deben introducirse siguiendo el sentido contrario a las
agujas del reloj a partir del origen (G0).
Bornes
Los
bornes est�n contenidas entro los siguientes marcadores:
[INIT_LIBCLAMP]
Inicio
de la secci�n.
...

[END_LIBCLAMP]
Fin
de la secci�n.
Definici�n de un borne
[INIT_CLAMP]
Inicio
de la definici�n.

[TYPEMORS]...
Define
el tipo de borne.
Valores:
G (gen�rico) S (est�ndar).

[GEOMBASE]...
Geometr�a
de la base. Valores: C (circular), R (rectangular).

[WBASE]...
Anchura
de la base (si la base es rectangular).

[LBASE]...
Longitud
de la base (si la base es rectangular).

[RBASE]...
Radio
de la base (si la base es circular).

[RSTELO]...
Radio
del v�stago.

[RPIATT]...
Radio
del plato.

[OFFX_OMORS]...
Offset
en X del centro del v�stago respecto al centro de la base.

[OFFY_OMORS]...
Offset
en Y del centro del� v�stago respecto
al centro de la base.

[INSERONBASE]...
Confirma
la posibilidad de introducir el borne en la base (solo para mesas
motorizadas). Valores: 0 (el soporte no se introduce en las bases
motorizadas) 1 (el soporte se puede introducir en las bases motorizadas).

[HTOT]...
Altura
de la morsa (base+v�stago+plato).

[HUP]...
Altura
v�stago+plato.

[SIMMORS]...
(Bornes
con cuerpo de tipo gen�rico). Tipo de simetr�a del cuerpo respecto del propio
centro. Valores: NDEF (ninguna simetr�a), SIMX (simetr�a en X), SIMY
(simetr�a en Y), SIMXY (simetr�a en X e Y).

[POS_MORS]...
Posici�n
de introducci�n del borne en la viga. Valores: 0 (central), 1 (en el lado
izquierdo), 2 (en el lado derecho).

[FILEBMP]...
Recorrido/NombreArchivo
de la imagen bitmap a visualizar en la ventana de las propiedades del borne.

[OFFX_MIR]...
Offset en X entre el centro de la base y el visor de la ventosa.

[OFFY_MIR]...
Offset en Y entre el centro de la base y el visor de la ventosa.

[MAXNUMTYPE]...
N�mero
de bornes disponibles.

[INIT_CORPO]...
Inicio
definici�n del perfil del cuerpo.

[G0]
X=...,Y=...
(Bornes
con cuerpo de tipo gen�rico). V�ase adem�s.

[G1]
X=...,Y=...
(Bornes
con cuerpo de tipo gen�rico). V�ase adem�s.

[G2]
X=...,Y=...,I=...,J=...,R=...
(Bornes
con cuerpo de tipo gen�rico). V�ase adem�s.

[G3]
X=...,Y=...,I=...,J=...,R=...
(Bornes
con cuerpo de tipo gen�rico). V�ase adem�s.

[END_CORPO]...
Fin
definici�n del perfil del cuerpo.

[NOME]...
Nombre
del borne (debe ser �nico dentro del archivo).
[END_CLAMP]
Fin
de la definici�n.
Configuraci�n de un cuerpo de tipo gen�rico o por borne
Si el
borne est� dotado de un cuerpo de tipo gen�rico (por ejemplo, de forma
triangular con �ngulos biselados), hay que programar algunos par�metros
espec�ficos, como indicado en la lista de los par�metros para la definici�n de
un borne.
En
especial, para definir el perfil del cuerpo est�n disponibles las siguientes
instrucciones:
[G0]
X=...,Y=...
Punto
de inicio del perfil del cuerpo.
X =
coordenada X;
Y = coordenada Y.
[G1]
X=...,Y=...
Segmento
de recta.
X =
coordenada X del punto final;
Y = coordenada Y del punto final.
[G2]
X=...,Y=...,I=...,J=...,R=...
Arco
de c�rculo en sentido horario.
X =
coordenada X del punto final;
Y =
coordenada Y del punto final;
I =
coordenada X del centro del arco;
J =
coordenada Y del centro del arco;
R =
radio del arco.
[G3]
X=...,Y=...,I=...,J=...,R=...
Arco de c�rculo en sentido contrario a las agujas del reloj.
X =
coordenada X del punto final;
Y =
coordenada Y del punto final;
I =
coordenada X del centro del arco;
J =
coordenada Y del centro del arco;
R = radio del arco.

Ejemplo:

[INIT_CLAMP]
[TYPEMORS]
G
[GEOMBASE]
R
[WBASE]
145
[LBASE]
145
[OFFX_OMORS]
-32.7
[OFFY_OMORS]
0
[INIT_CORPO]
[G0] X=-25,Y=75
[G1] X=100,Y=-75
[G2]
X=75,Y=-100,I=75,J=-75,R=25
[G1] X=-75,Y=-100
[G2] X=-100,Y=-75,I=-75,J=-75,R=25
[G1] X=-75,Y=75
[G2] X=-50,Y=100,I=-50,J=75,R=25
[END_CORPO]
Para
poder utilizar estas instrucciones hay que respetar algunas condiciones:
� El perfil del cuerpo debe estar definido
por lo menos con tres puntos;
� Todas las instrucciones utilizadas (G0,
G1, G2, G3) deben introducirse de modo tal que define un per�metro cerrado
constituido por puntos sucesivos y continuos uno respecto del otro.
El
borne del ejemplo puede dibujarse tambi�n utilizando la instrucci�n G3. En tal
caso, los puntos deben introducirse siguiendo el sentido contrario al reloj a
partir del origen (G0).
Modulset
Los
modulsets est�n contenidos entre los siguientes marcadores:
[INIT_LIBMSET]
Inicio
de la secci�n.
...

[END_LIBMSET]
Fin
de la secci�n.
Definici�n de un modulset
[INIT_MSET]
Inicio
de la definici�n.

[LINS]...
Longitud
del lado de introducci�n.

[LSEC]...
Longitud
del lado secundario.

[DIST]...
Distancia
entre los lados.

[FILEBMP]...
Recorrido/NombreArchivo
de la imagen bitmap a visualizar en la ventana de las propiedades del
modulset.

[MAXNUMTYPE]...
N�mero
de modulsets disponibles.

[NOME]...
Nombre
del modulset (debe ser �nico dentro del archivo).
[END_MSET]
Fin
de la definici�n.
Guarniciones
La
guarnici�n es �nica, y est� descrita por la siguiente secci�n:
[INIT_LIBGU]
Inicio
de la secci�n.

[W]...
Anchura
de la guarnici�n.

[FILEBMP]...
Recorrido/NombreArchivo
de la imagen bitmap a visualizar en la ventana de las propiedades de la
guarnici�n.
[END_LIBGU]
Fin
de la secci�n.
Barras ayudo-carga
Las
barras ayudo-carga est�n contenidas entre los siguientes marcadores:
[INIT_LIBBAC]
Inicio
de la secci�n.
...

[END_LIBBAC]
Fin
de la secci�n.
Definici�n de una barra ayuda-carga
[INIT_BAC]
Inicio
de la definici�n.

[W]...
Anchura
de la barra .

[OFFX]...
Offset
en X de la barra respecto al centro de la viga.

[FILEBMP]...
Recorrido/NombreArchivo
de la imagen bitmap a visualizar en la ventana de las propiedades de la
barra.

[MAXNUMTYPE]...
N�mero
de barras disponibles.

[NOME]...
Nombre
de la barra (debe ser �nico dentro del archivo).
[END_BAC]
Fin
de la definici�n.
Barras m�viles
Las
barras m�viles est�n contenidas entre los siguientes marcadores:
[INIT_LIBBM]
Inicio
de la secci�n.
...

[END_LIBBM]
Fin
de la secci�n.
Definici�n de una barra m�vil
[...]
Inicio
de la definici�n. Valores: INIT_BLSX (barra lateral izquierda), INIT_BCSX
(barra central izquierda), INIT_BCDX (barra central derecha), INIT_BLDX
(barra lateral derecha).

[W]...
Anchura
de la barra .

[OFFX]...
Offset
en X entre el centro de la barra y el punto de los topes de apoyo pieza que
va a tocar la pieza.

[FILEBMP]...
Recorrido/NombreArchivo
de la imagen bitmap a visualizar en la ventana de las propiedades de la
barra.

[EN_BM]...
Habilitaci�n
de la barra. Valores: 0 (ausente), 1 (presente).

[ZONE]
Posici�n
de la barra. Valores: 1 (barra lateral izquierda), 2 (barra central
izquierda), 3 (barra central derecha), 4 (barra lateral derecha).

[OFFXQUOTA]...
Offset
en X de la cota de la mesa entre el origen m�quina y el 0 de la varilla
m�trica aplicada sobre la base.

[NOME]...
Nombre
de la barra (debe ser �nico dentro del archivo).
[...]
Fin
de la definici�n. Valores: INIT_BLSX (barra lateral izquierda), INIT_BCSX
(barra central izquierda), INIT_BCDX (barra central derecha), INIT_BLDX (barra
lateral derecha).
Topes apoyo-pieza
Los
topes apoyo-pieza est�n contenidos entre los siguientes marcadores:
[INIT_LIBBAP]
Inicio
de la secci�n.
...

[END_LIBBAP]
Fin
de la secci�n.
Definici�n de un tope apoyo-pieza
[INIT_BAP]
Inicio
de la definici�n.

[R]...
Radio
del tope.

[INIT_CORPO]...
Inicio
definici�n del perfil del cuerpo.

[G0]
X=...,Y=...
(Tope
con cuerpo de tipo gen�rico). V�ase adem�s.

[G1]
X=...,Y=...
(Tope
con cuerpo de tipo gen�rico). V�ase adem�s.

[G2]
X=...,Y=...,I=...,J=...,R=...
(Tope
con cuerpo de tipo gen�rico). V�ase adem�s.

[G3]
X=...,Y=...,I=...,J=...,R=...
(Tope
con cuerpo de tipo gen�rico). V�ase adem�s.

[END_CORPO]...
Fin
definici�n del perfil del cuerpo.

[FILEBMP]...
Recorrido/NombreArchivo
de la imagen bitmap a visualizar en la ventana de las propiedades del tope.

[MAXNUMTYPE]...
N�mero
de topes disponibles.

[NOME]...
Nombre
del tope (debe ser �nico dentro del archivo).
[END_BAP]
Fin
de la definici�n.
Configuraci�n
de un cuerpo de tipo gen�rico para tope
Si el
tope est� dotado de un cuerpo de tipo gen�rico (por ejemplo, de forma
triangular con aristas biseladas), hay que programar algunos par�metros
espec�ficos, como indicado en la lista de los par�metros para la definici�n de
un tope.
En
especial, para definir el perfil del cuerpo est�n disponibles las siguientes
instrucciones:
[G0]
X=...,Y=...
Punto
de inicio del perfil del cuerpo.
X =
coordenada X;
Y = coordenada Y.
[G1]
X=...,Y=...
Segmento
de recta.
X =
coordenada X del punto final;
Y = coordenada Y del punto final.
[G2]
X=...,Y=...,I=...,J=...,R=...
Arco
de c�rculo en sentido horario.
X =
coordenada X del punto final;
Y =
coordenada Y del punto final;
I =
coordenada X del centro del arco;
J =
coordenada Y del centro del arco;
R =
radio del arco.
[G3]
X=...,Y=...,I=...,J=...,R=...
Arco de c�rculo en sentido contrario a las agujas del reloj.
X =
coordenada X del punto final;
Y =
coordenada Y del punto final;
I =
coordenada X del centro del arco;
J =
coordenada Y del centro del arco;
R = radio del arco.

Ejemplo:

[INIT_BAP]
����� [R] 12.5
����� [INIT_CORPO]
[G0] X=-25,Y=75
[G1] X=100,Y=-75
[G2]
X=75,Y=-100,I=75,J=-75,R=25
[G1] X=-75,Y=-100
[G2] X=-100,Y=-75,I=-75,J=-75,R=25
[G1] X=-75,Y=75
[G2]
X=-50,Y=100,I=-50,J=75,R=25
[END_CORPO]

Para
poder utilizar estas instrucciones hay que respetar algunas condiciones:
� El perfil del cuerpo debe estar definido
por lo menos con tres puntos;
� Todas las instrucciones utilizadas (G0,
G1, G2, G3) deben introducirse de modo tal que define un per�metro cerrado
constituido por puntos sucesivos y continuos uno respecto del otro.
El
tope del ejemplo puede dibujarse utilizando la instrucci�n G3. En tal caso, los
puntos deben introducirse siguiendo el sentido contrario al reloj a partir del
origen (G0).

AP�NDICE L. Control de los cortes con hoja
Configuraci�n de las herramientas
Grupos auxiliares
Los
grupos auxiliares (grupo Hoja, grupo Caja cerradura) pueden estar dotados de
rotaci�n neum�tica o rotaci�n continuada.
La rotaci�n neum�tica permite girar la
hoja en intervalos de 90 grados (seg�n las caracter�sticas de la herramienta).
En el equipamiento, las herramientas de rotaci�n neum�tica se identifican por:
� n�mero herramienta par, en posici�n no
girada (par�metro �Offset R� = 0);
� n�mero herramienta impar, en posici�n
girada (par�metro �Offset R� = -90).
La rotaci�n continuada permite girar la
hoja en continuado.
Eje Vector
El eje
Vector, que puede montarse ya sea en el mandril principal como en los grupos
auxiliares, permite girar la hoja durante el trabajo en el plano XY. Para los
cortes inclinados con eje Vector, es necesario introducir siempre el par�metro
IC de la instrucci�n (X)G0R en el valor 3: de este modo, Xilog Plus proceder�
con la alineaci�n de la hoja en la direcci�n de corte.
Cabezal Prisma
El
cabezal Prisma permite mover la hoja en cualquier direcci�n el el espacio
tridimensional durante el trabajo. La herramienta hoja montada en un cabezal
Prisma requiere una configuraci�n especial: ��
� el par�metro �A� debe programarse en 0;
� el par�metro �Offset R� debe programarse
en 0;
� el par�metro �Distancia Z� representa
toda la distancia entre la base del cono y la cara interna de la hoja (equivale
a la suma de los par�metros �Distancia Z� y �Distancia D� de una hoja en
cabezal angular).
El
cabezal Prisma posiciona autom�ticamente el mandril en posici�n horizontal, con
la hoja ortogonal a la mesa de trabajo. El �ngulo de rotaci�n de la hoja no
est� programado en el equipamiento, sino directamente en la instrucci�n G0R/XG0R,
con el par�metro B (cuyo uso est� reservado para el cabezal Prisma).
�
Nota:
si B=0, el lado de entrada programado con el par�metro IC/I de las
instrucciones G0R/XG0R no se respeta.
Programaci�n
Cortes
ortogonales en cara 1
Los cortes ortogonales en cara
1 pueden programarse con las instrucciones�
G0 y G1, o XG0 y XL2P. Como adicional:
� en el caso de cortes de toda la longitud
de la pieza, se pueden usar las instrucciones (X)GIN y (X)GOUT para asegurarse
una profundidad de corte constante;
� en el caso
de cortes ranura, se puede corregir la profundidad del corte en el punto
inicial y final introduciendo la instrucci�n C con el valor 3 (correcci�n de
profundidad).
Cortes
inclinados
Los cortes inclinados pueden
programarse con las instrucciones (X)G0R y (X)G1R. En los cortes inclinados:
� no es posible utilizar las instrucciones
(X)GIN/(X)GOUT;
� o es posible utilizar la correcci�n
herramienta: las coordinadas del corte se refieren siempre al punto central del
corte de la hoja.
Nota. En la cara 1, los cortes inclinados
pueden realizarse tambi�n utilizando la instrucci�n (X)PL. En este caso es
posible usar tambi�n la correcci�n herramienta.
Direcci�n de trabajo
La
direcci�n de trabajo de una hoja puede ser:
� a favor de avance: a hoja avanza
empujando los dientes hacia abajo;
� contra-avance: la hoja avanza empujando
los dientes hacia arriba.
La
direcci�n de trabajo puede programarse en el equipamiento de la herramienta con
el par�metro �Direcci�n de trabajo� (con valores: +/-), pero se necesita tener
en cuenta que La direcci�n de trabajo efectiva depende tambi�n de los dem�s
factores:
� el sentido en el cual est� montada la
hoja en el mandril;
� el sentido de rotaci�n del mandril.
Si las
condiciones mec�nicas lo permiten, se recomienda controlar que la hoja, una vez
montada en el mandril, gire frente al operador de modo que el movimiento en
sentido del reloj sea en avance.
En tal
caso, para programar el sentido de trabajo con el par�metro �Direcci�n de
trabajo� se utiliza:
� en avance: +;
� contra-avance: -.
Durante
el trabajo con hoja, Xilog Plus controla las herramientas seg�n estos
principios:
� la caja de los engranajes se coloca a la
izquierda del sentido de corte;
� la direcci�n de corte en contra-avance se
obtiene invirtiendo el sentido de recorrido del trabajo.
Se
except�an los cortes ortogonales
realizados con eje Vector y cabezal Prisma: en estos casos, la hoja se gira
de 180 grados, sin invertir el sentido de recorrido del trabajo.
Para
ganar tiempo durante los trabajos que prev�n la alternancia del sentido de
trabajo a favor/contra-avance, la misma herramienta se puede configurar como
dos herramientas separadas pero iguales (se except�a el sentido de trabajo
diferente), asignando a cado uno de los dos el mismo n�mero de grupo (par�metro
�N�mero adicional�): de este
modo, Xilog Plus reducir� el m�nimo las pausas entre los trabajos.
AP�NDICE M. Funciones adicionales
Calculadora
Si, en un determinado ambiente, el cursor se
encuentra en un campo editable habilitado solamente para la recepci�n de los
datos num�ricos, en el visor de la calculadora aparece el valor escrito en
aquel determinado campo. Oprimiendo la tecla [F6] el valor que aparece
en el visor de la calculadora queda indicado en el campo editable que contiene
el cursor.
Adem�s de la posibilidad
de operar con las teclas del teclado f�sico, est�n disponibles las siguientes
funciones (donde X es el valor visualizado en el visor e Y es el valor de la
memoria de la calculadora):
[S]
Seno de X.
[I]
Arco seno de X.
[C]
Coseno de X.
[O]
Arco coseno de X.
[T]
Tangente de X.
[N]
Arco tangente de X.
[P]
X = valor constante pi.
[R]
Ra�z cuadrada de X.
[L]�

Borrar memoria: Y = 0.
Funciones
de backup y restore
La funci�n di backup permite hacer una copia
en disco o cinta (o bien en la red) de todos los archivos ubicados en los
directorios principales del editor de Xilog
Plus. En la funci�n de backup, est�n comprendidos todos los archivos
situados en todos los subdirectorios de todos los directorios principales,
excepto los archivos de configuraci�n.
Es posible elegir la realizaci�n del backup
selectivo (por ejemplo s�lo de los programas) o completo. Si se selecciona la
unidad disco del floppy disk,
no es posible hacer el backup de aquellos archivos que superen la dimensi�n del
floppy disk. Esto sucede porque
los archivos son copiados sin comprimir en la unidad de disco seleccionada.
Cuando se termina el espacio disponible en el disco, se solicita la
introducci�n de un nuevo disco en la unidad de backup.
La funci�n de restore permite recuperar en el
disco principal los archivos anteriormente salvados en una sesi�n de backup. Si
se selecciona la unidad disco del floppy disk, como los discos no son
autom�ticamente catalogados, es tarea del usuario proceder a la recuperaci�n
introduciendo - uno a la vez (independientemente del orden) - todos los discos
del backup. Al final de la recuperaci�n de cada disco, se solicita la
introducci�n de un nuevo disco (si es que los hay).

AP�NDICE
N. Notas
Gesti�n
de los programas PGM
Edici�n
Pueden editarse y visualizarse gr�ficamente
programas con dimensiones de hasta 32700 l�neas aproximadamente.
Ejecuci�n
Pueden ejecutarse todos los programas
editables que produzcan como m�ximo unas 65500 instrucciones operativas. Las instrucciones
operativas son las siguientes, a saber: H, REF, F, BR, B, N, TA, G0, G1, G2,
G3, SET, MSG, ISO, VT, VROW, ENDVT, G0R, G1R, G2R, G3R.
En caso de necesidad el l�mite de unas 65500
instrucciones operativas puede aumentarse; sin embargo, no se aconseja dicha
modificaci�n puesto que las prestaciones del sistema podr�an degradar.
Gesti�n
directa de los programas ISO
En algunos tipos de m�quinas equipadas con
controlador NUM� existe una gesti�n directa de los programas ISO. Un
programa ISO es un archivo con extensi�n CNC que puede editarse libremente y
verse gr�ficamente; esta �ltima funcionalidad se solicita al Control Num�rico
y, por lo tanto, s�lo est� operativa con el Control Num�rico conectado. Los
nombres de los archivos CNC deben elegirse seg�n la convenci�n NUM�;
por lo tanto, cada nombre debe estar formado como m�ximo por 5 cifras num�ricas
seguidas por un 0 (cero).
Edici�n
Pueden editarse y visualizarse gr�ficamente
programas con dimensiones de hasta 65000 caracteres aproximadamente; para editar
programas de mayor dimensi�n hay que utilizar editores externos a Xilog Plus.
Los programas por debajo de la dimensi�n
l�mite pueden visualizarse gr�ficamente s�lo si en la memoria del Control
Num�rico hay espacio� suficiente para
contenerlos; asimismo, los posibles subprogramas deben ser trasladados
precedentemente a la memoria del Control Num�rico.
Ejecuci�n
El l�mite de los aproximadamente 65000
caracteres no se aplica para la ejecuci�n de los programas; sin embargo, valen
las siguientes consideraciones:
� si el programa a ejecutar contiene saltos
es necesario establecer el par�metro �Modo pasante CNC� del archivo de configuraci�n gendata.cfg a 0; en
tal caso el programa podr� ejecutarse solamente si en la memoria del Control
Num�rico hay espacio suficiente para contenerlo; asimismo, los posibles
subprogramas deber�n ser trasladados precedentemente a la memoria del Control
Num�rico.
� si el programa a ejecutar no contiene
saltos deber� programarse el par�metro �Modo pasante CNC� del archivo de configuraci�n gendata.cfg a 1; de
este modo el programa ser� trasladado al Control Num�rico en bloques; por lo
tanto, el �nico l�mite para sus dimensiones est� constituido por el espacio
libre en el disco duro del Ordenador Personal; sin embargo, los posibles subprogramas
deber�n ser trasladados precedentemente a la memoria del Control Num�rico.
M02
En los programas CNC todos los bloques M02
deben estar precedidos por un bloque M201; en caso de que no exista dicho
bloque, el programa sigue comport�ndose correctamente pero al concluir, el
color del �rea permanece� verde y el
contador de las piezas producidas no decrementa; ante esta situaci�n es
necesario pulsar F10 (Reset) para informar al Panel de la m�quina de Xilog Plus de que el programa ha
finalizado. Si se est� reutilizando un viejo programa CNC, editarlo e
introducir manualmente el c�digo M201 requerido.
M20
La presencia del c�digo M20 , en lugar del M2
( en los trabajos pendulares ), permite no cerrar la ejecuci�n en el modo
pasante y por lo tanto ganar tiempo al pasar de una �rea de trabajo (por ej.
�rea A) a otra (por ej. �rea B). Si se est� reutilizando un viejo programa CNC,
editarlo e introducir manualmente el c�digo M20 requerido.
Acercamiento
al trabajo
En algunas m�quinas el cabezal que debe realizar
el primer trabajo sobre el tablero baja antes o durante la traslaci�n; la cota
Z a la cual debe efectuarse el traslado se determina �nicamente en funci�n de la dimensi�n Z del tablero (valor del
campo DZ del encabezamiento del programa); por lo tanto, no se tiene en cuenta
la dimensi�n total de los tableros que se hallen posiblemente en otras zonas de
trabajo. En caso de choque contra los otros tableros ser� necesario anteponer,
al primer trabajo del programa, una o varias instrucciones N o XN a trav�s de
las cuales controlar la traslaci�n con seguridad. El mismo procedimiento deber�
aplicarse tambi�n en los trabajos sucesivos, en caso de que los cabezales deban
ser trasladados por encima de otros tableros.
Traslaciones
sobre la mesa
Las traslaciones de los cabezales, en fase de
acercamiento al punto de inicio del trabajo sucesivo, est�n optimizadas en
funci�n de las herramientas / grupos de la dimensi�n Z del tablero. Si no
existe una cota de seguridad a la cual realizar el traslado sobre el tablero con
las herramientas / grupos montados, se emite el error �No existe cota de
seguridad sobre la pieza�.
Casos no
recuperables
En los siguientes casos el error: �No existe
cota de seguridad encima de la pieza�, no puede recuperarse:
1. Si se puede trasladar con el cabezal
neum�ticamente alto:
� BR o XBR con herramienta configurada
sobre la cara 0
� TA o XTA sobre la cara 1
� B o XB sobre la superficie inclinada
2. Si tampoco se puede trasladar con el
cabezal neum�ticamente alto:
� BR o XBR con herramienta configurada
sobre la cara 0
� TA o XTA
� B o XB sobre la superficie inclinada
Los otros casos pueden recuperarse utilizando
la instrucci�n SET DONTCARE.
Selector
NO EDIT
En el panel de control de la m�quina
perforadora � fresadora hay un selector con llave, que permite
habilitar/inhabilitar la posibilidad de modificar y memorizar en modo
permanente los datos contenidos en el interior de un programa o la
configuraci�n del software, de los equipamientos o de los archivos ISO.
En el caso de inhabilitaci�n de dicha funci�n,
de todas maneras es siempre posible tener acceso a los Editor arriba
mencionados, pero no es posible memorizar eventuales modificaciones efectuadas
en los documentos abiertos (acceso s�lo a la visualizaci�n).
AP�NDICE O. Paleta (dispositivo transporta-virutas
rotatorio)
Programaci�n
SET DUSTPAN
En el lenguaje Xiso, la instrucci�n para
accionar la paleta sobre el mandril es la SET DUSTPAN. Hasta hoy, la set puede
asumir los valores 0(Off) y 1(On).
SET DUSTPANOFFSET
Set de habilitaci�n del offset-distancia entre
la paleta y el radio �til medido hortogon�lmente respecto a la trayectoria.
El dispositivo paleta, una vez calibrado, se
posiciona a lo largo de la trayectoria de la herramienta con un valor 0 de la
SET DUSTPANOFFSET.
En funci�n de cuanto se substraiga y del tipo
de correcci�n se distancia la paleta del panel para evitar colisiones.
�
La diferencia sustancial entre C1 y C2 es que
con el primer tipo de correcci�n la paleta roza el bruto, por tanto es
necesario configurar un valor igual a la profundidad de desbaste m�s un offset
de seguridad, vista la irregularidad del material no trabajado.
Con el segundo tipo de correcci�n, la paleta
puede rozar el material ya trabajado, por tanto, un offset ligeramente mayor de
0 garantiza una recogida �ptima de la viruta y una buena seguridad de
anticolisi�n.
El valor de default es SET DUSTPANOFFSET =
Radio �til
INSTRUCCIONES PERFIL
La paleta en el mandril est� habilitada solo
sobre instrucciones de fresado: G0, G1, G2, G3, G5 y de tipo R. Las
instrucciones de perforaci�n B y BR no se pueden operar con estas opciones,
esto vale tambi�n para la herramienta paleta.
Programaci�n sin la paleta:
C1
G0 X=0 Y=0 Z=-DZ-1 T=101
G1 X=DX
Programaci�n con la paleta a 5 mm del perfil:
SET DUSTPAN = 1
SET DUSTPANOFFSET = 5
C1
G0 X=0 Y=0 Z=-DZ-1 T=101
G1 X=DX

Configuraci�n
Pheads.cfg
Para configurar correctamente el dispositivo,
ante todo es necesario configurar seis par�metros de la Cabeza adecuada de
Pheads.cfg.
Tipo de dispositivo especial: Tipo del dispositivo, esto permite configurar un dispositivo paleta
en lugar de un soplador u otro. El valor preestablecido para la paleta es 1, 0
para no presente.
�ngulo 0 Vector - Perno: �ngulo formado entre el 0 trigonom�trico y el 0 Vector.
�ngulo Perno -Paleta: �ngulo formado entre el 0 Vector y la extremidad de la paleta. Valor
suministrado por la oficina t�cnica y personalizado en funci�n de los juegos mec�nicos.
Radio Paleta:
Radio formado entre el....de la extremidad de la Paleta y el centro del
mandril.
Radio m�ximo admitido...: Radio m�ximo de la herramienta admitido con el dispositivo
habilitado. Se quiere evitar, con un control preventivo, el uso de las
herramientas no compatibles con el dispositivo.
Dimensi�n en Z del dispositivo...: Longitud del dispositivo paleta insertado en la cabeza, la medida se
debe realizar sobre la misma referencia de la herramienta.
La medida se asume como dimensi�n de la
herramienta en elaboraci�n, en el caso en el que la longitud de la herramienta
seleccionada es inferior a la longitud de la paleta en la posici�n de trabajo.
Se ignora en el caso en el que la longitud de
la herramienta seleccionada es superior o igual a la longitud de la paleta en
la posici�n de trabajo.
�
Nci.cfg
Para evitar desenrollados particulares del eje
Vector en el paso de un perfil al otro, es posible habilitar la solicitud del
c�lculo del anti-desenrollado mediante clave �$�.esto permite optimizar la
rotaci�n del eje y aprovecharla al m�ximo en el interior de los finales de
carrera configurados.
La clave en cuesti�n es:
$GEN_OPTVECTOR
1
$
Gesti�n de paleta con Routolink Carpinter�a
Utilizando las macros de routolink
carpinter�a, la paleta se activar� configurando la variable offsetpaleta > 0
en el programa de apertura o abriendo las macros (circunda, perfila y perfilar)
con el par�metro ofp>0.
La variable offsetpaleta presente en el
programa se hereda de todas las macros abiertas en el programa.
Las macros, cuando encuentran la variable
offsetpaleta > 0, activan las instrucciones:
SET DUSTPAN=1
SET DUSTPANOFFSET=OFFSETPALETA
Cada macro preparada para utilizar la paleta
pondr� a disposici�n dos par�metros, que le permitir�n al usuario modificar el
offset o desactivar el uso de la paleta.
Los par�metros en cuesti�n son:
PAR PALETTA=1
PAR OFP=0
Si del programa de apertura, despu�s de haber
configurado offsetpaleta=2, se quisiera:
1. desactivar la paleta en la macro � se deber�a abrir la macro especificando el par�metro paleta=0 en el
campo �par�metros macro�
2. modificar el valor offset paleta en la
macro � se deber�a abrir la macro
especificando el par�metro ofp=5 en el campo �par�metros macro�
Ejemplo:
MAIN.PGM
1 L OFFSETPALETA=2
2 CIRCUNDA �.. ����
3 PERFILA �.. �.. ��
4 CIRCUNDA �.. ���� PALETA=0
5 CIRCUNDA �.. ����
6 CIRCUNDA �.. ���� OFP=5
En el ejemplo mostrado, el programa principal
activa la paleta en todas las macros menos la �4 circunda �.. ���� paleta=0�,
en la que la paleta no se usar�.
En todas las macros el offset paleta ser� de 2
mm, menos en la �6 circunda �.. ���� ofp=5�, donde el offset ser� de 5 mm, en
cuanto ofp =5 permanece en el offset general, offsetpaleta=2 mm.
Situaci�n par�metros para la solicitud de
trabajar con la paleta:
Comportamiento en base a la solicitud paleta y
a la paleta f�sica:
Esta gesti�n est� disponible en la versi�n
definitiva de xilog igual o superior a la 1.12.981.
Utilizo paleta con herramienta sobre ejes
portafresas
� es necesario respetar la cota m�nima para
evitar interferencias con la paleta
� es �til respetar la cota m�xima para no
reducir la eficacia de la paleta
� con piezas de altura superior a los 70
mm, la paleta no cubre totalmente el perfil de la pieza en elaboraci�n
Se puede exceder el di�metro m�ximo de la
herramienta modificando la paleta (esto implica una reducci�n de la eficacia de
la misma)
Utilizo cabezales angulares en presencia de
paleta
� los cabezales mpa actuales son
compatibles con la elaboraci�n de piezas m�x. 68 mm
� los cabezales ser�n modificados para
poder trabajar piezas hasta� 98 mm
� cabezales mpa actuales
� cabezales mpa futuros

AP�NDICE
P. Tecno: elaboraciones de cabezas paralelas
Generalidades
La nueva gama de m�quinas Tecno, en las que
las cabezas operadoras est�n provistas cada una de un movimiento vertical (eje
Z) aut�nomo, ofrece la nueva modalidad operativa de sincronizaci�n de la cabeza
Basic y Prisma, para realizar, en paralelo, dos piezas id�nticas, ubicados en
el plano de trabajo a lo largo de la direcci�n Y a una distancia igual al
intereje de las dos cabezas.
Est� modalidad ha sido copiada de las m�quinas
Ergon, donde el n�mero de cabezas sincronizables para las elaboraciones en
paralelo pueden ser tambi�n superiores a dos.
Limitaciones
El uso en paralelo de la cabeza Prisma y de la
cabeza Basic, tiene una serie de limitaciones que se muestran a continuaci�n:
a. se admiten solamente elaboraciones en la cara superior de la pieza
(cara 1)
b. se admiten solamente elaboraciones con herramientas verticales
c. no son admitidas elaboraciones 3D
d. no son admitidas elaboraciones con �intervector�
e. la cabeza master en la lista herramienta PGM es siempre la Prisma
Configuraci�n
La posibilidad de trabajar con cabezas
paralelas sigue las reglas previamente configuradas para el uso de las m�quinas
Ergon, es decir solicita, como condici�n de base, que las cabezas a sincronizar
sean:
a. de la misma tipolog�a (par�metro �Actuador� - Pheads.cfg)
b. del mismo orden (par�metro �Orden testa� - Pheads.cfg)
c. asociadas a diferentes ejes Z (par�metro �Grupo de pertenencia� -
Pheads.cfg)
En el caso de Tecno, la cabezas a sincronizar
son normalmente de tipolog�a diferente, es decir una es de tipo Basic
(Actuador=0) y la otra es de tipo Prisma (Actuador=10). Desde el punto de vista
de la fabricaci�n, la realizaci�n mec�nica ha sido realizada de manera que las
dos cabezas se encuentren alineadas en el centro de la herramienta a lo largo
del eje Y. El vector de la cabeza Prisma debe necesariamente encontrarse a una
posici�n espec�fica para poder operar en paralelo con la cabeza Basic; esta
posici�n puede asumir dos valores angulares que�� difieren entre ellos de 180�. Lo que cambia entre las dos
posiciones angulares de la Prisma, es el intereje que se forma entre las dos
cabezas y por tanto la distancia a la que posicionar las dos piezas a trabajar
contempor�neamente sobre el plano.
En este caso, se viola la regla �a.�
mencionada previamente; para forzar esta regla, es necesario introducir una
directiva bajo forma de clave NCI (archivo Nci.cfg). La directiva es la
siguiente:
$GEN_SYNCRO_PRISMA_ENABLE
1
$
El valor de la clave igual a �1�, permite al
sistema Xilog de trabajar en paralelo con una cabeza Prisma y una cabeza Basic.
Por tanto, es indispensable introducir esta clave en el archivo Nci.cfg de las
m�quinas Tecno que est�n preparadas mec�nicamente para esta modalidad
operativa.
En ausencia de la clave, el valore asumido es
�0�, por tanto por default no se admite trabajar en paralelo con cabeza Prisma
y Basic.
La posici�n del eje vector de la cabeza Prisma
es, seg�n la gesti�n can�nica inherente a las elaboraciones sobre la cara 1,
aquella especificada en el par�metro �Cota de toma angular� relativa a la
cabeza y ubicada en la secci�n par�metros Pheads.cfg de Xilog.
Programaci�n
Las reglas de programaci�n a la base de un
programa PGM para la gesti�n de las elaboraciones de cabezas paralelas de una
Tecno, son las mismas de una m�quina Ergon y como tales se encuentran descritas
en el Ap�ndice F� del manual del Editor de�
Xilog Plus.
La �nica advertencia que se debe subrayar en
este contexto, es que en el acoplamiento con la cabeza Basic, la cabeza Prisma
debe resultar siempre como cabeza "maestra". Esto significa que en la
lista de herramientas especificada en el campo �T� de las instrucciones de
inicio perfil (XG0, XG0R, XB), el primer n�mero que aparece debe ser la
combinaci�n cabeza+herramienta correspondiente a la cabeza Prisma.�
Ejemplo de programa
Suponiendo que, por ejemplo se quiera trabajar
contempor�neamente dos piezas (P1 e P2 � fig.1) posicionadas una al lado de la
otra a la distancia en Y entre la cabeza Basic (T100 � cabeza 3 en Pheads.cfg)
y la cabeza Prisma (T200 � cabeza 4 en Pheads.cfg), considerando una de las dos
posiciones notables asumida por el eje vector de la Prisma.
Si se quiere por ejemplo realizar un fresado
con al herramienta 5 para la Prisma y 12 para la Basic. Suponiendo adem�s que
se quiera trabajar en �rea AB. La disposici�n de las dos piezas ser� como la
que se muestra en la fig. 1:
Fig. 1
Como indicado gr�ficamente por las flechas
rojas, ser�n empleadas en la elaboraci�n las dos cabezas 100 y 200
contempor�neamente, una trabajar� sobre
la pieza P1 y la otra sobre la pieza P2.
Por tanto, ser� suficiente escribir, en el
programa, estas instrucciones:
H DX=� DY=�
DZ=� BX=� BY=� BZ=� /�Def�
XG0 X=� Y=� Z=� T=205 112
XG1 X=� Y=� Z=�
Seg�n lo mencionado previamente, si se indica
como lista de herramientas �T=112 205�, y es decir se considera la cabeza Basic
como maestra, Xilog emite un error en fase de carga programa (PanelMac):
Prestaciones
extra
Como se ha mostrado en los p�rrafos
precedentes, las dos cabezas, Basic y Prisma, pueden trabajar en paralelo a
condici�n de que el vector de la Prisma se encuentre en una de las dos
posiciones posibles que llevan el centro de las dos cabezas alineado a lo largo
del montante (direcci�n Y), como se puede deducir f�cilmente de las siguientes
figuras:
Fig.2� Fig.3
En los p�rrafos precedentes, se muestra el
comportamiento del caso est�ndar en el que ha sido previsto que la cabeza
Prisma posiciona su propio eje vector al valor indicado por el par�metro �Cota
de toma angular�[8]
que se muestra en Pheads.cfg. Al modificar esta cota de configuraci�n, por
consiguiente se modifica tambi�n la posici�n angular del vector de la Prisma
con la que esta cabeza trabajar� en paralelo junto con la cabeza Basic.
En el caso quisieran ser aprovechadas m�s
posiciones angulares programables en un PGM, dejando inalterado el valor de
configuraci�n �Cota de toma angular�, puede ser utilizada la macro �XHSYNASS� para
identificar un determinado orden angular de la Prisma, combinado con el valor
de la clave NCI (file Nci.cfg) �$Hnn_QVEC_SYN�.
Descripci�n clave
El formato del valor de la clave
�Hnn_QVEC_SYN�, en el que �nn� representa el n�mero de la cabeza a al que se
hace referencia, es el de una serie de n�meros separados por coma, que
representan el valor del �ngulo vector de la cabeza� Prisma para cada uno de las 4 (m�ximo) posiciones programables de
la m�quina cuando trabaja en paralelo.�
Considerando como ejemplo la siguiente
configuraci�n de la clave:
$H04_QVEC_SYN
-100, -150, -200, -250
$
�
Esta indica que en
el caso de elaboraciones en paralelo de la cabeza 4 (de tipo Prisma) con otra
cabeza:
si est� especificado el uso del orden �1�, el
vector ser� posicionado al valor �-100�
si est� especificado el uso del orden �2�, el
vector ser� posicionado al valor �-150�
si est� especificado el uso del orden �3�, el
vector ser� posicionado al valor �-200�
si est� especificado el uso del orden �4�, el
vector ser� posicionado al valor �-250�
Descripci�n
macro
La macro �XHSYNASS� se muestra con la
siguiente gr�fica:
y requiere un solo par�metro, o sea, el orden,
de �0� a �4� requerido para la posici�n del vector de la cabeza Prisma en el
caso de elaboraci�n en cabezas paralelas.
La regla de referencia es la siguiente:
N�mero de orden = �0�: la cuota angular del
vector de la Prisma en modalidad cabezas paralelas es la indicada en el
par�metro de configuraci�n �Cuota de detecci�n angular� del Pheads.cfg
N�mero de orden = �n� [n=1,..,4]: la cuota
angular del vector de la Prisma en modalidad cabezas paralelas es la indicada
en la clave Hnn_QVEC_SYN, seg�n lo especificado en el p�rrafo anterior
N�mero de orden = �n� [n= <1 o >4]: la
cuota angular del vector de la Prisma en modalidad cabezas paralelas es la
indicada en el par�metro de configuraci�n �Cuota de detecci�n angular� del
Pheads.cfg
Ausencia de la clave Hnn_QVEC_SYN:
independientemente del valor expresado en input de la macro, a cuota angular
del vector de la Prisma en modalidad cabezas paralelas es la indicada en el
par�metro de configuraci�n �Cuota de detecci�n angular� del Pheads.cfg
Ejemplo
de programa
Suponiendo que se quiera, por ejemplo,
trabajar simult�neamente dos piezas (P1 e P2 � fig.1),
ubicadas una al lado de la otra a la distancia en Y entre la cabeza Basic (T100
- cabeza 3 en Pheads.cfg) y la cabeza Prisma (T200 - cabeza 4 en Pheads.cfg),
considerando la posici�n notable asumida por el eje vector de la Prisma
equivalente a 90� en el caso del programa PGM_90 y equivalente a 270� en el
caso del programa PGM_270.
Si se quiere por ejemplo realizar un fresado
con la herramienta 5 para la Prisma y 12 para la Basic. Suponiendo adem�s que
se quiera trabajar en �rea AB. La disposici�n de las dos piezas ser� como la de
la figura 1, mostrada anteriormente. Se asume adem�s la programaci�n siguiente
de la clave H04_QVEC_SYN:
$H04_QVEC_SYN
90, 270
$
Los dos programas aparecen como sigue:
PGM_90
H DX=� DY=�
DZ=� BX=� BY=� BZ=�
/�Def�
XHSYNASS
a=1
XG0 X=� Y=� Z=� T=205 112
XG1 X=� Y=� Z=�
PGM_270
H DX=� DY=�
DZ=� BX=� BY=� BZ=� /�Def�
XHSYNASS a=2
XG0 X=� Y=� Z=� T=205 112
XG1 X=� Y=� Z=�
Operativamente, la cabeza Prisma (T200), despu�s
del posible cambio de herramienta que posiciona el vector a la �Cota de toma
angular� (Pheads), antes de realizar la entrada en la pieza, ser� sometida al
posicionamiento del vector a la cota 90� en el programa PGM_90 o 270� en el
programa PGM_270. Al final de la elaboraci�n, el vector ser� posicionado
nuevamente a la �Cota de toma angular� (Pheads).

[1] Es.: para el �rea AB, el �rea master es A
[2] Ej.: para el �rea AB, el �rea asociada es B
[4] Los clavos disparados en Mdi no se cuentan.
[5] Ambos datos pasan al Plc.
[6] El control acerca de la compatibilidad de los lados de conexi�n a la
correa en el caso de plano EASY-SET queda de todas manera activado.
[7] Tope de fondo lateral para referencia al cero del �rea
[8] Tipicamente es el valor al que se posiciona el vector para realizar el
cambio herramienta en el almac�n preferencial de la cabeza y como tal es el
valor al que siempre se posiciona la cabeza al final de una elaboraci�n.