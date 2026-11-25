from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
import io

TEMPLATE = Path(__file__).resolve().parent.parent / "Pass template.pdf"

def _overlay(lines, photo_path):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = A4[1] - 60 * mm
    for ln in lines:
        c.setFont("Helvetica", 11); c.drawString(30 * mm, y, ln); y -= 6 * mm
    if photo_path and Path(photo_path).exists():
        c.drawImage(photo_path, A4[0] - 60 * mm, A4[1] - 90 * mm,
                    width=40 * mm, height=50 * mm, preserveAspectRatio=True)
    c.save(); buf.seek(0); return buf

def _write(out_path, lines, photo_path):
    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    if TEMPLATE.exists():
        base = PdfReader(str(TEMPLATE))
        overlay = PdfReader(_overlay(lines, photo_path))
        for i, page in enumerate(base.pages):
            if i == 0:
                page.merge_page(overlay.pages[0])
            writer.add_page(page)
    else: 
        writer.append(PdfReader(_overlay(lines, photo_path)))
    with open(out_path, "wb") as fh:
        writer.write(fh)
    return str(out_path)

def generate_pass(visitor: dict, out_path) -> str:
    lines = [
        "VISITOR PASS",
        f"Visitor No: {visitor['visitor_number']}",
        f"Name: {visitor['name']}",
        f"Mobile: {visitor['mobile']}",
        f"Meeting: {visitor['whom_to_meet']}",
        f"Purpose: {visitor['purpose']}",
        f"ID: {visitor['id_type']} {visitor['id_number']}",
        f"Locker: {visitor.get('locker_assigned') or '-'}",
        f"Time In: {visitor['check_in_time']}",
    ]
    return _write(out_path, lines, visitor.get("photo_path"))

def generate_receipt(visitor: dict, out_path) -> str:
    lines = [
        "CHECKOUT RECEIPT",
        f"Visitor No: {visitor['visitor_number']}",
        f"Name: {visitor['name']}",
        f"Time In: {visitor['check_in_time']}",
        f"Time Out: {visitor['check_out_time']}",
        "Thank you for visiting.",
    ]
    return _write(out_path, lines, visitor.get("checkout_photo_path"))