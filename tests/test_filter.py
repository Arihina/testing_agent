"""Тесты Candidate Filter."""

from pathlib import Path

from tester_agent.analysis.filter import CandidateFilter
from tester_agent.analysis.scanner import SourceScanner

FIXTURE = Path(__file__).parent / "fixtures" / "sample_pkg"


def _scan():
    return SourceScanner().scan_package(FIXTURE)


def test_excludes_private_and_trivial():
    names = {t.name for t in CandidateFilter().filter(_scan())}
    assert "_private_helper" not in names
    assert "UserService.__init__" not in names  # dunder считается приватным
    assert "add" not in names  # цикломатика 1
    assert "normalize" in names
    assert "UserService.find_by_name" in names
    assert "rank_users" in names


def test_known_hashes_are_skipped():
    decls = _scan()
    decl = next(d for d in decls if d.name == "normalize")
    targets = CandidateFilter().filter(decls, known_hashes=frozenset({decl.signature_hash}))
    assert all(t.name != "normalize" for t in targets)


def test_fully_covered_is_skipped():
    decls = _scan()
    decl = next(d for d in decls if d.name == "normalize")
    end = decl.end_line or decl.line
    coverage = {decl.file_path: set(range(decl.line, end + 1))}
    targets = CandidateFilter().filter(decls, coverage=coverage)
    assert all(t.name != "normalize" for t in targets)


def test_sorting_complexity_desc():
    targets = CandidateFilter().filter(_scan())
    complexities = [t.complexity for t in targets]
    assert complexities == sorted(complexities, reverse=True)
