import os
import docx
from pdfminer.high_level import extract_text as pdf_extract
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def extract_from_docx(path: str) -> str:
    try:
        doc = docx.Document(path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""

def extract_from_pdf(path: str) -> str:
    try:
        return pdf_extract(path)
    except Exception:
        return ""

def extract_from_image(path: str) -> str:
    if not OCR_AVAILABLE:
        return "OCR kutubxonasi o'rnatilmagan."
    try:
        text = pytesseract.image_to_string(Image.open(path), lang='eng+rus+uzb')
        return text
    except Exception as e:
        return f"Rasmdan matnni o'qishda xatolik: {e}"
