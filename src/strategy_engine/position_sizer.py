"""
Position Sizing Module

Calculates optimal position sizes based on portfolio volatility and risk parameters.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PositionSizer:
    """
    Dynamic position sizing engine
    
    Calculates position sizes based on:
    - Portfolio volatility
    - Risk per trade
    - Kelly Criterion
    - Volatility regime
    """
    
    def __init__(self, config: Dict):
        """
        Initialize position sizer
        
        Args:
            config: Configuration with risk parameters
        """
        self.config = config
        
        # Risk parameters
        self.portfolio_value = config.get('portfolio_value', 100000)
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.02)  # 2%
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.06)  # 6%
        self.target_volatility = config.get('target_volatility', 0.15)  # 15% annualized
        
        # Position limits
        self.max_position_size = config.get('max_position_size', 0.2)  # 20% of portfolio
        self.min_position_size = config.get('min_position_size', 0.01)  # 1% of portfolio
        
        # Kelly parameters
        self.use_kelly = config.get('use_kelly', False)
        self.kelly_fraction = config.get('kelly_fraction', 0.25)  # Use 25% of Kelly
        
        self.current_positions_risk = 0.0
    
    def calculate_position_size(
        self,
        signal_strength: float,
        asset_price: float,
        asset_volatility: float,
        stop_loss_pct: float,
        win_rate: Optional[float] = None,
        avg_win_loss_ratio: Optional[float] = None,
        volatility_regime: Optional[str] = None
    ) -> Dict:
        """
        Calculate optimal position size
        
        Args:
            signal_strength: Signal strength (0.0 to 1.0)
            asset_price: Current asset price
            asset_volatility: Asset volatility (annualized)
            stop_loss_pct: Stop loss percentage
            win_rate: Historical win rate (for Kelly)
            avg_win_loss_ratio: Average win/loss ratio (for Kelly)
            volatility_regime: Current volatility regime
            
        Returns:
            Dict with position sizing details
        """
        # Calculate base position size using volatility targeting
        volatility_size = self._volatility_based_sizing(
            asset_volatility, 
            asset_price
        )
        
        # Calculate risk-based position size
        risk_size = self._risk_based_sizing(
            asset_price, 
            stop_loss_pct
        )
        
        # Calculate Kelly-based size if enabled
        kelly_size = None
        if self.use_kelly and win_rate and avg_win_loss_ratio:
            kelly_size = self._kelly_criterion_sizing(
                asset_price,
                win_rate,
                avg_win_loss_ratio
            )
        
        # Choose most conservative size
        position_sizes = [volatility_size, risk_size]
        if kelly_size:
            position_sizes.append(kelly_size)
        
        base_size = min(position_sizes)
        
        # Apply signal strength adjustment
        adjusted_size = base_size * signal_strength
        
        # Apply volatility regime adjustment
        if volatility_regime:
            regime_multiplier = self._get_regime_multiplier(volatility_regime)
            adjusted_size *= regime_multiplier
        
        # Apply portfolio risk limits
        final_size = self._apply_portfolio_limits(adjusted_size)
        
        # Calculate number of units
        units = final_size / asset_price
        
        # Calculate dollar risk
        dollar_risk = final_size * stop_loss_pct
        
        # Calculate position metrics
        position_pct = final_size / self.portfolio_value
        risk_pct = dollar_risk / self.portfolio_value
        
        return {
            'units': units,
            'position_value': final_size,
            'position_pct': position_pct,
            'dollar_risk': dollar_risk,
            'risk_pct': risk_pct,
            'method': 'composite',
            'volatility_size': volatility_size,
            'risk_size': risk_size,
            'kelly_size': kelly_size,
            'signal_adjusted': adjusted_size != base_size
        }
    
    def _volatility_based_sizing(
        self, 
        asset_volatility: float, 
        asset_price: float
    ) -> float:
        """
        Calculate position size based on volatility targeting
        
        Uses inverse volatility weighting to maintain consistent portfolio risk
        """
        if asset_volatility <= 0:
            logger.warning("Invalid asset volatility")
            return self.min_position_size * self.portfolio_value
        
        # Target volatility contribution
        target_position_vol = self.target_volatility / np.sqrt(252)  # Daily
        
        # Position size = (Target Vol / Asset Vol) * Portfolio Value
        size = (target_position_vol / asset_volatility) * self.portfolio_value
        
        return size
    
    def _risk_based_sizing(
        self, 
        asset_price: float, 
        stop_loss_pct: float
    ) -> float:
        """
        Calculate position size based on fixed fractional risk
        
        Risk amount = Portfolio Value * Risk per Trade
        Position Size = Risk Amount / Stop Loss %
        """
        if stop_loss_pct <= 0:
            logger.warning("Invalid stop loss percentage")
            return self.min_position_size * self.portfolio_value
        
        # Dollar amount willing to risk
        risk_amount = self.portfolio_value * self.max_risk_per_trade
        
        # Position size that risks this amount
        size = risk_amount / stop_loss_pct
        
        return size
    
    def _kelly_criterion_sizing(
        self,
        asset_price: float,
        win_rate: float,
        avg_win_loss_ratio: float
    ) -> float:
        """
        Calculate position size using Kelly Criterion
        
        Kelly % = W - [(1 - W) / R]
        Where: W = win rate, R = avg win/loss ratio
        """
        if not (0 < win_rate < 1) or avg_win_loss_ratio <= 0:
            logger.warning("Invalid Kelly parameters")
            return self.min_position_size * self.portfolio_value
        
        # Calculate Kelly percentage
        kelly_pct = win_rate - ((1 - win_rate) / avg_win_loss_ratio)
        
        # Never use full Kelly - too aggressive
        kelly_pct = max(0, kelly_pct) * self.kelly_fraction
        
        # Calculate position size
        size = self.portfolio_value * kelly_pct
        
        return size
    
    def _get_regime_multiplier(self, regime: str) -> float:
        """Get position size multiplier based on volatility regime"""
        multipliers = {
            'low': 1.3,
            'normal': 1.0,
            'high': 0.7,
            'extreme': 0.3
        }
        return multipliers.get(regime, 1.0)
    
    def _apply_portfolio_limits(self, position_size: float) -> float:
        """Apply portfolio-level position limits"""
        # Maximum position size
        max_size = self.portfolio_value * self.max_position_size
        position_size = min(position_size, max_size)
        
        # Minimum position size
        min_size = self.portfolio_value * self.min_position_size
        if position_size < min_size:
            logger.info(f"Position size below minimum, setting to {min_size}")
            position_size = min_size
        
        # Check total portfolio risk
        if self.current_positions_risk >= self.max_portfolio_risk:
            logger.warning("Portfolio risk limit reached, reducing position size")
            position_size *= 0.5
        
        return position_size
    
    def update_portfolio_value(self, new_value: float):
        """Update portfolio value"""
        self.portfolio_value = new_value
        logger.info(f"Portfolio value updated to ${new_value:,.2f}")
    
    def update_positions_risk(self, total_risk: float):
        """Update current positions risk"""
        self.current_positions_risk = total_risk
    
    def get_max_units(
        self, 
        asset_price: float, 
        available_margin: Optional[float] = None
    ) -> float:
        """
        Calculate maximum units that can be purchased
        
        Args:
            asset_price: Current asset price
            available_margin: Available margin (for leveraged positions)
            
        Returns:
            Maximum number of units
        """
        max_value = self.portfolio_value * self.max_position_size
        
        if available_margin:
            max_value = min(max_value, available_margin)
        
        max_units = max_value / asset_price
        
        return max_units
    
    def calculate_leverage(
        self,
        position_value: float,
        collateral: float,
        max_leverage: float = 10.0
    ) -> float:
        """
        Calculate appropriate leverage for position
        
        Args:
            position_value: Desired position value
            collateral: Available collateral
            max_leverage: Maximum allowed leverage
            
        Returns:
            Recommended leverage
        """
        if collateral <= 0:
            return 1.0
        
        required_leverage = position_value / collateral
        
        # Cap at maximum
        leverage = min(required_leverage, max_leverage)
        
        # Ensure minimum of 1x
        leverage = max(1.0, leverage)
        
        return leverage
    
    def get_position_limits(self) -> Dict:
        """Get current position sizing limits"""
        return {
            'portfolio_value': self.portfolio_value,
            'max_position_size_pct': self.max_position_size * 100,
            'max_position_value': self.portfolio_value * self.max_position_size,
            'max_risk_per_trade_pct': self.max_risk_per_trade * 100,
            'max_portfolio_risk_pct': self.max_portfolio_risk * 100,
            'current_portfolio_risk_pct': self.current_positions_risk * 100,
            'remaining_risk_capacity_pct': (self.max_portfolio_risk - self.current_positions_risk) * 100
        }
