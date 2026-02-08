# PredictX Deployment Guide

Complete guide to deploy PredictX to production with your own domain.

## Table of Contents

1. [Quick Deploy (Recommended)](#quick-deploy-recommended)
2. [Deploy Smart Contracts](#deploy-smart-contracts)
3. [Deploy Frontend (Vercel)](#deploy-frontend-vercel)
4. [Deploy Backend API](#deploy-backend-api)
5. [Custom Domain Setup](#custom-domain-setup)
6. [Environment Variables](#environment-variables)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Quick Deploy (Recommended)

The fastest way to deploy PredictX with a custom domain:

### Option 1: Full Automated Deploy

```bash
# 1. Clone and setup
git clone https://github.com/dderan-pixel/worldloom.git
cd worldloom
./setup.sh

# 2. Deploy contracts to Base Sepolia
cd packages/contracts
export PRIVATE_KEY=your_private_key
export RPC_URL=https://sepolia.base.org
npm run deploy:testnet

# 3. Deploy frontend to Vercel
cd ../../apps/web
vercel --prod

# 4. Deploy backend to Railway
cd ../api
railway up
```

### Option 2: Platform-Specific

**Frontend**: Vercel (free, automatic SSL, custom domain)
**Backend**: Railway or Render (free tier available)
**Contracts**: Base Sepolia testnet (free with faucet)

---

## Deploy Smart Contracts

### Prerequisites

1. **Get Base Sepolia ETH**
   - Visit: https://www.alchemy.com/faucets/base-sepolia
   - Or: https://faucet.quicknode.com/base/sepolia
   - You need ~0.1 ETH for deployment

2. **Get Etherscan API Key**
   - Visit: https://basescan.org/
   - Create account and get API key for verification

### Deploy to Base Sepolia

```bash
cd packages/contracts

# Set environment variables
export PRIVATE_KEY=your_wallet_private_key_without_0x
export RPC_URL=https://sepolia.base.org
export ETHERSCAN_API_KEY=your_etherscan_api_key

# Deploy contracts
npm run deploy:testnet
```

**Expected output:**
```
Vault deployed at: 0x1234...
MarketManager deployed at: 0x5678...
OutcomeToken deployed at: 0x9abc...
Settlement deployed at: 0xdef0...
FeeCollector deployed at: 0x1111...
```

**Save these addresses** - you'll need them for frontend/backend configuration.

### Verify on Basescan

After deployment, verify your contracts are live:
1. Visit: https://sepolia.basescan.org/
2. Search for your contract addresses
3. Verify the source code (automatically done during deployment)

---

## Deploy Frontend (Vercel)

Vercel is the recommended platform for Next.js deployment with free SSL and custom domains.

### Method 1: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to web app
cd apps/web

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

### Method 2: Deploy via GitHub (Recommended)

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect to Vercel**
   - Visit: https://vercel.com
   - Click "New Project"
   - Import your GitHub repository
   - Select "apps/web" as root directory

3. **Configure Build Settings**
   - Framework Preset: **Next.js**
   - Root Directory: **apps/web**
   - Build Command: `npm run build`
   - Output Directory: `.next`

4. **Add Environment Variables** (in Vercel dashboard)
   ```env
   NEXT_PUBLIC_API_URL=https://your-api-domain.com
   NEXT_PUBLIC_CHAIN_ID=84532
   NEXT_PUBLIC_VAULT_ADDRESS=0x...
   NEXT_PUBLIC_MARKET_MANAGER_ADDRESS=0x...
   NEXT_PUBLIC_OUTCOME_TOKEN_ADDRESS=0x...
   NEXT_PUBLIC_SETTLEMENT_ADDRESS=0x...
   NEXT_PUBLIC_FEE_COLLECTOR_ADDRESS=0x...
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes for build
   - Your site will be live at: `https://your-project.vercel.app`

### Add Custom Domain to Vercel

1. **In Vercel Dashboard**
   - Go to your project
   - Settings → Domains
   - Add your domain: `predictx.com` or `www.predictx.com`

2. **Configure DNS** (at your domain registrar)
   
   For apex domain (predictx.com):
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   ```
   
   For www subdomain:
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

3. **Wait for DNS Propagation** (5-30 minutes)
   - Vercel automatically provisions SSL certificate
   - Your site will be live at your custom domain with HTTPS

---

## Deploy Backend API

### Option 1: Railway (Recommended)

Railway offers free tier and easy deployment.

#### Setup Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Navigate to API
cd apps/api

# Initialize project
railway init

# Deploy
railway up
```

#### Configure Railway

1. **Add Environment Variables** (in Railway dashboard)
   ```env
   PORT=3001
   CORS_ORIGIN=https://your-frontend-domain.com
   NODE_ENV=production
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   RPC_URL=https://sepolia.base.org
   PRIVATE_KEY=your_operator_private_key
   VAULT_ADDRESS=0x...
   MARKET_MANAGER_ADDRESS=0x...
   SETTLEMENT_ADDRESS=0x...
   ```

2. **Get Your API URL**
   - Railway provides: `https://your-app.railway.app`
   - Update frontend NEXT_PUBLIC_API_URL with this

3. **Add Custom Domain**
   - Railway Dashboard → Settings → Domains
   - Add `api.predictx.com`
   - Configure DNS:
     ```
     Type: CNAME
     Name: api
     Value: your-app.railway.app
     ```

### Option 2: Render

```bash
# Create render.yaml in apps/api/
cat > apps/api/render.yaml << EOF
services:
  - type: web
    name: predictx-api
    env: node
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - key: NODE_ENV
        value: production
EOF

# Push to GitHub and connect in Render dashboard
```

### Option 3: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Navigate to API
cd apps/api

# Launch app
fly launch

# Deploy
fly deploy

# Set environment variables
fly secrets set CORS_ORIGIN=https://your-domain.com
fly secrets set DATABASE_URL=postgresql://...
```

### Option 4: Docker + VPS

If you have your own server:

```bash
# Build Docker image
cd apps/api
docker build -t predictx-api .

# Run container
docker run -d \
  -p 3001:3001 \
  -e CORS_ORIGIN=https://your-domain.com \
  -e DATABASE_URL=postgresql://... \
  --name predictx-api \
  predictx-api

# Or use docker-compose
docker-compose up -d
```

---

## Custom Domain Setup

### Full Setup Example

Let's say you own `predictx.com`:

#### 1. Configure DNS Records

At your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.):

```
# Frontend (Vercel)
Type: A,     Name: @,    Value: 76.76.21.21
Type: CNAME, Name: www,  Value: cname.vercel-dns.com

# API (Railway/Render/etc)
Type: CNAME, Name: api,  Value: your-api-host.railway.app

# Optional: Status page
Type: CNAME, Name: status, Value: stats.uptimerobot.com
```

#### 2. Update Environment Variables

**Frontend (.env.local or Vercel):**
```env
NEXT_PUBLIC_API_URL=https://api.predictx.com
```

**Backend (.env or Railway/Render):**
```env
CORS_ORIGIN=https://predictx.com,https://www.predictx.com
```

#### 3. Verify Setup

```bash
# Check DNS propagation
dig predictx.com
dig www.predictx.com
dig api.predictx.com

# Test endpoints
curl https://predictx.com
curl https://api.predictx.com/health
```

### Using Cloudflare (Optional but Recommended)

Cloudflare provides free SSL, CDN, and DDoS protection:

1. **Add Site to Cloudflare**
   - Visit: https://www.cloudflare.com/
   - Add your domain
   - Update nameservers at your registrar

2. **Configure DNS in Cloudflare**
   - Same records as above
   - Enable "Proxied" (orange cloud) for frontend
   - Use "DNS only" (gray cloud) for API if using Railway/Render SSL

3. **SSL/TLS Settings**
   - SSL/TLS → Overview → Full (strict)
   - Edge Certificates → Always Use HTTPS: ON

---

## Environment Variables

### Complete Environment Setup

#### Frontend (apps/web/.env.local)

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://api.predictx.com

# Blockchain Configuration
NEXT_PUBLIC_CHAIN_ID=84532
NEXT_PUBLIC_RPC_URL=https://sepolia.base.org

# Contract Addresses (from deployment)
NEXT_PUBLIC_VAULT_ADDRESS=0x...
NEXT_PUBLIC_MARKET_MANAGER_ADDRESS=0x...
NEXT_PUBLIC_OUTCOME_TOKEN_ADDRESS=0x...
NEXT_PUBLIC_SETTLEMENT_ADDRESS=0x...
NEXT_PUBLIC_FEE_COLLECTOR_ADDRESS=0x...

# Optional: Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

#### Backend (apps/api/.env)

```env
# Server Configuration
NODE_ENV=production
PORT=3001
CORS_ORIGIN=https://predictx.com,https://www.predictx.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/predictx
REDIS_URL=redis://host:6379

# Blockchain
RPC_URL=https://sepolia.base.org
PRIVATE_KEY=your_operator_private_key_for_settlement

# Contract Addresses
VAULT_ADDRESS=0x...
MARKET_MANAGER_ADDRESS=0x...
OUTCOME_TOKEN_ADDRESS=0x...
SETTLEMENT_ADDRESS=0x...

# Optional: Monitoring
SENTRY_DSN=https://...
LOG_LEVEL=info
```

---

## SSL/HTTPS Setup

### Automatic SSL (Recommended)

Both Vercel and Railway/Render provide automatic SSL:

1. **Vercel**: Automatic Let's Encrypt certificates
2. **Railway**: Automatic SSL for custom domains
3. **Render**: Automatic SSL for custom domains

No additional configuration needed!

### Manual SSL (VPS/Docker)

If hosting on your own server:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d predictx.com -d www.predictx.com -d api.predictx.com

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

---

## Monitoring & Maintenance

### 1. Uptime Monitoring

**UptimeRobot** (Free):
```
Monitor: https://predictx.com
Monitor: https://api.predictx.com/health
Alert: Email when down
```

### 2. Error Tracking

**Sentry** (Free tier):
```bash
# Install in frontend
npm install @sentry/nextjs

# Install in backend
npm install @sentry/node
```

### 3. Analytics

**Vercel Analytics** (Built-in):
- Automatically enabled in Vercel projects

**Google Analytics**:
```typescript
// Add to apps/web/app/layout.tsx
import { GoogleAnalytics } from '@next/third-parties/google'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>{children}</body>
      <GoogleAnalytics gaId="G-XXXXXXXXXX" />
    </html>
  )
}
```

### 4. Database Backups

**Automated Backups**:
- Railway: Automatic backups (paid plans)
- Render: Automatic backups (PostgreSQL)
- Manual: Set up daily pg_dump cron job

### 5. Log Monitoring

```bash
# Vercel logs
vercel logs

# Railway logs
railway logs

# Docker logs
docker logs predictx-api
```

---

## Production Checklist

Before going live:

- [ ] Smart contracts deployed and verified on Basescan
- [ ] Frontend deployed with custom domain and SSL
- [ ] Backend deployed with custom domain and SSL
- [ ] All environment variables configured
- [ ] DNS records propagated (check with `dig`)
- [ ] HTTPS working on all domains
- [ ] API health check responding: `/health`
- [ ] CORS configured correctly
- [ ] Database connected and migrations run
- [ ] Redis/cache configured (if using)
- [ ] Error tracking set up (Sentry)
- [ ] Uptime monitoring configured
- [ ] Backup strategy in place
- [ ] Rate limiting configured on API
- [ ] Security headers configured
- [ ] Test wallet connections work
- [ ] Test end-to-end flows

---

## Quick Reference

### Deployment Commands

```bash
# Deploy contracts
cd packages/contracts && npm run deploy:testnet

# Deploy frontend (Vercel)
cd apps/web && vercel --prod

# Deploy backend (Railway)
cd apps/api && railway up

# Check deployments
vercel ls
railway status
```

### Common Issues

**Issue**: DNS not resolving
- **Fix**: Wait 30 minutes for propagation, check with `dig domain.com`

**Issue**: SSL certificate not provisioning
- **Fix**: Ensure DNS is correctly configured, wait for Vercel/Railway to provision

**Issue**: CORS errors
- **Fix**: Add frontend domain to CORS_ORIGIN in backend env vars

**Issue**: Contract calls failing
- **Fix**: Verify contract addresses in frontend env vars

---

## Cost Estimate

### Free Tier (Perfect for MVP)

- **Frontend (Vercel)**: Free (100GB bandwidth/month)
- **Backend (Railway)**: Free ($5 credit/month)
- **Database (Supabase)**: Free (500MB)
- **Redis (Upstash)**: Free (10K commands/day)
- **Domain**: $10-15/year
- **Blockchain**: Free (testnet)

**Total**: ~$10-15/year for domain only!

### Production Scale (~1000 users)

- **Frontend (Vercel Pro)**: $20/month
- **Backend (Railway)**: $20/month
- **Database (Railway)**: $25/month
- **Redis (Railway)**: $10/month
- **Domain**: $10-15/year
- **Monitoring**: Free (UptimeRobot + Sentry free tier)

**Total**: ~$75-80/month

---

## Support

For deployment issues:
- Check logs: `vercel logs` / `railway logs`
- Vercel Support: https://vercel.com/support
- Railway Discord: https://railway.app/discord
- GitHub Issues: https://github.com/dderan-pixel/worldloom/issues

---

## Next Steps

After deployment:
1. Test all user flows on production
2. Set up monitoring and alerts
3. Configure rate limiting
4. Add analytics
5. Set up CI/CD for automatic deployments
6. Create staging environment
7. Plan for mainnet migration

🎉 Congratulations! Your PredictX platform is now live on your custom domain!
