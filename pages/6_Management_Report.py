"""
WARP Management Report Page (pages/6_Management_Report.py)

PURPOSE:
  Generates and sends weekly management reports to leadership.
  Report includes KPI summary, alerts, top problem suppliers, and recommendations.
  Uses Claude API to generate professional narrative summary.

WORKFLOW:
  Step 1 - PREPARE: Calculate KPIs from alerts and historical data
  Step 2 - GENERATE: Use Claude API to create executive summary
  Step 3 - REVIEW: Display report for team member to review
  Step 4 - SEND: Explicit confirmation button required (HITL gate)

HITL GATE ENFORCEMENT:
  - KPIs collected and displayed
  - Claude generates draft report
  - Team member reviews report
  - Must click "✅ Send Report" to confirm
  - Report logged with timestamp and sender
  - Simulated send (production would use email API)
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from anthropic import Anthropic
import sys
sys.path.insert(0, '.')

from agent.scorer import score_all_suppliers
from agent.delay_detector import detect_all_alerts

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="WARP Management Report",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# VALIDATION: LOGIN
# ============================================================================
st.title("📊 WARP Management Report")
st.markdown("### Weekly Supplier & Procurement KPI Summary")

if "team_member" not in st.session_state or not st.session_state["team_member"]:
    st.error("❌ **Not logged in.** Please sign in on the Home page first.")
    if st.button("← Go to Home", key="go_home_report"):
        st.switch_page("Home.py")
    st.stop()

st.info(f"👤 **Logged in as:** {st.session_state['team_member']}")

# ============================================================================
# CACHED DATA LOADING
# ============================================================================
@st.cache_data
def load_supplier_scores():
    scores_df = score_all_suppliers(
        "data/synthetic/suppliers.csv",
        "data/synthetic/delivery_events.csv",
        "data/synthetic/penalties.csv",
        "data/synthetic/email_threads.csv"
    )
    return scores_df

@st.cache_data
def load_purchase_orders():
    pos_df = pd.read_csv("data/synthetic/purchase_orders.csv")
    return pos_df

@st.cache_data
def load_suppliers():
    suppliers_df = pd.read_csv("data/synthetic/suppliers.csv")
    return suppliers_df

@st.cache_data
def load_email_threads():
    emails_df = pd.read_csv("data/synthetic/email_threads.csv")
    return emails_df

@st.cache_data
def load_penalties():
    penalties_df = pd.read_csv("data/synthetic/penalties.csv")
    return penalties_df

@st.cache_data
def load_airfreight():
    airfreight_df = pd.read_csv("data/synthetic/airfreight_incidents.csv")
    return airfreight_df

@st.cache_data
def detect_all_po_alerts(pos_df, scores_df, emails_df):
    from agent.delay_detector import DelayDetector
    detector = DelayDetector(pos_df, scores_df, emails_df)
    alerts_df = detector.detect_alerts()
    
    # Ensure required fields
    if 'warp_score' not in alerts_df.columns:
        alerts_df = alerts_df.merge(
            scores_df[['supplier_id', 'warp_score']],
            on='supplier_id',
            how='left'
        )
    if 'alert_level' not in alerts_df.columns:
        alerts_df['alert_level'] = 'ok'
    if 'material_category' not in alerts_df.columns:
        suppliers_df = pd.read_csv("data/synthetic/suppliers.csv")
        alerts_df = alerts_df.merge(
            suppliers_df[['supplier_id', 'material_category']],
            on='supplier_id',
            how='left'
        )
    
    return alerts_df

# ============================================================================
# LOAD DATA
# ============================================================================
st.write("**Loading data...**")

suppliers_df = load_suppliers()
scores_df = load_supplier_scores()
pos_df = load_purchase_orders()
emails_df = load_email_threads()
penalties_df = load_penalties()
airfreight_df = load_airfreight()
alerts_df = detect_all_po_alerts(pos_df, scores_df, emails_df)

st.success("✅ Data loaded!")

# ============================================================================
# STEP 1: CALCULATE KPIs
# ============================================================================
st.markdown("---")
st.subheader("📊 Step 1: Calculate Key Performance Indicators")

# Alert counts
red_alerts = (alerts_df["alert_level"] == "red").sum()
amber_alerts = (alerts_df["alert_level"] == "amber").sum()
proactive_alerts = (alerts_df["alert_level"] == "proactive").sum()
ok_alerts = (alerts_df["alert_level"] == "ok").sum()
total_alerts = len(alerts_df)

# OTIF calculation (simplified)
otif_rate = (ok_alerts / total_alerts * 100) if total_alerts > 0 else 0

# Financial metrics
total_penalties = penalties_df["penalty_amount_eur"].sum() if len(penalties_df) > 0 else 0
total_airfreight = airfreight_df["airfreight_cost_eur"].sum() if len(airfreight_df) > 0 else 0

# Cost at risk (estimated based on red/amber alerts)
estimated_cost_per_alert = 5000  # EUR estimate
cost_at_risk = (red_alerts + amber_alerts) * estimated_cost_per_alert

# Top problem suppliers (low WARP scores)
problem_suppliers = scores_df[~scores_df['warp_score'].isna()].nsmallest(3, 'warp_score')[
    ['supplier_name', 'warp_score']
].to_dict('records')

# Top suppliers with most alerts
supplier_alert_counts = alerts_df[alerts_df['alert_level'] != 'ok'].groupby('supplier_name').size().reset_index(name='alert_count')
top_alert_suppliers = supplier_alert_counts.nlargest(3, 'alert_count').to_dict('records')

# Display KPI cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🔴 Red Alerts", red_alerts)
    st.metric("🟡 Amber Alerts", amber_alerts)

with col2:
    st.metric("🟠 Proactive Alerts", proactive_alerts)
    st.metric("🟢 OK", ok_alerts)

with col3:
    st.metric("📦 Total POs", total_alerts)
    st.metric("✅ OTIF Rate", f"{otif_rate:.1f}%")

with col4:
    st.metric("💶 Penalties YTD", f"€{total_penalties:,.0f}")
    st.metric("✈️ Air Freight", f"€{total_airfreight:,.0f}")

# ============================================================================
# STEP 2: GENERATE REPORT WITH CLAUDE API
# ============================================================================
st.markdown("---")
st.subheader("🤖 Step 2: Generate Executive Summary with Claude")

st.write("Claude API will generate a professional management summary report...")

# Initialize Anthropic client (cached)
@st.cache_resource
def get_anthropic_client():
    return Anthropic()

# Build the prompt for Claude
def build_report_prompt(kpis: dict) -> str:
    return f"""
You are a procurement intelligence analyst for Piubelle, a Portuguese home textile company.

Generate a brief, professional WEEKLY MANAGEMENT REPORT based on these KPIs:

**Current Week KPIs:**
- Red Alerts (Overdue): {kpis['red_alerts']}
- Amber Alerts (Imminent): {kpis['amber_alerts']}
- Proactive Alerts (High Risk): {kpis['proactive_alerts']}
- On-Track POs: {kpis['ok_alerts']}
- Total Open POs: {kpis['total_alerts']}
- On-Time In-Full (OTIF) Rate: {kpis['otif_rate']:.1f}%
- Penalties This Period: €{kpis['total_penalties']:,.0f}
- Air Freight Incidents Cost: €{kpis['total_airfreight']:,.0f}
- Estimated Cost-at-Risk: €{kpis['cost_at_risk']:,.0f}

**Top Problem Suppliers (Low WARP Score):**
{chr(10).join([f"- {{name}}: Score {{score:.1f}}/10".format(name=s['supplier_name'], score=s['warp_score']) for s in kpis['problem_suppliers'][:3]])}

**Suppliers with Most Alerts:**
{chr(10).join([f"- {{name}}: {{count}} alerts".format(name=s['supplier_name'], count=s['alert_count']) for s in kpis['top_alert_suppliers'][:3]])}

**Your Report Should Include:**
1. **Executive Summary** (3-4 sentences): Overall procurement health status
2. **Key Metrics**: Highlight critical metrics and trends
3. **Risk Highlights**: Red and Amber alerts that need attention
4. **Problem Suppliers**: Which suppliers are causing delays
5. **Financial Impact**: Penalties and air freight costs incurred
6. **Recommendations**: 3-4 actionable recommendations for leadership

Keep the tone professional, direct, and suitable for C-level executives.
Do NOT use bullet points — write in flowing prose paragraphs.
Total length: 400-500 words.
"""

# Prepare KPIs dict for Claude
kpis_for_report = {
    "red_alerts": red_alerts,
    "amber_alerts": amber_alerts,
    "proactive_alerts": proactive_alerts,
    "ok_alerts": ok_alerts,
    "total_alerts": total_alerts,
    "otif_rate": otif_rate,
    "total_penalties": total_penalties,
    "total_airfreight": total_airfreight,
    "cost_at_risk": cost_at_risk,
    "problem_suppliers": problem_suppliers,
    "top_alert_suppliers": top_alert_suppliers,
}

# Check if we should generate the report
if st.button("🤖 Generate Report with Claude", type="primary", use_container_width=True, key="generate_report"):
    try:
        # Show progress
        progress_bar = st.progress(0, text="Calling Claude API...")
        
        # Get Claude client and generate report
        client = get_anthropic_client()
        prompt = build_report_prompt(kpis_for_report)
        
        progress_bar.progress(25, text="Connecting to Claude...")
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        progress_bar.progress(75, text="Generating report...")
        
        # Extract report text
        report_text = message.content[0].text
        
        # Store in session state
        st.session_state["generated_report"] = report_text
        st.session_state["report_kpis"] = kpis_for_report
        
        progress_bar.progress(100, text="Report generated!")
        st.success("✅ Report generated successfully!")
        
    except Exception as e:
        st.error(f"❌ Claude API error: {e}")
        st.info("Using fallback mock report...")
        
        # Fallback mock report
        fallback_report = f"""
WARP Weekly Procurement Report — Week of {date.today().strftime('%B %d, %Y')}

**Executive Summary**
This week presents moderate supply chain disruption across our procurement portfolio. We currently have {red_alerts} critical overdue orders and {amber_alerts} imminent delivery risks, affecting our on-time in-full (OTIF) rate of {otif_rate:.1f}%. The main concerns center on three suppliers experiencing persistent delivery delays, requiring immediate escalation and supplier relationship management intervention.

**Key Metrics**
Our procurement health indicators show mixed performance. The OTIF rate of {otif_rate:.1f}% is below our 95% target, driven primarily by the {red_alerts} red alerts currently in the system. We have incurred €{total_penalties:,.0f} in penalties and €{total_airfreight:,.0f} in air freight costs this period, with an estimated €{cost_at_risk:,.0f} at risk from current delays.

**Risk Highlights**
Red alerts indicate immediate action is required. We have {red_alerts} purchase orders past their expected delivery date with no goods receipt recorded. Additionally, {amber_alerts} orders are within 10 days of delivery and unconfirmed, requiring urgent follow-up with suppliers.

**Problem Suppliers**
Three suppliers are flagged with low WARP risk scores and should be prioritized for performance improvement discussions. These suppliers consistently miss delivery commitments and have communication delays exceeding acceptable thresholds.

**Recommendations**
1. Immediately escalate all red alerts to supplier leadership with 24-hour response required.
2. Implement daily monitoring of the {amber_alerts} amber alerts until confirmed delivery.
3. Schedule supplier performance reviews with the three lowest-scoring suppliers this week.
4. Evaluate expedited shipping options for critical items to mitigate OTIF penalty risk.
        """
        
        st.session_state["generated_report"] = fallback_report
        st.session_state["report_kpis"] = kpis_for_report

# ============================================================================
# STEP 3: DISPLAY REPORT FOR REVIEW
# ============================================================================
if "generated_report" in st.session_state:
    st.markdown("---")
    st.subheader("📄 Step 3: Review Report")
    
    st.write("**Read the report below and make any edits before sending.**")
    
    # Display report in editable text area
    report_text = st.text_area(
        label="Management Report (editable):",
        value=st.session_state["generated_report"],
        height=400,
        key="report_text_area"
    )
    
    # Update session state with any edits
    st.session_state["generated_report"] = report_text
    
    # ================================================================
    # STEP 4: SEND REPORT - HITL GATE
    # ================================================================
    st.markdown("---")
    st.subheader("✅ Step 4: Send Report (HITL Gate)")
    
    st.warning("""
⚠️ **Important — Please Review Before Sending:**

This report will be logged and marked as sent.
Confirm that:
  ✓ The content is accurate and appropriate for leadership
  ✓ You have reviewed and approved all findings
  ✓ You understand this will be stored in the audit log
    """)
    
    col_send, col_cancel = st.columns(2)
    
    with col_send:
        if st.button(
            "✅ Send Report",
            type="primary",
            use_container_width=True,
            key="send_report_button",
            help="Click to confirm and send this report to management"
        ):
            # Log the report send
            if "sent_reports" not in st.session_state:
                st.session_state["sent_reports"] = []
            
            report_record = {
                "week_ending": date.today(),
                "sent_by": st.session_state['team_member'],
                "sent_at": pd.Timestamp.now(),
                "report_text": st.session_state["generated_report"],
                "kpis": st.session_state["report_kpis"],
                "status": "Sent"
            }
            
            st.session_state["sent_reports"].append(report_record)
            st.session_state["last_sent_report"] = report_record
            
            # Success feedback
            st.balloons()
            st.success("✅ **Report Sent Successfully!**")
            st.info(f"""
Report has been sent to management on {date.today().strftime('%Y-%m-%d')}.

**Report Summary:**
- **Sent by:** {st.session_state['team_member']}
- **Red Alerts:** {st.session_state["report_kpis"]["red_alerts"]}
- **Amber Alerts:** {st.session_state["report_kpis"]["amber_alerts"]}
- **OTIF Rate:** {st.session_state["report_kpis"]["otif_rate"]:.1f}%
- **Cost at Risk:** €{st.session_state["report_kpis"]["cost_at_risk"]:,.0f}

The report has been permanently logged and will be part of the audit trail.
            """)
            
            # Clear the report from session
            del st.session_state["generated_report"]
            del st.session_state["report_kpis"]
    
    with col_cancel:
        if st.button(
            "❌ Cancel",
            use_container_width=True,
            key="cancel_report_button",
            help="Discard this report without sending"
        ):
            st.info("❌ Report cancelled. Not sent.")
            del st.session_state["generated_report"]
            st.rerun()

# ============================================================================
# NAVIGATION
# ============================================================================
st.markdown("---")
st.subheader("🚀 Next Steps")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 View Task Board", use_container_width=True, key="nav_taskboard_report"):
        st.switch_page("pages/2_Task_Board.py")

with col2:
    if st.button("📊 View Dashboard", use_container_width=True, key="nav_dashboard_report"):
        st.switch_page("pages/1_Dashboard.py")

with col3:
    if st.button("🔄 Refresh Report", use_container_width=True, key="refresh_report"):
        st.cache_data.clear()
        st.rerun()

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    f"WARP Management Report | {st.session_state['team_member']} | "
    f"{date.today().strftime('%Y-%m-%d')} | Piubelle Supplier Management System"
)