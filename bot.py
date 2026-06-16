"""
Telegram Price Comparison Bot
Scans QR codes / barcodes from product images and compares prices
across local (Azerbaijan) and global marketplaces.

Deploy on Railway with BOT_TOKEN environment variable.
"""

import os
import asyncio
import logging
from io import BytesIO

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, MAX_IMAGE_SIZE
from scanner import scan_qr_from_bytes, extract_barcode, extract_product_query
from search.manager import SearchManager
from search.base import SearchResult
from barcode_lookup import lookup_barcode

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Init ──────────────────────────────────────────────────────────────────────
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
router = Router()
dp.include_router(router)

search_manager = SearchManager()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def build_results_message(
    product_name: str,
    results: list[SearchResult],
    barcode: str | None = None,
) -> str:
    """Build a formatted results message."""
    lines = [
        "🔍 <b>Qiymət Müqayisəsi</b>",
        f"📦 <b>{product_name}</b>",
    ]
    if barcode:
        lines.append(f"🏷️ Barkod: <code>{barcode}</code>")
    
    lines.append("")

    local_results = [r for r in results if r.is_local]
    global_results = [r for r in results if not r.is_local]

    if local_results:
        lines.append("🇦🇿 <b>Yerli Bazarlar:</b>")
        lines.append("──────────────────")
        for r in local_results:
            lines.append(r.format())
            lines.append("")

    if global_results:
        lines.append("🌍 <b>Qlobal Bazarlar:</b>")
        lines.append("──────────────────")
        for r in global_results:
            lines.append(r.format())
            lines.append("")

    if not local_results and not global_results:
        lines.append("😔 Heç bir nəticə tapılmadı. Zəhmət olmasa başqa məhsul sınayın.")

    lines.append("")
    lines.append("📡 @PriceCompareAZ_Bot")

    return "\n".join(lines)


def build_search_keyboard(query: str, barcode: str | None = None) -> InlineKeyboardMarkup:
    """Build inline keyboard for search options."""
    buttons = []
    data_prefix = f"search:{'barcode' if barcode else 'query'}:"
    
    # Encode query/barcode for callback data (max 64 bytes)
    q = (barcode or query)[:50]
    
    buttons.append([
        InlineKeyboardButton(text="🇦🇿 Yerli Bazarlar", callback_data=f"local:{q}"),
        InlineKeyboardButton(text="🌍 Qlobal Bazarlar", callback_data=f"global:{q}"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🔎 Hamısında Axtar", callback_data=f"all:{q}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Commands ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Salam! Mən <b>Qiymət Müqayisə Botu</b>yam!\n\n"
        "🔍 Məhsulun QR kodunu və ya barkodunu skan edin\n"
        "📸 Məhsul şəklini göndərin\n"
        "✏️ Məhsul adını yazın\n\n"
        "Mən sizin üçün yerli və qlobal bazarlarda ən yaxşı qiyməti tapacam!\n\n"
        "🇦🇿 <b>Yerli:</b> Araz, Bravo, BazarStore, Sait.az, BolMart\n"
        "🌍 <b>Qlobal:</b> Amazon, eBay, AliExpress, Temu, Walmart\n\n"
        "📷 QR kod / barkod şəklini göndərin və ya /search əmrindən istifadə edin!"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>İstifadə Qaydası:</b>\n\n"
        "1️⃣ Marketdəki məhsulun QR/barkod şəklini çəkin və mənə göndərin\n"
        "2️⃣ Bot QR kodu oxuyub məhsulu tanıyacaq\n"
        "3️⃣ Bütün bazarlarda qiymət müqayisəsi edəcək\n\n"
        "📌 <b>Əmrlər:</b>\n"
        "/start - Botu başlat\n"
        "/search [məhsul] - Məhsul axtarın\n"
        "/local [məhsul] - Yerli bazarlarda axtarın\n"
        "/global [məhsul] - Qlobal bazarlarda axtarın\n"
        "/help - Kömək\n\n"
        "💡 <b>Məsləhət:</b> Barkod (EAN/UPC) ən dəqiq nəticə verir!"
    )


@router.message(Command("search"))
async def cmd_search(message: Message):
    """Search by text query: /search Coca Cola 330ml"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Zəhmət olmasa məhsul adını yazın!\n\nNümunə: /search Coca Cola 330ml")
        return

    query = args[1].strip()
    if not query:
        await message.answer("❌ Axtarış sorğusu boşdur!")
        return

    await _perform_search(message, query)


@router.message(Command("local"))
async def cmd_local(message: Message):
    """Search only local markets."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Zəhmət olmasa məhsul adını yazın!\n\nNümunə: /local Süd 1L")
        return

    query = args[1].strip()
    await _perform_search(message, query, include_global=False)


@router.message(Command("global"))
async def cmd_global(message: Message):
    """Search only global markets."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Zəhmət olmasa məhsul adını yazın!\n\nNümunə: /global iPhone 15")
        return

    query = args[1].strip()
    await _perform_search(message, query, include_local=False)


# ─── Image/Photo Handler (QR Scan) ────────────────────────────────────────────

@router.message(F.photo)
async def handle_photo(message: Message):
    """Handle photo messages — scan QR/barcode from image."""
    status_msg = await message.answer("📸 Şəkil qəbul edildi, QR kod oxunur...")

    # Get the highest resolution photo
    photo = message.photo[-1]

    # Download photo
    try:
        file = await bot.get_file(photo.file_id)
        photo_bytes_io = BytesIO()
        await bot.download_file(file.file_path, photo_bytes_io)
        photo_bytes = photo_bytes_io.getvalue()
    except Exception as e:
        await status_msg.edit_text("❌ Şəkli yükləmək mümkün olmadı. Yenidən cəhd edin.")
        logger.error(f"Photo download error: {e}")
        return

    # Scan QR/barcode
    decoded = scan_qr_from_bytes(photo_bytes)

    if not decoded:
        await status_msg.edit_text(
            "❌ Şəkildə QR kod və ya barkod tapılmadı.\n\n"
            "Zəhmət olmasa:\n"
            "• Şəkilin aydın olduğuna əmin olun\n"
            "• QR kodun tam görünməsinə çalışın\n"
            "• Ya da /search əmri ilə məhsul adını yazın"
        )
        return

    # Extract barcode if available
    barcode = extract_barcode(decoded)
    query = extract_product_query(decoded)

    await status_msg.edit_text(
        f"✅ Kod oxundu!\n"
        f"🏷️ Barkod: <code>{barcode or 'Tapılmadı'}</code>\n"
        f"📝 Məlumat: <code>{query or decoded[0]}</code>\n\n"
        f"⏳ Bazarlarda axtarılır..."
    )

    # If it's a barcode, look up product info
    product_name = query or decoded[0]
    if barcode:
        product_info = await lookup_barcode(barcode)
        if product_info and product_info.get("name"):
            product_name = product_info["name"]

    # Search all marketplaces
    results = await search_manager.search_all(
        query=product_name,
        barcode=barcode,
    )

    # Build and send results
    result_text = build_results_message(product_name, results, barcode)

    # If too long, split message
    if len(result_text) > 4096:
        # Send in chunks
        chunks = [result_text[i:i+4096] for i in range(0, len(result_text), 4096)]
        for i, chunk in enumerate(chunks):
            if i == 0:
                await status_msg.edit_text(chunk)
            else:
                await message.answer(chunk)
    else:
        await status_msg.edit_text(result_text)


# ─── Text Message Handler (Search by name) ────────────────────────────────────

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message):
    """Handle text messages as product search queries."""
    query = message.text.strip()
    if not query or len(query) < 2:
        return

    await _perform_search(message, query)


# ─── Callback Query Handlers ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("local:"))
async def callback_local(callback: CallbackQuery):
    """Search local markets via inline button."""
    query = callback.data.split(":", 1)[1]
    await callback.answer("🇦🇿 Yerli bazarlarda axtarılır...")
    results = await search_manager.search_local(query)
    text = build_results_message(query, results)
    if len(text) > 4096:
        text = text[:4090] + "..."
    await callback.message.edit_text(text)


@router.callback_query(F.data.startswith("global:"))
async def callback_global(callback: CallbackQuery):
    """Search global markets via inline button."""
    query = callback.data.split(":", 1)[1]
    await callback.answer("🌍 Qlobal bazarlarda axtarılır...")
    results = await search_manager.search_global(query)
    text = build_results_message(query, results)
    if len(text) > 4096:
        text = text[:4090] + "..."
    await callback.message.edit_text(text)


@router.callback_query(F.data.startswith("all:"))
async def callback_all(callback: CallbackQuery):
    """Search all markets via inline button."""
    query = callback.data.split(":", 1)[1]
    await callback.answer("🔎 Bütün bazarlarda axtarılır...")
    results = await search_manager.search_all(query)
    text = build_results_message(query, results)
    if len(text) > 4096:
        text = text[:4090] + "..."
    await callback.message.edit_text(text)


# ─── Core Search Function ─────────────────────────────────────────────────────

async def _perform_search(
    message: Message,
    query: str,
    barcode: str | None = None,
    include_local: bool = True,
    include_global: bool = True,
):
    """Perform search and send results."""
    status_msg = await message.answer(f"⏳ <b>{query}</b> axtarılır...")

    # If barcode provided, lookup product info
    product_name = query
    if barcode:
        product_info = await lookup_barcode(barcode)
        if product_info and product_info.get("name"):
            product_name = product_info["name"]

    # Search marketplaces
    results = await search_manager.search_all(
        query=product_name,
        barcode=barcode,
        include_local=include_local,
        include_global=include_global,
    )

    # Build results
    result_text = build_results_message(product_name, results, barcode)

    # Add keyboard for additional searches
    keyboard = build_search_keyboard(query, barcode)

    # Send results
    if len(result_text) > 4096:
        chunks = [result_text[i:i+4096] for i in range(0, len(result_text), 4096)]
        for i, chunk in enumerate(chunks):
            if i == 0:
                await status_msg.edit_text(chunk, reply_markup=keyboard if i == len(chunks)-1 else None)
            else:
                await message.answer(chunk, reply_markup=keyboard if i == len(chunks)-1 else None)
    else:
        await status_msg.edit_text(result_text, reply_markup=keyboard)


# ─── Main ──────────────────────────────────────────────────────────────────────

async def main():
    logger.info("Starting Price Comparison Bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
