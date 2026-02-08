"""
Data Layer Module

Handles real-time and historical market data ingestion from multiple exchanges.
Provides normalized data feeds and persistent storage.
"""

from .websocket_connector import WebSocketConnector
from .historical_data import HistoricalDataFetcher
from .data_normalizer import DataNormalizer
from .storage_manager import StorageManager

__all__ = [
    'WebSocketConnector',
    'HistoricalDataFetcher', 
    'DataNormalizer',
    'StorageManager'
]
