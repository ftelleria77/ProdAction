# Trazabilidad CNC

Este subsistema es una herramienta auxiliar para seguir la ejecucion real de un
proyecto en la PC del CNC.

No reemplaza a la aplicacion principal de ProdAction. La aplicacion principal
sigue generando proyectos, planillas, estructuras de salida y archivos de
produccion; esta herramienta consume esa salida, ayuda al operador a preparar
un `.iso` por vez en `USBMIX` y registra el avance operativo.

## Estructura

| Ruta | Rol |
| --- | --- |
| `viewer_xp.py` | Aplicacion Tkinter/stdlib compatible con runtime Windows XP 32 bits. |
| `config/cnc_project_viewer_settings.json` | Configuracion local inicial del subsistema. |
| `docs/contract.md` | Contrato estable de responsabilidades, datos y seguridad. |
| `memory/current-state.md` | Memoria historica y estado de trabajo del subsistema. |

## Ejecutar En Desarrollo

Desde la raiz del repo:

```powershell
py -3 cnc_traceability\viewer_xp.py
```

Validacion rapida:

```powershell
py -3 -m py_compile cnc_traceability\viewer_xp.py
```

## Compatibilidad

El codigo evita PySide6, `pathlib`, `dataclasses`, f-strings y dependencias
modernas. La restriccion de diseno sigue siendo producir un ejecutable portable
para Windows XP 32 bits, a validar en la PC real del CNC.

## Datos Persistidos

- La configuracion del operador vive en
  `cnc_traceability/config/cnc_project_viewer_settings.json` durante el
  desarrollo.
- En ejecucion portable, el mismo archivo debe vivir junto al ejecutable dentro
  de una carpeta `config/`.
- El avance de mecanizado se guarda como `cnc_progress.json` dentro de la
  estructura CNC del proyecto, para que el estado viaje con la salida de
  produccion.
