"""
Volatility Regime Detection Module

Detects market volatility regimes to adjust trading strategies dynamically.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VolatilityRegime(Enum):
    """Volatility regime classifications"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class VolatilityRegimeDetector:
    """
    Detects and classifies market volatility regimes
    
    Uses multiple volatility measures to identify current market conditions
    and adjust trading parameters accordingly.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize volatility regime detector
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Volatility thresholds (percentiles)
        self.low_threshold = self.config.get('low_threshold', 25)
        self.high_threshold = self.config.get('high_threshold', 75)
        self.extreme_threshold = self.config.get('extreme_threshold', 95)
        
        # Lookback periods
        self.short_window = self.config.get('short_window', 20)
        self.long_window = self.config.get('long_window', 100)
        
        self.current_regime = VolatilityRegime.NORMAL
        self.regime_history = []
    
    def calculate_volatility_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate multiple volatility measures
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with volatility metrics
        """
        df = data.copy()
        
        # Historical volatility (standard deviation of returns)
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=self.short_window).std() * np.sqrt(252)
        
        # Parkinson volatility (using high-low range)
        df['parkinson_vol'] = np.sqrt(
            (1 / (4 * np.log(2))) * 
            np.log(df['high'] / df['low']) ** 2
        ).rolling(window=self.short_window).mean() * np.sqrt(252)
        
        # ATR (Average True Range)
        df['tr'] = self._calculate_true_range(df)
        df['atr'] = df['tr'].rolling(window=self.short_window).mean()
        df['atr_pct'] = df['atr'] / df['close'] * 100
        
        # Garman-Klass volatility
        df['gk_vol'] = self._calculate_garman_klass(df, self.short_window)
        
        # Realized volatility (actual price movements)
        df['realized_vol'] = df['returns'].rolling(window=self.short_window).std() * np.sqrt(252)
        
        # Volatility of volatility
        df['vol_of_vol'] = df['volatility'].rolling(window=self.short_window).std()
        
        return df
    
    def _calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr
    
    def _calculate_garman_klass(self, df: pd.DataFrame, window: int) -> pd.Series:
        """Calculate Garman-Klass volatility estimator"""
        log_hl = np.log(df['high'] / df['low'])
        log_co = np.log(df['close'] / df['open'])
        
        gk = 0.5 * log_hl ** 2 - (2 * np.log(2) - 1) * log_co ** 2
        gk_vol = np.sqrt(gk.rolling(window=window).mean()) * np.sqrt(252)
        
        return gk_vol
    
    def detect_regime(self, data: pd.DataFrame) -> Tuple[VolatilityRegime, Dict]:
        """
        Detect current volatility regime
        
        Args:
            data: OHLCV DataFrame with volatility metrics
            
        Returns:
            Tuple of (regime, metrics_dict)
        """
        # Calculate volatility metrics if not present
        if 'volatility' not in data.columns:
            data = self.calculate_volatility_metrics(data)
        
        # Get current and historical volatility
        current_vol = data['volatility'].iloc[-1]
        historical_vol = data['volatility'].dropna()
        
        if len(historical_vol) < self.long_window:
            logger.warning("Insufficient data for regime detection")
            return self.current_regime, {}
        
        # Calculate percentile
        percentile = (historical_vol <= current_vol).mean() * 100
        
        # Determine regime
        if percentile >= self.extreme_threshold:
            regime = VolatilityRegime.EXTREME
        elif percentile >= self.high_threshold:
            regime = VolatilityRegime.HIGH
        elif percentile <= self.low_threshold:
            regime = VolatilityRegime.LOW
        else:
            regime = VolatilityRegime.NORMAL
        
        self.current_regime = regime
        
        # Compile metrics
        metrics = {
            'current_volatility': current_vol,
            'volatility_percentile': percentile,
            'regime': regime.value,
            'atr': data['atr'].iloc[-1],
            'atr_pct': data['atr_pct'].iloc[-1],
            'parkinson_vol': data['parkinson_vol'].iloc[-1],
            'vol_of_vol': data['vol_of_vol'].iloc[-1]
        }
        
        # Store in history
        self.regime_history.append({
            'timestamp': data.index[-1],
            'regime': regime,
            'volatility': current_vol
        })
        
        logger.info(f"Volatility regime: {regime.value} (percentile: {percentile:.1f}%)")
        
        return regime, metrics
    
    def get_regime_adjustments(self, regime: VolatilityRegime = None) -> Dict:
        """
        Get recommended parameter adjustments for current regime
        
        Args:
            regime: Volatility regime (uses current if not provided)
            
        Returns:
            Dict with adjustment factors
        """
        if regime is None:
            regime = self.current_regime
        
        adjustments = {
            VolatilityRegime.LOW: {
                'position_size_multiplier': 1.3,
                'stop_loss_multiplier': 0.8,
                'take_profit_multiplier': 1.2,
                'leverage_multiplier': 1.2,
                'trade_frequency': 'increase'
            },
            VolatilityRegime.NORMAL: {
                'position_size_multiplier': 1.0,
                'stop_loss_multiplier': 1.0,
                'take_profit_multiplier': 1.0,
                'leverage_multiplier': 1.0,
                'trade_frequency': 'normal'
            },
            VolatilityRegime.HIGH: {
                'position_size_multiplier': 0.7,
                'stop_loss_multiplier': 1.3,
                'take_profit_multiplier': 0.8,
                'leverage_multiplier': 0.7,
                'trade_frequency': 'decrease'
            },
            VolatilityRegime.EXTREME: {
                'position_size_multiplier': 0.3,
                'stop_loss_multiplier': 2.0,
                'take_profit_multiplier': 0.5,
                'leverage_multiplier': 0.3,
                'trade_frequency': 'minimal'
            }
        }
        
        return adjustments.get(regime, adjustments[VolatilityRegime.NORMAL])
    
    def should_halt_trading(self, regime: VolatilityRegime = None) -> bool:
        """
        Determine if trading should be halted due to extreme volatility
        
        Args:
            regime: Volatility regime (uses current if not provided)
            
        Returns:
            True if trading should be halted
        """
        if regime is None:
            regime = self.current_regime
        
        return regime == VolatilityRegime.EXTREME
    
    def get_regime_statistics(self) -> Dict:
        """Get statistics about regime changes"""
        if not self.regime_history:
            return {}
        
        df = pd.DataFrame(self.regime_history)
        
        regime_counts = df['regime'].value_counts()
        regime_durations = df.groupby('regime').size()
        
        return {
            'current_regime': self.current_regime.value,
            'regime_distribution': regime_counts.to_dict(),
            'total_observations': len(df),
            'regime_changes': (df['regime'] != df['regime'].shift()).sum()
        }
