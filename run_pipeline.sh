#!/bin/bash

uv add reportlab pypdf

uv run python extract_pdf_customers.py \
    ./etsy_invoice_pdf \
    ./customers_out

uv run python etsy_invoice_xml.py

mkdir -p pdf

for f in ./invoices/*.xml; do
    uv run python convert_xml_to_pdf.py "$f" ./pdf
done