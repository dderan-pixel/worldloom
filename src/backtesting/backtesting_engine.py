"""
Backtesting Engine

Vectorized backtesting for trading strategies.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class BacktestingEngine:
    """
    Vectorized backtesting engine
    
    Fast backtesting using pandas vectorized operations.
    Supports:
    - Multiple strategies
    - Transaction costs
    - Slippage modeling
    - Performance metrics
    """
    
    def __init__(self, config: Dict):
        """
        Initialize backtesting engine
        
        Args:
            config: Backtesting configuration
        """
        self.config = config
        
        # Backtest parameters
        self.initial_capital = config.get('initial_capital', 100000)
        self.commission = config.get('commission', 0.001)  # 0.1%
        self.slippage = config.get('slippage', 0.0005)  # 0.05%
        
        # Results
        self.results: Optional[pd.DataFrame] = None
        self.trades: List[Dict] = []
        self.metrics: Dict = {}
        
        logger.info("Backtesting engine initialized")
    
    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            data: Historical OHLCV data
            strategy: Trading strategy instance
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            Backtest results dict
        """
        logger.info(f"Starting backtest for {strategy.name}")
        
        # Filter data by date range
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if len(data) < 2:
            logger.error("Insufficient data for backtest")
            return {}
        
        # Calculate indicators
        data_with_indicators = strategy.calculate_indicators(data)
        
        # Generate signals
        signals_list = []
        for i in range(len(data_with_indicators)):
            row_data = data_with_indicators.iloc[:i+1]
            if len(row_data) >= strategy.config.lookback_period:
                signals = strategy.generate_signals(row_data)
                if signals:
                    signals_list.extend(signals)
        
        # Simulate trading
        results = self._simulate_trading(
            data_with_indicators,
            signals_list
        )
        
        # Calculate metrics
        self.metrics = self._calculate_metrics(results)
        
        logger.info(f"Backtest complete for {strategy.name}")
        
        return {
            'results': results,
            'metrics': self.metrics,
            'trades': self.trades
        }
    
    def _simulate_trading(
        self,
        data: pd.DataFrame,
        signals: List
    ) -> pd.DataFrame:
        """
        Simulate trading based on signals
        
        Args:
            data: Market data
            signals: List of trading signals
            
        Returns:
            Results DataFrame with positions and returns
        """
        results = data.copy()
        results['signal'] = 0
        results['position'] = 0
        results['returns'] = 0.0
        results['portfolio_value'] = self.initial_capital
        
        # Apply signals to results
        for signal in signals:
            timestamp = signal.timestamp
            if timestamp in results.index:
                if signal.signal_type.value in ['buy']:
                    results.loc[timestamp, 'signal'] = 1
                elif signal.signal_type.value in ['sell']:
                    results.loc[timestamp, 'signal'] = -1
                elif signal.signal_type.value in ['close_long', 'close_short']:
                    results.loc[timestamp, 'signal'] = 0
        
        # Calculate positions and returns
        cash = self.initial_capital
        position = 0
        entry_price = 0
        
        for i in range(1, len(results)):
            current_signal = results.iloc[i]['signal']
            current_price = results.iloc[i]['close']
            
            # Execute signal
            if current_signal == 1 and position == 0:  # Buy
                # Apply transaction costs
                effective_price = current_price * (1 + self.slippage + self.commission)
                units = cash / effective_price
                
                position = units
                entry_price = effective_price
                cash = 0
                
                self.trades.append({
                    'timestamp': results.index[i],
                    'type': 'buy',
                    'price': effective_price,
                    'units': units
                })
                
            elif current_signal == -1 and position > 0:  # Sell
                # Apply transaction costs
                effective_price = current_price * (1 - self.slippage - self.commission)
                
                cash = position * effective_price
                pnl = cash - self.initial_capital
                
                self.trades.append({
                    'timestamp': results.index[i],
                    'type': 'sell',
                    'price': effective_price,
                    'units': position,
                    'pnl': pnl
                })
                
                position = 0
                entry_price = 0
            
            # Update position and portfolio value
            results.iloc[i, results.columns.get_loc('position')] = position
            
            if position > 0:
                portfolio_value = position * current_price
            else:
                portfolio_value = cash
            
            results.iloc[i, results.columns.get_loc('portfolio_value')] = portfolio_value
        
        # Calculate returns
        results['returns'] = results['portfolio_value'].pct_change()
        
        self.results = results
        return results
    
    def _calculate_metrics(self, results: pd.DataFrame) -> Dict:
        """Calculate performance metrics"""
        if results.empty or len(results) < 2:
            return {}
        
        returns = results['returns'].dropna()
        
        # Total return
        initial_value = self.initial_capital
        final_value = results['portfolio_value'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value
        
        # Annualized return
        days = (results.index[-1] - results.index[0]).days
        if days > 0:
            annualized_return = (1 + total_return) ** (365 / days) - 1
        else:
            annualized_return = 0.0
        
        # Volatility
        volatility = returns.std() * np.sqrt(252)
        
        # Sharpe ratio
        if volatility > 0:
            sharpe_ratio = annualized_return / volatility
        else:
            sharpe_ratio = 0.0
        
        # Maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        profitable_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        win_rate = len(profitable_trades) / len(self.trades) if self.trades else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': abs(max_drawdown),
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'profitable_trades': len(profitable_trades),
            'final_portfolio_value': final_value
        }
    
    def get_equity_curve(self) -> pd.Series:
        """Get equity curve"""
        if self.results is not None:
            return self.results['portfolio_value']
        return pd.Series()
    
    def get_trade_history(self) -> List[Dict]:
        """Get trade history"""
        return self.trades
