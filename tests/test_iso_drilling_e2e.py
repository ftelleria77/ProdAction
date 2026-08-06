"""Red e2e de la era DRILLING (F0.4 del plan de cierre): byte contra los pares de S:/P:.

Hasta 2026-08-05 la era de taladros (N001–N021) se validaba SOLO offline con ground-truth
horneado: una regresión del converter no se veía contra los ISO reales de Maestro. Esta red
recorre cada lote con `iso.synthesis.corpus.run_corpus` y exige `byte_identico` en TODO par
existente (los huérfanos conocidos sin .iso — `N011\\N_SD_through_front`,
`N019\\N_FG_left_ef` — cuentan como `sin_iso` y no fallan; están en la tanda B2 del plan).

Corrida fundacional 2026-08-05: 143/143 byte-idéntico.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from iso.synthesis.corpus import run_corpus

PGMX_ROOT = Path(r"S:\Maestro\Projects\ProdAction")
ISO_ROOT = Path(r"P:\USBMIX\ProdAction")

LOTES = (
    "N001_baselines", "N004_top_diameters", "N005_top_through", "N006_top_peck",
    "N007_top_conical", "N008_drill_patterns", "N009_top_feedspindle", "N010_tool_limits",
    "N011_side_features", "N012_side_faces_depth", "N013_top_depth_limit",
    "N014_side_security", "N015_xn_park", "N016_g53_transition", "N017_top_side_faces",
    "N018_work_origin", "N019_field_geometry", "N020_ef_origin", "N021_fields_ab_dc",
)


@unittest.skipUnless(PGMX_ROOT.exists() and ISO_ROOT.exists(), "S:/P: no montados")
class DrillingEraE2ETest(unittest.TestCase):
    def test_lotes_drilling_byte_identicos(self):
        for lote in LOTES:
            with self.subTest(lote=lote):
                report = run_corpus(PGMX_ROOT / lote, ISO_ROOT / lote)
                counts = report.counts()
                malos = [r for r in report.results
                         if r.verdict not in ("byte_identico", "sin_iso")]
                self.assertFalse(
                    malos,
                    f"{lote}: {counts} — primeros problemas: "
                    f"{[(r.pgmx.name, r.verdict, r.detail[:80]) for r in malos[:3]]}")
                self.assertGreater(counts.get("byte_identico", 0), 0,
                                   f"{lote}: no comparó ningún par (¿lote vacío?)")


if __name__ == "__main__":
    unittest.main()
