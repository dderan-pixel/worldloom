"""
Telegram Alerter Module

Send trading alerts via Telegram.
"""

import logging
from typing import Dict, Optional
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramAlerter:
    """
    Telegram alert system
    
    Sends notifications for:
    - Trade executions
    - Risk violations
    - Circuit breaker triggers
    - Significant P&L changes
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Telegram alerter
        
        Args:
            config: Telegram configuration with token and chat_id
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.token = config.get('token')
        self.chat_id = config.get('chat_id')
        self.alert_on = config.get('alert_on', [])
        
        if self.enabled and (not self.token or not self.chat_id):
            logger.warning("Telegram enabled but missing token/chat_id")
            self.enabled = False
        
        if self.enabled:
            logger.info("Telegram alerter initialized")
    
    async def send_alert(self, message: str, level: str = 'INFO'):
        """
        Send alert message
        
        Args:
            message: Alert message
            level: Alert level (INFO, WARNING, ERROR, CRITICAL)
        """
        if not self.enabled:
            return
        
        try:
            # Format message with emoji
            emoji_map = {
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }
            
            emoji = emoji_map.get(level, 'ℹ️')
            formatted_message = f"{emoji} *{level}*\n\n{message}\n\n_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            
            # In production, use python-telegram-bot library
            # For now, log the message
            logger.info(f"Telegram alert [{level}]: {message}")
            
            # TODO: Implement actual Telegram API call
            # await self._send_to_telegram(formatted_message)
            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    async def alert_trade_execution(self, trade: Dict):
        """Alert on trade execution"""
        if 'trade_execution' not in self.alert_on:
            return
        
        message = (
            f"*Trade Executed*\n"
            f"Symbol: {trade.get('symbol', 'N/A')}\n"
            f"Side: {trade.get('side', 'N/A')}\n"
            f"Quantity: {trade.get('quantity', 0)}\n"
            f"Price: ${trade.get('price', 0):,.2f}\n"
            f"Strategy: {trade.get('strategy', 'N/A')}"
        )
        
        await self.send_alert(message, 'INFO')
    
    async def alert_risk_violation(self, violation: Dict):
        """Alert on risk violation"""
        if 'risk_violation' not in self.alert_on:
            return
        
        message = (
            f"*Risk Violation Detected*\n"
            f"Type: {violation.get('type', 'N/A')}\n"
            f"Severity: {violation.get('severity', 'N/A')}\n"
            f"Message: {violation.get('message', 'N/A')}"
        )
        
        await self.send_alert(message, 'WARNING')
    
    async def alert_circuit_breaker(self, reason: str):
        """Alert on circuit breaker trigger"""
        if 'circuit_breaker' not in self.alert_on:
            return
        
        message = (
            f"*Circuit Breaker Triggered*\n"
            f"Trading has been automatically halted.\n"
            f"Reason: {reason}"
        )
        
        await self.send_alert(message, 'CRITICAL')
    
    async def alert_significant_pnl(self, pnl_data: Dict):
        """Alert on significant P&L change"""
        if 'significant_pnl' not in self.alert_on:
            return
        
        pnl = pnl_data.get('pnl', 0)
        pnl_pct = pnl_data.get('pnl_pct', 0)
        
        emoji = '📈' if pnl > 0 else '📉'
        
        message = (
            f"{emoji} *Significant P&L Change*\n"
            f"P&L: ${pnl:,.2f} ({pnl_pct:.2%})\n"
            f"Position: {pnl_data.get('symbol', 'N/A')}\n"
            f"Strategy: {pnl_data.get('strategy', 'N/A')}"
        )
        
        level = 'INFO' if pnl > 0 else 'WARNING'
        await self.send_alert(message, level)
    
    async def alert_system_status(self, status: str, details: str = ''):
        """Alert on system status change"""
        message = (
            f"*System Status Change*\n"
            f"Status: {status}\n"
            f"{details}"
        )
        
        await self.send_alert(message, 'INFO')
