# Smart Contracts Setup Guide

This guide helps you set up and test the PredictX smart contracts using Foundry.

## Prerequisites

1. **Install Foundry**
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```

2. **Verify Installation**
   ```bash
   forge --version
   cast --version
   anvil --version
   ```

## Initial Setup

### 1. Install Dependencies

Navigate to the contracts package and install OpenZeppelin contracts:

```bash
cd packages/contracts

# Install OpenZeppelin Contracts
forge install OpenZeppelin/openzeppelin-contracts --no-commit

# Install Forge Standard Library
forge install foundry-rs/forge-std --no-commit
```

### 2. Build Contracts

```bash
forge build
```

You should see output like:
```
[⠊] Compiling...
[⠒] Compiling 25 files with Solc 0.8.20
[⠑] Solc 0.8.20 finished in 2.34s
Compiler run successful!
```

### 3. Run Tests

```bash
# Run all tests
forge test

# Run tests with verbosity (shows gas usage)
forge test -vv

# Run tests with stack traces
forge test -vvv

# Run specific test
forge test --match-test testDepositUSDC
```

Expected output:
```
[⠊] Compiling...
No files changed, compilation skipped

Ran 8 tests for test/PredictX.t.sol:PredictXTest
[PASS] testCreateMarket() (gas: 123456)
[PASS] testDepositETH() (gas: 54321)
[PASS] testDepositUSDC() (gas: 67890)
...
Suite result: ok. 8 passed; 0 failed; 0 skipped;
```

## Local Development

### 1. Start Local Network

In a separate terminal, start Anvil (local Ethereum node):

```bash
anvil
```

This starts a local node at `http://localhost:8545` with 10 pre-funded accounts.

### 2. Deploy Contracts

In your contracts directory:

```bash
# Set your private key (use one from Anvil output)
export PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# Deploy to local network
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url http://localhost:8545 \
  --broadcast
```

### 3. Interact with Contracts

Use Cast to interact with deployed contracts:

```bash
# Get contract code
cast code <CONTRACT_ADDRESS> --rpc-url http://localhost:8545

# Call a view function
cast call <VAULT_ADDRESS> "supportedAssets(address)(bool)" 0x0000000000000000000000000000000000000000

# Send a transaction
cast send <VAULT_ADDRESS> "depositETH()" \
  --value 1ether \
  --private-key $PRIVATE_KEY \
  --rpc-url http://localhost:8545
```

## Deploy to Base Sepolia Testnet

### 1. Get Testnet ETH

- Visit: https://www.alchemy.com/faucets/base-sepolia
- Or: https://faucet.quicknode.com/base/sepolia

### 2. Set Environment Variables

```bash
# Your deployer wallet private key (without 0x prefix)
export PRIVATE_KEY=your_private_key_here

# Base Sepolia RPC URL
export RPC_URL=https://sepolia.base.org

# Etherscan API key for verification
export ETHERSCAN_API_KEY=your_etherscan_api_key
```

### 3. Deploy

```bash
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url $RPC_URL \
  --broadcast \
  --verify \
  --etherscan-api-key $ETHERSCAN_API_KEY
```

### 4. Save Contract Addresses

The deployment will output addresses like:
```
Vault: 0x1234...
MarketManager: 0x5678...
OutcomeToken: 0x9abc...
Settlement: 0xdef0...
FeeCollector: 0x1111...
```

Save these addresses in your environment files:
- Frontend: `apps/web/.env.local`
- Backend: `apps/api/.env`

## Testing Checklist

After deployment, verify:

- [ ] Can deposit USDC to Vault
- [ ] Can deposit ETH to Vault
- [ ] Can withdraw from Vault
- [ ] Admin can create market
- [ ] Market shows as OPEN
- [ ] Settlement contract can mint outcome tokens
- [ ] Can resolve market after end time
- [ ] Can redeem winning shares
- [ ] Fees are collected properly

## Useful Commands

### Gas Optimization

```bash
# Run tests with gas report
forge test --gas-report

# Run specific test with detailed gas
forge test --match-test testSettleTrade -vvv --gas-report
```

### Coverage

```bash
# Generate coverage report
forge coverage

# Generate detailed HTML report
forge coverage --report lcov
genhtml lcov.info -o coverage --branch-coverage
```

### Code Size

```bash
# Check contract sizes
forge build --sizes
```

### Format Code

```bash
# Format Solidity files
forge fmt
```

## Troubleshooting

### "forge: command not found"

Install Foundry:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### "Could not find artifact"

Build the contracts first:
```bash
forge build
```

### "Failed to resolve imports"

Install dependencies:
```bash
forge install
```

### Gas too high

Optimize your contracts in `foundry.toml`:
```toml
optimizer = true
optimizer_runs = 200
```

### Reverted transactions

Run with verbosity to see revert reasons:
```bash
forge test -vvvv
```

## Next Steps

1. Add USDC support to Vault (get testnet USDC address)
2. Implement market creation on frontend
3. Set up backend matching engine
4. Test full trade flow end-to-end
5. Audit contracts before mainnet

## Resources

- Foundry Book: https://book.getfoundry.sh/
- OpenZeppelin: https://docs.openzeppelin.com/contracts/
- Base Docs: https://docs.base.org/
- Solidity Docs: https://docs.soliditylang.org/
