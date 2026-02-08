"""
Risk Manager Module

Central risk management system coordinating all risk controls.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd

from .exposure_calculator import ExposureCalculator
from .drawdown_guard import DrawdownGuard
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Central risk management system
    
    Coordinates all risk controls including:
    - Position exposure limits
    - Drawdown protection
    - Circuit breakers
    - Dynamic leverage adjustment
    """
    
    def __init__(self, config: Dict):
        """
        Initialize risk manager
        
        Args:
            config: Risk management configuration
        """
        self.config = config
        
        # Initialize sub-components
        self.exposure_calculator = ExposureCalculator(
            config.get('exposure', {})
        )
        self.drawdown_guard = DrawdownGuard(
            config.get('drawdown', {})
        )
        self.circuit_breaker = CircuitBreaker(
            config.get('circuit_breaker', {})
        )
        
        # Risk limits
        self.max_portfolio_exposure = config.get('max_portfolio_exposure', 1.0)
        self.max_single_position = config.get('max_single_position', 0.2)
        self.max_sector_exposure = config.get('max_sector_exposure', 0.3)
        self.max_leverage = config.get('max_leverage', 3.0)
        
        # State
        self.trading_enabled = True
        self.risk_violations = []
        
        logger.info("Risk Manager initialized")
    
    def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        current_positions: Dict,
        portfolio_value: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if an order can be placed
        
        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            quantity: Order quantity
            price: Order price
            current_positions: Current portfolio positions
            portfolio_value: Current portfolio value
            
        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        # Check if trading is globally disabled
        if not self.trading_enabled:
            return False, "Trading is currently disabled"
        
        # Check circuit breaker
        if self.circuit_breaker.is_triggered():
            return False, f"Circuit breaker triggered: {self.circuit_breaker.get_trigger_reason()}"
        
        # Check drawdown limit
        if self.drawdown_guard.is_limit_reached():
            return False, f"Drawdown limit reached: {self.drawdown_guard.get_current_drawdown():.2%}"
        
        # Calculate order value
        order_value = quantity * price
        order_pct = order_value / portfolio_value
        
        # Check single position limit
        if order_pct > self.max_single_position:
            return False, f"Order exceeds max single position limit: {order_pct:.2%} > {self.max_single_position:.2%}"
        
        # Calculate new exposure after order
        new_exposure = self.exposure_calculator.calculate_new_exposure(
            current_positions,
            symbol,
            side,
            quantity,
            price,
            portfolio_value
        )
        
        # Check portfolio exposure limit
        if new_exposure['total_exposure_pct'] > self.max_portfolio_exposure:
            return False, f"Order would exceed portfolio exposure limit: {new_exposure['total_exposure_pct']:.2%} > {self.max_portfolio_exposure:.2%}"
        
        # Check concentration risk
        if symbol in new_exposure['position_exposures']:
            position_exposure = new_exposure['position_exposures'][symbol]
            if position_exposure > self.max_single_position:
                return False, f"Position concentration too high: {position_exposure:.2%}"
        
        # All checks passed
        return True, None
    
    def check_leverage(
        self,
        position_value: float,
        collateral: float,
        volatility: Optional[float] = None
    ) -> Tuple[float, bool]:
        """
        Calculate and validate leverage
        
        Args:
            position_value: Total position value
            collateral: Available collateral
            volatility: Optional volatility for dynamic adjustment
            
        Returns:
            Tuple of (recommended_leverage, is_acceptable)
        """
        if collateral <= 0:
            return 1.0, False
        
        # Calculate current leverage
        current_leverage = position_value / collateral
        
        # Adjust max leverage based on volatility
        adjusted_max_leverage = self.max_leverage
        
        if volatility:
            # Reduce leverage in high volatility
            if volatility > 0.5:  # 50% annualized
                adjusted_max_leverage *= 0.5
            elif volatility > 0.3:  # 30% annualized
                adjusted_max_leverage *= 0.7
        
        # Check if acceptable
        is_acceptable = current_leverage <= adjusted_max_leverage
        
        # Recommend leverage
        recommended = min(current_leverage, adjusted_max_leverage)
        
        if not is_acceptable:
            logger.warning(
                f"Leverage {current_leverage:.2f}x exceeds limit {adjusted_max_leverage:.2f}x"
            )
        
        return recommended, is_acceptable
    
    def update_portfolio_state(
        self,
        portfolio_value: float,
        positions: Dict,
        pnl: float,
        timestamp: datetime
    ):
        """
        Update risk manager with current portfolio state
        
        Args:
            portfolio_value: Current portfolio value
            positions: Current positions
            pnl: Profit/loss since last update
            timestamp: Current timestamp
        """
        # Update drawdown guard
        self.drawdown_guard.update(portfolio_value, timestamp)
        
        # Update circuit breaker
        self.circuit_breaker.update(portfolio_value, pnl, timestamp)
        
        # Update exposure calculator
        self.exposure_calculator.update_positions(positions, portfolio_value)
        
        # Check for violations
        self._check_risk_violations(portfolio_value, positions)
    
    def _check_risk_violations(self, portfolio_value: float, positions: Dict):
        """Check for any risk limit violations"""
        violations = []
        
        # Check drawdown
        if self.drawdown_guard.is_limit_reached():
            violations.append({
                'type': 'drawdown',
                'severity': 'critical',
                'message': f"Drawdown limit exceeded: {self.drawdown_guard.get_current_drawdown():.2%}"
            })
        
        # Check circuit breaker
        if self.circuit_breaker.is_triggered():
            violations.append({
                'type': 'circuit_breaker',
                'severity': 'critical',
                'message': f"Circuit breaker triggered: {self.circuit_breaker.get_trigger_reason()}"
            })
        
        # Check exposure
        exposure = self.exposure_calculator.get_current_exposure()
        if exposure['total_exposure_pct'] > self.max_portfolio_exposure:
            violations.append({
                'type': 'exposure',
                'severity': 'high',
                'message': f"Portfolio exposure limit exceeded: {exposure['total_exposure_pct']:.2%}"
            })
        
        # Log violations
        for violation in violations:
            logger.error(f"Risk violation: {violation['message']}")
            self.risk_violations.append({
                'timestamp': datetime.now(),
                **violation
            })
    
    def enable_trading(self):
        """Enable trading"""
        self.trading_enabled = True
        logger.info("Trading enabled")
    
    def disable_trading(self, reason: str = "Manual"):
        """Disable trading"""
        self.trading_enabled = False
        logger.warning(f"Trading disabled: {reason}")
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker"""
        self.circuit_breaker.reset()
        logger.info("Circuit breaker reset")
    
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        return {
            'trading_enabled': self.trading_enabled,
            'circuit_breaker': {
                'triggered': self.circuit_breaker.is_triggered(),
                'reason': self.circuit_breaker.get_trigger_reason()
            },
            'drawdown': {
                'current': self.drawdown_guard.get_current_drawdown(),
                'limit_reached': self.drawdown_guard.is_limit_reached(),
                'max_allowed': self.drawdown_guard.max_drawdown
            },
            'exposure': self.exposure_calculator.get_current_exposure(),
            'limits': {
                'max_portfolio_exposure': self.max_portfolio_exposure,
                'max_single_position': self.max_single_position,
                'max_leverage': self.max_leverage
            },
            'violations': self.risk_violations[-10:]  # Last 10 violations
        }
    
    def calculate_position_limits(
        self,
        symbol: str,
        current_positions: Dict,
        portfolio_value: float
    ) -> Dict:
        """
        Calculate maximum position size for a symbol
        
        Args:
            symbol: Trading symbol
            current_positions: Current positions
            portfolio_value: Current portfolio value
            
        Returns:
            Dict with position limits
        """
        # Maximum single position value
        max_position_value = portfolio_value * self.max_single_position
        
        # Remaining portfolio capacity
        current_exposure = self.exposure_calculator.calculate_total_exposure(
            current_positions, portfolio_value
        )
        remaining_capacity = (self.max_portfolio_exposure - current_exposure) * portfolio_value
        
        # Maximum allowed for this symbol
        max_allowed_value = min(max_position_value, remaining_capacity)
        
        return {
            'symbol': symbol,
            'max_position_value': max_allowed_value,
            'max_position_pct': max_allowed_value / portfolio_value,
            'current_exposure_pct': current_exposure,
            'remaining_capacity_pct': self.max_portfolio_exposure - current_exposure
        }
