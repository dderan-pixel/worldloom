"""
Configuration Management Module

Centralized configuration for the trading system.
"""

import os
import yaml
import json
from typing import Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration manager for trading system"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or os.getenv(
            'TRADING_CONFIG',
            'config/config.yaml'
        )
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
            
            with open(config_file, 'r') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                elif self.config_path.endswith('.json'):
                    config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {self.config_path}")
            
            # Override with environment variables
            config = self._apply_env_overrides(config)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'system': {
                'mode': 'paper_trading',  # paper_trading or live
                'log_level': 'INFO'
            },
            'exchanges': {},
            'data': {},
            'strategies': {},
            'risk': {},
            'execution': {},
            'portfolio': {},
            'monitoring': {}
        }
    
    def _apply_env_overrides(self, config: Dict) -> Dict:
        """Apply environment variable overrides"""
        # Exchange API keys
        for exchange in ['binance', 'bybit', 'okx']:
            api_key = os.getenv(f'{exchange.upper()}_API_KEY')
            api_secret = os.getenv(f'{exchange.upper()}_API_SECRET')
            
            if api_key and api_secret:
                if 'exchanges' not in config:
                    config['exchanges'] = {}
                if exchange not in config['exchanges']:
                    config['exchanges'][exchange] = {}
                
                config['exchanges'][exchange]['api_key'] = api_key
                config['exchanges'][exchange]['api_secret'] = api_secret
        
        # Database settings
        if os.getenv('DB_HOST'):
            if 'data' not in config:
                config['data'] = {}
            if 'storage' not in config['data']:
                config['data']['storage'] = {}
            
            config['data']['storage']['db_host'] = os.getenv('DB_HOST')
            config['data']['storage']['db_port'] = int(os.getenv('DB_PORT', 5432))
            config['data']['storage']['db_name'] = os.getenv('DB_NAME', 'trading_db')
            config['data']['storage']['db_user'] = os.getenv('DB_USER', 'postgres')
            config['data']['storage']['db_password'] = os.getenv('DB_PASSWORD', '')
        
        # Telegram
        if os.getenv('TELEGRAM_TOKEN'):
            if 'monitoring' not in config:
                config['monitoring'] = {}
            if 'telegram' not in config['monitoring']:
                config['monitoring']['telegram'] = {}
            
            config['monitoring']['telegram']['token'] = os.getenv('TELEGRAM_TOKEN')
            config['monitoring']['telegram']['chat_id'] = os.getenv('TELEGRAM_CHAT_ID')
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, path: str = None):
        """Save configuration to file"""
        save_path = path or self.config_path
        
        try:
            with open(save_path, 'w') as f:
                if save_path.endswith('.yaml') or save_path.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False)
                elif save_path.endswith('.json'):
                    json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
