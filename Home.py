"""
WARP Home Page — Entry point for the Streamlit app
"""

import streamlit as st

st.set_page_config(page_title="WARP", page_icon="⚙️", layout="wide")

st.title("🚀 WARP — Workflow-Aware Risk & Procurement Agent")
st.markdown("### Piubelle Supplier Management System")

st.write("""
Welcome to WARP! This is a procurement intelligence platform that helps detect, 
score, and recommend responses to supplier delays before they cascade into production 
disruptions.
""")

# Initialize session state
defaults = {"team_member": None, "tasks": [], "draft": None, "erp_preview": False}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Procurement Team Member sign-in
st.header("Procurement Team Member Sign-In")
team_members = ["Ana Silva", "João Santos", "Maria Costa", "Pedro Oliveira"]
selected_member = st.selectbox("Select your name:", team_members)

if st.button("Sign In", type="primary"):
    st.session_state["team_member"] = selected_member
    st.success(f"Welcome, {selected_member}! 👋")
    st.info("Navigate to the Task Board to view open alerts.")

if st.session_state["team_member"]:
    st.write(f"**Logged in as:** {st.session_state['team_member']}")
