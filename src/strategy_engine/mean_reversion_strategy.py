"""
Mean Reversion Strategy Module

Implements mean reversion trading strategy using statistical methods.
"""

import pandas as pd
import numpy as np
from typing import List
import logging

from .base_strategy import BaseStrategy, StrategyConfig, Signal, SignalType

logger = logging.getLogger(__name__)


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion trading strategy
    
    Identifies overbought/oversold conditions using:
    - Bollinger Bands
    - Z-score analysis
    - RSI extremes
    - Volume divergences
    """
    
    def __init__(self, config: StrategyConfig):
        """Initialize mean reversion strategy"""
        super().__init__(config)
        
        # Strategy-specific parameters
        self.bb_period = 20
        self.bb_std = 2.0
        self.zscore_period = 20
        self.zscore_threshold = 2.0
        self.rsi_period = 14
        self.rsi_extreme_high = 80
        self.rsi_extreme_low = 20
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate mean reversion indicators"""
        df = data.copy()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Z-score
        df['price_zscore'] = self._calculate_zscore(df['close'], self.zscore_period)
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # Distance from mean
        df['distance_from_mean'] = (df['close'] - df['bb_middle']) / df['bb_middle'] * 100
        
        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df
    
    def _calculate_zscore(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Z-score"""
        mean = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        zscore = (prices - mean) / std
        return zscore
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate mean reversion signals
        
        Buy signals when:
        - Price touches or goes below lower Bollinger Band
        - Z-score below threshold (oversold)
        - RSI in extreme low territory
        
        Sell signals when:
        - Price touches or goes above upper Bollinger Band
        - Z-score above threshold (overbought)
        - RSI in extreme high territory
        """
        if not self.validate_data(data):
            return []
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        signals = []
        
        if len(df) < 2:
            return signals
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        symbol = current.get('symbol', 'UNKNOWN')
        
        # Check for buy signal (oversold)
        if self._check_oversold(current, previous):
            signal_strength = self._calculate_signal_strength(current, 'buy')
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=signal_strength,
                price=current['close'],
                quantity=0,
                timestamp=current.name if hasattr(current, 'name') else pd.Timestamp.now(),
                metadata={
                    'rsi': current['rsi'],
                    'zscore': current['price_zscore'],
                    'bb_position': current['bb_position'],
                    'reason': 'oversold'
                }
            )
            
            signals.append(signal)
            self.performance_metrics['total_signals'] += 1
            logger.info(f"OVERSOLD buy signal for {symbol} at {current['close']}")
        
        # Check for sell signal (overbought)
        elif self._check_overbought(current, previous):
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
                    'zscore': current['price_zscore'],
                    'bb_position': current['bb_position'],
                    'reason': 'overbought'
                }
            )
            
            signals.append(signal)
            self.performance_metrics['total_signals'] += 1
            logger.info(f"OVERBOUGHT sell signal for {symbol} at {current['close']}")
        
        # Check mean reversion (exit signals)
        if symbol in self.positions:
            position = self.positions[symbol]
            
            # Close long if price reverted to mean
            if position['side'] == 'long' and self._check_reversion_to_mean(current):
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG,
                    strength=1.0,
                    price=current['close'],
                    quantity=position['quantity'],
                    timestamp=current.name if hasattr(current, 'name') else pd.Timestamp.now(),
                    metadata={'reason': 'mean_reversion'}
                ))
            
            # Close short if price reverted to mean
            elif position['side'] == 'short' and self._check_reversion_to_mean(current):
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_SHORT,
                    strength=1.0,
                    price=current['close'],
                    quantity=position['quantity'],
                    timestamp=current.name if hasattr(current, 'name') else pd.Timestamp.now(),
                    metadata={'reason': 'mean_reversion'}
                ))
            
            # Standard stop loss / take profit
            elif self.check_stop_loss(symbol, current['close']):
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.CLOSE_LONG if position['side'] == 'long' else SignalType.CLOSE_SHORT,
                    strength=1.0,
                    price=current['close'],
                    quantity=position['quantity'],
                    timestamp=current.name if hasattr(current, 'name') else pd.Timestamp.now(),
                    metadata={'reason': 'stop_loss'}
                ))
        
        return signals
    
    def _check_oversold(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if asset is oversold"""
        # Price below lower Bollinger Band
        below_bb = current['close'] <= current['bb_lower']
        
        # Extreme Z-score
        extreme_zscore = current['price_zscore'] <= -self.zscore_threshold
        
        # RSI oversold
        rsi_oversold = current['rsi'] <= self.rsi_extreme_low
        
        # At least 2 of 3 conditions
        conditions = sum([below_bb, extreme_zscore, rsi_oversold])
        
        return conditions >= 2
    
    def _check_overbought(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if asset is overbought"""
        # Price above upper Bollinger Band
        above_bb = current['close'] >= current['bb_upper']
        
        # Extreme Z-score
        extreme_zscore = current['price_zscore'] >= self.zscore_threshold
        
        # RSI overbought
        rsi_overbought = current['rsi'] >= self.rsi_extreme_high
        
        # At least 2 of 3 conditions
        conditions = sum([above_bb, extreme_zscore, rsi_overbought])
        
        return conditions >= 2
    
    def _check_reversion_to_mean(self, current: pd.Series) -> bool:
        """Check if price has reverted to mean"""
        # Price within middle Bollinger Band range
        near_mean = abs(current['distance_from_mean']) < 1.0
        
        # Z-score normalized
        zscore_normal = abs(current['price_zscore']) < 0.5
        
        # RSI in neutral range
        rsi_neutral = 40 < current['rsi'] < 60
        
        return near_mean or zscore_normal or rsi_neutral
    
    def _calculate_signal_strength(self, current: pd.Series, signal_type: str) -> float:
        """Calculate signal strength"""
        strength = 0.0
        
        if signal_type == 'buy':
            # Stronger signal when further below mean
            bb_strength = max(0, 1 - current['bb_position'])
            zscore_strength = max(0, min(1, abs(current['price_zscore']) / 3))
            rsi_strength = max(0, (self.rsi_extreme_low - current['rsi']) / self.rsi_extreme_low)
        else:  # sell
            # Stronger signal when further above mean
            bb_strength = max(0, current['bb_position'])
            zscore_strength = max(0, min(1, abs(current['price_zscore']) / 3))
            rsi_strength = max(0, (current['rsi'] - self.rsi_extreme_high) / (100 - self.rsi_extreme_high))
        
        # Weighted average
        strength = (
            0.4 * bb_strength +
            0.3 * zscore_strength +
            0.3 * rsi_strength
        )
        
        return max(0.0, min(1.0, strength))
