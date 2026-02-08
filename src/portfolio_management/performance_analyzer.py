"""
Performance Analyzer Module

Analyzes trading performance with comprehensive metrics.
"""

import logging
from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    Trading performance analyzer
    
    Calculates:
    - Sharpe ratio, Sortino ratio
    - Maximum drawdown
    - Win rate, profit factor
    - Return metrics
    """
    
    def __init__(self):
        """Initialize performance analyzer"""
        self.trades_history: List[Dict] = []
        self.portfolio_history: List[Dict] = []
    
    def add_trade(self, trade: Dict):
        """Add a completed trade to history"""
        self.trades_history.append(trade)
    
    def add_portfolio_snapshot(self, snapshot: Dict):
        """Add a portfolio snapshot"""
        self.portfolio_history.append(snapshot)
    
    def calculate_returns(self) -> pd.Series:
        """Calculate portfolio returns series"""
        if not self.portfolio_history:
            return pd.Series()
        
        df = pd.DataFrame(self.portfolio_history)
        df['returns'] = df['total_value'].pct_change()
        
        return df['returns'].dropna()
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio
        
        Args:
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sharpe ratio
        """
        returns = self.calculate_returns()
        
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        
        return sharpe
    
    def calculate_sortino_ratio(
        self, 
        risk_free_rate: float = 0.02,
        target_return: float = 0.0
    ) -> float:
        """
        Calculate Sortino ratio
        
        Args:
            risk_free_rate: Annual risk-free rate
            target_return: Target return threshold
            
        Returns:
            Sortino ratio
        """
        returns = self.calculate_returns()
        
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = returns[returns < target_return]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        sortino = np.sqrt(252) * excess_returns.mean() / downside_returns.std()
        
        return sortino
    
    def calculate_max_drawdown(self) -> Dict:
        """Calculate maximum drawdown"""
        if not self.portfolio_history:
            return {'max_drawdown': 0, 'drawdown_duration': 0}
        
        df = pd.DataFrame(self.portfolio_history)
        portfolio_values = df['total_value']
        
        # Calculate running maximum
        running_max = portfolio_values.expanding().max()
        
        # Calculate drawdown
        drawdown = (portfolio_values - running_max) / running_max
        
        max_dd = drawdown.min()
        
        # Find drawdown duration
        dd_duration = 0
        current_duration = 0
        max_duration = 0
        
        for dd in drawdown:
            if dd < 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        
        return {
            'max_drawdown': abs(max_dd),
            'drawdown_duration': max_duration,
            'current_drawdown': abs(drawdown.iloc[-1]) if len(drawdown) > 0 else 0
        }
    
    def calculate_win_rate(self) -> float:
        """Calculate win rate"""
        if not self.trades_history:
            return 0.0
        
        winning_trades = sum(1 for trade in self.trades_history if trade.get('pnl', 0) > 0)
        
        return winning_trades / len(self.trades_history)
    
    def calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        if not self.trades_history:
            return 0.0
        
        gross_profit = sum(
            trade.get('pnl', 0) 
            for trade in self.trades_history 
            if trade.get('pnl', 0) > 0
        )
        
        gross_loss = abs(sum(
            trade.get('pnl', 0) 
            for trade in self.trades_history 
            if trade.get('pnl', 0) < 0
        ))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def calculate_avg_win_loss_ratio(self) -> float:
        """Calculate average win/loss ratio"""
        if not self.trades_history:
            return 0.0
        
        wins = [trade.get('pnl', 0) for trade in self.trades_history if trade.get('pnl', 0) > 0]
        losses = [abs(trade.get('pnl', 0)) for trade in self.trades_history if trade.get('pnl', 0) < 0]
        
        if not wins or not losses:
            return 0.0
        
        avg_win = np.mean(wins)
        avg_loss = np.mean(losses)
        
        return avg_win / avg_loss if avg_loss > 0 else 0.0
    
    def get_comprehensive_metrics(self) -> Dict:
        """Get all performance metrics"""
        returns = self.calculate_returns()
        max_dd_info = self.calculate_max_drawdown()
        
        if not self.portfolio_history or len(self.portfolio_history) < 2:
            return {}
        
        initial_value = self.portfolio_history[0]['total_value']
        final_value = self.portfolio_history[-1]['total_value']
        total_return = (final_value - initial_value) / initial_value
        
        # Calculate annualized return
        days = (
            self.portfolio_history[-1]['timestamp'] - 
            self.portfolio_history[0]['timestamp']
        ).days
        
        if days > 0:
            annualized_return = (1 + total_return) ** (365 / days) - 1
        else:
            annualized_return = 0.0
        
        return {
            'total_return': total_return,
            'total_return_pct': total_return,
            'annualized_return': annualized_return,
            'annualized_return_pct': annualized_return,
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'max_drawdown': max_dd_info['max_drawdown'],
            'max_drawdown_pct': max_dd_info['max_drawdown'],
            'current_drawdown': max_dd_info['current_drawdown'],
            'drawdown_duration': max_dd_info['drawdown_duration'],
            'win_rate': self.calculate_win_rate(),
            'profit_factor': self.calculate_profit_factor(),
            'avg_win_loss_ratio': self.calculate_avg_win_loss_ratio(),
            'total_trades': len(self.trades_history),
            'winning_trades': sum(1 for t in self.trades_history if t.get('pnl', 0) > 0),
            'losing_trades': sum(1 for t in self.trades_history if t.get('pnl', 0) < 0),
            'volatility': returns.std() * np.sqrt(252) if len(returns) > 1 else 0.0
        }
