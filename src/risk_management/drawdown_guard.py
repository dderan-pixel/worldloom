"""
Drawdown Guard Module

Monitors and protects against excessive portfolio drawdowns.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


class DrawdownGuard:
    """
    Drawdown protection system
    
    Monitors portfolio value and enforces maximum drawdown limits.
    Includes daily, weekly, and overall drawdown tracking.
    """
    
    def __init__(self, config: dict):
        """
        Initialize drawdown guard
        
        Args:
            config: Drawdown configuration
        """
        self.config = config
        
        # Drawdown limits
        self.max_drawdown = config.get('max_drawdown', 0.20)  # 20%
        self.max_daily_drawdown = config.get('max_daily_drawdown', 0.05)  # 5%
        self.max_weekly_drawdown = config.get('max_weekly_drawdown', 0.10)  # 10%
        
        # State tracking
        self.peak_value = 0.0
        self.daily_peak_value = 0.0
        self.weekly_peak_value = 0.0
        self.current_value = 0.0
        
        self.daily_start_value = 0.0
        self.weekly_start_value = 0.0
        
        self.last_reset_date = None
        self.last_weekly_reset = None
        
        # History
        self.value_history = []
        self.drawdown_history = []
        
        logger.info(f"Drawdown Guard initialized - Max DD: {self.max_drawdown:.1%}")
    
    def update(self, portfolio_value: float, timestamp: datetime):
        """
        Update with current portfolio value
        
        Args:
            portfolio_value: Current portfolio value
            timestamp: Current timestamp
        """
        self.current_value = portfolio_value
        
        # Initialize on first update
        if self.peak_value == 0:
            self.peak_value = portfolio_value
            self.daily_peak_value = portfolio_value
            self.weekly_peak_value = portfolio_value
            self.daily_start_value = portfolio_value
            self.weekly_start_value = portfolio_value
            self.last_reset_date = timestamp.date()
            self.last_weekly_reset = timestamp.date()
        
        # Update peaks
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        
        if portfolio_value > self.daily_peak_value:
            self.daily_peak_value = portfolio_value
        
        if portfolio_value > self.weekly_peak_value:
            self.weekly_peak_value = portfolio_value
        
        # Check for daily reset
        if timestamp.date() > self.last_reset_date:
            self.daily_start_value = self.daily_peak_value
            self.daily_peak_value = portfolio_value
            self.last_reset_date = timestamp.date()
            logger.debug(f"Daily drawdown reset at ${portfolio_value:,.2f}")
        
        # Check for weekly reset
        if (timestamp.date() - self.last_weekly_reset).days >= 7:
            self.weekly_start_value = self.weekly_peak_value
            self.weekly_peak_value = portfolio_value
            self.last_weekly_reset = timestamp.date()
            logger.debug(f"Weekly drawdown reset at ${portfolio_value:,.2f}")
        
        # Record history
        self.value_history.append({
            'timestamp': timestamp,
            'value': portfolio_value,
            'peak': self.peak_value
        })
        
        # Calculate drawdowns
        overall_dd = self.get_current_drawdown()
        daily_dd = self.get_daily_drawdown()
        weekly_dd = self.get_weekly_drawdown()
        
        self.drawdown_history.append({
            'timestamp': timestamp,
            'overall': overall_dd,
            'daily': daily_dd,
            'weekly': weekly_dd
        })
        
        # Check limits
        if self.is_limit_reached():
            logger.error(
                f"Drawdown limit reached! Overall: {overall_dd:.2%}, "
                f"Daily: {daily_dd:.2%}, Weekly: {weekly_dd:.2%}"
            )
    
    def get_current_drawdown(self) -> float:
        """Get current overall drawdown"""
        if self.peak_value == 0:
            return 0.0
        
        drawdown = (self.peak_value - self.current_value) / self.peak_value
        return drawdown
    
    def get_daily_drawdown(self) -> float:
        """Get current daily drawdown"""
        if self.daily_peak_value == 0:
            return 0.0
        
        drawdown = (self.daily_peak_value - self.current_value) / self.daily_peak_value
        return drawdown
    
    def get_weekly_drawdown(self) -> float:
        """Get current weekly drawdown"""
        if self.weekly_peak_value == 0:
            return 0.0
        
        drawdown = (self.weekly_peak_value - self.current_value) / self.weekly_peak_value
        return drawdown
    
    def is_limit_reached(self) -> bool:
        """Check if any drawdown limit is reached"""
        overall_dd = self.get_current_drawdown()
        daily_dd = self.get_daily_drawdown()
        weekly_dd = self.get_weekly_drawdown()
        
        if overall_dd >= self.max_drawdown:
            logger.warning(f"Overall drawdown limit reached: {overall_dd:.2%}")
            return True
        
        if daily_dd >= self.max_daily_drawdown:
            logger.warning(f"Daily drawdown limit reached: {daily_dd:.2%}")
            return True
        
        if weekly_dd >= self.max_weekly_drawdown:
            logger.warning(f"Weekly drawdown limit reached: {weekly_dd:.2%}")
            return True
        
        return False
    
    def reset(self):
        """Reset drawdown tracking (use with caution)"""
        self.peak_value = self.current_value
        self.daily_peak_value = self.current_value
        self.weekly_peak_value = self.current_value
        logger.warning("Drawdown tracking reset")
    
    def get_statistics(self) -> dict:
        """Get drawdown statistics"""
        if not self.drawdown_history:
            return {}
        
        df = pd.DataFrame(self.drawdown_history)
        
        return {
            'current_overall': self.get_current_drawdown(),
            'current_daily': self.get_daily_drawdown(),
            'current_weekly': self.get_weekly_drawdown(),
            'max_overall_observed': df['overall'].max(),
            'max_daily_observed': df['daily'].max(),
            'max_weekly_observed': df['weekly'].max(),
            'limits': {
                'max_drawdown': self.max_drawdown,
                'max_daily_drawdown': self.max_daily_drawdown,
                'max_weekly_drawdown': self.max_weekly_drawdown
            },
            'peak_value': self.peak_value,
            'current_value': self.current_value,
            'total_decline_from_peak': self.peak_value - self.current_value
        }
    
    def get_underwater_period(self) -> Optional[int]:
        """
        Get number of days portfolio has been underwater (below peak)
        
        Returns:
            Number of days, or None if at peak
        """
        if self.current_value >= self.peak_value:
            return None
        
        if not self.value_history:
            return None
        
        # Find last time we were at peak
        days_underwater = 0
        for record in reversed(self.value_history):
            if record['value'] >= record['peak']:
                break
            days_underwater += 1
        
        return days_underwater
