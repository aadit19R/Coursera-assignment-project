"""Build the Times New Roman report using actual VS Code output screenshots."""
import ast
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import textwrap

import nbformat
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, XPreformatted,
)

ROOT = Path(__file__).resolve().parents[1]
STEM = "48_Aadit_Rangnekar_CaseStudyB"
WIDTH = A4[0] - 144
TABLES = "Customers Restaurants MenuItems DeliveryAgents Orders OrderItems Payments Reviews".split()
FONT_DIR = Path("/System/Library/Fonts/Supplemental")
for name, file in [("TNR", "Times New Roman.ttf"), ("TNRBold", "Times New Roman Bold.ttf"),
                   ("TNRItalic", "Times New Roman Italic.ttf"), ("Code", "Courier New.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNRBold", italic="TNRItalic", boldItalic="TNRBold")
STYLES = {
    "body": ParagraphStyle("body", fontName="TNR", fontSize=11, leading=14.5, spaceAfter=8),
    "part": ParagraphStyle("part", fontName="TNRBold", fontSize=14, leading=18, spaceAfter=10, keepWithNext=True),
    "sub": ParagraphStyle("sub", fontName="TNRBold", fontSize=12, leading=15, spaceBefore=9, spaceAfter=6, keepWithNext=True),
    "label": ParagraphStyle("label", fontName="TNRBold", fontSize=11, leading=14, spaceBefore=5, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="TNR", fontSize=11, leading=13.5),
    "head": ParagraphStyle("head", fontName="TNRBold", fontSize=11, leading=13.5),
    "caption": ParagraphStyle("caption", fontName="TNRItalic", fontSize=11, leading=14, spaceAfter=8),
    "center": ParagraphStyle("center", fontName="TNR", fontSize=11, leading=16, alignment=TA_CENTER, spaceAfter=2),
    "center_bold": ParagraphStyle("center_bold", fontName="TNRBold", fontSize=12, leading=16, alignment=TA_CENTER, spaceAfter=2),
    "code": ParagraphStyle("code", fontName="Code", fontSize=9, leading=11.4,
                           textColor=colors.HexColor("#E5E5E5"), backColor=colors.HexColor("#16181A"),
                           borderPadding=6, spaceBefore=3, spaceAfter=10, allowWidows=0, allowOrphans=0),
}


def paragraph(text, style="body"):
    text = escape(str(text)).replace("\n", "<br/>")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return Paragraph(text, STYLES[style])


def grid(rows, widths, padding=4):
    content = [[paragraph(value, "head" if i == 0 else "cell") for value in row]
               for i, row in enumerate(rows)]
    result = Table(content, colWidths=widths, hAlign="LEFT", repeatRows=1)
    result.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), .45, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]))
    return result


def code(source):
    lines = []
    for line in source.splitlines():
        lines.extend(textwrap.wrap(line, width=80, subsequent_indent="    ",
                                   replace_whitespace=False, drop_whitespace=False) or [""])
    return XPreformatted(escape("\n".join(lines)), STYLES["code"])


class HTMLTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.value, self.active = [], [], "", False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        if tag in ("td", "th"):
            self.value, self.active = "", True

    def handle_data(self, text):
        if self.active:
            self.value += text

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self.row.append(self.value.strip())
            self.active = False
        if tag == "tr" and self.row:
            self.rows.append(self.row)


def result_rows(cell):
    output = next(o for o in cell.outputs if "text/html" in o.get("data", {}))
    parser = HTMLTable()
    parser.feed(output.data["text/html"])
    rows = parser.rows
    return [row[1:] for row in rows] if rows[0][0] == "" else rows


def fingerprint(notebook):
    payload = [(c.source, c.outputs) for c in notebook.cells if c.cell_type == "code"]
    return sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def screenshot(name, manifest):
    path = ROOT / "output" / "screenshots" / manifest["images"][name]["file"]
    image = Image(str(path), hAlign="LEFT")
    factor = min(.34, WIDTH / image.imageWidth)
    image.drawWidth, image.drawHeight = image.imageWidth * factor, image.imageHeight * factor
    return image


def build_report(notebook_path=ROOT / f"{STEM}.ipynb"):
    notebook = nbformat.read(notebook_path, as_version=4)
    cells = [c for c in notebook.cells if c.cell_type == "code"]
    live = all(c.execution_count is not None and c.outputs and
               not any(o.output_type == "error" for o in c.outputs) for c in cells)
    manifest_path = ROOT / "output" / "screenshots" / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    needed = ["connection", "reset", "tables", "insertion", "close", *notebook.metadata.assignment.schema,
              "q1", "q2", "q3", "q4", "q5"]
    screenshots_ready = manifest.get("fingerprint") == fingerprint(notebook) and all(
        (ROOT / "output" / "screenshots" / manifest.get("images", {}).get(key, {}).get("file", "missing")).is_file()
        for key in needed
    )
    complete = live and screenshots_ready
    output = ROOT / "output" / "pdf" / f"{STEM}{'' if complete else '_DRAFT'}.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    by_role = {c.metadata.get("role"): c for c in cells if c.metadata.get("role") != "query"}
    queries = [c for c in cells if c.metadata.get("role") == "query"]
    story = []

    def output_image(key, cell):
        if screenshots_ready:
            return screenshot(key, manifest)
        text = "VS Code screenshot pending."
        return paragraph(text, "caption")

    def code_and_output(cell, key):
        group = [paragraph("Code:", "label"), code(cell.source),
                 paragraph("Output (VS Code screenshot):", "label"), output_image(key, cell), Spacer(1, 9)]
        story.extend([KeepTogether(group)] if len(cell.source.splitlines()) <= 22 else group)

    # Part 1: match the reference's academic cover and plain bordered table.
    for text, style in [
        ("SVKM's NMIMS", "center_bold"),
        ("Mukesh Patel School of Technology, Management and Engineering", "center_bold"),
        ("Department of Computer Engineering", "center_bold"),
        ("CSEDS, Semester V", "center"),
        ("Coursera Course: Database and SQL for Data Science with Python", "center"),
        ("Case Study Assignment (30 Marks)", "center"),
    ]:
        story.append(paragraph(text, style))
    story += [Spacer(1, 44), paragraph("Part 1: Cover page", "part")]
    cover = []
    for line in notebook.cells[0].source.splitlines():
        if line.strip().startswith("|"):
            values = [s.strip() for s in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", value) for value in values):
                cover.append(values)
    cover = [[{"Case study": "Case study allotted", "Database": "Database used"}.get(a, a), b] for a, b in cover]
    story.append(grid(cover, [165, WIDTH - 165]))
    if not complete:
        story += [Spacer(1, 18), paragraph("DRAFT - execution or VS Code screenshots pending", "sub")]

    # Part 2: all attributes, relationships, and a standalone ER image page.
    story += [PageBreak(), paragraph("Part 2: Schema design", "part"),
              paragraph("The QuickBite scenario is represented by eight related MySQL tables. IDs and quantities use INT, money uses DECIMAL, dates use DATE or DATETIME, and text uses VARCHAR or TEXT. The types and constraints are listed below.")]
    for i, name in enumerate(TABLES, 1):
        columns = notebook.metadata.assignment.schema[name]
        if i in (4, 7):
            story.append(PageBreak())
        story += [paragraph(f"{i}. {name}", "sub"),
                  grid([["Column", "Data type", "Constraints"], *columns], [112, 94, WIDTH - 206]), Spacer(1, 7)]
        if name == "OrderItems":
            story.append(paragraph("Additional constraint: UNIQUE (order_id, item_id)."))
    story += [paragraph("Relationships", "sub"),
              paragraph("Customers, restaurants and delivery agents link to many orders; restaurants offer many menu items. OrderItems links orders to items. Each order has one payment and an optional review; reviews also reference customers."),
              PageBreak(), paragraph("ER diagram", "sub")]
    er_path = ROOT / "er_diagram.png"
    if er_path.exists():
        image = Image(str(er_path), width=WIDTH, height=WIDTH * 430 / 530)
        story += [image, Spacer(1, 7), paragraph("Figure 1: ER diagram (primary and foreign keys only).", "caption"),
                  paragraph("1 = one; 0..N = zero or many; 1..N = one or many; 0..1 = optional one."),
                  paragraph("Payments.order_id and Reviews.order_id are UNIQUE. Every seeded order has a payment and at least one item; reviews are optional.")]
    else:
        story.append(paragraph("ER image pending."))

    # Parts 3-5: actual source followed by genuine VS Code screenshots.
    story += [PageBreak(), paragraph("Part 3: Python-SQL connectivity code", "part"),
              paragraph("I used mysql.connector to connect Python to the local MySQL server and pandas to display results. Connection settings are loaded from the private .env file, so the password is not embedded in the code or report.")]
    code_and_output(by_role["connect"], "connection")
    story += [paragraph("Reset assignment database", "sub"),
              paragraph("This guarded cell drops and recreates only quickbite_roll48. Running the notebook from the beginning therefore creates fresh data for each screenshot session.")]
    code_and_output(by_role["reset"], "reset")
    story += [PageBreak(), paragraph("Part 4: Table creation code", "part"),
              paragraph("Parent tables are created before child tables. The dictionary contains the eight definitions; the loop executes them using InnoDB and SHOW TABLES lists the resulting tables.")]
    parent_ddl, child_ddl = by_role["ddl"].source.split('    "Orders":', 1)
    story += [paragraph("Code:", "label"), code(parent_ddl.rstrip()), PageBreak(),
              paragraph("Table creation code (continued)", "sub"), code('    "Orders":' + child_ddl),
              paragraph("Output (VS Code screenshot):", "label"), output_image("tables", by_role["ddl"])]
    story += [PageBreak(), paragraph("Part 5: Data insertion code", "part"),
              paragraph("The 46 original fictional records span Mumbai, Pune and Nashik. Tables are populated in the prescribed order, with at least five rows each. Payment amounts match item totals; failed payments represent attempted amounts. Parameterized inserts are committed together or rolled back on error.")]
    seed_source, transaction = by_role["insert"].source.split("\ntry:", 1)
    parent_data, child_data = seed_source.split('    "Orders":', 1)
    story += [paragraph("Code:", "label"), code(parent_data.rstrip()), PageBreak(),
              paragraph("Data insertion code (continued)", "sub"), code('    "Orders":' + child_data),
              KeepTogether([code("try:" + transaction)]),
              paragraph("Output (VS Code screenshot):", "label"), output_image("insertion", by_role["insert"]),
              PageBreak(), paragraph("Contents of every table", "sub"),
              paragraph("Code:", "label"), code(by_role["contents"].source)]
    for i, name in enumerate(TABLES):
        if i == 4:
            story.append(PageBreak())
        story += [KeepTogether([paragraph(f"Table: {name}", "label"),
                               output_image(name, by_role["contents"])]), Spacer(1, 8)]

    # Part 6: one query per page, with the reference's (a)-(d) arrangement.
    rows_by_query = []
    for i, cell in enumerate(queries, 1):
        story.append(PageBreak())
        if i == 1:
            story += [paragraph("Part 6: Query execution and results", "part"),
                      paragraph("Each query uses GROUP BY and at most one join. Q1, Q3 and Q4 use joins; Q2 and Q3 use HAVING. Together they use COUNT, AVG, SUM and MAX. Monetary results are in INR.")]
        question_cell = next(c for c in notebook.cells if c.metadata.get("role") == "question" and c.metadata.get("query") == i)
        question, note = question_cell.source.split("\n\n", 2)[1:]
        sql = ast.literal_eval(ast.parse(cell.source).body[0].value.args[0]).strip()
        rows = result_rows(cell) if live else [["Output pending"]]
        rows_by_query.append(rows)
        story += [paragraph(f"Query {i}", "sub"), paragraph(f"**(a) Question:** {question}"),
                  paragraph("(b) SQL query:", "label"), code(sql),
                  paragraph("(c) Python execution cell:", "label"), code(cell.source),
                  paragraph("(d) Output (VS Code screenshot):", "label"), output_image(f"q{i}", cell)]
        if live:
            story.append(paragraph(f"Rows returned: {len(rows) - 1}"))
        story.append(paragraph(note))
        if i == len(queries):
            story.append(paragraph("Closing the connection", "sub"))
            code_and_output(by_role["close"], "close")

    # Summary uses full query outputs, avoiding pandas' truncated long strings.
    story += [PageBreak(), paragraph("Summary of results", "sub")]
    labels = [["Restaurant", "Items", "Average price"], ["Payment mode", "Total collected"],
              ["Customer", "Orders"], ["Agent", "Orders"], ["Category", "Items", "Highest price"]]
    notes = ast.literal_eval(ast.parse(by_role["summary"].source).body[1].value)
    summary = [[paragraph(t, "head") for t in ["Query", "Output", "Rows returned", "Interpretation"]]]
    for i, rows in enumerate(rows_by_query):
        widths = [112, 36, 60] if i in (0, 4) else [130, 78]
        inner_rows = [labels[i], *rows[1:]] if live else [["Output pending"]]
        inner = grid(inner_rows, widths if live else [208], padding=2)
        summary.append([paragraph(f"Q{i + 1}"), inner, paragraph(len(rows) - 1 if live else "Pending"), paragraph(notes[i])])
    result = Table(summary, colWidths=[40, 220, 54, WIDTH - 314], hAlign="LEFT", repeatRows=1)
    result.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), .45, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [result, Spacer(1, 16)]
    conclusion = next(c.source for c in notebook.cells if c.metadata.get("part") == 7)
    conclusion_parts = conclusion.split("\n\n")
    story += [KeepTogether([paragraph("Part 7: Conclusion", "part"),
                           *[paragraph(p.strip()) for p in conclusion_parts[1:] if p.strip()]])]

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("TNR", 9)
        canvas.drawCentredString(A4[0] / 2, 29, str(document.page))
        if not complete:
            canvas.setFont("TNR", 9)
            canvas.drawRightString(A4[0] - 72, A4[1] - 28, "DRAFT - evidence pending")
        canvas.restoreState()

    document = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=72, rightMargin=72,
                                 topMargin=72, bottomMargin=50,
                                 title="QuickBite Online Food Delivery - Roll 48",
                                 author="Aadit Rangnekar")
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Created {output.name}; native VS Code screenshots: {screenshots_ready}")
    return output


if __name__ == "__main__":
    build_report()
