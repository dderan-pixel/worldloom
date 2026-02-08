"""
Storage Manager Module

Manages persistent storage of market data using PostgreSQL and Parquet files.
Provides efficient querying and data retrieval.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import asyncpg
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Hybrid storage manager using PostgreSQL and Parquet
    
    - PostgreSQL: Metadata, trades, orders, positions
    - Parquet: Historical OHLCV data for fast analytics
    """
    
    def __init__(self, config: Dict):
        """
        Initialize storage manager
        
        Args:
            config: Storage configuration with DB and file paths
        """
        self.config = config
        self.db_pool = None
        self.parquet_path = Path(config.get('parquet_path', './data/parquet'))
        self.parquet_path.mkdir(parents=True, exist_ok=True)
    
    async def connect(self):
        """Establish database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(
                host=self.config.get('db_host', 'localhost'),
                port=self.config.get('db_port', 5432),
                database=self.config.get('db_name', 'trading_db'),
                user=self.config.get('db_user', 'postgres'),
                password=self.config.get('db_password', ''),
                min_size=2,
                max_size=10
            )
            
            await self._init_schema()
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def _init_schema(self):
        """Initialize database schema"""
        async with self.db_pool.acquire() as conn:
            # Trades table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    exchange VARCHAR(50) NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    price DECIMAL(20, 8) NOT NULL,
                    quantity DECIMAL(20, 8) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    INDEX idx_trades_symbol_timestamp (symbol, timestamp)
                )
            """)
            
            # Orders table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    order_id VARCHAR(100) UNIQUE NOT NULL,
                    exchange VARCHAR(50) NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    order_type VARCHAR(20) NOT NULL,
                    price DECIMAL(20, 8),
                    quantity DECIMAL(20, 8) NOT NULL,
                    filled_quantity DECIMAL(20, 8) DEFAULT 0,
                    status VARCHAR(20) NOT NULL,
                    strategy VARCHAR(100),
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Positions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id SERIAL PRIMARY KEY,
                    exchange VARCHAR(50) NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    quantity DECIMAL(20, 8) NOT NULL,
                    entry_price DECIMAL(20, 8) NOT NULL,
                    current_price DECIMAL(20, 8),
                    unrealized_pnl DECIMAL(20, 8),
                    realized_pnl DECIMAL(20, 8) DEFAULT 0,
                    strategy VARCHAR(100),
                    opened_at TIMESTAMP NOT NULL,
                    closed_at TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'open',
                    UNIQUE(exchange, symbol, strategy, status)
                )
            """)
            
            # Portfolio snapshots table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id SERIAL PRIMARY KEY,
                    total_value DECIMAL(20, 8) NOT NULL,
                    cash_balance DECIMAL(20, 8) NOT NULL,
                    positions_value DECIMAL(20, 8) NOT NULL,
                    unrealized_pnl DECIMAL(20, 8) NOT NULL,
                    realized_pnl DECIMAL(20, 8) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Performance metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    strategy VARCHAR(100) NOT NULL,
                    total_return DECIMAL(10, 4),
                    sharpe_ratio DECIMAL(10, 4),
                    max_drawdown DECIMAL(10, 4),
                    win_rate DECIMAL(10, 4),
                    total_trades INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            logger.info("Database schema initialized")
    
    async def save_trade(self, trade: Dict):
        """Save trade to database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO trades (exchange, symbol, price, quantity, side, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, trade['exchange'], trade['symbol'], trade['price'], 
                trade['quantity'], trade['side'], trade['timestamp'])
    
    async def save_order(self, order: Dict):
        """Save order to database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO orders 
                (order_id, exchange, symbol, side, order_type, price, quantity, 
                 filled_quantity, status, strategy, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (order_id) DO UPDATE SET
                    filled_quantity = EXCLUDED.filled_quantity,
                    status = EXCLUDED.status,
                    updated_at = NOW()
            """, order['order_id'], order['exchange'], order['symbol'], 
                order['side'], order['order_type'], order.get('price'), 
                order['quantity'], order.get('filled_quantity', 0),
                order['status'], order.get('strategy'), order['timestamp'])
    
    async def get_orders(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Query orders with optional filters"""
        async with self.db_pool.acquire() as conn:
            query = "SELECT * FROM orders WHERE 1=1"
            params = []
            
            if filters:
                if 'symbol' in filters:
                    params.append(filters['symbol'])
                    query += f" AND symbol = ${len(params)}"
                
                if 'status' in filters:
                    params.append(filters['status'])
                    query += f" AND status = ${len(params)}"
                
                if 'strategy' in filters:
                    params.append(filters['strategy'])
                    query += f" AND strategy = ${len(params)}"
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def save_position(self, position: Dict):
        """Save or update position"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO positions 
                (exchange, symbol, side, quantity, entry_price, current_price,
                 unrealized_pnl, realized_pnl, strategy, opened_at, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (exchange, symbol, strategy, status) DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    current_price = EXCLUDED.current_price,
                    unrealized_pnl = EXCLUDED.unrealized_pnl,
                    realized_pnl = EXCLUDED.realized_pnl
            """, position['exchange'], position['symbol'], position['side'],
                position['quantity'], position['entry_price'], position.get('current_price'),
                position.get('unrealized_pnl', 0), position.get('realized_pnl', 0),
                position.get('strategy'), position['opened_at'], position.get('status', 'open'))
    
    async def get_positions(self, status: str = 'open') -> List[Dict]:
        """Get positions by status"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM positions WHERE status = $1",
                status
            )
            return [dict(row) for row in rows]
    
    def save_ohlcv_parquet(self, df: pd.DataFrame, exchange: str, symbol: str):
        """
        Save OHLCV data to Parquet file
        
        Args:
            df: OHLCV DataFrame
            exchange: Exchange identifier
            symbol: Trading symbol
        """
        try:
            # Create directory structure
            symbol_safe = symbol.replace('/', '_')
            file_path = self.parquet_path / exchange / f"{symbol_safe}.parquet"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to Arrow Table
            table = pa.Table.from_pandas(df)
            
            # Write with compression
            pq.write_table(
                table, 
                file_path,
                compression='snappy',
                use_dictionary=True
            )
            
            logger.info(f"Saved {len(df)} rows to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save Parquet file: {e}")
            raise
    
    def load_ohlcv_parquet(
        self, 
        exchange: str, 
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Load OHLCV data from Parquet file
        
        Args:
            exchange: Exchange identifier
            symbol: Trading symbol
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            OHLCV DataFrame
        """
        try:
            symbol_safe = symbol.replace('/', '_')
            file_path = self.parquet_path / exchange / f"{symbol_safe}.parquet"
            
            if not file_path.exists():
                logger.warning(f"Parquet file not found: {file_path}")
                return pd.DataFrame()
            
            # Read with filters
            filters = []
            if start_date:
                filters.append(('timestamp', '>=', start_date))
            if end_date:
                filters.append(('timestamp', '<=', end_date))
            
            df = pq.read_table(
                file_path,
                filters=filters if filters else None
            ).to_pandas()
            
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load Parquet file: {e}")
            raise
    
    async def save_portfolio_snapshot(self, snapshot: Dict):
        """Save portfolio snapshot"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO portfolio_snapshots 
                (total_value, cash_balance, positions_value, unrealized_pnl, 
                 realized_pnl, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, snapshot['total_value'], snapshot['cash_balance'],
                snapshot['positions_value'], snapshot['unrealized_pnl'],
                snapshot['realized_pnl'], snapshot['timestamp'])
    
    async def get_portfolio_history(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get portfolio value history"""
        async with self.db_pool.acquire() as conn:
            query = "SELECT * FROM portfolio_snapshots WHERE 1=1"
            params = []
            
            if start_date:
                params.append(start_date)
                query += f" AND timestamp >= ${len(params)}"
            
            if end_date:
                params.append(end_date)
                query += f" AND timestamp <= ${len(params)}"
            
            query += " ORDER BY timestamp"
            
            rows = await conn.fetch(query, *params)
            return pd.DataFrame([dict(row) for row in rows])
    
    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database connections closed")
