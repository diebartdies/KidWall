from fpdf import FPDF # type: ignore
import re

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(78, 115, 223)
        self.cell(0, 10, 'ColePago Student Wallet', new_x='LMARGIN', new_y='NEXT', align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_combined_pdf():
    files = [
        'd:/kidwall/brochure/colepago_wallet_brochure.md',
        'd:/kidwall/brochure/colepago_onepage_brochure.md',
        'd:/kidwall/brochure/colepago_architecture_diagram.md'
    ]
    
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = content.encode('ascii', 'ignore').decode('ascii')
            # Insert architecture diagram image when mermaid diagram is found
            mermaid_match = re.search(r'```mermaid.*?```', content, flags=re.DOTALL)
            if mermaid_match:
                before = content[:mermaid_match.start()]
                after = content[mermaid_match.end():]
                content = before + '[ARCHITECTURE_DIAGRAM_IMAGE]' + after
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line == '[ARCHITECTURE_DIAGRAM_IMAGE]':
                    try:
                        pdf.ln(5)
                        pdf.image('d:/kidwall/brochure/architecture_diagram.png', w=170)
                        pdf.ln(5)
                    except Exception as e:
                        pdf.set_font('helvetica', 'I', 10)
                        pdf.set_text_color(255, 0, 0)
                        pdf.multi_cell(0, 8, '[Architecture diagram image missing]', new_x='LMARGIN', new_y='NEXT')
                        pdf.set_text_color(0, 0, 0)
                elif line.startswith('# '):
                    pdf.ln(10)
                    pdf.set_font('helvetica', 'B', 16)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 10, line.replace('# ', ''), new_x='LMARGIN', new_y='NEXT')
                elif line.startswith('## '):
                    pdf.ln(5)
                    pdf.set_font('helvetica', 'B', 14)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 10, line.replace('## ', ''), new_x='LMARGIN', new_y='NEXT')
                elif line.startswith('- '):
                    pdf.set_font('helvetica', '', 12)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 8, '  - ' + line[2:], new_x='LMARGIN', new_y='NEXT')
                elif line == '':
                    pdf.ln(2)
                elif 'Security' in line or 'Secure' in line:
                    pdf.set_font('helvetica', 'B', 12)
                    pdf.set_text_color(255, 0, 0)
                    pdf.multi_cell(0, 8, line, new_x='LMARGIN', new_y='NEXT')
                    pdf.set_text_color(0, 0, 0)
                else:
                    pdf.set_font('helvetica', '', 12)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 8, line, new_x='LMARGIN', new_y='NEXT')

    pdf.output('d:/kidwall/brochure/colepago_complete_brochure.pdf')

if __name__ == '__main__':
    create_combined_pdf()
