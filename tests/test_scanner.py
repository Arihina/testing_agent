"""Тесты Source Scanner."""

from pathlib import Path

from tester_agent.analysis.scanner import SourceScanner

FIXTURE = Path(__file__).parent / "fixtures" / "sample_pkg"


def test_scan_finds_functions_and_methods():
    targets = SourceScanner().scan_package(FIXTURE)
    names = {t.name for t in targets}
    assert "add" in names
    assert "normalize" in names
    assert "rank_users" in names
    assert "UserService.find_by_name" in names
    # сканер собирает всё, включая приватное — фильтрация на стороне CandidateFilter
    assert "_private_helper" in names


def test_target_metadata():
    targets = {t.name: t for t in SourceScanner().scan_package(FIXTURE)}
    add = targets["add"]
    assert add.complexity == 1
    assert add.is_method is False
    assert add.docstring == "Складывает два числа."
    assert add.signature_hash

    method = targets["UserService.find_by_name"]
    assert method.is_method is True
    assert method.complexity >= 2
