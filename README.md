# 🏷️ Qiymət Müqayisə Botu — Telegram Price Comparison Bot

Azərbaycan və qlobal marketlərdə məhsul qiymətlərini müqayisə edən Telegram botu.

QR kod / barkod skan edərək məhsulun qiymətini bütün bazarlarda tapır!

## 🇦🇿 Yerli Bazarlar (Real API!)
| Market | Məlumat |
|--------|---------|
| **Wolt Marketlər** | Araz, Bravo, SPAR, Neptun + 115 market (Wolt API ilə REAL qiymətlər!) |
| **Umico / Birmarket** | AZ-nın ən böyük onlayn mağazası (500K+ məhsul) |
| **Trendyol AZ** | AZN ilə alış-veriş (geyim, elektronika və s.) |
| **OBA Market** | Azərbaycanın ən böyük supermarketlərindən biri |
| **Google Shopping** | Bütün AZ saytlarında axtarış |

## 🌍 Qlobal Bazarlar
| Market | Məlumat |
|--------|---------|
| **Amazon** | amazon.com — dünya ən böyük onlayn mağazası |
| **eBay** | ebay.com — auksion və fixed price |
| **AliExpress** | aliexpress.com — Çin bazarı |
| **Temu** | temu.com — ucuz məhsullar |
| **Walmart** | walmart.com — ABŞ marketi |

## 🔑 Əsas Xüsusiyyət: Wolt API

Bot **Wolt-un rəsmi consumer API**-sindən istifadə edir:
- `restaurant-api.wolt.com/v1/pages/search` — məhsul axtarışı
- Araz Supermarket, Bravo Supermarket, SPAR, Neptun və digər 115+ marketdən **real qiymətlər** göstərir
- Qiymətlər AZN ilə, stok məlumatı ilə birlikdə

## 🚀 Railway-ə Deploy

### 1. Bot Token əldə edin
1. Telegram-da [@BotFather](https://t.me/BotFather)-a baş vurun
2. `/newbot` əmrini yazın
3. Bot adı və username seçin
4. Token-i kopyalayın

### 2. Railway-də deploy
1. [Railway.app](https://railway.app)-a daxil olun
2. "New Project" → "Deploy from GitHub repo"
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
# Virtual environment yaradın
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Asılılıqları quraşdırın
pip install -r requirements.txt

# System dependency (pyzbar üçün)
# Ubuntu/Debian: sudo apt-get install libzbar0

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
| `/local [məhsul]` | Yalnız yerli bazarlarda axtar |
| `/global [məhsul]` | Yalnız qlobal bazarlarda axtar |
| `/help` | Kömək |

**QR Kod Skan:** Marketdəki məhsulun QR kodunun şəklini çəkin və bot-a göndərin.

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
│   ├── manager.py         # SearchManager
│   ├── wolt.py            # Wolt API (Araz, Bravo, SPAR, Neptun...)
│   ├── umico.py           # Umico / Birmarket
│   ├── trendyol.py        # Trendyol AZ
│   ├── oba.py             # OBA Market
│   ├── google_shopping.py # Google Shopping AZ
│   ├── amazon.py          # Amazon.com
│   ├── ebay.py            # eBay.com
│   ├── aliexpress.py      # AliExpress.com
│   ├── temu.py            # Temu.com
│   └── walmart.py         # Walmart.com
├── requirements.txt
├── Dockerfile
├── railway.toml
└── README.md
```

## ⚠️ Qeydlər

- **Wolt API** ən etibarlı yerli mənbədir (real qiymətlər, AZN)
- Barkod ilə axtarış ən dəqiq nəticə verir
- Bəzi saytlar CAPTCHA qoruma istifadə edə bilər
- Temu və Walmart JS-rendered olduqları üçün yalnız link təqdim edir

## 📄 Lisenziya

MIT License
