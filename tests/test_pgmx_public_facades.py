import unittest

from pgmx import adapters, snapshot, synthesis
from pgmx.synthesis import cli as synthesis_cli
from pgmx.synthesis import core as synthesis_core
from pgmx.synthesis import pocket_support as synthesis_pocket_support
from pgmx.synthesis.milling import pocket_contract as milling_pocket_contract


class PgmxPublicBoundaryTests(unittest.TestCase):
    def test_synthesis_public_api_uses_modular_package(self) -> None:
        self.assertIs(synthesis.PocketSpec, synthesis_core.PocketSpec)
        self.assertIs(synthesis.main, synthesis_cli.main)
        self.assertIs(synthesis_core.main, synthesis_cli.main)
        self.assertIn("main", synthesis.__all__)

    def test_snapshot_and_adapter_public_apis_are_direct_modules(self) -> None:
        self.assertTrue(callable(snapshot.read_pgmx_snapshot))
        self.assertTrue(callable(snapshot.main))
        self.assertIn("main", snapshot.__all__)

        self.assertTrue(callable(adapters.adapt_pgmx_path))
        self.assertTrue(callable(adapters.main))
        self.assertIn("main", adapters.__all__)

    def test_pocket_milling_contract_is_the_final_public_contract(self) -> None:
        self.assertTrue(callable(milling_pocket_contract.plan_rectangular_no_islands))
        self.assertIn("VaciadoGeometry", milling_pocket_contract.__all__)
        self.assertIn("VaciadoDepth", milling_pocket_contract.__all__)

        status = synthesis_pocket_support.pocket_support_status()
        self.assertTrue(status.enabled)
        self.assertEqual(status.model_package, "pgmx.synthesis.milling.pocket")
        self.assertFalse(status.legacy_engine_allowed)


if __name__ == "__main__":
    unittest.main()
