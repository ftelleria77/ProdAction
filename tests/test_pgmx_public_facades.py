import unittest

from pgmx import adapters, snapshot, synthesis, vaciado, vaciado_lab
from pgmx.synthesis import cli as synthesis_cli
from pgmx.synthesis import core as synthesis_core
from pgmx.synthesis import vaciado as synthesis_vaciado
from pgmx.synthesis.milling import pocket_trace as milling_pocket_trace
from tools import pgmx_adapters, pgmx_snapshot, pgmx_synthesis, synthesize_pgmx
from tools.pgmx_synthesis import core as legacy_synthesis_core
from tools.pgmx_synthesis import vaciado as legacy_synthesis_vaciado
from tools import pgmx_vaciado, pgmx_vaciado_v2
from tools.pgmx_vaciado import scan_samples as legacy_vaciado_scan_samples
from tools.pgmx_vaciado import trace_engine as legacy_vaciado_trace_engine
from tools.pgmx_vaciado_v2 import trace as legacy_vaciado_v2_trace
from pgmx.vaciado import trace as vaciado_trace
from pgmx.vaciado_lab import scan_samples as vaciado_scan_samples
from pgmx.vaciado_lab import trace_engine as vaciado_trace_engine


class PgmxPublicFacadeTests(unittest.TestCase):
    def test_legacy_synthesis_facades_reexport_pgmx_synthesis(self) -> None:
        self.assertIs(synthesize_pgmx.PocketMillingSpec, synthesis_core.PocketMillingSpec)
        self.assertIs(synthesize_pgmx.main, synthesis.main)
        self.assertIs(synthesis.main, synthesis_cli.main)
        self.assertIs(synthesis_core.main, synthesis_cli.main)
        self.assertIn("main", synthesize_pgmx.__all__)

        self.assertIs(pgmx_synthesis.PocketMillingSpec, synthesis.PocketMillingSpec)
        self.assertIs(pgmx_synthesis.main, synthesis.main)
        self.assertIs(legacy_synthesis_core.PocketMillingSpec, synthesis_core.PocketMillingSpec)
        self.assertIs(legacy_synthesis_core.main, synthesis_core.main)
        self.assertIs(
            legacy_synthesis_vaciado.vaciado_support_status,
            synthesis_vaciado.vaciado_support_status,
        )

    def test_legacy_snapshot_and_adapter_facades_reexport_pgmx_modules(self) -> None:
        self.assertIs(pgmx_snapshot.read_pgmx_snapshot, snapshot.read_pgmx_snapshot)
        self.assertIs(pgmx_snapshot.main, snapshot.main)
        self.assertIn("main", pgmx_snapshot.__all__)

        self.assertIs(pgmx_adapters.adapt_pgmx_path, adapters.adapt_pgmx_path)
        self.assertIs(pgmx_adapters.main, adapters.main)
        self.assertIn("main", pgmx_adapters.__all__)

    def test_legacy_vaciado_facades_reexport_current_boundaries(self) -> None:
        self.assertIs(pgmx_vaciado.EXTERNAL_ROOT, vaciado_lab.EXTERNAL_ROOT)
        self.assertIs(legacy_vaciado_scan_samples.main, vaciado_scan_samples.main)
        self.assertIs(
            legacy_vaciado_trace_engine.generate_contour_parallel_pocket_trace,
            vaciado_trace_engine.generate_contour_parallel_pocket_trace,
        )
        self.assertIs(
            vaciado_trace_engine.generate_contour_parallel_pocket_trace,
            milling_pocket_trace.generate_contour_parallel_pocket_trace,
        )

        self.assertIs(pgmx_vaciado_v2.VaciadoGeometry, vaciado.VaciadoGeometry)
        self.assertIs(
            legacy_vaciado_v2_trace.plan_rectangular_no_islands,
            vaciado_trace.plan_rectangular_no_islands,
        )


if __name__ == "__main__":
    unittest.main()
