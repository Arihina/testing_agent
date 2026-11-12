"""Тесты paths.module_info."""

from pathlib import Path

from tester_agent.analysis.paths import module_info

FIXTURE = Path(__file__).parent / "fixtures" / "sample_pkg"


def test_module_info_package():
    module, root = module_info(FIXTURE / "service.py")
    assert module == "sample_pkg.service"
    assert root.name == "fixtures"


def test_module_info_plain_file():
    module, _ = module_info(Path("/tmp") / "script.py")
    assert module == "script"
