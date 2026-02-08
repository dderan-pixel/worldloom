"""
Exposure Calculator Module

Calculates portfolio exposure across positions and exchanges.
"""

import logging
from typing import Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


class ExposureCalculator:
    """
    Portfolio exposure calculator
    
    Tracks and calculates exposure across:
    - Individual positions
    - Asset classes
    - Exchanges
    - Correlation-adjusted exposure
    """
    
    def __init__(self, config: Dict):
        """
        Initialize exposure calculator
        
        Args:
            config: Exposure configuration
        """
        self.config = config
        self.current_positions = {}
        self.portfolio_value = 0
        
        # Asset correlation matrix (placeholder)
        self.correlation_matrix = {}
    
    def calculate_total_exposure(
        self,
        positions: Dict,
        portfolio_value: float
    ) -> float:
        """
        Calculate total portfolio exposure
        
        Args:
            positions: Dict of current positions
            portfolio_value: Current portfolio value
            
        Returns:
            Total exposure as percentage of portfolio
        """
        if portfolio_value <= 0:
            return 0.0
        
        total_position_value = 0.0
        
        for symbol, position in positions.items():
            # Calculate position value
            position_value = abs(position['quantity'] * position.get('current_price', position['entry_price']))
            total_position_value += position_value
        
        # Calculate gross exposure (sum of all position values)
        gross_exposure = total_position_value / portfolio_value
        
        return gross_exposure
    
    def calculate_net_exposure(
        self,
        positions: Dict,
        portfolio_value: float
    ) -> float:
        """
        Calculate net portfolio exposure (longs - shorts)
        
        Args:
            positions: Dict of current positions
            portfolio_value: Current portfolio value
            
        Returns:
            Net exposure as percentage of portfolio
        """
        if portfolio_value <= 0:
            return 0.0
        
        long_value = 0.0
        short_value = 0.0
        
        for symbol, position in positions.items():
            position_value = abs(position['quantity'] * position.get('current_price', position['entry_price']))
            
            if position['side'] == 'long':
                long_value += position_value
            else:
                short_value += position_value
        
        net_exposure = (long_value - short_value) / portfolio_value
        
        return net_exposure
    
    def calculate_new_exposure(
        self,
        current_positions: Dict,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        portfolio_value: float
    ) -> Dict:
        """
        Calculate exposure after a new order
        
        Args:
            current_positions: Current positions
            symbol: Symbol for new order
            side: Order side (buy/sell)
            quantity: Order quantity
            price: Order price
            portfolio_value: Current portfolio value
            
        Returns:
            Dict with exposure metrics
        """
        # Create a copy of positions
        new_positions = current_positions.copy()
        
        # Add or update position
        order_value = quantity * price
        
        if symbol in new_positions:
            # Update existing position
            existing = new_positions[symbol]
            if existing['side'] == side:
                # Same side - increase position
                total_quantity = existing['quantity'] + quantity
                new_positions[symbol] = {
                    'side': side,
                    'quantity': total_quantity,
                    'entry_price': price,
                    'current_price': price
                }
            else:
                # Opposite side - reduce or reverse position
                net_quantity = abs(existing['quantity'] - quantity)
                if net_quantity > 0:
                    new_side = side if quantity > existing['quantity'] else existing['side']
                    new_positions[symbol] = {
                        'side': new_side,
                        'quantity': net_quantity,
                        'entry_price': price,
                        'current_price': price
                    }
                else:
                    # Position closed
                    del new_positions[symbol]
        else:
            # New position
            new_positions[symbol] = {
                'side': side,
                'quantity': quantity,
                'entry_price': price,
                'current_price': price
            }
        
        # Calculate exposures
        total_exposure = self.calculate_total_exposure(new_positions, portfolio_value)
        net_exposure = self.calculate_net_exposure(new_positions, portfolio_value)
        
        # Calculate per-position exposures
        position_exposures = {}
        for sym, pos in new_positions.items():
            pos_value = abs(pos['quantity'] * pos.get('current_price', pos['entry_price']))
            position_exposures[sym] = pos_value / portfolio_value
        
        return {
            'total_exposure_pct': total_exposure,
            'net_exposure_pct': net_exposure,
            'position_exposures': position_exposures,
            'num_positions': len(new_positions)
        }
    
    def get_current_exposure(self) -> Dict:
        """Get current exposure metrics"""
        if not self.current_positions or self.portfolio_value <= 0:
            return {
                'total_exposure_pct': 0.0,
                'net_exposure_pct': 0.0,
                'long_exposure_pct': 0.0,
                'short_exposure_pct': 0.0,
                'num_positions': 0,
                'position_exposures': {}
            }
        
        total_exposure = self.calculate_total_exposure(
            self.current_positions, self.portfolio_value
        )
        net_exposure = self.calculate_net_exposure(
            self.current_positions, self.portfolio_value
        )
        
        # Calculate long/short breakdown
        long_value = 0.0
        short_value = 0.0
        position_exposures = {}
        
        for symbol, position in self.current_positions.items():
            pos_value = abs(position['quantity'] * position.get('current_price', position['entry_price']))
            position_exposures[symbol] = pos_value / self.portfolio_value
            
            if position['side'] == 'long':
                long_value += pos_value
            else:
                short_value += pos_value
        
        return {
            'total_exposure_pct': total_exposure,
            'net_exposure_pct': net_exposure,
            'long_exposure_pct': long_value / self.portfolio_value,
            'short_exposure_pct': short_value / self.portfolio_value,
            'num_positions': len(self.current_positions),
            'position_exposures': position_exposures
        }
    
    def update_positions(self, positions: Dict, portfolio_value: float):
        """Update current positions and portfolio value"""
        self.current_positions = positions
        self.portfolio_value = portfolio_value
    
    def calculate_sector_exposure(
        self,
        positions: Dict,
        portfolio_value: float,
        sector_mapping: Dict
    ) -> Dict:
        """
        Calculate exposure by sector
        
        Args:
            positions: Current positions
            portfolio_value: Portfolio value
            sector_mapping: Dict mapping symbols to sectors
            
        Returns:
            Dict with sector exposures
        """
        sector_exposures = {}
        
        for symbol, position in positions.items():
            sector = sector_mapping.get(symbol, 'unknown')
            pos_value = abs(position['quantity'] * position.get('current_price', position['entry_price']))
            
            if sector not in sector_exposures:
                sector_exposures[sector] = 0.0
            
            sector_exposures[sector] += pos_value
        
        # Convert to percentages
        sector_pct = {
            sector: value / portfolio_value
            for sector, value in sector_exposures.items()
        }
        
        return sector_pct
    
    def calculate_exchange_exposure(
        self,
        positions: Dict,
        portfolio_value: float
    ) -> Dict:
        """
        Calculate exposure by exchange
        
        Args:
            positions: Current positions
            portfolio_value: Portfolio value
            
        Returns:
            Dict with exchange exposures
        """
        exchange_exposures = {}
        
        for symbol, position in positions.items():
            exchange = position.get('exchange', 'unknown')
            pos_value = abs(position['quantity'] * position.get('current_price', position['entry_price']))
            
            if exchange not in exchange_exposures:
                exchange_exposures[exchange] = 0.0
            
            exchange_exposures[exchange] += pos_value
        
        # Convert to percentages
        exchange_pct = {
            exchange: value / portfolio_value
            for exchange, value in exchange_exposures.items()
        }
        
        return exchange_pct
