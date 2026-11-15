# Testing Agent

CLI-агент для автоматизации тестирования Python-бэкенда: генерирует unit-тесты и строит нагрузочные профили по OpenAPI-спецификации. Детерминированный пайплайн с LLM (локальная Ollama) в узких точках генерации и интерпретации.

## Возможности

- **`unit`** — обход AST, отбор целей, генерация pytest-тестов и итеративная починка упавших, валидация гейтами (Syntax / Green / Coverage / Assertion / Isolation).
- **`load`** — чтение `/openapi.json`, синтез payload'ов, smoke-прогон, k6-скрипт, сравнение с baseline, интерпретация деградации.

## Установка

```bash
uv sync
```

Требуется локальная [Ollama](https://ollama.com) с моделью (по умолчанию `qwen2.5-coder:14b`):

```bash
ollama pull qwen2.5-coder:14b
```

Для сценария `load` нужен [k6](https://k6.io) (иначе генерируется только скрипт).

## Использование

```bash
uv run tester-agent init                        # создать .testagent/ и конфиг
uv run tester-agent unit <путь> --dry-run       # отобранные цели + контекст
uv run tester-agent unit <путь>                 # генерация + доводка + валидация
uv run tester-agent unit <путь> --tests-dir tests/   # принятые тесты в папку
uv run tester-agent unit <путь> --model qwen3-coder:30b  # выбор модели
uv run tester-agent unit --diff                  # только изменённые относительно ветки
uv run tester-agent load <url>                   # нагрузка
uv run tester-agent load <url> --baseline        # зафиксировать baseline
uv run tester-agent report                       # сводка последнего прогона
uv run tester-agent clean                        # удалить артефакты прогонов
```

Коды возврата: `0` — успех, `1` — гейты не пройдены, `2` — ошибка конфигурации/окружения.

## Конфигурация

`.testagent/config.toml` — разделы `targets`, `generation` (модель, бюджет токенов, лимит починки), `gates`, `execution`, `load`, `output`. Приоритет: дефолты → файл → env (`TESTER_AGENT_*`) → флаги CLI.

## Артефакты прогона

```
.testagent/
  config.toml     конфигурация
  state.json      хеши принятых тестов (идемпотентность)
  baseline.json   метрики нагрузки по машинам
  runs/<ts>/      report.json/report.md, accepted/, rejected/, generated/, prompts/
```

## Архитектура

Слои общаются только вниз, через структуры данных (`Target`, `ContextPackage`, `Candidate`, `Verdict`, `Endpoint`, `LoadMetrics`):

```
CLI → Orchestrator → { Analysis (детерм.) · Generation (LLM) · Execution (sandbox) }
                   → Validation (гейты) → Infrastructure (state/artifacts/reporter)
```

Любой выход LLM проходит через валидатор; ни один артефакт не попадает в репозиторий без quality gate.

## Разработка

```bash
uv run pytest          # тесты
uv run ruff check .    # линтер
```
