"""
WebSocket Connector Module

Provides real-time market data streaming from multiple exchanges.
Supports Binance, Bybit, and OKX with automatic reconnection.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Optional
import websockets
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseExchangeConnector(ABC):
    """Base class for exchange WebSocket connectors"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        """
        Initialize exchange connector
        
        Args:
            symbols: List of trading symbols to subscribe to
            callback: Function to call with market data updates
        """
        self.symbols = symbols
        self.callback = callback
        self.ws = None
        self.running = False
        
    @abstractmethod
    async def connect(self):
        """Establish WebSocket connection"""
        pass
    
    @abstractmethod
    async def subscribe(self):
        """Subscribe to market data streams"""
        pass
    
    @abstractmethod
    def parse_message(self, message: dict) -> Optional[Dict]:
        """Parse exchange-specific message format to normalized format"""
        pass
    
    async def run(self):
        """Main event loop with auto-reconnection"""
        self.running = True
        retry_delay = 1
        max_retry_delay = 60
        
        while self.running:
            try:
                await self.connect()
                await self.subscribe()
                
                # Reset retry delay on successful connection
                retry_delay = 1
                
                async for message in self.ws:
                    try:
                        data = json.loads(message)
                        parsed_data = self.parse_message(data)
                        
                        if parsed_data:
                            await self.callback(parsed_data)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        
            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
            
            if self.running:
                logger.info(f"Reconnecting in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
    
    async def stop(self):
        """Stop the WebSocket connection"""
        self.running = False
        if self.ws:
            await self.ws.close()


class BinanceConnector(BaseExchangeConnector):
    """Binance WebSocket connector"""
    
    WS_URL = "wss://stream.binance.com:9443/ws"
    
    async def connect(self):
        """Connect to Binance WebSocket"""
        # Build stream names
        streams = [f"{symbol.lower()}@trade" for symbol in self.symbols]
        streams += [f"{symbol.lower()}@depth20@100ms" for symbol in self.symbols]
        
        url = f"{self.WS_URL}/{'/'.join(streams)}"
        self.ws = await websockets.connect(url)
        logger.info(f"Connected to Binance: {', '.join(self.symbols)}")
    
    async def subscribe(self):
        """Binance doesn't require explicit subscription for combined streams"""
        pass
    
    def parse_message(self, message: dict) -> Optional[Dict]:
        """Parse Binance message to normalized format"""
        try:
            if 'e' not in message:
                return None
            
            event_type = message['e']
            
            if event_type == 'trade':
                return {
                    'exchange': 'binance',
                    'type': 'trade',
                    'symbol': message['s'],
                    'price': float(message['p']),
                    'quantity': float(message['q']),
                    'timestamp': message['T'],
                    'is_buyer_maker': message['m']
                }
            
            elif event_type == 'depthUpdate':
                return {
                    'exchange': 'binance',
                    'type': 'orderbook',
                    'symbol': message['s'],
                    'bids': [[float(p), float(q)] for p, q in message['b']],
                    'asks': [[float(p), float(q)] for p, q in message['a']],
                    'timestamp': message['E']
                }
                
        except Exception as e:
            logger.error(f"Failed to parse Binance message: {e}")
            return None


class BybitConnector(BaseExchangeConnector):
    """Bybit WebSocket connector"""
    
    WS_URL = "wss://stream.bybit.com/v5/public/linear"
    
    async def connect(self):
        """Connect to Bybit WebSocket"""
        self.ws = await websockets.connect(self.WS_URL)
        logger.info(f"Connected to Bybit: {', '.join(self.symbols)}")
    
    async def subscribe(self):
        """Subscribe to Bybit channels"""
        subscribe_msg = {
            "op": "subscribe",
            "args": [f"publicTrade.{symbol}" for symbol in self.symbols] +
                    [f"orderbook.50.{symbol}" for symbol in self.symbols]
        }
        await self.ws.send(json.dumps(subscribe_msg))
    
    def parse_message(self, message: dict) -> Optional[Dict]:
        """Parse Bybit message to normalized format"""
        try:
            if 'topic' not in message:
                return None
            
            topic = message['topic']
            
            if topic.startswith('publicTrade'):
                data = message['data'][0] if isinstance(message['data'], list) else message['data']
                return {
                    'exchange': 'bybit',
                    'type': 'trade',
                    'symbol': data['s'],
                    'price': float(data['p']),
                    'quantity': float(data['v']),
                    'timestamp': data['T'],
                    'is_buyer_maker': data['S'] == 'Sell'
                }
            
            elif topic.startswith('orderbook'):
                data = message['data']
                return {
                    'exchange': 'bybit',
                    'type': 'orderbook',
                    'symbol': data['s'],
                    'bids': [[float(p), float(q)] for p, q in data['b']],
                    'asks': [[float(p), float(q)] for p, q in data['a']],
                    'timestamp': data['t']
                }
                
        except Exception as e:
            logger.error(f"Failed to parse Bybit message: {e}")
            return None


class OKXConnector(BaseExchangeConnector):
    """OKX WebSocket connector"""
    
    WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
    
    async def connect(self):
        """Connect to OKX WebSocket"""
        self.ws = await websockets.connect(self.WS_URL)
        logger.info(f"Connected to OKX: {', '.join(self.symbols)}")
    
    async def subscribe(self):
        """Subscribe to OKX channels"""
        subscribe_msg = {
            "op": "subscribe",
            "args": [{"channel": "trades", "instId": symbol} for symbol in self.symbols] +
                    [{"channel": "books", "instId": symbol} for symbol in self.symbols]
        }
        await self.ws.send(json.dumps(subscribe_msg))
    
    def parse_message(self, message: dict) -> Optional[Dict]:
        """Parse OKX message to normalized format"""
        try:
            if 'data' not in message:
                return None
            
            arg = message.get('arg', {})
            channel = arg.get('channel')
            
            if channel == 'trades':
                data = message['data'][0]
                return {
                    'exchange': 'okx',
                    'type': 'trade',
                    'symbol': arg['instId'],
                    'price': float(data['px']),
                    'quantity': float(data['sz']),
                    'timestamp': int(data['ts']),
                    'is_buyer_maker': data['side'] == 'sell'
                }
            
            elif channel == 'books':
                data = message['data'][0]
                return {
                    'exchange': 'okx',
                    'type': 'orderbook',
                    'symbol': arg['instId'],
                    'bids': [[float(p), float(q)] for p, q, _, _ in data['bids']],
                    'asks': [[float(p), float(q)] for p, q, _, _ in data['asks']],
                    'timestamp': int(data['ts'])
                }
                
        except Exception as e:
            logger.error(f"Failed to parse OKX message: {e}")
            return None


class WebSocketConnector:
    """
    Unified WebSocket connector manager
    
    Manages connections to multiple exchanges and provides
    a single normalized data feed.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize WebSocket connector
        
        Args:
            config: Configuration dict with exchange settings
        """
        self.config = config
        self.connectors: List[BaseExchangeConnector] = []
        self.data_callbacks: List[Callable] = []
        
    def add_callback(self, callback: Callable):
        """Add a callback function for market data updates"""
        self.data_callbacks.append(callback)
    
    async def _handle_data(self, data: Dict):
        """Internal data handler that broadcasts to all callbacks"""
        for callback in self.data_callbacks:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    async def connect_all(self):
        """Connect to all configured exchanges"""
        tasks = []
        
        for exchange_name, exchange_config in self.config.items():
            if not exchange_config.get('enabled', False):
                continue
            
            symbols = exchange_config.get('symbols', [])
            
            if exchange_name == 'binance':
                connector = BinanceConnector(symbols, self._handle_data)
            elif exchange_name == 'bybit':
                connector = BybitConnector(symbols, self._handle_data)
            elif exchange_name == 'okx':
                connector = OKXConnector(symbols, self._handle_data)
            else:
                logger.warning(f"Unknown exchange: {exchange_name}")
                continue
            
            self.connectors.append(connector)
            tasks.append(connector.run())
        
        logger.info(f"Starting {len(self.connectors)} exchange connections")
        await asyncio.gather(*tasks)
    
    async def stop_all(self):
        """Stop all exchange connections"""
        tasks = [connector.stop() for connector in self.connectors]
        await asyncio.gather(*tasks)
        logger.info("All connections stopped")
