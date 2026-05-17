import os
import sys
import xml.etree.ElementTree as ET

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet


styles = getSampleStyleSheet()
H = styles["Heading2"]
N = styles["Normal"]


def text(node, tag):
    if node is None:
        return ""
    el = node.find(tag)
    return el.text if el is not None and el.text else ""


def section(out, title, node):
    out.append(Paragraph(title, H))

    if node is None:
        out.append(Paragraph("-", N))
        out.append(Spacer(1, 10))
        return

    for c in node:
        if c.tag in {"items", "summary", "meta"}:
            continue
        out.append(Paragraph(f"{c.tag}: {c.text or ''}", N))

    out.append(Spacer(1, 10))


def xml_to_pdf(xml_path: str, pdf_path: str):
    root = ET.parse(xml_path).getroot()

    doc = SimpleDocTemplate(pdf_path)
    out = []

    order_id = root.attrib.get("order_id", "")

    # HEADER
    out.append(Paragraph(f"Factura {order_id}", H))
    out.append(Spacer(1, 10))

    # DATE (CRITICAL FIX)
    meta = root.find("meta")
    date = text(meta, "date")
    if date:
        out.append(Paragraph(f"Data: {date}", N))
        out.append(Spacer(1, 10))

    # SUPPLIER / CLIENT
    section(out, "Emitent", root.find("supplier"))
    section(out, "Client", root.find("client"))

    # ITEMS
    out.append(Paragraph("Articole", H))

    table = [["Nume", "Cantitate", "Pret unitar", "Total"]]

    for i in root.findall("./items/item"):
        table.append([
            i.findtext("name", ""),
            i.findtext("qty", ""),
            i.findtext("unit_price", ""),
            i.findtext("total", ""),
        ])

    out.append(Table(table))
    out.append(Spacer(1, 10))

    # SUMMARY (FISCAL STRUCTURE)
    summary = root.find("summary")

    out.append(Paragraph("Rezumat", H))

    if summary is not None:
        summary_table = [["Indicator", "Valoare"]]

        for c in summary:
            summary_table.append([c.tag, c.text or "0"])

        out.append(Table(summary_table))
    else:
        out.append(Paragraph("-", N))

    doc.build(out)


def run(xml_file, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    pdf_path = os.path.join(
        out_dir,
        os.path.splitext(os.path.basename(xml_file))[0] + ".pdf"
    )

    xml_to_pdf(xml_file, pdf_path)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])