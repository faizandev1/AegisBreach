from fpdf import FPDF
import datetime
from utils.logger import logger

class ReportGenerator:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)

    def create_report(self, title, content, filename="report.pdf"):
        self.pdf.add_page()
        # Title
        self.pdf.set_font("Arial", 'B', 20)
        self.pdf.cell(0, 10, title, ln=True, align='C')
        self.pdf.ln(10)
        # Timestamp
        self.pdf.set_font("Arial", '', 10)
        self.pdf.cell(0, 10, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        self.pdf.ln(5)
        # Content
        self.pdf.set_font("Arial", '', 12)
        for line in content.split('\n'):
            self.pdf.multi_cell(0, 8, line)
        self.pdf.output(filename)
        logger.info(f"Report saved to {filename}")
        return filename