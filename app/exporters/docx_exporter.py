"""
Professional Academic Word Document (.docx) Exporter.
Builds beautifully formatted academic manuscripts with IEEE / APA / Standard styling,
embedded tables, high-resolution figures, equations, and hanging references.
"""

import os
from typing import Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from app.models import PaperDocument, Section, TableData, FigureData

def set_cell_background(cell, fill_hex: str):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def export_paper_to_docx(paper: PaperDocument, output_dir: str = "outputs") -> str:
    """Generates and saves the Word (.docx) manuscript."""
    os.makedirs(output_dir, exist_ok=True)
    doc_path = os.path.join(output_dir, f"{paper.id}_manuscript.docx")
    
    doc = Document()
    
    # Page setup: Standard academic letter size, 1-inch margins
    sections = doc.sections
    for sec in sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)
        
        # Header: Running title
        header = sec.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run(paper.running_title or paper.title[:50])
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.italic = True
        hrun.font.color.rgb = RGBColor(128, 128, 128)
        
        # Footer: Page number hint
        footer = sec.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run(f"{paper.template.upper()} Academic Manuscript • Confidential Draft")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(8)
        frun.font.color.rgb = RGBColor(140, 140, 140)

    # 1. Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(12)
    title_p.paragraph_format.space_after = Pt(10)
    title_run = title_p.add_run(paper.title)
    title_run.font.name = "Times New Roman"
    title_run.font.size = Pt(18)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(20, 30, 45)

    # 2. Authors
    author_p = doc.add_paragraph()
    author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    author_p.paragraph_format.space_after = Pt(4)
    for i, a in enumerate(paper.authors):
        arun = author_p.add_run(a.name)
        arun.font.name = "Times New Roman"
        arun.font.size = Pt(11)
        arun.font.bold = True
        
        # Superscript affiliation index
        sup = author_p.add_run(f" {i+1}")
        sup.font.name = "Times New Roman"
        sup.font.size = Pt(8)
        sup.font.superscript = True
        
        if i < len(paper.authors) - 1:
            sep = author_p.add_run("   •   ")
            sep.font.name = "Times New Roman"
            sep.font.size = Pt(10)
            sep.font.color.rgb = RGBColor(150, 150, 150)

    # Affiliations & Emails
    affil_p = doc.add_paragraph()
    affil_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    affil_p.paragraph_format.space_after = Pt(16)
    for i, a in enumerate(paper.authors):
        af_run = affil_p.add_run(f"({i+1}) {a.affiliation} — {a.email}\n")
        af_run.font.name = "Times New Roman"
        af_run.font.size = Pt(8.5)
        af_run.font.color.rgb = RGBColor(80, 80, 80)

    # 3. Abstract Box
    abstract_table = doc.add_table(rows=1, cols=1)
    abstract_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    abstract_table.autofit = False
    abstract_cell = abstract_table.cell(0, 0)
    abstract_cell.width = Inches(6.5)
    set_cell_background(abstract_cell, "F4F6F9")
    set_cell_margins(abstract_cell, top=160, bottom=160, left=200, right=200)
    
    ab_p = abstract_cell.paragraphs[0]
    ab_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    ab_lbl = ab_p.add_run("Abstract—")
    ab_lbl.font.name = "Times New Roman"
    ab_lbl.font.size = Pt(10)
    ab_lbl.font.bold = True
    
    ab_txt = ab_p.add_run(paper.abstract)
    ab_txt.font.name = "Times New Roman"
    ab_txt.font.size = Pt(9.5)
    
    # Keywords in abstract box
    kw_p = abstract_cell.add_paragraph()
    kw_p.paragraph_format.space_before = Pt(6)
    kw_lbl = kw_p.add_run("Keywords: ")
    kw_lbl.font.name = "Times New Roman"
    kw_lbl.font.size = Pt(9)
    kw_lbl.font.bold = True
    
    kw_txt = kw_p.add_run(", ".join(paper.keywords))
    kw_txt.font.name = "Times New Roman"
    kw_txt.font.size = Pt(9)
    kw_txt.font.italic = True

    # Spacing after abstract
    sp_p = doc.add_paragraph()
    sp_p.paragraph_format.space_before = Pt(12)

    # 4. Sections
    for sec in paper.sections:
        # Section Heading (Heading 1)
        h1 = doc.add_paragraph()
        h1.paragraph_format.space_before = Pt(16)
        h1.paragraph_format.space_after = Pt(6)
        h1.paragraph_format.keep_with_next = True
        h1_run = h1.add_run(sec.title)
        h1_run.font.name = "Times New Roman"
        h1_run.font.size = Pt(13)
        h1_run.font.bold = True
        h1_run.font.color.rgb = RGBColor(16, 44, 87)

        # Section Body Paragraphs
        for para_text in sec.content.split("\n\n"):
            if not para_text.strip():
                continue
            bp = doc.add_paragraph()
            bp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            bp.paragraph_format.line_spacing = 1.15
            bp.paragraph_format.space_after = Pt(6)
            
            # Check for math or regular text
            if "$$" in para_text:
                # Math display equation
                mrun = bp.add_run(para_text.strip())
                mrun.font.name = "Cambria Math"
                mrun.font.size = Pt(10)
                mrun.font.italic = True
                bp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                brun = bp.add_run(para_text.strip())
                brun.font.name = "Times New Roman"
                brun.font.size = Pt(10.5)

        # Subsections
        for sub in sec.subsections:
            h2 = doc.add_paragraph()
            h2.paragraph_format.space_before = Pt(12)
            h2.paragraph_format.space_after = Pt(4)
            h2.paragraph_format.keep_with_next = True
            h2_run = h2.add_run(f"{sub.number} {sub.title}")
            h2_run.font.name = "Times New Roman"
            h2_run.font.size = Pt(11)
            h2_run.font.bold = True
            h2_run.font.color.rgb = RGBColor(30, 60, 100)

            for sub_p_text in sub.content.split("\n\n"):
                if not sub_p_text.strip():
                    continue
                sub_p = doc.add_paragraph()
                sub_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                sub_p.paragraph_format.line_spacing = 1.15
                sub_p.paragraph_format.space_after = Pt(6)
                
                if sub_p_text.strip().startswith("```"):
                    # Code / algorithm block
                    code_clean = sub_p_text.replace("```", "").strip()
                    sub_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    crun = sub_p.add_run(code_clean)
                    crun.font.name = "Consolas"
                    crun.font.size = Pt(8.5)
                    crun.font.color.rgb = RGBColor(40, 40, 40)
                elif "$$" in sub_p_text:
                    mrun = sub_p.add_run(sub_p_text.strip())
                    mrun.font.name = "Cambria Math"
                    mrun.font.size = Pt(10)
                    mrun.font.italic = True
                    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    srun = sub_p.add_run(sub_p_text.strip())
                    srun.font.name = "Times New Roman"
                    srun.font.size = Pt(10)

        # Tables in section
        for tbl in sec.tables:
            # Caption above table
            cap_p = doc.add_paragraph()
            cap_p.paragraph_format.space_before = Pt(12)
            cap_p.paragraph_format.space_after = Pt(4)
            cap_p.paragraph_format.keep_with_next = True
            cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            crun = cap_p.add_run(tbl.caption)
            crun.font.name = "Times New Roman"
            crun.font.size = Pt(9.5)
            crun.font.bold = True

            # Table rows
            w_table = doc.add_table(rows=len(tbl.rows) + 1, cols=len(tbl.headers))
            w_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            w_table.autofit = True
            
            # Header Row
            hdr_cells = w_table.rows[0].cells
            for col_idx, htext in enumerate(tbl.headers):
                cell = hdr_cells[col_idx]
                set_cell_background(cell, "2C3E50")
                set_cell_margins(cell, top=120, bottom=120, left=100, right=100)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                hr = p.add_run(htext)
                hr.font.name = "Times New Roman"
                hr.font.size = Pt(9)
                hr.font.bold = True
                hr.font.color.rgb = RGBColor(255, 255, 255)
                
            # Data Rows
            for r_idx, row in enumerate(tbl.rows):
                row_cells = w_table.rows[r_idx + 1].cells
                bg_color = "F9FAFC" if r_idx % 2 == 1 else "FFFFFF"
                for c_idx, val in enumerate(row):
                    cell = row_cells[c_idx]
                    set_cell_background(cell, bg_color)
                    set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
                    vr = p.add_run(val.replace("**", ""))
                    vr.font.name = "Times New Roman"
                    vr.font.size = Pt(8.5)
                    if "**" in val:
                        vr.font.bold = True
                        vr.font.color.rgb = RGBColor(160, 20, 20)

            # Table Note
            if tbl.note:
                note_p = doc.add_paragraph()
                note_p.paragraph_format.space_before = Pt(2)
                note_p.paragraph_format.space_after = Pt(10)
                nrun = note_p.add_run(tbl.note)
                nrun.font.name = "Times New Roman"
                nrun.font.size = Pt(8)
                nrun.font.italic = True
                nrun.font.color.rgb = RGBColor(100, 100, 100)

        # Figures in section
        for fig in sec.figures:
            if fig.file_path and os.path.exists(fig.file_path):
                fig_p = doc.add_paragraph()
                fig_p.paragraph_format.space_before = Pt(14)
                fig_p.paragraph_format.space_after = Pt(4)
                fig_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                fig_p.paragraph_format.keep_with_next = True
                
                # Insert image scaled to 5.5 inches width
                try:
                    run = fig_p.add_run()
                    run.add_picture(fig.file_path, width=Inches(5.5))
                except Exception as e:
                    print(f"Error adding picture to docx: {e}")

                # Caption
                fcap_p = doc.add_paragraph()
                fcap_p.paragraph_format.space_after = Pt(12)
                fcap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                fc_run = fcap_p.add_run(fig.caption)
                fc_run.font.name = "Times New Roman"
                fc_run.font.size = Pt(9)
                fc_run.font.italic = True
                fc_run.font.color.rgb = RGBColor(50, 50, 50)

    # 5. References Section
    ref_h = doc.add_paragraph()
    ref_h.paragraph_format.space_before = Pt(20)
    ref_h.paragraph_format.space_after = Pt(8)
    ref_h.paragraph_format.keep_with_next = True
    ref_hrun = ref_h.add_run("References")
    ref_hrun.font.name = "Times New Roman"
    ref_hrun.font.size = Pt(13)
    ref_hrun.font.bold = True
    ref_hrun.font.color.rgb = RGBColor(16, 44, 87)

    for ref in paper.references:
        rp = doc.add_paragraph()
        rp.paragraph_format.left_indent = Inches(0.4)
        rp.paragraph_format.first_line_indent = Inches(-0.4)
        rp.paragraph_format.space_after = Pt(4)
        rp.paragraph_format.line_spacing = 1.1
        
        idx_run = rp.add_run(f"[{ref.index}]  ")
        idx_run.font.name = "Times New Roman"
        idx_run.font.size = Pt(9)
        idx_run.font.bold = True
        
        cit_run = rp.add_run(ref.raw_citation)
        cit_run.font.name = "Times New Roman"
        cit_run.font.size = Pt(9)

    doc.save(doc_path)
    return doc_path
