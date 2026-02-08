"""
Circuit Breaker Module

Automatic trading halt system triggered by abnormal market conditions.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Trading halted
    COOLDOWN = "cooldown"  # Waiting to resume


class CircuitBreaker:
    """
    Circuit breaker system
    
    Automatically halts trading when:
    - Volatility spikes above threshold
    - Rapid losses exceed threshold
    - Unusual market conditions detected
    - Manual trigger
    """
    
    def __init__(self, config: dict):
        """
        Initialize circuit breaker
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        
        # Volatility thresholds
        self.volatility_threshold = config.get('volatility_threshold', 0.10)  # 10%
        self.price_change_threshold = config.get('price_change_threshold', 0.05)  # 5%
        
        # Loss thresholds
        self.rapid_loss_threshold = config.get('rapid_loss_threshold', 0.03)  # 3%
        self.rapid_loss_window = config.get('rapid_loss_window', 300)  # 5 minutes
        
        # Cooldown period
        self.cooldown_period = config.get('cooldown_period', 900)  # 15 minutes
        
        # State
        self.state = CircuitBreakerState.CLOSED
        self.trigger_time = None
        self.trigger_reason = None
        self.cooldown_start = None
        
        # Tracking
        self.recent_values = []
        self.recent_pnl = []
        
        logger.info("Circuit Breaker initialized")
    
    def update(
        self,
        portfolio_value: float,
        pnl: float,
        timestamp: datetime
    ):
        """
        Update circuit breaker with current state
        
        Args:
            portfolio_value: Current portfolio value
            pnl: Recent P&L
            timestamp: Current timestamp
        """
        # Check if in cooldown
        if self.state == CircuitBreakerState.COOLDOWN:
            if self._is_cooldown_complete(timestamp):
                self._reset()
                logger.info("Circuit breaker cooldown complete - resuming trading")
        
        # Only check conditions if closed
        if self.state == CircuitBreakerState.CLOSED:
            # Add to tracking
            self.recent_values.append({
                'timestamp': timestamp,
                'value': portfolio_value
            })
            
            self.recent_pnl.append({
                'timestamp': timestamp,
                'pnl': pnl
            })
            
            # Keep only recent data
            cutoff_time = timestamp - timedelta(seconds=self.rapid_loss_window)
            self.recent_values = [
                v for v in self.recent_values 
                if v['timestamp'] > cutoff_time
            ]
            self.recent_pnl = [
                p for p in self.recent_pnl 
                if p['timestamp'] > cutoff_time
            ]
            
            # Check conditions
            self._check_rapid_loss()
            self._check_volatility()
    
    def _check_rapid_loss(self):
        """Check for rapid losses"""
        if len(self.recent_pnl) < 2:
            return
        
        # Calculate loss over window
        total_pnl = sum(p['pnl'] for p in self.recent_pnl)
        first_value = self.recent_values[0]['value']
        
        if first_value > 0:
            loss_pct = -total_pnl / first_value
            
            if loss_pct >= self.rapid_loss_threshold:
                self._trigger(f"Rapid loss: {loss_pct:.2%} in {len(self.recent_pnl)} updates")
    
    def _check_volatility(self):
        """Check for extreme volatility"""
        if len(self.recent_values) < 10:
            return
        
        # Calculate recent volatility
        values = [v['value'] for v in self.recent_values]
        returns = [
            (values[i] - values[i-1]) / values[i-1]
            for i in range(1, len(values))
        ]
        
        if not returns:
            return
        
        # Standard deviation of returns
        import statistics
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        if volatility >= self.volatility_threshold:
            self._trigger(f"Extreme volatility: {volatility:.2%}")
    
    def _trigger(self, reason: str):
        """Trigger circuit breaker"""
        self.state = CircuitBreakerState.OPEN
        self.trigger_time = datetime.now()
        self.trigger_reason = reason
        
        logger.error(f"CIRCUIT BREAKER TRIGGERED: {reason}")
        
        # Start cooldown after a short period
        self.cooldown_start = self.trigger_time
        self.state = CircuitBreakerState.COOLDOWN
    
    def manual_trigger(self, reason: str = "Manual trigger"):
        """Manually trigger circuit breaker"""
        self._trigger(reason)
    
    def _is_cooldown_complete(self, timestamp: datetime) -> bool:
        """Check if cooldown period is complete"""
        if not self.cooldown_start:
            return False
        
        elapsed = (timestamp - self.cooldown_start).total_seconds()
        return elapsed >= self.cooldown_period
    
    def _reset(self):
        """Reset circuit breaker to closed state"""
        self.state = CircuitBreakerState.CLOSED
        self.trigger_time = None
        self.trigger_reason = None
        self.cooldown_start = None
        self.recent_values = []
        self.recent_pnl = []
    
    def reset(self):
        """Manually reset circuit breaker"""
        old_state = self.state
        self._reset()
        logger.warning(f"Circuit breaker manually reset from {old_state.value}")
    
    def is_triggered(self) -> bool:
        """Check if circuit breaker is triggered (open or cooldown)"""
        return self.state != CircuitBreakerState.CLOSED
    
    def get_trigger_reason(self) -> Optional[str]:
        """Get reason for trigger"""
        return self.trigger_reason
    
    def get_state(self) -> CircuitBreakerState:
        """Get current state"""
        return self.state
    
    def get_status(self) -> dict:
        """Get detailed status"""
        status = {
            'state': self.state.value,
            'triggered': self.is_triggered(),
            'trigger_reason': self.trigger_reason,
            'trigger_time': self.trigger_time,
        }
        
        if self.state == CircuitBreakerState.COOLDOWN and self.cooldown_start:
            elapsed = (datetime.now() - self.cooldown_start).total_seconds()
            remaining = max(0, self.cooldown_period - elapsed)
            status['cooldown_remaining_seconds'] = remaining
        
        return status
    
    def check_market_conditions(
        self,
        volatility: float,
        price_change: float
    ) -> bool:
        """
        Check if market conditions warrant circuit breaker
        
        Args:
            volatility: Current market volatility
            price_change: Recent price change percentage
            
        Returns:
            True if conditions are abnormal
        """
        if volatility > self.volatility_threshold:
            logger.warning(f"High volatility detected: {volatility:.2%}")
            return True
        
        if abs(price_change) > self.price_change_threshold:
            logger.warning(f"Large price change detected: {price_change:.2%}")
            return True
        
        return False
