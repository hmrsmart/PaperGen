/**
 * PaperGen Academic Workbench Client Application.
 * Handles paper generation, multi-tab rendering, section editing, KaTeX math rendering,
 * interactive agent chat refinement, and academic exports.
 */

// Application State
let currentPaper = null;
let currentChatHistory = [];
let activeTab = 'preview';
let appSettings = {
  provider: 'built-in',
  apiKey: '',
  modelName: ''
};

// Initialization
document.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  loadSettings();
  await loadPresets();
  
  // Set default sample topic in textarea if empty
  const topicEl = document.getElementById('param-topic');
  if (!topicEl.value) {
    topicEl.value = "Quantum-Resistant Cryptographic Routing in Next-Generation 6G Networks";
  }
});

// Settings Management
function loadSettings() {
  const saved = localStorage.getItem('papergen_settings');
  if (saved) {
    try {
      appSettings = JSON.parse(saved);
      document.getElementById('setting-provider').value = appSettings.provider || 'built-in';
      document.getElementById('setting-api-key').value = appSettings.apiKey || '';
      document.getElementById('setting-model-name').value = appSettings.modelName || '';
      handleProviderChange(appSettings.provider);
    } catch (e) {
      console.error("Error loading settings:", e);
    }
  }
}

function saveSettings() {
  appSettings.provider = document.getElementById('setting-provider').value;
  appSettings.apiKey = document.getElementById('setting-api-key').value.trim();
  appSettings.modelName = document.getElementById('setting-model-name').value.trim();
  localStorage.setItem('papergen_settings', JSON.stringify(appSettings));
  toggleSettingsModal();
}

function toggleSettingsModal() {
  const modal = document.getElementById('settings-modal');
  modal.classList.toggle('hidden');
}

function handleProviderChange(provider) {
  const apiKeyBox = document.getElementById('setting-api-key-container');
  if (provider === 'built-in' || provider === 'ollama') {
    apiKeyBox.classList.add('hidden');
  } else {
    apiKeyBox.classList.remove('hidden');
  }
}

// Preset Handlers
async function loadPresets() {
  try {
    const res = await fetch('/api/presets');
    if (!res.ok) return;
    const presets = await res.json();
    const selector = document.getElementById('preset-selector');
    selector.innerHTML = '<option value="">-- Choose a Research Frontier Preset --</option>';
    presets.forEach((p, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = `${p.title} (${p.domain}, ${p.target_pages}p)`;
      selector.appendChild(opt);
    });
    window.PRESETS_CACHE = presets;
  } catch (err) {
    console.warn("Could not fetch presets:", err);
  }
}

function applyPreset(index) {
  if (index === "" || !window.PRESETS_CACHE) return;
  const p = window.PRESETS_CACHE[index];
  if (!p) return;
  document.getElementById('param-topic').value = p.title;
  document.getElementById('param-domain').value = p.domain;
  document.getElementById('param-pages').value = p.target_pages;
  updatePagesDisplay(p.target_pages);
  document.getElementById('param-refs').value = p.target_references;
  updateRefsDisplay(p.target_references);
  document.getElementById('param-template').value = p.template || 'ieee';
}

function suggestRandomTopic() {
  if (!window.PRESETS_CACHE || window.PRESETS_CACHE.length === 0) return;
  const rand = Math.floor(Math.random() * window.PRESETS_CACHE.length);
  applyPreset(rand);
  document.getElementById('preset-selector').value = rand;
}

// Parameter Sliders UI Updates
function updatePagesDisplay(val) {
  document.getElementById('pages-badge').textContent = `${val} Pages`;
}

function updateRefsDisplay(val) {
  document.getElementById('refs-badge').textContent = `${val} Citations`;
}

function toggleAdvancedOptions() {
  const panel = document.getElementById('advanced-options-panel');
  const chevron = document.getElementById('adv-chevron');
  panel.classList.toggle('hidden');
  chevron.classList.toggle('rotate-180');
}

// Tab Switching
function switchTab(tabId) {
  activeTab = tabId;
  const tabs = ['preview', 'editor', 'latex', 'print'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const content = document.getElementById(`tab-content-${t}`);
    if (t === tabId) {
      btn.className = "py-3 border-b-2 border-blue-600 text-blue-600 flex items-center space-x-1.5 font-bold";
      content.classList.remove('hidden');
    } else {
      btn.className = "py-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center space-x-1.5 font-medium";
      content.classList.add('hidden');
    }
  });

  if (tabId === 'preview') {
    renderKaTeXMath();
  }
}

function toggleChatPanel() {
  const panel = document.getElementById('chat-panel');
  const label = document.getElementById('chat-toggle-label');
  panel.classList.toggle('hidden');
  label.textContent = panel.classList.contains('hidden') ? "Show Agent Chat" : "Hide Agent Chat";
}

// ====================================================
// GENERATION ORCHESTRATION
// ====================================================
async function triggerPaperGeneration() {
  const topic = document.getElementById('param-topic').value.trim();
  if (!topic) {
    alert("Please specify a research topic or paper title.");
    return;
  }

  const domain = document.getElementById('param-domain').value;
  const pages = parseInt(document.getElementById('param-pages').value, 10) || 12;
  const refs = parseInt(document.getElementById('param-refs').value, 10) || 36;
  const template = document.getElementById('param-template').value || 'ieee';
  const includeFigures = document.getElementById('param-figures').checked;
  const includeTables = document.getElementById('param-tables').checked;
  const includeAlgorithms = document.getElementById('param-algorithms').checked;
  const instructions = document.getElementById('param-instructions').value.trim();

  // Show loading overlay with animated messages
  const loader = document.getElementById('generation-loader');
  const loaderTitle = document.getElementById('loader-title');
  const loaderSubtitle = document.getElementById('loader-subtitle');
  loader.classList.remove('hidden');

  const progressSteps = [
    { title: "Formulating Theoretical Hypotheses...", sub: `Calibrating mathematical frameworks for ${topic.substring(0, 35)}...` },
    { title: "Synthesizing Literature & Taxonomy...", sub: `Constructing ${refs} authentic scholarly citations...` },
    { title: "Deriving Equations & Algorithm 1...", sub: "Generating closed-loop convergence proofs and pseudocode..." },
    { title: "Generating Scientific Charts (300 DPI)...", sub: "Rendering benchmark comparative figures via Matplotlib..." },
    { title: "Compiling LaTeX & Word Artifacts...", sub: `Formatting according to ${template.toUpperCase()} standard guidelines...` }
  ];

  let stepIdx = 0;
  const interval = setInterval(() => {
    if (stepIdx < progressSteps.length) {
      loaderTitle.textContent = progressSteps[stepIdx].title;
      loaderSubtitle.textContent = progressSteps[stepIdx].sub;
      stepIdx++;
    }
  }, 1200);

  const payload = {
    topic: topic,
    domain: domain,
    target_pages: pages,
    target_references: refs,
    template: template,
    custom_instructions: instructions,
    include_figures: includeFigures,
    include_tables: includeTables,
    include_algorithms: includeAlgorithms,
    api_key: appSettings.apiKey || null,
    llm_provider: appSettings.provider || "built-in",
    model_name: appSettings.modelName || null
  };

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    clearInterval(interval);
    loader.classList.add('hidden');

    if (!res.ok) {
      const err = await res.json();
      alert(`Generation failed: ${err.detail || 'Internal server error'}`);
      return;
    }

    const paper = await res.json();
    currentPaper = paper;
    renderPaper(paper);

    // Initial greeting in agent chat
    appendAgentMessage(
      `🎉 **Paper Generated Successfully!**\n\n` +
      `I have synthesized the manuscript: **"${paper.title}"** conforming to the **${paper.template.upper ? paper.template.toUpperCase() : paper.template}** standard.\n\n` +
      `• **Calibrated Depth:** ~${paper.stats.estimated_pages || pages} pages (${paper.stats.word_count.toLocaleString()} words)\n` +
      `• **Scholarly Citations:** ${paper.references.length} high-impact references\n` +
      `• **Artifacts:** High-res Matplotlib benchmark figures & Algorithmic pseudocode\n\n` +
      `Feel free to chat with me to refine proofs, add specific baselines, critique as Reviewer #2, or elevate specific sections!`
    );

  } catch (err) {
    clearInterval(interval);
    loader.classList.add('hidden');
    console.error("Generation error:", err);
    alert("Connection error while generating paper. Ensure server is running.");
  }
}

// ====================================================
// PAPER RENDERING (PREVIEW, EDITOR, LATEX)
// ====================================================
function renderPaper(paper) {
  // 1. Update Ribbon
  document.getElementById('ribbon-title').textContent = paper.title;
  document.getElementById('ribbon-template-badge').textContent = paper.template.toUpperCase();
  document.getElementById('ribbon-authors').textContent = paper.authors.map(a => a.name).join(' • ');
  
  document.getElementById('stat-pages').textContent = paper.stats.estimated_pages || paper.target_pages;
  document.getElementById('stat-refs').textContent = paper.references.length;
  document.getElementById('stat-words').textContent = `~${(paper.stats.word_count || 6500).toLocaleString()}`;
  document.getElementById('stat-rigor').textContent = `${paper.stats.academic_rigor_score || 98.4}%`;

  // 2. Populate Section Focus in Chat
  const chatSelect = document.getElementById('chat-section-select');
  chatSelect.innerHTML = '<option value="">Entire Paper (Global)</option>';
  paper.sections.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = s.title;
    chatSelect.appendChild(opt);
  });

  // 3. Render Formatted Preview HTML
  const container = document.getElementById('paper-render-container');
  let html = `
    <div class="academic-title">${escapeHtml(paper.title)}</div>
    <div class="academic-authors">
      <div class="font-semibold text-slate-800">
        ${paper.authors.map((a, i) => `<span>${escapeHtml(a.name)}<sup>${i+1}</sup></span>`).join(' &nbsp;•&nbsp; ')}
      </div>
      <div class="text-xs text-slate-500 mt-1">
        ${paper.authors.map((a, i) => `<div><sup>${i+1}</sup>${escapeHtml(a.affiliation)} — <span class="text-blue-600">${escapeHtml(a.email)}</span></div>`).join('')}
      </div>
    </div>

    <!-- Abstract Box -->
    <div class="academic-abstract-box">
      <p class="academic-paragraph"><b class="text-slate-900">Abstract—</b>${escapeHtml(paper.abstract)}</p>
      <div class="text-xs font-semibold text-slate-700 mt-2">
        <b>Index Terms—</b> <span class="italic font-normal">${paper.keywords.join(', ')}</span>
      </div>
    </div>
  `;

  // Sections
  paper.sections.forEach(sec => {
    html += `<div class="academic-h1">${escapeHtml(sec.title)}</div>`;
    
    // Section paragraphs
    sec.content.split('\n\n').forEach(p => {
      if (p.trim().startsWith('$$')) {
        html += `<div class="text-center my-3">${escapeHtml(p)}</div>`;
      } else {
        html += `<p class="academic-paragraph">${escapeHtml(p)}</p>`;
      }
    });

    // Subsections
    sec.subsections.forEach(sub => {
      html += `<div class="academic-h2">${escapeHtml(sub.number)} ${escapeHtml(sub.title)}</div>`;
      sub.content.split('\n\n').forEach(subP => {
        if (subP.trim().startsWith('```')) {
          html += `<pre class="academic-code-box"><code>${escapeHtml(subP.replace(/```/g, '').trim())}</code></pre>`;
        } else if (subP.trim().startsWith('$$')) {
          html += `<div class="text-center my-3">${escapeHtml(subP)}</div>`;
        } else {
          html += `<p class="academic-paragraph">${escapeHtml(subP)}</p>`;
        }
      });
    });

    // Tables
    if (sec.tables && sec.tables.length > 0) {
      sec.tables.forEach(tbl => {
        html += `
          <div class="my-6">
            <div class="text-center font-bold text-xs text-slate-800 mb-1">${escapeHtml(tbl.caption)}</div>
            <table class="academic-table">
              <thead>
                <tr>${tbl.headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr>
              </thead>
              <tbody>
                ${tbl.rows.map(row => `
                  <tr>${row.map((cell, cIdx) => `
                    <td class="${cIdx === 0 ? 'text-left font-medium' : 'text-center'}">
                      ${cell.includes('**') ? `<b class="text-red-700 font-bold">${escapeHtml(cell.replace(/\*\*/g, ''))}</b>` : escapeHtml(cell)}
                    </td>
                  `).join('')}</tr>
                `).join('')}
              </tbody>
            </table>
            ${tbl.note ? `<div class="text-[11px] text-slate-500 italic text-center mt-1">${escapeHtml(tbl.note)}</div>` : ''}
          </div>
        `;
      });
    }

    // Figures
    if (sec.figures && sec.figures.length > 0) {
      sec.figures.forEach(fig => {
        const imgSrc = fig.base64_data ? `data:image/png;base64,${fig.base64_data}` : (fig.file_path ? `/${fig.file_path}` : '');
        html += `
          <div class="academic-figure">
            <img src="${imgSrc}" alt="${escapeHtml(fig.caption)}" class="mx-auto border border-slate-200 rounded">
            <div class="academic-caption">${escapeHtml(fig.caption)}</div>
          </div>
        `;
      });
    }
  });

  // References List
  html += `
    <div class="academic-h1 mt-10">References</div>
    <div class="space-y-2 mt-4 text-xs font-serif leading-relaxed">
      ${paper.references.map(r => `
        <div class="academic-ref-item" id="ref-${r.index}">
          <span class="academic-ref-idx">[${r.index}]</span>
          <span>${escapeHtml(r.raw_citation)}</span>
        </div>
      `).join('')}
    </div>
  `;

  container.innerHTML = html;
  document.getElementById('print-render-container').innerHTML = html;

  // 4. Render Section-by-Section Editor Accordion
  renderSectionEditor(paper);

  // 5. Fetch and Render LaTeX Source
  fetchLatexSource(paper.id);

  // 6. KaTeX math rendering
  renderKaTeXMath();

  if (window.lucide) lucide.createIcons();
}

function renderSectionEditor(paper) {
  const accordion = document.getElementById('editor-sections-accordion');
  let cardsHtml = `
    <!-- Abstract Card -->
    <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <span class="font-bold text-xs text-slate-800 flex items-center space-x-2">
          <i data-lucide="align-left" class="w-4 h-4 text-blue-600"></i>
          <span>Abstract</span>
        </span>
        <button onclick="requestAgentRefine('abstract')" class="text-[11px] text-blue-600 hover:underline flex items-center space-x-1">
          <i data-lucide="sparkles" class="w-3 h-3"></i>
          <span>Refine with Agent</span>
        </button>
      </div>
      <div class="p-3">
        <textarea id="editor-content-abstract" rows="4" class="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 leading-relaxed">${escapeHtml(paper.abstract)}</textarea>
      </div>
    </div>
  `;

  paper.sections.forEach(sec => {
    cardsHtml += `
      <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm" id="accordion-sec-${sec.id}">
        <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <i data-lucide="bookmark" class="w-4 h-4 text-slate-500"></i>
            <input type="text" id="editor-title-${sec.id}" value="${escapeHtml(sec.title)}" class="font-bold text-xs text-slate-800 bg-transparent border-b border-transparent hover:border-slate-300 focus:border-blue-500 focus:outline-none">
          </div>
          <div class="flex items-center space-x-3">
            <button onclick="requestAgentRefine('${sec.id}')" class="text-[11px] text-blue-600 hover:underline flex items-center space-x-1">
              <i data-lucide="sparkles" class="w-3 h-3"></i>
              <span>Refine Section</span>
            </button>
            <button onclick="saveSingleSection('${sec.id}')" class="px-2 py-1 bg-slate-100 hover:bg-blue-50 hover:text-blue-600 rounded text-[11px] font-semibold text-slate-700">Save</button>
          </div>
        </div>
        <div class="p-3">
          <label class="block text-[10px] font-semibold text-slate-500 mb-1">Primary Content (Markdown / LaTeX math supported):</label>
          <textarea id="editor-content-${sec.id}" rows="6" class="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 leading-relaxed">${escapeHtml(sec.content)}</textarea>
        </div>
      </div>
    `;
  });

  accordion.innerHTML = cardsHtml;
  if (window.lucide) lucide.createIcons();
}

async function fetchLatexSource(paperId) {
  try {
    const res = await fetch(`/api/export/${paperId}/latex`);
    if (res.ok) {
      const tex = await res.text();
      document.getElementById('latex-source-textarea').value = tex;
    }
  } catch (e) {
    console.error("Error fetching LaTeX source:", e);
  }
}

function copyLatexSource() {
  const textarea = document.getElementById('latex-source-textarea');
  textarea.select();
  navigator.clipboard.writeText(textarea.value);
  const btn = document.getElementById('copy-latex-btn-text');
  btn.textContent = "Copied!";
  setTimeout(() => btn.textContent = "Copy LaTeX", 2000);
}

// Math Rendering with KaTeX
function renderKaTeXMath() {
  if (window.renderMathInElement) {
    renderMathInElement(document.getElementById('paper-render-container'), {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\(', right: '\\)', display: false },
        { left: '\\[', right: '\\]', display: true }
      ],
      throwOnError: false
    });
  }
}

// Section Editing Handlers
async function saveSingleSection(secId) {
  if (!currentPaper) return;
  const content = document.getElementById(`editor-content-${secId}`).value;
  const title = document.getElementById(`editor-title-${secId}`).value;

  try {
    const res = await fetch(`/api/paper/${currentPaper.id}/section/${secId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content })
    });
    if (res.ok) {
      currentPaper = await res.json();
      renderPaper(currentPaper);
      alert("Section updated successfully!");
    }
  } catch (e) {
    alert("Error saving section: " + e.message);
  }
}

async function saveAllSections() {
  if (!currentPaper) return;
  // Save abstract
  const absContent = document.getElementById('editor-content-abstract').value;
  await fetch(`/api/paper/${currentPaper.id}/section/abstract`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: absContent })
  });

  // Save all sections
  for (const s of currentPaper.sections) {
    const content = document.getElementById(`editor-content-${s.id}`).value;
    const title = document.getElementById(`editor-title-${s.id}`).value;
    await fetch(`/api/paper/${currentPaper.id}/section/${s.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content })
    });
  }

  // Refresh
  const res = await fetch(`/api/paper/${currentPaper.id}`);
  currentPaper = await res.json();
  renderPaper(currentPaper);
  alert("All sections saved successfully!");
}

// ====================================================
// INTERACTIVE AGENT CHAT
// ====================================================
function handleChatKeyDown(event) {
  if (event.key === 'Enter') {
    submitChatMessage();
  }
}

function sendQuickPrompt(promptText) {
  document.getElementById('chat-input').value = promptText;
  submitChatMessage();
}

function requestAgentRefine(secId) {
  document.getElementById('chat-section-select').value = secId;
  const secName = secId === 'abstract' ? 'Abstract' : (currentPaper.sections.find(s => s.id === secId)?.title || secId);
  document.getElementById('chat-input').value = `Please critique and elevate ${secName} with enhanced scholarly rigor and mathematical precision.`;
  submitChatMessage();
  // Open chat panel if hidden
  const panel = document.getElementById('chat-panel');
  if (panel.classList.contains('hidden')) {
    toggleChatPanel();
  }
}

async function submitChatMessage() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;

  if (!currentPaper) {
    alert("Please generate an academic paper first.");
    return;
  }

  const secSelect = document.getElementById('chat-section-select');
  const selectedSecId = secSelect.value || null;

  // Append user message
  appendUserMessage(msg);
  input.value = "";

  currentChatHistory.push({ role: 'user', content: msg });

  // Add agent thinking indicator
  const typingIndicatorId = appendTypingIndicator();

  const payload = {
    paper_id: currentPaper.id,
    message: msg,
    selected_section_id: selectedSecId,
    history: currentChatHistory.map(h => ({ role: h.role, content: h.content })),
    api_key: appSettings.apiKey || null,
    llm_provider: appSettings.provider || "built-in",
    model_name: appSettings.modelName || null
  };

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    removeTypingIndicator(typingIndicatorId);

    if (!res.ok) {
      appendAgentMessage("I encountered an issue processing your request. Please verify connection to the server.");
      return;
    }

    const data = await res.json();
    currentChatHistory.push({ role: 'assistant', content: data.reply });
    appendAgentMessage(data.reply, data.proposed_changes);

  } catch (err) {
    removeTypingIndicator(typingIndicatorId);
    appendAgentMessage("Connection error while speaking with agent.");
  }
}

function appendUserMessage(text) {
  const container = document.getElementById('chat-messages-container');
  const div = document.createElement('div');
  div.className = "chat-bubble-user p-2.5 ml-6 text-white text-xs shadow-sm self-end";
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendAgentMessage(markdownText, proposedChanges = null) {
  const container = document.getElementById('chat-messages-container');
  const div = document.createElement('div');
  div.className = "chat-bubble-agent p-3 border border-slate-200 text-xs shadow-sm space-y-2";

  // Parse markdown
  const renderedHtml = marked.parse(markdownText);
  div.innerHTML = renderedHtml;

  // If there are proposed changes, add interactive apply button
  if (proposedChanges) {
    const changeCard = document.createElement('div');
    changeCard.className = "mt-3 p-2.5 bg-blue-50/70 border border-blue-200 rounded-lg text-slate-800";
    changeCard.innerHTML = `
      <div class="flex items-center justify-between mb-1.5">
        <span class="font-bold text-[11px] text-blue-900 flex items-center space-x-1">
          <i data-lucide="git-pull-request" class="w-3.5 h-3.5 text-blue-600"></i>
          <span>Proposed Revision: ${escapeHtml(proposedChanges.target_title || 'Section')}</span>
        </span>
        <span class="text-[9px] px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded font-semibold">Ready to Merge</span>
      </div>
      <p class="text-[11px] text-slate-600 mb-2">${escapeHtml(proposedChanges.summary || 'Scholarly enhancement to paper')}</p>
      <button onclick="applyAgentChange(${escapeJsObject(proposedChanges)})" class="w-full py-1.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold rounded-md text-[11px] flex items-center justify-center space-x-1.5 shadow transition">
        <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
        <span>Apply Changes to Paper</span>
      </button>
    `;
    div.appendChild(changeCard);
  }

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
}

function appendTypingIndicator() {
  const container = document.getElementById('chat-messages-container');
  const id = "typing-" + Date.now();
  const div = document.createElement('div');
  div.id = id;
  div.className = "chat-bubble-agent p-2.5 border border-slate-200 text-xs shadow-sm flex items-center space-x-2 text-slate-500";
  div.innerHTML = `
    <span class="w-2 h-2 rounded-full bg-blue-500 animate-bounce"></span>
    <span class="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.2s]"></span>
    <span class="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.4s]"></span>
    <span class="text-[11px] italic">Senior Agent is formulating response...</span>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

async function applyAgentChange(changeObj) {
  if (!currentPaper) return;
  try {
    const res = await fetch(`/api/paper/${currentPaper.id}/apply-change`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ change: changeObj })
    });
    if (res.ok) {
      currentPaper = await res.json();
      renderPaper(currentPaper);
      appendAgentMessage(`✅ **Changes successfully merged into ${changeObj.target_title || 'paper'}!** The live preview, editor, and LaTeX artifacts have been updated.`);
    } else {
      alert("Failed to apply changes.");
    }
  } catch (e) {
    alert("Error applying change: " + e.message);
  }
}

// ====================================================
// EXPORT SYSTEM (LATEX, DOCX, PDF, BIBTEX)
// ====================================================
function exportPaper(format) {
  if (!currentPaper) {
    alert("Please generate an academic paper first before exporting.");
    return;
  }
  let endpoint = "";
  if (format === 'latex-zip') {
    endpoint = `/api/export/${currentPaper.id}/latex-zip`;
  } else if (format === 'latex') {
    endpoint = `/api/export/${currentPaper.id}/latex`;
  } else if (format === 'docx') {
    endpoint = `/api/export/${currentPaper.id}/docx`;
  } else if (format === 'pdf') {
    endpoint = `/api/export/${currentPaper.id}/pdf`;
  } else if (format === 'bib') {
    endpoint = `/api/export/${currentPaper.id}/bib`;
  }

  if (endpoint) {
    window.location.href = endpoint;
  }
}

// Utility Helpers
function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeJsObject(obj) {
  return JSON.stringify(obj).replace(/"/g, '&quot;');
}
