"""
Momentum Strategy Module

Implements momentum-based trading strategy using multiple technical indicators.
"""

import pandas as pd
import numpy as np
from typing import List
import logging

from .base_strategy import BaseStrategy, StrategyConfig, Signal, SignalType

logger = logging.getLogger(__name__)


class MomentumStrategy(BaseStrategy):
    """
    Momentum trading strategy
    
    Identifies strong trends using:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Moving Average crossovers
    - Volume confirmation
    """
    
    def __init__(self, config: StrategyConfig):
        """Initialize momentum strategy"""
        super().__init__(config)
        
        # Strategy-specific parameters
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.ma_fast = 20
        self.ma_slow = 50
        self.volume_ma_period = 20
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators"""
        df = data.copy()
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # MACD
        macd_data = self._calculate_macd(
            df['close'], 
            self.macd_fast, 
            self.macd_slow, 
            self.macd_signal
        )
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_histogram'] = macd_data['histogram']
        
        # Moving averages
        df['ma_fast'] = df['close'].rolling(window=self.ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(window=self.ma_slow).mean()
        
        # Volume indicators
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Trend strength
        df['trend_strength'] = (df['close'] - df['ma_slow']) / df['ma_slow'] * 100
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(
        self, 
        prices: pd.Series, 
        fast: int, 
        slow: int, 
        signal: int
    ) -> dict:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate momentum-based trading signals
        
        Buy signals when:
        - Price above MA fast and MA fast above MA slow (uptrend)
        - MACD crosses above signal line
        - RSI not overbought
        - Volume above average
        
        Sell signals when:
        - Price below MA fast and MA fast below MA slow (downtrend)
        - MACD crosses below signal line
        - RSI not oversold
        """
        if not self.validate_data(data):
            return []
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        signals = []
        
        # Only generate signal on the latest data point
        if len(df) < 2:
            return signals
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        symbol = current.get('symbol', 'UNKNOWN')
        
        # Check for buy signal
        if self._check_buy_conditions(current, previous):
            signal_strength = self._calculate_signal_strength(current, 'buy')
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=signal_strength,
                price=current['close'],
                quantity=0,  # Will be set by position sizer
                timestamp=current.name if hasattr(current, 'name') else pd.Timestamp.now(),
                metadata={
                    'rsi': current['rsi'],
                    'macd': current['macd'],
                    'trend_strength': current['trend_strength']
                }
            )
            
            signals.append(signal)
            self.performance_metrics['total_signals'] += 1
            logger.info(f"BUY signal generated for {symbol} at {current['close']}")
        
        # Check for sell signal
        elif self._check_sell_conditions(current, previous):
            signal_strength = self._calculate_signal_strength(current, 'sell')
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=signal_strength,
                price=current['close'],
                quantity=0,
                timestamp=current.name if hasattr(current, 'name') else pd.Timestamp.now(),
                metadata={
                    'rsi': current['rsi'],
                    'macd': current['macd'],
                    'trend_strength': current['trend_strength']
                }
            )
            
            signals.append(signal)
            self.performance_metrics['total_signals'] += 1
            logger.info(f"SELL signal generated for {symbol} at {current['close']}")
        
        # Check exit conditions for existing positions
        if symbol in self.positions:
            if self.check_stop_loss(symbol, current['close']):
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG if self.positions[symbol]['side'] == 'long' else SignalType.CLOSE_SHORT,
                    strength=1.0,
                    price=current['close'],
                    quantity=self.positions[symbol]['quantity'],
                    timestamp=current.name if hasattr(current, 'name') else pd.Timestamp.now(),
                    metadata={'reason': 'stop_loss'}
                ))
            
            elif self.check_take_profit(symbol, current['close']):
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG if self.positions[symbol]['side'] == 'long' else SignalType.CLOSE_SHORT,
                    strength=1.0,
                    price=current['close'],
                    quantity=self.positions[symbol]['quantity'],
                    timestamp=current.name if hasattr(current, 'name') else pd.Timestamp.now(),
                    metadata={'reason': 'take_profit'}
                ))
        
        return signals
    
    def _check_buy_conditions(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if buy conditions are met"""
        # Price trend
        uptrend = (
            current['close'] > current['ma_fast'] and
            current['ma_fast'] > current['ma_slow']
        )
        
        # MACD crossover
        macd_cross = (
            previous['macd'] <= previous['macd_signal'] and
            current['macd'] > current['macd_signal']
        )
        
        # RSI not overbought
        rsi_ok = current['rsi'] < self.rsi_overbought
        
        # Volume confirmation
        volume_ok = current['volume_ratio'] > 1.0
        
        return uptrend and macd_cross and rsi_ok and volume_ok
    
    def _check_sell_conditions(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if sell conditions are met"""
        # Price trend
        downtrend = (
            current['close'] < current['ma_fast'] and
            current['ma_fast'] < current['ma_slow']
        )
        
        # MACD crossover
        macd_cross = (
            previous['macd'] >= previous['macd_signal'] and
            current['macd'] < current['macd_signal']
        )
        
        # RSI not oversold
        rsi_ok = current['rsi'] > self.rsi_oversold
        
        # Volume confirmation
        volume_ok = current['volume_ratio'] > 1.0
        
        return downtrend and macd_cross and rsi_ok and volume_ok
    
    def _calculate_signal_strength(self, current: pd.Series, signal_type: str) -> float:
        """Calculate signal strength (0.0 to 1.0)"""
        strength = 0.0
        
        # RSI contribution
        if signal_type == 'buy':
            rsi_strength = (self.rsi_oversold - current['rsi']) / self.rsi_oversold
            rsi_strength = max(0, min(1, rsi_strength))
        else:
            rsi_strength = (current['rsi'] - self.rsi_overbought) / (100 - self.rsi_overbought)
            rsi_strength = max(0, min(1, rsi_strength))
        
        # MACD contribution
        macd_strength = abs(current['macd_histogram']) / current['close'] * 1000
        macd_strength = max(0, min(1, macd_strength))
        
        # Trend strength contribution
        trend_contribution = abs(current['trend_strength']) / 10
        trend_contribution = max(0, min(1, trend_contribution))
        
        # Volume contribution
        volume_strength = min(1, (current['volume_ratio'] - 1) / 2)
        
        # Weighted average
        strength = (
            0.3 * rsi_strength +
            0.3 * macd_strength +
            0.2 * trend_contribution +
            0.2 * volume_strength
        )
        
        return max(0.0, min(1.0, strength))
