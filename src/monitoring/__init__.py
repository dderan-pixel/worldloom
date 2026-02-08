"""
Monitoring Module

Web dashboard, alerts, and health monitoring.
"""

from .dashboard import create_dashboard_app
from .telegram_alerts import TelegramAlerter

__all__ = [
    'create_dashboard_app',
    'TelegramAlerter'
]
