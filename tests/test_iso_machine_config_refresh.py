"""Ciclo de refresco de config (F0.7): el catálogo derivado ya no se mantiene a mano.

Regla del requisito (Fermín 2026-08-04): sobreescribir los archivos extraídos de la PC
del CNC = converter actualizado, sin tocar código. La brecha era `tool_catalog.csv`
(derivado A MANO del def.tlgx). Estos tests fijan que la regeneración automática
reproduce el CSV curado y preserva el vocabulario de Fermín (type/description).
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from iso.machine_config import DEF_TLGX, TOOL_CATALOG, regenerate_tool_catalog, tool_rows_from_tlgx


class ToolCatalogRefreshTest(unittest.TestCase):
    def test_regeneracion_reproduce_el_csv_curado(self):
        # Regenerar a un tmp partiendo del CSV real: byte-idéntico al original.
        tmp = Path(tempfile.mkdtemp()) / "tool_catalog.csv"
        tmp.write_bytes(TOOL_CATALOG.read_bytes())
        regenerate_tool_catalog(DEF_TLGX, tmp)
        self.assertEqual(tmp.read_bytes(), TOOL_CATALOG.read_bytes())

    def test_numericos_salen_del_tlgx(self):
        rows = tool_rows_from_tlgx()
        self.assertEqual(len(rows), 19)
        self.assertEqual(rows["001"]["tool_offset_length"], "77")
        self.assertEqual(rows["082"]["name"], "082")
        self.assertIn("E004", rows)

    def test_herramienta_nueva_avisa_y_preserva_vocabulario(self):
        # Simulo un catálogo curado al que le falta una herramienta del tlgx: la
        # regeneración la agrega SIN type/description y avisa (vocabulario = de Fermín).
        tmp = Path(tempfile.mkdtemp()) / "tool_catalog.csv"
        originales = list(csv.DictReader(TOOL_CATALOG.open(encoding="utf-8-sig")))
        sin_082 = [r for r in originales if r["name"] != "082"]
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=originales[0].keys())
            writer.writeheader()
            writer.writerows(sin_082)
        avisos = regenerate_tool_catalog(DEF_TLGX, tmp)
        self.assertTrue(any("NUEVA '082'" in a for a in avisos))
        regenerado = {r["name"]: r for r in csv.DictReader(tmp.open(encoding="utf-8-sig"))}
        self.assertEqual(regenerado["082"]["type"], "")          # vocabulario NO inventado
        self.assertEqual(regenerado["001"]["type"], "Broca")     # curado preservado
        self.assertEqual(regenerado["082"]["diameter"], "120")   # numérico del tlgx


if __name__ == "__main__":
    unittest.main()
