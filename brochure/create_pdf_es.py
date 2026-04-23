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
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_combined_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    files = ['d:/kidwall/brochure/colepago_onepage_brochure_es.md']
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
            mermaid_match = re.search(r'`mermaid.*?`', content, flags=re.DOTALL)
            if mermaid_match:
                before = content[:mermaid_match.start()]
                after = content[mermaid_match.end():]
                content = before + '[ARCHITECTURE_DIAGRAM_IMAGE]' + after
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    pdf.ln(2)
                    continue
                line = line.replace('¿', 'i').replace('ñ', 'n').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                line = line.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
                line = line.encode('latin-1', 'ignore').decode('latin-1')

                if line == '[ARCHITECTURE_DIAGRAM_IMAGE]':
                    try:
                        pdf.ln(5)
                        pdf.image('d:/kidwall/brochure/architecture_diagram_es.png', w=170)
                        pdf.ln(5)
                    except Exception as e:
                        print(f"Error loading image: {e}")
                        pdf.set_font('helvetica', 'I', 10)
                        pdf.set_text_color(255, 0, 0)
                        pdf.multi_cell(0, 8, '[Falta imagen del diagrama de arquitectura]', new_x='LMARGIN', new_y='NEXT')
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
                elif line.startswith('### '):
                    pdf.ln(3)
                    pdf.set_font('helvetica', 'B', 12)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 8, line.replace('### ', ''), new_x='LMARGIN', new_y='NEXT')
                elif line.startswith('- '):
                    pdf.set_font('helvetica', '', 12)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 8, '  - ' + line[2:], new_x='LMARGIN', new_y='NEXT')
                elif 'Seguridad' in line or 'Seguro' in line:
                    pdf.set_font('helvetica', 'B', 12)
                    pdf.set_text_color(255, 0, 0)
                    pdf.multi_cell(0, 8, line, new_x='LMARGIN', new_y='NEXT')
                    pdf.set_text_color(0, 0, 0)
                elif line == '---' or line == '***':
                    pdf.ln(5)
                    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
                    pdf.ln(5)
                else:
                    pdf.set_font('helvetica', '', 12)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 8, line, new_x='LMARGIN', new_y='NEXT')

    pdf.output('d:/kidwall/brochure/colepago_brochure_es.pdf')

if __name__ == '__main__':
    create_combined_pdf()
