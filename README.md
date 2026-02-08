# SD - Production-Grade Multi-Exchange Algorithmic Trading System

A modular, institutional-grade cryptocurrency trading platform designed for reliability, scalability, and risk management.

## 🏗️ Architecture Overview

SD is built with a clean separation of concerns across multiple layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring & Control                      │
│         (FastAPI Dashboard, Telegram Alerts, Health)        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Portfolio Management                      │
│         (Valuation, P&L Tracking, Attribution)              │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Execution Engine                          │
│    (Smart Order Routing, TWAP/VWAP, Retry Logic)           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Risk Management Engine                     │
│    (Exposure Limits, Drawdown Guard, Circuit Breaker)      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Strategy Engine                           │
│  (Momentum, Mean Reversion, Position Sizing, Volatility)   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  (WebSocket Streams, Historical Data, PostgreSQL, Parquet) │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Key Features

### Data Layer
- **Real-time Market Data**: WebSocket connections to Binance, Bybit, and OKX
- **Historical Data**: Fetch and store OHLCV data for backtesting
- **Data Normalization**: Unified format across all exchanges
- **Hybrid Storage**: PostgreSQL for transactions, Parquet for analytics

### Strategy Engine
- **Pluggable Framework**: Easy to add custom strategies
- **Built-in Strategies**:
  - Momentum (RSI, MACD, Moving Averages)
  - Mean Reversion (Bollinger Bands, Z-Score)
- **Volatility Regime Detection**: Adjust parameters based on market conditions
- **Dynamic Position Sizing**: Kelly Criterion, volatility-based, risk-based

### Risk Management
- **Portfolio Exposure Limits**: Control total exposure and position concentration
- **Drawdown Protection**: Daily, weekly, and overall drawdown limits
- **Circuit Breaker**: Automatic halt on extreme volatility or rapid losses
- **Dynamic Leverage**: Adjust leverage based on volatility regime

### Execution Engine
- **Smart Order Routing**: Routes to exchange with best liquidity and fees
- **Execution Algorithms**: TWAP, VWAP for large orders
- **Failover Logic**: Automatic retry on backup exchanges
- **Slippage Control**: Monitor and limit execution slippage

### Portfolio Management
- **Real-time Valuation**: Track portfolio value across exchanges
- **P&L Tracking**: Realized and unrealized profit/loss
- **Performance Attribution**: Analyze returns by strategy
- **Allocation Optimizer**: Rebalance portfolio based on strategy performance

### Monitoring & Control
- **Web Dashboard**: Real-time monitoring via FastAPI
- **Telegram Alerts**: Instant notifications for important events
- **Health Monitoring**: Heartbeat system for system health
- **Emergency Kill-Switch**: Immediately halt all trading

### Backtesting & Simulation
- **Vectorized Engine**: Fast backtesting on historical data
- **Walk-Forward Testing**: Avoid overfitting with proper validation
- **Monte Carlo Simulation**: Assess strategy robustness
- **Performance Analytics**: Sharpe ratio, drawdown, win rate, etc.

## 📦 Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (optional, for persistent storage)
- Docker (optional, for containerized deployment)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/sd.git
cd sd
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. **Setup database (optional)**
```bash
# Create PostgreSQL database
createdb trading_db

# The system will auto-create tables on first run
```

## ⚙️ Configuration

Edit `config/config.yaml` to customize:

- **Exchange Settings**: API keys, enabled exchanges, trading pairs
- **Strategy Parameters**: Timeframes, risk limits, indicator settings
- **Risk Management**: Drawdown limits, exposure caps, leverage
- **Execution Settings**: Order types, slippage tolerance, routing
- **Monitoring**: Dashboard, Telegram alerts, logging

### Environment Variables

Required variables in `.env`:
```bash
# Exchange API Keys
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
BYBIT_API_KEY=your_bybit_key
BYBIT_API_SECRET=your_bybit_secret
OKX_API_KEY=your_okx_key
OKX_API_SECRET=your_okx_secret

# Database (optional)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=your_password

# Telegram (optional)
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🎯 Usage

### Paper Trading (Recommended for Testing)

```bash
python main_trading_system.py --mode paper
```

### Live Trading (Use with Caution)

```bash
python main_trading_system.py --mode live
```

### Backtesting

```bash
python backtesting_runner.py --strategy momentum --start 2023-01-01 --end 2024-01-01
```

### Start Web Dashboard

```bash
uvicorn src.monitoring.dashboard:app --host 0.0.0.0 --port 8000
```

Access dashboard at: http://localhost:8000

## 📊 Monitoring

### Web Dashboard
- Real-time P&L and portfolio value
- Active positions and orders
- Strategy performance metrics
- Risk metrics and exposure
- Recent trade history

### Telegram Alerts
Configure Telegram bot to receive alerts for:
- Trade executions
- Risk violations
- Circuit breaker triggers
- Significant P&L changes

## 🐳 Docker Deployment

### Build and run with Docker Compose

```bash
docker-compose up -d
```

This starts:
- Trading system backend
- PostgreSQL database
- Web dashboard
- Monitoring services

### Production Deployment

For production, consider:
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Set up monitoring (Prometheus, Grafana)
- Configure log aggregation (ELK stack)
- Use managed database (AWS RDS, Google Cloud SQL)
- Set up alerts and notifications

## 📚 Module Documentation

### Data Layer (`src/data_layer/`)
- `websocket_connector.py`: Real-time market data streams
- `historical_data.py`: Historical data fetching
- `data_normalizer.py`: Data cleaning and normalization
- `storage_manager.py`: Database and file storage

### Strategy Engine (`src/strategy_engine/`)
- `base_strategy.py`: Abstract strategy interface
- `momentum_strategy.py`: Momentum-based trading
- `mean_reversion_strategy.py`: Mean reversion trading
- `volatility_regime.py`: Market regime detection
- `position_sizer.py`: Dynamic position sizing

### Risk Management (`src/risk_management/`)
- `risk_manager.py`: Central risk coordination
- `exposure_calculator.py`: Portfolio exposure tracking
- `drawdown_guard.py`: Drawdown protection
- `circuit_breaker.py`: Emergency halt system

### Execution Engine (`src/execution_engine/`)
- `order_router.py`: Smart order routing
- `execution_algorithms.py`: TWAP/VWAP execution
- `order_manager.py`: Order lifecycle management

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run specific module tests
pytest tests/test_strategy_engine.py

# Run with coverage
pytest --cov=src tests/
```

## 📈 Performance Metrics

The system tracks comprehensive metrics:
- **Returns**: Total, annualized, by strategy
- **Risk Metrics**: Sharpe ratio, Sortino ratio, max drawdown
- **Win Rate**: Percentage of profitable trades
- **P&L**: Realized and unrealized profit/loss
- **Exposure**: Gross and net exposure by asset
- **Volatility**: Portfolio and position-level volatility

## ⚠️ Risk Disclosure

**This is experimental trading software. Use at your own risk.**

- Always start with paper trading
- Test thoroughly before using real funds
- Never invest more than you can afford to lose
- Cryptocurrency trading is highly volatile
- Past performance does not guarantee future results
- The authors are not responsible for any financial losses

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [CCXT](https://github.com/ccxt/ccxt) - Cryptocurrency exchange integration
- [FastAPI](https://fastapi.tiangolo.com/) - Web dashboard
- [Pandas](https://pandas.pydata.org/) - Data analysis
- [PostgreSQL](https://www.postgresql.org/) - Data storage
- [asyncio](https://docs.python.org/3/library/asyncio.html) - Async operations

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: GitHub Issues
- Discussions: GitHub Discussions

---

**Built by quantitative trading professionals for institutional-grade performance.**
