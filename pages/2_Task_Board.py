"""
WARP Task Board Page (pages/2_Task_Board.py)
Displays alerts sorted by severity with action buttons for each alert

FILE STRUCTURE:
  Page 1: 1_Dashboard.py (overview, metrics, charts)
  Page 2: 2_Task_Board.py (list of alerts, action buttons) ← YOU ARE HERE
  Page 3: 3_Supplier_Scores.py (supplier rankings)
  Page 4: 4_Follow_Up.py (draft emails)
  Page 5: 5_ERP_Update.py (update delivery dates)
  Page 6: 6_Management_Report.py (weekly summary report)

WHAT THIS PAGE DOES:
  1. Load alerts from Phase 3 (delay detection)
  2. Sort by severity: Red → Amber → Proactive → OK
  3. Display each alert as a card/row
  4. Provide action buttons: Draft Follow-up, Update ERP, View Details
  5. Filter by alert level (optional)
  6. Show supplier risk score inline

WORKFLOW:
  Team member views Task Board
  → Sees Red alerts first
  → Clicks "Draft Follow-up" for an alert
  → Routes to Follow-Up page (Phase 4) with PO pre-filled
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys
sys.path.insert(0, '.')

from agent.scorer import score_all_suppliers
from agent.delay_detector import detect_all_alerts


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="WARP Task Board",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# CACHED DATA LOADING (same as Dashboard)
# ============================================================================
# Reuse the same @st.cache_data functions to avoid reloading data

@st.cache_data
def load_supplier_scores():
    """Load and score all suppliers."""
    scores_df = score_all_suppliers(
        "data/synthetic/suppliers.csv",
        "data/synthetic/delivery_events.csv",
        "data/synthetic/penalties.csv",
        "data/synthetic/email_threads.csv"
    )
    return scores_df


@st.cache_data
def load_purchase_orders():
    """Load all open purchase orders."""
    pos_df = pd.read_csv("data/synthetic/purchase_orders.csv")
    return pos_df


@st.cache_data
def load_suppliers():
    """Load supplier master data."""
    suppliers_df = pd.read_csv("data/synthetic/suppliers.csv")
    return suppliers_df


@st.cache_data
def load_email_threads():
    """Load email communication threads."""
    emails_df = pd.read_csv("data/synthetic/email_threads.csv")
    return emails_df

# Connecte to _4_Follow_Up.py to reuse the same alert detection logic
@st.cache_data
def detect_all_po_alerts(pos_df, scores_df, emails_df):
    from agent.delay_detector import DelayDetector
    detector = DelayDetector(pos_df, scores_df, emails_df)
    alerts_df = detector.detect_alerts()
    
    # Ensure all required fields exist in alerts_df
    if 'warp_score' not in alerts_df.columns:
        # Merge scores from scores_df
        alerts_df = alerts_df.merge(
            scores_df[['supplier_id', 'warp_score']],
            on='supplier_id',
            how='left'
        )
    
    if 'alert_level' not in alerts_df.columns:
        alerts_df['alert_level'] = 'ok'  # Default
    
    if 'material_category' not in alerts_df.columns:
        # Get from suppliers
        suppliers_df = pd.read_csv("data/synthetic/suppliers.csv")
        alerts_df = alerts_df.merge(
            suppliers_df[['supplier_id', 'material_category']],
            on='supplier_id',
            how='left'
        )
    
    return alerts_df


# ============================================================================
# PAGE TITLE AND INTRO
# ============================================================================
st.title("📋 Task Board")
st.markdown("### Open Alerts Requiring Action")

# Check if team member is logged in
if "team_member" not in st.session_state or not st.session_state["team_member"]:
    st.error("❌ Please sign in on the Home page first")
    st.stop()

st.info(f"👤 Logged in as: **{st.session_state['team_member']}**")


# ============================================================================
# LOAD DATA
# ============================================================================
st.write("**Loading alerts...**")

suppliers_df = load_suppliers()
scores_df = load_supplier_scores()
pos_df = load_purchase_orders()
emails_df = load_email_threads()
alerts_df = detect_all_po_alerts(pos_df, scores_df, emails_df)

st.success("✅ Alerts loaded!")


# ============================================================================
# FILTER BY TEAM MEMBER'S MATERIAL CATEGORY
# ============================================================================
# Only show alerts relevant to this team member's portfolio

TEAM_MEMBER_CATEGORIES = {
    "Ana Silva": ["Raw Materials", "Weaving"],
    "João Santos": ["Cutting", "Sewing"],
    "Maria Costa": ["Finishing"],
    "Pedro Oliveira": ["Raw Materials", "Finishing"],
}

team_member = st.session_state.get("team_member", "Ana Silva")
categories = TEAM_MEMBER_CATEGORIES.get(team_member, ["Raw Materials"])

# Filter alerts to team member's categories
filtered_alerts_df = alerts_df[
    alerts_df["material_category"].isin(categories)
].copy()

# Sort by alert level (Red first, then Amber, then Proactive, then OK)
# This ensures critical alerts appear at the top
alert_order = {"red": 0, "amber": 1, "proactive": 2, "ok": 3}
filtered_alerts_df["sort_order"] = filtered_alerts_df["alert_level"].map(alert_order)
filtered_alerts_df = filtered_alerts_df.sort_values(["sort_order", "days_to_delivery"])


# ============================================================================
# ALERT LEVEL FILTER (SIDEBAR)
# ============================================================================
# Allow team member to filter by specific alert level

st.sidebar.markdown("### Filter Alerts")
alert_filter = st.sidebar.multiselect(
    label="Show alert levels:",
    options=["red", "amber", "proactive", "ok"],
    default=["red", "amber", "proactive"],
    format_func=lambda x: {
        "red": "🔴 RED (Overdue)",
        "amber": "🟡 AMBER (Imminent)",
        "proactive": "🟠 PROACTIVE (High Risk)",
        "ok": "🟢 OK (On Track)"
    }.get(x, x)
)

# Apply the filter
if alert_filter:
    filtered_alerts_df = filtered_alerts_df[filtered_alerts_df["alert_level"].isin(alert_filter)]


# ============================================================================
# DISPLAY ALERT SUMMARY
# ============================================================================
# Show counts of each alert type after filtering

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    red_count = (filtered_alerts_df["alert_level"] == "red").sum()
    st.metric("🔴 RED", red_count)

with col2:
    amber_count = (filtered_alerts_df["alert_level"] == "amber").sum()
    st.metric("🟡 AMBER", amber_count)

with col3:
    proactive_count = (filtered_alerts_df["alert_level"] == "proactive").sum()
    st.metric("🟠 PROACTIVE", proactive_count)

with col4:
    ok_count = (filtered_alerts_df["alert_level"] == "ok").sum()
    st.metric("🟢 OK", ok_count)


# ============================================================================
# DISPLAY ALERTS AS EXPANDABLE CARDS
# ============================================================================
# Each alert is displayed as a collapsible section (st.expander)
# Clicking the expander reveals detailed information and action buttons

st.markdown("---")
st.subheader(f"📌 {len(filtered_alerts_df)} Alerts to Review")

# Check if there are any alerts to display
if len(filtered_alerts_df) == 0:
    st.success("✅ No alerts matching your filter! All POs are on track.")
else:
    # Loop through each alert and display it
    for idx, alert in filtered_alerts_df.iterrows():
        # ================================================================
        # ALERT HEADER (Always visible)
        # ================================================================
        # Shows: [ALERT ICON] PO Number | Supplier Name | Score | Days Left
        
        # Get the alert icon based on level
        icon_map = {
            "red": "🔴",
            "amber": "🟡",
            "proactive": "🟠",
            "ok": "🟢"
        }
        icon = icon_map.get(alert["alert_level"], "⚪")
        
        # Format the header text
        # Example: "🔴 PO00001 | Supplier ABC | Score: 4.5 | Overdue by 3 days"
        header_text = (
            f"{icon} **{alert['po_number']}** | "
            f"{alert['supplier_name']} | "
            f"Score: {alert['warp_score']:.1f} | "
            f"{alert['days_to_delivery']} days"
        )
        
        # Create an expander (collapsible section)
        # When clicked, it expands to show detailed info and action buttons
        with st.expander(header_text, expanded=(alert["alert_level"] == "red")):
            # RED alerts start expanded; others are collapsed by default
            
            # ================================================================
            # ALERT DETAILS (Hidden until expander is clicked)
            # ================================================================
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**PO Number:** {alert['po_number']}")
                st.write(f"**Supplier:** {alert['supplier_name']}")
                st.write(f"**Category:** {alert['material_category']}")
            
            with col2:
                st.write(f"**Expected Delivery:** {alert['expected_delivery'].strftime('%Y-%m-%d')}")
                st.write(f"**Days to Delivery:** {alert['days_to_delivery']}")
                st.write(f"**Status:** {alert['alert_level'].upper()}")
            
            with col3:
                st.write(f"**WARP Score:** {alert['warp_score']:.1f}/10")
                st.write(f"**Trend:** {alert['trend_arrow']}")
                
                # Show delay signal if detected
                if alert.get("has_delay_signal", False):
                    st.warning("⚠️ Delay signal detected in supplier email")
            
            # Show the alert reason (with context)
            st.markdown(f"**Alert Reason:** {alert['reason']}")
            
            # ================================================================
            # ACTION BUTTONS (For team member to take action)
            # ================================================================
            # These buttons route to other pages or update session state
            
            st.markdown("---")
            st.subheader("📌 Actions")
            
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                # BUTTON 1: Draft Follow-up Email
                # Clicking this stores the PO in session state and routes to Follow-Up page
                if st.button(
                    "✉️ Draft Follow-up",
                    key=f"draft_{alert['po_number']}",
                    type="primary",
                    use_container_width=True
                ):
                    # Store the PO details in session state so Follow-Up page can access them
                    st.session_state["selected_po"] = {
                        "po_number": alert["po_number"],
                        "supplier_name": alert["supplier_name"],
                        "supplier_id": alert["supplier_id"],
                        "expected_delivery": alert["expected_delivery"],
                        "days_to_delivery": alert["days_to_delivery"],
                        "warp_score": alert["warp_score"],
                        "alert_level": alert["alert_level"],
                    }
                    
                    # Route to the Follow-Up page
                    st.switch_page("pages/4_Follow_Up.py")
            
            # ============ UPDATE ERP DATE BUTTON ============
            with action_col2:
                if st.button(
                    "📅 Update ERP Date",
                    key=f"erp_{alert['po_number']}",
                    use_container_width=True
                ):
                    # Build selected_po with all available fields
                    selected_po_data = {
                        "po_number": alert["po_number"],
                        "supplier_name": alert["supplier_name"],
                        "supplier_id": alert.get("supplier_id", "unknown"),
                        "expected_delivery": alert["expected_delivery"],
                        "days_to_delivery": alert.get("days_to_delivery", 0),
                        "warp_score": alert.get("warp_score", 0.0),
                        "alert_level": alert.get("alert_level", "ok"),
                        "material_category": alert.get("material_category", "Unknown"),
                    }
                    
                    st.session_state["selected_po"] = selected_po_data
                    st.switch_page("pages/5_ERP_Update.py")
            # =============================================
            
            with action_col3:
                # BUTTON 3: View Full Details
                # Displays additional information about the PO and supplier
                if st.button(
                    "📖 View Details",
                    key=f"details_{alert['po_number']}",
                    use_container_width=True
                ):
                    # Store and navigate (or just expand with more info here)
                    st.session_state["show_full_details"] = True
            
            # Show additional details if requested
            if st.session_state.get("show_full_details", False):
                st.markdown("---")
                st.subheader("📖 Full PO Details")
                
                # Get the original PO data
                po_data = pos_df[pos_df["po_number"] == alert["po_number"]]
                
                if len(po_data) > 0:
                    po = po_data.iloc[0]
                    st.write(f"**Item Code:** {po.get('item_code', 'N/A')}")
                    st.write(f"**Quantity:** {po.get('quantity', 'N/A')} units")
                    st.write(f"**PO Date:** {po.get('po_date', 'N/A')}")
                    
                    # Get supplier details
                    supplier_data = suppliers_df[suppliers_df["supplier_id"] == alert["supplier_id"]]
                    if len(supplier_data) > 0:
                        supplier = supplier_data.iloc[0]
                        st.write(f"**Supplier Country:** {supplier.get('country', 'N/A')}")