"""Generate a deterministic synthetic invoice PDF for the lab.

This is a synthetic document created for workshop MAIS-WS1 activity A2. It is not a
real invoice. The contents are fixed so verify.py can assert against known values.
No binary asset ships with the lab: you render this PDF locally instead.

Run with reportlab available:
  uv run --no-project --with reportlab python make_sample_invoice.py
"""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

OUTPUT_PDF = "sample_invoice.pdf"

# Known, fixed contents. verify.py and the acceptance gate assert against these.
SUPPLIER = "Northwind Traders"
INVOICE_NUMBER = "INV-2048"
INVOICE_DATE = "2026-07-15"
LINE_ITEMS = [
    # (description, quantity, unit_price, amount)
    ("Widget A", 10, 12.50, 125.00),
    ("Widget B", 4, 30.00, 120.00),
    ("Service fee", 1, 55.00, 55.00),
]
TOTAL = 300.00


def build_pdf(path: str = OUTPUT_PDF) -> str:
    c = canvas.Canvas(path, pagesize=LETTER)
    width, height = LETTER
    y = height - inch

    c.setFont("Helvetica-Bold", 18)
    c.drawString(inch, y, "INVOICE")
    y -= 0.4 * inch

    c.setFont("Helvetica", 11)
    c.drawString(inch, y, f"Supplier: {SUPPLIER}")
    y -= 0.25 * inch
    c.drawString(inch, y, f"Invoice number: {INVOICE_NUMBER}")
    y -= 0.25 * inch
    c.drawString(inch, y, f"Date: {INVOICE_DATE}")
    y -= 0.5 * inch

    # Table header.
    c.setFont("Helvetica-Bold", 11)
    c.drawString(inch, y, "Description")
    c.drawString(4.0 * inch, y, "Qty")
    c.drawString(4.8 * inch, y, "Unit price")
    c.drawString(6.2 * inch, y, "Amount")
    y -= 0.1 * inch
    c.line(inch, y, 7.5 * inch, y)
    y -= 0.25 * inch

    # Table rows.
    c.setFont("Helvetica", 11)
    for description, qty, unit_price, amount in LINE_ITEMS:
        c.drawString(inch, y, description)
        c.drawString(4.0 * inch, y, str(qty))
        c.drawString(4.8 * inch, y, f"{unit_price:.2f}")
        c.drawString(6.2 * inch, y, f"{amount:.2f}")
        y -= 0.25 * inch

    y -= 0.1 * inch
    c.line(inch, y, 7.5 * inch, y)
    y -= 0.3 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(4.8 * inch, y, "Total")
    c.drawString(6.2 * inch, y, f"{TOTAL:.2f}")

    c.showPage()
    c.save()
    return path


if __name__ == "__main__":
    out = build_pdf()
    print(f"Wrote {out} (synthetic invoice: {SUPPLIER}, {INVOICE_NUMBER}, total {TOTAL:.2f})")
