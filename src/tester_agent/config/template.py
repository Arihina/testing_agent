"""Шаблон config.toml, создаваемый командой `init` ."""

DEFAULT_CONFIG_TOML = """\
# Testing Agent configuration
# Приоритет источников: defaults → этот файл → env (TESTER_AGENT_*) → флаги CLI

[targets]
include = []
exclude = []
mode = "package"        # "package" | "diff"
base_branch = "main"

[generation]
model = "gpt-4o-mini"
temperature = 0.2
max_repair_iterations = 3
token_budget = 200000

[gates]
min_coverage_delta = 0.0
assertion_enabled = true
min_assert_ratio = 0.05
coverage_enabled = true
isolation_enabled = true

[execution]
timeout_seconds = 60
isolation = "subprocess"   # "subprocess" | "container"
# environment_path = ""     # путь к окружению для изоляции
network_enabled = false

[load]
base_url = "http://localhost:8000"
tool = "k6"                # "wrk2" | "k6"
warmup_seconds = 10
duration_seconds = 30
rate = 50
regression_threshold = 0.2

[output]
verbosity = "normal"       # "quiet" | "normal" | "verbose"
format = "both"            # "json" | "markdown" | "both"
"""
