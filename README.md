# WARP — Workflow-Aware Risk & Procurement Agent

**A Streamlit-based AI agent for Piubelle's supplier management and delay detection.**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.43+-green)
![Claude API](https://img.shields.io/badge/Claude%20API-Anthropic-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)

---

## 📋 Overview

WARP (Workflow-Aware Risk & Procurement Agent) transforms Piubelle's procurement from reactive to proactive by:

- 🔍 **Detecting supplier delays** before they cascade into production stoppages
- 📊 **Scoring supplier risk** using 6 weighted dimensions (on-time rate, penalty history, responsiveness, etc.)
- ✉️ **Drafting follow-up emails** with Claude AI (multiple tone levels)
- 📅 **Updating delivery dates** in ERP with audit trails
- 📈 **Generating management reports** with KPI summaries
- 🚪 **Enforcing human-in-the-loop (HITL)** gates on all critical actions

**Status:** ✅ Working prototype (Phases 1-8 complete)  
**Deadline:** April 8, 2026  
**Team:** Master Business Analytics & AI Group Project - Porto Business School, Portugal:
1. **Ivana Ruiz**
2. **Marisa Fernandes**
3. **Olena Kovalchuk**
4. **Francisco Lé**
5. **Pedro Pinto**

---
# 🔗 Live Demo

**Launch the App** → https://warp-piubelle-aqv6uttvueu6fgrxcbg2vi.streamlit.app/

Ask the agent anything about supplier management:

* **"Which suppliers have Red alerts today?"** — Real-time delay detection
* **"Generate a follow-up email for Supplier X"** — AI drafts professional follow-ups (3 tone levels)
* **"Update the ERP date for PO12045"** — Preview & confirm delivery date changes
* **"Show the supplier risk scores"** — View WARP scores (1–10) with trend analysis
* **"Generate this week's management report"** — Executive summary of delays & financial impact
* **"What's our OTIF rate this month?"** — Live KPI dashboard with trending
* **"Which suppliers are deteriorating?"** — Identify suppliers with ↓ trend (declining performance)
* **"Show me all Amber alerts"** — Alerts within 10 days of delivery requiring follow-up

---

## Quick Start

1. **Sign in** as one of 4 buyers (Ana Silva, João Santos, Maria Costa, Pedro Oliveira)
2. **View Dashboard** → See real-time KPIs and alert distribution
3. **Click a Red Alert** → Review supplier details and WARP risk score
4. **Generate Draft** → AI creates a follow-up email (select tone: Routine / Urgent / Escalation)
5. **Approve & Send** → Confirm action; it's logged to the task board
6. **View Weekly Report** → Aggregated metrics ready for leadership

---

## Features Demonstrated

| Feature | What It Does |
|---------|-------------|
| **Order Monitoring** | Real-time PO status vs. delivery dates |
| **Delay Detection** | Alerts: 🔴 Red (overdue), 🟡 Amber (within 10d), 🟠 Proactive (at-risk), 🟢 OK |
| **Risk Scoring** | Supplier score (1–10) based on 6 dimensions + trend arrow |
| **Task Board** | Prioritized tasks by alert level, assigned to buyers |
| **Follow-up Drafting** | Claude AI generates emails in 3 tones (Routine/Urgent/Escalation) |
| **ERP Updates** | Prepare, preview, confirm new delivery dates (HITL gate) |
| **KPI Dashboard** | Live metrics: OTIF rate, penalties, air freight, cost-at-risk |
| **Management Reports** | Weekly executive summary (prose, no jargon) |

---

## How It Works (Human-in-the-Loop)

---
## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/<your-org>/warp-piubelle.git
cd warp-piubelle
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (Mac/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Secrets

Create `.streamlit/secrets.toml` (never commit this):

```toml
ANTHROPIC_API_KEY = "sk-ant-..." # Get from https://console.anthropic.com
```

### 4. Generate Synthetic Data

```bash
python3 data/generate_data.py
```

This creates 6 CSV files in `data/synthetic/`:

- `suppliers.csv` — 200 suppliers
- `purchase_orders.csv` — 400 open POs
- `delivery_events.csv` — 18 months of history
- `email_threads.csv` — supplier communications
- `penalties.csv` — OTIF penalties
- `airfreight_incidents.csv` — air freight cost incidents

### 5. Run Locally

```bash
streamlit run Home.py
```

Opens at `http://localhost:8501`

---

## 📁 Project Structure

```text
warp-piubelle/
├── data/
│   ├── generate_data.py              # Synthetic data generator
│   └── synthetic/                    # CSV outputs (git-ignored in prod)
│       ├── suppliers.csv
│       ├── purchase_orders.csv
│       ├── delivery_events.csv
│       ├── email_threads.csv
│       ├── penalties.csv
│       └── airfreight_incidents.csv
│
├── agent/                            # Core AI logic
│   ├── __init__.py
│   ├── delay_detector.py             # Phase 3: Alert classification (Red/Amber/OK)
│   ├── scorer.py                     # Phase 2: Supplier risk scoring (1–10)
│   ├── recommender.py                # Action recommendations
│   └── claude_agent.py               # Claude API integration
│
├── pages/                            # Streamlit multi-page app
│   ├── 1_Dashboard.py                # Phase 4: KPI overview + charts
│   ├── 2_Task_Board.py               # Phase 5: Alert list + action buttons
│   ├── 4_Follow_Up.py                # Phase 6: Draft emails (Claude AI)
│   ├── 5_ERP_Update.py               # Phase 7: Update delivery dates (HITL)
│   └── 6_Management_Report.py        # Phase 8: Weekly KPI report (Claude AI)
│
├── utils/                            # Helper utilities
│   ├── __init__.py
│   ├── data_loader.py                # Cached data loading (@st.cache_data)
│   ├── state.py                      # Session state management
│   └── formatters.py                 # Currency, date, score formatting
│
├── tests/                            # Pytest test suite
│   ├── __init__.py
│   ├── test_delay_detector.py        # Boundary condition tests
│   └── test_scorer.py                # Score validation tests
│
├── Home.py                           # App entry point (buyer sign-in)
├── requirements.txt                  # Dependencies
├── .streamlit/
│   ├── config.toml                   # Theme + UI config
│   └── secrets.toml                  # ANTHROPIC_API_KEY (git-ignored)
│
├── .gitignore
├── .env.example
├── README.md                         # This file
└── WARP_SKILL.md                     # Technical specification
```
---

## 🧪 Running Tests

All tests pass (15/15):

```bash
pytest tests/ -v
```

**Test Coverage:**

- `test_delay_detector.py` — Boundary conditions for alert classification
- `test_scorer.py` — Score range validation, problematic supplier identification

---

## 🌐 Deploy to Streamlit Community Cloud

### Step 1: Push to GitHub

```bash
git add .
git commit -m "feat: WARP Phase 8 complete — all 6 pages + tests + docs"
git push origin main
```

### Step 2: Create Streamlit App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your `warp-piubelle` repository
4. **Main file path:** `Home.py`
5. Click **"Deploy"** — live in ~60 seconds

### Step 3: Add Secret

1. In Streamlit Cloud, click **"Settings"** (gear icon)
2. Click **"Secrets"**
3. Paste: ANTHROPIC_API_KEY = "sk-ant-..."

4. Save — app restarts automatically

**Live URL:** `https://share.streamlit.io/[username]/warp-piubelle/main/Home.py`

---

## 🎯 Key Features

### Phase 1: Synthetic Data ✅

- 200 suppliers, 400 POs, 18 months history
- Seeded with `random.seed(42)` for reproducibility

### Phase 2: Supplier Scoring ✅

- **6 weighted dimensions:**
  - On-time delivery rate (35%)
  - Avg delay duration (20%)
  - Penalty history (15%)
  - Last-minute notification rate (15%)
  - Email responsiveness (10%)
  - Trend delta (5%)
- **Score range:** 1.0 (critical) → 10.0 (excellent)
- **Insufficient data:** Returns NaN for < 5 events

### Phase 3: Delay Detection ✅

- **Alert levels:**
  - 🔴 **RED:** PO overdue (days_to_delivery < 0)
  - 🟡 **AMBER:** Imminent (0-10 days) or delay signal
  - 🟠 **PROACTIVE:** High-risk supplier (score ≤ 3.5, 0-20 days)
  - 🟢 **OK:** On track (> 10 days, no signals)
- **Email signal detection:** Keywords like "delay", "atraso", "problema"

### Phase 4: Dashboard ✅

- KPI cards (Red/Amber/Proactive/OK counts)
- OTIF rate, supplier scores, financial metrics
- Interactive Plotly charts (scatter, pie)
- Filter by team member category

### Phase 5: Task Board ✅

- Alerts sorted by severity (Red → Amber → Proactive → OK)
- RED alerts expanded by default
- Action buttons: Draft Follow-up, Update ERP, View Details
- Category-based filtering for each team member

### Phase 6: Follow-Up Page ✅

- Claude AI drafts emails with 3 tone levels:
  - **Routine:** Polite, 5-day window
  - **Urgent:** Firm, OTIF reference, 48-hour window
  - **Escalation:** Direct, senior escalation, 24-hour window
- Edit before sending (HITL gate)
- Logs approved follow-ups

### Phase 7: ERP Update ✅

- Collect new delivery date from supplier
- Preview change (old → new)
- Document source + notes
- Confirm with HITL gate before updating
- Full audit trail (who, when, source)

### Phase 8: Management Report ✅

- Claude AI generates executive summary
- KPIs: Red/Amber/Proactive counts, OTIF rate, cost-at-risk
- Top problem suppliers identified
- Professional tone, suitable for C-level
- Review + HITL approval before "sending"

---

## 🔐 Security & Compliance

✅ **GDPR:** No personal data collected. Corporate supplier data only.  
✅ **EU AI Act:** HITL enforcement on all critical actions. Transparent logging.  
✅ **Audit Trail:** Every action logged with timestamp, user, source, approval.  
✅ **Secrets Management:** `.env` and `secrets.toml` never committed.  
✅ **Production Readiness:** Real ERP/email APIs can be swapped for synthetic data.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit 1.43.0 |
| **Backend** | Python 3.10+ |
| **AI Model** | Claude (Anthropic API) |
| **Data** | pandas 2.2.0, numpy 1.26.0 |
| **Synthetic Data** | faker 24.0.0 |
| **Charts** | plotly 5.20.0 |
| **Testing** | pytest |
| **Deployment** | Streamlit Community Cloud |

---

## 📊 Demo Checklist

Run this before pitching to verify everything works:

- [ ] Sign in as each team member (Ana Silva, João Santos, Maria Costa, Pedro Oliveira)
- [ ] Dashboard loads KPI cards correctly
- [ ] Task Board shows Red/Amber/Proactive alerts
- [ ] Click "Draft Follow-up" → Follow-up page loads pre-filled PO
- [ ] Generate email draft → Switch tones (Routine/Urgent/Escalation)
- [ ] Approve follow-up → Logged in session state
- [ ] Click "Update ERP Date" → ERP Update page loads
- [ ] Enter new date → Preview shows change
- [ ] Confirm ERP update → Success message + balloons
- [ ] Return to Task Board → See green "✅ ERP Update Confirmed" box
- [ ] Generate Management Report → Claude generates executive summary
- [ ] Send report → Logged with metadata
- [ ] Run tests: `pytest tests/ -v` → 15/15 pass
- [ ] No crashes on browser refresh

---

## 🚨 Known Limitations

- ❌ WhatsApp integration: Buyers must manually relay WhatsApp updates
- ❌ Live Sage ERP: Uses synthetic data; production would call Sage API
- ❌ Live Outlook: Email sends are simulated; production would use SMTP
- ❌ Real database: Uses flat CSV files; scale to SQL in production
- ⚠️ Session state resets on browser refresh (Streamlit constraint)
- ⚠️ Claude API latency: 3-8 seconds for draft generation

---

## 📚 References

- **WARP_SKILL.md** — Technical specification (phases, gates, troubleshooting)
- **WARP_PROJECT_CLAUDE.md** — Project overview, context, architecture decisions
- **WARP_system_prompt.md** — WARP agent system prompt (identity, capabilities, compliance)

---

## 🤝 Procurement Team

- **Ana Silva** — Raw Materials, Weaving
- **João Santos** — Cutting, Sewing
- **Maria Costa** — Finishing
- **Pedro Oliveira** — Raw Materials, Finishing

---

## 📝 License

Proprietary — Team Members
Master in Business Analytics & AI — Group Project
Gen AI & AI Agents module
---

## ✉️ Support

For issues or questions, contact the development team or refer to `WARP_SKILL.md` for troubleshooting.

---

**Last Updated:** April 2026  
**Status:** ✅ Production-Ready Prototype
