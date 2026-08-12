"""El snapshot de máquina y su manifest tienen que decir lo mismo.

El 2026-08-12 apareció que dos archivos del snapshot venían de la PC equivocada, y que
el manifest declaraba carpetas (`maestro_cfgx`) que en el árbol se llamaban de otro modo
(`maestro/Cfgx`). Nada lo detectaba: el snapshot se copiaba a mano.

Estos tests son la red. Corren 100% offline sobre lo que está versionado.
"""
import csv
import unittest
from pathlib import Path

from iso.machine_config import MANIFEST, SELECCION, SNAPSHOT, sha256


def _manifest() -> list[dict]:
    with MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _archivos_del_snapshot() -> list[Path]:
    return sorted(p for p in SNAPSHOT.rglob("*") if p.is_file() and p != MANIFEST)


class ManifestTests(unittest.TestCase):
    def test_el_manifest_describe_exactamente_los_archivos_presentes(self) -> None:
        declarados = {f"{f['snapshot_root']}/{f['relative_path']}".replace("\\", "/")
                      for f in _manifest()}
        presentes = {str(p.relative_to(SNAPSHOT)).replace("\\", "/")
                     for p in _archivos_del_snapshot()}
        self.assertEqual(declarados, presentes)

    def test_cada_hash_del_manifest_coincide_con_el_archivo(self) -> None:
        for fila in _manifest():
            ruta = SNAPSHOT / fila["snapshot_root"] / fila["relative_path"]
            with self.subTest(archivo=fila["relative_path"]):
                self.assertTrue(ruta.exists())
                self.assertEqual(sha256(ruta), fila["sha256"])
                self.assertEqual(str(ruta.stat().st_size), fila["bytes"])

    def test_toda_fuente_declarada_es_la_pc_del_cnc(self) -> None:
        """El requisito del 2026-08-04, ahora verificable."""
        for fila in _manifest():
            with self.subTest(archivo=fila["relative_path"]):
                self.assertIn("CNC", fila["source_root"])


class SeleccionTests(unittest.TestCase):
    def test_cada_archivo_del_snapshot_cae_bajo_una_carpeta_de_la_seleccion(self) -> None:
        carpetas = {destino for destino, _origen, _patron in SELECCION}
        for p in _archivos_del_snapshot():
            rel = str(p.parent.relative_to(SNAPSHOT)).replace("\\", "/")
            with self.subTest(archivo=p.name):
                self.assertIn(rel, carpetas)


if __name__ == "__main__":
    unittest.main()
