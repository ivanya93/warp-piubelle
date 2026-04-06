"""
WARP Session State Manager (utils/state.py)

Centralized session state initialization.
Ensures all pages have the same default state values.
"""

import streamlit as st


def initialize_session_state():
    """Initialize all session state variables with defaults."""
    
    defaults = {
        # User
        "team_member": None,
        
        # Navigation
        "selected_po": None,
        "show_full_details": False,
        
        # Follow-up drafts
        "draft_email": None,
        "approved_followups": [],
        
        # ERP updates
        "erp_updates": [],
        "last_erp_update": None,
        
        # Reports
        "generated_report": None,
        "report_kpis": None,
        "sent_reports": [],
        "last_sent_report": None,
    }
    
    # Set defaults for any missing keys
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_team_member():
    """Get the currently logged-in team member."""
    return st.session_state.get("team_member", None)


def set_team_member(name: str):
    """Set the logged-in team member."""
    st.session_state["team_member"] = name


def get_selected_po():
    """Get the currently selected PO."""
    return st.session_state.get("selected_po", None)


def set_selected_po(po_data: dict):
    """Store a PO for multi-page access."""
    st.session_state["selected_po"] = po_data


def clear_selected_po():
    """Clear the selected PO."""
    st.session_state["selected_po"] = None


def add_followup(record: dict):
    """Log an approved follow-up."""
    if "approved_followups" not in st.session_state:
        st.session_state["approved_followups"] = []
    st.session_state["approved_followups"].append(record)


def add_erp_update(record: dict):
    """Log an ERP update."""
    if "erp_updates" not in st.session_state:
        st.session_state["erp_updates"] = []
    st.session_state["erp_updates"].append(record)
    st.session_state["last_erp_update"] = record


def add_sent_report(record: dict):
    """Log a sent report."""
    if "sent_reports" not in st.session_state:
        st.session_state["sent_reports"] = []
    st.session_state["sent_reports"].append(record)
    st.session_state["last_sent_report"] = record