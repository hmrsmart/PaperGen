"""
Professional Academic PDF Exporter using ReportLab.
Renders high-quality PDF manuscripts with Running Headers, "Page X of Y" numbering,
IEEE/APA typography, embedded tables, high-resolution figures, and hanging-indent references.
"""

import os
import re
from typing import List
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from app.models import PaperDocument, Section, TableData, FigureData

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and stamp total page count and running headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.running_title = "Academic Research Manuscript"

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Times-Roman", 8.5)
        self.setFillColor(colors.HexColor("#666666"))
        
        # Don't draw header on first page
        if self._pageNumber > 1:
            # Header
            self.drawRightString(letter[0] - 0.75 * inch, letter[1] - 0.5 * inch, self.running_title)
            self.setStrokeColor(colors.HexColor("#dddddd"))
            self.setLineWidth(0.5)
            self.line(0.75 * inch, letter[1] - 0.55 * inch, letter[0] - 0.75 * inch, letter[1] - 0.55 * inch)
            
        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, footer_text)
        self.drawString(0.75 * inch, 0.45 * inch, "Confidential Academic Draft • Peer Review Manuscript")
        self.setStrokeColor(colors.HexColor("#dddddd"))
        self.setLineWidth(0.5)
        self.line(0.75 * inch, 0.58 * inch, letter[0] - 0.75 * inch, 0.58 * inch)
        
        self.restoreState()

def clean_for_reportlab(text: str) -> str:
    """Escapes special XML characters for ReportLab Paragraphs."""
    # Replace markdown bold **text** with <b>text</b>
    t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Replace *italic* with <i>italic</i>
    t = re.sub(r'(?<!\*)\*(?!\*)(.*?)\*', r'<i>\1</i>', t)
    # Replace & with &amp; if not already part of an entity
    t = re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', t)
    return t

def export_paper_to_pdf(paper: PaperDocument, output_dir: str = "outputs") -> str:
    """Renders the paper document to PDF format using ReportLab."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{paper.id}_manuscript.pdf")
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=18,
        leading=22,
        alignment=1,  # Center
        textColor=colors.HexColor("#112233"),
        spaceAfter=12
    )
    
    author_style = ParagraphStyle(
        'PaperAuthor',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10.5,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#222222"),
        spaceAfter=4
    )
    
    affil_style = ParagraphStyle(
        'PaperAffil',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.5,
        leading=11.5,
        alignment=1,
        textColor=colors.HexColor("#555555"),
        spaceAfter=14
    )
    
    abstract_heading = ParagraphStyle(
        'AbstractHeading',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1a2b4c")
    )
    
    abstract_body = ParagraphStyle(
        'AbstractBody',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=9,
        leading=12.5,
        alignment=4,  # Justified
        textColor=colors.HexColor("#2a2a2a")
    )
    
    h1_style = ParagraphStyle(
        'AcademicH1',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#0d2040"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'AcademicH2',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1a365d"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'AcademicBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.2,
        alignment=4,  # Justified
        spaceAfter=6
    )
    
    math_style = ParagraphStyle(
        'AcademicMath',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=9.5,
        leading=13,
        alignment=1,  # Centered
        textColor=colors.HexColor("#1b325f"),
        spaceBefore=4,
        spaceAfter=6
    )
    
    code_style = ParagraphStyle(
        'AcademicCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#222222"),
        spaceAfter=6
    )
    
    table_caption_style = ParagraphStyle(
        'TableCaption',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=8.5,
        leading=11.5,
        alignment=1,
        textColor=colors.HexColor("#222222"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    table_note_style = ParagraphStyle(
        'TableNote',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#666666"),
        spaceAfter=10
    )
    
    fig_caption_style = ParagraphStyle(
        'FigCaption',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=8.5,
        leading=11.5,
        alignment=1,
        textColor=colors.HexColor("#444444"),
        spaceBefore=4,
        spaceAfter=12
    )
    
    ref_style = ParagraphStyle(
        'ReferenceEntry',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8,
        leading=10.5,
        leftIndent=18,
        firstLineIndent=-18,
        spaceAfter=4
    )
    
    story = []
    
    # 1. Title
    story.append(Paragraph(clean_for_reportlab(paper.title), title_style))
    
    # 2. Authors
    author_line = " &nbsp;&nbsp;•&nbsp;&nbsp; ".join([f"<b>{a.name}</b><sup>{i+1}</sup>" for i, a in enumerate(paper.authors)])
    story.append(Paragraph(author_line, author_style))
    
    affil_line = "<br/>".join([f"<sup>{i+1}</sup>{escape(a.affiliation)} — <i>{escape(a.email)}</i>" for i, a in enumerate(paper.authors)])
    story.append(Paragraph(affil_line, affil_style))
    
    # 3. Abstract Box
    abs_text = f"<b>Abstract—</b> {clean_for_reportlab(paper.abstract)}<br/><br/><b>Index Terms—</b> <i>{', '.join(paper.keywords)}</i>"
    abs_cell = Paragraph(abs_text, abstract_body)
    abs_table = Table([[abs_cell]], colWidths=[7.0 * inch])
    abs_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(abs_table)
    story.append(Spacer(1, 12))
    
    # 4. Sections
    for sec in paper.sections:
        story.append(Paragraph(clean_for_reportlab(sec.title), h1_style))
        
        for para in sec.content.split("\n\n"):
            if not para.strip():
                continue
            if "$$" in para:
                story.append(Paragraph(escape(para.strip()), math_style))
            else:
                story.append(Paragraph(clean_for_reportlab(para.strip()), body_style))
                
        # Subsections
        for sub in sec.subsections:
            story.append(Paragraph(f"{sub.number} {clean_for_reportlab(sub.title)}", h2_style))
            for sub_p in sub.content.split("\n\n"):
                if not sub_p.strip():
                    continue
                if sub_p.strip().startswith("```"):
                    # Code block inside box
                    cleaned_code = escape(sub_p.replace("```", "").strip())
                    code_cell = Paragraph(cleaned_code.replace("\n", "<br/>"), code_style)
                    code_tbl = Table([[code_cell]], colWidths=[7.0 * inch])
                    code_tbl.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
                        ('TOPPADDING', (0,0), (-1,-1), 6),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                        ('LEFTPADDING', (0,0), (-1,-1), 8),
                        ('RIGHTPADDING', (0,0), (-1,-1), 8),
                    ]))
                    story.append(code_tbl)
                    story.append(Spacer(1, 6))
                elif "$$" in sub_p:
                    story.append(Paragraph(escape(sub_p.strip()), math_style))
                else:
                    story.append(Paragraph(clean_for_reportlab(sub_p.strip()), body_style))
                    
        # Tables inside Section
        for tbl in sec.tables:
            story.append(Paragraph(clean_for_reportlab(tbl.caption), table_caption_style))
            
            # Build Table Flowable
            table_matrix = []
            # Header
            header_row = [Paragraph(f"<b>{clean_for_reportlab(h)}</b>", ParagraphStyle('TH', fontName='Times-Bold', fontSize=8, leading=10, textColor=colors.white, alignment=1)) for h in tbl.headers]
            table_matrix.append(header_row)
            
            for row in tbl.rows:
                row_cells = []
                for idx, c in enumerate(row):
                    align = 1 if idx > 0 else 0
                    c_clean = clean_for_reportlab(c)
                    row_cells.append(Paragraph(c_clean, ParagraphStyle('TD', fontName='Times-Roman', fontSize=7.5, leading=9.5, alignment=align)))
                table_matrix.append(row_cells)
                
            num_cols = len(tbl.headers)
            col_width = (7.0 * inch) / num_cols
            t_flowable = Table(table_matrix, colWidths=[col_width] * num_cols)
            t_flowable.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            story.append(t_flowable)
            if tbl.note:
                story.append(Paragraph(clean_for_reportlab(tbl.note), table_note_style))
            else:
                story.append(Spacer(1, 6))
                
        # Figures inside Section
        for fig in sec.figures:
            if fig.file_path and os.path.exists(fig.file_path):
                try:
                    img = RLImage(fig.file_path, width=6.2 * inch, height=3.2 * inch)
                    img.hAlign = 'CENTER'
                    story.append(img)
                    story.append(Paragraph(clean_for_reportlab(fig.caption), fig_caption_style))
                except Exception as e:
                    print(f"Error adding image to PDF: {e}")
                    
    # 5. References Section
    story.append(Paragraph("References", h1_style))
    for ref in paper.references:
        ref_text = f"<b>[{ref.index}]</b> &nbsp; {clean_for_reportlab(ref.raw_citation)}"
        story.append(Paragraph(ref_text, ref_style))
        
    # Build Document with NumberedCanvas
    def canvas_maker(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.running_title = paper.running_title or paper.title[:55]
        return c
        
    doc.build(story, canvasmaker=canvas_maker)
    return pdf_path
