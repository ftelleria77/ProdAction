import inspect
import re
import unittest

from core import nesting, nesting_compat
from tools.studies.cut_diagrams import ordering_lab


class NestingCompatTests(unittest.TestCase):
    def test_nesting_facade_reexports_declared_compatibility_contract(self) -> None:
        for name in nesting_compat.__all__:
            self.assertIs(getattr(nesting, name), getattr(nesting_compat, name), name)

    def test_cut_diagram_ordering_lab_usage_is_declared(self) -> None:
        source = inspect.getsource(ordering_lab)
        used_names = set(re.findall(r"\bnesting\.([A-Za-z_][A-Za-z0-9_]*)", source))

        self.assertEqual(used_names, set(nesting_compat.LAB_COMPATIBILITY_NAMES))
        for name in used_names:
            getattr(nesting, name)

    def test_cut_diagram_ordering_lab_uses_public_app_services(self) -> None:
        source = inspect.getsource(ordering_lab)

        self.assertNotIn("from app.project_store import _", source)
        self.assertNotIn("from app.settings import _", source)


if __name__ == "__main__":
    unittest.main()
