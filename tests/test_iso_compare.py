"""Tests directos de `iso.synthesis.compare` (hasta 2026-08-05 solo tenía cobertura vía e2e).

Cubre los tres veredictos, las omisiones deliberadas y el caso nuevo del ensayo general:
el comentario `% nombre.pgm` con case distinto entre versiones del emisor de Maestro
(dato de Fermín 2026-08-05: producción 2026-01 preserva, salidas 2026-05+ minusculizan
— ambos Maestro real ⇒ ruido del emisor, funcional y REPORTADO, como las milésimas).
"""

from __future__ import annotations

import unittest

from iso.synthesis.compare import classify_iso_diff

BASE = "% faja frontal.pgm\nG0 X10.000 Y20.000\nG1 Z-5.000 F1000.000\n"


class ClassifyIsoDiffTest(unittest.TestCase):
    def test_byte_identico(self):
        self.assertEqual(classify_iso_diff(BASE, BASE).verdict, "byte_identico")

    def test_milesimas_son_funcionales_y_reportadas(self):
        ref = BASE.replace("Y20.000", "Y20.001")
        comparison = classify_iso_diff(BASE, ref)
        self.assertEqual(comparison.verdict, "funcionalmente_identico")
        self.assertEqual(len(comparison.numeric_diffs), 1)
        self.assertAlmostEqual(comparison.max_delta, 0.001)

    def test_delta_grande_es_diferente(self):
        ref = BASE.replace("Y20.000", "Y21.000")
        self.assertEqual(classify_iso_diff(BASE, ref).verdict, "diferente")

    def test_esqueleto_distinto_es_diferente(self):
        ref = BASE.replace("G1 Z", "G0 Z")
        comparison = classify_iso_diff(BASE, ref)
        self.assertEqual(comparison.verdict, "diferente")
        self.assertTrue(comparison.structural_issues)

    def test_case_del_comentario_es_funcional_y_reportado(self):
        ref = BASE.replace("% faja frontal.pgm", "% Faja frontal.pgm")
        comparison = classify_iso_diff(BASE, ref)
        self.assertEqual(comparison.verdict, "funcionalmente_identico")
        self.assertEqual(len(comparison.comment_case_diffs), 1)
        self.assertIn("Faja frontal", comparison.comment_case_diffs[0])
        self.assertIn("case", comparison.report())

    def test_case_de_un_registro_NO_se_tolera(self):
        # `%DONTCARESPEEDV=1` vs `%dontcarespeedv=1` u otro registro: no es comentario
        # (sin espacio tras el %) — un case distinto ahí es estructural, nunca ruido.
        gen = BASE + "%ETK[114]\n"
        ref = BASE + "%etk[114]\n"
        self.assertEqual(classify_iso_diff(gen, ref).verdict, "diferente")

    def test_omision_deliberada_reportada(self):
        ref = BASE + "%DONTCARESPEEDV=1\n"
        comparison = classify_iso_diff(BASE, ref)
        self.assertEqual(comparison.verdict, "funcionalmente_identico")
        self.assertEqual(comparison.deliberate_omissions, ("%DONTCARESPEEDV=1",))

    def test_tolerancia_fisica_en_lineas_Or_micrones(self):
        # Las líneas %Or van en µm: un delta de 0.024 son 24 nm (ruido f32 del emisor,
        # ensayo 2026-08-05) → funcional. La MISMA magnitud en una coordenada (mm) → diferente.
        base = "% p.pgm\n%Or[0].ofX=-758100.000\nG0 X10.000\n"
        ref = base.replace("-758100.000", "-758099.976")
        self.assertEqual(classify_iso_diff(base, ref).verdict, "funcionalmente_identico")
        ref_coord = base.replace("X10.000", "X10.024")
        self.assertEqual(classify_iso_diff(base, ref_coord).verdict, "diferente")

    def test_case_mas_milesimas_sigue_funcional(self):
        ref = (BASE.replace("% faja frontal.pgm", "% Faja Frontal.pgm")
                   .replace("X10.000", "X10.001"))
        comparison = classify_iso_diff(BASE, ref)
        self.assertEqual(comparison.verdict, "funcionalmente_identico")
        self.assertEqual(len(comparison.comment_case_diffs), 1)
        self.assertEqual(len(comparison.numeric_diffs), 1)


if __name__ == "__main__":
    unittest.main()
