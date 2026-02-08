# PredictX - Hybrid Prediction Market MVP

A production-grade MVP of a crypto-only, hybrid prediction market platform with off-chain orderbook matching and on-chain custody, settlement, and withdrawals.

## Architecture

### Monorepo Structure
```
/apps/web              # Next.js frontend (App Router)
/apps/api              # Fastify backend API
/packages/contracts    # Solidity smart contracts (Foundry)
/packages/shared       # Shared TypeScript types and Zod schemas
```

### Smart Contracts

1. **Vault.sol** - Manages user deposits (USDC/ETH) with internal accounting
2. **MarketManager.sol** - Handles market lifecycle (creation, states, resolution)
3. **OutcomeToken.sol** - ERC1155 tokens for YES/NO outcome shares
4. **Settlement.sol** - Processes batch settlements from off-chain matching
5. **FeeCollector.sol** - Collects and manages trading fees

All contracts include:
- Role-based access control
- Pausable functionality
- Reentrancy guards
- Comprehensive event emissions

### Off-Chain Backend

- **Fastify** server with TypeScript
- **Redis** for in-memory orderbook (planned)
- **PostgreSQL** for persistent data (planned)
- **WebSocket** for real-time updates

### Frontend

- **Next.js 14+** with App Router
- **Tailwind CSS** for styling
- **RainbowKit + wagmi** for wallet connections (planned)
- **viem** for contract interactions

## Getting Started

### Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0
- Foundry (for contracts)

### Installation

```bash
# Install dependencies
npm install

# Build all packages
npm run build
```

## Development

### Contracts

```bash
# Navigate to contracts
cd packages/contracts

# Install Foundry dependencies (OpenZeppelin)
forge install OpenZeppelin/openzeppelin-contracts
forge install foundry-rs/forge-std

# Run tests
forge test

# Run tests with verbosity
forge test -vvv

# Deploy to local network (requires anvil running)
anvil  # In separate terminal
npm run deploy:local
```

### API Server

```bash
# Navigate to API
cd apps/api

# Start development server
npm run dev

# The API will run on http://localhost:3001
```

### Web Frontend

```bash
# Navigate to web app
cd apps/web

# Start development server
npm run dev

# The app will run on http://localhost:3000
```

### Run Everything

From the root:

```bash
# Start all services in development mode
npm run dev
```

## Deployment

### Deploy to Base Testnet

1. Set up your environment variables:

```bash
cp .env.example .env
# Edit .env with your values
```

Required variables:
- `PRIVATE_KEY` - Your deployer wallet private key
- `RPC_URL` - Base testnet RPC URL (https://sepolia.base.org)
- `ETHERSCAN_API_KEY` - For contract verification

2. Get testnet ETH from Base Sepolia faucet

3. Deploy contracts:

```bash
npm run contracts:deploy:testnet
```

The deployment script will:
- Deploy all 5 contracts
- Set up roles and permissions
- Add supported assets (ETH by default)
- Output all contract addresses

4. Save the contract addresses to your frontend/backend config

## Contract Addresses (Update After Deployment)

### Base Sepolia Testnet

- Vault: `0x...`
- MarketManager: `0x...`
- OutcomeToken: `0x...`
- Settlement: `0x...`
- FeeCollector: `0x...`

## Testing

### Contract Tests

```bash
cd packages/contracts
forge test
```

Tests include:
- Deposit/withdraw USDC and ETH
- Market creation and lifecycle
- Order matching and settlement
- Outcome token minting/burning
- Market resolution and redemption

## Key Features

### Core User Flows

1. **Connect Wallet** - RainbowKit integration (to be implemented)
2. **Deposit Collateral** - USDC or ETH into Vault
3. **Browse Markets** - View active prediction markets
4. **Place Orders** - YES/NO limit orders with price 0-1
5. **Trade Execution** - Off-chain matching engine
6. **View Positions** - Track outcome shares and P&L
7. **Market Resolution** - Oracle-based settlement
8. **Redeem & Withdraw** - Claim winnings and withdraw funds

### Security Features

- Role-based access control (Admin, Operator, Oracle)
- Pausable contracts for emergency stops
- Reentrancy protection on all state-changing functions
- SafeERC20 for token transfers
- Separate fee collector contract

## Configuration

### Contract Configuration

Edit `packages/contracts/script/Deploy.s.sol` to:
- Change default fee rate (100 = 1%)
- Add USDC token address for your network
- Adjust dispute windows

### API Configuration

Create `apps/api/.env`:
```
PORT=3001
CORS_ORIGIN=http://localhost:3000
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
RPC_URL=...
PRIVATE_KEY=...
```

### Frontend Configuration

Create `apps/web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_CHAIN_ID=84532
NEXT_PUBLIC_VAULT_ADDRESS=0x...
NEXT_PUBLIC_MARKET_MANAGER_ADDRESS=0x...
```

## Roadmap

### MVP (Current)
- ✅ Monorepo structure
- ✅ Core smart contracts
- ✅ Basic frontend pages
- ✅ API skeleton
- ⏳ Matching engine implementation
- ⏳ Settlement batcher
- ⏳ Wallet integration

### Future Enhancements
- EIP-712 signed orders (decentralized matching)
- Multi-market support
- Advanced order types
- Mobile app
- Decentralized oracle network
- Multi-chain deployment

## Contributing

This is an MVP implementation. Contributions are welcome!

## License

MIT

## Support

For issues or questions, please open a GitHub issue.
