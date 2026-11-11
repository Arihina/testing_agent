"""Candidate Filter: отбор целей по сложности, приватности, покрытию и хешу."""

from __future__ import annotations

from ..contracts import Target


class CandidateFilter:
    """Превращает объявления в отсортированный список целей."""

    def __init__(self, min_complexity: int = 2, exclude_private: bool = True) -> None:
        self.min_complexity = min_complexity
        self.exclude_private = exclude_private

    def filter(
        self,
        declarations: list[Target],
        coverage: dict[str, set[int]] | None = None,
        known_hashes: frozenset[str] = frozenset(),
    ) -> list[Target]:
        """Отсеять приватные, тривиальные, покрытые и неизменённые цели.

        ``coverage`` — словарь ``{file_path: {покрытые строки}}``;
        ``known_hashes`` — хеши сигнатур уже принятых тестов.
        """
        targets: list[Target] = []
        for decl in declarations:
            if self.exclude_private and self._is_private(decl.name):
                continue
            if decl.complexity < self.min_complexity:
                continue
            if decl.signature_hash in known_hashes:
                continue
            covered = self._coverage_of(decl, coverage)
            if covered is True:
                continue
            targets.append(decl.model_copy(update={"covered": covered}))
        targets.sort(key=lambda t: (-t.complexity, t.name))
        return targets

    @staticmethod
    def _is_private(name: str) -> bool:
        """Приватным считается имя, чья последняя часть начинается с ``_``."""
        return name.rsplit(".", 1)[-1].startswith("_")

    @staticmethod
    def _coverage_of(
        target: Target,
        coverage: dict[str, set[int]] | None,
    ) -> bool | None:
        if coverage is None or target.file_path not in coverage:
            return None
        covered_lines = coverage[target.file_path]
        end = target.end_line or target.line
        lines = range(target.line, end + 1)
        return all(ln in covered_lines for ln in lines)
