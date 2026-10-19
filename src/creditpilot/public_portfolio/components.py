"""Pure presentation over validated public objects; Streamlit and stdlib only.

Adapted concepts: owner portfolio_app _card, _feature_name, _risk_tab,
_route_banner and _executive_journey. No owner module import or snapshot adapter.
Renderers never mutate inputs. Journey summaries bind existing public event refs.
"""
import hashlib
from html import escape
from pathlib import Path
import textwrap

import streamlit as st

RECOMMENDATIONS = {'APPROVAL_RECOMMENDATION': 'Approval recommendation',
                   'REVIEW_RECOMMENDATION': 'Review recommendation',
                   'DECLINE_RECOMMENDATION': 'Decline recommendation'}
DECISION_RULES = {'DPV1_PD_LOW': 'Low PD band · synthetic decision policy',
                  'DPV1_PD_INTERMEDIATE': 'Intermediate PD band · synthetic decision policy',
                  'DPV1_PD_HIGH': 'High PD band · synthetic decision policy'}
ROUTES = {'NO_PHASE10_ACTION': 'Straight-through decision',
          'HUMAN_CREDIT_REVIEW': 'Human Credit Review',
          'HUMAN_INVESTIGATION': 'Human Investigation',
          'OPERATIONAL_HANDLING': 'Operational handling'}
FEATURE_NAMES = {'monthly_income': 'Monthly income', 'MonthlyIncome': 'Monthly income',
                 'debt_ratio': 'Debt ratio', 'DebtRatio': 'Debt ratio',
                 'revolving_utilization': 'Credit utilization', 'RevolvingUtilization': 'Credit utilization',
                 'Delinquency30To59Days': '30–59 days past due',
                 'Delinquency60To89Days': '60–89 days past due', 'Delinquency90Days': '90+ days past due',
                 'NumberOfDependents': 'Dependents', 'number_of_dependents': 'Dependents'}
LIMITATIONS = {
    'RECORDED_OFFLINE': 'Recorded offline results; navigation does not run a credit workflow.',
    'SYNTHETIC_FIXTURES': 'Synthetic demonstration applicants and Verification evidence only.',
    'DETERMINISTIC_ADAPTERS': 'Deterministic offline policy/explanation adapters and demonstration embeddings; no live LLM claim.',
    'PD_PROXY': 'PD is a dataset-specific two-year serious-delinquency portfolio proxy, not a bank regulatory PD.',
    'PARTIAL_SHAP': 'Grouped Top-K SHAP is partial attribution in raw-score/log-odds units; displayed contributions need not sum to the score.',
    'INITIAL_SNAPSHOTS_UNAVAILABLE': 'Initial historical model/policy snapshots are unavailable; current values are not presented as initial values.',
    'HISTORICAL_METRICS_MISSING': 'Historical KS, precision, recall and F1 evidence is missing; no holdout was reopened to reconstruct it.',
    'RAG_AGENT_UNSCORED': 'RAG/Agent quality baselines remain unscored; no new quality certification is implied.',
}

ASSET_DIRECTORY = Path(__file__).resolve().parent / 'assets'
ARCHITECTURE_ASSETS = {
    'system': ('creditpilot-system-architecture.png', '223c86d6e9d04cac0294d7152d8bdb30b2df23adcaa97a58abe8f0bef7be197f', (1475, 1298)),
    'runtime': ('creditpilot-runtime-workflow.png', 'ad6a46f83a387a36287e84add30f1679fc8606a4953250639b24a61e74fab4a1', (1536, 1024)),
}

# Static presentation coordinates and labels ported from the Owner Demo's
# _architecture_svg(). No Owner Demo module or runtime data is imported.
ARCHITECTURE_NODES = [
    (40, 70, "INPUT / EVIDENCE", "Application", ["Immutable reported evidence", "Tokenized identity"], "#edf6f0"),
    (420, 70, "INPUT / EVIDENCE", "Deterministic Validation", ["DataQualityAssessment", "Missing / invalid → human-data request"], "#edf6f0"),
    (800, 70, "INPUT / EVIDENCE", "Feature Source Resolver", ["FeatureSourcePolicy + lineage", "Feature Engineering"], "#edf6f0"),
    (800, 225, "RISK INTELLIGENCE", "Risk Model + Calibration", ["Quantitative PD proxy", "SHAP · raw model score"], "#eef4f8"),
    (420, 225, "POLICY INTELLIGENCE", "Policy Agent + Grounded RAG", ["Synthetic Policy Knowledge Base", "Hybrid retrieval · versioned FAISS"], "#f0eef7"),
    (40, 225, "AGENTIC ORCHESTRATION", "Orchestrator Agent", ["Reads persisted CreditState", "Proposes · never authorizes routes"], "#f0eef7"),
    (40, 510, "DECISION / VERIFICATION", "Verification Request Builder", ["Controller-authorized immutable scope", "Verification Agent · execution only"], "#edf6f0"),
    (420, 510, "DECISION / VERIFICATION", "Policy Evidence Validator", ["Provenance · support · consistency", "Current context-bound evidence only"], "#edf6f0"),
    (800, 510, "DECISION / VERIFICATION", "Decision Engine", ["Deterministic recommendation", "Exclusive decision-field writer"], "#edf6f0"),
    (40, 675, "INPUT / EVIDENCE", "Verified evidence + Resolver", ["Reported evidence stays immutable", "Changed vector → risk / SHAP / policy"], "#edf6f0"),
    (420, 675, "HUMAN GOVERNANCE", "Escalation Agent", ["Approved handoff preparation", "No lending or routing authority"], "#f0eef7"),
    (800, 675, "HUMAN GOVERNANCE", "Human Review", ["Authorized human Final Outcome", "Separate from System Recommendation"], "#fbf5e8"),
    (40, 840, "EXTERNAL ACTIONS / AUDIT", "Persisted audit artifacts", ["SQLite workflow ledger + recovery", "Evidence · decisions · human records"], "#eef4f8"),
    (420, 840, "EXTERNAL ACTIONS / AUDIT", "Guarded ACTION tools", ["create_review_case → Slack / email", "Preconditions · idempotency · receipts"], "#fbf5e8"),
    (800, 840, "AGENTIC ORCHESTRATION", "Explanation Agent", ["Persisted decision evidence only", "Read-only relative to decision facts"], "#f0eef7"),
]
ARCHITECTURE_EDGES = ["M370 120 H420", "M750 120 H800", "M965 170 V225", "M800 275 H750",
                      "M420 275 H370", "M205 325 V370", "M205 460 V510", "M585 460 V510",
                      "M750 560 H800", "M205 610 V675", "M585 775 V840", "M750 725 H800",
                      "M420 890 H370"]
ARCHITECTURE_BRANCHES = ["M40 725 H20 V45 H965 V70", "M750 415 H780 V650 H585 V675",
                         "M965 610 V675", "M720 460 V480 H1140 V650 H965 V675",
                         "M1130 560 H1155 V890 H1130", "M800 890 H780 V955 H205 V940"]


def safe(value):
    return escape(str(value), quote=True)


def label(value):
    return 'Not recorded' if value is None else str(value).replace('_', ' ').title()


def feature_name(value):
    return FEATURE_NAMES.get(value, label(value))


def value_text(feature, value):
    if value is None:
        return 'Not recorded'
    if feature == 'monthly_income':
        return '${:,.0f}'.format(value)
    return str(value)


def text(value):
    """Escape source text even though the strict loader already screens it."""
    st.markdown('<p class="cp-copy">' + safe(value) + '</p>', unsafe_allow_html=True)


def cards(items, *, summary=False):
    grid = 'cp-summary-grid' if summary else 'cp-grid'
    st.markdown('<div class="{}">'.format(grid) + ''.join(
        '<div class="cp-card"><div class="cp-eyebrow">{}</div><div class="cp-value">{}</div>'
        '<div class="cp-note">{}</div></div>'.format(safe(k), safe(v), safe(note))
        for k, v, note in items) + '</div>', unsafe_allow_html=True)


def style():
    st.markdown('''<style>
    :root {--cp-ink:#172b3a;--cp-muted:#617384;--cp-line:#dce4ea;--cp-blue:#145b7d;--cp-panel:#fff;--cp-canvas:#f4f7f9;}
    .stApp {background:var(--cp-canvas);color:var(--cp-ink);}
    [data-testid="stHeader"] {background:transparent;}
    [data-testid="stMainBlockContainer"] {max-width:1480px;padding-top:1.35rem;}
    [data-testid="stSidebar"] {background:#172b3a;}
    [data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] p,[data-testid="stSidebar"] label {color:#e7eef4;}
    [data-testid="stSidebar"] button p {color:#172b3a;}
    [data-testid="stSidebar"] .cp-sidebar-brand {color:#fff;font-size:1.36rem;font-weight:760;letter-spacing:.055em;margin-top:.25rem;}
    [data-testid="stSidebar"] .cp-sidebar-kicker {color:#9fd3dc;font-size:.72rem;font-weight:750;letter-spacing:.13em;margin:.15rem 0 1.35rem;}
    [data-testid="stSidebar"] .cp-sidebar-copy {color:#e7eef4;font-size:.95rem;font-weight:650;margin-bottom:1rem;}
    [data-testid="stSidebar"] .cp-sidebar-status {color:#fff;background:#12577a;border:1px solid #78cbd4;border-radius:8px;padding:.7rem .8rem;font-weight:700;margin-bottom:1.15rem;}
    .cp-hero {background:#fff;color:#172b3a;border:1px solid #dce4ea;border-left:5px solid #145b7d;border-radius:9px;padding:25px 29px;margin-bottom:18px;box-shadow:0 1px 2px rgba(21,43,58,.04);}
    .cp-hero h1 {font-size:2.05rem;letter-spacing:-.035rem;margin:8px 0;color:#172b3a;}
    .cp-hero p {max-width:920px;color:#617384;line-height:1.58;}
    .cp-hero .cp-tagline {font-size:1rem;font-weight:650;color:#145b7d;margin:3px 0 8px;}
    .cp-hero .cp-description {margin:6px 0 10px;max-width:1150px;font-size:.94rem;line-height:1.5;}
    .cp-explore {display:flex;flex-wrap:wrap;gap:5px 25px;padding-left:18px;margin:8px 0 12px;font-size:.84rem;line-height:1.45;color:#426b7d;}
    .cp-hero .cp-disclosure {max-width:none;margin:0;padding-top:10px;border-top:1px solid #dce4ea;font-size:.8rem;line-height:1.5;color:#425b6b;}
    .cp-kicker {font-size:.74rem;letter-spacing:.12rem;text-transform:uppercase;color:#145b7d;font-weight:750;}
    .cp-summary-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem;margin:.55rem 0;}
    .cp-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,245px),1fr));gap:14px;margin:14px 0 24px;}
    .cp-card {box-sizing:border-box;min-width:0;height:100%;min-height:118px;background:#fff;border:1px solid #dce4ea;border-radius:9px;padding:1rem 1.05rem;color:#172b3a;box-shadow:0 1px 2px rgba(21,43,58,.04);}
    .cp-eyebrow {font-size:.76rem;color:#617384;font-weight:700;letter-spacing:.035em;text-transform:uppercase;margin-bottom:.62rem;}
    .cp-value {font-size:1.2rem;font-weight:720;line-height:1.3;overflow-wrap:anywhere;}
    .cp-note {font-size:.82rem;color:#617384;margin-top:.38rem;line-height:1.4;}
    .cp-copy {line-height:1.65;white-space:pre-wrap;overflow-wrap:anywhere;}
    .cp-workflow-svg {display:block;width:100%;height:auto;overflow:visible;margin:.7rem 0 1rem;}
    .cp-workflow-narrow {display:none!important;}
    .cp-flow-arrow {fill:none;stroke:#718792;stroke-width:2;marker-end:url(#cp-arrow-wide);}
    .cp-branch-line {fill:none;stroke:#718792;stroke-width:2;}
    .cp-svg-icon {font:800 22px system-ui,-apple-system,sans-serif;}
    .cp-svg-state {font:760 10px system-ui,-apple-system,sans-serif;letter-spacing:.055em;}
    .cp-svg-title {font:720 16px system-ui,-apple-system,sans-serif;fill:#172b3a;}
    .cp-svg-component {font:500 11.5px system-ui,-apple-system,sans-serif;fill:#426b7d;}
    .cp-svg-note {font:500 12px system-ui,-apple-system,sans-serif;fill:#617384;}
    .cp-income-cell {fill:#f7fafb;stroke:#d5e0e6;stroke-width:1;}
    .cp-income-label {font:700 9px system-ui,-apple-system,sans-serif;letter-spacing:.035em;fill:#617384;}
    .cp-income-value {font:720 14px system-ui,-apple-system,sans-serif;fill:#172b3a;}
    .cp-semantic-banner {padding:.9rem 1rem;border-radius:8px;background:#edf5f2;border:1px solid #c9dfd5;color:#205c46;font-weight:760;margin:.4rem 0 .8rem;}
    .cp-semantic-banner.investigation {background:#fbefed;border-color:#e7c4c0;color:#8b332e;}
    .cp-outcome-note {color:#617384;font-size:.82rem;margin:.35rem 0 .9rem;}
    .cp-section-title {font-size:1.18rem;font-weight:700;margin:.1rem 0 .2rem;}
    .cp-section-note {color:#617384;font-size:.88rem;margin-bottom:.8rem;}
    .cp-why-route {border:1px solid #cfdde5;border-left:4px solid #145b7d;background:#fff;border-radius:8px;padding:1rem 1.1rem;margin:.7rem 0 1.2rem;}
    .cp-why-route.investigation {border-left-color:#a65b4c;background:#fffafa;}
    .cp-why-title {color:#172b3a;font-weight:760;font-size:1rem;letter-spacing:.035em;}
    .cp-why-chain {display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:.65rem;margin-top:.8rem;}
    .cp-why-node {border:1px solid #dce4ea;border-radius:7px;padding:.72rem;background:#f8fafb;}
    .cp-why-node small {display:block;color:#617384;font-weight:700;font-size:.68rem;letter-spacing:.045em;text-transform:uppercase;}
    .cp-why-node strong {display:block;margin-top:.3rem;color:#172b3a;overflow-wrap:anywhere;}
    [data-testid="stTable"] {overflow-x:auto;max-width:100%;}
    .cp-chart {width:100%;overflow-x:auto;}.cp-chart svg {width:100%;min-width:520px;height:auto;}
    .st-key-primary-navigation [data-testid="stHorizontalBlock"] {gap:.65rem;}
    .st-key-primary-navigation button {min-height:76px;min-width:0;display:flex;align-items:center;justify-content:center;text-align:center;border-radius:10px;padding:.75rem .85rem;white-space:normal;box-shadow:0 3px 0 #193044,0 5px 9px rgba(21,43,58,.18);}
    .st-key-primary-navigation button[kind="primary"] {background:#12577a!important;border-color:#12577a!important;border-bottom:4px solid #78cbd4!important;color:#fff!important;}
    .st-key-primary-navigation button[kind="primary"] p {color:#fff!important;font-weight:700;}
    .st-key-primary-navigation button[kind="secondary"] {background:#29445d!important;border-color:#1d354a!important;color:#fff!important;}
    .st-key-primary-navigation button[kind="secondary"] p {color:#fff!important;font-weight:700;}
    .st-key-primary-navigation button:hover {transform:translateY(-1px);filter:brightness(1.06);box-shadow:0 4px 0 #193044,0 7px 12px rgba(21,43,58,.22);}
    .st-key-primary-navigation button:active {transform:translateY(2px);box-shadow:0 1px 0 #193044,0 2px 4px rgba(21,43,58,.16);}
    .st-key-primary-navigation button:focus-visible {outline:3px solid #12577a!important;outline-offset:5px;}
    .st-key-primary-navigation button [data-testid="stMarkdownContainer"] p {white-space:normal;overflow-wrap:anywhere;text-align:center;line-height:1.2;font-size:18px;font-weight:700;}
    .cp-architecture-frame {width:100%;max-width:1180px;overflow-x:auto;background:#fff;border:1px solid #dce4ea;border-radius:9px;margin:.5rem 0 1rem;}
    .cp-architecture-svg {display:block;width:100%;min-width:960px;height:auto;font-family:system-ui,-apple-system,sans-serif;}
    .cp-architecture-full .cp-architecture-svg {min-width:1180px;}
    .cp-architecture-frame:focus-visible {outline:3px solid #145b7d;outline-offset:3px;}
    .st-key-scenario-selector [data-testid="stHorizontalBlock"] {gap:.8rem;}
    .st-key-scenario-selector button {min-height:80px;min-width:0;display:flex;align-items:center;justify-content:center;text-align:center;border-radius:9px;padding:.75rem .9rem;white-space:normal;box-shadow:0 2px 0 #aabec8,0 3px 6px rgba(21,43,58,.09);}
    .st-key-scenario-selector button[kind="primary"] {background:#087f8c!important;border:2px solid #066570!important;color:#fff!important;box-shadow:0 3px 0 #075963,0 5px 8px rgba(21,43,58,.14);}
    .st-key-scenario-selector button[kind="primary"] p {color:#fff!important;font-weight:700;}
    .st-key-scenario-selector button[kind="secondary"] {background:#f6fafb!important;border-color:#8aa8b8!important;color:#172b3a!important;}
    .st-key-scenario-selector button[kind="secondary"] p {color:#172b3a!important;font-weight:650;}
    .st-key-scenario-selector button:hover {transform:translateY(-1px);filter:brightness(.97);box-shadow:0 3px 0 #698d9d,0 5px 8px rgba(21,43,58,.13);}
    .st-key-scenario-selector button:active {transform:translateY(2px);box-shadow:0 1px 2px rgba(21,43,58,.13);}
    .st-key-scenario-selector button:focus-visible {outline:3px solid #12577a!important;outline-offset:5px;}
    .st-key-scenario-selector button [data-testid="stMarkdownContainer"] p {white-space:normal;overflow-wrap:anywhere;text-align:center;line-height:1.25;font-size:16px;}
    .st-key-technical-evidence [data-testid="stExpander"] {border:1px solid #477c8a;border-radius:10px;background:#f0f7f8;box-shadow:0 3px 8px rgba(21,43,58,.1);overflow:hidden;}
    .st-key-technical-evidence summary {padding:1rem 1.1rem!important;background:#173f54;color:#fff;}
    .st-key-technical-evidence summary p {color:#fff;font-size:1rem;font-weight:700;}
    .st-key-technical-evidence summary:hover {background:#20566a;color:#fff;}
    .st-key-technical-evidence summary:focus-visible {outline:3px solid #f0b429;outline-offset:-4px;}
    .st-key-technical-evidence .cp-evidence-description {margin:.45rem 0 .65rem;color:#426b7d;font-size:.86rem;line-height:1.5;}
    @media(max-width:1100px){.cp-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.cp-workflow-wide{display:none!important;}.cp-workflow-narrow{display:block!important;}}
    @media(max-width:800px){.st-key-primary-navigation [data-testid="stHorizontalBlock"]{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));}.st-key-primary-navigation [data-testid="column"]{width:100%!important;flex:none!important;}}
    @media(max-width:800px){.st-key-scenario-selector [data-testid="stHorizontalBlock"]{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));}.st-key-scenario-selector [data-testid="column"]{width:100%!important;flex:none!important;}.st-key-scenario-selector [data-testid="column"]:last-child{grid-column:1/-1;}}
    @media(max-width:520px){.st-key-scenario-selector [data-testid="stHorizontalBlock"]{grid-template-columns:1fr;}.st-key-scenario-selector [data-testid="column"]:last-child{grid-column:auto;}}
    @media(max-width:700px){[data-testid="stMainBlockContainer"]{padding-left:1rem;padding-right:1rem}.cp-summary-grid{grid-template-columns:1fr;}.cp-hero{padding:21px}.cp-hero h1{font-size:1.8rem}.cp-why-chain{grid-template-columns:1fr;}}
    </style>''', unsafe_allow_html=True)


def introduction():
    st.markdown('''<div class="cp-hero"><div class="cp-kicker">CREDITPILOT · AI ENGINEERING PORTFOLIO</div>
    <h1>Credit Risk Intelligence, Built for Explainable Decisions.</h1>
    <p class="cp-tagline">Evidence before decisions.</p>
    <p class="cp-description">CreditPilot is an end-to-end, agentic credit-risk decision-support system combining calibrated machine learning, explainable predictions, policy-grounded RAG, controlled verification workflows, and human-in-the-loop governance.</p>
    <ul class="cp-explore"><li>System Architecture and controlled Runtime Workflow.</li>
    <li>Three recorded synthetic Golden Scenarios, including their decision journeys and supporting evidence.</li>
    <li>Technical implementation highlights and evidence provenance.</li></ul>
    <p class="cp-disclosure"><strong>Read-only public portfolio · Precomputed synthetic scenario executions</strong><br>
    This viewer presents recorded results using offline adapters and mock external actions. No real lending or adverse-action decisions. No live notifications or privileged runtime access.</p></div>''', unsafe_allow_html=True)


def architecture_svg(*, full_size=False):
    """Render the Owner Demo's fixed architecture drawing without runtime imports."""
    marker = 'cp-public-arch-full-arrow' if full_size else 'cp-public-arch-main-arrow'
    svg = ['<svg class="cp-architecture-svg" viewBox="0 0 1180 1015" role="img" '
           'aria-label="CreditPilot system architecture: deterministic authority, quantitative ML, five agents and human governance">',
           '<defs><marker id="{}" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
           '<path d="M0,0 L0,6 L7,3 z" fill="#718792"/></marker></defs>'.format(marker)]
    for dashed, paths in ((False, ARCHITECTURE_EDGES), (True, ARCHITECTURE_BRANCHES)):
        for path in paths:
            svg.append('<path d="{}" fill="none" stroke="#718792" stroke-width="2" {} '
                       'marker-end="url(#{})"/>'.format(safe(path), 'stroke-dasharray="6 4"' if dashed else '', marker))
    svg.append('<rect x="40" y="370" width="710" height="90" rx="12" fill="#e1edf3" stroke="#145b7d"/>'
               '<text x="60" y="395" font-size="14" fill="#145b7d">CONTROLLED WORKFLOW · AUTHORITY ACROSS EVERY STAGE</text>'
               '<text x="60" y="422" font-size="21" font-weight="650" fill="#183743">Deterministic Workflow Controller / LangGraph</text>'
               '<text x="60" y="445" font-size="16" fill="#365565">Controller authorizes · LangGraph executes · mandatory rules / bounded retries</text>'
               '<text x="820" y="395" font-size="16" fill="#365565">Agents propose.</text>'
               '<text x="820" y="421" font-size="16" fill="#365565">The Controller commits.</text>'
               '<text x="820" y="447" font-size="16" fill="#365565">Humans finalize.</text>')
    for x, y, group, title, lines, fill in ARCHITECTURE_NODES:
        svg.append(f'<rect x="{x}" y="{y}" width="330" height="100" rx="10" fill="{fill}" stroke="#c5d4dc"/>')
        for offset, line, size, weight in ((23, group, 12, 600), (47, title, 18, 650),
                                          (69, lines[0], 14, 400), (88, lines[1], 14, 400)):
            svg.append(f'<text x="{x+13}" y="{y+offset}" font-size="{size}" font-weight="{weight}" fill="#183743">{safe(line)}</text>')
    svg.append('<text x="40" y="993" font-size="16" fill="#365565">PII GOVERNANCE · allowlisted context · tokenized review · agents have no MockPIIVault access</text></svg>')
    frame_class = 'cp-architecture-frame cp-architecture-full' if full_size else 'cp-architecture-frame'
    return '<div class="{}" role="region" tabindex="0" aria-label="Scrollable CreditPilot System Architecture">{}</div>'.format(
        frame_class, ''.join(svg))


def project_overview():
    st.subheader('A governed AI credit-risk workflow')
    text('CreditPilot demonstrates how machine learning and specialized agents can support an analyst while deterministic controls retain authority over evidence, routing and recommendations.')
    cards([
        ('Quantitative risk', 'Calibrated Logistic Regression', 'Dataset-specific two-year delinquency PD proxy with grouped SHAP attribution.'),
        ('Grounded policy', 'Synthetic Policy RAG', 'Retrieved policy passages remain tied to source references and current evidence context.'),
        ('Controlled investigation', 'Bounded Verification', 'Controller-authorized requests, persisted attempts, resolver lineage and recomputation.'),
        ('Human governance', 'Separate final authority', 'Decision Engine recommendations and pending Human Review remain distinct.'),
    ])
    st.markdown('<div class="cp-semantic-banner">Agents propose. The Controller commits. Humans finalize.</div>', unsafe_allow_html=True)
    st.caption('Explore the System Architecture, the three genuine recorded Golden Scenarios and the technical highlights using the navigation above.')
    st.markdown('#### CreditPilot System Architecture')
    # Keep the original approved reference screenshot integrity-gated even
    # though the public page now renders its crisp static SVG source design.
    architecture_asset('system')
    st.caption('Architecture v1.0.1 presentation view. The retained original screenshot contains an Owner Demo live-notification mode badge; this public viewer is anonymous, offline and read-only, and performs no live action.')
    st.markdown('<div class="cp-kicker">PUBLIC PORTFOLIO · READ-ONLY · OFFLINE RECORDED SCENARIOS</div>', unsafe_allow_html=True)
    st.markdown(architecture_svg(), unsafe_allow_html=True)
    st.caption('Green: deterministic components · Blue: quantitative / persistence · Purple: agent / policy intelligence · Amber: human / external actions. Dashed arrows: controlled branches and evidence feedback.')
    st.caption('Verification returns to the Resolver: changed features require risk / SHAP / policy recomputation; unchanged features use deterministic policy relevance. Mandatory Human Review precedes normal decisioning. Explanation follows a persisted decision; pre-engine investigation has no fabricated explanation. Notifications require approved escalation and an existing review case.')
    with st.expander('View CreditPilot System Architecture at full size'):
        st.markdown(architecture_svg(full_size=True), unsafe_allow_html=True)


def disclosures():
    st.caption('Synthetic Portfolio Policy — Not Real Bank Policy')
    st.caption('Synthetic demonstration threshold — not real bank policy.')
    st.caption('Synthetic decision support only; no real lending or adverse-action decision.')


def scenario_header(a):
    st.markdown('<div class="cp-section-title">{} · {}</div><div class="cp-section-note">Recorded synthetic Golden Scenario · Artifact {}</div>'.format(
        safe(a['scenario']['id']), safe(a['scenario']['title'].split(' — ', 1)[-1]), safe(a['artifact_version'])), unsafe_allow_html=True)
    h = a['human_route']
    if not a['decision']['engine_reached']:
        review_value, review_note = 'Human Investigation', 'Pending Human Review' if h['review_status'] == 'PENDING' else 'Recorded handoff'
    elif h['review_required']:
        review_value, review_note = 'Human Credit Review', 'Pending Human Review' if h['review_status'] == 'PENDING' else 'Review required'
    else:
        review_value, review_note = 'Not required', 'Straight-through route recorded'
    if not a['verification']:
        verification, verification_note = 'Not required', 'No Verification attempt recorded'
    else:
        income_count = sum(x['tool'] == 'verify_income' for x in a['verification'])
        credit_count = sum(x['tool'] == 'get_credit_report' for x in a['verification'])
        verification = '{} income · {} credit'.format(income_count, credit_count)
        verification_note = '{} persisted attempt{}'.format(len(a['verification']), '' if len(a['verification']) == 1 else 's')
    rec = RECOMMENDATIONS.get(a['decision']['system_recommendation'], 'No system recommendation')
    cards([('Calibrated Probability of Default', '{:.2%}'.format(a['risk']['calibrated_pd']), 'Persisted portfolio PD proxy'),
           ('System Recommendation', rec, 'Decision Engine reached' if a['decision']['engine_reached'] else 'Decision Engine NOT REACHED'),
           ('Human Route', review_value, review_note),
           ('Verification', verification, verification_note)], summary=True)
    rule = DECISION_RULES.get(a['decision']['decision_rule'], 'No Decision Engine rule recorded')
    terminal = {'READY':'Decision Engine reached', 'UNRESOLVED':'Evidence unresolved',
                'RUNTIME_FAILURE':'Runtime failure'}.get(a['workflow']['terminal'], 'Not recorded')
    st.markdown('<div class="cp-outcome-note">Risk classification · {} &nbsp; · &nbsp; Workflow status · {}</div>'.format(
        safe(rule), safe(terminal)), unsafe_allow_html=True)


def overview(a):
    st.subheader('The recorded outcome')
    route = a['human_route']
    if not a['decision']['engine_reached']:
        st.warning('Human Investigation required · Automated decision BLOCKED · Decision Engine NOT REACHED')
    elif route['review_required']:
        st.info('Human Credit Review required · A system recommendation is recorded; review remains pending.')
    else:
        st.success('Straight-through decision · Human Review not required in this recorded execution.')
    text('Current quantitative and policy evidence is shown below. Initial historical snapshots are unavailable.')
    st.subheader('Recorded Explanation')
    explanation = a['explanation']
    if explanation is None:
        st.info('No Phase 11 Explanation recorded. The Decision Engine was not reached.')
    else:
        st.caption('Persisted outcome · ' + explanation['status'])
        with st.expander('Read the recorded Explanation'):
            st.text(explanation['text'] if explanation['text'] is not None else 'Explanation text not recorded.')
            st.text('Source reference: ' + explanation['source_ref'])


def shap_svg(shap):
    """Diverging raw-score chart; no PD conversion or fabricated residual."""
    rows = shap['top_risk_drivers'] + shap['top_risk_reducers']
    scale = max([abs(x['contribution']) for x in rows] or [1]) or 1
    width, zero, half = 850, 500, 230
    height = 95 + len(rows) * 43
    parts = [f'<div class="cp-chart"><svg viewBox="0 0 {width} {height}" role="img" aria-label="Grouped Top-K SHAP contributions to raw model score in log-odds">',
             f'<rect width="{width}" height="{height}" fill="#f7fafb" rx="12"/>',
             f'<line x1="{zero}" x2="{zero}" y1="24" y2="{height-44}" stroke="#496774"/>']
    for i, row in enumerate(rows):
        value = row['contribution']; length = abs(value) / scale * half
        x = zero if value > 0 else zero - length
        y = 25 + i * 43
        parts.append(f'<text x="16" y="{y+17}" fill="#153441" font-size="14">{safe(feature_name(row["concept"]))}</text>')
        parts.append(f'<rect x="{x}" y="{y}" width="{length}" height="25" rx="3" fill="{"#ac5143" if value>0 else "#287d78"}"><title>{safe(row["concept"])}: {value:+.6f} log-odds</title></rect>')
        parts.append(f'<text x="{zero+half+10}" y="{y+17}" fill="#153441" font-size="13">{value:+.5f}</text>')
    parts.append(f'<text x="270" y="{height-22}" font-size="13" fill="#153441">Risk reducing ← 0 → Risk increasing</text>')
    parts.append(f'<text x="270" y="{height-5}" font-size="12" fill="#153441">Contribution to raw model score (log-odds)</text></svg></div>')
    return ''.join(parts)


def risk(a):
    r = a['risk']
    st.subheader('Calibrated Probability of Default')
    text('Dataset-specific two-year serious-delinquency portfolio PD proxy; not a bank regulatory PD.')
    cards([('Calibrated PD', '{:.2%}'.format(r['calibrated_pd']), 'Current persisted result'),
           ('Raw probability', '{:.2%}'.format(r['raw_probability']), 'Separate uncalibrated probability'),
           ('Raw model score', '{:.6f}'.format(r['raw_model_score']), 'Log-odds, not a probability')])
    st.caption('Risk band: ' + label(r['risk_band']) + ' · Model status: ' + r['status'])
    st.subheader('Risk contribution drivers')
    st.caption('Grouped Top-K SHAP · raw-score/log-odds units · partial attribution')
    text('SHAP does not directly decompose calibrated PD. Up to three drivers and three reducers are recorded; their sum need not recover the raw score.')
    shap = r['shap']
    if shap is None:
        st.info('No SHAP artifact recorded.')
    else:
        st.markdown(shap_svg(shap), unsafe_allow_html=True)
        st.caption('SHAP base score (log-odds): ' + str(shap['base_score']))
        st.table([{'Concept': feature_name(x['concept']), 'Contribution (log-odds)': x['contribution'],
                   'Direction': label(x['direction'])} for x in shap['top_risk_drivers'] + shap['top_risk_reducers']])
    with st.expander('Quantitative values and versions'):
        st.table([{'Field': key, 'Recorded value': str(r[key])} for key in
                  ('calibrated_pd', 'raw_probability', 'raw_model_score', 'model_version', 'calibration_version', 'explanation_version', 'model_timestamp')])
        for key, features in r['data_quality'].items():
            text(label(key) + ': ' + (', '.join(features) if features else 'None recorded'))


def policy(a):
    p = a['policy']
    st.subheader('Grounded synthetic policy evidence')
    st.caption('Synthetic Portfolio Policy — Not Real Bank Policy')
    text('Policy as of: ' + p['policy_as_of'])
    admission = p['admission']
    if admission is None:
        st.info('No Decision Engine admission recorded. Supported findings are not an admitted decision.')
    else:
        st.success('Decision Engine admission: ' + admission['status'])
        st.text('Admission reference: ' + admission['admission_ref'])
        st.text('Validator: ' + admission['validator_version'])
    for finding in p['findings']:
        with st.expander('Finding · ' + finding['status'] + ' · ' + finding['finding_ref']):
            st.text(finding['question'])
            for claim in finding['claims']:
                st.text(claim)
            st.text('Grounded evidence references: ' + ', '.join(finding['evidence_refs']))
            st.text('Admitted: ' + ('Yes' if admission and finding['finding_ref'] in admission['finding_refs'] else 'No'))
    for e in p['grounded_evidence']:
        with st.expander(e['document_id'] + ' · ' + e['section_id'] + ' · ' + e['clause_id']):
            st.text(e['text'])
            st.text('Source: ' + e['source_reference'])
            st.text('Evidence reference: ' + e['evidence_id'])
            st.text('Document version: ' + e['document_version'])
            st.text('Chunk: ' + e['chunk_id'])
            st.text('Text SHA-256: ' + e['text_hash'])
    st.text('Evidence context: ' + p['evidence_context_version'])


def relevance_text(lineage):
    changed = lineage['vector_changed']
    comparison = 'No post-Verification comparison recorded.' if changed is None else 'Model feature vector changed: ' + ('Yes.' if changed else 'No.')
    if lineage['policy_relevant'] is None:
        return comparison + ' No separate Evidence Relevance Assessment recorded. Policy relevance: Not recorded.'
    return comparison + ' Policy relevance: ' + ('Yes.' if lineage['policy_relevant'] else 'No.') + ' Assessment rule: ' + lineage['relevance_rule_version']


def verification(a):
    st.subheader('Verification evidence and feature sources')
    text(relevance_text(a['lineage']))
    st.caption('Resolver policy: ' + a['lineage']['feature_source_policy_version'])
    if not a['verification']:
        st.info('No Verification was required in this recorded execution.')
    for v in a['verification']:
        with st.expander(label(v['tool']) + ' · Attempt ' + str(v['attempt_number']) + ' · ' + v['outcome'], expanded=True):
            st.text('Request reference: ' + v['request_ref'])
            st.text('Attempt reference: ' + v['attempt_ref'])
            if not v['evidence']:
                st.text('No verified value recorded for this attempt.')
            for e in v['evidence']:
                st.text(feature_name(e['field']) + ': ' + value_text(e['field'], e['value']))
                st.text('Evidence reference: ' + e['evidence_ref'])
                st.text('Source: ' + e['source_reference'])
                if e['contradicts']:
                    st.text('Retained conflict references: ' + ', '.join(e['contradicts']))
            if v['retry_policy_version'] is not None:
                st.text('Retry eligibility policy: ' + v['retry_policy_version'])
                st.text('Retry proof reference: ' + v['retry_proof_ref'])
    rows = []
    for f in a['lineage']['selected_features']:
        rows.append({'Feature': feature_name(f['feature']), 'Original reported': value_text(f['feature'], f['original_reported_value']),
                     'Selected': value_text(f['feature'], f['selected_value']), 'Selected source': f['selected_source'],
                     'Source reference': f['source_reference'], 'Rule': f['rule_version'],
                     'Verification references': ', '.join(f['verification_evidence_refs']) or 'None recorded'})
    st.table(rows)
    st.text('Evidence context: ' + a['lineage']['evidence_context_version'])


def journey_steps(a):
    """Create display summaries strictly from ordered, persisted public events."""
    steps, events = [], a['workflow']['events']
    attempts = {v['attempt_ref']: v for v in a['verification']}
    actions = {x['action_ref']: x for x in a['mock_actions']}
    recompute_seen = False

    def add(group, title, state, note, components, *, detail_refs=()):
        steps.append({'title': title, 'state': state, 'note': note,
                      'components': components,
                      'refs': [x['event_ref'] for x in group],
                      'attempt_refs': [x['attempt_ref'] for x in group if x['attempt_ref']],
                      'evidence_refs': [r for x in group for r in x['evidence_refs']],
                      'detail_refs': list(detail_refs)})

    i = 0
    while i < len(events):
        event = events[i]
        kind, stage, route = event['kind'], event['stage'], event['route']
        group = [event]
        if kind == 'TRANSITION' and route == 'RECOMPUTE':
            recompute_seen = True
            i += 1
            while i < len(events) and events[i]['kind'] == 'TRANSITION' and events[i]['route'] == 'RECOMPUTE':
                group.append(events[i]); i += 1
            selected = [f for f in a['lineage']['selected_features'] if f['selected_source'] != 'application']
            selected_text = '; '.join('{} {} · {}'.format(feature_name(f['feature']),
                                  value_text(f['feature'], f['selected_value']), label(f['selected_source']))
                                      for f in selected)
            note = ('Feature vector changed; selected ' + selected_text + '. Downstream recomputation follows.'
                    if selected_text else 'Persisted feature-vector comparison; downstream recomputation follows.')
            add(group, 'Resolver · selected evidence', 'reevaluated',
                note,
                ('Feature Source Resolver · Phase 3', 'Workflow Controller · Phase 8'))
            continue
        if kind == 'TRANSITION' and stage == 'RISK_SHAP':
            title = 'Recompute · Risk / SHAP' if recompute_seen else 'Risk Model'
            note = ('Post-Verification quantitative rerun is recorded; current values are shown in Risk & SHAP.'
                    if recompute_seen else 'Persisted model and SHAP stage. Initial historical model values are unavailable.')
            add(group, title, 'reevaluated' if recompute_seen else 'complete', note,
                ('Risk Model + Calibration · Phase 1A', 'SHAP · Phase 1B'))
        elif kind == 'TRANSITION' and stage == 'POLICY':
            i += 1
            while i < len(events) and events[i]['kind'] == 'TRANSITION' and events[i]['stage'] == 'POLICY':
                group.append(events[i]); i += 1
            title = 'Policy Re-evaluation' if recompute_seen else 'Policy Evaluation'
            add(group, title, 'reevaluated' if recompute_seen else 'complete', 'Grounded policy stage recorded; source passages are available in Policy Evidence.',
                ('Grounded Policy RAG · Phase 4', 'Policy Agent · Phase 5'))
            continue
        elif kind == 'TRANSITION' and route == 'VERIFY':
            if i + 1 < len(events) and events[i + 1]['kind'] == 'RETRY_AUTHORIZED':
                group.append(events[i + 1]); i += 1
                add(group, 'Controller Retry Authorization', 'retry',
                    'Controller-authorized route and one additional attempt are recorded.',
                    ('Workflow Controller / LangGraph · Phase 8', 'Bounded retry policy'))
            else:
                add(group, 'Verification Authorized', 'complete', 'Controller-authorized route recorded.',
                    ('Orchestrator proposal · Phase 7', 'Workflow Controller / LangGraph · Phase 8'))
        elif kind == 'ATTEMPT_COMPLETED':
            attempt = attempts[event['attempt_ref']]
            title = ('Income Verification · Attempt ' + str(attempt['attempt_number'])
                     if attempt['tool'] == 'verify_income' else 'Credit Evidence')
            note = 'Recorded result · ' + label(attempt['outcome'])
            if attempt['evidence']:
                note += ' · separate evidence recorded'
            add(group, title, 'failed' if attempt['outcome'] == 'FAILED' else 'complete', note,
                ('Verification Agent · Phase 6',
                 'Verification request · ' + ('EXECUTE' if attempt['tool'] != 'get_credit_report' else 'READ')),
                detail_refs=(attempt['request_ref'], *[x['evidence_ref'] for x in attempt['evidence']]))
            if attempt['tool'] == 'verify_income' and attempt['evidence']:
                reported = next((x['original_reported_value'] for x in a['lineage']['selected_features']
                                 if x['feature'] == 'monthly_income'), None)
                verified = attempt['evidence'][0]['value']
                add(group, 'Reported vs Verified Income', 'complete',
                    'Reported {} · Verified {}'.format(value_text('monthly_income', reported),
                                                       value_text('monthly_income', verified)),
                    ('Verification evidence · Phase 6',))
        elif kind == 'RETRY_AUTHORIZED':
            add(group, 'Controller Retry Authorization', 'retry', 'One additional income attempt authorized under the persisted retry policy.',
                ('Workflow Controller · Phase 8', 'Bounded retry policy'))
        elif kind == 'RETRY_EXHAUSTED':
            add(group, 'Retry Budget · EXHAUSTED', 'exhausted', 'Controller-recorded limit reached; no third income attempt.',
                ('Workflow Controller · Phase 8',))
        elif kind == 'TRANSITION' and route == 'UNRESOLVED':
            add(group, 'Evidence · UNRESOLVED', 'unresolved', 'Authoritative evidence path remains unresolved.',
                ('Workflow Controller · Phase 8',))
            if not a['decision']['engine_reached']:
                add(group, 'Automated Decision · BLOCKED', 'blocked',
                    'Decision Engine NOT REACHED · no system recommendation or admission recorded.',
                    ('Workflow Controller · Phase 8',))
        elif kind == 'ADMISSION':
            add(group, 'Policy Evidence · ADMITTED', 'complete', 'Persisted validator admission for Decision Engine use.',
                ('Policy Evidence Validator · Phase 8.9',), detail_refs=(a['decision']['admission_ref'],))
        elif kind == 'DECISION':
            rec = RECOMMENDATIONS.get(a['decision']['system_recommendation'], 'No system recommendation')
            add(group, 'Decision Engine', 'complete', rec,
                ('Deterministic Decision Engine · Phase 9',), detail_refs=(a['decision']['decision_ref'],))
        elif kind == 'DISPOSITION':
            disposition = a['human_route']['disposition']
            title = {'NO_PHASE10_ACTION':'Straight-through decision',
                     'HUMAN_CREDIT_REVIEW':'Human Credit Review',
                     'HUMAN_INVESTIGATION':'Human Investigation',
                     'OPERATIONAL_HANDLING':'Operational handling'}[disposition]
            state = ('resolved' if disposition == 'NO_PHASE10_ACTION' else
                     'credit_review' if disposition == 'HUMAN_CREDIT_REVIEW' else 'human')
            note = ('Human Review not required.' if not a['human_route']['review_required'] else
                    'Pending Human Review; no final human outcome is recorded.')
            add(group, title, state, note,
                ('Workflow Controller · Phase 10', 'Human authority' if a['human_route']['review_required'] else 'No human route'))
        elif kind == 'MOCK_ACTION':
            action = actions[event['event_ref']]
            title = {'REVIEW_CASE':'Investigation Case', 'SLACK':'Slack notification', 'EMAIL':'Email notification'}[action['action']]
            add(group, title, 'mock', 'MOCK · RECORDED · Offline mock action — no live message sent.',
                ('Escalation Agent · Phase 10', action['action'] + ' · MOCK effect'),
                detail_refs=(action['action_ref'], action['case_ref'], action['receipt_ref']))
        elif kind == 'REVIEW_ENTRY':
            add(group, 'Pending Human Review', 'human', 'Pending review; no human Final Outcome recorded.',
                ('Authorized human · Human authority',))
        elif kind == 'EXPLANATION':
            add(group, 'Explanation', 'complete', 'Persisted Phase 11 Explanation.',
                ('Explanation Agent · Phase 11',))
        i += 1
    return steps


JOURNEY_COLORS = {
    'complete':('#edf6f0','#6da784','#23664b','✓','COMPLETED'),
    'resolved':('#edf6f0','#6da784','#23664b','✓','COMPLETED'),
    'failed':('#fbefed','#c67870','#a33b35','✕','FAILED'),
    'retry':('#eef4f8','#7ca0b5','#145b7d','↻','RETRY AUTHORIZED'),
    'reevaluated':('#eef4f8','#7ca0b5','#145b7d','↻','REEVALUATED'),
    'exhausted':('#fbf5e8','#c5a354','#80530e','!','EXHAUSTED'),
    'unresolved':('#fbf5e8','#c5a354','#80530e','!','UNRESOLVED'),
    'human':('#fbf5e8','#c5a354','#80530e','!','HUMAN INVESTIGATION REQUIRED'),
    'credit_review':('#fbf5e8','#c5a354','#80530e','!','HUMAN CREDIT REVIEW REQUIRED'),
    'blocked':('#f1f2f3','#77818a','#4d5962','■','BLOCKED'),
    'mock':('#eef4f8','#7ca0b5','#145b7d','↗','MOCK · RECORDED'),
}


def _wrap(value, width):
    return textwrap.wrap(str(value), width=width, break_long_words=True, break_on_hyphens=False) or ['']


def journey_svg(steps, narrow=False):
    """Owner-style responsive two-column serpentine SVG; values are escaped."""
    columns = 1 if narrow else 2
    width, node_w = (700,650) if narrow else (960,430)
    gap_x, gap_y, left, top = (0,28,25,22) if narrow else (60,30,20,22)
    layouts=[]
    for step in steps:
        titles=_wrap(step['title'], 70 if narrow else 43)
        components=[]
        for component in step['components']:
            line=' · '.join(components[-1:]+[component]) if components else component
            if components and len(line)<= (100 if narrow else 60): components[-1]=line
            else: components.append(component)
        notes=_wrap(step['note'],90 if narrow else 57)
        title_y=52; title_end=title_y+18*(len(titles)-1)
        component_y=title_end+20; note_y=component_y+14*max(0,len(components)-1)+20
        height=max(108,note_y+15*max(0,len(notes)-1)+19)
        layouts.append((titles,components,notes,height,title_y,component_y,note_y))
    positions=[]; row_y=top
    for start in range(0,len(steps),columns):
        row=start//columns; row_h=max(x[3] for x in layouts[start:start+columns])
        for slot in range(min(columns,len(steps)-start)):
            col=0 if narrow else (slot if row%2==0 else 1-slot)
            positions.append((left+col*(node_w+gap_x),row_y,row_h,col,row))
        row_y+=row_h+gap_y
    height=row_y-gap_y+top if steps else top*2
    variant='narrow' if narrow else 'wide'
    svg=[f'<svg class="cp-workflow-svg cp-workflow-{variant}" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMin meet" role="img" aria-label="Recorded CreditPilot decision journey with component annotations">',
         f'<defs><marker id="cp-arrow-{variant}" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#718792"/></marker></defs>',
         f'<style>.cp-workflow-{variant} .cp-flow-arrow{{marker-end:url(#cp-arrow-{variant});}}</style>']
    for current,following in zip(positions,positions[1:]):
        x,y,h,col,row=current; nx,ny,_,ncol,nrow=following
        if row==nrow:
            start=x+(node_w if ncol>col else 0); end=nx+(0 if ncol>col else node_w); cy=y+h/2
            svg.append(f'<path class="cp-flow-arrow" d="M{start} {cy} L{end} {cy}"/>')
        else:
            cx=x+node_w/2; ncx=nx+node_w/2; mid=y+h+gap_y/2
            if cx!=ncx: svg.append(f'<path class="cp-branch-line" d="M{cx} {y+h} L{cx} {mid} L{ncx} {mid}"/>')
            svg.append(f'<path class="cp-flow-arrow" d="M{ncx} {mid} L{ncx} {ny}"/>')
    for step,layout,(x,y,h,_,_) in zip(steps,layouts,positions):
        titles,components,notes,_,title_y,component_y,note_y=layout
        fill,stroke,ink,glyph,status=JOURNEY_COLORS[step['state']]
        svg.extend([f'<g class="cp-svg-node" data-state="{safe(step["state"])}">',
                    f'<rect x="{x}" y="{y}" width="{node_w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>',
                    f'<text class="cp-svg-icon" x="{x+18}" y="{y+31}" fill="{ink}">{glyph}</text>',
                    f'<text class="cp-svg-state" x="{x+50}" y="{y+27}" fill="{ink}">{status}</text>'])
        for idx,line in enumerate(titles): svg.append(f'<text class="cp-svg-title" x="{x+20}" y="{y+title_y+idx*18}">{safe(line)}</text>')
        svg.append(f'<text class="cp-svg-component" x="{x+20}" y="{y+component_y-5}">ARCHITECTURE · NOT AN EVENT</text>')
        for idx,line in enumerate(components): svg.append(f'<text class="cp-svg-component" x="{x+20}" y="{y+component_y+idx*14+10}">{safe(line)}</text>')
        for idx,line in enumerate(notes): svg.append(f'<text class="cp-svg-note" x="{x+20}" y="{y+note_y+idx*15}">{safe(line)}</text>')
        svg.append('</g>')
    svg.append('</svg>')
    return ''.join(svg)


def executive_journey(a):
    banner = ('HUMAN INVESTIGATION REQUIRED · AUTOMATED DECISION BLOCKED · DECISION ENGINE NOT REACHED'
              if not a['decision']['engine_reached'] else
              'HUMAN CREDIT REVIEW REQUIRED · A system recommendation is recorded; review remains pending.'
              if a['human_route']['review_required'] else
              'STRAIGHT-THROUGH DECISION · HUMAN REVIEW NOT REQUIRED')
    st.markdown('<div class="cp-semantic-banner{}">{}</div>'.format(
        ' investigation' if not a['decision']['engine_reached'] else '', safe(banner)), unsafe_allow_html=True)
    st.markdown('<div class="cp-section-title">Executive Decision Journey</div><div class="cp-section-note">Persisted business stages and directional execution order. Component annotations describe the frozen architecture; they are not additional execution events.</div>', unsafe_allow_html=True)
    steps=journey_steps(a)
    st.markdown('<div class="cp-journey-frame">{} {}</div>'.format(journey_svg(steps),journey_svg(steps,True)),unsafe_allow_html=True)
    with st.container(key='technical-evidence'):
        st.markdown('<p class="cp-evidence-description">Inspect source references, evidence provenance, and architecture annotations.</p>', unsafe_allow_html=True)
        with st.expander('🔎 Technical Evidence & Execution Details'):
            technical_evidence(steps)


def technical_evidence(steps):
    """Retain complete source details inside the native disclosure."""
    for index,step in enumerate(steps,1):
        st.markdown('**{:02d} · {}**'.format(index,safe(step['title'])))
        st.caption('Architecture · ' + ' · '.join(step['components']))
        st.text('Workflow events: ' + (', '.join(step['refs']) or 'Not recorded'))
        st.text('Verification attempts: ' + (', '.join(step['attempt_refs']) or 'Not recorded'))
        st.text('Evidence references: ' + (', '.join(step['evidence_refs']) or 'Not recorded'))
        st.text('Additional source references: ' + (', '.join(x for x in step['detail_refs'] if x) or 'Not recorded'))


def workflow(a):
    st.subheader('Recorded workflow trajectory')
    st.caption('Business-stage summary linked to persisted events. Sequence is presentation order, not an invented timestamp.')
    st.text('Terminal state: ' + a['workflow']['terminal'])
    st.text('Terminal proof reference: ' + a['workflow']['terminal_proof_ref'])
    st.table([{'Sequence': e['sequence'], 'Kind': e['kind'], 'Component': e['stage'], 'Route': e['route'] or 'Not applicable',
               'Source revision': str(e['source_revision']) if e['source_revision'] is not None else 'Not recorded',
               'Authorized': label(e['authorized']), 'Event reference': e['event_ref'],
               'Attempt reference': e['attempt_ref'] or 'Not applicable', 'Evidence references': ', '.join(e['evidence_refs']) or 'None recorded'}
              for e in a['workflow']['events']])
    st.caption('Notifications have a stable display order; this does not assert a global cross-ledger timestamp order.')


def architecture_asset(key):
    """Read only the two fixed, hash-pinned, reviewed images shipped with this module."""
    filename, expected_hash, _dimensions = ARCHITECTURE_ASSETS[key]
    path = ASSET_DIRECTORY / filename
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 5_000_000:
        raise ValueError('Reviewed architecture asset integrity check failed')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError('Reviewed architecture asset integrity check failed')
    return raw


def runtime_workflow():
    st.subheader('Runtime Workflow')
    st.markdown('#### CreditPilot Runtime Workflow (Phases 1–11)')
    text('This conceptual view connects pre-LangGraph model and policy preparation to Controller-owned LangGraph execution. It shows Orchestrator proposals, approved Verification and the evidence/recomputation loop, followed by Decision Engine or Escalation and Explanation paths over shared CreditState.')
    st.caption('Conceptual/historical roadmap illustration. It labels Logistic/XGBoost and claims accurate phase mapping; the frozen implemented Risk Model is calibrated Logistic Regression, while XGBoost is historical challenger planning. Treat phase details in this image as illustrative, not an authoritative implementation map.')
    st.image(architecture_asset('runtime'), caption='CreditPilot Runtime Workflow · original approved visual asset', use_container_width=True)


def technical_highlights():
    st.subheader('Technical Highlights')
    st.caption('Architecture facts are drawn from the frozen specification. Golden Scenario values and execution details come only from the validated public artifacts.')
    highlights = [
        ('Risk Intelligence', 'Frozen calibrated Logistic Regression produces a dataset-specific two-year delinquency PD proxy. Grouped Top-K SHAP contributions explain the raw score in log-odds units; they are not a decomposition of calibrated PD.'),
        ('Policy Intelligence', 'Synthetic Policy Knowledge Base and grounded retrieval provide source-bound passages. Policy evidence validation checks applicability, support and consistency before Decision Engine admission.'),
        ('Agentic Orchestration', 'The architecture defines five specialized agents: Orchestrator, Policy, Verification, Explanation and Escalation. LangGraph executes transitions authorized by the deterministic Workflow Controller.'),
        ('Deterministic Governance', 'The Feature Source Resolver selects model inputs with versioned lineage. Changed features trigger required downstream recomputation. Verification retries are bounded; deterministic rules own recommendation fields.'),
        ('Human Authority', 'Human Credit Review and Human Investigation remain separate routes. A human Final Outcome is distinct from a system recommendation; pending records are not presented as completed decisions.'),
        ('Security and Evaluation', 'The anonymous explorer reads only a fixed, allowlisted bundle with a caller-pinned manifest digest. Strict validation fails closed. Golden Scenarios use synthetic fixtures, offline adapters and mock action receipts.'),
    ]
    cards([(name, name, description) for name, description in highlights])
    st.caption('No production lending, live provider activity, RAG quality score or new model evaluation is claimed by this portfolio.')


def human_route(a):
    h, d = a['human_route'], a['decision']
    st.subheader('System recommendation and human authority')
    cards([('System recommendation', RECOMMENDATIONS.get(d['system_recommendation'], 'No system recommendation'),
            'Decision Engine reached' if d['engine_reached'] else 'Decision Engine NOT REACHED'),
           ('Recorded human route', ROUTES[h['disposition']], 'Review status: ' + label(h['review_status'])),
           ('Human Final Outcome', 'Not recorded', 'Pending handoff' if h['review_required'] else 'Human Review not required')])
    if d['engine_reached']:
        st.text('Decision rule: ' + d['decision_rule'])
        st.text('Decision reason: ' + d['decision_reason'])
        st.text('Decision reference: ' + d['decision_ref'])
    st.text('Disposition reference: ' + h['route_ref'])
    st.text('Review trigger: ' + label(h['review_trigger']))
    text('A system recommendation and a human Final Outcome are separate records. This explorer displays the recorded handoff only.')
    if not a['mock_actions']:
        st.info('No external-action receipts recorded for this scenario.')
    else:
        st.subheader('Recorded mock action receipts')
        st.warning('Offline mock action — no live message sent.')
        st.table([{'Action': x['action'], 'Status': x['status'], 'Provider': x['provider'], 'Effects': x['effect_count'],
                   'Case reference': x['case_ref'], 'Receipt reference': x['receipt_ref'], 'Action reference': x['action_ref']}
                  for x in a['mock_actions']])


def provenance(a):
    st.subheader('Recorded provenance and limitations')
    p = a['provenance']
    st.table([{'Field': key, 'Recorded value': p[key]} for key in (
        'source_release_tag', 'source_release_commit', 'execution_code_commit', 'exporter_code_commit',
        'exporter_version', 'executed_at_utc', 'generated_at_utc', 'source_execution_id', 'model_artifact_sha256',
        'policy_corpus_sha256', 'decision_policy_sha256', 'source_runtime_sha256', 'source_evidence_sha256', 'execution_environment_sha256')])
    st.caption('Schema: ' + a['schema_version'] + ' · Artifact version: ' + a['artifact_version'])
    st.text('Artifact payload SHA-256: ' + a['integrity']['payload_sha256'])
    with st.expander('Offline adapter profile'):
        st.table([{'Component': key, 'Recorded adapter': value} for key,value in p['adapter_profile'].items()])
    for code in a['limitations']:
        text(LIMITATIONS[code])
