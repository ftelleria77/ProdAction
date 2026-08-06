"""Guarda de operaciones de máquina sin render: Xmsg / Park / Iso → fail-loud.

El adapter deja los pasos sin manufacturing feature como `ignored` (ni adapted ni
unsupported), así que ANTES de esta guarda un `.pgmx` con Xmsg («Girar pieza»), Park
(Aparcamiento) o una instrucción Iso convertía PERDIENDO esas operaciones — un ISO
incompleto que ejecuta de largo donde el programa real para. Detectado en la auditoría
del plan de cierre (2026-08-04): era la única violación de la regla 4 del proyecto.

El Xn NO cae en esta guarda: tiene render propio (`_xn_park`). Los CUATRO son
Executables distintos — ver labs `aparcamiento` y `machine_operations`.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pgmx.synthesis import (
    build_line_spec, build_park_spec, build_synthesis_request, build_workplan_spec,
    build_xmsg_spec, build_xn_spec, synthesize_request,
)
from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError

MACHINE_OPS_DIR = Path(
    r"S:\Maestro\Projects\ProdAction\Investigación previa\PGMX\machine_operations\manual")


def _synthesize(machine_operations) -> Path:
    tmp = Path(tempfile.mkdtemp())
    path = tmp / "machine_ops.pgmx"
    req = build_synthesis_request(
        output_path=path, piece_name="machine_ops",
        length=300.0, width=200.0, depth=18.0, origin_x=5.0, origin_y=5.0, origin_z=25.0,
        workplans=[build_workplan_spec(
            name="Fase",
            machinings=[build_line_spec(
                20.0, 100.0, 280.0, 100.0, None, None, None, None, None,
                target_depth=5.0, is_through=False)],
            machine_operations=machine_operations,
        )],
    )
    synthesize_request(req)
    return path


class MachineOpsGuardTest(unittest.TestCase):
    def test_xmsg_rebota_fail_loud(self):
        path = _synthesize([build_xmsg_spec(text="Girar pieza", stop="NoUnlock")])
        with self.assertRaises(UnsupportedOperationError) as caught:
            convert(path)
        self.assertIn("Xmsg", str(caught.exception))
        self.assertIn("Eje C", str(caught.exception))

    def test_park_rebota_fail_loud(self):
        path = _synthesize([build_park_spec()])
        with self.assertRaises(UnsupportedOperationError) as caught:
            convert(path)
        self.assertIn("Park", str(caught.exception))

    def test_xn_solo_sigue_convirtiendo(self):
        # El Xn tiene render (footer M5 + park): la guarda nueva NO lo toca.
        path = _synthesize([build_xn_spec(x=-2000.0)])
        iso = convert(path)
        self.assertIn("G0 G53 X-2000.000", iso)

    @unittest.skipUnless(MACHINE_OPS_DIR.exists(), "S: no montada")
    def test_flujo_real_dos_caras_rebota(self):
        # El caso real del Eje C (cara A → Xn + Xmsg girar → cara B → Xn): hoy DEBE rebotar,
        # nombrando el Xmsg — no convertir en silencio sin el mensaje ni el paro.
        path = MACHINE_OPS_DIR / "MachineOps_001_FI_XN_MSG_NP_FF_XN.pgmx"
        with self.assertRaises(UnsupportedOperationError) as caught:
            convert(path)
        self.assertIn("Xmsg", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
