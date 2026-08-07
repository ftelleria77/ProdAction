"""Campo de trabajo (ExecutionFields del .pgmx) → origen del campo y fail-loud.

El campo elegido en Maestro queda en el .pgmx como <ExecutionFields>HG</ExecutionFields>. Determina
el origen (field_origin, de fields.cfg) y el espejado de direcciones del 2×2. Hoy solo HG está
calibrado y con direcciones validadas → el resto es fail-loud.
"""

from __future__ import annotations

import io
import unittest
import zipfile
from pathlib import Path

from iso.synthesis import _reader
from iso.synthesis._machine import SIDE_SUPPORTED_FIELDS, SUPPORTED_FIELDS
from iso.synthesis._machine_config import field_origin
from iso.synthesis._reader import _execution_field, read_pgmx
from iso.synthesis._validation import UnsupportedOperationError

_FIXTURE = Path(r"S:\Maestro\Projects\ProdAction\Investigacion iso_converter\N001_baselines\N_A001_top_1hole_D5.pgmx")
_SIDE_FIXTURE = Path(r"S:\Maestro\Projects\ProdAction\Investigacion iso_converter\N001_baselines\N_B001_left_1hole.pgmx")


class FieldOriginTest(unittest.TestCase):
    def test_four_main_fields_origins(self):
        # Orígenes de los 4 campos principales (de fields.cfg, según Fermín).
        self.assertEqual(field_origin("AB"), (-3685.85, 0.0))
        self.assertEqual(field_origin("DC"), (0.0, 0.0))
        self.assertEqual(field_origin("EF"), (-3688.00, -1515.25))
        self.assertEqual(field_origin("HG"), (0.0, -1515.60))

    def test_origin_taken_from_first_field_of_the_pair(self):
        # El área toma el origen del PRIMER campo del par (HG→H, EF→E).
        self.assertEqual(field_origin("HG"), field_origin("H"))
        self.assertEqual(field_origin("EF"), field_origin("E"))


class ExecutionFieldTest(unittest.TestCase):
    def _pgmx_with_field(self, value: str) -> Path:
        import tempfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("piece.xml", f"<root><x:ExecutionFields>{value}</x:ExecutionFields></root>")
        tmp = Path(tempfile.mkdtemp()) / "fake.pgmx"
        tmp.write_bytes(buf.getvalue())
        return tmp

    def test_reads_field_from_real_fixture(self):
        if not _FIXTURE.exists():
            self.skipTest("fixture no disponible")
        self.assertEqual(_execution_field(_FIXTURE), "HG")

    def test_reads_arbitrary_field_from_zip(self):
        self.assertEqual(_execution_field(self._pgmx_with_field("EF")), "EF")

    def test_default_hg_when_absent(self):
        import tempfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("piece.xml", "<root><Other>1</Other></root>")
        tmp = Path(tempfile.mkdtemp()) / "fake.pgmx"
        tmp.write_bytes(buf.getvalue())
        self.assertEqual(_execution_field(tmp), "HG")


class FieldSupportTest(unittest.TestCase):
    def test_supported_fields(self):
        # Los 4 campos de la grilla 2×2, para top/router Y caras laterales (side_shf derivado).
        self.assertEqual(SUPPORTED_FIELDS, ("HG", "EF", "DC", "AB"))
        self.assertEqual(SIDE_SUPPORTED_FIELDS, ("HG", "EF", "DC", "AB"))

    def _with_field(self, value: str):
        orig = _reader._execution_field
        _reader._execution_field = lambda _p: value
        return orig

    def test_unknown_field_raises(self):
        if not _FIXTURE.exists():
            self.skipTest("fixture no disponible")
        orig = self._with_field("XY")  # fuera de la grilla
        try:
            with self.assertRaises(UnsupportedOperationError):
                read_pgmx(_FIXTURE)
        finally:
            _reader._execution_field = orig

    def test_non_hg_top_is_allowed(self):
        # El fixture es un taladro TOP → un campo no-HG (EF) YA está soportado (no fail-loud).
        if not _FIXTURE.exists():
            self.skipTest("fixture no disponible")
        orig = self._with_field("EF")
        try:
            ctx, _ = read_pgmx(_FIXTURE)
            self.assertEqual(ctx.field, "EF")
        finally:
            _reader._execution_field = orig

    def test_non_hg_side_is_allowed(self):
        # Taladro lateral en campo no-HG (EF) YA está soportado (side_shf por-cara derivado).
        if not _SIDE_FIXTURE.exists():
            self.skipTest("fixture lateral no disponible")
        orig = self._with_field("EF")
        try:
            ctx, _ = read_pgmx(_SIDE_FIXTURE)
            self.assertEqual(ctx.field, "EF")
        finally:
            _reader._execution_field = orig


if __name__ == "__main__":
    unittest.main()
