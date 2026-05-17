import csv
import re
import json
import xml.etree.ElementTree as ET

from pathlib import Path
from collections import defaultdict
from decimal import Decimal
from xml.dom import minidom


ORDER_RE = re.compile(r"Order\s*#(\d+)", re.I)


# =========================================================
# HELPERS
# =========================================================

def norm(x):
    return x.strip().lower() if x else ""


def money(x):
    if not x or x == "--":
        return Decimal("0")

    x = (
        x.replace("€", "")
         .replace("$", "")
         .replace(",", ".")
         .strip()
    )

    x = re.sub(r"[^0-9.\-]", "", x)

    try:
        return Decimal(x)
    except:
        return Decimal("0")


def pretty(xml):
    return minidom.parseString(
        ET.tostring(xml, encoding="utf-8")
    ).toprettyxml(indent="  ")


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def get_order_id(row):
    for v in row.values():
        m = ORDER_RE.search(str(v))
        if m:
            return m.group(1)
    return None


def group_orders(rows):
    grouped = defaultdict(list)

    for row in rows:
        oid = get_order_id(row)

        if oid:
            grouped[oid].append(row)

    return grouped


# =========================================================
# PDF CUSTOMER EXTRACTION RESULTS
# =========================================================

def load_pdf_map(path: Path):
    """
    loads:
        customers_out/4017111244.json
    """

    result = {}

    if not path.exists():
        return result

    for f in path.glob("*.json"):
        result[f.stem] = json.loads(
            f.read_text(encoding="utf-8")
        )

    return result


def apply_pdf_customer(root, pdf_map, order_id):
    client = root.find("client")

    if client is None:
        client = ET.SubElement(root, "client")

    if order_id not in pdf_map:
        return

    data = pdf_map[order_id]

    ET.SubElement(client, "name").text = data.get("name", "")
    ET.SubElement(client, "address").text = data.get("address", "")


# =========================================================
# XML GENERATION
# =========================================================

def build_invoice(order_id, rows, supplier, pdf_map):

    root = ET.Element(
        "invoice",
        {
            "order_id": order_id,
            "schema": "ANAF_RO_MIN"
        }
    )

    # =====================================================
    # SUPPLIER
    # =====================================================

    supplier_el = ET.SubElement(root, "supplier")

    for k, v in supplier.items():
        ET.SubElement(supplier_el, k).text = str(v)

    # =====================================================
    # CLIENT
    # =====================================================

    ET.SubElement(root, "client")

    apply_pdf_customer(
        root,
        pdf_map,
        order_id
    )

    # =====================================================
    # DATE
    # =====================================================

    invoice_date = ""

    for r in rows:
        if r.get("Date"):
            invoice_date = r["Date"]
            break

    meta = ET.SubElement(root, "meta")
    ET.SubElement(meta, "date").text = invoice_date

    # =====================================================
    # FINANCIAL COMPUTATION
    # =====================================================

    gross_sale = Decimal("0")

    transaction_fee = Decimal("0")
    processing_fee = Decimal("0")
    sales_tax = Decimal("0")

    item_title = ""

    for r in rows:

        t = norm(r.get("Type"))
        title = r.get("Title", "")

        # -----------------------------
        # SALE
        # -----------------------------

        if t == "sale":
            gross_sale += money(r.get("Amount"))

        # -----------------------------
        # FEES
        # -----------------------------

        elif t == "fee":

            fee_value = abs(
                money(r.get("Fees & Taxes"))
            )

            if "transaction fee" in title.lower():
                transaction_fee += fee_value

                # recover product title
                if not item_title:
                    item_title = (
                        title
                        .replace("Transaction fee:", "")
                        .strip()
                    )

            elif "processing fee" in title.lower():
                processing_fee += fee_value

        # -----------------------------
        # TAX
        # -----------------------------

        elif t == "tax":
            sales_tax += abs(
                money(r.get("Fees & Taxes"))
            )

    # fallback
    if not item_title:
        item_title = f"Comanda Etsy #{order_id}"

    # =====================================================
    # ITEMS
    # =====================================================

    items = ET.SubElement(root, "items")

    item = ET.SubElement(items, "item")

    ET.SubElement(item, "name").text = item_title
    ET.SubElement(item, "qty").text = "1"
    ET.SubElement(item, "unit_price").text = str(gross_sale)
    ET.SubElement(item, "total").text = str(gross_sale)

    # =====================================================
    # SUMMARY
    # =====================================================

    summary = ET.SubElement(root, "summary")

    ET.SubElement(summary, "subtotal").text = str(gross_sale)

    ET.SubElement(
        summary,
        "transaction_fee"
    ).text = str(transaction_fee)

    ET.SubElement(
        summary,
        "processing_fee"
    ).text = str(processing_fee)

    ET.SubElement(
        summary,
        "sales_tax"
    ).text = str(sales_tax)

    net = (
        gross_sale
        - transaction_fee
        - processing_fee
        - sales_tax
    )

    ET.SubElement(summary, "net").text = str(net)

    ET.SubElement(summary, "total").text = str(gross_sale)

    return root


# =========================================================
# MAIN
# =========================================================

def main():

    rows = read_csv("etsy_payments.csv")

    grouped = group_orders(rows)

    supplier = json.loads(
        Path("supplier.example.json")
        .read_text(encoding="utf-8")
    )["supplier"]

    pdf_map = load_pdf_map(
        Path("./customers_out")
    )

    out_dir = Path("./invoices")

    out_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    for order_id, order_rows in grouped.items():

        xml = build_invoice(
            order_id,
            order_rows,
            supplier,
            pdf_map
        )

        out_file = (
            out_dir
            / f"invoice_{order_id}.xml"
        )

        out_file.write_text(
            pretty(xml),
            encoding="utf-8"
        )

        print(f"generated {out_file}")


if __name__ == "__main__":
    main()