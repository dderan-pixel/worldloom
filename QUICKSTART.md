# Quick Start Guide

Get PredictX running in 5 minutes.

## Step 1: Install Dependencies

```bash
# Install root dependencies
npm install

# Install Foundry (for smart contracts)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

## Step 2: Set Up Contracts

```bash
cd packages/contracts

# Install contract dependencies
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge install foundry-rs/forge-std --no-commit

# Build contracts
forge build

# Run tests
forge test

cd ../..
```

## Step 3: Build All Packages

```bash
# From root directory
npm run build
```

## Step 4: Start Development Servers

### Option A: Start Everything at Once

```bash
npm run dev
```

This starts:
- Web app on http://localhost:3000
- API server on http://localhost:3001

### Option B: Start Services Individually

Terminal 1 - Frontend:
```bash
cd apps/web
npm run dev
```

Terminal 2 - Backend:
```bash
cd apps/api
npm run dev
```

Terminal 3 - Local Blockchain (optional):
```bash
anvil
```

## Step 5: Deploy Contracts (Optional)

For local development:

```bash
# Terminal 3: Start Anvil
anvil

# Terminal 4: Deploy contracts
cd packages/contracts
export PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
npm run deploy:local
```

For Base Sepolia testnet:

```bash
# Set up environment
export PRIVATE_KEY=your_private_key
export RPC_URL=https://sepolia.base.org
export ETHERSCAN_API_KEY=your_key

# Deploy
npm run deploy:testnet
```

## Step 6: Open the App

Visit http://localhost:3000 to see the PredictX interface!

## Verify Installation

### Check Contracts
```bash
cd packages/contracts
forge test
# Should see: "ok. 8 passed"
```

### Check Frontend
```bash
cd apps/web
npm run build
# Should compile successfully
```

### Check Backend
```bash
cd apps/api
npm run build
# Should compile successfully
```

## Common Issues

**"forge: command not found"**
- Run: `curl -L https://foundry.paradigm.xyz | bash && foundryup`

**"Module not found"**
- Run: `npm install` in root directory

**"Port already in use"**
- Change port in package.json scripts or kill existing process

**Build errors**
- Clear caches: `npm run clean && npm install && npm run build`

## What's Next?

1. Read [README.md](./README.md) for architecture details
2. Review contracts in [packages/contracts/src/](./packages/contracts/src/)
3. Check [CONTRACTS_SETUP.md](./packages/contracts/CONTRACTS_SETUP.md) for deployment guide
4. Explore frontend pages in [apps/web/app/](./apps/web/app/)
5. Review API routes in [apps/api/src/routes/](./apps/api/src/routes/)

## Development Workflow

1. Make changes to contracts → `forge test` → `forge build`
2. Make changes to shared types → `npm run build` in packages/shared
3. Make changes to API → Hot reload automatically via tsx watch
4. Make changes to frontend → Hot reload automatically via Next.js

Happy building! 🚀
