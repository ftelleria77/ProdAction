
# 8.8# Descripci�n
de los archivos
En los archivos de formato ASCII del Editor de
las mesas de trabajo se puede distinguir una serie de secciones definidas por [Secci�n] � [END_Secci�n], cada una de ellas representa la programaci�n de un
objeto especial de la mesa travesa�os y ventosas o de la mesa multifuncional.
Dentro de cada secci�n se encuentran los datos que caracterizan la programaci�n
de cada objeto: [NombreDato]� Valor.
Ejemplo
de un archivo ASCII para mesa travesa�os y ventosas.

[TIPOPIANO]
TV
Tipo de mesa.

[OLD_SPECULARE_X]
0
Valor especular de X en el momento de la
memorizaci�n.

[OLD_SPECULARE_Y]
0
Valor especular de Y en el momento de la
memorizaci�n.

[TRAVERSA]

[X]
300.000
Cota referida al origen OP (=�origen panel�) del
centro de la viga.

[E]
1
Estado de habilitaci�n de la viga. La
habilitaci�n se puede realizar mediante los visualizadores.

[PAV_NUMTRAV]
1
N�mero de la viga desde el algoritmo de la
programaci�n autom�tica de las ventosas.

[PAV_ENABLE]
1
Estado de habilitaci�n de la viga durante la
programaci�n autom�tica de las ventosas.

[PAV_STEP] �������
0.000
Paso entre dos ventosas en la misma viga durante
la programaci�n autom�tica de las ventosas.

[PAV_MAXNUMVENT]
3
N�mero m�ximo de ventosas que se pueden
introducir en la misma viga durante la programaci�n autom�tica de las
ventosas.

[BAC]

[NAME]
Nombre
Nombre de la barra sube carga (o barra
elevadora).

[POS]
SX
Posici�n en la viga (SX=�izq.� , DX=�der.�).

[END_BAC]

[VENTOSA]

[NAME]
Nombre
Nombre de la ventosa.

[X]
300.000
Cota referida al origen OP (=�origen panel�) del
centro X de la base.

[Y]
134.765
Cota referida al origen OP del centro Y de la
base.

[XAPP]
340.000
Cota referida al origen OP del centro X del
apoyo principal.

[YAPP]
104.765
Cota referida al origen OP del centro Y del
apoyo principal.

[XAPP2]
0.000
Cota referida al origen OP del centro X del
apoyo secundario (s�lo en presencia de apoyo secundario).

[YAPP2]
0.000
Cota referida al origen OP del centro Y del
apoyo secundario (s�lo en presencia de apoyo secundario).

[ALFAAPP]
0.000
Cota referida en grado del �ngulo de rotaci�n
del apoyo principal, respecto de su centro de rotaci�n.

[ALFAAPP2]
0.000
Cota referida en grado del �ngulo de rotaci�n
del apoyo secundario, respecto de su centro de rotaci�n (s�lo en presencia de
apoyo secundario).

[ALFABASE]
0.000
Cota referida en grados del �ngulo de rotaci�n
de la base.

[SIMSUPPORT]
SIMX
Tipo de simetr�a del apoyo principal (SIMX,
SIMY, SIMXY, NDEF).

[SIMSUPPORT2]
SIMY
Tipo de simetr�a del apoyo secundario (SIMX,
SIMY, SIMXY, NDEF; s�lo en presencia de apoyo secundario).

[LKEY]
1
ID asociado al soporte.

[LKEY2]
2
ID asociado al apoyo secundario (s�lo en
presencia de apoyo secundario).

[END_VENTOSA]

[MORSETTO]

[NAME]
Nombre
Nombre del borne.

[Y]
111
Cota referida al origen OP (=�origen panel�) del
centro Y de la base.

[LATOINSM]
NDEF
Lado de introducci�n del borne en la viga, que
puede ser SX (=�izq.�), NDEF (no definido o central) o DX (=�der.�).

[LKEY]
2
ID asociado al soporte.

[ALFABASE]
0.000
Cota referida en grados del �ngulo de rotaci�n
de la base.

[SIMSUPPORT]
SIMX
Tipo de simetr�a del apoyo principal (SIMX,
SIMY, SIMXY, NDEF).

[END_MORSETTO]

[END_TRAVERSA]

[BARRAM]

[TYPE]
OFF
Tipo de barra m�vil configurada (FIXED, ON, OFF,
CONTINUA).

[X]
300.000
Cota referida al origen OP del centro de la
viga.

[BAP]

[NAME]
Nome
Nombre del tope de apoyo pieza.

[TIPO]
LATERALE
Tipo de tope en la mesa, que puede ser LATERALE
(=�lateral�)� o CENTRALE (=�central�).

[OFFSET]
23..5
Distancia referida al origen OP (=�origen
panel�)� del centro Y del tope de
apoyo pieza.

[END_BAP]

�
[END_BARRAM]

Ejemplo
de un archivo ASCII para mesa multifuncional.

[TIPOPIANO]
MLTF
Tipo de mesa.

[OLD_SPECULARE_X]
0
Valor especular de X en el momento de la
memorizaci�n.

[OLD_SPECULARE_Y]
0
Valor especular de Y en el momento de la
memorizaci�n.

[VENTOSA]

[NAME]
Nombre
Nombre de la ventosa.

[X]
300.000
Cota referida al origen OP (=�origen panel�) del
centro X de la base.

[Y]
134.765
Cota referida al origen OP del centro Y de la
base.

[XAPP]
340.000
Cota referida al origen OP del centro X del
apoyo principal.

[YAPP] �
104.765
Cota referida al origen OP del centro Y del
apoyo principal.

[XAPP2]
0.000
Cota referida al origen OP del centro X del
apoyo secundario (s�lo en presencia de apoyo secundario).

[YAPP2]
0.000
Cota referida al origen OP del centro Y del
apoyo secundario (s�lo en presencia de apoyo secundario).

[ALFAAPP]
0.000
Cota referida en grados del �ngulo de rotaci�n
del apoyo, respecto de su centro de rotaci�n.

[ALFAAPP2]
0.000
Cota referida en grado del �ngulo de rotaci�n
del apoyo secundario, respecto de su centro de rotaci�n (s�lo en presencia de
apoyo secundario).

[ALFABASE]
0.000
Cota referida en grados del �ngulo de rotaci�n
de la base.

[SIMSUPPORT]
SIMX
Tipo de simetr�a del apoyo principal (SIMX,
SIMY, SIMXY, NDEF).

[SIMSUPPORT2]
SIMY
Tipo de simetr�a del apoyo secundario (SIMX,
SIMY, SIMXY, NDEF; s�lo en presencia de apoyo secundario).

[LKEY]
1
ID asociado al soporte.

[LKEY2]
2
ID asociado al apoyo secundario (s�lo en
presencia de apoyo secundario).

[END_VENTOSA]

[MODULSET]

[NAME]
Nombre
Nombre del modulset.

[XM]�����
111
Cota referida al origen OP (=�origen panel�)� del centro X de macho.

[YM]
222
Cota referida al origen OP del centro Y de
macho.

[XF]
333
Cota referida al origen OP del centro X de la
hembra.

[YF]
444
Cota referida al origen OP del centro Y de la
hembra.

[ALFA]
45
Cota referida en grados del �ngulo de rotaci�n
del punto hembra, respecto del punto macho.

[LKEY]
2
ID asociado al soporte.

[END_MODULSET]

[GUARNIZIONE]

[POINT]
111,222,3
111: cota del centro X del punto (respecto a
OP).
222: cota del centroY del punto (respecto a OP).
3: ID asociado al soporte.

[POINT]
333,444,4
(v�ase arriba)

�

[END_GUARNIZIONE]

[BAP]

[NAME]
Nombre
Nombre del tope de apoyo pieza.

[TIPO]
LATERALE
Tipo de tope en la mesa, que puede ser LATERALE
(=�lateral�)� o CENTRALE (=�central�).

[OFFSET]
23.5
Distancia referida al origen OP (=�origen
panel�)� del centro X o Y del tope de
apoyo pieza:
- si el Tipo es LATERALE/CENTRALE entonces el
offset es el centro X;
- si el Tipo es de Fondo entonces el offset es
el centro Y.

[END_BAP]