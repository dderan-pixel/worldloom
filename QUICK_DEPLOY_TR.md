# PredictX Hızlı Deployment Kılavuzu

## Soru: "bunu nasıl bir domain e deploy ederim?"

## Cevap: 3 Basit Adımda Deploy Et!

### 1️⃣ Smart Contract'ları Deploy Et (5 dakika)

```bash
cd packages/contracts
export PRIVATE_KEY=cuzdan_private_key
export RPC_URL=https://sepolia.base.org
npm run deploy:testnet
```

**Adresler Kaydedilecek:**
- Vault: 0x...
- MarketManager: 0x...
- OutcomeToken: 0x...
- Settlement: 0x...
- FeeCollector: 0x...

### 2️⃣ Frontend'i Deploy Et (10 dakika)

**Vercel ile (Önerilen):**

```bash
cd apps/web
npm install -g vercel
vercel --prod
```

**Özel Domain Ekle:**
1. Vercel Dashboard → Domains
2. `predictx.com` ekle
3. DNS kayıtlarını ekle:
   - A kaydı: `@` → `76.76.21.21`
   - CNAME: `www` → `cname.vercel-dns.com`

### 3️⃣ Backend'i Deploy Et (10 dakika)

**Railway ile (Önerilen):**

```bash
cd apps/api
npm install -g @railway/cli
railway login
railway up
```

**Özel Domain Ekle:**
1. Railway Dashboard → Domains
2. `api.predictx.com` ekle
3. DNS kaydı:
   - CNAME: `api` → `uygulamaniz.railway.app`

---

## Otomatik Deploy

```bash
./deploy.sh
```

Menüden seçin:
1. Contract'ları deploy et
2. Frontend'i deploy et
3. Backend'i deploy et
4. Hepsini deploy et
5. Deployment'ı doğrula

---

## Tam Dokümantasyon

**Türkçe:** [DEPLOYMENT_TR.md](./DEPLOYMENT_TR.md)
**English:** [DEPLOYMENT.md](./DEPLOYMENT.md)

İçerik:
- Detaylı adım adım talimatlar
- Platform seçenekleri
- DNS yapılandırması
- SSL/HTTPS kurulumu
- Ortam değişkenleri
- Maliyet tahminleri
- İzleme ve bakım

---

## Gereksinimler

### Başlamadan Önce:

1. **Domain:** GoDaddy, Namecheap, vs.'den alın (~₺200-300/yıl)
2. **Testnet ETH:** Base Sepolia faucet'ten alın (ücretsiz)
3. **Hesaplar:**
   - Vercel hesabı (ücretsiz)
   - Railway hesabı (ücretsiz)

### Kurulu Olması Gerekenler:

```bash
# Node.js kontrol et
node --version  # >= 18.0.0

# NPM kontrol et
npm --version   # >= 9.0.0

# Foundry yükle (contract'lar için)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

---

## Deployment Akışı

```
┌─────────────────────┐
│ 1. Contract Deploy  │ → Base Sepolia Testnet
│    (~5 dakika)      │   Contract adresleri al
└─────────────────────┘
          ↓
┌─────────────────────┐
│ 2. Frontend Deploy  │ → Vercel
│    (~10 dakika)     │   predictx.com
└─────────────────────┘
          ↓
┌─────────────────────┐
│ 3. Backend Deploy   │ → Railway
│    (~10 dakika)     │   api.predictx.com
└─────────────────────┘
          ↓
┌─────────────────────┐
│ 4. DNS Yapılandır   │ → Domain kayıt şirketi
│    (~30 dakika)     │   Otomatik SSL
└─────────────────────┘
          ↓
┌─────────────────────┐
│ ✅ Canlı!           │ → https://predictx.com
└─────────────────────┘
```

---

## Ortam Değişkenleri (Hızlı Referans)

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=https://api.predictx.com
NEXT_PUBLIC_CHAIN_ID=84532
NEXT_PUBLIC_VAULT_ADDRESS=0x...
NEXT_PUBLIC_MARKET_MANAGER_ADDRESS=0x...
NEXT_PUBLIC_OUTCOME_TOKEN_ADDRESS=0x...
NEXT_PUBLIC_SETTLEMENT_ADDRESS=0x...
```

### Backend (.env)
```env
PORT=3001
CORS_ORIGIN=https://predictx.com
NODE_ENV=production
RPC_URL=https://sepolia.base.org
PRIVATE_KEY=operator_private_key
VAULT_ADDRESS=0x...
MARKET_MANAGER_ADDRESS=0x...
```

---

## DNS Yapılandırması Özeti

Domain'inizde (GoDaddy, Namecheap, vb.):

```
# Ana domain (predictx.com)
Tip: A
İsim: @
Değer: 76.76.21.21

# www subdomain
Tip: CNAME
İsim: www
Değer: cname.vercel-dns.com

# API subdomain
Tip: CNAME
İsim: api
Değer: sizin-app.railway.app
```

**DNS Yayılma:** 5-30 dakika

---

## Maliyet

### Ücretsiz Tier (MVP için)
- Frontend (Vercel): **₺0/ay**
- Backend (Railway): **₺0/ay** ($5 kredi)
- Domain: **₺200-300/yıl**
- **Toplam: ~₺20/ay** (sadece domain)

### Production (1000 kullanıcı)
- Tüm servisler: **~₺2,500/ay** ($75)

---

## Hızlı Komutlar

```bash
# Deploy hepsi
./deploy.sh

# Contract'ları deploy et
cd packages/contracts && npm run deploy:testnet

# Frontend'i deploy et
cd apps/web && vercel --prod

# Backend'i deploy et
cd apps/api && railway up

# Deployment durumunu kontrol et
vercel ls
railway status
```

---

## Yaygın Sorunlar

### DNS çözümlenmiyor
```bash
# DNS kontrolü
dig predictx.com

# 30 dakika bekleyin, tekrar deneyin
```

### CORS hatası
Backend `.env` dosyasında:
```env
CORS_ORIGIN=https://predictx.com,https://www.predictx.com
```

### Contract adresleri yanlış
Frontend/backend env var'larını kontrol edin

---

## Destek

**Dokümantasyon:**
- Türkçe: [DEPLOYMENT_TR.md](./DEPLOYMENT_TR.md)
- English: [DEPLOYMENT.md](./DEPLOYMENT.md)

**Platform Desteği:**
- Vercel: https://vercel.com/support
- Railway: https://railway.app/discord

**GitHub Issues:** 
https://github.com/dderan-pixel/worldloom/issues

---

## Sonraki Adımlar

✅ Deploy tamamlandıktan sonra:

1. Tüm sayfalara gözat (https://predictx.com)
2. API health check kontrol et (https://api.predictx.com/health)
3. Basescan'de contract'ları doğrula
4. Test cüzdanı bağla
5. İzleme kur (UptimeRobot, Sentry)
6. Analytics ekle (Google Analytics)
7. Mainnet geçişi planla

---

🎉 **Tebrikler!** 

PredictX'iniz artık kendi domain'inizde canlı!

Domain'inizi ziyaret edin: **https://predictx.com** 🚀
