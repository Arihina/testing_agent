"""Коды возврата для встраивания в CI/pre-commit."""

EXIT_OK = 0            # успех
EXIT_GATES_FAILED = 1  # гейты не пройдены
EXIT_ENV_ERROR = 2     # ошибка конфигурации или окружения
