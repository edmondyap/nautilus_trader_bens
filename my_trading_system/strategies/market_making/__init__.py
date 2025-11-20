"""
Market Making Strategies

Simple market making strategies that provide liquidity by maintaining
bid and ask orders around a reference price.
"""

from my_trading_system.strategies.market_making.simple_market_maker import (
    TestSingleMakerStrategy,
    TestSingleMakerStrategyConfig,
)

__all__ = [
    "TestSingleMakerStrategy",
    "TestSingleMakerStrategyConfig",
]
