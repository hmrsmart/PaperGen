"""
Academic Paper Templates and Styling Definitions.
"""

from typing import Dict, Any

TEMPLATES_METADATA: Dict[str, Dict[str, Any]] = {
    "ieee": {
        "id": "ieee",
        "name": "IEEE Conference & Transactions",
        "description": "Standard IEEE two-column format with Roman numeral section numbering, IEEE citation style [1], and formal academic typography.",
        "font_family": "Times New Roman",
        "columns": 2,
        "latex_class": "IEEEtran",
        "latex_class_options": "conference",
        "latex_packages": [
            "cite", "amsmath,amssymb,amsfonts", "algorithmic", "graphicx",
            "textcomp", "xcolor", "booktabs", "multirow", "hyperref"
        ],
        "section_prefix": "ROMAN",  # I, II, III...
        "abstract_label": "Abstract---",
        "keywords_label": "Index Terms---",
        "citation_format": "[{index}]",
    },
    "acm": {
        "id": "acm",
        "name": "ACM SIGCONF / Master Article",
        "description": "Official ACM proceedings format with CCS concepts, ACM reference format, and crisp modern typography.",
        "font_family": "Linux Libertine, Times New Roman",
        "columns": 2,
        "latex_class": "acmart",
        "latex_class_options": "sigconf",
        "latex_packages": [
            "amsmath,amssymb", "booktabs", "graphicx", "hyperref", "microtype"
        ],
        "section_prefix": "ARABIC",  # 1, 2, 3...
        "abstract_label": "ABSTRACT",
        "keywords_label": "CCS CONCEPTS & KEYWORDS",
        "citation_format": "[{index}]",
    },
    "springer": {
        "id": "springer",
        "name": "Springer LNCS (Lecture Notes in Computer Science)",
        "description": "Springer Lecture Notes in Computer Science single-column format widely used in European conferences and Springer journals.",
        "font_family": "Times New Roman",
        "columns": 1,
        "latex_class": "llncs",
        "latex_class_options": "",
        "latex_packages": [
            "amsmath,amssymb", "graphicx", "booktabs", "url", "microtype", "hyperref"
        ],
        "section_prefix": "ARABIC",
        "abstract_label": "Abstract.",
        "keywords_label": "Keywords:",
        "citation_format": "[{index}]",
    },
    "nature": {
        "id": "nature",
        "name": "Nature / Science Journal Format",
        "description": "Prestigious multidisciplinary format featuring an unreferenced introductory executive abstract, clear narrative headings, and numbered references.",
        "font_family": "Helvetica, Arial",
        "columns": 1,
        "latex_class": "article",
        "latex_class_options": "11pt,a4paper",
        "latex_packages": [
            "amsmath,amssymb", "graphicx", "booktabs", "cite", "hyperref", "geometry"
        ],
        "section_prefix": "ARABIC",
        "abstract_label": "Summary",
        "keywords_label": "Subject Categories:",
        "citation_format": "^{{[{index}]}}",
    },
    "apa": {
        "id": "apa",
        "name": "APA 7th Edition (Social Sciences & Psychology)",
        "description": "Standard American Psychological Association 7th Edition format with running header, title page, clear section levels, and hanging references.",
        "font_family": "Times New Roman",
        "columns": 1,
        "latex_class": "article",
        "latex_class_options": "12pt,letterpaper",
        "latex_packages": [
            "amsmath,amssymb", "graphicx", "booktabs", "setspace", "geometry", "hyperref"
        ],
        "section_prefix": "NONE",  # Just section title
        "abstract_label": "Abstract",
        "keywords_label": "Keywords:",
        "citation_format": "[{index}]",
    },
    "neurips": {
        "id": "neurips",
        "name": "NeurIPS / ICML AI Conference",
        "description": "Top-tier AI conference format with clean single-column wide margins, modern typography, line numbering support, and algorithmic styling.",
        "font_family": "Times New Roman",
        "columns": 1,
        "latex_class": "article",
        "latex_class_options": "10pt,letterpaper",
        "latex_packages": [
            "amsmath,amssymb", "graphicx", "booktabs", "microtype", "hyperref", "algorithm2e"
        ],
        "section_prefix": "ARABIC",
        "abstract_label": "Abstract",
        "keywords_label": "Keywords:",
        "citation_format": "[{index}]",
    }
}

def get_template(template_id: str) -> Dict[str, Any]:
    return TEMPLATES_METADATA.get(template_id.lower(), TEMPLATES_METADATA["ieee"])
