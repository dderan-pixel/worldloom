"""
Base Strategy Module

Abstract base class for all trading strategies with common interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    signal_type: SignalType
    strength: float  # 0.0 to 1.0
    price: float
    quantity: float
    timestamp: pd.Timestamp
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StrategyConfig:
    """Base strategy configuration"""
    name: str
    enabled: bool = True
    symbols: List[str] = None
    timeframe: str = '1h'
    lookback_period: int = 100
    max_position_size: float = 1.0
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05
    risk_per_trade: float = 0.01
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []


class BaseStrategy(ABC):
    """
    Abstract base strategy class
    
    All trading strategies must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, config: StrategyConfig):
        """
        Initialize strategy
        
        Args:
            config: Strategy configuration
        """
        self.config = config
        self.name = config.name
        self.positions: Dict[str, Dict] = {}
        self.signals_history: List[Signal] = []
        self.performance_metrics: Dict = {
            'total_signals': 0,
            'winning_signals': 0,
            'losing_signals': 0,
            'total_pnl': 0.0
        }
        
        logger.info(f"Initialized strategy: {self.name}")
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate trading signals from market data
        
        Args:
            data: Market data DataFrame with OHLCV columns
            
        Returns:
            List of trading signals
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators required for the strategy
        
        Args:
            data: Market data DataFrame
            
        Returns:
            DataFrame with additional indicator columns
        """
        pass
    
    def update_position(self, symbol: str, signal: Signal):
        """
        Update position based on signal
        
        Args:
            symbol: Trading symbol
            signal: Trading signal
        """
        if signal.signal_type in [SignalType.BUY]:
            if symbol not in self.positions:
                self.positions[symbol] = {
                    'side': 'long',
                    'entry_price': signal.price,
                    'quantity': signal.quantity,
                    'timestamp': signal.timestamp
                }
                logger.info(f"Opened LONG position for {symbol} at {signal.price}")
        
        elif signal.signal_type == SignalType.SELL:
            if symbol not in self.positions:
                self.positions[symbol] = {
                    'side': 'short',
                    'entry_price': signal.price,
                    'quantity': signal.quantity,
                    'timestamp': signal.timestamp
                }
                logger.info(f"Opened SHORT position for {symbol} at {signal.price}")
        
        elif signal.signal_type in [SignalType.CLOSE_LONG, SignalType.CLOSE_SHORT]:
            if symbol in self.positions:
                position = self.positions.pop(symbol)
                pnl = self._calculate_pnl(position, signal.price)
                self.performance_metrics['total_pnl'] += pnl
                
                if pnl > 0:
                    self.performance_metrics['winning_signals'] += 1
                else:
                    self.performance_metrics['losing_signals'] += 1
                
                logger.info(f"Closed position for {symbol} with PnL: {pnl:.2f}")
    
    def _calculate_pnl(self, position: Dict, exit_price: float) -> float:
        """Calculate PnL for a position"""
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        if position['side'] == 'long':
            return (exit_price - entry_price) * quantity
        else:  # short
            return (entry_price - exit_price) * quantity
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        Check if stop loss should trigger
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            True if stop loss triggered
        """
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        
        if position['side'] == 'long':
            loss_pct = (entry_price - current_price) / entry_price
            return loss_pct >= self.config.stop_loss_pct
        else:  # short
            loss_pct = (current_price - entry_price) / entry_price
            return loss_pct >= self.config.stop_loss_pct
    
    def check_take_profit(self, symbol: str, current_price: float) -> bool:
        """
        Check if take profit should trigger
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            True if take profit triggered
        """
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        
        if position['side'] == 'long':
            profit_pct = (current_price - entry_price) / entry_price
            return profit_pct >= self.config.take_profit_pct
        else:  # short
            profit_pct = (entry_price - current_price) / entry_price
            return profit_pct >= self.config.take_profit_pct
    
    def get_performance_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        total_trades = (
            self.performance_metrics['winning_signals'] + 
            self.performance_metrics['losing_signals']
        )
        
        win_rate = (
            self.performance_metrics['winning_signals'] / total_trades
            if total_trades > 0 else 0
        )
        
        return {
            'name': self.name,
            'total_signals': self.performance_metrics['total_signals'],
            'total_trades': total_trades,
            'winning_trades': self.performance_metrics['winning_signals'],
            'losing_trades': self.performance_metrics['losing_signals'],
            'win_rate': win_rate,
            'total_pnl': self.performance_metrics['total_pnl']
        }
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data quality
        
        Args:
            data: Market data DataFrame
            
        Returns:
            True if data is valid
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Check required columns
        if not all(col in data.columns for col in required_columns):
            logger.error(f"Missing required columns in data")
            return False
        
        # Check minimum data points
        if len(data) < self.config.lookback_period:
            logger.warning(f"Insufficient data points: {len(data)}")
            return False
        
        # Check for NaN values
        if data[required_columns].isna().any().any():
            logger.warning("Data contains NaN values")
            return False
        
        return True
