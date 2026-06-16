import os
import logging
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ─────────────────────────────────────────────
# Barkod oxuma
# ─────────────────────────────────────────────
def decode_barcode(image_bytes: bytes) -> str | None:
    """Şəkildən barkod / QR kodunu oxuyur."""
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        codes = decode(image)
        if codes:
            return codes[0].data.decode("utf-8")
    except Exception as e:
        logger.error(f"Barkod oxuma xətası: {e}")
    return None


# ─────────────────────────────────────────────
# Qiymət axtarışı — Open Food Facts (pulsuz API)
# ─────────────────────────────────────────────
async def search_open_food_facts(session: aiohttp.ClientSession, barcode: str) -> dict | None:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 200:
                data = await r.json()
                if data.get("status") == 1:
                    p = data["product"]
                    return {
                        "source": "Open Food Facts",
                        "name": p.get("product_name") or p.get("product_name_en", "—"),
                        "brand": p.get("brands", "—"),
                        "category": p.get("categories", "—").split(",")[0].strip(),
                        "image": p.get("image_url", ""),
                        "url": f"https://world.openfoodfacts.org/product/{barcode}",
                        "price": None,
                    }
    except Exception as e:
        logger.warning(f"OpenFoodFacts xətası: {e}")
    return None


# ─────────────────────────────────────────────
# Qiymət axtarışı — Open Beauty Facts
# ─────────────────────────────────────────────
async def search_open_beauty_facts(session: aiohttp.ClientSession, barcode: str) -> dict | None:
    url = f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 200:
                data = await r.json()
                if data.get("status") == 1:
                    p = data["product"]
                    return {
                        "source": "Open Beauty Facts",
                        "name": p.get("product_name", "—"),
                        "brand": p.get("brands", "—"),
                        "category": "Gözəllik məhsulu",
                        "image": p.get("image_url", ""),
                        "url": f"https://world.openbeautyfacts.org/product/{barcode}",
                        "price": None,
                    }
    except Exception as e:
        logger.warning(f"OpenBeautyFacts xətası: {e}")
    return None


# ─────────────────────────────────────────────
# Qiymət axtarışı — UPC Item DB (qiymət məlumatı)
# ─────────────────────────────────────────────
async def search_upc_itemdb(session: aiohttp.ClientSession, barcode: str) -> list[dict]:
    url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
    results = []
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 200:
                data = await r.json()
                for item in data.get("items", [])[:3]:
                    for offer in item.get("offers", [])[:3]:
                        results.append({
                            "source": offer.get("merchant", "Onlayn mağaza"),
                            "name": item.get("title", "—"),
                            "brand": item.get("brand", "—"),
                            "category": item.get("category", "—"),
                            "image": item.get("images", [""])[0] if item.get("images") else "",
                            "url": offer.get("link", ""),
                            "price": f"{offer.get('price', '?')} {offer.get('currency', 'USD')}",
                        })
    except Exception as e:
        logger.warning(f"UPCItemDB xətası: {e}")
    return results


# ─────────────────────────────────────────────
# Google Shopping axtarış linki
# ─────────────────────────────────────────────
def google_shopping_link(query: str) -> str:
    q = query.replace(" ", "+")
    return f"https://www.google.com/search?tbm=shop&q={q}"

def amazon_link(query: str) -> str:
    q = query.replace(" ", "+")
    return f"https://www.amazon.com/s?k={q}"

def ebay_link(query: str) -> str:
    q = query.replace(" ", "+")
    return f"https://www.ebay.com/sch/i.html?_nkw={q}"

def umico_link(query: str) -> str:
    q = query.replace(" ", "+")
    return f"https://umico.az/search?q={q}"


# ─────────────────────────────────────────────
# Mesaj formatlaması
# ─────────────────────────────────────────────
def format_result(barcode: str, product_info: dict | None, price_offers: list[dict]) -> str:
    lines = [f"🔍 *Barkod:* `{barcode}`\n"]

    if product_info:
        lines.append(f"📦 *Məhsul:* {product_info['name']}")
        if product_info.get("brand") and product_info["brand"] != "—":
            lines.append(f"🏷 *Brend:* {product_info['brand']}")
        if product_info.get("category") and product_info["category"] != "—":
            lines.append(f"📂 *Kateqoriya:* {product_info['category']}")
        lines.append("")

    if price_offers:
        lines.append("💰 *Tapılan qiymətlər:*")
        for offer in price_offers[:5]:
            price_str = offer.get("price") or "Qiymət məlumatı yoxdur"
            lines.append(f"• *{offer['source']}* — {price_str}")
    else:
        lines.append("ℹ️ Birbaşa qiymət tapılmadı. Aşağıdakı düymələrdən axtarış edə bilərsiniz.")

    return "\n".join(lines)


def build_keyboard(product_name: str, barcode: str) -> InlineKeyboardMarkup:
    query = product_name if product_name and product_name != "—" else barcode
    buttons = [
        [
            InlineKeyboardButton("🛒 Google Shopping", url=google_shopping_link(query)),
            InlineKeyboardButton("🟠 Amazon", url=amazon_link(query)),
        ],
        [
            InlineKeyboardButton("🔵 eBay", url=ebay_link(query)),
            InlineKeyboardButton("🇦🇿 Umico.az", url=umico_link(query)),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────────────────────────
# Telegram handler-lar
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 Salam! Mən *Qiymət Axtarışı Botuyam* 🤖\n\n"
        "📸 Məhsulun *barkod* və ya *QR kod* şəklini göndər,\n"
        "mən isə sənin üçün qiymətləri tapım!\n\n"
        "✅ *Dəstəklənən formatlar:*\n"
        "• EAN-8, EAN-13 barkodlar\n"
        "• UPC-A, UPC-E barkodlar\n"
        "• QR kodlar\n\n"
        "💡 *İpucu:* Şəkli yaxından və aydın çək!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "ℹ️ *Necə istifadə etməli?*\n\n"
        "1️⃣ Marketdə məhsulun barkodunu tap\n"
        "2️⃣ Telefon kameranla şəkil çək\n"
        "3️⃣ Həmin şəkli bu bota göndər\n"
        "4️⃣ Bot avtomatik qiymətləri tapacaq!\n\n"
        "🔗 Düymələr vasitəsilə daha çox saytda axtara bilərsən."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("⏳ Şəkil analiz edilir, zəhmət olmasa gözləyin...")

    try:
        # Ən yüksək keyfiyyətli fotoğrafı al
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        # Barkod oxu
        barcode = decode_barcode(bytes(image_bytes))
        if not barcode:
            await msg.edit_text(
                "❌ *Barkod tapılmadı!*\n\n"
                "💡 *Tövsiyələr:*\n"
                "• Şəkli daha yaxından çək\n"
                "• Işıqlandırmanı yaxşılaşdır\n"
                "• Barkod tam görünsün",
                parse_mode="Markdown"
            )
            return

        await msg.edit_text(f"✅ Barkod tapıldı: `{barcode}`\n🔍 Qiymətlər axtarılır...", parse_mode="Markdown")

        # Paralel axtarış
        async with aiohttp.ClientSession() as session:
            food_task = search_open_food_facts(session, barcode)
            beauty_task = search_open_beauty_facts(session, barcode)
            upc_task = search_upc_itemdb(session, barcode)

            food_result, beauty_result, upc_offers = await asyncio.gather(
                food_task, beauty_task, upc_task
            )

        product_info = food_result or beauty_result
        product_name = product_info["name"] if product_info else barcode

        text = format_result(barcode, product_info, upc_offers)
        keyboard = build_keyboard(product_name, barcode)

        # Əgər məhsulun şəkli varsa
        if product_info and product_info.get("image"):
            await msg.delete()
            await update.message.reply_photo(
                photo=product_info["image"],
                caption=text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        else:
            await msg.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Foto emal xətası: {e}")
        await msg.edit_text("⚠️ Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sənəd kimi göndərilən şəkilləri emal et (orijinal keyfiyyət)."""
    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        await update.message.reply_text("❌ Yalnız şəkil faylı göndərin.")
        return

    # photo handler-ı simulyasiya et
    update.message.photo = [doc]
    doc.file_id = doc.file_id
    await handle_photo(update, context)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    logger.info("Bot işə düşdü...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
