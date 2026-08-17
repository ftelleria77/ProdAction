# Parámetros — el panel «Parámetros» de Maestro y su forma en el `.pgmx`

**Época nueva, 2026-08-15/16.** Fixtures manuales hechos por Fermín en Maestro sobre
`R_PV_manual_base`, uno por combinación, cada uno partiendo de la base limpia. Este
documento cubre **la etapa 1** (qué escribe Maestro en el `.pgmx`); si un parámetro deja o
no rastro en el ISO es la etapa 2 y sigue abierto — ver el final.

Es el frente **A7** de la hoja de ruta, con una corrección de partida: A7 lo planteaba como
dos temas —«parámetros de usuario **y** dimensiones paramétricas»— y son **el mismo
mecanismo**. Las dimensiones de la pieza ya son parámetros: `dx1`/`dy1`/`dz1` viven en la
misma tabla, con la misma estructura, y la pieza las referencia por nombre.

## 1. Nomenclatura: Maestro usa las dos palabras

| dónde | cómo lo llama |
|---|---|
| panel inferior izquierdo | **«Parámetros»** |
| diálogo de alta/edición | **«Parámetro»** (con el rótulo fijo `A,B` arriba) |
| tooltip del botón de alta | **«Crear una nueva variable»** |
| el `.pgmx` | `<Variables>` → `<a:Variable>`, `ObjectType = …Parametrics.Variable` |
| nuestro código | `ParametricVariableSpec`, `parametric_variables` |

No hay una traducción que corregir: **Maestro mismo mezcla «parámetro» y «variable»**. El
nombre `Variable` del código está respaldado por el XML (excepción legítima de la regla 3);
lo que hace falta es dejar escrito el sinónimo, porque quien lo busque en la UI lo va a
encontrar como «Parámetro».

⚠️ **No existe «variable de usuario» en la UI.** Es un nombre nuestro. El fixture
sintetizado `R001/R_PV_variable_usuario.pgmx` lo lleva en el nombre del archivo.

## 2. La ventana «Parámetro», paso a paso

Instructivo de Fermín (2026-08-16), con captura por paso:

1. Click en **«Crear una nueva variable»** (primer icono de la barra del panel Parámetros;
   el segundo es **«Editar parámetro»** y el tercero borra).
2. Seleccionar el **Tipo**.
3. Escribir el **Nombre**.
4. Escribir el **Valor** (`True` o `False` si es booleano — se escribe, no es un checkbox).
5. Elegir la **Unidad física**.
6. Opcionalmente, una **Descripción**.

Detalles de la ventana, observados:

- Los dos desplegables tienen **dominio cerrado de tres**, y no hay más opciones.
- **El diálogo abre en `Tipo = Decimal` y `Unidad física = Longitud`** (observado con el
  formulario en blanco, 2026-08-16). ⚠️ Corrige lo que este documento decía antes: que el
  default de la unidad era `Adimensional`. Ese `Adimensional` se había visto en un diálogo
  donde el Tipo **ya estaba en Booleano**.
  > **Hipótesis, con discriminador de un paso**: la unidad la ajusta el Tipo — al elegir
  > `Booleano` la unidad pasa sola a `Adimensional`. Se falsea abriendo el diálogo,
  > cambiando **sólo** el Tipo a Booleano y mirando si la Unidad se movió sin tocarla.
- Con **Nombre o Valor vacíos** el borde se pone rojo y **`Aplicar` queda deshabilitado**.
- El campo Valor **acepta más de tres decimales** al escribir (`12,3456789`), aunque la
  grilla muestre tres.
- El rótulo azul **`A,B`** es **fijo del diálogo**: aparece igual con el formulario en
  blanco, no dice nada del programa.
- La grilla muestra los valores con **coma** decimal (`10,000`); el XML los guarda con
  **punto**. La coma es presentación, no dato.

## 3. La tabla de traducción UI → `.pgmx` — COMPLETA

Los seis valores de los dos desplegables, todos derivados contra archivos de Maestro:

| UI «Tipo» | `<a:Type>` | atributo del valor | formato del valor |
|---|---|---|---|
| **Decimal** | `Double` | `i:type="b:double"` | punto decimal, sin ceros de relleno (`10`, `-12.5`) y **sin redondear** (`12.3456789`) |
| **Entero** | `Integer` | `i:type="b:int"` | `1500` |
| **Booleano** | `Boolean` | `i:type="b:boolean"` | **minúscula**: `true` / `false` (la UI acepta `True`) |

| UI «Unidad física» | `<a:FisicalUnitType>` |
|---|---|
| **Longitud** | `Lenght` |
| **Velocidad** | `Speed` |
| **Adimensional** | `UnitLess` |

⚠️ **`Lenght` va con el typo de SCM.** En el mismo archivo, el `Description` de `dx1` dice
`Length` bien escrito. Las dos formas conviven: la del tag lleva el error y hay que
copiarla tal cual. Nombre de Maestro, intocable (regla 3).

## 4. La forma del nodo

Un parámetro es un `<a:Variable>` dentro de `<Variables>`, siempre con los mismos ocho
campos y en este orden:

```xml
<a:Variable>
  <Key xmlns="…MachiningDataModel.Utility">
    <ID>1930</ID>
    <ObjectType>ScmGroup.XCam.MachiningDataModel.Parametrics.Variable</ObjectType>
  </Key>
  <Name xmlns="…MachiningDataModel.Utility">Nombre_Parametro</Name>
  <a:Description>Una descripción (opcional).</a:Description>
  <a:FisicalUnitType>Speed</a:FisicalUnitType>
  <a:IsReadOnly>false</a:IsReadOnly>
  <a:Scope>Local</a:Scope>
  <a:Type>Integer</a:Type>
  <a:Value i:type="b:int" xmlns:b="http://www.w3.org/2001/XMLSchema">1500</a:Value>
</a:Variable>
```

- **`Key` y `Name` van en el namespace `Utility`**, el resto en `Parametrics`. Escribir
  `Name` en `Parametrics` hace que Maestro lo deserialice nulo y **reviente al abrir el
  archivo** (`VariableList` indexa por nombre). Fue el bug de R001, 2026-08-10.
- `IsReadOnly=false` y `Scope=Local` en los cuatro fixtures. La UI **no expone** ninguno de
  los dos, así que no hay forma de variarlos desde el diálogo.
- Una `Description` vacía se serializa como `<a:Description/>`, no se omite.
- La declaración `xmlns:b` del XSD va **en el propio nodo `Value`**, repetida en cada uno.

### El `ID` arranca en el primer libre del archivo y avanza DENTRO de la sesión

Partiendo siempre del mismo `manual_base` (máximo ID ocupado: 1926), el parámetro nuevo
recibió **1927, 1928, 1930, 1932** … y después **1927 otra vez** (`Presicion`).

- El primer valor de una sesión de edición es **el primer libre del archivo** — que es
  exactamente la regla de nuestro `_reserve_ids`. Dentro de la misma sesión el contador
  sigue avanzando y **no se reinicia al guardar**; los 1930 y 1932 salieron de una sesión
  en la que ya se habían creado y borrado parámetros.
- Al **cerrar y reabrir**, el contador vuelve a partir del archivo: `Presicion` recibió el
  1927 que había quedado libre ⇒ **un `ID` liberado sí se reutiliza**.
- Borrar **no renumera** lo que quedó: al eliminar el 1927 el booleano se quedó con 1928.
- ⇒ Nuestro sintetizador coincide con Maestro **partiendo de un archivo recién abierto**,
  que es el caso normal. En una sesión larga de edición manual pueden divergir, y no
  importa: el `.pgmx` es **entrada** del converter, no salida; lo que se compara es el
  contenido, no los bytes.

⚠️ Corrige lo que este documento afirmaba antes —«los ID los asigna la sesión, no el
archivo, y no son reproducibles»—, que se escribió sin haber visto todavía un archivo
abierto de nuevo.

## 5. Las dimensiones paramétricas son el MISMO mecanismo, con una pieza más

`dx1`/`dy1`/`dz1` son parámetros normales (`Double` / `Lenght`, IDs 1914-1916), con la
única particularidad de que su `Description` trae `Length`/`Width`/`Depth`. Lo que los ata
a la pieza es un nodo **aparte**, un `Parametrics.Expression`:

```xml
<a:Expression>
  <Key><ID>1924</ID>
    <ObjectType>ScmGroup.XCam.MachiningDataModel.Parametrics.Expression</ObjectType></Key>
  <Name/>
  <a:Property><a:Index>-1</a:Index><a:Key i:nil="true"/><a:Name>Length</a:Name></a:Property>
  <a:ReferencedObject>
    <b:ID>1917</b:ID>
    <b:ObjectType>ScmGroup.XCam.MachiningDataModel.ProjectModule.WorkPiece</b:ObjectType>
  </a:ReferencedObject>
  <a:Value>dx1</a:Value>
</a:Expression>
```

Se lee: «la propiedad **`Length`** del objeto **`WorkPiece` 1917** vale la expresión
**`dx1`**». O sea **el `manual_base` ya es paramétrico de fábrica**: DX no guarda `400`,
guarda una referencia al parámetro.

Por eso `build_parametric_variable_spec` rechaza los nombres `dx1`/`dy1`/`dz1`: pisarlos
rompería la expresión que la pieza tiene apuntada.

## 6. Estado del sintetizador

`ParametricVariableSpec` y `build_parametric_variable_spec` ya existían y están exportados
en `pgmx.synthesis`; `build_synthesis_request` acepta `parametric_variables`. Estaban **sin
documentar** (el README lista quince builders públicos y omitía éste) y con los valores de
`Integer`, `b:int` y `Speed` **predefinidos sin evidencia**, de la época anterior.

**Los cuatro fixtures de hoy los derivaron, y los cuatro resultaron correctos.** Verificado
campo por campo y atributo por atributo contra los archivos de Maestro, pasándole al
sintetizador los términos de la UI en castellano (`Entero`, `Velocidad`, `Decimal`,
`Longitud`): la única diferencia es el prefijo de namespace (`ns0:` contra `a:`), que es
estilo de serialización.

## 7. Los fixtures

En `S:\Maestro\Projects\ProdAction\Programas Manuales\Reinvestigación\`:

| archivo | Tipo | Unidad | Valor | qué derivó |
|---|---|---|---|---|
| `R_PV_manual_base_Variable_Usuario_10.pgmx` | Decimal | Longitud | `10` | la forma del nodo, `Double`, `Lenght` |
| `R_PV_manual_base_Booleano_Usuario_True.pgmx` | Booleano | Adimensional | `True` | `Boolean`, `b:boolean`, `true` minúscula, `UnitLess` |
| `R_PV_manual_base_Entero_Velocidad_1500.pgmx` | Entero | Velocidad | `1500` | `Integer`, `b:int`, `Speed` |
| `R_PV_manual_base_Decimal_Longitud_-12_5.pgmx` | Decimal | Longitud | `-12,5` | **punto** decimal y el signo negativo |
| `R_PV_manual_base_Presicion.pgmx` | Decimal | Longitud | `12,3456789` | que Maestro **no redondea**; encontró un defecto nuestro |

Los dos primeros se hicieron encadenados (el del booleano llegó a tener los dos parámetros)
y se corrigió borrando; los dos últimos partieron de la base limpia.

## 8. Lo que queda abierto

> **Orden fijado por Fermín (2026-08-16)**: primero aprender a **escribir e identificar**
> los parámetros en el `.pgmx`, después ver **cómo se vuelcan al `.iso`**, y recién
> después usarlos — porque el uso de un parámetro es en los **mecanizados**, que son la
> rama D. El `Parametrics.Expression` de un parámetro usado NO se estudia todavía.

- ✅ **¿Un parámetro sin usar deja rastro en el ISO? NO. RESPONDIDA el 2026-08-17.**
  Fermín postprocesó en el CNC los cinco fixtures de parámetros; los cinco ISO son
  **idénticos al del programa vacío** salvo la línea 1, que lleva el nombre del archivo.
  43 líneas, mismo contenido. Con esto **A7 queda cerrado entero**.
  - Control cruzado independiente del diff: la diferencia de **bytes** de cada ISO contra
    el del vacío es **exactamente** el largo de más del nombre. Ni un byte sin explicar.
  - ⇒ **El converter puede ignorar los parámetros sin uso**: no emite nada por ellos.
  - ⚠️ Vale para parámetros **sin usar**. Cuando un parámetro alimente una cota o un
    mecanizado va a llegar al ISO **resuelto** — eso es rama D y no está derivado.
  - ⇒ Lo derivado sobre la ventana «Parámetro» no sirve para *emitir* ISO: sirve para que
    el **sintetizador** fabrique `.pgmx` válidos, que es de donde salen los fixtures.
- ✅ **¿Una dimensión definida por expresión llega resuelta o como expresión?** Contestado
  el 2026-08-17 por el costado de la geometría (`dibujos.md`, §7): el `.pgmx` guarda **las
  dos cosas, en dos lugares distintos** — el valor **ya resuelto** en el objeto, y la
  fórmula en un `Parametrics.Expression` aparte. ⇒ **El converter lee el número e ignora
  la fórmula; no necesita evaluar expresiones nunca.**
  - Y `Parametrics.Expression` resultó ser el mecanismo **general**, no algo de la pieza:
    `GeomTrimmedCurve#1927.EndY = 'dx1 - Distancia'` tiene la misma forma que
    `WorkPiece#1917.Length = 'dx1'`.
  - ⚠️ Un parámetro **usado** sí mueve la traza: cambiar `Distancia` de 50 a 130 recalculó
    la geometría entera. Lo de §8 vale sólo para los **sin usar**.
- ⚠️ **DEUDA ABIERTA: el redondeo a 6 decimales sigue en el resto del sintetizador.**
  `_compact_number` formatea con `f"{n:.6f}"`, y el fixture `Presicion` mostró que eso
  **no es lo que hace Maestro**: guardó `12.3456789` completo. Se corrigió **sólo el
  `Value` del parámetro** (`_parameter_value_text`), por decisión de alcance de Fermín
  del 2026-08-16: la evidencia sale de un parámetro y extenderla a los **153 usos** de
  `_compact_number` —geometría, fresados, taladros, herramientas— sería aplicar una
  hipótesis donde no se derivó.
  - Nadie derivó nunca el truncado a 6: es un valor predefinido de la época anterior,
    igual que `Integer` y `Speed`, sólo que éste **resultó estar mal**.
  - **El corpus no puede discriminarlo**: barridos los 55 `.pgmx` de autoría de Maestro
    que tenemos (baseline + manuales de la serie R), el **único** número con 7 o más
    decimales es el que se escribió a mano para este fixture. Punto ciego de la regla 5.
  - Contraindicación real de cambiarlo global: el redondeo **absorbe el ruido binario
    del float** (`0.1 + 0.2` → `0.3` en vez de `0.30000000000000004`).
  - Lo cierra un fixture de la **rama D**: un mecanizado con una coordenada de más de 6
    decimales dice si Maestro se comporta igual en geometría.
  - **Por qué el del parámetro SÍ se corrigió** pese al criterio «funcionalmente idéntico»
    de Fermín (2026-08-16): truncar `12.3456789` a `12.345679` **cambia el valor**. Si ese
    parámetro alimenta una cota, la pieza sale distinta. Es funcional, no cosmético — a
    diferencia del ULP de la dirección de una línea (ver `dibujos.md`, §5).
  - ⓘ La **geometría no está afectada**: usa `_format_maestro_number` con `.17g`, no
    `_compact_number`. Verificado con las líneas dibujadas.
- ⚠️ Defecto lateral encontrado de paso, independiente de todo lo anterior:
  `_compact_number(1e-07)` devuelve **`0`** — un valor chico desaparece en silencio.
- **Editar** un parámetro existente (segundo icono): ¿cambia el `ID`?
- ¿Nuestro default de unidad (`UnitLess`) debería alinearse con el del diálogo
  (`Longitud`)? Decisión de API pendiente; hoy la divergencia está fijada en
  `tests/test_pgmx_parametric_variables.py`.
- ¿El **nombre** admite espacios, acentos o mayúsculas iniciales? Los cuatro fixtures usan
  ASCII con guión bajo.
- ¿Se reutiliza un `ID` liberado al cerrar y reabrir Maestro?
