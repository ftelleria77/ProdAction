# Generacion ISO

Subsistema experimental para estudiar y construir la futura traduccion
`.pgmx -> .iso` de ProdAction.

No reemplaza a Maestro ni al postprocesador. Por ahora organiza la frontera de
trabajo: leer `.pgmx` existentes, adaptar lo que ya entiende el snapshot PGMX,
emitir solo reglas ISO ya validadas y comparar contra ISO Maestro.

## Estructura

| Ruta | Rol |
| --- | --- |
| `pgmx_source.py` | Lector/adaptador desde `tools.pgmx_snapshot` y `tools.pgmx_adapters`. |
| `emitter.py` | Emision ISO experimental para las familias ya validadas. |
| `modal.py` | Planificador inicial de estado modal para transiciones entre mecanizados. |
| `comparator.py` | Normalizacion y comparacion Maestro vs candidato. |
| `cli.py` | CLI de inspeccion, cabecera y comparacion. |
| `docs/contract.md` | Contrato del subsistema y MVP previsto. |
| `machine_config/` | Snapshot versionable y lectores de configuracion Maestro/Xilog. |
| `memory/current-state.md` | Estado vivo de este subsistema. |

## Comandos

Desde la raiz del repo:

```powershell
python -m iso_generation --help
python -m iso_generation inspect-pgmx ruta\pieza.pgmx
python -m iso_generation emit-header ruta\pieza.pgmx
python -m iso_generation emit ruta\pieza.pgmx --output candidato.iso
python -m iso_generation compare maestro.iso candidato.iso
```

## Frontera Actual

- Lee y adapta PGMX mediante APIs existentes.
- Advierte sobre herramientas sensibles `E002`, `E005` y `E006`.
- Mantiene un snapshot de configuracion de maquina en `machine_config/snapshot`,
  sincronizable desde `S:\Maestro\Cfgx`, `S:\Maestro\Tlgx` y `S:\Xilog Plus`.
- Lee desde `machine_config/snapshot` los largos, velocidades, avances y
  desplazamientos de herramientas `001..007`, laterales D8, `082` y `E004`;
  el emitter ya no conserva esas tablas dimensionales como literales propios.
- Lee desde `xilog_plus/Cfg/fields.cfg` el origen Y del marco `HG` observado:
  campo `H`, `Y0=-1515.600`, con `%Or[Y]` emitido en unidades del controlador
  tras redondeo `float32`.
- Lee el parking X de cierre desde el paso administrativo `Xn` del `.pgmx`;
  usa la configuracion de maquina solo como fallback si falta `Xn.X`.
- Emite cabecera ISO con la regla validada:
  `DX=length+origin_x`, `DY=width+origin_y`, `DZ=depth+origin_z`, area `-HG`.
- Emite los primeros bloques operativos MVP:
  - pieza sin operaciones;
  - taladros superiores (`Top DrillingSpec` y patrones `DrillingPatternSpec`)
    con herramientas verticales `001..007`;
  - taladros laterales D8 individuales y patrones en `Left`, `Right`, `Front`
    y `Back`.
  - ranura lineal horizontal `082` sobre `Top`, con correcciones `Left`/`Right`;
  - fresado lineal `E004` sobre `Top`, horizontal o vertical, incluyendo
    estrategia PH5 observada con pasadas multiples.
- Empieza a modelar transiciones por diferencial de estado modal, con la salida
  de ranura `082` hacia taladros `Top` y laterales como primer caso conectado.
- La validacion del emitter se apoya en planes por operacion y ya no en guardas
  por combinaciones completas de mecanizados.
- Validado por comparacion exacta contra Maestro para `ISO_MIN_001..006`,
  `ISO_MIN_010..013`, `ISO_MIN_020..023`, `Pieza`, `Pieza_001`,
  `Pieza_002`, `Pieza_003`, `Pieza_004`, `Pieza_004_Repeticiones` y
  `Pieza_005..015`.
- Validado puntualmente para parqueos laterales intermedios `G0 G53 Z...` en
  `side_g53_z_fixtures_2026-05-03` y en `Pieza_002/003/005`: el valor se
  calcula como `DZ_cabecera + 2*SecurityDistance + max(SHF_Z lateral
  involucrado)`.
- No se conecta con `cnc_traceability/` hasta tener un MVP confiable.

## Regla De Configuracion De Maquina

Los valores dimensionales propios de herramientas, cabezales, campos de trabajo,
posiciones de parqueo y parametros de operacion deben venir de la configuracion
Maestro/Xilog cuando esten disponibles. Las constantes observadas en ISO Maestro
son validas solo como bootstrap o prueba de contrato; antes de consolidar nuevas
familias, deben migrarse hacia lectores sobre `machine_config/snapshot`.

Los valores que todavia no tienen una ubicacion inequivoca en los archivos de
Maestro/Xilog quedan centralizados en `machine_config.loader` como politica ISO
observada, para que el emitter no vuelva a ser la fuente dimensional.

Para renovar el snapshot tras una calibracion:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\iso_generation\machine_config\sync_machine_config.ps1
```
