import importlib
import pkgutil

import app.modules


def test_module_facades_define_explicit_all_and_hide_repositories() -> None:
    package = app.modules
    assert package.__path__ is not None

    checked_modules = 0
    for module_info in pkgutil.iter_modules(package.__path__):
        if not module_info.ispkg:
            continue

        module_name = f"app.modules.{module_info.name}"
        mod = importlib.import_module(module_name)

        assert hasattr(mod, "__all__"), f"Module {module_name} must define __all__"
        public_exports = mod.__all__
        assert isinstance(public_exports, list), f"{module_name}.__all__ must be a list"
        assert len(public_exports) > 0, f"{module_name}.__all__ must not be empty"

        for export_name in public_exports:
            assert hasattr(mod, export_name), (
                f"Exported symbol '{export_name}' not found in {module_name}"
            )
            assert not export_name.endswith("Repository"), (
                f"Repository '{export_name}' MUST NOT be exported from facade {module_name}"
            )
        checked_modules += 1

    assert checked_modules == 15, f"Expected 15 modules, but checked {checked_modules}"
