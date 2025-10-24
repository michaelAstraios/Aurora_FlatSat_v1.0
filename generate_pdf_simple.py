#!/usr/bin/env python3
"""
FlatSat Simulator Plan PDF Generator (Simplified)

Converts the FlatSat Simulator Plan markdown file to a professional PDF document.
Uses reportlab for PDF generation with proper formatting and styling.
"""

import os
import sys
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas

class FlatSatPlanPDFGenerator:
    """Generate PDF from FlatSat Simulator Plan"""
    
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Heading 1 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        # Heading 2 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen
        ))
        
        # Heading 3 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=8,
            textColor=colors.darkred
        ))
        
        # Bullet style
        self.styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=self.styles['Normal'],
            leftIndent=20,
            spaceAfter=3,
            spaceBefore=3
        ))
        
        # Status style
        self.styles.add(ParagraphStyle(
            name='CustomStatus',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=6,
            textColor=colors.green,
            fontName='Helvetica-Bold'
        ))
    
    def clean_text(self, text):
        """Clean text by removing markdown formatting"""
        # Remove bold markers
        text = text.replace('**', '')
        # Remove code markers
        text = text.replace('`', '')
        # Remove emoji markers
        text = text.replace('🆕', 'NEW: ')
        return text
    
    def parse_markdown_content(self):
        """Parse markdown content and convert to PDF elements"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        elements = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                elements.append(Spacer(1, 6))
                continue
                
            # Title
            if line.startswith('# '):
                clean_line = self.clean_text(line[2:])
                elements.append(Paragraph(clean_line, self.styles['CustomTitle']))
                elements.append(Spacer(1, 20))
            
            # Heading 1
            elif line.startswith('## '):
                clean_line = self.clean_text(line[3:])
                elements.append(Paragraph(clean_line, self.styles['CustomHeading1']))
                elements.append(Spacer(1, 12))
            
            # Heading 2
            elif line.startswith('### '):
                clean_line = self.clean_text(line[4:])
                elements.append(Paragraph(clean_line, self.styles['CustomHeading2']))
                elements.append(Spacer(1, 8))
            
            # Heading 3
            elif line.startswith('#### '):
                clean_line = self.clean_text(line[5:])
                elements.append(Paragraph(clean_line, self.styles['CustomHeading3']))
                elements.append(Spacer(1, 6))
            
            # Code blocks
            elif line.startswith('```'):
                continue  # Skip code block markers
            
            # Bullet points
            elif line.startswith('- '):
                clean_line = self.clean_text(line[2:])
                elements.append(Paragraph(f"• {clean_line}", self.styles['CustomBullet']))
            
            # Checkbox items
            elif line.startswith('- [x]'):
                clean_line = self.clean_text(line[5:].strip())
                elements.append(Paragraph(f"✓ {clean_line}", self.styles['CustomBullet']))
            
            # Status lines
            elif line.startswith('## Status:'):
                clean_line = self.clean_text(line)
                elements.append(Paragraph(clean_line, self.styles['CustomStatus']))
                elements.append(Spacer(1, 12))
            
            # Regular paragraphs
            else:
                if line:
                    clean_line = self.clean_text(line)
                    elements.append(Paragraph(clean_line, self.styles['Normal']))
                    elements.append(Spacer(1, 6))
        
        return elements
    
    def add_header_footer(self, canvas, doc):
        """Add header and footer to each page"""
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(colors.darkblue)
        canvas.drawString(50, A4[1] - 30, "FlatSat Device Simulator - Implementation Plan")
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(50, 30, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas.drawRightString(A4[0] - 50, 30, f"Page {doc.page}")
        
        # Line separator
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(50, A4[1] - 40, A4[0] - 50, A4[1] - 40)
        canvas.line(50, 40, A4[0] - 50, 40)
        
        canvas.restoreState()
    
    def generate_pdf(self):
        """Generate the PDF document"""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                self.output_file,
                pagesize=A4,
                rightMargin=50,
                leftMargin=50,
                topMargin=80,
                bottomMargin=60
            )
            
            # Parse content
            elements = self.parse_markdown_content()
            
            # Add title page
            title_elements = [
                Paragraph("FlatSat Device Simulator", self.styles['CustomTitle']),
                Spacer(1, 20),
                Paragraph("Implementation Plan", self.styles['CustomTitle']),
                Spacer(1, 40),
                Paragraph("Aurora FlatSat v1.0", self.styles['Heading2']),
                Spacer(1, 20),
                Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']),
                Spacer(1, 40),
                Paragraph("Comprehensive application that receives data from MATLAB simulator via TCP/IP and converts it to proper device packet formats for testing satellite systems.", self.styles['Normal']),
                Spacer(1, 20),
                Paragraph("Supports ARS (Angular Rate Sensor), Magnetometer, and Reaction Wheel devices with multiple output interfaces.", self.styles['Normal']),
                Spacer(1, 20),
                Paragraph("NEW: Now includes complete MATLAB orbital mechanics simulator with device format output for realistic space environment testing.", self.styles['Normal']),
                PageBreak()
            ]
            
            # Combine title and content
            all_elements = title_elements + elements
            
            # Build PDF
            doc.build(all_elements, onFirstPage=self.add_header_footer, onLaterPages=self.add_header_footer)
            
            print(f"✅ PDF generated successfully: {self.output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            return False

def main():
    """Main function"""
    # File paths
    input_file = "FLATSAT_SIMULATOR_PLAN.md"
    output_file = "FlatSat_Simulator_Plan.pdf"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    # Generate PDF
    generator = FlatSatPlanPDFGenerator(input_file, output_file)
    success = generator.generate_pdf()
    
    if success:
        print(f"\n📄 PDF Document Information:")
        print(f"   File: {output_file}")
        print(f"   Size: {os.path.getsize(output_file)} bytes")
        print(f"   Location: {os.path.abspath(output_file)}")
        print(f"\n🎉 FlatSat Simulator Plan PDF generated successfully!")
    else:
        print(f"\n❌ Failed to generate PDF")
        sys.exit(1)

if __name__ == "__main__":
    main()

