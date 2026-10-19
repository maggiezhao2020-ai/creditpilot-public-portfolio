# CreditPilot Public Portfolio

CreditPilot is an AI engineering project for synthetic credit-risk decision support. The underlying system combines a calibrated Logistic Regression risk model and grouped SHAP attribution, policy-grounded retrieval, five specialized agents, deterministic workflow and evidence controls, and separate human final-outcome authority. Its policies and thresholds are demonstrations, not real bank policy.

This public app is an **anonymous, read-only explorer of three precomputed synthetic offline executions**. It loads a fixed, integrity-checked JSON bundle. It does not run the model, agents, retrieval, verification, workflow, Owner Demo API, or external actions. Mock review-case, Slack and email receipts are records of offline effects; no live message is sent. It makes no real lending or adverse-action decision.

## Explore

- **Project Overview:** engineering summary and a scalable rendering of the approved System Architecture. The retained original reference image includes a historical Owner Demo live-notification badge; that badge does not describe this public viewer.
- **Golden Scenario Explorer:** CP-001, low-risk approval recommendation; CP-002, verified-income correction and review recommendation; CP-003, bounded failed verification, blocked automated decision and pending Human Investigation. CP-003 has no Decision Engine recommendation or final human outcome.
- **Runtime Workflow:** the approved conceptual Phases 1–11 illustration, with its historical model/phase-label limitations disclosed in the app.
- **Technical Highlights:** risk, policy evidence, orchestration, deterministic governance, PII boundaries and evaluation limitations.

Each scenario has seven evidence views. Calibrated PD is a dataset-specific two-year serious-delinquency portfolio proxy; grouped Top-K SHAP values explain the raw model score in log-odds units and are only partial attribution. Initial historical snapshots and some evaluation metrics were not persisted and are not reconstructed here.

## Run locally

Use **Python 3.12** and install the single declared direct dependency from `requirements.txt`. From this repository's root:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run src/app.py
```

The app validates the complete four-file bundle on every rerun using an independently pinned manifest payload digest. Missing, modified, extra or unsupported files fail closed. No credentials, environment variables, model files, database, private repository, network provider or artifact-generation step is needed. The application reads only its packaged JSON artifacts and two fixed, hash-checked images.

To run the package's local checks after installing the dependency:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

For a future Streamlit Community Cloud deployment, select Python 3.12, this repository, and entry point `src/app.py`. The root `requirements.txt` and `.streamlit/config.toml` are intended for that platform. No cloud deployment or browser acceptance is claimed by this package.

## Public-data and governance boundary

All applicants, policies, thresholds, verification evidence and actions are synthetic or offline demonstrations. **Synthetic Portfolio Policy — Not Real Bank Policy. Synthetic demonstration threshold — not real bank policy.** Public artifacts are an allowlisted projection of recorded executions; they do not contain raw Kaggle rows, raw identity, credentials, private source maps or mutable workflow commands. The full CreditPilot architecture shown in the diagrams is broader than the functionality of this public viewer.

## Copyright & Usage

Copyright © 2026 maggiezhao2020-ai. All rights reserved.

This proposed repository is intended for public access for professional portfolio presentation, technical evaluation, recruitment review, and demonstration purposes. The owner's original CreditPilot code, documentation, diagrams, presentation, schemas, and synthetic scenario artifacts are **All Rights Reserved**. They are **not released under an open-source license**.

Public access does not grant permission to reproduce, modify, redistribute, sublicense, commercially exploit, or incorporate these original materials into another product. Any such use requires separate written authorization from the copyright holder.

Third-party dependencies and any separately owned assets retain their own licensing terms. Those terms do not grant rights to the owner's original CreditPilot materials. This notice does not change the app's synthetic, read-only, offline, no-real-lending-decision, and no-live-notification boundaries.

The production dependency inventory and reviewed upstream notices are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
