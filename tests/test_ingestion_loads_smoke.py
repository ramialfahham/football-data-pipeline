import importlib
import pkgutil
import unittest

import ingestion.api_football.loads as loads_pkg


class TestApiFootballLoadsImport(unittest.TestCase):
    def test_all_loader_modules_import(self) -> None:
        """
        Smoke-test import wiring for ingestion loaders.

        This catches missing imports (for example merge helpers) before
        runtime pipeline execution.
        """
        module_names = sorted(
            name
            for _, name, ispkg in pkgutil.iter_modules(loads_pkg.__path__)
            if not ispkg and not name.startswith("_")
        )

        for module_name in module_names:
            with self.subTest(module=module_name):
                importlib.import_module(f"{loads_pkg.__name__}.{module_name}")


if __name__ == "__main__":
    unittest.main()
