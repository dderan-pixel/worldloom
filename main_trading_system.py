"""
Main Trading System Orchestrator

Coordinates all trading system components and manages the main event loop.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config_manager import ConfigManager
from src.data_layer import WebSocketConnector, HistoricalDataFetcher, DataNormalizer, StorageManager
from src.strategy_engine import MomentumStrategy, MeanReversionStrategy, PositionSizer, VolatilityRegimeDetector
from src.risk_management import RiskManager
from src.execution_engine import OrderRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TradingSystem:
    """
    Main trading system orchestrator
    
    Coordinates all components and manages the trading lifecycle.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize trading system
        
        Args:
            config_path: Path to configuration file
        """
        logger.info("=" * 60)
        logger.info("SD Trading System Starting")
        logger.info("=" * 60)
        
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        # Initialize components
        self.data_connector: Optional[WebSocketConnector] = None
        self.storage_manager: Optional[StorageManager] = None
        self.risk_manager: Optional[RiskManager] = None
        self.order_router: Optional[OrderRouter] = None
        
        self.strategies = []
        self.position_sizer: Optional[PositionSizer] = None
        self.volatility_detector: Optional[VolatilityRegimeDetector] = None
        
        # System state
        self.running = False
        self.mode = self.config.get('system.mode', 'paper_trading')
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Trading mode: {self.mode}")
    
    async def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing system components...")
            
            # Initialize storage
            storage_config = self.config.get('data.storage', {})
            if storage_config:
                self.storage_manager = StorageManager(storage_config)
                await self.storage_manager.connect()
                logger.info("✓ Storage manager initialized")
            
            # Initialize risk manager
            risk_config = self.config.get('risk', {})
            self.risk_manager = RiskManager(risk_config)
            logger.info("✓ Risk manager initialized")
            
            # Initialize order router
            execution_config = self.config.get('execution', {})
            execution_config['exchanges'] = self.config.get('exchanges', {})
            self.order_router = OrderRouter(execution_config)
            logger.info("✓ Order router initialized")
            
            # Initialize position sizer
            position_config = self.config.get('position_sizing', {})
            self.position_sizer = PositionSizer(position_config)
            logger.info("✓ Position sizer initialized")
            
            # Initialize volatility detector
            volatility_config = self.config.get('volatility', {})
            self.volatility_detector = VolatilityRegimeDetector(volatility_config)
            logger.info("✓ Volatility detector initialized")
            
            # Initialize strategies
            await self._initialize_strategies()
            
            # Initialize data connector
            ws_config = {}
            for exchange_id, exchange_config in self.config.get('exchanges', {}).items():
                if exchange_config.get('enabled', False):
                    ws_config[exchange_id] = exchange_config
            
            if ws_config:
                self.data_connector = WebSocketConnector(ws_config)
                self.data_connector.add_callback(self._handle_market_data)
                logger.info("✓ WebSocket connector initialized")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    async def _initialize_strategies(self):
        """Initialize trading strategies"""
        from src.strategy_engine.base_strategy import StrategyConfig
        
        strategies_config = self.config.get('strategies', {})
        
        # Momentum strategy
        if strategies_config.get('momentum', {}).get('enabled', False):
            momentum_config = StrategyConfig(
                name='momentum',
                **strategies_config['momentum']
            )
            momentum_strategy = MomentumStrategy(momentum_config)
            self.strategies.append(momentum_strategy)
            logger.info("✓ Momentum strategy initialized")
        
        # Mean reversion strategy
        if strategies_config.get('mean_reversion', {}).get('enabled', False):
            mr_config = StrategyConfig(
                name='mean_reversion',
                **strategies_config['mean_reversion']
            )
            mr_strategy = MeanReversionStrategy(mr_config)
            self.strategies.append(mr_strategy)
            logger.info("✓ Mean reversion strategy initialized")
        
        logger.info(f"Loaded {len(self.strategies)} strategies")
    
    async def _handle_market_data(self, data: dict):
        """
        Handle incoming market data
        
        Args:
            data: Market data from WebSocket
        """
        try:
            # Store data if storage is enabled
            if self.storage_manager and data.get('type') == 'trade':
                await self.storage_manager.save_trade(data)
            
            # Process data through strategies
            # Note: In production, you would aggregate data into OHLCV
            # before generating signals
            
        except Exception as e:
            logger.error(f"Error handling market data: {e}")
    
    async def run(self):
        """Main trading loop"""
        self.running = True
        
        try:
            await self.initialize()
            
            logger.info("=" * 60)
            logger.info("Trading System Running")
            logger.info("=" * 60)
            
            # Start WebSocket connections if available
            if self.data_connector:
                ws_task = asyncio.create_task(self.data_connector.connect_all())
            
            # Main loop
            while self.running:
                await asyncio.sleep(1)
                
                # Periodic tasks would go here
                # - Check positions
                # - Update risk metrics
                # - Generate signals
                # - Execute orders
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown system gracefully"""
        logger.info("Shutting down trading system...")
        
        self.running = False
        
        try:
            # Stop WebSocket connections
            if self.data_connector:
                await self.data_connector.stop_all()
            
            # Close order router connections
            if self.order_router:
                await self.order_router.close_all()
            
            # Close storage connections
            if self.storage_manager:
                await self.storage_manager.close()
            
            logger.info("Trading system shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SD Trading System')
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['paper', 'live'],
        help='Trading mode (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Initialize and run system
    system = TradingSystem(args.config)
    
    # Override mode if specified
    if args.mode:
        system.mode = 'paper_trading' if args.mode == 'paper' else 'live'
        system.config_manager.set('system.mode', system.mode)
    
    try:
        await system.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
