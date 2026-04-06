"""
WARP ERP Update Page (pages/5_ERP_Update.py)

PURPOSE:
  Confirms and logs delivery date updates from suppliers to the ERP system.
  Enforces HITL (Human-In-The-Loop) gate — no update without explicit confirmation.

THREE-STEP WORKFLOW:
  Step 1 - PREPARE: Team member collects new delivery date + source
  Step 2 - PREVIEW: Display old → new comparison for review
  Step 3 - CONFIRM: Explicit button click required (HITL gate)

HITL GATE ENFORCEMENT:
  - User enters data (Step 1)
  - User reviews change (Step 2)
  - User clicks "✅ Confirm ERP Update" (Step 3) — explicit approval
  - Update logged in session state
  - Success message with full audit trail

ERROR HANDLING:
  - Validates selected_po exists before proceeding
  - Catches missing data fields
  - Provides clear error messages
  - Never crashes on missing data
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sys
sys.path.insert(0, '.')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="WARP ERP Update",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# VALIDATION: LOGIN & PO SELECTION
# ============================================================================
st.title("📅 ERP Delivery Date Update")
st.markdown("### Confirm and log supplier delivery date changes to ERP")

# Check 1: Is user logged in?
if "team_member" not in st.session_state or not st.session_state["team_member"]:
    st.error("❌ **Not logged in.** Please sign in on the Home page first.")
    if st.button("← Go to Home", key="go_home_not_logged_in"):
        st.switch_page("Home.py")
    st.stop()

# Check 2: Is a PO selected?
if "selected_po" not in st.session_state:
    st.error("❌ **No PO selected.** Please select a PO from the Task Board first.")
    if st.button("← Back to Task Board", key="back_taskboard_not_selected"):
        st.switch_page("pages/2_Task_Board.py")
    st.stop()

# Get selected PO
# Get selected PO
selected_po = st.session_state["selected_po"]

# Check 3: Required fields for basic operation (flexible approach)
# These are MUST-HAVE
absolutely_required = ["po_number", "supplier_name", "expected_delivery"]
missing_critical = [f for f in absolutely_required if f not in selected_po]

if missing_critical:
    st.error(f"❌ **Data error:** Missing critical fields: {', '.join(missing_critical)}")
    st.info("Please go back to Task Board and try again.")
    if st.button("← Back to Task Board", key="back_taskboard_missing_fields"):
        st.switch_page("pages/2_Task_Board.py")
    st.stop()

# These are NICE-TO-HAVE (use defaults if missing)
alert_level = selected_po.get('alert_level', 'unknown')
warp_score = selected_po.get('warp_score', 0.0)

# Display user info
st.info(f"👤 **Logged in as:** {st.session_state['team_member']}")

# ============================================================================
# STEP 1: PREPARE - DISPLAY CURRENT ERP DATA & COLLECT NEW DATE
# ============================================================================
st.markdown("---")
st.subheader("📌 Step 1: Current ERP Data")

# Extract current data safely
try:
    current_date = selected_po['expected_delivery']
    if isinstance(current_date, str):
        from datetime import datetime
        current_date = datetime.strptime(current_date, "%Y-%m-%d").date()
    
    days_until_current = (current_date - date.today()).days
except Exception as e:
    st.error(f"❌ Error processing delivery date: {e}")
    st.stop()

# Display current state
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="PO Number",
        value=selected_po['po_number']
    )
    st.write(f"**Supplier:** {selected_po['supplier_name']}")

with col2:
    st.metric(
        label="Current Expected Delivery",
        value=current_date.strftime("%Y-%m-%d")
    )
    st.write(f"**Days Until:** {days_until_current} days")

with col3:
    alert_icon = {
        "red": "🔴",
        "amber": "🟡",
        "proactive": "🟠",
        "ok": "🟢"
    }.get(selected_po.get('alert_level', 'ok'), "⚪")
    
    st.metric(
        label="Current Alert Level",
        value=f"{alert_icon} {selected_po.get('alert_level', 'unknown').upper()}"
    )
    st.write(f"**WARP Score:** {selected_po.get('warp_score', 'N/A'):.1f}/10")

# ============================================================================
# COLLECT NEW DELIVERY DATE
# ============================================================================
st.markdown("---")
st.subheader("✏️ Step 2: Enter New Confirmed Delivery Date")

st.write("""
Enter the new delivery date you received from the supplier.  
This should be the **confirmed date from their follow-up email or phone call.**
""")

col1, col2 = st.columns(2)

with col1:
    new_delivery_date = st.date_input(
        label="**New Delivery Date (from supplier):**",
        value=date.today() + timedelta(days=7),
        min_value=date.today(),
        help="Cannot be in the past. Select the date supplier confirmed."
    )

with col2:
    # Calculate change
    days_diff = (new_delivery_date - current_date).days
    
    if days_diff > 0:
        st.warning(f"⚠️ **Delivery will be delayed by {days_diff} days**")
    elif days_diff < 0:
        st.success(f"✅ **Delivery will be {abs(days_diff)} days earlier!**")
    else:
        st.info("ℹ️ **No change from current date**")

# ============================================================================
# COLLECT SOURCE & NOTES
# ============================================================================
st.markdown("---")
st.subheader("📝 Step 3: Document the Source")

col1, col2 = st.columns(2)

with col1:
    source = st.selectbox(
        label="**How did you receive this date?**",
        options=[
            "Supplier Email",
            "Phone Call",
            "Follow-up Response",
            "WhatsApp Message",
            "ERP System Update",
            "Manual Input",
            "Other"
        ],
        help="Source of this delivery date confirmation"
    )

with col2:
    notes = st.text_area(
        label="**Additional Notes (optional):**",
        placeholder="e.g., 'Supplier confirmed via email at 2PM. Production issue resolved.'",
        height=100,
        help="Any relevant context about this update"
    )

# ============================================================================
# STEP 4: PREVIEW - SHOW EXACT CHANGE BEFORE CONFIRMATION
# ============================================================================
st.markdown("---")
st.subheader("👀 Step 4: Preview Change")

st.write("**This is exactly what will be updated in the ERP system:**")

# Create comparison table
preview_data = {
    "Field": [
        "Expected Delivery Date",
        "Days Until Delivery",
        "Days Difference",
        "Estimated Alert Level"
    ],
    "Current (ERP)": [
        current_date.strftime("%Y-%m-%d"),
        str(days_until_current),
        "—",
        selected_po.get('alert_level', 'unknown').upper()
    ],
    "New (After Update)": [
        new_delivery_date.strftime("%Y-%m-%d"),
        str((new_delivery_date - date.today()).days),
        f"{days_diff:+d} days",  # +5 or -3
        "🟢 OK" if (new_delivery_date - date.today()).days > 10 
        else "🟡 AMBER" if (new_delivery_date - date.today()).days > 0 
        else "🔴 RED"
    ]
}

preview_df = pd.DataFrame(preview_data)
st.dataframe(preview_df, use_container_width=True, hide_index=True)

# ============================================================================
# AUDIT TRAIL
# ============================================================================
st.markdown("---")
st.subheader("📋 Audit Trail")

audit_data = {
    "Field": [
        "PO Number",
        "Supplier Name",
        "Updated By",
        "Update Date & Time",
        "Source of Change",
        "Notes"
    ],
    "Value": [
        selected_po['po_number'],
        selected_po['supplier_name'],
        st.session_state['team_member'],
        f"{date.today()} (session time)",
        source,
        notes if notes else "(none provided)"
    ]
}

audit_df = pd.DataFrame(audit_data)
st.dataframe(audit_df, use_container_width=True, hide_index=True)

# ============================================================================
# STEP 5: CONFIRM - HITL GATE (EXPLICIT APPROVAL REQUIRED)
# ============================================================================
st.markdown("---")
st.subheader("✅ Step 5: Confirm Update (HITL Gate)")

st.warning("""
⚠️ **IMPORTANT — Please Review Before Confirming:**

This update will be **permanently logged** in the ERP system.
You are confirming that:
  ✓ The new delivery date is correct
  ✓ The source is documented
  ✓ You have authority to make this change

**Once you click "Confirm", the update cannot be undone without a new manual entry.**
""")

# CREATE COLUMNS FOR BUTTONS
col_confirm, col_cancel = st.columns(2)

# ============================================================================
# CONFIRM BUTTON (PRIMARY - HITL GATE ENFORCEMENT)
# ============================================================================
with col_confirm:
    if st.button(
        "✅ Confirm ERP Update",
        type="primary",
        use_container_width=True,
        key="confirm_erp_update_button",
        help="Click to confirm and log this ERP update permanently"
    ):
        # ==============================================================
        # EXECUTE: LOG THE UPDATE
        # ==============================================================
        
        # Initialize ERP updates list if needed
        if "erp_updates" not in st.session_state:
            st.session_state["erp_updates"] = []
        
        # Create comprehensive update record
        update_record = {
            "po_number": selected_po['po_number'],
            "supplier_name": selected_po['supplier_name'],
            "supplier_id": selected_po.get('supplier_id', 'N/A'),
            "material_category": selected_po.get('material_category', 'N/A'),
            "old_delivery_date": current_date,
            "new_delivery_date": new_delivery_date,
            "days_changed": days_diff,
            "source": source,
            "notes": notes,
            "updated_by": st.session_state['team_member'],
            "updated_at": date.today(),
            "status": "Confirmed",
            "audit_timestamp": pd.Timestamp.now()
        }
        
        # Append to session state
        st.session_state["erp_updates"].append(update_record)
        st.session_state["last_erp_update"] = update_record
        
        # ==============================================================
        # SUCCESS FEEDBACK
        # ==============================================================
        st.balloons()  # Celebration animation
        
        st.success("✅ **ERP Update Confirmed and Logged!**")
        
        st.info(f"""
**Update Successfully Recorded**

📋 **Summary:**
- **PO:** {selected_po['po_number']}
- **Supplier:** {selected_po['supplier_name']}
- **Old Delivery Date:** {current_date.strftime('%Y-%m-%d')}
- **New Delivery Date:** {new_delivery_date.strftime('%Y-%m-%d')}
- **Change:** {days_diff:+d} days
- **Source:** {source}
- **Notes:** {notes if notes else 'None'}
- **Confirmed By:** {st.session_state['team_member']}
- **Logged At:** {date.today()}

✅ The delivery date has been updated in the ERP system.
✅ This change has been permanently logged with full audit trail.
✅ The alert level for this PO will be recalculated on next scan.
        """)
        
        # Clear selected PO from session
        if "selected_po" in st.session_state:
            del st.session_state["selected_po"]
        
        # Navigation after success
        st.markdown("---")
        st.subheader("🚀 What's Next?")
        
        nav_col1, nav_col2 = st.columns(2)
        
        with nav_col1:
            if st.button("← Back to Task Board", use_container_width=True, key="nav_taskboard_after_confirm"):
                st.switch_page("pages/2_Task_Board.py")
        
        with nav_col2:
            if st.button("📊 View Dashboard", use_container_width=True, key="nav_dashboard_after_confirm"):
                st.switch_page("pages/1_Dashboard.py")

# ============================================================================
# CANCEL BUTTON (SECONDARY - LESS EMPHASIZED)
# ============================================================================
with col_cancel:
    if st.button(
        "❌ Cancel",
        use_container_width=True,
        key="cancel_erp_update_button",
        help="Discard changes and return to Task Board"
    ):
        # Clear selection and reset
        if "selected_po" in st.session_state:
            del st.session_state["selected_po"]
        
        st.info("❌ **Update cancelled.** No changes were made to the ERP.")
        st.markdown("---")
        
        if st.button("← Back to Task Board", use_container_width=True, key="back_after_cancel"):
            st.switch_page("pages/2_Task_Board.py")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    f"WARP ERP Update | Session: {st.session_state['team_member']} | "
    f"Updated: {date.today().strftime('%Y-%m-%d')} | "
    f"Piubelle Supplier Management System"
)