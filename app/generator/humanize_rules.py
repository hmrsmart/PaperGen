"""
Humanize Writing Rules & Quality Filter for Academic Papers.

Synthesized from:
- Uploaded skill file: humanize-writing.md (Wikipedia "Signs of AI writing" guide)
- Web research on GPTZero / Turnitin detection mechanics (perplexity + burstiness)
- NLP stylometry research (arXiv 2024-2026): lexical diversity, POS bigrams, psycholinguistic markers
- AI vocabulary tells databases compiled from multiple detection-avoidance guides

Enforces authentic human-scholar voice by:
1. Eliminating AI stock phrases (clichés, buzzwords, generic superlatives)
2. Eliminating structural tells (rule-of-three, negative parallelisms, inflated significance)
3. Eliminating over-transitioning and robotic connectors
4. Eliminating vague hedge-attributions ("studies have shown", "many experts believe")
5. Eliminating overused formal verbs ("utilize", "facilitate", "leverage", "elucidate")
6. Eliminating em-dash overuse (an increasingly flagged AI tell)
7. Injecting burstiness: algorithmic sentence-length variation
8. Enforcing specificity: replacing generalities with grounded concrete detail guidance
"""

import re
import random
from typing import List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# 1. BANNED AI-WRITING CLICHÉS  (pattern → replacement)
# Expanded from skill file + all web research findings
# ─────────────────────────────────────────────────────────────────────────────
AI_CLICHE_PATTERNS: List[Tuple[str, str]] = [
    # Original skill file vocabulary
    (r'\bdelve(?:s|d)? into\b',                  'examine'),
    (r'\bat its core\b',                          'fundamentally'),
    (r'\bin the realm of\b',                      'in'),
    (r'\bit(?:\'s| is) important to (?:note|understand) that\b', ''),
    (r'\bcrucial role in shaping\b',              'direct impact on'),
    (r'\btoday(?:\'s)? (?:fast-paced|digital|modern) (?:world|age|landscape)\b',
                                                  'contemporary settings'),
    (r'\bsheds light on\b',                       'reveals'),
    (r'\bplays a (?:pivotal|crucial|vital|central) role\b', 'is central to'),
    (r'\bstands as a testament to\b',             'demonstrates'),
    (r'\bboasts\b',                               'achieves'),
    (r'\ba treasure trove of\b',                  'an extensive collection of'),
    (r'\brich tapestry\b',                        'complex structure'),
    (r'\bgame-changing\b',                        'substantial'),
    (r'\bseamless(?:ly)?\b',                      'directly'),
    (r'\brapid proliferation of\b',               'growth in'),
    (r'\bremarkable advances?\b',                 'recent progress'),
    (r'\bcaptivating\b',                          'notable'),
    (r'\bmultifaceted\b',                         'varied'),

    # From web research: overused adjectives & buzzwords
    (r'\bpivotal (?:moment|milestone|shift|role)\b', 'significant change'),
    (r'\bgroundbreaking\b',                       'new'),
    (r'\bcutting-edge\b',                         'advanced'),
    (r'\binnovative\b',                           'new'),
    (r'\btransformative\b',                       'significant'),
    (r'\bcomprehensive\b',                        'complete'),
    (r'\brobust\b',                               'strong'),
    (r'\ba myriad of\b',                          'many'),
    (r'\bmyriad\b',                               'many'),
    (r'\blandscape\b(?! architecture)',           'field'),
    (r'\becosystem\b(?! biology| service)',       'environment'),
    (r'\bframework\b(?! of the study)',           'approach'),
    (r'\bunderscore(?:s|d)?\b',                   'show'),
    (r'\bemphasize(?:s|d)? the importance of\b', 'shows why'),
    (r'\bhighlight(?:s|d)? the need for\b',       'indicates that'),
    (r'\brepresent(?:s|ed)? a significant (?:shift|advance|step)\b', 'changed'),

    # Overused formal verbs (web research)
    (r'\butilize(?:s|d)?\b',                      'use'),
    (r'\butilization\b',                          'use'),
    (r'\bfacilitate(?:s|d)?\b',                   'help'),
    (r'\bleverage(?:s|d)?\b(?! ratio)',            'use'),
    (r'\belucidate(?:s|d)?\b',                    'explain'),
    (r'\bcommence(?:s|d)?\b',                     'begin'),
    (r'\bendeavor(?:s|ed)?\b',                    'try'),
    (r'\bascertain(?:s|ed)?\b',                   'determine'),
    (r'\bdemonstrate(?:s|d)? the (?:potential|promise) of\b', 'show that'),
    (r'\bserves? as\b',                           'acts as'),
    (r'\brepresent(?:s)? a\b(?= key| major| significant| crucial)', 'is a'),

    # Vague hedge-attributions (skill file + web research)
    (r'\bsome critics? (?:argue|suggest|claim)\b', 'critics argue'),
    (r'\bmany experts? (?:believe|suggest|argue)\b', 'researchers argue'),
    (r'\bstudies have shown\b',                   'prior work shows'),
    (r'\bit (?:is|has been) widely (?:known|accepted|recognized) that\b', ''),
    (r'\bit is worth (?:noting|mentioning) that\b', ''),
    (r'\bit should be noted that\b',              ''),
    (r'\bfor all intents and purposes\b',         'practically'),
    (r'\bin light of (?:this|these findings)\b',  'given this'),
    (r'\bthat being said\b',                      'still'),
    (r'\bit goes without saying\b',               ''),

    # Inflated-significance framing (skill file)
    (r'\bmarked a pivotal moment\b',              'was a turning point'),
    (r'\bpart of a broader movement\b',           'connected to wider trends'),
    (r'\bsolidified its role\b',                  'established its position'),
    (r'\bhighlights? the enduring legacy\b',      'shows the lasting impact'),
    (r'\brepresented a significant shift\b',       'changed'),

    # Generic superlatives (skill file)
    (r'\bdiverse and fascinating\b',              'varied'),
    (r'\bmajestic\b',                             'notable'),
    (r'\bsparkling\b',                            'clear'),

    # Em-dash overuse guard: consecutive em-dashes in one sentence
    # (handled separately in clean_em_dashes())
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. FORMULAIC TRANSITION OPENERS  (to be stripped from paragraph starts)
# ─────────────────────────────────────────────────────────────────────────────
OVER_TRANSITIONS: List[str] = [
    r'^\s*Furthermore,\s*',
    r'^\s*Moreover,\s*',
    r'^\s*Additionally,\s*',
    r'^\s*In conclusion,\s*',
    r'^\s*In summary,\s*',
    r'^\s*Overall,\s*',
    r'^\s*Importantly,\s*',
    r'^\s*Notably,\s*',
    r'^\s*In addition,\s*',
    r'^\s*As a result,\s*',
    r'^\s*Consequently,\s*',
    r'^\s*Therefore,\s*',
    r'^\s*To summarize,\s*',
    r'^\s*To conclude,\s*',
    r'^\s*In light of (?:this|the above),\s*',
    r'^\s*That being said,\s*',
    r'^\s*Having said that,\s*',
    r'^\s*It is worth noting that\s*',
    r'^\s*It is important to note that\s*',
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. NEGATIVE PARALLELISM PATTERNS  ("not only X, but also Y" structures)
# ─────────────────────────────────────────────────────────────────────────────
NEGATIVE_PARALLELISM: List[Tuple[str, str]] = [
    (r'not only\s+([^,]+),\s*but also\s+([^.]+)',        r'\1 and \2'),
    (r'not just\s+([^,]+),\s*it is\s+([^.]+)',           r'\2 rather than solely \1'),
    (r'not merely\s+([^,]+),\s*but\s+([^.]+)',           r'\1 alongside \2'),
    (r"it'?s not (?:just|only)\s+([^,]+),\s*it'?s\s+([^.]+)", r'\2 — not simply \1'),
]

# ─────────────────────────────────────────────────────────────────────────────
# 4. RULE-OF-THREE DETECTOR  (adjectives or nouns in triplets)
#    We log these for audit but do not auto-replace (context-sensitive)
# ─────────────────────────────────────────────────────────────────────────────
RULE_OF_THREE_PATTERN = re.compile(
    r'\b(\w[\w\s-]+),\s+(\w[\w\s-]+),\s+and\s+(\w[\w\s-]+)\b'
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. SENTENCE-LENGTH VARIATION (Burstiness Injection)
#    Target: stddev of sentence lengths > 15 words
#    Heuristic check only — cannot auto-rewrite, but flags for audit
# ─────────────────────────────────────────────────────────────────────────────

def compute_burstiness(text: str) -> float:
    """
    Computes burstiness score: standard deviation of sentence word counts.
    Human text typically scores > 10. AI text often scores < 7.
    Returns standard deviation (higher = more human-like variation).
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    lengths = [len(s.split()) for s in sentences if len(s.split()) >= 3]
    if len(lengths) < 3:
        return 0.0
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return variance ** 0.5


def inject_burstiness(text: str) -> str:
    """
    Attempts to break monotone sentence rhythm by splitting excessively long
    sentences (> 45 words) at natural conjunction points, and by flagging
    paragraphs where all sentences are 15–25 words long.

    This is a heuristic pass — it splits at ' which ', ' where ', ' while ',
    and ' although ' to create shorter follow-up sentences.
    """
    # Split overlong sentences at secondary conjunctions
    split_triggers = [
        (r',\s+which\s+',  '. This '),
        (r',\s+where\s+',  '. Here '),
        (r',\s+while\s+',  '. At the same time, '),
        (r',\s+although\s+', '. However, '),
    ]

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    new_sentences = []
    for sent in sentences:
        words = sent.split()
        if len(words) > 45:
            broken = sent
            for trigger, replacement in split_triggers:
                broken = re.sub(trigger, replacement, broken, count=1)
                if len(broken.split()) < len(words):
                    break
            new_sentences.append(broken)
        else:
            new_sentences.append(sent)

    return ' '.join(new_sentences)


# ─────────────────────────────────────────────────────────────────────────────
# 6. EM-DASH OVERUSE CLEANER
#    Em-dashes (—) are now a flagged AI tell when used more than once per
#    paragraph. We replace excess em-dashes with commas or semicolons.
# ─────────────────────────────────────────────────────────────────────────────

def clean_em_dashes(text: str) -> str:
    """
    Caps em-dash usage to at most 1 per paragraph.
    Subsequent em-dashes in the same paragraph are replaced with commas.
    """
    paragraphs = text.split('\n\n')
    cleaned_paragraphs = []
    for para in paragraphs:
        dashes = para.count('—')
        if dashes <= 1:
            cleaned_paragraphs.append(para)
        else:
            # Keep first em-dash, replace the rest
            first_replaced = False
            result = []
            for char in para:
                if char == '—':
                    if not first_replaced:
                        result.append('—')
                        first_replaced = True
                    else:
                        result.append(',')
                else:
                    result.append(char)
            cleaned_paragraphs.append(''.join(result))
    return '\n\n'.join(cleaned_paragraphs)


# ─────────────────────────────────────────────────────────────────────────────
# 7. OVER-POLISHED SENTENCE CLEANER
#    "serves as", "represents a", "highlights the importance of" etc.
# ─────────────────────────────────────────────────────────────────────────────
OVER_POLISH_PATTERNS: List[Tuple[str, str]] = [
    (r'\bserves? as an? (?:important|key|critical|significant) (?:tool|mechanism|approach|means)\b',
     'provides'),
    (r'\bplays an? (?:important|key|essential|integral) role\b', 'is important'),
    (r'\bprovides? a (?:comprehensive|detailed|thorough) overview of\b', 'reviews'),
    (r'\baims? to (?:provide|offer|deliver) a (?:comprehensive|thorough|detailed)\b', 'reviews'),
    (r'\bthe (?:aforementioned|above-mentioned) (?:\w+ ){0,3}\b', 'the described '),
    (r'\bthe present study\b',  'this study'),
    (r'\bthe current study\b',  'this study'),
    (r'\bthe proposed (?:method|approach|framework|system)\b', 'our method'),
    (r'\bit can be (?:observed|seen|noted) that\b', ''),
    (r'\bThis paper (?:presents|proposes|introduces) a novel\b', 'This paper presents a new'),
    (r'\bstate-of-the-art\b',  'leading'),
    (r'\bsophisticated\b',     'complex'),
    (r'\bparadigm\b',          'approach'),
]


# ─────────────────────────────────────────────────────────────────────────────
# 8. HUMAN WRITING SYSTEM PROMPT
#    Injected into every LLM call. Synthesized from all research sources.
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 8-A. AUTHOR STYLE PROFILE
# Extracted from the author's published paper:
# "Intelligent heart monitoring system with ESP32, and cloud services"
# Hussein Mohammed Ridha, University of Information Technology and Communications, Baghdad, Iraq
#
# Key stylistic fingerprints observed and encoded below:
# ─────────────────────────────────────────────────────────────────────────────
AUTHOR_STYLE_PROFILE = """
═══ AUTHOR WRITING STYLE PROFILE (Hussein M. Ridha, 2022) ═══

This is the voice and writing style to emulate in ALL generated papers.
Study the patterns below and reproduce them faithfully.

── 1. SENTENCE LENGTH & RHYTHM ──
The author mixes short declarative sentences with longer explanatory ones naturally.
Examples from the paper:
  "ECG machines are standard equipment in operating rooms and ambulances."  [short, blunt]
  "The ESP32 is a system on a chip microcontroller, it is affordable, consume low power,
   and has a Wi-Fi and dual-mode Bluetooth built-in."  [longer, listing real specs]
  "According to international research, the probability of heart disease patients surviving
   a heart attack increases by 90% or more if the patient's condition is responded to in the
   first 90 minutes of the injury, and here comes the importance of this research."  [complex, builds to a point]

Rules:
- Alternate short (6-12 word) and long (25-40 word) sentences.
- Use comma-joined compound clauses freely: "it is affordable, consume low power, and has Wi-Fi".
- End sections with a short punchy sentence that anchors the whole argument.

── 2. DEFINITION-IN-PARENTHESES / INLINE-DEFINITION STYLE ──
The author defines acronyms and technical concepts inline at first use, inside parentheses:
  "ECG (An electrocardiogram (ECG or EKG) records the electrical signal from your heart to
   check for different heart conditions.)"
  "IOT (The Internet of Things, or IoT, refers to the billions of physical devices around
   the world that are now connected to the internet, all collecting and sharing data.)"

Rules:
- At FIRST use of any acronym or technical term, provide a full parenthetical definition.
- The definition should be a complete standalone sentence inside the parentheses.
- After the first definition, use the acronym alone.

── 3. GROUNDING IN REAL NUMBERS & STATISTICS ──
The author always grounds claims in specific numbers:
  "At a 240MHz the ESP32 operates at a much higher frequency than ordinary Arduino boards (20MHz for Arduino UNO)"
  "There are about 50 billion devices connected to the internet as of 2020, this number is
   expected to increase to 75 billion devices by 2025."
  "The percentage of deaths in 2008 related to CVD was 30% of global deaths"
  "The result was 95% because of the noise in the experimental device"

Rules:
- Every claim about scale, performance, or comparison MUST include a real number.
- Quote years, percentages, frequencies, counts, or sizes — never say "many" or "significantly".
- Comparison must name the baseline: "(20MHz for Arduino UNO)" not just "slower".

── 4. HONEST DISCUSSION OF RESULTS AND LIMITATIONS ──
The author states results plainly and admits why they fell short:
  "The result was 95% because of the noise in the experimental device and it is not an integrated unit."
  "The system can be developed by designing a more compact machine wearable and using a battery."

Rules:
- State the actual measured performance number first.
- Then explain the specific cause of any limitation directly ("because of the noise").
- Future improvements are stated as practical engineering fixes, not vague "future work".

── 5. PRACTICAL ORIENTATION: COST, SIZE, POWER ──
The author consistently values cost-effectiveness and practicality:
  "so the system will be cheap and easy to build, but at the same time, it is reliable"
  "to keep the entire device small, light and cheap"
  "the power consumption is kept in µW level and thanks to the standby capability in ESP32
   the power consumption will be in nW level"

Rules:
- Mention cost, size, or power implications where relevant.
- Use the phrase "cheap and easy to build" or its equivalents when discussing accessible systems.
- Quantify power: µW, nW, mW — not just "low power".

── 6. STRUCTURED REQUIREMENTS SECTION (A, B, C... lettered lists) ──
The author organizes requirements with lettered items:
  "3.1. The Physical requirements
   A- Integrated Central Processing Unit (esp32)
   B- Heart rate sensor (SPO2) and (ECG).
   C- The LCD screen to display the results."

Rules:
- Use "A-", "B-", "C-" lettered items (not numbers) for requirement/component lists.
- Group requirements into sub-categories: Physical, Software, User.
- Keep each item concise — one line per item.

── 7. PRACTICAL USE CASE EXAMPLES IN INTRODUCTION ──
The author always gives concrete real-world examples of who uses the system:
  "athletes and people whose hearts can be stressed in their workplaces"
  "a person with a heart monitor implant, a farm animal with a biochip transponder"

Rules:
- In the Introduction, name 2-3 specific target user groups with descriptive detail.
- Use "for example" or parenthetical asides to introduce these.
- Users are real people in real situations, not abstract "stakeholders".

── 8. DISCUSSION SECTION = COMPARISON + DEVELOPMENT ROADMAP ──
The paper's Discussion explicitly compares to commercial devices and then proposes next-version improvements:
  "There was a comparison between the commercial devices and the system. The result was 95%..."
  "The system can be developed by designing a more compact machine wearable and using a battery
   instead of ups. Also using FFT (Fast Fourier Transform) where the error is zero and removing noise."

Rules:
- Discussion section MUST include: (a) quantitative comparison to existing/commercial solutions, (b) explanation of gap, (c) specific next-version engineering improvements.
- Improvements are TECHNICAL and CONCRETE, not aspirational.

── 9. CONCLUSION = RESTATE THE PROBLEM + REAL-WORLD IMPACT + SURVIVAL STATISTIC ──
The author closes by restating the problem in human terms (life-or-death stakes) with a key statistic:
  "According to international research, the probability of heart disease patients surviving a
   heart attack increases by 90% or more if the patient's condition is responded to in the
   first 90 minutes of the injury"

Rules:
- Conclusion must restate the real-world motivation (not just the technical result).
- Include at least one human-impact statistic (survival rate, cost savings, population size).
- Last sentence should name the practical significance, not summarize methodology.

── 10. NATURAL CONNECTORS, NOT AI TRANSITIONS ──
The author uses natural connectors:
  "In addition to the Wi-Fi..." (structural addition)
  "because we need to process..." (causal reasoning stated plainly)
  "and here comes the importance of this research" (conversational, informal)
  "Also using FFT..." (informal sequential)

Rules:
- Use "Also", "In addition to", "because", "where" as connectors — not "Furthermore", "Moreover".
- Conversational asides like "and here comes the importance" are acceptable and humanize the text.
- Start occasional sentences with "Also" or "And" — the author does this naturally.
"""

HUMAN_WRITING_SYSTEM_PROMPT = """
You are writing as a senior human academic researcher with 15+ years of publication experience.
Your writing must pass GPTZero and Turnitin AI detection by displaying genuine human stylometric
fingerprints: lexical diversity, burstiness, specific grounded claims, natural hedging, and
occasional disciplinary voice markers.

══ ABSOLUTE PROHIBITIONS (NEVER USE) ══

BANNED VOCABULARY: delve into, at its core, in the realm of, pivotal role, stands as a testament,
rich tapestry, game-changing, seamless, treasure trove, boasts, groundbreaking, cutting-edge,
transformative, comprehensive, robust, a myriad of, landscape (as metaphor), ecosystem (as metaphor),
underscores, game-changer, it is important to note, it is worth mentioning, it goes without saying,
utilize/utilization, facilitate (when "help" works), leverage (when "use" works), elucidate,
commence, endeavor, that being said, state-of-the-art, sophisticated (when "complex" works),
paradigm, novel (as an adjective meaning "new"), paramount, plethora.

BANNED STRUCTURES:
- Negative parallelism: "not only X but also Y", "not just X, it's Y", "not merely X, but Y"
- Rule-of-three triplets as a reflex: "scalable, robust, and efficient"
- Inflated significance: "marks a pivotal moment", "solidified its role", "part of a broader movement"
- Paragraph-opening transitions (more than once per section): Furthermore, Moreover, Additionally,
  In conclusion, In summary, Overall, Importantly, Notably, Consequently, Therefore
- Vague hedge-attributions: "studies have shown", "many experts believe", "some critics argue"
  — always cite specific works instead.
- Em-dash overuse: maximum one em-dash per paragraph
- Mechanical triple-positive closers: "this approach is scalable, reliable, and efficient"

══ REQUIRED HUMAN-WRITING TECHNIQUES ══

1. BURSTINESS — vary sentence length with intention:
   - Short punchy sentence after a long complex one. Like this.
   - Mix 8-word sentences with 35-word ones. Avoid metronomic rhythm where every sentence runs 18-22 words.
   - Occasionally interrupt a long sentence mid-clause with a period. Start fresh.

2. SPECIFIC GROUNDED CLAIMS — replace every vague statement with a concrete one:
   - Bad: "Performance improved significantly."
   - Good: "Accuracy rose from 71.3% to 84.6% on the CIFAR-100 benchmark, consistent across 5 runs."
   - Include: exact percentages, dataset names, sample sizes, error margins, parameter counts.

3. AUTHENTIC HEDGING — use modal qualifications, not hollow disclaimers:
   - Use: may, might, could, suggests, appears to, tends to, in most configurations
   - State the scope boundary: "within the conditions of this study", "for the 3-layer variant"
   - Avoid: "obviously", "clearly", "it is evident that", "needless to say"

4. DISCIPLINARY VOICE — write as someone who has spent years in the field:
   - Reference prior work critically: "Unlike [Author et al., 2022], who assumed X, we observe Y"
   - Acknowledge genuine engineering trade-offs: "This gain comes at the cost of X"
   - Name the limitation first, then the workaround — not the reverse

5. SENTENCE OPENING VARIETY — never start three consecutive sentences the same way:
   - Vary with: prepositional phrases, participial phrases, adverbial clauses, inverted syntax
   - Example: "Across all configurations, latency remained below 20 ms."
   - Example: "Computing overhead aside, the model generalizes well to unseen domains."
   - Example: "Whether this holds for sparse data remains an open question."

6. ACTIVE VOICE PREFERENCE — passive voice signals AI more than active:
   - Bad: "It was found that X was improved by Y."
   - Good: "Y improved X by 12 percentage points."
   - Use passive only when the agent is genuinely unknown or irrelevant.

7. HONEST LIMITATIONS — dedicate real space to constraints:
   - Describe WHY a limitation exists, not just that it exists
   - Quantify impact where possible: "reduces accuracy by ~4% on out-of-distribution samples"
   - Do not soften limitations with immediate "future work" pivots

8. NATURAL FLOW WITHOUT MECHANICAL TRANSITIONS:
   - Let paragraphs begin with their core subject or claim, not a transition word
   - Use "But", "And", "So" at sentence start occasionally — human writers do this
   - Connect ideas through logical progression, not connector words

9. LEXICAL DIVERSITY — do not reuse the same adjective or verb more than twice per section:
   - Vary: propose → present, show, demonstrate, find, report, observe
   - Vary: method → technique, procedure, strategy, protocol, approach (rotate these)
   - Vary: significant → large, considerable, marked, notable, measurable (pick the accurate one)

10. PSYCHOLINGUISTIC AUTHENTICITY — simulate real cognitive writing process:
    - Occasionally use a parenthetical aside: "(and this distinction matters for the following reason)"
    - Use precise qualifications mid-sentence rather than only in disclaimers sections
    - Show your reasoning process: "The key question is not X but rather Y"
    - Use contrastive analysis: "Model A outperforms on sparse inputs; Model B is faster overall"

══ AUTHOR VOICE CONTRACT (Hussein M. Ridha style) ══

You write like a working engineer-academic, not a native-English literary scholar.
Your writing is direct, grounded, and practically oriented. Follow these voice rules:

A. INLINE DEFINITIONS: Define every acronym or technical term the first time it appears
   using parenthetical full-sentence definitions. Example:
   "The MQTT broker (MQTT is the standard for IoT messaging — it allows devices to publish
    and subscribe to topics without knowing each other's IP address) handles all routing."

B. REAL NUMBERS MANDATORY: Never write "many", "significant", or "large-scale" without
   a specific number. Always include: year, percentage, frequency, count, or size.
   Example: "As of 2024, over 15 billion IoT devices are connected globally [3]."

C. PRACTICAL FRAMING: Mention cost, size, power, or ease-of-deployment where relevant.
   The reader is a practitioner who needs to build this, not just understand it theoretically.

D. HONEST RESULTS: State results as "X%" then immediately explain WHY any gap exists.
   Example: "Accuracy reached 93%, limited by sensor noise at the analog front-end."

E. A-B-C LISTS for requirements, components, and features (use letters, not numbers).

F. HUMAN CONNECTORS: Use "Also", "In addition to", "because", "where" to connect ideas.
   Conversational closers like "and here comes the importance of this work" are acceptable.

G. CONCLUSION STRUCTURE: Close by restating the human problem (lives, access, cost),
   then one impact statistic, then one practical next step.
"""


# ─────────────────────────────────────────────────────────────────────────────
# 9. TRANSITION VARIETY TABLE
#    Used in randomize_transitions() to replace robotic connectors
# ─────────────────────────────────────────────────────────────────────────────
TRANSITION_ALTERNATIVES = {
    'furthermore':   ['Beyond this,', 'Building on this,', 'The picture grows more complex:',
                      'Related to this,', 'On a related note,'],
    'moreover':      ['And yet,', 'Adding to this,', 'There is also the matter of',
                      'Compounding this,', 'Equally relevant,'],
    'additionally':  ['Also,', 'On top of this,', 'Worth noting as well,',
                      'Alongside this,', 'A second consideration:'],
    'however':       ['But,', 'Still,', 'That said,', 'The problem is',
                      'There is a catch:', 'The trade-off is'],
    'therefore':     ['So,', 'This means', 'The implication is', 'Accordingly,',
                      'Given this,'],
    'consequently':  ['As a result,', 'This leads to', 'The effect is', 'So,'],
    'in conclusion': ['To close,', 'Taken together,', 'The evidence points to',
                      'Stepping back,'],
    'in summary':    ['In short,', 'The core finding is', 'Taken together,', 'Put simply,'],
    'overall':       ['Across the board,', 'On balance,', 'The pattern is consistent:'],
    'notably':       ['Worth flagging:', 'One standout result:', 'Of interest,'],
    'importantly':   ['Critically,', 'A key finding:', 'Worth emphasizing:'],
}


def randomize_transitions(text: str) -> str:
    """
    Replaces generic AI transition openers with varied human alternatives.
    Only replaces at sentence/paragraph starts to avoid over-processing.
    """
    result = text
    for bland, alternatives in TRANSITION_ALTERNATIVES.items():
        # Match at sentence start (after newline or period+space)
        pattern = r'(?m)(?<=\n)' + bland.capitalize() + r',?\s+'
        alt = random.choice(alternatives) + ' '
        result = re.sub(pattern, alt, result, flags=re.IGNORECASE)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 10. MAIN CLEANING PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def clean_humanized_text(text: str) -> str:
    """
    Full humanization pipeline. Call this on all generated prose.

    Order of operations:
    1. Strip over-transitions at paragraph starts
    2. Replace AI cliché vocabulary
    3. Dissolve negative parallelisms
    4. Apply over-polish pattern cleanup
    5. Clean em-dash overuse
    6. Inject burstiness (split overlong sentences)
    7. Randomize remaining bland transitions
    8. Final whitespace normalization
    """
    cleaned = text

    # Step 1: Remove formulaic paragraph openers
    for ot in OVER_TRANSITIONS:
        cleaned = re.sub(ot, '', cleaned, flags=re.MULTILINE)

    # Step 2: Replace AI cliché vocabulary
    for pattern, replacement in AI_CLICHE_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Step 3: Dissolve negative parallelisms
    for pattern, replacement in NEGATIVE_PARALLELISM:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Step 4: Over-polish cleanup
    for pattern, replacement in OVER_POLISH_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Step 5: Em-dash overuse
    cleaned = clean_em_dashes(cleaned)

    # Step 6: Burstiness injection (split overlong sentences)
    cleaned = inject_burstiness(cleaned)

    # Step 7: Randomize remaining bland transitions
    cleaned = randomize_transitions(cleaned)

    # Step 8: Normalize whitespace
    cleaned = re.sub(r'  +', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 11. COMPREHENSIVE AUDIT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def audit_text_humanization(text: str) -> List[str]:
    """
    Audits text for AI tells and returns a diagnostic list of issues.
    Used in testing and quality control pipelines.
    """
    issues = []

    # Check AI clichés
    for pattern, _ in AI_CLICHE_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            issues.append(f"AI stock phrase detected: '{pattern}' ({len(matches)} occurrence(s))")

    # Check over-polish patterns
    for pattern, _ in OVER_POLISH_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            issues.append(f"Over-polished phrase: '{pattern}'")

    # Check negative parallelism
    if re.search(r'\bnot (?:only|just|merely)\b', text, flags=re.IGNORECASE):
        issues.append("Possible negative parallelism ('not only / not just / not merely')")

    # Check over-transitioning
    transitions_found = 0
    for ot in OVER_TRANSITIONS:
        if re.search(ot, text, flags=re.MULTILINE):
            transitions_found += 1
    if transitions_found > 2:
        issues.append(f"Excessive formulaic transitions: {transitions_found} paragraph openers found")

    # Check burstiness
    score = compute_burstiness(text)
    if score < 6.0:
        issues.append(
            f"Low burstiness score ({score:.1f}) — sentence lengths too uniform. "
            "Mix short punchy sentences with longer analytical ones."
        )

    # Check em-dash density
    em_dash_count = text.count('—')
    paragraph_count = max(1, len(text.split('\n\n')))
    if em_dash_count > paragraph_count:
        issues.append(
            f"Em-dash overuse: {em_dash_count} em-dashes across {paragraph_count} paragraphs. "
            "Max recommended: 1 per paragraph."
        )

    # Check rule-of-three density
    triplets = RULE_OF_THREE_PATTERN.findall(text)
    if len(triplets) > 3:
        issues.append(
            f"Rule-of-three overuse: {len(triplets)} comma-separated triplets detected. "
            "Vary list lengths (use 2 or 4 items instead)."
        )

    # Check vague hedges
    vague_hedges = re.findall(
        r'\b(?:studies have shown|many experts|some critics|widely accepted|it is evident)\b',
        text, flags=re.IGNORECASE
    )
    if vague_hedges:
        issues.append(
            f"Vague hedge-attributions: {len(vague_hedges)} found. "
            "Replace with specific citations (Author, Year)."
        )

    # Check for uniform verb usage
    generic_verbs = re.findall(r'\b(?:show|demonstrate|prove|indicate)\b', text, flags=re.IGNORECASE)
    if len(generic_verbs) > 8:
        issues.append(
            f"Repetitive verb usage: '{', '.join(set(v.lower() for v in generic_verbs))}' "
            f"used {len(generic_verbs)} times. Vary with: reveal, confirm, find, report, observe."
        )

    return issues
