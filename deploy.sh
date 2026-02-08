#!/bin/bash
# Quick deployment script for PredictX
# This script helps deploy all components step by step

set -e

echo "🚀 PredictX Deployment Wizard"
echo "=============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}📝 Please edit .env file with your configuration before continuing!${NC}"
    exit 1
fi

# Load environment variables
source .env

echo "Select deployment target:"
echo "1) Deploy Smart Contracts (Base Sepolia)"
echo "2) Deploy Frontend (Vercel)"
echo "3) Deploy Backend (Railway)"
echo "4) Full Deploy (All components)"
echo "5) Verify Deployment"
echo ""
read -p "Enter your choice (1-5): " choice

deploy_contracts() {
    echo -e "${GREEN}📜 Deploying Smart Contracts...${NC}"
    
    if [ -z "$PRIVATE_KEY" ]; then
        echo -e "${RED}❌ PRIVATE_KEY not set in .env${NC}"
        exit 1
    fi
    
    if [ -z "$RPC_URL" ]; then
        echo -e "${RED}❌ RPC_URL not set in .env${NC}"
        exit 1
    fi
    
    cd packages/contracts
    
    # Install dependencies if needed
    if [ ! -d "lib/openzeppelin-contracts" ]; then
        echo "Installing Foundry dependencies..."
        forge install OpenZeppelin/openzeppelin-contracts --no-commit
        forge install foundry-rs/forge-std --no-commit
    fi
    
    echo "Building contracts..."
    forge build
    
    echo "Running tests..."
    forge test
    
    echo "Deploying to Base Sepolia..."
    forge script script/Deploy.s.sol:DeployScript \
        --rpc-url $RPC_URL \
        --broadcast \
        --verify \
        --etherscan-api-key $ETHERSCAN_API_KEY || true
    
    echo -e "${GREEN}✅ Contracts deployed!${NC}"
    echo -e "${YELLOW}📝 Don't forget to save the contract addresses!${NC}"
    
    cd ../..
}

deploy_frontend() {
    echo -e "${GREEN}🎨 Deploying Frontend...${NC}"
    
    cd apps/web
    
    # Check if vercel is installed
    if ! command -v vercel &> /dev/null; then
        echo "Installing Vercel CLI..."
        npm install -g vercel
    fi
    
    echo "Building frontend..."
    npm run build
    
    echo "Deploying to Vercel..."
    vercel --prod
    
    echo -e "${GREEN}✅ Frontend deployed!${NC}"
    
    cd ../..
}

deploy_backend() {
    echo -e "${GREEN}⚙️  Deploying Backend...${NC}"
    
    cd apps/api
    
    # Check if railway is installed
    if ! command -v railway &> /dev/null; then
        echo "Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    echo "Building backend..."
    npm run build
    
    echo "Deploying to Railway..."
    railway up
    
    echo -e "${GREEN}✅ Backend deployed!${NC}"
    
    cd ../..
}

verify_deployment() {
    echo -e "${GREEN}🔍 Verifying Deployment...${NC}"
    echo ""
    
    # Check contracts
    if [ ! -z "$VAULT_ADDRESS" ]; then
        echo "Checking contracts on Basescan..."
        echo "Vault: https://sepolia.basescan.org/address/$VAULT_ADDRESS"
    fi
    
    # Check frontend
    echo ""
    echo "Testing frontend..."
    read -p "Enter your frontend URL (e.g., https://predictx.vercel.app): " FRONTEND_URL
    if [ ! -z "$FRONTEND_URL" ]; then
        curl -I $FRONTEND_URL 2>/dev/null | head -n 1
    fi
    
    # Check backend
    echo ""
    echo "Testing backend API..."
    read -p "Enter your backend URL (e.g., https://api.predictx.com): " BACKEND_URL
    if [ ! -z "$BACKEND_URL" ]; then
        curl $BACKEND_URL/health 2>/dev/null || echo "Health check endpoint not available"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Verification complete!${NC}"
}

case $choice in
    1)
        deploy_contracts
        ;;
    2)
        deploy_frontend
        ;;
    3)
        deploy_backend
        ;;
    4)
        echo -e "${GREEN}🚀 Full deployment starting...${NC}"
        deploy_contracts
        echo ""
        deploy_frontend
        echo ""
        deploy_backend
        echo ""
        echo -e "${GREEN}✅ All components deployed!${NC}"
        ;;
    5)
        verify_deployment
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "=============================="
echo -e "${GREEN}🎉 Deployment process completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Update frontend environment variables with contract addresses"
echo "2. Update backend environment variables with contract addresses"
echo "3. Configure your custom domain DNS"
echo "4. Test the application end-to-end"
echo ""
echo "For detailed instructions, see DEPLOYMENT.md"
