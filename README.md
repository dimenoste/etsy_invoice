# Etsy : Invoice Generation Pipeline

---

## System Overview

Pipeline transforms Etsy exports into invoices for personal accounting.

## Etsy Input Files Required

Two data sources are required to generate invoices correctly.

---

## 1. Etsy CSV Transaction Statements

This file contains structured financial data for all orders.

It is used to extract:

- order IDs
- revenue (sales)
- transaction fees
- processing fees
- listing fees (if present)
- advertising / marketing costs (if present)
- tax amounts
- timestamps / order dates

This file is the **source of truth for all financial calculations**.

---

## 2. Etsy Client Invoice PDFs

These are the official invoices sent to customers by Etsy.

They are used to extract:

- buyer name
- buyer address
- order reference number (order ID)

These PDFs provide **customer identity information missing from the CSV**.

---

## Required Folder Structure

All client invoice PDFs must be stored in the following directory:

```text
etsy_invoice_pdf/
```

---

## File Naming Convention

Each PDF must follow this exact format:

```text
order_<order_number>.pdf
```

---

## Example

Order number:

```text
0000012345
```

Correct file path:

```text
etsy_invoice_pdf/order_0000012345.pdf
```

---

## Consistency Rules

Each order must satisfy all of the following:

- Exists in the CSV file
- Has a corresponding PDF file
- Uses the same order number in both sources
- PDF filename matches the CSV order ID exactly

If any mismatch exists, that order cannot be reliably processed for invoice generation.


Inputs:
- Etsy Payments CSV (`etsy_payments.csv`)
- Etsy PDF invoices (`./etsy_invoice_pdf/`)

Outputs:
- Structured XML invoices (`./invoices/`)
- Rendered PDFs (`./pdf/`)
- Extracted customer data (`./customers_out`)

----

***👉 Open the example PDF here :*** [View example PDF](etsy_invoice_pdf/order_123456789.pdf)
-----


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
