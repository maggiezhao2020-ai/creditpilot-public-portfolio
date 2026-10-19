"""Anonymous recorded explorer. Run with streamlit run; no owner capabilities."""
from pathlib import Path

import streamlit as st

from creditpilot.public_portfolio.contracts import ArtifactError, SCENARIOS
from creditpilot.public_portfolio.loader import load_bundle
from creditpilot.public_portfolio import components as view

# Reviewed independently of the bundle. Neither paths nor pin come from visitors,
# environment, query parameters, session data or the manifest being checked.
MANIFEST_PIN = 'aefd27fac4321c7d56e0466eba63233f0aa1fda9ca3fd893992beca31c50086e'
BUNDLE_DIRECTORY = Path(__file__).resolve().parents[3] / 'public_artifacts' / 'v1'
TABS = ('Overview', 'Risk & SHAP', 'Policy Evidence', 'Verification & Lineage',
        'Workflow', 'Human Route', 'Provenance')
SECTIONS = ('Project Overview', 'Golden Scenario Explorer', 'Runtime Workflow', 'Technical Highlights')
SCENARIO_LABELS = {
    'CP-001': 'CP-001 — Low-Risk Straight-Through',
    'CP-002': 'CP-002 — Verification + Review',
    'CP-003': 'CP-003 — Verification Failure + Escalation',
}


def _select_section(section):
    """Keep navigation in this visitor's Streamlit session only."""
    if section in SECTIONS:
        st.session_state['portfolio_section'] = section


def _select_scenario(scenario_id):
    """Select only a fixed scenario ID from the validated public bundle."""
    if scenario_id in SCENARIO_LABELS:
        st.session_state['public_scenario'] = scenario_id


def _render_sidebar(bundle):
    """Show the same verified, read-only identity panel on every page."""
    version = bundle['CP-001']['artifact_version']
    with st.sidebar:
        st.markdown('<div class="cp-sidebar-brand">CREDITPILOT</div>'
                    '<div class="cp-sidebar-kicker">PUBLIC PORTFOLIO</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="cp-sidebar-copy">Read-only Explorer</div>', unsafe_allow_html=True)
        st.markdown('<div class="cp-sidebar-status">Bundle Verified · v{}</div>'.format(view.safe(version)),
                    unsafe_allow_html=True)
        st.caption('Synthetic Scenarios · Offline Adapters · Mock Actions')
        st.caption('No real lending decisions · No live notifications')


def main():
    st.set_page_config(page_title='CreditPilot | Golden Scenario Explorer', page_icon='◈',
                       layout='wide', initial_sidebar_state='expanded')
    view.style()
    view.introduction()
    try:
        # Deliberately uncached: every rerun validates every file before exposure.
        bundle = load_bundle(BUNDLE_DIRECTORY, expected_manifest_sha256=MANIFEST_PIN)
    except ArtifactError:
        st.error('Recorded scenarios unavailable. Bundle validation did not pass.')
        st.stop()
        return
    _render_sidebar(bundle)
    if st.session_state.get('portfolio_section') not in SECTIONS:
        st.session_state['portfolio_section'] = SECTIONS[0]
    section = st.session_state['portfolio_section']
    with st.container(key='primary-navigation'):
        columns = st.columns(4, gap='small')
        for column, label in zip(columns, SECTIONS):
            with column:
                st.button(label, key='nav_' + label.lower().replace(' ', '_'),
                          type='primary' if section == label else 'secondary',
                          use_container_width=True, on_click=_select_section, args=(label,))
    if section == 'Project Overview':
        try:
            view.project_overview()
        except (OSError, ValueError):
            st.error('Architecture diagrams unavailable. Asset validation did not pass.')
    elif section == 'Runtime Workflow':
        try:
            view.runtime_workflow()
        except (OSError, ValueError):
            st.error('Architecture diagrams unavailable. Asset validation did not pass.')
    elif section == 'Technical Highlights':
        view.technical_highlights()
    else:
        if st.session_state.get('public_scenario') not in SCENARIOS:
            st.session_state['public_scenario'] = 'CP-002'
        sid = st.session_state['public_scenario']
        st.subheader('Explore a Golden Scenario')
        st.caption('Select one of three recorded synthetic execution scenarios.')
        with st.container(key='scenario-selector'):
            columns = st.columns(3, gap='small')
            for column, scenario_id in zip(columns, SCENARIO_LABELS):
                with column:
                    st.button(SCENARIO_LABELS[scenario_id], key='scenario_' + scenario_id.lower(),
                              type='primary' if sid == scenario_id else 'secondary',
                              use_container_width=True, on_click=_select_scenario, args=(scenario_id,))
        scenario = bundle[sid]
        view.scenario_header(scenario)
        view.executive_journey(scenario)
        renderers = (view.overview, view.risk, view.policy, view.verification,
                     view.workflow, view.human_route, view.provenance)
        for tab, render in zip(st.tabs(TABS), renderers):
            with tab:
                render(scenario)
    st.divider()
    view.disclosures()


if __name__ == '__main__':
    main()
