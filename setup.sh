#!/bin/bash
# PredictX MVP Setup Script
# Run this to set up the entire project

set -e

echo "🚀 Setting up PredictX MVP..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this script from the project root"
    exit 1
fi

echo ""
echo "📦 Step 1: Installing Node dependencies..."
npm install

echo ""
echo "🔨 Step 2: Installing Foundry..."
if ! command -v forge &> /dev/null; then
    echo "Foundry not found. Installing..."
    curl -L https://foundry.paradigm.xyz | bash
    export PATH="$HOME/.foundry/bin:$PATH"
    foundryup
else
    echo "✅ Foundry already installed"
fi

echo ""
echo "📚 Step 3: Installing smart contract dependencies..."
cd packages/contracts
if [ ! -d "lib/openzeppelin-contracts" ]; then
    forge install OpenZeppelin/openzeppelin-contracts --no-commit
else
    echo "✅ OpenZeppelin already installed"
fi

if [ ! -d "lib/forge-std" ]; then
    forge install foundry-rs/forge-std --no-commit
else
    echo "✅ forge-std already installed"
fi

echo ""
echo "🏗️  Step 4: Building contracts..."
forge build

echo ""
echo "🧪 Step 5: Running contract tests..."
forge test

cd ../..

echo ""
echo "🎯 Step 6: Building all packages..."
npm run build

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo ""
echo "  1. Start local blockchain (optional):"
echo "     anvil"
echo ""
echo "  2. Deploy contracts (optional):"
echo "     cd packages/contracts"
echo "     export PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
echo "     npm run deploy:local"
echo ""
echo "  3. Start development servers:"
echo "     npm run dev"
echo ""
echo "  4. Open browser:"
echo "     http://localhost:3000  (Frontend)"
echo "     http://localhost:3001  (API)"
echo ""
echo "📖 Read the documentation:"
echo "   - README.md - Full documentation"
echo "   - QUICKSTART.md - Quick start guide"
echo "   - CONTRACTS_SETUP.md - Contract deployment guide"
echo "   - STEP1_SUMMARY.md - Implementation summary"
echo ""
echo "Happy building! 🎉"
