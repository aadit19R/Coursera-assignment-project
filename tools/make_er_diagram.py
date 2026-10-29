"""Draw the project's ER image with the reference report's simple box style."""
from pathlib import Path

import pymupdf
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = Path("/System/Library/Fonts/Supplemental")


def make_diagram():
    for name, file in [("ERBody", "Times New Roman.ttf"), ("ERBold", "Times New Roman Bold.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
    master = ROOT / "tmp" / "pdfs" / "er_master.pdf"
    master.parent.mkdir(parents=True, exist_ok=True)
    drawing = canvas.Canvas(str(master), pagesize=(530, 430))
    drawing.setTitle("QuickBite ER diagram - Roll 48")
    drawing.setLineWidth(0.8)

    def box(name, x, y, height, keys):
        drawing.setFillColorRGB(1, 1, 1)
        drawing.rect(x, y, 150, height, fill=1, stroke=1)
        drawing.line(x, y + height - 24, x + 150, y + height - 24)
        drawing.setFillColorRGB(0, 0, 0)
        drawing.setFont("ERBold", 12)
        drawing.drawCentredString(x + 75, y + height - 16, name)
        drawing.setFont("ERBody", 11)
        for i, key in enumerate(keys):
            drawing.drawString(x + 8, y + height - 43 - 17 * i, key)

    def link(start, end, labels):
        drawing.line(*start, *end)
        drawing.setFont("ERBody", 10)
        for text, x, y in labels:
            drawing.drawString(x, y, text)

    # Nine foreign-key relationships. Optionality follows this project's schema.
    link((85, 355), (85, 282), [("1", 91, 339), ("0..N", 91, 294)])
    link((145, 355), (210, 282), [("1", 141, 340), ("0..N", 162, 299)])
    link((265, 355), (265, 282), [("1", 272, 339), ("0..N", 272, 295)])
    link((402, 355), (320, 282), [("1", 397, 341), ("0..N", 350, 301)])
    link((445, 355), (445, 282), [("1", 452, 339), ("0..N", 452, 295)])
    link((160, 219), (190, 219), [("0..1", 161, 226), ("1", 182, 226)])
    link((265, 170), (265, 96), [("1", 272, 155), ("1", 272, 108)])
    link((318, 170), (396, 112), [("1", 316, 151), ("1..N", 394, 128)])
    link((445, 190), (445, 112), [("1", 452, 175), ("0..N", 452, 124)])

    box("Customers", 10, 355, 62, ["PK: customer_id"])
    box("DeliveryAgents", 190, 355, 62, ["PK: agent_id"])
    box("Restaurants", 370, 355, 62, ["PK: restaurant_id"])
    box("Reviews", 10, 170, 112, ["PK: review_id", "FK: order_id (UNIQUE)", "FK: customer_id"])
    box("Orders", 190, 170, 112, ["PK: order_id", "FK: customer_id", "FK: restaurant_id", "FK: agent_id"])
    box("MenuItems", 370, 190, 92, ["PK: item_id", "FK: restaurant_id"])
    box("Payments", 190, 20, 76, ["PK: payment_id", "FK: order_id (UNIQUE)"])
    box("OrderItems", 370, 20, 92, ["PK: order_item_id", "FK: order_id", "FK: item_id"])
    drawing.save()
    document = pymupdf.open(master)
    output = ROOT / "er_diagram.png"
    document[0].get_pixmap(matrix=pymupdf.Matrix(4, 4)).save(output)
    print(f"Created {output.name} (2120 x 1720 pixels)")
    return output


if __name__ == "__main__":
    make_diagram()
