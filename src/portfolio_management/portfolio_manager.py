"""
Portfolio Manager Module

Manages portfolio state, positions, and real-time valuation.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Portfolio management system
    
    Tracks:
    - Cash balance
    - Open positions
    - Portfolio valuation
    - Asset allocation
    """
    
    def __init__(self, config: Dict):
        """
        Initialize portfolio manager
        
        Args:
            config: Portfolio configuration
        """
        self.config = config
        
        # Initial state
        self.initial_capital = config.get('initial_capital', 100000)
        self.cash_balance = self.initial_capital
        self.cash_reserve_pct = config.get('cash_reserve_pct', 0.1)
        
        # Positions: {symbol: position_dict}
        self.positions: Dict[str, Dict] = {}
        
        # Historical snapshots
        self.snapshots: List[Dict] = []
        
        # Metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        logger.info(f"Portfolio initialized with ${self.initial_capital:,.2f}")
    
    def add_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        exchange: str,
        strategy: str,
        timestamp: datetime = None
    ):
        """
        Add or update a position
        
        Args:
            symbol: Trading symbol
            side: Position side (long/short)
            quantity: Position quantity
            entry_price: Entry price
            exchange: Exchange name
            strategy: Strategy name
            timestamp: Position timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        position_value = quantity * entry_price
        
        # Check if we have enough cash
        required_cash = position_value
        if required_cash > self.cash_balance:
            logger.warning(
                f"Insufficient cash for position: ${required_cash:,.2f} > ${self.cash_balance:,.2f}"
            )
            return False
        
        # Deduct cash
        self.cash_balance -= required_cash
        
        # Add position
        if symbol in self.positions:
            # Update existing position
            existing = self.positions[symbol]
            total_quantity = existing['quantity'] + quantity
            avg_price = (
                (existing['entry_price'] * existing['quantity']) +
                (entry_price * quantity)
            ) / total_quantity
            
            self.positions[symbol] = {
                'side': side,
                'quantity': total_quantity,
                'entry_price': avg_price,
                'current_price': entry_price,
                'exchange': exchange,
                'strategy': strategy,
                'opened_at': existing['opened_at'],
                'updated_at': timestamp
            }
        else:
            # New position
            self.positions[symbol] = {
                'side': side,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': entry_price,
                'exchange': exchange,
                'strategy': strategy,
                'opened_at': timestamp,
                'updated_at': timestamp
            }
        
        logger.info(
            f"Position added: {side} {quantity} {symbol} @ ${entry_price:.2f}"
        )
        
        return True
    
    def close_position(
        self,
        symbol: str,
        exit_price: float,
        timestamp: datetime = None
    ) -> Optional[Dict]:
        """
        Close a position
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            timestamp: Close timestamp
            
        Returns:
            Position result dict with P&L
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return None
        
        position = self.positions.pop(symbol)
        
        # Calculate P&L
        quantity = position['quantity']
        entry_price = position['entry_price']
        
        if position['side'] == 'long':
            pnl = (exit_price - entry_price) * quantity
        else:  # short
            pnl = (entry_price - exit_price) * quantity
        
        pnl_pct = pnl / (entry_price * quantity)
        
        # Return cash
        position_value = quantity * exit_price
        self.cash_balance += position_value
        
        # Update metrics
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        result = {
            'symbol': symbol,
            'side': position['side'],
            'quantity': quantity,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'duration': (timestamp - position['opened_at']).total_seconds(),
            'strategy': position['strategy'],
            'exchange': position['exchange'],
            'closed_at': timestamp
        }
        
        logger.info(
            f"Position closed: {symbol} P&L: ${pnl:,.2f} ({pnl_pct:.2%})"
        )
        
        return result
    
    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for positions
        
        Args:
            prices: Dict mapping symbols to current prices
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol]['current_price'] = price
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        positions_value = sum(
            pos['quantity'] * pos['current_price']
            for pos in self.positions.values()
        )
        
        return self.cash_balance + positions_value
    
    def get_positions_value(self) -> float:
        """Calculate total value of open positions"""
        return sum(
            pos['quantity'] * pos['current_price']
            for pos in self.positions.values()
        )
    
    def get_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L"""
        total_pnl = 0.0
        
        for position in self.positions.values():
            quantity = position['quantity']
            entry_price = position['entry_price']
            current_price = position['current_price']
            
            if position['side'] == 'long':
                pnl = (current_price - entry_price) * quantity
            else:
                pnl = (entry_price - current_price) * quantity
            
            total_pnl += pnl
        
        return total_pnl
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        portfolio_value = self.get_portfolio_value()
        positions_value = self.get_positions_value()
        unrealized_pnl = self.get_unrealized_pnl()
        
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        
        win_rate = (
            self.winning_trades / self.total_trades
            if self.total_trades > 0 else 0
        )
        
        return {
            'timestamp': datetime.now(),
            'total_value': portfolio_value,
            'cash_balance': self.cash_balance,
            'positions_value': positions_value,
            'unrealized_pnl': unrealized_pnl,
            'total_return': total_return,
            'total_return_pct': total_return,
            'num_positions': len(self.positions),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'cash_utilization': 1 - (self.cash_balance / portfolio_value) if portfolio_value > 0 else 0
        }
    
    def get_position_summary(self) -> List[Dict]:
        """Get summary of all positions"""
        summaries = []
        
        for symbol, position in self.positions.items():
            quantity = position['quantity']
            entry_price = position['entry_price']
            current_price = position['current_price']
            
            if position['side'] == 'long':
                pnl = (current_price - entry_price) * quantity
            else:
                pnl = (entry_price - current_price) * quantity
            
            pnl_pct = pnl / (entry_price * quantity)
            position_value = quantity * current_price
            
            summaries.append({
                'symbol': symbol,
                'side': position['side'],
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'position_value': position_value,
                'unrealized_pnl': pnl,
                'unrealized_pnl_pct': pnl_pct,
                'strategy': position['strategy'],
                'exchange': position['exchange'],
                'duration': (datetime.now() - position['opened_at']).total_seconds()
            })
        
        return summaries
    
    def take_snapshot(self):
        """Take a portfolio snapshot for history"""
        snapshot = self.get_portfolio_summary()
        self.snapshots.append(snapshot)
        
        # Keep last 10000 snapshots
        if len(self.snapshots) > 10000:
            self.snapshots = self.snapshots[-10000:]
    
    def get_allocation(self) -> Dict[str, float]:
        """Get asset allocation percentages"""
        portfolio_value = self.get_portfolio_value()
        
        if portfolio_value == 0:
            return {}
        
        allocation = {}
        
        # Cash allocation
        allocation['CASH'] = self.cash_balance / portfolio_value
        
        # Position allocations
        for symbol, position in self.positions.items():
            position_value = position['quantity'] * position['current_price']
            allocation[symbol] = position_value / portfolio_value
        
        return allocation
    
    def check_cash_reserve(self) -> bool:
        """Check if cash reserve requirement is met"""
        portfolio_value = self.get_portfolio_value()
        required_reserve = portfolio_value * self.cash_reserve_pct
        
        return self.cash_balance >= required_reserve
    
    def get_available_cash(self) -> float:
        """Get cash available for new positions"""
        portfolio_value = self.get_portfolio_value()
        required_reserve = portfolio_value * self.cash_reserve_pct
        
        return max(0, self.cash_balance - required_reserve)
