"""
WARP Data Loader (utils/data_loader.py)

Centralized, cached data loading functions.
All data reads use @st.cache_data to avoid reloading on every page interaction.
"""

import streamlit as st
import pandas as pd
import sys
sys.path.insert(0, '.')

from agent.scorer import score_all_suppliers
from agent.delay_detector import DelayDetector


@st.cache_data
def load_suppliers():
    """Load supplier master data."""
    suppliers_df = pd.read_csv("data/synthetic/suppliers.csv")
    return suppliers_df


@st.cache_data
def load_purchase_orders():
    """Load all open purchase orders."""
    pos_df = pd.read_csv("data/synthetic/purchase_orders.csv")
    return pos_df


@st.cache_data
def load_delivery_events():
    """Load historical delivery events."""
    events_df = pd.read_csv("data/synthetic/delivery_events.csv")
    return events_df


@st.cache_data
def load_email_threads():
    """Load email communication threads."""
    emails_df = pd.read_csv("data/synthetic/email_threads.csv")
    return emails_df


@st.cache_data
def load_penalties():
    """Load OTIF penalty history."""
    penalties_df = pd.read_csv("data/synthetic/penalties.csv")
    return penalties_df


@st.cache_data
def load_airfreight():
    """Load air freight incident history."""
    airfreight_df = pd.read_csv("data/synthetic/airfreight_incidents.csv")
    return airfreight_df


@st.cache_data
def load_supplier_scores():
    """Calculate and load supplier WARP scores."""
    scores_df = score_all_suppliers(
        "data/synthetic/suppliers.csv",
        "data/synthetic/delivery_events.csv",
        "data/synthetic/penalties.csv",
        "data/synthetic/email_threads.csv"
    )
    return scores_df


@st.cache_data
def load_alerts(pos_df, scores_df, emails_df):
    """Detect and load all open alerts."""
    detector = DelayDetector(pos_df, scores_df, emails_df)
    alerts_df = detector.detect_alerts()
    
    # Ensure all required fields exist
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


def load_all_data():
    """Load all data at once. Useful for dashboard."""
    suppliers_df = load_suppliers()
    pos_df = load_purchase_orders()
    delivery_events_df = load_delivery_events()
    emails_df = load_email_threads()
    penalties_df = load_penalties()
    airfreight_df = load_airfreight()
    scores_df = load_supplier_scores()
    alerts_df = load_alerts(pos_df, scores_df, emails_df)
    
    return {
        "suppliers": suppliers_df,
        "pos": pos_df,
        "delivery_events": delivery_events_df,
        "emails": emails_df,
        "penalties": penalties_df,
        "airfreight": airfreight_df,
        "scores": scores_df,
        "alerts": alerts_df,
    }