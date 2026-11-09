"""Команда `init`: создать .testagent/ и конфиг."""

from pathlib import Path

import typer

from ...config.template import DEFAULT_CONFIG_TOML
from ..app import app
from ..exit_codes import EXIT_ENV_ERROR


@app.command("init")
def init() -> None:
    """Создать служебную директорию .testagent/ и конфиг с разумными значениями."""
    agent_dir = Path.cwd() / ".testagent"
    config_path = agent_dir / "config.toml"
    try:
        (agent_dir / "runs").mkdir(parents=True, exist_ok=True)
        if config_path.exists():
            typer.echo(f"Конфиг уже существует, не перезаписываю: {config_path}")
        else:
            config_path.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
            typer.echo(f"Создан конфиг: {config_path}")
        for name in ("state.json", "baseline.json"):
            state_path = agent_dir / name
            if not state_path.exists():
                state_path.write_text("{}\n", encoding="utf-8")
        typer.echo("Готово. Можно запускать `tester-agent unit` или `tester-agent load`.")
    except OSError as exc:
        typer.echo(f"Не удалось инициализировать .testagent/: {exc}", err=True)
        raise typer.Exit(EXIT_ENV_ERROR) from exc
