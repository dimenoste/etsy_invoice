# Etsy : Invoice Generation Pipeline

---

## System Overview

Pipeline transforms Etsy exports into invoices for personal accounting.

Inputs:
- Etsy Payments CSV (`etsy_payments.csv`)
- Etsy PDF invoices (`./etsy_invoice_pdf/`)

Outputs:
- Structured XML invoices (`./invoices/`)
- Rendered PDFs (`./pdf/`)
- Extracted customer data (`./customers_out`)

----

***👉 Open the example PDF here :*** [View example PDF](example_generated_invoice/invoice_0000012345.pdf)
-----
---

## 1. System Flow (Data Lineage)

```
Etsy PDF invoices
   ./etsy_invoice_pdf/
        │
        │  (extract_pdf_customers.py)
        ▼
Customer JSON store
   ./customers_out/<order_id>.json
        │
        │
Etsy Payments CSV (financial ledger)
   etsy_payments.csv
        │
        │ (etsy_invoice_xml.py)
        ▼
XML invoice
   ./invoices/invoice_<order_id>.xml
        │
        │ (convert_xml_to_pdf.py)
        ▼
Final PDF invoice
   ./pdf/invoice_<order_id>.pdf
```

---

## 2. Step-by-step Execution

### Install dependencies
```bash
uv add reportlab pypdf
```

---

### Step 1 — Extract customer identity from Etsy PDF invoices
```bash
uv run python extract_pdf_customers.py \
    ./etsy_invoice_pdf \
    ./customers_out
```

Output:
```
./customers_out/<order_id>.json
```

Contains:
- buyer name
- shipping address

---

### Step 2 — Generate XML invoices from CSV + extracted customers
```bash
uv run python etsy_invoice_xml.py
```

Output:
```
./invoices/invoice_<order_id>.xml
```

Each XML contains:
- supplier (issuer)
- client (from PDF extraction)
- order date (from CSV)
- item representation
- financial summary (fees, taxes, net)

---

### Step 3 — Convert single XML → PDF
```bash
uv run python convert_xml_to_pdf.py \
    ./invoices/invoice_<order_id>.xml \
    ./pdf
```

---

### Step 4 — Batch conversion (all invoices)
```bash
mkdir -p pdf

for f in ./invoices/*.xml; do
    uv run python convert_xml_to_pdf.py "$f" ./pdf
done
```

---

## 3. Full Pipeline (single execution)

Create script:

```bash
nano run_pipeline.sh
```

Paste:

```bash
#!/bin/bash
set -e

uv add reportlab pypdf

uv run python extract_pdf_customers.py \
    ./etsy_invoice_pdf \
    ./customers_out

uv run python etsy_invoice_xml.py

mkdir -p pdf

for f in ./invoices/*.xml; do
    uv run python convert_xml_to_pdf.py "$f" ./pdf
done
```

Make executable:
```bash
chmod +x run_pipeline.sh
```

Run:
```bash
./run_pipeline.sh
```

---

## Output Structure

```
./customers_out/   → extracted buyer identity (JSON)
./invoices/        → XML invoices
./pdf/             → final PDFs
```

---

## Financial Model (Important)

Per order:

Revenue:
```
sum(Sale rows)
```

Costs:
- transaction fees
- processing fees
- sales tax

Net:
```
net = revenue − transaction fees − processing fees − sales tax
```

---

## Known Missing Components

Not yet included in computation:

- listing fees (Etsy per-listing charges)
- Etsy Ads / marketing costs

Impact:
- expenses are underestimated
- net profit is overstated

---

## Accounting Interpretation

System produces:
```
operational invoice-level fiscal reconstruction
```

It is suitable for:
- per-order reporting
- simplified accounting export
- audit traceability

To be done:
- One final aggregated montly invoice with the super net amount (missing marketing + listing costs)
