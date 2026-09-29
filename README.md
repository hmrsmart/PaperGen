# PaperGen — Academic Research Papers Generator Agent

**PaperGen** is a full-lifecycle, autonomous academic research paper generator agent designed to synthesize publication-grade academic manuscripts with rigorous scientific structure, formal mathematical proofs, algorithmic pseudocode, publication-quality figures, and authentic scholarly citations.

---

## 🌟 Key Features

### 1. Publication-Grade Academic Synthesis
- **Structured Sections**: Title, Authors & Affiliations, Abstract, Index Terms, Introduction (Motivation, Limitations, Hypotheses, Contributions), Related Work (Systematic Taxonomy Table), Theoretical Methodology (Problem Formulation, Equations, Algorithm 1 Pseudocode, Complexity Bounds), Experimental Design (Datasets, Baselines, Hyperparameters), Results & In-Depth Discussion (Comparative Results Table, Ablations, Statistical Significance $p < 0.01$), Threats to Validity, and Strategic Conclusion.
- **Embedded Visuals**: Automatically generates 300 DPI publication-quality figures via Matplotlib (Benchmark Comparison grouped bar chart, Empirical Convergence loss curve with 95% confidence intervals, and Ablation Study horizontal bar chart).

### 2. Multi-Format Academic Exports
- **LaTeX Source & BibTeX (`.tex` + `.bib` or `.zip`)**:
  - Compilable LaTeX source using official templates (`IEEEtran`, `acmart`, `llncs`, standard `article`).
  - Standalone `references.bib` with BibTeX entries matching all in-text `\cite{...}` keys.
  - One-click `.zip` bundle export containing `main.tex`, `references.bib`, and all generated figure images.
- **Word Document (`.docx`)**:
  - Formatted using `python-docx`.
  - Academic styling: Running header with manuscript title, author affiliation blocks, shaded abstract callout, numbered headings, booktabs-style tables, centered equations, embedded high-res figures, and numbered references with hanging indents.
- **Publication PDF (`.pdf`)**:
  - High-resolution PDF generated via ReportLab Platypus.
  - Dynamic `NumberedCanvas` stamping "Page X of Y" and running headers.
  - Native print preview layout for direct browser printing/saving as PDF.

### 3. User-Configurable Parameters
- **Target Pages**: Calibrated from **2 to 24+ pages** (**default: 12 pages**). Calibrates word density (~6,000–7,500 words), subsection depth, tables, and figures.
- **Target References**: Number of citations (**default: 36 references**, configurable from 5 to 80+). Generates authentic scholar metadata, top-tier venues (IEEE TPAMI, NeurIPS, ICML, CVPR, Nature Machine Intelligence), publication years (2018–2025), DOIs, and weaves them systematically into the text `[1]` to `[36]`.
- **Paper Template**:
  - **IEEE**: Conference & Transactions (Two-column layout, Roman numerals, IEEE reference format).
  - **ACM**: SIGCONF / Master Article format.
  - **Springer LNCS**: Lecture Notes in Computer Science format.
  - **Nature / Science**: Multidisciplinary summary lead format.
  - **APA 7th Edition**: Standard academic journal format.
  - **NeurIPS / ICML**: Top-tier AI conference style.

### 4. Interactive Co-Author & Peer Reviewer Chat
- Users can chat directly with the AI Research Paper Agent to refine specific points.
- **Section Focus**: Focus chat globally or drill down into specific sections (e.g. Methodology, Abstract, Discussion).
- **One-Click Quick Actions**:
  - 📐 Add formal mathematical proof & Lyapunov stability bounds
  - 🧐 Act as Reviewer #2 with critical academic critique
  - 📚 Expand citations with recent 2024–2025 literature
  - ✨ Elevate abstract with quantitative gains
- **Interactive Merge**: The agent proposes concrete additions with an interactive **"Apply Changes to Paper"** button that updates the live manuscript and exports in real time.

### 5. Multi-Provider AI Engine
- **Built-in Autonomous Academic Synthesizer**: Fully functional offline without requiring any API keys.
- **Optional LLM Integration**: Connect OpenAI (GPT-4o), Google Gemini (Gemini 1.5 Pro), or local Ollama (Llama 3, Mistral) via the Settings modal.

---

## 🚀 Quick Start Guide

### 1. Installation
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
Run the server:
```bash
python run.py
```
Open your browser at **http://localhost:8000**.

### 3. Generate a Paper
1. Select one of the curated presets or enter your own custom research topic.
2. Select your desired domain (Computer Science, Cybersecurity, Healthcare, etc.).
3. Set your target **Number of Pages** (default: 12) and **Number of References** (default: 36).
4. Select your **Paper Template** (e.g., IEEE).
5. Click **"Generate Academic Paper"**.
6. Switch between **Formatted Paper Preview**, **Section-by-Section Editor**, and **LaTeX Source Code**.
7. Chat with the agent in the right panel to improve specific points and click **"Apply Changes to Paper"**.
8. Export your manuscript to **LaTeX (.zip)**, **Word (.docx)**, or **PDF** with one click from the top toolbar!
