"""
Order Router Module

Smart order routing across multiple exchanges with failover support.
"""

import logging
from typing import Dict, List, Optional, Tuple
import asyncio
import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)


class OrderRouter:
    """
    Smart order router
    
    Routes orders to optimal exchanges based on:
    - Liquidity
    - Fees
    - Slippage estimates
    - Exchange health
    """
    
    def __init__(self, config: Dict):
        """
        Initialize order router
        
        Args:
            config: Router configuration with exchange settings
        """
        self.config = config
        self.exchanges = {}
        self.exchange_priorities = config.get('exchange_priorities', [])
        
        # Initialize exchanges
        for exchange_id, exchange_config in config.get('exchanges', {}).items():
            try:
                exchange_class = getattr(ccxt, exchange_id)
                self.exchanges[exchange_id] = exchange_class({
                    'apiKey': exchange_config.get('api_key'),
                    'secret': exchange_config.get('api_secret'),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': exchange_config.get('market_type', 'spot')
                    }
                })
                logger.info(f"Initialized exchange: {exchange_id}")
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_id}: {e}")
        
        # Slippage tolerance
        self.max_slippage = config.get('max_slippage', 0.005)  # 0.5%
    
    async def route_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = 'limit',
        price: Optional[float] = None,
        preferred_exchange: Optional[str] = None
    ) -> Dict:
        """
        Route order to best exchange
        
        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            quantity: Order quantity
            order_type: Order type (market/limit)
            price: Limit price (if limit order)
            preferred_exchange: Preferred exchange (if any)
            
        Returns:
            Order result dict
        """
        # Get available exchanges for symbol
        available_exchanges = await self._get_available_exchanges(symbol)
        
        if not available_exchanges:
            raise ValueError(f"No exchanges available for {symbol}")
        
        # Use preferred exchange if specified and available
        if preferred_exchange and preferred_exchange in available_exchanges:
            target_exchange = preferred_exchange
        else:
            # Select best exchange
            target_exchange = await self._select_best_exchange(
                symbol, side, quantity, available_exchanges
            )
        
        # Execute order with retry logic
        try:
            result = await self._execute_order(
                target_exchange,
                symbol,
                side,
                quantity,
                order_type,
                price
            )
            
            logger.info(
                f"Order executed on {target_exchange}: {side} {quantity} {symbol}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Order execution failed on {target_exchange}: {e}")
            
            # Try failover exchanges
            for fallback_exchange in available_exchanges:
                if fallback_exchange == target_exchange:
                    continue
                
                try:
                    logger.info(f"Attempting failover to {fallback_exchange}")
                    result = await self._execute_order(
                        fallback_exchange,
                        symbol,
                        side,
                        quantity,
                        order_type,
                        price
                    )
                    
                    logger.info(f"Failover successful on {fallback_exchange}")
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Failover failed on {fallback_exchange}: {fallback_error}")
            
            # All exchanges failed
            raise Exception("Order execution failed on all exchanges")
    
    async def _get_available_exchanges(self, symbol: str) -> List[str]:
        """Get exchanges that support the symbol"""
        available = []
        
        for exchange_id, exchange in self.exchanges.items():
            try:
                await exchange.load_markets()
                if symbol in exchange.markets:
                    available.append(exchange_id)
            except Exception as e:
                logger.error(f"Error checking {exchange_id}: {e}")
        
        return available
    
    async def _select_best_exchange(
        self,
        symbol: str,
        side: str,
        quantity: float,
        available_exchanges: List[str]
    ) -> str:
        """
        Select best exchange based on liquidity and fees
        
        Returns:
            Exchange ID
        """
        exchange_scores = {}
        
        for exchange_id in available_exchanges:
            try:
                score = await self._calculate_exchange_score(
                    exchange_id, symbol, side, quantity
                )
                exchange_scores[exchange_id] = score
            except Exception as e:
                logger.error(f"Error scoring {exchange_id}: {e}")
                exchange_scores[exchange_id] = 0
        
        # Select exchange with highest score
        best_exchange = max(exchange_scores, key=exchange_scores.get)
        
        logger.debug(f"Exchange scores for {symbol}: {exchange_scores}")
        logger.info(f"Selected exchange: {best_exchange}")
        
        return best_exchange
    
    async def _calculate_exchange_score(
        self,
        exchange_id: str,
        symbol: str,
        side: str,
        quantity: float
    ) -> float:
        """Calculate exchange suitability score"""
        exchange = self.exchanges[exchange_id]
        score = 0.0
        
        try:
            # Get orderbook for liquidity check
            orderbook = await exchange.fetch_order_book(symbol, limit=20)
            
            # Check liquidity
            relevant_side = orderbook['bids'] if side == 'buy' else orderbook['asks']
            available_liquidity = sum(level[1] for level in relevant_side)
            
            if available_liquidity >= quantity:
                score += 50  # Good liquidity
            else:
                score += (available_liquidity / quantity) * 50
            
            # Check fees
            market = exchange.markets[symbol]
            fee = market.get('taker', 0.001)  # Default 0.1%
            score += (1 - fee) * 30  # Lower fees = higher score
            
            # Priority bonus
            if exchange_id in self.exchange_priorities:
                priority_index = self.exchange_priorities.index(exchange_id)
                score += (10 - priority_index) * 2
            
        except Exception as e:
            logger.error(f"Error calculating score for {exchange_id}: {e}")
        
        return score
    
    async def _execute_order(
        self,
        exchange_id: str,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        price: Optional[float]
    ) -> Dict:
        """Execute order on specified exchange"""
        exchange = self.exchanges[exchange_id]
        
        # Prepare order parameters
        params = {}
        
        try:
            if order_type == 'market':
                order = await exchange.create_market_order(
                    symbol, side, quantity, params
                )
            elif order_type == 'limit':
                if price is None:
                    raise ValueError("Price required for limit orders")
                order = await exchange.create_limit_order(
                    symbol, side, quantity, price, params
                )
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            # Add exchange info to result
            order['exchange'] = exchange_id
            
            return order
            
        except Exception as e:
            logger.error(f"Order execution error on {exchange_id}: {e}")
            raise
    
    async def cancel_order(
        self,
        order_id: str,
        symbol: str,
        exchange_id: str
    ) -> Dict:
        """Cancel an order"""
        if exchange_id not in self.exchanges:
            raise ValueError(f"Unknown exchange: {exchange_id}")
        
        exchange = self.exchanges[exchange_id]
        
        try:
            result = await exchange.cancel_order(order_id, symbol)
            logger.info(f"Cancelled order {order_id} on {exchange_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    async def get_order_status(
        self,
        order_id: str,
        symbol: str,
        exchange_id: str
    ) -> Dict:
        """Get order status"""
        if exchange_id not in self.exchanges:
            raise ValueError(f"Unknown exchange: {exchange_id}")
        
        exchange = self.exchanges[exchange_id]
        
        try:
            order = await exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Failed to fetch order {order_id}: {e}")
            raise
    
    async def close_all(self):
        """Close all exchange connections"""
        for exchange_id, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed connection to {exchange_id}")
            except Exception as e:
                logger.error(f"Error closing {exchange_id}: {e}")
