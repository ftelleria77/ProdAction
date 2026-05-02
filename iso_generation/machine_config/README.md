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
