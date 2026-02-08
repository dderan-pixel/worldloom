# PredictX Deployment Rehberi (Türkçe)

PredictX'i kendi domain'inize production ortamına deploy etmek için eksiksiz rehber.

## İçindekiler

1. [Hızlı Deploy (Önerilen)](#hızlı-deploy-önerilen)
2. [Smart Contract'ları Deploy Etme](#smart-contractları-deploy-etme)
3. [Frontend Deploy (Vercel)](#frontend-deploy-vercel)
4. [Backend API Deploy](#backend-api-deploy)
5. [Özel Domain Kurulumu](#özel-domain-kurulumu)
6. [Ortam Değişkenleri](#ortam-değişkenleri)
7. [SSL/HTTPS Kurulumu](#sslhttps-kurulumu)
8. [İzleme & Bakım](#izleme--bakım)

---

## Hızlı Deploy (Önerilen)

PredictX'i özel domain ile deploy etmenin en hızlı yolu:

### Seçenek 1: Tam Otomatik Deploy

```bash
# 1. Klonla ve kur
git clone https://github.com/dderan-pixel/worldloom.git
cd worldloom
./setup.sh

# 2. Contract'ları Base Sepolia'ya deploy et
cd packages/contracts
export PRIVATE_KEY=cuzdan_private_key
export RPC_URL=https://sepolia.base.org
npm run deploy:testnet

# 3. Frontend'i Vercel'e deploy et
cd ../../apps/web
vercel --prod

# 4. Backend'i Railway'e deploy et
cd ../api
railway up
```

### Seçenek 2: Platform Bazlı

**Frontend**: Vercel (ücretsiz, otomatik SSL, özel domain)
**Backend**: Railway veya Render (ücretsiz tier mevcut)
**Contract'lar**: Base Sepolia testnet (faucet ile ücretsiz)

---

## Smart Contract'ları Deploy Etme

### Gereksinimler

1. **Base Sepolia ETH Alın**
   - Ziyaret edin: https://www.alchemy.com/faucets/base-sepolia
   - Veya: https://faucet.quicknode.com/base/sepolia
   - Deploy için ~0.1 ETH gerekli

2. **Etherscan API Key Alın**
   - Ziyaret edin: https://basescan.org/
   - Hesap oluşturun ve doğrulama için API key alın

### Base Sepolia'ya Deploy

```bash
cd packages/contracts

# Ortam değişkenlerini ayarla
export PRIVATE_KEY=cuzdan_private_key_0x_olmadan
export RPC_URL=https://sepolia.base.org
export ETHERSCAN_API_KEY=etherscan_api_key

# Contract'ları deploy et
npm run deploy:testnet
```

**Beklenen çıktı:**
```
Vault deployed at: 0x1234...
MarketManager deployed at: 0x5678...
OutcomeToken deployed at: 0x9abc...
Settlement deployed at: 0xdef0...
FeeCollector deployed at: 0x1111...
```

**Bu adresleri kaydedin** - frontend/backend yapılandırması için gerekecek.

### Basescan'de Doğrulama

Deploy sonrası contract'larınızın canlı olduğunu doğrulayın:
1. Ziyaret edin: https://sepolia.basescan.org/
2. Contract adreslerinizi arayın
3. Kaynak kodu doğrulayın (deploy sırasında otomatik yapılır)

---

## Frontend Deploy (Vercel)

Vercel, Next.js deployment için ücretsiz SSL ve özel domain'ler ile önerilen platformdur.

### Yöntem 1: Vercel CLI ile Deploy

```bash
# Vercel CLI'ı yükle
npm install -g vercel

# Web uygulamasına git
cd apps/web

# Vercel'e giriş yap
vercel login

# Production'a deploy et
vercel --prod
```

### Yöntem 2: GitHub üzerinden Deploy (Önerilen)

1. **GitHub'a Push Edin**
   ```bash
   git push origin main
   ```

2. **Vercel'e Bağlayın**
   - Ziyaret edin: https://vercel.com
   - "New Project" tıklayın
   - GitHub repository'nizi import edin
   - Root dizini olarak "apps/web" seçin

3. **Build Ayarlarını Yapılandırın**
   - Framework Preset: **Next.js**
   - Root Directory: **apps/web**
   - Build Command: `npm run build`
   - Output Directory: `.next`

4. **Ortam Değişkenlerini Ekleyin** (Vercel dashboard'da)
   ```env
   NEXT_PUBLIC_API_URL=https://sizin-api-domain.com
   NEXT_PUBLIC_CHAIN_ID=84532
   NEXT_PUBLIC_VAULT_ADDRESS=0x...
   NEXT_PUBLIC_MARKET_MANAGER_ADDRESS=0x...
   NEXT_PUBLIC_OUTCOME_TOKEN_ADDRESS=0x...
   NEXT_PUBLIC_SETTLEMENT_ADDRESS=0x...
   NEXT_PUBLIC_FEE_COLLECTOR_ADDRESS=0x...
   ```

5. **Deploy Edin**
   - "Deploy" tıklayın
   - Build için 2-3 dakika bekleyin
   - Siteniz şu adreste canlı olacak: `https://projeniz.vercel.app`

### Vercel'e Özel Domain Ekleme

1. **Vercel Dashboard'da**
   - Projenize gidin
   - Settings → Domains
   - Domain'inizi ekleyin: `predictx.com` veya `www.predictx.com`

2. **DNS Yapılandırın** (domain kayıt şirketinizde)
   
   Ana domain için (predictx.com):
   ```
   Tip: A
   İsim: @
   Değer: 76.76.21.21
   ```
   
   www subdomain için:
   ```
   Tip: CNAME
   İsim: www
   Değer: cname.vercel-dns.com
   ```

3. **DNS Yayılmasını Bekleyin** (5-30 dakika)
   - Vercel otomatik olarak SSL sertifikası sağlar
   - Siteniz HTTPS ile özel domain'inizde canlı olacak

---

## Backend API Deploy

### Seçenek 1: Railway (Önerilen)

Railway ücretsiz tier ve kolay deployment sunuyor.

#### Railway Kurulumu

```bash
# Railway CLI'ı yükle
npm install -g @railway/cli

# Giriş yap
railway login

# API'ye git
cd apps/api

# Projeyi başlat
railway init

# Deploy et
railway up
```

#### Railway Yapılandırması

1. **Ortam Değişkenlerini Ekleyin** (Railway dashboard'da)
   ```env
   PORT=3001
   CORS_ORIGIN=https://sizin-frontend-domain.com
   NODE_ENV=production
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   RPC_URL=https://sepolia.base.org
   PRIVATE_KEY=operator_private_key
   VAULT_ADDRESS=0x...
   MARKET_MANAGER_ADDRESS=0x...
   SETTLEMENT_ADDRESS=0x...
   ```

2. **API URL'nizi Alın**
   - Railway sağlar: `https://uygulamaniz.railway.app`
   - Frontend NEXT_PUBLIC_API_URL'yi bununla güncelleyin

3. **Özel Domain Ekleyin**
   - Railway Dashboard → Settings → Domains
   - `api.predictx.com` ekleyin
   - DNS yapılandırın:
     ```
     Tip: CNAME
     İsim: api
     Değer: uygulamaniz.railway.app
     ```

### Seçenek 2: Render

```bash
# apps/api/ içinde render.yaml oluştur
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

# GitHub'a push edin ve Render dashboard'da bağlayın
```

### Seçenek 3: Docker + VPS

Kendi sunucunuz varsa:

```bash
# Docker image oluştur
cd apps/api
docker build -t predictx-api .

# Container çalıştır
docker run -d \
  -p 3001:3001 \
  -e CORS_ORIGIN=https://domain.com \
  -e DATABASE_URL=postgresql://... \
  --name predictx-api \
  predictx-api

# Veya docker-compose kullan
docker-compose up -d
```

---

## Özel Domain Kurulumu

### Tam Kurulum Örneği

Diyelim ki `predictx.com` domain'ine sahipsiniz:

#### 1. DNS Kayıtlarını Yapılandırın

Domain kayıt şirketinizde (GoDaddy, Namecheap, Cloudflare, vb.):

```
# Frontend (Vercel)
Tip: A,     İsim: @,    Değer: 76.76.21.21
Tip: CNAME, İsim: www,  Değer: cname.vercel-dns.com

# API (Railway/Render/vb)
Tip: CNAME, İsim: api,  Değer: sizin-api-host.railway.app

# Opsiyonel: Durum sayfası
Tip: CNAME, İsim: status, Değer: stats.uptimerobot.com
```

#### 2. Ortam Değişkenlerini Güncelleyin

**Frontend (.env.local veya Vercel):**
```env
NEXT_PUBLIC_API_URL=https://api.predictx.com
```

**Backend (.env veya Railway/Render):**
```env
CORS_ORIGIN=https://predictx.com,https://www.predictx.com
```

#### 3. Kurulumu Doğrulayın

```bash
# DNS yayılmasını kontrol et
dig predictx.com
dig www.predictx.com
dig api.predictx.com

# Endpoint'leri test et
curl https://predictx.com
curl https://api.predictx.com/health
```

### Cloudflare Kullanımı (Opsiyonel ama Önerilen)

Cloudflare ücretsiz SSL, CDN ve DDoS koruması sağlar:

1. **Siteyi Cloudflare'e Ekleyin**
   - Ziyaret edin: https://www.cloudflare.com/
   - Domain'inizi ekleyin
   - Nameserver'ları kayıt şirketinizde güncelleyin

2. **Cloudflare'de DNS Yapılandırın**
   - Yukarıdaki kayıtların aynısı
   - Frontend için "Proxied" (turuncu bulut) etkinleştirin
   - Railway/Render SSL kullanıyorsa API için "DNS only" (gri bulut) kullanın

3. **SSL/TLS Ayarları**
   - SSL/TLS → Overview → Full (strict)
   - Edge Certificates → Always Use HTTPS: AÇIK

---

## Ortam Değişkenleri

### Eksiksiz Ortam Kurulumu

#### Frontend (apps/web/.env.local)

```env
# API Yapılandırması
NEXT_PUBLIC_API_URL=https://api.predictx.com

# Blockchain Yapılandırması
NEXT_PUBLIC_CHAIN_ID=84532
NEXT_PUBLIC_RPC_URL=https://sepolia.base.org

# Contract Adresleri (deployment'tan)
NEXT_PUBLIC_VAULT_ADDRESS=0x...
NEXT_PUBLIC_MARKET_MANAGER_ADDRESS=0x...
NEXT_PUBLIC_OUTCOME_TOKEN_ADDRESS=0x...
NEXT_PUBLIC_SETTLEMENT_ADDRESS=0x...
NEXT_PUBLIC_FEE_COLLECTOR_ADDRESS=0x...

# Opsiyonel: Analizler
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

#### Backend (apps/api/.env)

```env
# Sunucu Yapılandırması
NODE_ENV=production
PORT=3001
CORS_ORIGIN=https://predictx.com,https://www.predictx.com

# Veritabanı
DATABASE_URL=postgresql://user:pass@host:5432/predictx
REDIS_URL=redis://host:6379

# Blockchain
RPC_URL=https://sepolia.base.org
PRIVATE_KEY=settlement_icin_operator_private_key

# Contract Adresleri
VAULT_ADDRESS=0x...
MARKET_MANAGER_ADDRESS=0x...
OUTCOME_TOKEN_ADDRESS=0x...
SETTLEMENT_ADDRESS=0x...

# Opsiyonel: İzleme
SENTRY_DSN=https://...
LOG_LEVEL=info
```

---

## SSL/HTTPS Kurulumu

### Otomatik SSL (Önerilen)

Hem Vercel hem Railway/Render otomatik SSL sağlar:

1. **Vercel**: Otomatik Let's Encrypt sertifikaları
2. **Railway**: Özel domain'ler için otomatik SSL
3. **Render**: Özel domain'ler için otomatik SSL

Ek yapılandırma gerekmez!

### Manuel SSL (VPS/Docker)

Kendi sunucunuzda barındırıyorsanız:

```bash
# Certbot yükle
sudo apt install certbot python3-certbot-nginx

# SSL sertifikası al
sudo certbot --nginx -d predictx.com -d www.predictx.com -d api.predictx.com

# Otomatik yenileme (certbot tarafından zaten ayarlanmış)
sudo certbot renew --dry-run
```

---

## İzleme & Bakım

### 1. Uptime İzleme

**UptimeRobot** (Ücretsiz):
```
İzle: https://predictx.com
İzle: https://api.predictx.com/health
Uyarı: Çöktüğünde email
```

### 2. Hata Takibi

**Sentry** (Ücretsiz tier):
```bash
# Frontend'e yükle
npm install @sentry/nextjs

# Backend'e yükle
npm install @sentry/node
```

### 3. Analizler

**Vercel Analytics** (Yerleşik):
- Vercel projelerinde otomatik etkin

**Google Analytics**:
```typescript
// apps/web/app/layout.tsx'e ekle
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

### 4. Veritabanı Yedekleme

**Otomatik Yedeklemeler**:
- Railway: Otomatik yedekler (ücretli planlar)
- Render: Otomatik yedekler (PostgreSQL)
- Manuel: Günlük pg_dump cron job kurun

### 5. Log İzleme

```bash
# Vercel logları
vercel logs

# Railway logları
railway logs

# Docker logları
docker logs predictx-api
```

---

## Production Kontrol Listesi

Canlıya çıkmadan önce:

- [ ] Smart contract'lar deploy edildi ve Basescan'de doğrulandı
- [ ] Frontend özel domain ve SSL ile deploy edildi
- [ ] Backend özel domain ve SSL ile deploy edildi
- [ ] Tüm ortam değişkenleri yapılandırıldı
- [ ] DNS kayıtları yayıldı (`dig` ile kontrol et)
- [ ] HTTPS tüm domain'lerde çalışıyor
- [ ] API health check cevap veriyor: `/health`
- [ ] CORS doğru yapılandırıldı
- [ ] Veritabanı bağlandı ve migration'lar çalıştı
- [ ] Redis/cache yapılandırıldı (kullanılıyorsa)
- [ ] Hata takibi kuruldu (Sentry)
- [ ] Uptime izleme yapılandırıldı
- [ ] Yedekleme stratejisi yerinde
- [ ] API'de rate limiting yapılandırıldı
- [ ] Güvenlik header'ları yapılandırıldı
- [ ] Cüzdan bağlantıları test edildi
- [ ] Uçtan uca akışlar test edildi

---

## Hızlı Referans

### Deployment Komutları

```bash
# Contract'ları deploy et
cd packages/contracts && npm run deploy:testnet

# Frontend'i deploy et (Vercel)
cd apps/web && vercel --prod

# Backend'i deploy et (Railway)
cd apps/api && railway up

# Deployment'ları kontrol et
vercel ls
railway status
```

### Yaygın Sorunlar

**Sorun**: DNS çözümlenmiyor
- **Çözüm**: Yayılma için 30 dakika bekleyin, `dig domain.com` ile kontrol edin

**Sorun**: SSL sertifikası sağlanmıyor
- **Çözüm**: DNS'in doğru yapılandırıldığından emin olun, Vercel/Railway'in sağlamasını bekleyin

**Sorun**: CORS hataları
- **Çözüm**: Backend env var'larında CORS_ORIGIN'e frontend domain'i ekleyin

**Sorun**: Contract çağrıları başarısız oluyor
- **Çözüm**: Frontend env var'larındaki contract adreslerini doğrulayın

---

## Maliyet Tahmini

### Ücretsiz Tier (MVP için Mükemmel)

- **Frontend (Vercel)**: Ücretsiz (100GB bandwidth/ay)
- **Backend (Railway)**: Ücretsiz ($5 kredi/ay)
- **Veritabanı (Supabase)**: Ücretsiz (500MB)
- **Redis (Upstash)**: Ücretsiz (10K komut/gün)
- **Domain**: Yıllık ₺200-300
- **Blockchain**: Ücretsiz (testnet)

**Toplam**: Yılda ~₺200-300 sadece domain için!

### Production Ölçek (~1000 kullanıcı)

- **Frontend (Vercel Pro)**: Aylık $20
- **Backend (Railway)**: Aylık $20
- **Veritabanı (Railway)**: Aylık $25
- **Redis (Railway)**: Aylık $10
- **Domain**: Yıllık ₺200-300
- **İzleme**: Ücretsiz (UptimeRobot + Sentry ücretsiz tier)

**Toplam**: Aylık ~$75-80 (₺2,500-2,700)

---

## Destek

Deployment sorunları için:
- Logları kontrol edin: `vercel logs` / `railway logs`
- Vercel Destek: https://vercel.com/support
- Railway Discord: https://railway.app/discord
- GitHub Issues: https://github.com/dderan-pixel/worldloom/issues

---

## Sonraki Adımlar

Deployment sonrası:
1. Production'da tüm kullanıcı akışlarını test edin
2. İzleme ve uyarıları kurun
3. Rate limiting yapılandırın
4. Analizleri ekleyin
5. Otomatik deployment için CI/CD kurun
6. Staging ortamı oluşturun
7. Mainnet geçişi planlayın

🎉 Tebrikler! PredictX platformunuz artık özel domain'inizde canlı!
