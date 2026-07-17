# Xn (Operación Nula) y Xmsg — modelo del dominio y estado

## Qué es y para qué sirve (Fermín, 2026-07-17)

El **Xn (Operación Nula)**, igual que la función **Park (Aparcamiento)**, desplaza el cabezal
para **retirar la cabina de seguridad de la zona de trabajo**, permitiendo al operario **acceder
a la pieza**.

En Maestro se agregan **uno, varios o ninguno**, y **por defecto el archivo no trae ninguno**.

## El flujo real: varios Xn + Xmsg en un mismo programa

> "Luego de ejecutar un escuadrado y otros mecanizados, se ejecuta un XN y un XMSG, que permite
> hacer una pausa para que el operario pueda girar la pieza. Al reanudar la ejecución el programa
> efectúa mecanizados en la otra cara y un segundo XN para retirar la pieza terminada. Luego
> poner la siguiente pieza y volver a ejecutar el mismo programa. Esto permite repetición con muy
> poca intervención del operario sobre el programa." — Fermín

```
  [escuadrado + mecanizados cara A]
  Xn      → retira la cabina: el operario puede meter las manos
  Xmsg    → pausa + mensaje: "girá la pieza"
  [mecanizados cara B]
  Xn      → retira la cabina: el operario saca la pieza terminada
  (poner la siguiente pieza y volver a ejecutar el MISMO programa)
```

El objetivo es **repetición con mínima intervención sobre el programa**: el operario ejecuta
siempre el mismo archivo y solo responde a las pausas.

## ⚠️ Nuestro modelo actual está mal de raíz (y hay guarda)

Hoy el converter trata el Xn como una **propiedad de la pieza que se emite en el footer**:
`PieceCtx.park_x` / `park_y`, renderizados por `render_epilogue` como `M5` + `G0 G53 X{park}`.

Eso es **estructuralmente incorrecto**. El Xn es una **OPERACIÓN POSICIONAL**: ocurre en un punto
del programa y se renderiza *ahí*. El que va al final PARECE un "park de footer", pero es
simplemente el último Xn.

**Por qué no lo vimos**: los 346 fixtures de N001–N042 tienen exactamente UN Xn, al final, porque
los escribía nuestro sintetizador siempre igual. Con esa muestra, "propiedad de la pieza
renderizada en el footer" y "última operación del programa" son **indistinguibles**. Es el mismo
punto ciego que el del footer sin Xn: el corpus auto-generado no puede contradecir a su autor.

**Guardas activas** (`iso/synthesis/_reader.py`), en vez de aproximar en silencio:
- **Más de un Xn** → se rechaza: sin evidencia de dónde se emiten los intermedios.
- **Sin Xn + taladro/sierra** → se rechaza: los 5 archivos sin Xn de N043 son todos router-only.

## Lo derivado hasta hoy

| caso | evidencia | modelo |
|---|---|---|
| **Un Xn** (al final) | N015 + los 346 | footer: `M5` + `G0 G53 X{Xn.x}` (+ ` Y{-Xn.y}` si tiene Y); `park_y = -Xn.y` porque la cama va 0..−1500 en pgmx → 0..+1500 en máquina |
| **Sin Xn** | N043 (5 archivos hechos a mano, router-only) | el footer NO lleva `M5` ni park X — nadie pidió retirar la cabina |
| **Varios Xn** | ninguna | ⛔ guarda |
| **Xmsg** | ninguna en el converter | ⛔ no modelado (`XmsgSpec` existe en la autoría, con `stop`) |

`X_PARK = -3700.0` fue **borrado**: existía para inventar un park cuando no había Xn — el caso
que N043 falsificó. El park sale SIEMPRE del Xn.

## Autoría

```python
build_synthesis_request(...)                  # el Xn por defecto (nuestra decisión de diseño)
build_synthesis_request(..., xn=None)         # NINGUNO — la forma nativa de Maestro
build_synthesis_request(..., xn=XnSpec(...))  # ESE Xn
```

⚠️ Seguimos al revés que Maestro (nuestro default escribe uno; el suyo, ninguno). Es deliberado:
darlo vuelta cambiaría los 40 generadores y **los 346 fixtures dejarían de reproducirse tal como
fueron postprocesados**. Pendiente de decisión.

La autoría todavía escribe **un solo** Xn, siempre al final: no hay forma de pedir varios ni de
ubicarlos. Es lo que hay que extender para el flujo de arriba (Eje C).

## Pendiente (Eje C)

1. **Modelar el Xn como operación posicional**, no como propiedad de la pieza: sacar `park_x/park_y`
   de `PieceCtx` y emitir cada Xn en su lugar del programa.
2. **Autoría de varios Xn** + su posición entre mecanizados.
3. **Xmsg**: pausa + mensaje al operario, con su modo de parada (`stop`).
4. **Lote de derivación** del flujo cara A → Xn+Xmsg → cara B → Xn. Lo tiene que hacer **Fermín en
   Maestro**: hoy no podemos autorar varios Xn, y además el punto es ver **dónde** los emite el
   postprocesador — que es justamente la incógnita.
5. Relacionado: mecanizado de la otra cara ⇒ toca **multi-pieza / caras / fases** y el
   workstream pendular EF/HG.
