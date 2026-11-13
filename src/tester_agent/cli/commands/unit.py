"""Команда `unit`: генерация, доводка и валидация unit-тестов (§4)."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ...analysis import CandidateFilter, ContextBuilder, SourceScanner
from ...config.loader import load_config
from ...execution import PytestAdapter, SandboxRunner
from ...generation import LLMError, LLMGateway, RepairSynthesizer, TestSynthesizer
from ...infrastructure import ArtifactStore, Reporter, StateStore
from ...orchestrator import UnitScenario
from ...validation import Validator
from ..app import app
from ..exit_codes import EXIT_ENV_ERROR

console = Console()


@app.command("unit")
def unit(
    path: str | None = typer.Argument(None, help="Путь к пакету (иначе — из конфига targets)."),
    diff: bool = typer.Option(False, "--diff", help="Отбирать только объекты, изменённые относительно базовой ветки."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Показать отобранные цели и план без вызова модели."),
    limit: int | None = typer.Option(None, "--limit", help="Обработать не более N целей."),
    model: str | None = typer.Option(None, "--model", help="Модель Ollama: qwen2.5-coder:14b | qwen3-coder:30b."),
) -> None:
    """Сгенерировать, довести и провалидировать unit-тесты."""
    config = load_config()
    if model is not None:
        config.generation.model = model

    scanner = SourceScanner()
    declarations = _collect_declarations(scanner, config, path, diff)
    state_store = StateStore()
    targets = CandidateFilter().filter(
        declarations, coverage=None, known_hashes=state_store.accepted_hashes()
    )

    if dry_run:
        _print_targets(targets)
        if targets:
            builder = ContextBuilder()
            for target in targets:
                rprint(f"\n--- ContextPackage: {target.name} ---")
                rprint(builder.build(target).model_dump())
        return

    if not targets:
        typer.echo("Нет целей (все покрыты, тривиальны или уже приняты).")
        return

    if limit is not None:
        targets = targets[:limit]

    _generate(config, targets, state_store)


def _generate(config, targets, state_store) -> None:
    sandbox = SandboxRunner(timeout_seconds=config.execution.timeout_seconds)
    adapter = PytestAdapter(sandbox)
    gateway = LLMGateway(
        base_url=config.generation.base_url,
        model=config.generation.model,
        temperature=config.generation.temperature,
        timeout_seconds=config.generation.timeout_seconds,
        max_retries=config.generation.max_retries,
        token_budget=config.generation.token_budget,
        cache_path=Path(".testagent") / "cache" / "llm_cache.json",
    )
    artifacts = ArtifactStore()
    run_dir = artifacts.create_run()
    scenario = UnitScenario(
        builder=ContextBuilder(),
        synthesizer=TestSynthesizer(gateway, artifact_store=artifacts),
        repairer=RepairSynthesizer(gateway, artifact_store=artifacts),
        adapter=adapter,
        artifacts=artifacts,
        validator=Validator(adapter, config.gates),
        state_store=state_store,
        max_repair_iterations=config.generation.max_repair_iterations,
    )

    typer.echo(f"Генерация и прогон для {len(targets)} целей (модель {config.generation.model})…")
    outcomes = []
    for target in targets:
        typer.echo(f"\n{'=' * 60}\n{target.name}\n{'=' * 60}")
        try:
            outcome = scenario.run(target)
        except LLMError as exc:
            typer.echo(f"Ошибка генерации: {exc}", err=True)
            continue
        outcomes.append(outcome)
        _print_outcome(outcome)

    Reporter(run_dir).write_report(outcomes)
    typer.echo(f"\nОтчёт: {run_dir}/report.json, {run_dir}/report.md")


def _print_outcome(outcome) -> None:
    verdict = outcome.verdict
    if verdict and verdict.accepted:
        typer.echo(f"[ACCEPT] итераций: {outcome.iteration}")
        typer.echo(outcome.source)
    else:
        gate = verdict.failed_gate if verdict else "?"
        reason = verdict.reason if verdict else ""
        typer.echo(f"[REJECT] {gate}: {reason} (итераций: {outcome.iteration})")
        if outcome.passed is False:
            lines = outcome.output.strip().splitlines()
            typer.echo("\n".join(lines[-12:]) if lines else "")


def _collect_declarations(scanner, config, path, diff):
    if diff:
        return scanner.scan_git_diff(config.targets.base_branch)
    if path:
        return scanner.scan_package(path)
    if config.targets.include:
        declarations = []
        for p in config.targets.include:
            declarations.extend(scanner.scan_package(p))
        return declarations
    typer.echo(
        "Укажите путь к пакету или настройте targets.include в .testagent/config.toml.",
        err=True,
    )
    raise typer.Exit(EXIT_ENV_ERROR)


def _print_targets(targets) -> None:
    typer.echo(f"Отобрано целей: {len(targets)}")
    table = Table(title="Цели для генерации тестов")
    table.add_column("name", no_wrap=True)
    table.add_column("complexity", justify="right")
    table.add_column("module")
    table.add_column("line", justify="right")
    for t in targets:
        table.add_row(t.name, str(t.complexity), t.module, str(t.line))
    console.print(table)
