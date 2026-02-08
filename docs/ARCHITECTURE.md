# SD Trading System - Architecture Documentation

## System Overview

SD is a production-grade, modular algorithmic trading system designed for cryptocurrency markets. It provides institutional-level reliability, comprehensive risk management, and extensive monitoring capabilities.

## Architecture Layers

### 1. Data Layer
- WebSocket Connector - Real-time market data streams
- Historical Data Fetcher - OHLCV data retrieval
- Data Normalizer - Exchange-specific data format conversion
- Storage Manager - PostgreSQL + Parquet storage

### 2. Strategy Engine
- Base Strategy - Abstract base class
- Momentum Strategy - RSI, MACD, Moving Averages
- Mean Reversion Strategy - Bollinger Bands, Z-score
- Volatility Regime Detector - Market regime classification
- Position Sizer - Dynamic position sizing

### 3. Risk Management Engine
- Risk Manager - Central coordination
- Exposure Calculator - Portfolio exposure tracking
- Drawdown Guard - Drawdown monitoring and limits
- Circuit Breaker - Automatic trading halt

### 4. Execution Engine
- Order Router - Multi-exchange order routing

### 5. Portfolio Management
- Portfolio Manager - Real-time portfolio valuation
- Performance Analyzer - Risk-adjusted returns

### 6. Monitoring & Control
- Dashboard - FastAPI-based REST API
- Telegram Alerter - Notification system

### 7. Backtesting
- Backtesting Engine - Vectorized backtesting

## Key Design Principles

1. **Modularity** - Independent, replaceable components
2. **Safety First** - Multiple layers of risk management
3. **Performance** - Async operations, efficient storage
4. **Observability** - Structured logging, monitoring
5. **Configuration-Driven** - No hardcoded parameters

See README.md for detailed usage instructions.
