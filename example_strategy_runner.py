#!/usr/bin/env python3
"""
Example Strategy Runner

Demonstrates how to run backtests on trading strategies.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config_manager import ConfigManager
from src.strategy_engine import MomentumStrategy, MeanReversionStrategy
from src.strategy_engine.base_strategy import StrategyConfig
from src.backtesting import BacktestingEngine
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def generate_sample_data(symbol: str = 'BTC/USDT', days: int = 365) -> pd.DataFrame:
    """
    Generate sample OHLCV data for testing
    
    In production, use HistoricalDataFetcher to get real data
    """
    logger.info(f"Generating sample data for {symbol}")
    
    dates = pd.date_range(
        end=datetime.now(),
        periods=days * 24,  # Hourly data
        freq='H'
    )
    
    # Generate random walk price data
    import numpy as np
    np.random.seed(42)
    
    returns = np.random.normal(0.0001, 0.02, len(dates))
    price = 40000 * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'open': price * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
        'high': price * (1 + np.random.uniform(0, 0.02, len(dates))),
        'low': price * (1 + np.random.uniform(-0.02, 0, len(dates))),
        'close': price,
        'volume': np.random.uniform(100, 1000, len(dates))
    }, index=dates)
    
    # Ensure high >= low
    data['high'] = data[['high', 'close', 'open']].max(axis=1)
    data['low'] = data[['low', 'close', 'open']].min(axis=1)
    
    return data


async def run_momentum_backtest():
    """Run backtest for momentum strategy"""
    logger.info("=" * 60)
    logger.info("Momentum Strategy Backtest")
    logger.info("=" * 60)
    
    # Generate sample data
    data = await generate_sample_data('BTC/USDT', days=180)
    
    # Create strategy
    config = StrategyConfig(
        name='momentum',
        symbols=['BTC/USDT'],
        timeframe='1h',
        lookback_period=100,
        max_position_size=0.15,
        stop_loss_pct=0.02,
        take_profit_pct=0.05,
        risk_per_trade=0.01
    )
    
    strategy = MomentumStrategy(config)
    
    # Create backtesting engine
    backtest_config = {
        'initial_capital': 100000,
        'commission': 0.001,
        'slippage': 0.0005
    }
    
    engine = BacktestingEngine(backtest_config)
    
    # Run backtest
    results = engine.run_backtest(
        data,
        strategy,
        start_date=data.index[0],
        end_date=data.index[-1]
    )
    
    # Display results
    metrics = results.get('metrics', {})
    
    logger.info("\nBacktest Results:")
    logger.info(f"Total Return: {metrics.get('total_return', 0):.2%}")
    logger.info(f"Annualized Return: {metrics.get('annualized_return', 0):.2%}")
    logger.info(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    logger.info(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
    logger.info(f"Win Rate: {metrics.get('win_rate', 0):.2%}")
    logger.info(f"Total Trades: {metrics.get('total_trades', 0)}")
    logger.info(f"Final Portfolio Value: ${metrics.get('final_portfolio_value', 0):,.2f}")
    
    return results


async def run_mean_reversion_backtest():
    """Run backtest for mean reversion strategy"""
    logger.info("=" * 60)
    logger.info("Mean Reversion Strategy Backtest")
    logger.info("=" * 60)
    
    # Generate sample data
    data = await generate_sample_data('ETH/USDT', days=180)
    
    # Create strategy
    config = StrategyConfig(
        name='mean_reversion',
        symbols=['ETH/USDT'],
        timeframe='1h',
        lookback_period=100,
        max_position_size=0.1,
        stop_loss_pct=0.015,
        take_profit_pct=0.03,
        risk_per_trade=0.008
    )
    
    strategy = MeanReversionStrategy(config)
    
    # Create backtesting engine
    backtest_config = {
        'initial_capital': 100000,
        'commission': 0.001,
        'slippage': 0.0005
    }
    
    engine = BacktestingEngine(backtest_config)
    
    # Run backtest
    results = engine.run_backtest(
        data,
        strategy,
        start_date=data.index[0],
        end_date=data.index[-1]
    )
    
    # Display results
    metrics = results.get('metrics', {})
    
    logger.info("\nBacktest Results:")
    logger.info(f"Total Return: {metrics.get('total_return', 0):.2%}")
    logger.info(f"Annualized Return: {metrics.get('annualized_return', 0):.2%}")
    logger.info(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    logger.info(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
    logger.info(f"Win Rate: {metrics.get('win_rate', 0):.2%}")
    logger.info(f"Total Trades: {metrics.get('total_trades', 0)}")
    logger.info(f"Final Portfolio Value: ${metrics.get('final_portfolio_value', 0):,.2f}")
    
    return results


async def main():
    """Main entry point"""
    logger.info("Worldloom Strategy Backtesting")
    logger.info("=" * 60)
    
    # Run momentum backtest
    await run_momentum_backtest()
    
    print("\n")
    
    # Run mean reversion backtest
    await run_mean_reversion_backtest()
    
    logger.info("\n" + "=" * 60)
    logger.info("All backtests completed")


if __name__ == '__main__':
    asyncio.run(main())
