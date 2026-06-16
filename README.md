# 🤖 Qiymət Axtarışı Telegram Botu

Barkod / QR kod şəkli göndər → Bot avtomatik qiymətləri tapır!

---

## 📋 Quraşdırma (Windows / Mac / Linux)

### 1. Python yüklə
https://python.org — versiya 3.11 və ya 3.12 tövsiyə olunur.

### 2. Sistem kitabxanasını yüklə (pyzbar üçün)

**Ubuntu/Debian (Linux):**
```bash
sudo apt-get install libzbar0
```

**macOS:**
```bash
brew install zbar
```

**Windows:**
pyzbar Windows-da avtomatik işləyir, əlavə quraşdırma lazım deyil.

---

### 3. Bot Token al

1. Telegramda [@BotFather](https://t.me/BotFather) yazın
2. `/newbot` yazın
3. Botun adını yazın (məs: `Qiymet Axtaris Botu`)
4. Username yazın (məs: `qiymet_axtaris_bot`)
5. BotFather sizə bir TOKEN verəcək (belə görünür: `1234567890:ABCDefGHIjklmNOPQRST`)

---

### 4. Token-i bota əlavə et

`bot.py` faylını açın, bu sətri tapın:
```python
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
```
`YOUR_BOT_TOKEN_HERE` yerinə öz tokeninizi yazın.

**Və ya** terminal/CMD-də belə işlədin:

**Linux/Mac:**
```bash
export BOT_TOKEN="sizin_tokeniniz"
python bot.py
```

**Windows CMD:**
```cmd
set BOT_TOKEN=sizin_tokeniniz
python bot.py
```

---

### 5. Kitabxanaları yüklə və botu işlət

```bash
pip install -r requirements.txt
python bot.py
```

---

## 🌐 Serverdə işlətmək (24/7 aktiv olsun)

### Pulsuz seçim: Railway.app

1. https://railway.app qeydiyyatdan keçin (GitHub ilə)
2. "New Project" → "Deploy from GitHub repo"
3. Bu faylları GitHub-a yükləyin
4. Environment Variables-a `BOT_TOKEN` əlavə edin
5. Deploy edin — bot daima aktiv olacaq!

### Procfile (Railway üçün):
```
worker: python bot.py
```

---

## ⚙️ İstifadə olunan API-lər (hamısı PULSUZdur)

| API | Nə üçün |
|-----|---------|
| Open Food Facts | Ərzaq məhsullarının məlumatı |
| Open Beauty Facts | Gözəllik məhsullarının məlumatı |
| UPC Item DB | Qiymət məlumatı (gündə 100 sorğu pulsuz) |
| Google Shopping | Axtarış linki |
| Amazon / eBay | Axtarış linki |
| Umico.az | Axtarış linki |

---

## 📱 Botun işləmə sxemi

```
İstifadəçi şəkil göndərir
        ↓
pyzbar ilə barkod oxunur
        ↓
3 API-yə paralel sorğu göndərilir
        ↓
Nəticə + düymələr göstərilir
        ↓
İstifadəçi daha çox saytda axtara bilir
```

---

## 🔧 UPC Item DB Limit artırmaq

Gündə 100-dən çox sorğu üçün:
1. https://www.upcitemdb.com qeydiyyat edin
2. Pulsuz plan: 100 sorğu/gün
3. Ödənişli plan: Limitsiz
