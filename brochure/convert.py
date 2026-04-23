import os
from fpdf import FPDF

def md_to_pdf(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    lines = md_content.split('\n')
    for line in lines:
        if line.strip().startswith('!') or line.strip().startswith('<img'):
            continue
        
        safe_line = line.replace('\u2013', '-').replace('\u2014', '--').replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
        try:
            safe_line.encode('latin-1')
        except UnicodeEncodeError:
            safe_line = safe_line.encode('ascii', 'replace').decode('ascii')

        if len(safe_line.strip()) == 0:
            pdf.ln(4)
            continue

        if safe_line.startswith('# '):
            pdf.set_font("Helvetica", 'B', 14)
            pdf.multi_cell(0, 8, safe_line[2:])
            pdf.set_font("Helvetica", size=10)
        elif safe_line.startswith('## '):
            pdf.set_font("Helvetica", 'B', 12)
            pdf.multi_cell(0, 8, safe_line[3:])
            pdf.set_font("Helvetica", size=10)
        else:
            pdf.multi_cell(0, 6, safe_line)

    pdf.output(output_file)

if __name__ == "__main__":
    md_to_pdf("d:/kidwall/brochure/combined.md", "d:/kidwall/brochure/colepago_brochure_es.pdf")
