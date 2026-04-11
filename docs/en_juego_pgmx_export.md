# Exportacion PGMX En Juego

Este flujo exporta un layout En Juego a un `.pgmx` compuesto usando el script aislado `tools/export_pgmx.py`.

Estado actual:
- Validado en Maestro: abre, permite revisar y guarda sin error.
- Sigue siendo experimental y separado del flujo principal de la app.
- Los baselines manuales guardados desde Maestro ahora se concentran en `archive/maestro_baselines/` dentro del repo.

## Requisitos
- El modulo debe tener piezas marcadas como En Juego.
- Debe existir un `en_juego_layout` guardado desde la UI.
- El modulo debe tener `.pgmx` reales de origen para clonar geometria, operaciones y worksteps.
- El proyecto debe poder resolverse desde el JSON del proyecto y la carpeta del modulo.

## Comportamiento estable actual
- El tablero compuesto respeta `cut_saw_kerf` de `app_settings.json` al recomponer la separacion entre piezas.
- El setup de mecanizado se exporta con `_zP = 9`.
- Los escuadrados originales por pieza no se copian.
- Se crean dos mecanizados sinteticos:
  - `ESCUADRADO_EN_JUEGO`
  - `DIVISION_EN_JUEGO`
- Se preserva `Xn` dentro del `MainWorkplan`.
- Los taladros conservan `ToolpathList` en modo `raw`.
  - Esto significa que el exportador conserva esos toolpaths sin transformar su geometria serializada.
  - Esta decision es deliberada: fue la variante que Maestro abrio y guardo correctamente.
- Los perfiles sinteticos generan `Approach`, `TrajectoryPath` y `Lift` compatibles con Maestro.
  - `ESCUADRADO_EN_JUEGO` usa lineas rectas mas arcos de 1/4 de circunferencia en las esquinas.
  - `DIVISION_EN_JUEGO` usa una linea central con arcos de entrada y salida.
  - La compensacion lateral de `DIVISION_EN_JUEGO` depende del diametro de la herramienta.
  - Regla practica: el desplazamiento se calcula con el radio de herramienta (`diametro / 2`), no con un valor fijo.

## Ejecucion

```powershell
cd C:\Users\fermi\Proyectos\my-python-api
python -m tools.export_pgmx \
  --project-json "S:/Maestro/Projects/Prod 01-2026 - Cocina Vargas/Prod. 2026-04-01.json" \
  --module-path "S:/Maestro/Projects/Prod 01-2026 - Cocina Vargas/Mod.4 - BM-2P-PC-800"
```

Usando un baseline local del repo como plantilla real:

```powershell
cd C:\Users\fermi\Proyectos\my-python-api
python -m tools.export_pgmx \
  --project-json "S:/Maestro/Projects/Prod 01-2026 - Cocina Vargas/Prod. 2026-04-01.json" \
  --module-path "S:/Maestro/Projects/Prod 01-2026 - Cocina Vargas/Mod.4 - BM-2P-PC-800" \
  --template-pgmx "archive/maestro_baselines/baseline_sin_mecanizados.pgmx" \
  --output "archive/maestro_baselines/baseline_experimento_inicial.pgmx"
```

Salida por defecto:
- Se escribe un archivo `*_en_juego_compuesto.pgmx` dentro de la carpeta del modulo.
- Si se usa `--template-pgmx` sin `--output`, la salida se escribe junto a esa plantilla.

## Baselines manuales de Maestro
- Guardar los `.pgmx` base de referencia en `archive/maestro_baselines/`.
- Hacer los experimentos y snapshots dentro del repo para evitar seguir ensuciando la carpeta real del modulo.
- Tratar la carpeta del modulo solo como origen de piezas y datos reales, no como area de pruebas.

## Flags utiles
- `--output`: permite escribir a otra ruta.
- `--template-pgmx`: usa un `.pgmx` base del repo como plantilla XML/ZIP de salida.
- `--transform-drill-toolpaths`: solo para depuracion; reactiva la transformacion de toolpaths de taladro.
- `--synthetic-toolpaths empty`: deja vacios los toolpaths sinteticos para pruebas.
- `--strip-xn`: elimina `Xn` del `MainWorkplan` para pruebas.

## Notas para futuras modificaciones
- Antes de integrar este flujo al programa principal conviene seguir iterando aca.
- Si Maestro vuelve a cambiar toolpaths al guardar, usar el archivo guardado para diff estructurado contra una exportacion fresca.
- Evitar tocar simultaneamente toolpaths de taladro y toolpaths sinteticos; es mejor aislar cada cambio.