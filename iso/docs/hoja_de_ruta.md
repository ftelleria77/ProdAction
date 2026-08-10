# Hoja de ruta de la reinvestigación PGMX → ISO

**Documento VIVO.** Registra el trayecto recorrido (bitácora, abajo) y establece el camino
por delante en la medida en que los hallazgos lo van definiendo. Se actualiza en cada hito:
lo recorrido se AGREGA a la bitácora (nunca se reescribe), el mapa se REVISA (los cambios de
rumbo se anotan como decisiones con fecha). La vista visual se republica en cada hito
(artifact "Reinvestigación PGMX→ISO", URL estable).

Estados: ✅ hecho · 🔄 en curso · ⏸ esperando a Fermín · ⬜ pendiente · 🔮 futuro (sin fecha)

## Estado actual (2026-08-07)

La limpieza terminó: rama `reinvestigacion` desde `main`, época anterior congelada fuera del
árbol (ramas `iso_converter` y `respaldo/ejecucion-plan-f0-f3`), suite 282 passed 100%
offline. El lote R001 (programa sin mecanizados, 7 fixtures) está generado en S: esperando
postproceso, y el repaso de configuración espera las capturas de la UI. La anatomía del ISO
arranca con el primer ISO vacío.

## El mapa: troncos y ramificaciones

El orden DENTRO de cada tronco y el orden entre troncos es dinámico: lo deciden los
hallazgos. Lo único fijo es el método (regla de la época): fixtures propios de variación
controlada (serie R), byte-idéntico o fail-loud, nomenclatura genérica de Maestro.

### A. Configuración de programa — 🔄 en curso (etapa 1)
- A1. Programa vacío, lote R001 (7 variaciones: base, dims, origen XY, origen Z, campo EF,
  Xn, variable) — ✅ generado · ⏸ postproceso
- A2. Repaso opción por opción contra la UI de Maestro (capturas) — ⏸ capturas
- A3. Opciones que el synth no varía (offset de pieza, repeticiones, ciclo continuo, espejo
  tecnológico, opciones de mesa/mecánica) → gemelos manuales, una opción por archivo — ⬜
- A4. Fases (workplans) y orígenes múltiples — 🔮

### B. Anatomía del ISO — ⬜ (transversal, arranca con el primer ISO de R001)
- B1. Partes del archivo del programa vacío: atribuir CADA línea a **uno de TRES** orígenes —
  configuración de programa (`.pgmx`), configuración de máquina (snapshot del CNC) o
  **configuración global de la aplicación (ventana Opciones)**. El tercero apareció el
  2026-08-09 y no estaba previsto — ⬜
- B2. Con cada operación nueva: qué líneas agrega, origen de cada parámetro y valor — 🔮
- B3. Ruido del emisor (milésimas, case, f32): re-derivar con evidencia R propia — 🔮

### C. Operaciones de máquina — 🔮 (Xn · Xmsg · Park · Iso)
- El lab de la época anterior queda congelado; la instancia nueva se crea oportunamente.

### D. Mecanizados — 🔮 (una operación por vez, cada parámetro variado de forma controlada)
- Perforado (vertical, lateral, patrones) — 🔮
- Fresados (línea, arco, círculo, polilínea, contorno) — 🔮
- Canal (sierra) — 🔮
- Vaciado — 🔮 (el lab pgmx congelado se recrea oportunamente)
- El ORDEN de estas ramas se define por hallazgos, no está prefijado.

### E. Configuración de máquina — 🔮
- Ciclo de refresco del snapshot (requisito 2026-08-04: siempre de los archivos extraídos de
  la PC del CNC, refresco = sobreescribir carpeta) — formalizar como spec — 🔮
- E1. **Ampliar el alcance del snapshot** (2026-08-09): hoy son 3 archivos; una instalación
  real tiene 83 sólo en `<Xilog Plus>\Cfg\`, más todo el lado Maestro
  (`UI00.exe.Config` = la ventana Opciones, `Settings\`, `Cfgx\`, `Tlgx\`). Lista de
  extracción en `experiments/programa_vacio.md` — ⏸ esperando la extracción de la PC del CNC

### Cierre — 🔮
1. Repaso del plan (`plan_cierre_converter.md`, untracked) con las specs de la reinvestigación
2. Construcción del converter definitivo
3. Corrección de la app (re-habilitar exportación ISO)
4. App de conversión por lotes (proyectos con carpetas y múltiples piezas)

## Preguntas abiertas

- ¿Maestro postprocesa un programa sin operaciones, o lo rechaza? (R001 lo responde)
- ¿El origen de la pieza aparece en el ISO vacío? ¿Dónde?
- ¿Una variable de usuario sin uso deja rastro en el ISO?
- ¿Qué opciones de programa muestra la UI que el XML de la plantilla no expone (o al revés)?

## Bitácora del trayecto

### 2026-08-06 — El rumbo nuevo
- Tras ejecutar parte del plan de cierre de la época anterior, Fermín lo revisa y decide
  VOLVER ATRÁS ("no me gustó como quedó"): re-especificar antes de reconstruir. La ejecución
  completa queda preservada en `respaldo/ejecucion-plan-f0-f3`.
- Directiva de la reinvestigación metódica: empezar desde un `.pgmx` VACÍO, repasar toda la
  configuración (con capturas de la UI si hace falta), programas crecientes variando cada
  parámetro de forma controlada, anatomía del ISO en paralelo, y regla de nomenclatura
  genérica (términos de Maestro; nunca proyectos de producción ni fixtures).

### 2026-08-07 — Limpieza del repositorio y preparación
- Serie N archivada por Fermín en `Investigacion iso_converter\` de AMBAS raíces (S: y P:);
  repo reapuntado (80 archivos) y `iso_converter` congelada verde (683 passed, tip 260f340).
- Rama **`reinvestigacion`** creada desde `main`. Congelados fuera del árbol: converter
  viejo (`iso/synthesis`), sus 20 tests, labs N001–N042, estudios ISO, docs de la época,
  `iso_state_synthesis` completo (la app queda con exportación ISO deshabilitada CON AVISO
  por pieza), `test_pgmx_pocket`, y los labs pgmx (`aparcamiento`, `machine_operations`,
  `pocket_milling`).
- Auditoría de la suite pedida por Fermín: 28 de los 33 subtests leían fixtures viejos
  (`Vaciado_NNN` de `Investigación previa`) tras un `skipUnless` silencioso → retirados.
  Resultado: **282 passed, 5 subtests, 100% offline**.
- Lote **R001** generado (7 `.pgmx` de variación controlada + INSTRUCCIONES con gemelo
  manual) y doc del experimento `programa_vacio.md` con el inventario completo de la
  configuración de programa del `.pgmx`.
- CLAUDE.md regla 2 actualizada a la época nueva (aprobado por Fermín).
- Esta hoja de ruta creada.

### 2026-08-09 — Arrancan las capturas de la UI (A2) y aparece un tercer origen
- Definido dónde viven las capturas: **repo Nora**, partidas por la regla del propio repo
  («datos por máquina = memoria; oficio = skills»). La VENTANA va a
  `skills/cnc-scm-maestro/references/pantallas/`; los VALORES de la Pratix, a
  `memory/machines/pratix-s15/pantallas/`. Se llaman **pantallas**, no fotos ni capturas
  («captura» ya significa snapshot de config en `iso/data/`). Hasta hoy no se había guardado
  ni una imagen: las 7 de Vaciado del 29-jul se perdieron, sobrevive sólo su prosa.
- 20 capturas: el Editor en frío + la ventana **Opciones** completa, nodo por nodo.
  Transcripción en `cnc-scm-maestro/references/opciones-de-maestro.md`.
- **Hallazgo que cambia B1**: la dicotomía programa/máquina no alcanza. La ventana Opciones
  es un TERCER origen — global de la aplicación, fuera del `.pgmx` — y de ahí salen el
  formato de salida (ISO vs PGM), el tope de referencia, la notación de Z negativa, el
  «Paso de retroacción en los fresados» (10) y el estacionamiento automático al terminar.
  Detalle y consecuencias en `experiments/programa_vacio.md`.
- Respondida una fila del inventario: `IsMM` = Opciones → Idioma → «Unidad de medida».
- Abierto: si la instalación capturada es la que postprocesa de verdad (sus rutas son las de
  fábrica, no `S:`), o si es una copia de escritorio.
