"""Команда `load`: построить профиль и прогнать нагрузку."""

from __future__ import annotations

import typer
from rich import print as rprint

from ...analysis import SpecReader
from ...config.loader import load_config
from ...execution import LoadRunner, LoadScriptBuilder, SmokeProber
from ...generation import PayloadSynthesizer
from ...infrastructure import ArtifactStore, BaselineStore, machine_id
from ...validation import check_regression
from ..app import app
from ..exit_codes import EXIT_ENV_ERROR, EXIT_GATES_FAILED


@app.command("load")
def load(
    base_url: str | None = typer.Argument(None, help="Базовый URL сервиса (иначе — config.load.base_url)."),
    baseline: bool = typer.Option(False, "--baseline", help="Зафиксировать текущие метрики как эталон."),
) -> None:
    """Построить нагрузочный профиль из /openapi.json и прогнать нагрузку."""
    config = load_config()
    url = (base_url or config.load.base_url).rstrip("/")

    try:
        endpoints, schemas = SpecReader().read_full(f"{url}/openapi.json")
    except Exception as exc:  # noqa: BLE001 — сетевые/JSON ошибки при чтении спеки
        typer.echo(f"Не удалось прочитать OpenAPI: {exc}", err=True)
        raise typer.Exit(EXIT_ENV_ERROR)

    payloader = PayloadSynthesizer(schemas)
    requests = [payloader.synthesize(e) for e in endpoints]
    passed = SmokeProber(url).probe(requests)
    typer.echo(f"Smoke: {len(passed)}/{len(requests)} ручек отвечают 2xx")

    if not passed:
        typer.echo("Нет рабочих ручек — прерываю.", err=True)
        raise typer.Exit(EXIT_GATES_FAILED)

    script = LoadScriptBuilder().build(
        url, passed, config.load.rate, config.load.warmup_seconds, config.load.duration_seconds
    )
    artifacts = ArtifactStore()
    run_dir = artifacts.create_run()
    script_path = run_dir / "load_script.js"
    script_path.write_text(script, encoding="utf-8")

    try:
        metrics = LoadRunner().run(script, run_dir / "summary.json")
    except (RuntimeError, FileNotFoundError) as exc:
        typer.echo(f"Load Runner: {exc}", err=True)
        typer.echo(f"k6-скрипт сгенерирован: {script_path}")
        raise typer.Exit(EXIT_ENV_ERROR)

    metrics.machine_id = machine_id()
    store = BaselineStore()
    previous = store.get(metrics.machine_id)

    if baseline or previous is None:
        store.set(metrics)
        typer.echo(f"Baseline зафиксирован для машины {metrics.machine_id}")

    rprint(metrics.model_dump())
    verdict = check_regression(metrics, previous, config.load.regression_threshold)
    if not verdict.accepted:
        typer.echo(f"Regression: {verdict.reason}", err=True)
        raise typer.Exit(EXIT_GATES_FAILED)
    typer.echo("OK: регрессии нет.")
