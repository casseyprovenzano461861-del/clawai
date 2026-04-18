#!/usr/bin/env python3
"""Convert HTML report to PDF using Playwright Chromium headless."""
import os
import sys

html_path = sys.argv[1] if len(sys.argv) > 1 else "e:/ClawAI/docs/regression_test_report.html"
pdf_path  = sys.argv[2] if len(sys.argv) > 2 else "e:/ClawAI/docs/regression_test_report.pdf"

abs_html = os.path.abspath(html_path)
# Windows path → file:/// URL
file_url = "file:///" + abs_html.replace("\\", "/")
print(f"[*] Source : {abs_html}")
print(f"[*] URL    : {file_url}")
print(f"[*] Output : {pdf_path}")

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(file_url, wait_until="networkidle", timeout=30000)
    page.pdf(
        path=pdf_path,
        format="A4",
        print_background=True,
        margin={"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"},
    )
    browser.close()

size = os.path.getsize(pdf_path)
print(f"[+] PDF created: {pdf_path} ({size // 1024} KB)")
