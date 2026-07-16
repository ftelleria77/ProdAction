"""Xn (Operación Nula): autoría opcional + su render en el footer del ISO.

El Xn desplaza el cabezal para que la cabina de seguridad libere la zona de trabajo y el operario
pueda acceder a la pieza (la misma función que el Park). En Maestro se agregan UNO, VARIOS o
NINGUNO, y **por defecto el archivo no trae ninguno**. Nuestro sintetizador escribe uno por
decisión de diseño; `include_xn=False` pide la forma nativa de Maestro.

En el ISO el Xn se RENDERIZA como `M5` + `G0 G53 X{park}` en el footer: sin Xn, ninguno de los dos
(derivado del lote N043 — los .pgmx hechos a mano en Maestro no traen Xn).

⚠️ Los 346 fixtures de N001–N042 tienen Xn porque los generó NUESTRO sintetizador, que siempre lo
escribía: el corpus entero es auto-generado y nunca pudo ver este caso. Estos tests son la red de
esa asimetría.
"""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from pgmx.synthesis import build_line_spec, build_synthesis_request, synthesize_request

from iso.synthesis import convert
from iso.synthesis._validation import UnsupportedOperationError


def _line(**kw):
    base = dict(start_x=20.0, start_y=100.0, end_x=280.0, end_y=100.0, feature_name="Fresado",
                tool_id="1903", tool_name="E004", tool_width=4.0, security_plane=20.0,
                is_through=False, target_depth=5.0)
    base.update(kw)
    return build_line_spec(**base)


def _synth(tmp: Path, name: str, *, include_xn: bool, **kw) -> Path:
    # OJO con el `name`: en Windows CON/PRN/AUX/NUL/COM1..9/LPT1..9 son nombres de DISPOSITIVO
    # reservados — un fixture llamado "con" cuelga el proceso al escribir `con.pgmx`.
    path = tmp / f"{name}.pgmx"
    synthesize_request(build_synthesis_request(
        output_path=path, piece_name=name, length=300.0, width=200.0, depth=18.0,
        origin_x=5.0, origin_y=5.0, origin_z=25.0, include_xn=include_xn, **kw))
    return path


def _has_xn(path: Path) -> bool:
    with zipfile.ZipFile(path) as z:
        xml = z.read([n for n in z.namelist() if n.endswith(".xml")][0]).decode("utf-8", "replace")
    return "Xn" in xml


class AuthoringTest(unittest.TestCase):
    def test_por_defecto_escribe_xn(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertTrue(_has_xn(_synth(Path(t), "xn_si", include_xn=True, lines=[_line()])))

    def test_include_xn_false_no_escribe_xn(self):
        # La forma NATIVA de Maestro: por defecto el archivo no trae Xn.
        with tempfile.TemporaryDirectory() as t:
            self.assertFalse(_has_xn(_synth(Path(t), "xn_no", include_xn=False, lines=[_line()])))


class FooterTest(unittest.TestCase):
    """El Xn se renderiza como `M5` + park X. Sin Xn, no se emiten."""

    def _footer(self, include_xn: bool) -> list[str]:
        with tempfile.TemporaryDirectory() as t:
            p = _synth(Path(t), "f", include_xn=include_xn, lines=[_line()])
            return [l.strip() for l in convert(p).replace("\r\n", "\n").split("\n")]

    def test_con_xn_emite_m5_y_park(self):
        ls = self._footer(True)
        self.assertIn("M5", ls)
        self.assertTrue(any(l.startswith("G0 G53 X") for l in ls))

    def test_sin_xn_no_emite_m5_ni_park(self):
        # N043: los 4 archivos manuales (todos router) no tienen Xn y su ISO no lleva ninguno.
        ls = self._footer(False)
        self.assertNotIn("M5", ls)
        self.assertFalse(any(l.startswith("G0 G53 X") for l in ls))

    def test_sin_xn_el_resto_del_footer_no_cambia(self):
        # Solo se caen esas dos líneas: todo lo demás del footer es idéntico.
        con, sin = self._footer(True), self._footer(False)
        self.assertEqual([l for l in con if l != "M5" and not l.startswith("G0 G53 X")], sin)


class GuardTest(unittest.TestCase):
    def test_sin_xn_con_taladro_se_rechaza(self):
        # N043 solo trae fixtures router-only sin Xn: para taladro/sierra no hay evidencia.
        from pgmx.synthesis import build_drill_spec
        with tempfile.TemporaryDirectory() as t:
            p = _synth(Path(t), "g", include_xn=False, lines=[_line()],
                       drills=[build_drill_spec(center_x=50.0, center_y=50.0, diameter=8.0,
                                                is_through=False, target_depth=10.0)])
            with self.assertRaises(UnsupportedOperationError):
                convert(p)


if __name__ == "__main__":
    unittest.main()
