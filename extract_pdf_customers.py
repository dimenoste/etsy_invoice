from pathlib import Path
from pypdf import PdfReader
import re
import json


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages)


def order_id_from_filename(path: Path) -> str:
    # order_4017111244.pdf -> 4017111244
    return path.stem.split("_")[-1]


def extract_ship_to_block(text: str) -> str:
    # stable anchors in Etsy invoices
    start = text.find("Ship to")
    if start == -1:
        return ""

    end_markers = ["Shop", "Order date", "Payment method"]
    end = len(text)

    for m in end_markers:
        i = text.find(m, start)
        if i != -1:
            end = min(end, i)

    return text[start + len("Ship to"):end].strip()


def parse_ship_to(block: str) -> dict:
    lines = [l.strip() for l in block.split("\n") if l.strip()]

    if not lines:
        return {"name": "", "address": ""}

    name = lines[0]
    address_lines = lines[1:]

    # normalize multi-line address
    address = ", ".join(address_lines)

    return {
        "name": name,
        "address": address
    }


def extract_customer(pdf_path: Path) -> dict:
    text = extract_text(pdf_path)
    block = extract_ship_to_block(text)
    return parse_ship_to(block)


def load_pdf_customers(pdf_dir: Path) -> dict:
    """
    returns:
    {
        order_id: {name, address}
    }
    """
    result = {}

    for pdf in pdf_dir.glob("*.pdf"):
        order_id = order_id_from_filename(pdf)
        result[order_id] = extract_customer(pdf)

    return result


if __name__ == "__main__":
    import sys

    pdf_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    data = load_pdf_customers(pdf_dir)

    for order_id, customer in data.items():
        (out_dir / f"{order_id}.json").write_text(
            json.dumps(customer, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )