"""
Backtesting Module

Vectorized backtesting engine for strategy validation.
"""

from .backtesting_engine import BacktestingEngine
from .walk_forward import WalkForwardTester

__all__ = [
    'BacktestingEngine',
    'WalkForwardTester'
]
