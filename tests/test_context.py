"""Тесты Context Builder."""

from pathlib import Path

from tester_agent.analysis.context import ContextBuilder
from tester_agent.analysis.scanner import SourceScanner

FIXTURE = Path(__file__).parent / "fixtures" / "sample_pkg"


def _target(name):
    decls = SourceScanner().scan_package(FIXTURE)
    return next(t for t in decls if t.name == name)


def test_called_functions_depth_one():
    pkg = ContextBuilder().build(_target("UserService.sorted_users"))
    called = {f.name for f in pkg.called_functions}
    assert "_sort_by_id" in called


def test_used_types_and_pydantic_models():
    pkg = ContextBuilder().build(_target("UserService.add_user"))
    assert "User" in pkg.used_types
    assert any("class User" in src for src in pkg.pydantic_models)


def test_imports_collected():
    pkg = ContextBuilder().build(_target("UserService.names"))
    assert any("normalize" in imp for imp in pkg.imports)
