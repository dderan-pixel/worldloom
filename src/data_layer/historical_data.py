"""
Historical Data Fetcher Module

Fetches historical market data from exchanges for backtesting and analysis.
Supports multiple timeframes and data types.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import ccxt
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseHistoricalFetcher(ABC):
    """Base class for historical data fetchers"""
    
    def __init__(self, exchange_id: str, api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None):
        """
        Initialize historical data fetcher
        
        Args:
            exchange_id: Exchange identifier (binance, bybit, okx)
            api_key: Optional API key for private endpoints
            api_secret: Optional API secret
        """
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        
    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, 
                          start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch OHLCV data"""
        pass


class HistoricalDataFetcher:
    """
    Multi-exchange historical data fetcher
    
    Fetches and normalizes historical OHLCV data from multiple exchanges
    with proper rate limiting and error handling.
    """
    
    SUPPORTED_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
    
    def __init__(self, exchange_configs: Dict):
        """
        Initialize historical data fetcher
        
        Args:
            exchange_configs: Dict of exchange configurations
        """
        self.exchanges = {}
        
        for exchange_id, config in exchange_configs.items():
            try:
                exchange_class = getattr(ccxt, exchange_id)
                self.exchanges[exchange_id] = exchange_class({
                    'apiKey': config.get('api_key'),
                    'secret': config.get('api_secret'),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future' if config.get('use_futures', False) else 'spot'
                    }
                })
                logger.info(f"Initialized {exchange_id} exchange")
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_id}: {e}")
    
    async def fetch_ohlcv(
        self, 
        exchange_id: str,
        symbol: str, 
        timeframe: str = '1h',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a symbol
        
        Args:
            exchange_id: Exchange to fetch from
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Candlestick timeframe
            start_date: Start date for historical data
            end_date: End date for historical data
            limit: Max number of candles per request
            
        Returns:
            DataFrame with OHLCV data
        """
        if exchange_id not in self.exchanges:
            raise ValueError(f"Exchange {exchange_id} not configured")
        
        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            raise ValueError(f"Timeframe {timeframe} not supported")
        
        exchange = self.exchanges[exchange_id]
        
        # Set default dates
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # Convert to milliseconds
        since = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        all_data = []
        
        try:
            while since < end_ts:
                ohlcv = await exchange.fetch_ohlcv(
                    symbol, 
                    timeframe, 
                    since=since, 
                    limit=limit
                )
                
                if not ohlcv:
                    break
                
                all_data.extend(ohlcv)
                
                # Update since to the last candle's timestamp
                since = ohlcv[-1][0] + 1
                
                # Rate limiting
                await exchange.sleep(exchange.rateLimit)
            
            # Convert to DataFrame
            df = pd.DataFrame(
                all_data, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Add exchange info
            df['exchange'] = exchange_id
            df['symbol'] = symbol
            
            logger.info(
                f"Fetched {len(df)} candles for {symbol} from {exchange_id}"
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            raise
    
    async def fetch_multiple_symbols(
        self,
        exchange_id: str,
        symbols: List[str],
        timeframe: str = '1h',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for multiple symbols
        
        Args:
            exchange_id: Exchange to fetch from
            symbols: List of trading symbols
            timeframe: Candlestick timeframe
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            Dict mapping symbols to DataFrames
        """
        results = {}
        
        for symbol in symbols:
            try:
                df = await self.fetch_ohlcv(
                    exchange_id, symbol, timeframe, start_date, end_date
                )
                results[symbol] = df
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
        
        return results
    
    async def fetch_trades(
        self,
        exchange_id: str,
        symbol: str,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch recent trades
        
        Args:
            exchange_id: Exchange to fetch from
            symbol: Trading symbol
            since: Fetch trades since this datetime
            limit: Max number of trades
            
        Returns:
            DataFrame with trade data
        """
        if exchange_id not in self.exchanges:
            raise ValueError(f"Exchange {exchange_id} not configured")
        
        exchange = self.exchanges[exchange_id]
        
        since_ts = int(since.timestamp() * 1000) if since else None
        
        try:
            trades = await exchange.fetch_trades(symbol, since=since_ts, limit=limit)
            
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Fetched {len(df)} trades for {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            raise
    
    async def fetch_order_book(
        self,
        exchange_id: str,
        symbol: str,
        limit: int = 100
    ) -> Dict:
        """
        Fetch current order book
        
        Args:
            exchange_id: Exchange to fetch from
            symbol: Trading symbol
            limit: Depth of order book
            
        Returns:
            Dict with bids and asks
        """
        if exchange_id not in self.exchanges:
            raise ValueError(f"Exchange {exchange_id} not configured")
        
        exchange = self.exchanges[exchange_id]
        
        try:
            orderbook = await exchange.fetch_order_book(symbol, limit=limit)
            
            return {
                'exchange': exchange_id,
                'symbol': symbol,
                'bids': orderbook['bids'],
                'asks': orderbook['asks'],
                'timestamp': datetime.fromtimestamp(orderbook['timestamp'] / 1000)
            }
            
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            raise
    
    def get_available_symbols(self, exchange_id: str) -> List[str]:
        """
        Get list of available trading symbols
        
        Args:
            exchange_id: Exchange identifier
            
        Returns:
            List of symbol strings
        """
        if exchange_id not in self.exchanges:
            raise ValueError(f"Exchange {exchange_id} not configured")
        
        exchange = self.exchanges[exchange_id]
        
        try:
            markets = exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            logger.error(f"Error loading markets: {e}")
            return []
