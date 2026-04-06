"""
WARP Dashboard Page (pages/1_Dashboard.py)
Multi-page Streamlit app — displays KPI cards, charts, and supplier health metrics

FILE NAMING CONVENTION:
  Streamlit recognizes pages by their number prefix: 1_Dashboard.py, 2_Task_Board.py, etc.
  The number controls the order in the sidebar navigation menu.

WHAT THIS PAGE DOES:
  1. Load PO and supplier data
  2. Detect all alerts using Phase 3 logic
  3. Display KPI cards (Red/Amber/Proactive/OK counts)
  4. Show supplier health scatter plot
  5. Filter by team member's material category
  6. Provide navigation to Task Board

DATA FLOW:
  suppliers.csv → scorer.py → delay_detector.py → [KPIs, charts, filters]
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# Import our custom modules from agent/ folder
import sys
sys.path.insert(0, '.')
from agent.scorer import score_all_suppliers
from agent.delay_detector import detect_all_alerts


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
# Set page layout, title, and icon at the very beginning
# Must be called before any other Streamlit commands
st.set_page_config(
    page_title="WARP Dashboard",
    page_icon="📊",
    layout="wide",  # Use full width (not narrow)
    initial_sidebar_state="expanded"
)


# ============================================================================
# CACHED DATA LOADING
# ============================================================================
# @st.cache_data decorator tells Streamlit to cache this function's output
# This means the data is loaded ONCE and reused on every page refresh
# Without caching, the CSV files would reload on every interaction (slow!)

@st.cache_data
def load_supplier_scores():
    """
    Load and score all suppliers.
    
    Returns:
        DataFrame with columns: supplier_id, supplier_name, warp_score, trend_arrow, etc.
    """
    # Call Phase 2 function to generate scores
    scores_df = score_all_suppliers(
        "data/synthetic/suppliers.csv",
        "data/synthetic/delivery_events.csv",
        "data/synthetic/penalties.csv",
        "data/synthetic/email_threads.csv"
    )
    return scores_df


@st.cache_data
def load_purchase_orders():
    """
    Load all open purchase orders.
    
    Returns:
        DataFrame with columns: po_number, supplier_id, supplier_name, expected_delivery, etc.
    """
    pos_df = pd.read_csv("data/synthetic/purchase_orders.csv")
    return pos_df


@st.cache_data
def load_suppliers():
    """
    Load supplier master data.
    
    Returns:
        DataFrame with columns: supplier_id, supplier_name, material_category, country, etc.
    """
    suppliers_df = pd.read_csv("data/synthetic/suppliers.csv")
    return suppliers_df


@st.cache_data
def load_email_threads():
    """
    Load email communication threads.
    
    Returns:
        DataFrame with columns: po_number, supplier_id, has_delay_signal, email_date, etc.
    """
    emails_df = pd.read_csv("data/synthetic/email_threads.csv")
    return emails_df


@st.cache_data
def detect_all_po_alerts(pos_df, scores_df, emails_df):
    """
    Detect all alerts for open POs.
    Uses Phase 3 logic to classify each PO as Red/Amber/Proactive/OK.
    
    Args:
        pos_df: Purchase orders DataFrame
        scores_df: Supplier scores DataFrame
        emails_df: Email threads DataFrame
    
    Returns:
        DataFrame with columns: po_number, alert_level, reason, days_to_delivery, etc.
    """
    # Create a temporary CSV path for POs (since detect_all_alerts expects a path)
    # Actually, we'll pass the DataFrame directly and use the updated function
    from agent.delay_detector import DelayDetector
    
    detector = DelayDetector(pos_df, scores_df, emails_df)
    alerts_df = detector.detect_alerts()
    
    return alerts_df


# ============================================================================
# PAGE TITLE AND INTRO
# ============================================================================
st.title("📊 WARP Dashboard")
st.markdown("### Procurement Intelligence & Supplier Risk Overview")

# Display the logged-in team member's name (from Home.py session state)
if "team_member" in st.session_state and st.session_state["team_member"]:
    st.info(f"👤 Logged in as: **{st.session_state['team_member']}**")
else:
    st.warning("⚠️ Please sign in on the Home page first")


# ============================================================================
# LOAD DATA
# ============================================================================
# All functions use @st.cache_data, so they only run once
st.write("**Loading data...**")

suppliers_df = load_suppliers()
scores_df = load_supplier_scores()
pos_df = load_purchase_orders()
emails_df = load_email_threads()
alerts_df = detect_all_po_alerts(pos_df, scores_df, emails_df)

st.success("✅ Data loaded successfully!")


# ============================================================================
# FILTER BY TEAM MEMBER'S MATERIAL CATEGORY
# ============================================================================
# Each team member is responsible for specific material categories
# Filter the data to show only alerts relevant to their category

# Define team member → material category mapping
TEAM_MEMBER_CATEGORIES = {
    "Ana Silva": ["Raw Materials", "Weaving"],
    "João Santos": ["Cutting", "Sewing"],
    "Maria Costa": ["Finishing"],
    "Pedro Oliveira": ["Raw Materials", "Finishing"],
}

# Get the logged-in team member's categories
team_member = st.session_state.get("team_member", "Ana Silva")
categories = TEAM_MEMBER_CATEGORIES.get(team_member, ["Raw Materials"])

# Filter alerts to only show this team member's material categories
# This ensures each buyer only sees alerts relevant to them
filtered_alerts_df = alerts_df[
    alerts_df["material_category"].isin(categories)
].copy()

st.write(f"**Showing alerts for categories:** {', '.join(categories)}")


# ============================================================================
# CALCULATE KPI METRICS
# ============================================================================
# These are the key performance indicators displayed as large cards

# Count alerts by level in the filtered dataset
red_count = (filtered_alerts_df["alert_level"] == "red").sum()
amber_count = (filtered_alerts_df["alert_level"] == "amber").sum()
proactive_count = (filtered_alerts_df["alert_level"] == "proactive").sum()
ok_count = (filtered_alerts_df["alert_level"] == "ok").sum()

# Total POs in this team member's portfolio
total_pos = len(filtered_alerts_df)

# Calculate at-risk percentage (Red + Amber + Proactive)
at_risk_count = red_count + amber_count + proactive_count
at_risk_pct = (at_risk_count / total_pos * 100) if total_pos > 0 else 0


# ============================================================================
# DISPLAY KPI CARDS IN A ROW
# ============================================================================
# Use st.columns() to create 4 equally-sized metric cards side-by-side
# Each card displays a count and color-coded alert level

st.markdown("---")
st.subheader("📈 Alert Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🔴 RED (Overdue)",
        value=red_count,
        help="POs past their delivery date"
    )

with col2:
    st.metric(
        label="🟡 AMBER (Imminent)",
        value=amber_count,
        help="POs due within 0-10 days"
    )

with col3:
    st.metric(
        label="🟠 PROACTIVE",
        value=proactive_count,
        help="High-risk suppliers with upcoming deliveries"
    )

with col4:
    st.metric(
        label="🟢 OK (On Track)",
        value=ok_count,
        help="POs with no immediate issues"
    )


# ============================================================================
# DISPLAY OVERALL RISK INDICATOR
# ============================================================================
# Show what percentage of this team member's POs are at risk

st.markdown("---")
st.subheader("⚠️ Risk Status")

col1, col2 = st.columns(2)

with col1:
    # Display at-risk percentage with a progress bar
    st.metric(
        label="At-Risk POs",
        value=f"{at_risk_count}/{total_pos}",
        delta=f"{at_risk_pct:.1f}%"
    )
    
    # Use a progress bar to visualize the risk level
    # Red zone: 0-50%, Yellow zone: 50-75%, Orange zone: 75%+
    st.progress(min(at_risk_pct / 100, 1.0))

with col2:
    # Show which levels are currently active
    st.write("**Active Alert Levels:**")
    if red_count > 0:
        st.error(f"🔴 {red_count} RED — Immediate action required")
    if amber_count > 0:
        st.warning(f"🟡 {amber_count} AMBER — Follow-up needed")
    if proactive_count > 0:
        st.info(f"🟠 {proactive_count} PROACTIVE — Early engagement")
    if ok_count == total_pos:
        st.success("🟢 All POs on track!")


# ============================================================================
# CHART 1: ALERT DISTRIBUTION (PIE CHART)
# ============================================================================
# Show the breakdown of alerts visually using a pie chart
# This helps quickly see the proportion of each alert type

st.markdown("---")
st.subheader("📊 Alert Distribution")

# Create a summary of alert counts
alert_summary = filtered_alerts_df["alert_level"].value_counts().reset_index()
alert_summary.columns = ["alert_level", "count"]

# Map alert levels to colors for consistency
color_map = {
    "red": "#DC3545",      # Bootstrap red
    "amber": "#FFC107",    # Bootstrap warning (amber)
    "proactive": "#FF8C00", # Orange
    "ok": "#28A745"        # Bootstrap green
}

# Create the pie chart using Plotly
fig_pie = px.pie(
    alert_summary,
    names="alert_level",
    values="count",
    color="alert_level",
    color_discrete_map=color_map,
    title="PO Status Distribution",
    labels={"alert_level": "Alert Level", "count": "Count"}
)

# Customize the pie chart appearance
fig_pie.update_traces(textposition="inside", textinfo="percent+label")
fig_pie.update_layout(
    height=400,
    showlegend=True,
    hovermode="closest"
)

st.plotly_chart(fig_pie, use_container_width=True)


# ============================================================================
# CHART 2: SUPPLIER HEALTH SCATTER PLOT
# ============================================================================
# Show each supplier as a dot on a 2D graph:
#   X-axis: On-time delivery rate (calculated from scores)
#   Y-axis: WARP Risk Score (1-10)
# This reveals clusters: high-performing, medium, low-performing suppliers

st.markdown("---")
st.subheader("🏥 Supplier Health Overview")

# Merge scores with delivery events to calculate on-time rates
delivery_events_df = pd.read_csv("data/synthetic/delivery_events.csv")

# Calculate on-time rate per supplier
on_time_rates = delivery_events_df.groupby("supplier_id").apply(
    lambda x: (x["delay_days"] == 0).sum() / len(x)
).reset_index()
on_time_rates.columns = ["supplier_id", "on_time_rate"]

# Merge with scores
supplier_health_df = scores_df.merge(on_time_rates, on="supplier_id", how="left")

# Filter to team member's categories
supplier_health_df = supplier_health_df.merge(
    suppliers_df[["supplier_id", "material_category"]],
    on="supplier_id",
    how="left"
)
supplier_health_df = supplier_health_df[
    supplier_health_df["material_category"].isin(categories)
]

# Create scatter plot: On-time rate (X) vs WARP Score (Y)
# Color by alert level (red suppliers cluster bottom-left)
fig_scatter = px.scatter(
    supplier_health_df,
    x="on_time_rate",
    y="warp_score",
    hover_data=["supplier_name", "material_category", "trend_arrow"],
    color="warp_score",
    size="on_time_rate",
    color_continuous_scale="RdYlGn",  # Red to Yellow to Green
    title="Supplier Health Matrix: On-Time Rate vs WARP Score",
    labels={
        "on_time_rate": "On-Time Delivery Rate",
        "warp_score": "WARP Risk Score (1-10)"
    }
)

# Add reference zones
fig_scatter.add_hline(y=3.5, line_dash="dash", line_color="red", annotation_text="High Risk Threshold")
fig_scatter.add_vline(x=0.75, line_dash="dash", line_color="orange", annotation_text="On-Time Threshold")

fig_scatter.update_layout(
    height=500,
    hovermode="closest",
    xaxis_tickformat=".0%"
)

st.plotly_chart(fig_scatter, use_container_width=True)


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
# Show aggregated statistics about supplier performance

st.markdown("---")
st.subheader("📋 Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Average WARP score for this team's suppliers
    avg_score = supplier_health_df["warp_score"].mean()
    st.metric(
        label="Avg Supplier Score",
        value=f"{avg_score:.1f}/10",
        help="Mean WARP score across team's suppliers"
    )

with col2:
    # Average on-time rate
    avg_on_time = supplier_health_df["on_time_rate"].mean()
    st.metric(
        label="Avg On-Time Rate",
        value=f"{avg_on_time:.1%}",
        help="Mean on-time delivery percentage"
    )

with col3:
    # Number of suppliers
    num_suppliers = len(supplier_health_df)
    st.metric(
        label="Suppliers Managed",
        value=num_suppliers,
        help="Total suppliers in your portfolio"
    )

with col4:
    # Number of high-risk suppliers (score < 3.5)
    high_risk_suppliers = (supplier_health_df["warp_score"] < 3.5).sum()
    st.metric(
        label="High-Risk Suppliers",
        value=high_risk_suppliers,
        help="Suppliers with score < 3.5"
    )


# ============================================================================
# NAVIGATION TO OTHER PAGES
# ============================================================================
# Allow the team member to navigate to the Task Board to take action

st.markdown("---")
st.subheader("🚀 Next Steps")

col1, col2 = st.columns(2)

with col1:
    if st.button("📋 Go to Task Board", type="primary", use_container_width=True):
        # st.switch_page() navigates to another page in the multi-page app
        st.switch_page("pages/2_Task_Board.py")

with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        # Clear the cache to reload all data
        st.cache_data.clear()
        st.rerun()


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    "WARP Dashboard | Last updated: " + date.today().strftime("%Y-%m-%d") +
    " | Piubelle Supplier Management System"
)