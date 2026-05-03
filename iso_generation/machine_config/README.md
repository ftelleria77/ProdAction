# Machine Configuration Snapshot

This directory is the local calibration/configuration source for ISO generation.

The ISO emitter must not treat tool offsets, spindle data, work-field
coordinates, parking positions, or operation geometry constants as permanent
code literals when those values are available in Maestro/Xilog configuration.
Those values belong to the machine configuration snapshot and can change after a
machine calibration.

## Sources

The initial snapshot is copied from:

- `S:\Maestro\Cfgx`
- `S:\Maestro\Tlgx`
- `S:\Xilog Plus`

The Xilog Plus installation includes runtime/media/program files. The snapshot
copies only configuration-like files by extension: `.cfg`, `.ini`, `.str`,
`.tab`, `.tlg` and `.txt`. Communication/password files that are not needed for
dimensional ISO generation are excluded.

## Layout

| Path | Source |
| --- | --- |
| `snapshot/maestro/Cfgx` | `S:\Maestro\Cfgx` |
| `snapshot/maestro/Tlgx` | `S:\Maestro\Tlgx` |
| `snapshot/xilog_plus` | selected config files from `S:\Xilog Plus` |
| `snapshot/manifest.csv` | generated file inventory with hashes |

## Updating After Calibration

After a machine calibration, replace the snapshot by running:

```powershell
.\iso_generation\machine_config\sync_machine_config.ps1
```

Later ISO generator work should read dimensional machine/tool values through a
loader over this snapshot instead of adding new hardcoded constants to
`emitter.py`.

## Loader

`loader.py` exposes the ISO-facing configuration used by the emitter:

- Maestro `Tlgx/def.tlgx` supplies tool lengths, spindle speeds, feed/descent
  rates and aggregate translations for drilling tools, lateral D8 tools and
  slot tool `082`.
- Maestro `Cfgx/Programaciones.settingsx` supplies `SecurityDistance`; lateral
  aggregate G53 clearances use both safety offsets, so the observed `40.000`
  comes from `2 * 20`.
- Xilog `Cfg/pheads.cfg` supplies the observed head offsets for line milling
  tool `E004`.
- Xilog `Cfg/fields.cfg` supplies the observed `HG` frame Y reference from
  field `H`.
- Xilog `Cfg/Params.cfg` supplies safe-Z and fallback axis parking limits.
  Program parking X is read from the source PGMX `Xn` step when available.

Some ISO control masks are not yet mapped to a unique source file. Those
observed values are kept in the loader as ISO policy until the source mapping
is identified, so `emitter.py` remains free of dimensional machine tables.
