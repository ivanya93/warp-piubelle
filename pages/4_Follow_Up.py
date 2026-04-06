"""
WARP Follow-Up Page (pages/4_Follow_Up.py)
Drafts supplier follow-up emails using Claude API with tone control

WHAT THIS PAGE DOES:
  1. Retrieve the selected PO from session state (from Task Board)
  2. Display PO details and supplier info
  3. Let team member choose tone: Routine / Urgent / Escalation
  4. Call Claude API to generate a follow-up email draft
  5. Display the draft in an editable text area
  6. Require explicit "Approve" button click before logging action
  7. Log approved follow-ups in session state

TONE DEFINITIONS:
  Routine: Polite, no urgency, 5-day response window
  Urgent: Firm, references OTIF penalty risk, 48-hour response window
  Escalation: Direct, senior escalation threat, 24-hour window, CC line

HUMAN-IN-THE-LOOP (HITL) GATE:
  - Claude generates draft → team member reviews → must click "Approve"
  - No automatic sending; draft is logged as "pending approval"
  - Team member can edit the draft before approving
  - Requires explicit confirmation to proceed
"""

import streamlit as st
import pandas as pd
from datetime import date
import sys
sys.path.insert(0, '.')

# Import Claude API client
from anthropic import Anthropic

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="WARP Follow-Up Drafter",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# INITIALIZE CLAUDE CLIENT
# ============================================================================
# Create an Anthropic client to call Claude API
# API key is stored in .streamlit/secrets.toml

@st.cache_resource
def get_claude_client():
    """
    Initialize and cache the Anthropic client.
    
    Why cache?
      The client object is expensive to create. By caching it with
      @st.cache_resource, we create it once and reuse it across page reloads.
    
    Returns:
        Anthropic client instance
    """
    try:
        client = Anthropic()
        return client
    except Exception as e:
        st.error(f"❌ Failed to initialize Claude client: {e}")
        return None


# ============================================================================
# PAGE TITLE AND CHECKS
# ============================================================================
st.title("✉️ Supplier Follow-Up Drafter")
st.markdown("### Draft professional follow-up emails to suppliers")

# Check if team member is logged in
if "team_member" not in st.session_state or not st.session_state["team_member"]:
    st.error("❌ Please sign in on the Home page first")
    st.stop()

# Check if a PO was selected from Task Board
if "selected_po" not in st.session_state:
    st.warning("⚠️ No PO selected. Please select a PO from the Task Board first.")
    if st.button("← Back to Task Board"):
        st.switch_page("pages/2_Task_Board.py")
    st.stop()

# Get the selected PO from session state (passed from Task Board)
selected_po = st.session_state["selected_po"]

st.info(f"👤 Logged in as: **{st.session_state['team_member']}**")


# ============================================================================
# DISPLAY PO DETAILS (Context for the draft)
# ============================================================================
# Show the PO information that will be referenced in the follow-up email

st.markdown("---")
st.subheader("📌 PO Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.write(f"**PO Number:** {selected_po['po_number']}")
    st.write(f"**Supplier:** {selected_po['supplier_name']}")
    st.write(f"**Alert Level:** {selected_po['alert_level'].upper()}")

with col2:
    st.write(f"**Expected Delivery:** {selected_po['expected_delivery'].strftime('%Y-%m-%d')}")
    st.write(f"**Days to Delivery:** {selected_po['days_to_delivery']}")
    st.write(f"**WARP Score:** {selected_po['warp_score']:.1f}/10")

with col3:
    if selected_po['alert_level'] == 'red':
        st.write("**Risk Status:** 🔴 OVERDUE")
    elif selected_po['alert_level'] == 'amber':
        st.write("**Risk Status:** 🟡 IMMINENT")
    elif selected_po['alert_level'] == 'proactive':
        st.write("**Risk Status:** 🟠 HIGH RISK")
    else:
        st.write("**Risk Status:** 🟢 OK")


# ============================================================================
# TONE SELECTION
# ============================================================================
# Let the team member choose the tone for the follow-up email
# Different tones convey different levels of urgency

st.markdown("---")
st.subheader("🎯 Choose Tone")

st.write("""
Select the tone for your follow-up email. The tone affects:
- **Language:** Polite vs. Firm vs. Direct
- **Urgency:** 5-day window vs. 48-hour vs. 24-hour
- **Escalation:** Collaborative vs. Penalty-focused vs. Senior escalation
""")

col1, col2, col3 = st.columns(3)

with col1:
    routine_selected = st.checkbox(
        "🟢 **Routine**",
        value=False,
        help="Polite, collaborative, 5-day response window"
    )

with col2:
    urgent_selected = st.checkbox(
        "🟡 **Urgent**",
        value=False,
        help="Firm, references OTIF penalties, 48-hour window"
    )

with col3:
    escalation_selected = st.checkbox(
        "🔴 **Escalation**",
        value=False,
        help="Direct, senior escalation, 24-hour window"
    )

# Only allow one tone to be selected
tones_selected = [routine_selected, urgent_selected, escalation_selected]
if sum(tones_selected) > 1:
    st.error("❌ Please select only ONE tone")
    st.stop()
elif sum(tones_selected) == 0:
    st.warning("⚠️ Please select a tone to generate a draft")
    st.stop()

# Determine which tone was selected
if routine_selected:
    selected_tone = "routine"
    tone_emoji = "🟢"
elif urgent_selected:
    selected_tone = "urgent"
    tone_emoji = "🟡"
else:
    selected_tone = "escalation"
    tone_emoji = "🔴"

st.markdown(f"**Selected Tone:** {tone_emoji} {selected_tone.upper()}")


# ============================================================================
# GENERATE DRAFT BUTTON
# ============================================================================
# When clicked, calls Claude API to generate the email draft

st.markdown("---")
st.subheader("✍️ Generate Draft")

if st.button("Generate Draft Email", type="primary", use_container_width=True):
    # ================================================================
    # STEP 1: GET CLAUDE CLIENT
    # ================================================================
    client = get_claude_client()
    if not client:
        st.error("❌ Claude client not available")
        st.stop()
    
    # ================================================================
    # STEP 2: BUILD THE PROMPT
    # ================================================================
    # Create a detailed prompt that tells Claude to generate the email
    # Include PO details, supplier info, and tone instructions
    
    tone_instructions = {
        "routine": """
Tone: Professional and polite, collaborative approach
- Use courteous language ("We appreciate your partnership...")
- Reference the delivery timeline without alarm
- Request a response within 5 business days
- Express confidence in the supplier
- Do not mention penalties or escalation
Example opening: "We wanted to reach out regarding PO {po_number}..."
        """,
        "urgent": """
Tone: Firm and professional, emphasizing importance
- Use direct language without being rude
- Reference the OTIF penalty risk explicitly
- Request a response within 48 hours
- Mention potential business impact
- Include a clear action item
Example opening: "This is an urgent matter regarding PO {po_number}..."
        """,
        "escalation": """
Tone: Direct and formal, senior escalation implied
- Use formal business language
- Reference potential escalation to senior management
- Request immediate response (24 hours)
- Suggest a senior contact be involved
- Include CC line for escalation contact
Example opening: "Re: Critical Issue with PO {po_number} - Escalation Required"
        """
    }
    
    # Build the full prompt
    prompt = f"""
You are drafting a follow-up email to a supplier about a delayed purchase order.

PURCHASE ORDER DETAILS:
- PO Number: {selected_po['po_number']}
- Supplier: {selected_po['supplier_name']}
- Expected Delivery: {selected_po['expected_delivery'].strftime('%Y-%m-%d')}
- Days Until Delivery: {selected_po['days_to_delivery']} days
- Supplier Risk Score: {selected_po['warp_score']}/10
- Alert Level: {selected_po['alert_level'].upper()}

TONE INSTRUCTIONS:
{tone_instructions[selected_tone]}

REQUIREMENTS:
1. Keep the email concise (150-200 words)
2. Use professional Portuguese business language
3. Include a specific call-to-action
4. Reference the PO number prominently
5. Do NOT include "Subject:" line - just the body
6. Sign off as the procurement team (not a specific person)

Generate ONLY the email body text. Do not include any markdown formatting or explanations.
    """
    
    # ================================================================
    # STEP 3: CALL CLAUDE API
    # ================================================================
    with st.spinner(f"🤖 Generating {selected_tone.upper()} tone draft..."):
        try:
            # Call Claude to generate the email
            message = client.messages.create(
                model="claude-sonnet-4-20250514",  # Latest Claude model
                max_tokens=500,  # Keep it concise
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract the generated text from Claude's response
            draft_text = message.content[0].text
            
            # ================================================================
            # STEP 4: STORE DRAFT IN SESSION STATE
            # ================================================================
            # Save the draft so it persists if the page reloads
            st.session_state["draft_email"] = draft_text
            st.session_state["draft_tone"] = selected_tone
            st.session_state["draft_po"] = selected_po['po_number']
            
            st.success("✅ Draft generated! Review and approve below.")
            
        except Exception as e:
            st.error(f"❌ Failed to generate draft: {e}")
            st.info("💡 Tip: Make sure your API key is valid in .streamlit/secrets.toml")


# ============================================================================
# DISPLAY AND EDIT DRAFT
# ============================================================================
# Show the generated draft in an editable text area

if "draft_email" in st.session_state:
    st.markdown("---")
    st.subheader("📝 Review & Edit Draft")
    
    # Display the draft in an editable text area
    # Team member can modify the text before approval
    edited_draft = st.text_area(
        label="Email Draft (you can edit this before approving):",
        value=st.session_state["draft_email"],
        height=300,
        help="Edit this draft as needed before sending"
    )
    
    # Display draft metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Tone:** {tone_emoji} {selected_tone.upper()}")
    with col2:
        st.write(f"**PO:** {st.session_state['draft_po']}")
    with col3:
        st.write(f"**Character Count:** {len(edited_draft)}")
    
    # ================================================================
    # HUMAN-IN-THE-LOOP (HITL) APPROVAL GATE
    # ================================================================
    # Team member must explicitly click "Approve" to log the follow-up
    # This ensures no action is taken without confirmation
    
    st.markdown("---")
    st.subheader("✅ Approval Gate")
    
    st.warning("""
⚠️ **Important:** This draft will be logged as a follow-up action.
Once approved, you will send this email to the supplier from Outlook.
Please review carefully before proceeding.
    """)
    
    # Create two buttons: Approve (primary) and Discard (secondary)
    col1, col2 = st.columns(2)
    
    with col1:
        # APPROVE BUTTON (Primary - emphasized)
        if st.button("✅ Approve & Send", type="primary", use_container_width=True):
            # ================================================================
            # LOG THE ACTION
            # ================================================================
            # Store the approved follow-up in session state
            # (In production, this would send to email/database)
            
            if "approved_followups" not in st.session_state:
                st.session_state["approved_followups"] = []
            
            # Create a record of the approved follow-up
            followup_record = {
                "po_number": st.session_state['draft_po'],
                "supplier_name": selected_po['supplier_name'],
                "tone": st.session_state["draft_tone"],
                "draft": edited_draft,
                "approved_by": st.session_state["team_member"],
                "approved_at": date.today(),
                "status": "Pending Send"
            }
            
            # Add to list of approved follow-ups
            st.session_state["approved_followups"].append(followup_record)
            
            # ================================================================
            # SHOW CONFIRMATION
            # ================================================================
            st.success("✅ **Follow-up approved!**")
            st.info(f"""
Your follow-up email has been approved and is ready to send.

**Next Steps:**
1. Copy the draft below
2. Open Outlook
3. Create a new email to: {selected_po['supplier_name']}
4. Paste the draft
5. Send

**Details logged:**
- PO: {st.session_state['draft_po']}
- Tone: {st.session_state['draft_tone'].upper()}
- Approved by: {st.session_state['team_member']}
- Date: {date.today()}
            """)
            
            # Clear the draft from session state after approval
            del st.session_state["draft_email"]
            
            # Display a "Copy to Clipboard" friendly format
            st.markdown("---")
            st.subheader("📋 Copy This Draft")
            st.code(edited_draft, language="text")
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back to Task Board", use_container_width=True):
                    st.switch_page("pages/2_Task_Board.py")
            with col2:
                if st.button("📊 Go to Dashboard", use_container_width=True):
                    st.switch_page("pages/1_Dashboard.py")
    
    with col2:
        # DISCARD BUTTON (Secondary - less emphasized)
        if st.button("❌ Discard", use_container_width=True):
            # Remove the draft from session state
            del st.session_state["draft_email"]
            st.info("Draft discarded. Generate a new one or go back.")
            st.rerun()


# ============================================================================
# FOOTER & NAVIGATION
# ============================================================================
if "draft_email" not in st.session_state:
    st.markdown("---")
    st.subheader("🔄 Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← Back to Task Board", use_container_width=True, key="nav_taskboard_2"):
            st.switch_page("pages/2_Task_Board.py")
    
    with col2:
        if st.button("📊 View Dashboard", use_container_width=True, key="nav_dashboard_2"):
            st.switch_page("pages/1_Dashboard.py")
    
    with col3:
        if st.button("🔄 Refresh Page", use_container_width=True, key="nav_refresh"):
            st.rerun()


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    "WARP Follow-Up Drafter | Last updated: " + date.today().strftime("%Y-%m-%d") +
    " | Piubelle Supplier Management System"
)