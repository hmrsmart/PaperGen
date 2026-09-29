import os
from app.models import GenerationRequest, ChatRequest
from app.generator.agent import PAPER_AGENT
from app.exporters.docx_exporter import export_paper_to_docx
from app.exporters.pdf_exporter import export_paper_to_pdf
from app.exporters.latex_exporter import export_latex_bundle

def test_full_flow():
    req = GenerationRequest(
        topic='Scalable Quantum-Resistant Cryptographic Routing in Next-Generation 6G Networks',
        domain='Cybersecurity & Networks',
        target_pages=12,
        target_references=36,
        template='ieee',
        include_figures=True
    )

    print("1. Generating academic paper with 12 pages and 36 references...")
    paper = PAPER_AGENT.generate_new_paper(req, output_dir='outputs')
    print(f"   ✓ Paper ID: {paper.id}")
    print(f"   ✓ Title: {paper.title}")
    print(f"   ✓ Sections: {len(paper.sections)}")
    print(f"   ✓ References: {len(paper.references)} (Target: 36)")
    print(f"   ✓ Figures: {len(paper.figures)}")
    print(f"   ✓ Estimated Pages: {paper.stats.get('estimated_pages')} (Target: 12)")
    print(f"   ✓ Word Count: {paper.stats.get('word_count')}")

    assert len(paper.references) == 36, "Reference count must match 36"
    assert len(paper.sections) >= 7, "Must contain all standard academic sections"

    print("\n2. Testing Word (.docx) export...")
    docx_path = export_paper_to_docx(paper, 'outputs')
    assert os.path.exists(docx_path) and os.path.getsize(docx_path) > 10000
    print(f"   ✓ DOCX exported successfully: {docx_path} ({os.path.getsize(docx_path):,} bytes)")

    print("\n3. Testing PDF (.pdf) export...")
    pdf_path = export_paper_to_pdf(paper, 'outputs')
    assert os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 10000
    print(f"   ✓ PDF exported successfully: {pdf_path} ({os.path.getsize(pdf_path):,} bytes)")

    print("\n4. Testing LaTeX (.tex, .bib, .zip) export...")
    tex_path, zip_path = export_latex_bundle(paper, 'outputs')
    assert os.path.exists(tex_path) and os.path.getsize(tex_path) > 5000
    assert os.path.exists(zip_path) and os.path.getsize(zip_path) > 10000
    print(f"   ✓ LaTeX .tex exported: {tex_path} ({os.path.getsize(tex_path):,} bytes)")
    print(f"   ✓ LaTeX .zip bundle exported: {zip_path} ({os.path.getsize(zip_path):,} bytes)")

    print("\n5. Testing Interactive Chat & Proposal System...")
    chat_req = ChatRequest(
        paper_id=paper.id,
        message="Please add formal mathematical proofs and Lyapunov stability bounds to the methodology",
        selected_section_id="sec-3"
    )
    reply, change = PAPER_AGENT.chat_with_agent(chat_req)
    print(f"   ✓ Agent reply received ({len(reply)} chars)")
    print(f"   ✓ Proposed change generated: {change is not None}")

    if change:
        updated_paper = PAPER_AGENT.apply_change_to_paper(paper.id, change)
        print(f"   ✓ Changes successfully merged into paper! Updated word count: {updated_paper.stats.get('word_count')}")

    print("\n6. Testing Humanize Writing Quality Audit...")
    from app.generator.humanize_rules import audit_text_humanization
    sample_text = paper.abstract + "\n" + paper.sections[0].content + "\n" + paper.sections[-1].content
    issues = audit_text_humanization(sample_text)

    # Separate hard failures (AI clichés, structural tells) from soft warnings (burstiness/style)
    SOFT_WARNING_KEYWORDS = ["burstiness", "em-dash", "rule-of-three", "verb usage"]
    hard_failures = [i for i in issues if not any(kw in i.lower() for kw in SOFT_WARNING_KEYWORDS)]
    soft_warnings  = [i for i in issues if any(kw in i.lower() for kw in SOFT_WARNING_KEYWORDS)]

    print(f"   Hard failures (AI tells): {len(hard_failures)}")
    for iss in hard_failures:
        print(f"     ✗ {iss}")
    print(f"   Soft style warnings:       {len(soft_warnings)}")
    for iss in soft_warnings:
        print(f"     ⚠ {iss}")

    assert len(hard_failures) == 0, f"Text contains AI writing tells: {hard_failures}"
    print("   ✓ Paper passed AI-tell quality checks (0 hard failures)!")
    if soft_warnings:
        print("   ℹ  Style tips above are improvement recommendations for real LLM enrichment.")

    print("\n==========================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==========================================")

if __name__ == "__main__":
    test_full_flow()
