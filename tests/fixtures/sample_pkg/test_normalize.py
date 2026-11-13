import pytest

from sample_pkg.utils import normalize

def test_normalize():
    # Тест с обычными строками
    input_values = ["Hello", "WORLD", "  Python ", "TEST"]
    expected_output = ["hello", "world", "python", "test"]
    assert normalize(input_values) == expected_output

    # Тест со строками, содержащими только пробелы
    input_values = ["   ", "\t\n", "  ", ""]
    expected_output = []
    assert normalize(input_values) == expected_output

    # Тест с混合ом нормальных и пустых строк
    input_values = ["Valid", "", "  invalid  ", "Another"]
    expected_output = ["valid", "invalid", "another"]
    assert normalize(input_values) == expected_output

    # Тест с уже нижним регистром
    input_values = ["already", "lowercase", "strings"]
    expected_output = ["already", "lowercase", "strings"]
    assert normalize(input_values) == expected_output

    # Тест с пустым списком
    input_values = []
    expected_output = []
    assert normalize(input_values) == expected_output