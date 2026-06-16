# 🏷️ Qiymət Müqayisə Botu — Telegram Price Comparison Bot

Azərbaycan və qlobal marketlərdə məhsul qiymətlərini müqayisə edən Telegram botu.

QR kod / barkod skan edərək məhsulun qiymətini bütün bazarlarda tapır!

## 🇦🇿 Yerli Bazarlar
- **Araz Supermarket** — araz.az
- **Bravo Supermarket** — bravo.az
- **BazarStore** — bazarstore.az
- **Sait.az** — sait.az (qiymət müqayisə)
- **BolMart.az** — bolmart.az

## 🌍 Qlobal Bazarlar
- **Amazon** — amazon.com
- **eBay** — ebay.com
- **AliExpress** — aliexpress.com
- **Temu** — temu.com
- **Walmart** — walmart.com

## 🚀 Railway-ə Deploy

### 1. Bot Token əldə edin
1. Telegram-da [@BotFather](https://t.me/BotFather)-a baş vurun
2. `/newbot` əmrini yazın
3. Bot adı və username seçin
4. Token-i kopyalayın

### 2. Railway-də deploy
1. [Railway.app](https://railway.app)-a daxil olun
2. "New Project" → "Deploy from GitHub repo" (və ya GitHub-a push edin)
3. Environment Variables əlavə edin:
   - `BOT_TOKEN` = sizin bot tokeniniz
4. Railway avtomatik Dockerfile-dan build edəcək

### Və ya CLI ilə:
```bash
npm i -g @railway/cli
railway login
railway init
railway variables set BOT_TOKEN=sizin_token_burada
railway up
```

## 💻 Lokal İstifadə

```bash
# Reponu klonlayın
git clone <repo-url>
cd telegram-price-bot

# Virtual environment yaradın
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Asılılıqları quraşdırın
pip install -r requirements.txt

# System dependency (pyzbar üçün)
# Ubuntu/Debian: sudo apt-get install libzbar0
# macOS: brew install zbar

# Environment variable təyin edin
export BOT_TOKEN=sizin_token_burada

# Botu işə salın
python bot.py
```

## 📱 İstifadə Qaydası

| Əmr | Təsvir |
|------|--------|
| `/start` | Botu başlat |
| `/search [məhsul]` | Bütün bazarlarda axtar |
| `/local [məhsul]`` | Yalnız yerli bazarlarda axtar |
| `/global [məhsul]` | Yalnız qlobal bazarlarda axtar |
| `/help` | Kömək |

**QR Kod Skan:** Marketdəki məhsulun QR kodunun şəklini çəkin və bot-a göndərin. Bot barkodu oxuyub məhsulu bütün bazarlarda axtaracaq.

## 🏗️ Layihə Strukturu

```
telegram-price-bot/
├── bot.py                 # Əsas bot faylı (aiogram 3.x)
├── config.py              # Konfiqurasiya
├── scanner.py             # QR/barkod skaneri (pyzbar)
├── barcode_lookup.py      # Barkod məlumat bazası (Open Food Facts, UPCitemdb)
├── search/
│   ├── __init__.py
│   ├── base.py            # BaseSearcher və SearchResult
│   ├── manager.py         # SearchManager (bütün bazarları idarə edir)
│   ├── araz.py            # Araz Supermarket
│   ├── bravo.py           # Bravo Supermarket
│   ├── bazarstore.py      # BazarStore
│   ├── sait.py            # Sait.az
│   ├── bolmart.py         # BolMart.az
│   ├── amazon.py          # Amazon.com
│   ├── ebay.py            # eBay.com
│   ├── aliexpress.py      # AliExpress.com
│   ├── temu.py            # Temu.com
│   └── walmart.py         # Walmart.com
├── requirements.txt
├── Dockerfile
├── railway.toml
├── Procfile
└── README.md
```

## ⚠️ Qeydlər

- Bəzi marketlərin saytları CAPTCHA və ya anti-bot qoruma istifadə edə bilər
- Web scraping əsaslı axtarış marketlərin sayt strukturundan asılıdır
- Daha dəqiq nəticələr üçün barkod (EAN/UPC) istifadə edin
- API key əldə edərək daha stabil axtarış mümkündür

## 📄 Lisenziya

MIT License
