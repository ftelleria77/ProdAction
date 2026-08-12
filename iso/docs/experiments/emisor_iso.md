# El emisor: quién escribe materialmente el ISO

**Documento vivo.** Nació el 2026-08-12 de una pregunta que quedó abierta en
`anatomia_iso.md`: hay líneas del esqueleto que no salen del programa, ni de la
configuración de máquina, ni de la ventana Opciones — **las escribe el binario que genera
el ISO**. La pregunta era si eso constituye un cuarto origen. La copia completa de la PC
del CNC la respondió el mismo día.

## Quién genera el ISO

No lo genera Maestro por su cuenta: usa el **generador de Xilog Plus**, y la clave que lo
habilita está en el `NCI.CFG` de la máquina, en la primera línea del archivo:

```
$GEN_ISO_FOR_EXTERNAL_APP
1
```

Los módulos que aportan las líneas del esqueleto (`anatomia_iso.md`, B1g) son:

| Binario | Qué aporta |
|---|---|
| `PostISO.dll` | el bloque de puesta a punto, `SYN`, los `?%EDK[…]`, la tabla de códigos G y M |
| `PlPathFilter32.dll` | el teardown (`MLV`/`SHF`/`VL6`/`VL7`), dentro de su bloque de **mesa** |
| `VtGenIso.dll` | plantillas de `MLV`/`SHF` y el bloque del láser de cruce |
| `nci32.dll` | códigos G y las plantillas del header |

## ⭐ Las dos PCs NO tienen el mismo emisor (2026-08-12)

Comparación por sha256 entre la copia completa del CNC (`S:\Copia CNC`) y la instalación de
oficina técnica. **Los seis binarios difieren.**

| Binario | CNC | Oficina técnica |
|---|---|---|
| `PostISO.dll` | 262.144 B · **2011-11-18** | 262.144 B · 2011-10-14 |
| `PlPathFilter32.dll` | 184.320 B · **2011-11-18** | 184.320 B · 2011-10-14 |
| `VtGenIso.dll` | 262.144 B · **2011-11-18** | 262.144 B · 2011-10-14 |
| `nci32.dll` | **319.488 B** · **2011-11-18** | **315.392 B** · 2011-10-14 |
| `Nci.dll` · `ChkPgm32.dll` | difieren | difieren |

**El CNC tiene la build más nueva**, de un mes después. Y la diferencia no es cosmética:
`nci32.dll` además **pesa 4 KB más** y su tabla de cadenas cambió. Las plantillas del
header en formato PGM (`(H DX%.*f`, ` BX%.*f`, ` BY%.*f`, …) están **sólo en la versión de
oficina técnica**; la del CNC no las tiene.

> ⚠️ **Ninguno de estos DLL tiene número de versión** (`FileVersion` vacío: son de 2011).
> Su identidad sólo puede ser **fecha + tamaño + hash**, como el `manifest.csv`.

### Qué se sigue de esto

1. **El emisor es un origen.** No es «el binario hace siempre lo mismo»: hay dos emisores
   distintos conviviendo en el taller, y difieren justamente en plantillas de emisión.
2. **Toda evidencia queda fechada contra un emisor.** Un ISO de referencia prueba lo que
   emite *esa* build. Los ISO de la serie R salieron todos del CNC, así que son
   consistentes entre sí — pero no son transferibles a la otra PC sin verificar.
3. **Sube el valor del paso 0** (postprocesar el programa base en oficina técnica). Ya no
   es confirmar lo esperado: ahora hay un motivo concreto para que pueda dar distinto, y
   el resultado importa igual en los dos sentidos.

### Lo que este hallazgo NO dice

Que los binarios difieran **no prueba** que el ISO difiera. Las diferencias podrían estar
en rutas de código que este esqueleto no ejercita, y la evidencia disponible apunta a que
buena parte del preámbulo y del cierre viene de `NCI.CFG` —que **sí es idéntico en las dos
PCs**, igual que `Nci.ini`—. El paso 0 es exactamente el experimento que lo separa.

## El matiz que ordena todo esto: config vacía, no constante

De B1h: los binarios consultan **30 claves `$…`** que ningún archivo de la instalación
define (`$MA_*` de mesa, `$PM_*` de macros de archivo/bloque/ciclo, y `$KEY_G%d`/`$KEY_M%d`
para la traducción de cada código G y M).

⇒ Casi todo lo que parecía «constante del binario» es en realidad **el valor por defecto de
una clave de configuración que nadie escribió**. El mecanismo es el mismo de `NCI.CFG`, no
uno nuevo: el emisor lee configuración, y cuando no la encuentra tiene un default.

El emisor incluso trae su propio fail-loud: si no encuentra la clave de un código G escribe
`;G%d: CORRISPONDENZA NON TROVATA!` **dentro del ISO**.

## Decisión pendiente

**¿El snapshot incluye al emisor?** Hoy el snapshot guarda configuración (93 archivos) y no
guarda los binarios que la consumen. Con dos emisores distintos en el taller, la opción
conservadora es registrar al menos **su identidad** (nombre, tamaño, fecha y sha256) junto
al resto del manifest, sin necesariamente versionar 1 MB de DLL.

Es decisión de Fermín. Lo que cambia: con el emisor registrado, el converter puede declarar
contra qué build se derivó cada regla y **fallar ruidosamente** si el ISO de referencia
salió de otra. Sin registrarlo, esa diferencia es invisible.

## Herramienta

```
py -m iso.machining_lab.buscar_en_binarios barrer "VL[67]=" "SHF\[Z\]"
py -m iso.machining_lab.buscar_en_binarios contexto <binario> "^SYN$"
```
