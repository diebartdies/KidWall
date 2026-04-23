from fpdf import FPDF # type: ignore
from fpdf.enums import XPos, YPos # type: ignore
import re

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(74, 144, 226)
        self.cell(0, 10, 'ColePago Wallet', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} - ColePago 2026', 0, 0, 'C')

def clean_text(text):
    # Replace non-latin1 characters with equivalents
    replacements = {
        '\u2013': '-', # en-dash
        '\u2014': '--', # em-dash
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2022': '*', # bullet
        '\u2026': '...', # ellipsis
        '\ud83d\ude80': '[Rocket]', # 🚀
        '\ud83d\udcb3': '[Card]',   # 💳
        '\ud83d\udee0': '[Tools]',  # 🛠️
        '\ud83d\udcf1': '[Mobile]', # 📱
        '\ud83c\udfa8': '[Design]', # 🎨
        '🚀': '[Rocket]',
        '💳': '[Payment]',
        '🛠️': '[Stack]',
        '📱': '[Mobile]',
        '🎨': '[Design]'
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

def create_pdf(md_path, pdf_path):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        line = clean_text(line)
        if not line:
            pdf.ln(5)
            continue
            
        if line.startswith('# '):
            pdf.set_font('Helvetica', 'B', 18)
            pdf.set_text_color(74, 144, 226)
            pdf.cell(0, 15, line[2:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif line.startswith('## '):
            pdf.ln(5)
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(245, 166, 35)
            pdf.cell(0, 10, line[3:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif line.startswith('- '):
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(51, 51, 51)
            parts = re.split(r'(\*\*.*?\*\*)', line[2:])
            pdf.write(5, "  - ")
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    pdf.set_font('Helvetica', 'B', 11)
                    pdf.write(5, part[2:-2])
                    pdf.set_font('Helvetica', '', 11)
                else:
                    pdf.write(5, part)
            pdf.ln(7)
        elif line.startswith('---'):
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
        else:
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(51, 51, 51)
            pdf.multi_cell(0, 7, line)

    pdf.output(pdf_path)

if __name__ == "__main__":
    create_pdf("d:/kidwall/brochure/colepago_wallet_brochure.md", "d:/kidwall/brochure/colepago_wallet_brochure.pdf")
    print("PDF generated successfully.")
