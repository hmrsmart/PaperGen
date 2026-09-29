"""
LaTeX & BibTeX Academic Exporter.
Produces compilable LaTeX source code conforming to IEEE, ACM, Springer LNCS, APA, and Nature styles,
paired with a standalone .bib BibTeX file and bundled ZIP distribution.
"""

import os
import re
import zipfile
from typing import Dict, Any, Tuple
from app.models import PaperDocument, Section, TableData, FigureData
from app.generator.templates import get_template

def clean_latex(text: str) -> str:
    """Escape special LaTeX characters while preserving math blocks."""
    # Split by math blocks
    parts = re.split(r'(\$\$.*?\$\$|\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\])', text, flags=re.DOTALL)
    cleaned_parts = []
    for p in parts:
        if p.startswith('$') or p.startswith('\\(') or p.startswith('\\['):
            # Math block - preserve as is, just clean double newlines if needed
            cleaned_parts.append(p)
        else:
            # Text block: escape & % _ # ~ ^
            s = p.replace('&', '\\&').replace('%', '\\%').replace('#', '\\#')
            s = s.replace('_', '\\_')
            cleaned_parts.append(s)
    return "".join(cleaned_parts)

def generate_bibtex(paper: PaperDocument) -> str:
    """Generates complete BibTeX file contents for all paper references."""
    bib_entries = []
    for r in paper.references:
        # Determine entry type
        venue_lower = r.venue.lower()
        if any(kw in venue_lower for kw in ["conference", "proceedings", "symposium", "neurips", "icml", "cvpr", "icra"]):
            entry_type = "inproceedings"
            venue_field = f"  booktitle = {{{r.venue}}},"
        else:
            entry_type = "article"
            venue_field = f"  journal = {{{r.venue}}},"
            
        vol_str = f"  volume = {{{r.volume}}}," if r.volume else ""
        pages_str = f"  pages = {{{r.pages}}}," if r.pages else ""
        doi_str = f"  doi = {{{r.doi}}}," if r.doi else ""
        
        entry = (
            f"@{entry_type}{{{r.key},\n"
            f"  author = {{{r.authors}}},\n"
            f"  title = {{{{{r.title}}}}},\n"
            f"{venue_field}\n"
            f"{vol_str}\n"
            f"{pages_str}\n"
            f"  year = {{{r.year}}},\n"
            f"{doi_str}\n"
            f"}}"
        )
        # Clean empty lines
        lines = [line for line in entry.splitlines() if line.strip()]
        bib_entries.append("\n".join(lines))
        
    return "\n\n".join(bib_entries)

def table_to_latex(table: TableData) -> str:
    """Converts a structured TableData object to a booktabs LaTeX table."""
    num_cols = len(table.headers)
    col_spec = "l" + "c" * (num_cols - 1)
    
    header_row = " & ".join([f"\\textbf{{{clean_latex(h)}}}" for h in table.headers]) + " \\\\"
    
    data_rows = []
    for row in table.rows:
        cleaned_cells = [clean_latex(c).replace("**", "\\textbf{").replace("**", "}") for c in row]
        data_rows.append(" & ".join(cleaned_cells) + " \\\\")
        
    note_latex = f"\n\\multicolumn{{{num_cols}}}{{l}}{{\\footnotesize \\textit{{{clean_latex(table.note)}}}}} \\\\" if table.note else ""
    
    latex_tbl = (
        f"\\begin{{table}}[htbp]\n"
        f"\\centering\n"
        f"\\caption{{{clean_latex(table.caption)}}}\n"
        f"\\label{{{table.id}}}\n"
        f"\\begin{{tabular}}{{{col_spec}}}\n"
        f"\\toprule\n"
        f"{header_row}\n"
        f"\\midrule\n"
        f"\n".join(data_rows) + f"{note_latex}\n"
        f"\\bottomrule\n"
        f"\\end{{tabular}}\n"
        f"\\end{{table}}\n"
    )
    return latex_tbl

def generate_latex_source(paper: PaperDocument) -> str:
    """Synthesizes the complete .tex source document formatted according to template."""
    tmpl = get_template(paper.template)
    tmpl_id = paper.template.lower()
    
    preamble = []
    
    if tmpl_id == "ieee":
        preamble.append("\\documentclass[conference]{IEEEtran}")
        preamble.append("\\IEEEoverridecommandlockouts")
        preamble.append("\\usepackage{cite}")
        preamble.append("\\usepackage{amsmath,amssymb,amsfonts}")
        preamble.append("\\usepackage{algorithmic}")
        preamble.append("\\usepackage{graphicx}")
        preamble.append("\\usepackage{textcomp}")
        preamble.append("\\usepackage{xcolor}")
        preamble.append("\\usepackage{booktabs}")
        preamble.append("\\usepackage{multirow}")
        preamble.append("\\usepackage{hyperref}")
        
    elif tmpl_id == "acm":
        preamble.append("\\documentclass[sigconf]{acmart}")
        preamble.append("\\usepackage{booktabs}")
        preamble.append("\\usepackage{amsmath,amssymb}")
        preamble.append("\\usepackage{graphicx}")
        
    elif tmpl_id == "springer":
        preamble.append("\\documentclass{llncs}")
        preamble.append("\\usepackage{graphicx}")
        preamble.append("\\usepackage{booktabs}")
        preamble.append("\\usepackage{amsmath,amssymb}")
        preamble.append("\\usepackage{hyperref}")
        
    else:  # Generic, APA, Nature, NeurIPS
        preamble.append("\\documentclass[11pt,a4paper]{article}")
        preamble.append("\\usepackage[margin=1in]{geometry}")
        preamble.append("\\usepackage{amsmath,amssymb,amsfonts}")
        preamble.append("\\usepackage{graphicx}")
        preamble.append("\\usepackage{booktabs}")
        preamble.append("\\usepackage{cite}")
        preamble.append("\\usepackage{hyperref}")
        preamble.append("\\usepackage{microtype}")
        preamble.append("\\hypersetup{colorlinks=true, linkcolor=blue, citecolor=blue, urlcolor=blue}")

    # Title & Authors
    body = []
    body.append(f"\\title{{{clean_latex(paper.title)}}}")
    
    if tmpl_id == "ieee":
        authors_blocks = []
        for a in paper.authors:
            affil = a.affiliation.replace(",", "\\\\")
            block = (
                f"\\IEEEauthorblockN{{{a.name}}}\n"
                f"\\IEEEauthorblockA{{{affil}\\\\\n"
                f"Email: \\texttt{{{a.email}}}}}"
            )
            authors_blocks.append(block)
        body.append(f"\\author{{\n" + " \\and \n".join(authors_blocks) + "\n}")
    elif tmpl_id == "acm":
        for a in paper.authors:
            body.append(f"\\author{{{a.name}}}")
            body.append(f"\\affiliation{{\\institution{{{clean_latex(a.affiliation)}}}}}")
            body.append(f"\\email{{{a.email}}}")
    else:
        authors_str = " \\quad ".join([f"\\textbf{{{a.name}}}$^{{{i+1}}}$" for i, a in enumerate(paper.authors)])
        affil_str = "\\\\ ".join([f"$^{{{i+1}}}${clean_latex(a.affiliation)} (\\texttt{{{a.email}}})" for i, a in enumerate(paper.authors)])
        body.append(f"\\author{{{authors_str} \\\\[1ex] \\small {affil_str}}}")
        body.append("\\date{\\today}")

    body.append("\\begin{document}")
    body.append("\\maketitle")
    
    # Abstract & Keywords
    body.append("\\begin{abstract}")
    body.append(clean_latex(paper.abstract))
    body.append("\\end{abstract}")
    
    if tmpl_id == "ieee":
        kw_str = ", ".join(paper.keywords)
        body.append(f"\\begin{{IEEEkeywords}}\n{kw_str}\n\\end{{IEEEkeywords}}")
    elif paper.keywords:
        kw_str = ", ".join(paper.keywords)
        body.append(f"\\textbf{{Keywords:}} {kw_str}\n")

    # Sections
    for sec in paper.sections:
        body.append(f"\n\\section{{{clean_latex(sec.title)}}}")
        body.append(clean_latex(sec.content))
        
        # Subsections
        for sub in sec.subsections:
            body.append(f"\n\\subsection{{{clean_latex(sub.title)}}}")
            body.append(clean_latex(sub.content))
            
        # Tables inside section
        for tbl in sec.tables:
            body.append(table_to_latex(tbl))
            
        # Figures inside section
        for fig in sec.figures:
            fig_filename = os.path.basename(fig.file_path) if fig.file_path else "figure1.png"
            body.append(
                f"\n\\begin{{figure}}[htbp]\n"
                f"\\centering\n"
                f"\\includegraphics[width=0.9\\linewidth]{{{fig_filename}}}\n"
                f"\\caption{{{clean_latex(fig.caption)}}}\n"
                f"\\label{{{fig.id}}}\n"
                f"\\end{{figure}}\n"
            )

    # Bibliography
    body.append("\n\\bibliographystyle{IEEEtran}")
    body.append("\\bibliography{references}")
    body.append("\n\\end{document}")
    
    full_latex = "\n".join(preamble) + "\n\n" + "\n".join(body)
    return full_latex

def export_latex_bundle(paper: PaperDocument, output_dir: str = "outputs") -> Tuple[str, str]:
    """
    Exports .tex file, .bib file, and packages them into a .zip file with figures.
    Returns: (tex_file_path, zip_file_path)
    """
    os.makedirs(output_dir, exist_ok=True)
    tex_path = os.path.join(output_dir, f"{paper.id}_main.tex")
    bib_path = os.path.join(output_dir, f"{paper.id}_references.bib")
    zip_path = os.path.join(output_dir, f"{paper.id}_latex_bundle.zip")
    
    tex_content = generate_latex_source(paper)
    bib_content = generate_bibtex(paper)
    
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)
        
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(bib_content)
        
    # Create ZIP bundle
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(tex_path, arcname="main.tex")
        zipf.write(bib_path, arcname="references.bib")
        
        # Include figures in ZIP
        for fig in paper.figures:
            if fig.file_path and os.path.exists(fig.file_path):
                zipf.write(fig.file_path, arcname=os.path.basename(fig.file_path))
                
    return tex_path, zip_path
