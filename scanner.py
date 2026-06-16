"""
QR Code / Barcode scanner module.
Decodes barcodes (EAN, UPC, etc.) and QR codes from images sent by users.
"""

import io
from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol


def scan_qr_from_bytes(image_bytes: bytes) -> list[str]:
    """
    Accept raw image bytes, return list of decoded strings
    (barcode numbers, QR URLs, etc.)
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Convert to RGB if necessary (e.g., RGBA or P mode)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        
        decoded = decode(img)
        results = []
        for item in decoded:
            data = item.data.decode("utf-8", errors="ignore").strip()
            if data:
                results.append(data)
        return results
    except Exception as e:
        print(f"[Scanner Error] {e}")
        return []


def extract_barcode(codes: list[str]) -> str | None:
    """
    From a list of decoded strings, try to find a barcode (numeric, 8-13 digits).
    Returns the first barcode found or None.
    """
    for code in codes:
        clean = code.strip()
        if clean.isdigit() and 8 <= len(clean) <= 13:
            return clean
    return None


def extract_product_query(codes: list[str]) -> str | None:
    """
    Return a search-friendly string from decoded data.
    If it's a URL, try to extract product name/ID from it.
    If it's a barcode, return it as-is.
    Otherwise, return the raw string.
    """
    if not codes:
        return None
    code = codes[0].strip()
    
    # If it's a pure barcode number
    if code.isdigit():
        return code
    
    # If it's a URL, return as-is for product page detection
    if code.startswith(("http://", "https://")):
        return code
    
    # Otherwise return as-is for search
    return code
