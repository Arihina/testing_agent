"""Validation: quality gates, отсев, вердикт."""

from .regression import check_regression
from .validator import Validator

__all__ = ["Validator", "check_regression"]
