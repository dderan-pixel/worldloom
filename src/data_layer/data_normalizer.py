"""
Data Normalizer Module

Normalizes market data from different exchanges into a unified format.
Handles data cleaning, validation, and transformation.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Market data normalizer
    
    Converts exchange-specific data formats into a unified structure
    for consistent processing across the trading system.
    """
    
    # Standard column names
    OHLCV_COLUMNS = ['open', 'high', 'low', 'close', 'volume']
    TRADE_COLUMNS = ['price', 'quantity', 'side', 'timestamp']
    ORDERBOOK_COLUMNS = ['bids', 'asks', 'timestamp']
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize data normalizer
        
        Args:
            config: Optional configuration for normalization rules
        """
        self.config = config or {}
        self.exchange_mappings = self._load_exchange_mappings()
    
    def _load_exchange_mappings(self) -> Dict:
        """Load exchange-specific field mappings"""
        return {
            'binance': {
                'symbol': 's',
                'price': 'p',
                'quantity': 'q',
                'side': 'm'  # is_buyer_maker
            },
            'bybit': {
                'symbol': 's',
                'price': 'p',
                'quantity': 'v',
                'side': 'S'
            },
            'okx': {
                'symbol': 'instId',
                'price': 'px',
                'quantity': 'sz',
                'side': 'side'
            }
        }
    
    def normalize_trade(self, trade_data: Dict) -> Dict:
        """
        Normalize trade data to standard format
        
        Args:
            trade_data: Raw trade data from exchange
            
        Returns:
            Normalized trade dict
        """
        exchange = trade_data.get('exchange', 'unknown')
        
        try:
            normalized = {
                'exchange': exchange,
                'symbol': self._normalize_symbol(trade_data['symbol'], exchange),
                'price': float(trade_data['price']),
                'quantity': float(trade_data['quantity']),
                'side': 'buy' if not trade_data.get('is_buyer_maker', False) else 'sell',
                'timestamp': pd.to_datetime(trade_data['timestamp'], unit='ms')
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize trade data: {e}")
            return {}
    
    def normalize_orderbook(self, orderbook_data: Dict) -> Dict:
        """
        Normalize order book data to standard format
        
        Args:
            orderbook_data: Raw orderbook data from exchange
            
        Returns:
            Normalized orderbook dict
        """
        exchange = orderbook_data.get('exchange', 'unknown')
        
        try:
            # Sort bids descending, asks ascending
            bids = sorted(orderbook_data['bids'], key=lambda x: x[0], reverse=True)
            asks = sorted(orderbook_data['asks'], key=lambda x: x[0])
            
            normalized = {
                'exchange': exchange,
                'symbol': self._normalize_symbol(orderbook_data['symbol'], exchange),
                'bids': bids,
                'asks': asks,
                'best_bid': bids[0][0] if bids else 0,
                'best_ask': asks[0][0] if asks else 0,
                'mid_price': (bids[0][0] + asks[0][0]) / 2 if bids and asks else 0,
                'spread': asks[0][0] - bids[0][0] if bids and asks else 0,
                'timestamp': pd.to_datetime(orderbook_data['timestamp'], unit='ms')
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize orderbook data: {e}")
            return {}
    
    def normalize_ohlcv(self, ohlcv_df: pd.DataFrame, exchange: str) -> pd.DataFrame:
        """
        Normalize OHLCV DataFrame
        
        Args:
            ohlcv_df: Raw OHLCV DataFrame
            exchange: Exchange identifier
            
        Returns:
            Normalized DataFrame
        """
        try:
            df = ohlcv_df.copy()
            
            # Ensure required columns exist
            for col in self.OHLCV_COLUMNS:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # Convert to float
            for col in self.OHLCV_COLUMNS:
                df[col] = df[col].astype(float)
            
            # Remove invalid data
            df = df[df['high'] >= df['low']]
            df = df[df['close'] > 0]
            df = df[df['volume'] >= 0]
            
            # Add derived columns
            df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
            df['vwap'] = (df['typical_price'] * df['volume']).cumsum() / df['volume'].cumsum()
            
            # Add exchange info
            df['exchange'] = exchange
            
            logger.debug(f"Normalized {len(df)} OHLCV candles")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to normalize OHLCV data: {e}")
            raise
    
    def _normalize_symbol(self, symbol: str, exchange: str) -> str:
        """
        Normalize symbol format across exchanges
        
        Args:
            symbol: Raw symbol string
            exchange: Exchange identifier
            
        Returns:
            Normalized symbol (e.g., 'BTC/USDT')
        """
        # Remove common suffixes
        symbol = symbol.replace('USDT-PERP', '/USDT')
        symbol = symbol.replace('PERP', '')
        
        # Ensure forward slash format
        if '/' not in symbol and 'USDT' in symbol:
            symbol = symbol.replace('USDT', '/USDT')
        elif '/' not in symbol and 'USD' in symbol:
            symbol = symbol.replace('USD', '/USD')
        
        return symbol.upper()
    
    def aggregate_trades(self, trades_df: pd.DataFrame, interval: str = '1min') -> pd.DataFrame:
        """
        Aggregate trade data into OHLCV format
        
        Args:
            trades_df: DataFrame with trade data
            interval: Aggregation interval (e.g., '1min', '5min', '1H')
            
        Returns:
            Aggregated OHLCV DataFrame
        """
        try:
            # Ensure timestamp index
            if not isinstance(trades_df.index, pd.DatetimeIndex):
                trades_df = trades_df.set_index('timestamp')
            
            # Resample and aggregate
            ohlcv = pd.DataFrame()
            ohlcv['open'] = trades_df['price'].resample(interval).first()
            ohlcv['high'] = trades_df['price'].resample(interval).max()
            ohlcv['low'] = trades_df['price'].resample(interval).min()
            ohlcv['close'] = trades_df['price'].resample(interval).last()
            ohlcv['volume'] = trades_df['quantity'].resample(interval).sum()
            
            # Forward fill missing values
            ohlcv.fillna(method='ffill', inplace=True)
            
            # Remove rows with no data
            ohlcv.dropna(inplace=True)
            
            logger.debug(f"Aggregated {len(trades_df)} trades into {len(ohlcv)} candles")
            
            return ohlcv
            
        except Exception as e:
            logger.error(f"Failed to aggregate trades: {e}")
            raise
    
    def calculate_features(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical features from OHLCV data
        
        Args:
            ohlcv_df: OHLCV DataFrame
            
        Returns:
            DataFrame with additional feature columns
        """
        try:
            df = ohlcv_df.copy()
            
            # Price-based features
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            df['hl_ratio'] = (df['high'] - df['low']) / df['close']
            df['co_ratio'] = (df['close'] - df['open']) / df['open']
            
            # Volume-based features
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_std'] = df['volume'].rolling(window=20).std()
            df['volume_zscore'] = (df['volume'] - df['volume_ma']) / df['volume_std']
            
            # Volatility features
            df['volatility_20'] = df['returns'].rolling(window=20).std()
            df['volatility_60'] = df['returns'].rolling(window=60).std()
            
            # Trend features
            df['ma_5'] = df['close'].rolling(window=5).mean()
            df['ma_20'] = df['close'].rolling(window=20).mean()
            df['ma_50'] = df['close'].rolling(window=50).mean()
            df['trend_strength'] = (df['close'] - df['ma_20']) / df['ma_20']
            
            logger.debug(f"Calculated features for {len(df)} candles")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to calculate features: {e}")
            raise
    
    def clean_data(self, df: pd.DataFrame, remove_outliers: bool = True) -> pd.DataFrame:
        """
        Clean and validate data
        
        Args:
            df: Input DataFrame
            remove_outliers: Whether to remove statistical outliers
            
        Returns:
            Cleaned DataFrame
        """
        try:
            cleaned = df.copy()
            
            # Remove duplicates
            initial_len = len(cleaned)
            cleaned = cleaned[~cleaned.index.duplicated(keep='first')]
            
            if len(cleaned) < initial_len:
                logger.info(f"Removed {initial_len - len(cleaned)} duplicate rows")
            
            # Remove NaN values
            cleaned.dropna(subset=self.OHLCV_COLUMNS, inplace=True)
            
            # Remove outliers using IQR method
            if remove_outliers and 'close' in cleaned.columns:
                Q1 = cleaned['close'].quantile(0.25)
                Q3 = cleaned['close'].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
                
                outliers = (cleaned['close'] < lower_bound) | (cleaned['close'] > upper_bound)
                if outliers.sum() > 0:
                    logger.warning(f"Removed {outliers.sum()} outliers")
                    cleaned = cleaned[~outliers]
            
            logger.info(f"Cleaned data: {len(cleaned)} rows remaining")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to clean data: {e}")
            raise
