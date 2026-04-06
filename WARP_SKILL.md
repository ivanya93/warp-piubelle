---
name: warp-prototype
description: >
  Builds and iterates on WARP (Workflow-Aware Risk & Procurement Agent), a Streamlit prototype
  for Piubelle's AI supplier management system. Use when the user mentions "build the app",
  "generate data", "run the prototype", "Streamlit", "supplier scoring", "delay detection",
  "task board", "follow-up drafter", "ERP update", "KPI dashboard", "management report",
  or any WARP feature. Also triggers on "iterate on [phase]", "fix the scorer", "test the
  detector", or "deploy to Streamlit Cloud". Covers the full development loop: repo setup,
  synthetic data generation, agent logic, Streamlit pages, Claude API integration, testing,
  and deployment. Do NOT trigger for general Python questions unrelated to WARP.
metadata:
  author: MBA Business Analytics & AI — Group Project
  version: 1.2.0
  category: workflow-automation
  stack: streamlit, python, anthropic-api, pandas, plotly, faker, github
  deadline: "2026-04-08T18:00:00 Europe/Lisbon"
---

# WARP Prototype Skill

## Use Cases

This skill targets three concrete workflows. Before writing any code, confirm which one the session is addressing.

**Use Case 1 — Data Foundation**
Trigger: "Generate the synthetic data" / "Run the data generator" / "Reset the CSVs"
Steps: Run `data/generate_data.py` → verify 6 CSV outputs → spot-check alert distribution
Result: 200 suppliers, 400 POs, 18 months of delivery history, seeded at `random.seed(42)`

**Use Case 2 — Agent Logic**
Trigger: "Fix the scorer" / "Delay detection is wrong" / "Iterate on [phase]"
Steps: Isolate the failing module → reproduce the failure → fix one thing → re-run tests
Result: `scorer.py` and `delay_detector.py` pass all boundary tests in `tests/`

**Use Case 3 — Streamlit App**
Trigger: "Build the dashboard" / "The task board isn't routing correctly" / "Deploy to Streamlit Cloud"
Steps: Implement or fix the relevant page → verify HITL gate → run end-to-end demo checklist
Result: All 6 pages functional, HITL gates enforced, app live on Streamlit Community Cloud

---

## Success Criteria

**Quantitative targets**
- Skill triggers on 90%+ of WARP-related queries (see triggering tests below)
- `pytest tests/ -v` passes 100% — 0 failures on boundary conditions
- Claude API draft returns in < 10s on Streamlit Community Cloud
- Dashboard KPI values match `pytest`-verified module outputs exactly
- 0 unconfirmed write actions (email send, ERP update, report dispatch) in any demo run

**Qualitative targets**
- A new team member can run the app end-to-end from `README.md` alone — no verbal guidance needed
- The HITL gate is visible and cannot be bypassed on any page — no hidden auto-send path
- Tone switch (Routine / Urgent / Escalation) produces noticeably different Claude output
- Demo checklist (Section 8) completes in 8–10 minutes without errors or restarts

---

## Triggering Tests

Run these manually after each description update to verify skill precision.

**Should trigger:**
- "Build the WARP Streamlit app"
- "Generate synthetic supplier data for Piubelle"
- "The delay detector is classifying a PO due today as on_track"
- "Iterate on the supplier scoring engine"
- "Fix the ERP update gate — it's skipping the preview step"
- "Deploy WARP to Streamlit Cloud"
- "The follow-up drafter returns the same output for all tone levels"
- "Run the demo checklist before the pitch"

**Should NOT trigger:**
- "How do I write a for loop in Python?" (generic Python)
- "What is Streamlit?" (general concept question)
- "Help me build a different procurement app" (different project)
- "Fix my pandas merge" (no WARP context)

Debugging: Ask Claude "When would you use the warp-prototype skill?" — it will quote the description back. Add missing trigger phrases based on what it misses.

---

## Pattern Classification

WARP applies two patterns from the Anthropic Skills Guide:

**Pattern 2 — Sequential Workflow Orchestration**
Each capability is a discrete step with a validation gate before the next phase is unlocked. Steps have explicit data dependencies: the scorer requires delivery events; the detector requires scores; the task board requires both.

**Pattern 5 — Domain-Specific Intelligence**
Claude API calls embed procurement domain knowledge — OTIF risk, cascade delay logic, GDPR-scoped supplier search, tone calibration for supplier relationships. Prompts must reference PO numbers, supplier scores, delay days, and destination countries. Generic prompts will produce generic output.

---

## Build Order & Phase Gates

Complete phases in sequence. Do not start Phase N+1 until Phase N passes its gate.

| Phase | Module | Gate — definition of done |
|-------|--------|---------------------------|
| 1 | `data/generate_data.py` | 6 CSVs generated cleanly. ≥ 5 Red alerts, ≥ 10 Amber, score range 1.0–10.0 |
| 2 | `agent/scorer.py` | All scores in [1.0, 10.0]. Problematic suppliers average < 5.0. < 5 events returns `NaN` |
| 3 | `agent/delay_detector.py` | All boundary tests pass — see `tests/test_delay_detector.py` |
| 4 | `pages/1_Dashboard.py` | KPI cards correct, Plotly scatter renders, buyer filter applies cleanly |
| 5 | `pages/2_Task_Board.py` | Sorts Red → Amber → Proactive. "Draft follow-up" routes with PO pre-filled |
| 6 | `pages/4_Follow_Up.py` | Draft < 10s. Tone switch distinct. Approve gate logs action |
| 7 | `pages/5_ERP_Update.py` | Prepare → preview → confirm flow complete. Cancel leaves status "Pending" |
| 8 | `pages/6_Management_Report.py` | KPI values match dashboard. Approve gate enforced before generation |

---

## Step-by-Step Instructions

### Step 1: Environment and Repo Setup

```bash
git clone https://github.com/<your-org>/warp-piubelle.git && cd warp-piubelle
python -m venv .venv && source .venv/bin/activate
pip install streamlit pandas numpy faker anthropic plotly python-dateutil openpyxl pytest
pip freeze > requirements.txt
```

Create `.streamlit/secrets.toml` (never committed):
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1D9E75"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F0"
textColor = "#1A1A1A"
font = "sans serif"
```

Expected output: `streamlit run Home.py` opens at `http://localhost:8501` with buyer sign-in.

---

### Step 2: Synthetic Data Generation

```bash
python data/generate_data.py
```

Expected terminal output:
```
Generating Piubelle synthetic data...
Done. Files in data/synthetic/
  Suppliers: 200 | POs: 400 | Events: ~4800
  Email threads: ~120 | Penalties: ~25 | Air freight: ~15
```

Spot-check before proceeding to Phase 2:
```python
import pandas as pd
pos = pd.read_csv("data/synthetic/purchase_orders.csv")
print(pos["status"].value_counts())
# Must show: red >= 5, amber >= 10, on_track is the majority
```

Full generator implementation: `references/data_generator.md`

---

### Step 3: Supplier Scoring Engine

Full implementation: `references/scorer.md`

Rules Claude must follow when writing or fixing `agent/scorer.py`:
- Normalize every dimension to [0, 1] before applying weights — never weight raw values
- Final scale: `(weighted_sum * 9 + 1).round(1)` — always maps to [1.0, 10.0]
- Trend arrow: `↑` if last-90-day on-time rate improved > 5pp vs prior 90d, `↓` if fell > 5pp, `→` otherwise
- Suppliers with < 5 delivery events: return `NaN`, exclude from ranking, display `N/A` in UI

Weight table:

| Dimension | Weight |
|-----------|--------|
| On-time delivery rate (12 months) | 35% |
| Average delay duration when late (days) | 20% |
| Penalty history (count) | 15% |
| Last-minute notification rate (< 5 days before) | 15% |
| Avg email reply time (hours) | 10% |
| Trend delta (last 90d vs prior 90d on-time rate) | 5% |

---

### Step 4: Delay Detection Engine

Full implementation: `references/delay_detector.md`

Alert classification rules:

| Condition | Alert Level |
|-----------|-------------|
| `days_to_delivery < 0` and no goods receipt logged | `red` |
| `0 <= days_to_delivery <= 10` and delivery unconfirmed | `amber` |
| `warp_score <= 3.5` and `days_to_delivery <= 20` | `proactive` |
| Delay keyword in supplier email thread | Upgrades `ok` → `amber`; does not downgrade existing `red` |
| Trend arrow `↓` on amber or proactive PO | Appends reason string; alert level unchanged |
| All other cases | `ok` |

CRITICAL: Cast date columns before comparing with `date.today()`:
```python
pos_df["expected_delivery"] = pd.to_datetime(pos_df["expected_delivery"]).dt.date
days_to_delivery = (po["expected_delivery"] - date.today()).days
```
Mixed types cause silent wrong classifications. This is the most common Phase 3 failure.

---

### Step 5: Streamlit Pages

Full implementations: `references/pages.md`

HITL gate pattern — apply identically on Follow-Up (p.4), ERP Update (p.5), and Report (p.6):

```python
# Step 1 — Generate / prepare (no write action yet)
if st.button("Generate Draft"):
    st.session_state["draft"] = call_claude_api(po_details, tone)

# Step 2 — Display for review (always editable)
if "draft" in st.session_state:
    edited = st.text_area("Review and edit:", value=st.session_state["draft"], height=300)

    # Step 3 — Explicit confirmation required before any action
    col1, col2 = st.columns(2)
    if col1.button("Approve and Send", type="primary"):
        log_action(edited, buyer=st.session_state["buyer"])
        st.success("Logged. Send this from Outlook.")
        del st.session_state["draft"]
    if col2.button("Discard"):
        del st.session_state["draft"]
```

Never use `type="primary"` on a discard button. Visual hierarchy enforces the gate.

Session state initialization — always in `Home.py` before any page reads it:
```python
defaults = {"buyer": None, "tasks": [], "draft": None, "erp_preview": False}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val
```

---

### Step 6: Claude API Integration

Model: `claude-sonnet-4-6` | Max tokens: 600 (drafts), 800 (reports)

Tone anchors — always embed in follow-up prompts to prevent tone collapse:
```
Routine: polite, no urgency language, 5-day response window
Urgent: firm, references OTIF penalty risk explicitly, 48-hour response window
Escalation: direct, references senior contact escalation, 24-hour window, CC line suggested
```

Report input — always pass structured dict, never a pre-formatted string:
```python
kpis = {
    "red_alerts": int,
    "amber_alerts": int,
    "otif_rate_pct": float,
    "penalties_eur": float,
    "airfreight_eur": float,
    "cost_at_risk_eur": float,
    "top_3_problem_suppliers": list[dict],
    "week_ending": str,
}
```

Wrap every API call — never crash the page on API failure:
```python
try:
    msg = client.messages.create(model="claude-sonnet-4-6", max_tokens=600, messages=[...])
    return msg.content[0].text
except anthropic.APIError as e:
    st.error(f"Claude API unavailable. Use pre-written mock draft for demo. ({e})")
    return None
```

Full prompt templates: `references/claude_prompts.md`

---

### Step 7: Tests

```bash
pytest tests/ -v
```

Required boundary cases for `tests/test_delay_detector.py`:

| Input condition | Expected `alert_level` |
|-----------------|------------------------|
| `expected_delivery = today - 1 day` | `red` |
| `expected_delivery = today` | `amber` |
| `expected_delivery = today + 10 days` | `amber` |
| `expected_delivery = today + 11 days`, score > 3.5 | `ok` |
| `expected_delivery = today + 15 days`, score = 3.0 | `proactive` |
| Any level + delay email signal | level is `amber` or higher |

Full test suite: `references/tests.md`

---

### Step 8: Deploy to Streamlit Community Cloud

1. Push repo to GitHub — include `data/synthetic/*.csv` (synthetic data, no GDPR risk)
2. Go to `share.streamlit.io` → New app → select repo → Main file: `Home.py`
3. Add `ANTHROPIC_API_KEY` in Streamlit Cloud secrets UI (Advanced settings tab)
4. Click Deploy — live URL in ~60 seconds

---

## Iterate on Specific Tasks

> "Start by mastering a single workflow. Use `warp-prototype` skill to iterate on a tough task until it succeeds, then expand coverage."
> — Anthropic Complete Guide to Building Skills for Claude

**The core method:** isolate one failing task, fix it completely, verify the gate, then move on. Never fix two things simultaneously — parallel fixes make it impossible to attribute which change worked.

Invoke the skill explicitly when stuck:
```
"Use warp-prototype skill — I'm on Phase 3 (delay detection).
 A PO with expected_delivery = today returns 'on_track' instead of 'amber'.
 Iterate on delay_detector.py until the boundary condition is correct."
```

Iteration loop:
```
Run → Observe the specific failure → Fix one thing → Re-run pytest → Gate passes → Next phase
```

Known hard spots — read before starting the relevant phase:

**Phase 3 — Date type mismatch.**
pandas `datetime64` vs Python `date` silently produces wrong comparisons. Always cast with `.dt.date`. Use `date.today()` not `datetime.now().date()` — they can differ at midnight boundaries.

**Phase 6 — Tone collapse.**
If Routine and Escalation produce similar drafts, the prompt lacks behavioural anchors. Add the explicit tone definitions from Step 6. Structured dict input also helps — Claude reasons more reliably from typed fields than formatted strings.

**Phase 7 — Session state evaporation.**
Streamlit reruns the entire script on every widget click. Any local variable set in a button callback is gone by the next render. Store all HITL state in `st.session_state` explicitly, initialized in `Home.py`.

---

## Regression Checklist

Run end-to-end before the pitch without resetting session state between steps:

- [ ] Sign in as each of the 4 buyers — alerts filter to their material category only
- [ ] Open a Red alert → generate follow-up draft → approve → task shows "Follow-up logged"
- [ ] Open an Amber alert → prepare ERP update → click cancel → status remains "Pending"
- [ ] Generate management report → KPI numbers match dashboard values exactly
- [ ] Switch tone Routine → Urgent → Escalation → output is visibly different each time
- [ ] Reload app (browser refresh) → no crash from uninitialised session state
- [ ] `pytest tests/ -v` → 0 failures

---

## Troubleshooting

**Skill does not trigger automatically**
Revise the `description` field. Ask Claude: "When would you use the warp-prototype skill?" — it quotes the description back. Add the missing trigger phrase. See Triggering Tests section above.

**pytest fails on date boundary (Phase 3)**
Confirm `.dt.date` cast is applied before any comparison. Confirm `date.today()` is used consistently, not `datetime.now()`.

**Scores all cluster around 5.0 (Phase 2)**
Normalization step is missing. Each dimension must be independently scaled to [0, 1] before weighting. Without this, high-range raw values (e.g. reply_hours 1–120) dominate the weighted sum.

**Claude draft identical across tone levels (Phase 6)**
Add explicit tone anchors to the system prompt (see Step 6). Switch from formatted string to structured dict for KPI input.

**ERP gate skips preview (Phase 7)**
The prepare step is not setting `st.session_state["erp_preview"] = True`. Ensure the confirm button renders inside an `if st.session_state["erp_preview"]:` block, not unconditionally.

**Page crashes on load after browser refresh**
A page reads `st.session_state` before `Home.py` has run. Add `if "key" not in st.session_state: st.session_state["key"] = default` guard at the top of every page file.

**Dashboard and report show different KPI values**
Both must call the same `utils/data_loader.py` functions decorated with `@st.cache_data`. Direct `pd.read_csv()` calls in page files bypass the cache and can see stale or different data.

---

## References Index

Read the relevant file when implementing or debugging each phase. Do not inline long code into this file — keep SKILL.md under 5,000 words per Anthropic guidelines.

| File | Contents | Read for phase |
|------|----------|----------------|
| `references/data_generator.md` | Full `generate_data.py` — all 6 synthetic generators | Phase 1 |
| `references/scorer.md` | Full `scorer.py` — normalization, weighting, trend delta | Phase 2 |
| `references/delay_detector.md` | Full `delay_detector.py` — all alert rules and email signal logic | Phase 3 |
| `references/pages.md` | All 6 Streamlit page implementations | Phases 4–8 |
| `references/claude_prompts.md` | All Claude API prompt templates with tone anchors | Phase 6 |
| `references/tests.md` | Full pytest test suite — all boundary cases | All phases |

---

*WARP Prototype SKILL.md · v1.2.0*
*Aligned with: Anthropic Complete Guide to Building Skills for Claude (Jan 2026)*
*Piubelle Agentic Business Case · MBA AI & Analytics · Deadline: April 8, 2026*
