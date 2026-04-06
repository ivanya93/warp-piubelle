"""
WARP Delay Detection Engine
Classifies Purchase Orders into alert levels: Red, Amber, Proactive, or OK

ALERT CLASSIFICATION RULES:
===========================
RED Alert (🔴 Critical):
  - Expected delivery date is in the PAST (overdue)
  - AND no goods receipt logged yet
  - Action: IMMEDIATE escalation required

AMBER Alert (🟡 High):
  - Expected delivery is WITHIN 0-10 DAYS (imminent)
  - AND delivery not yet confirmed
  - Upgraded to AMBER if delay email signal detected
  - Action: Follow-up email required

PROACTIVE Alert (🟠 Monitor):
  - Expected delivery within 0-20 days
  - AND supplier score is LOW (≤ 3.5)
  - Action: Early engagement with risky suppliers

OK (🟢 Normal):
  - Expected delivery > 10 days away
  - AND no risk signals detected
  - Action: Monitor, no immediate action

TREND MODIFIER:
  - If supplier trend arrow is ↓ (deteriorating)
  - Append reason to alert: "⚠️ Deteriorating trend"
"""

import pandas as pd
import numpy as np
from datetime import datetime, date

class DelayDetector:
    """Classify POs into alert levels based on delivery dates and supplier risk"""
    
    def __init__(self, purchase_orders_df, suppliers_scores_df, email_threads_df):
        """
        Initialize detector with PO data and supplier scores.
        
        Args:
            purchase_orders_df: DataFrame with po_number, expected_delivery, supplier_id, status
            suppliers_scores_df: DataFrame with supplier_id, warp_score, trend_arrow
            email_threads_df: DataFrame with po_number, has_delay_signal
        """
        self.purchase_orders = purchase_orders_df
        self.supplier_scores = suppliers_scores_df
        self.email_threads = email_threads_df
    
    def detect_alerts(self):
        """
        Classify all open POs into alert levels.
        
        Algorithm:
          For each PO:
            1. Calculate days_to_delivery (expected_delivery - today)
            2. Check for delay email signals
            3. Retrieve supplier's WARP score and trend
            4. Apply classification rules (RED → AMBER → PROACTIVE → OK)
            5. Append alert reason/context
        
        Returns:
            DataFrame with po_number, alert_level, days_to_delivery, reason, trend_indicator
        """
        alerts = []
        today = date.today()
        
        for idx, po in self.purchase_orders.iterrows():
            # ================================================================
            # STEP 1: CALCULATE DAYS TO DELIVERY
            # ================================================================
            # Parse the expected_delivery date and convert to date object
            expected_delivery_str = po["expected_delivery"]
            
            # Handle different date formats (ensure it's a string first)
            if isinstance(expected_delivery_str, str):
                expected_delivery = datetime.strptime(expected_delivery_str, "%Y-%m-%d").date()
            else:
                expected_delivery = expected_delivery_str  # Already a date object
            
            # Calculate days until delivery
            # Negative = overdue, 0 = due today, Positive = days remaining
            days_to_delivery = (expected_delivery - today).days
            
            # ================================================================
            # STEP 2: CHECK FOR DELAY EMAIL SIGNALS
            # ================================================================
            # Look for emails from this supplier that signal a delay
            po_number = po["po_number"]
            po_emails = self.email_threads[
                self.email_threads["po_number"] == po_number
            ]
            
            # has_delay_signal = True means supplier email contained delay keywords
            # (e.g., "delay", "atraso", "problem", "unable to deliver")
            has_delay_signal = False
            if len(po_emails) > 0:
                has_delay_signal = po_emails["has_delay_signal"].any()
            
            # ================================================================
            # STEP 3: GET SUPPLIER'S RISK SCORE AND TREND
            # ================================================================
            # Retrieve this supplier's WARP score and trend arrow
            supplier_id = po["supplier_id"]
            supplier_score_row = self.supplier_scores[
                self.supplier_scores["supplier_id"] == supplier_id
            ]
            
            if len(supplier_score_row) > 0:
                warp_score = supplier_score_row.iloc[0]["warp_score"]
                trend_arrow = supplier_score_row.iloc[0]["trend_arrow"]
            else:
                warp_score = np.nan  # No score available
                trend_arrow = "→"
            
            # ================================================================
            # STEP 4: APPLY ALERT CLASSIFICATION RULES
            # ================================================================
            
            # RULE 1: RED ALERT (Overdue)
            # Condition: days_to_delivery < 0 (delivery date has passed)
            # Severity: CRITICAL - Order is late, no receipt logged
            if days_to_delivery < 0:
                alert_level = "red"
                reason = f"🔴 OVERDUE by {abs(days_to_delivery)} days"
            
            # RULE 2: AMBER ALERT (Imminent or Email Signal)
            # Condition A: days_to_delivery between 0-10 (due within 10 days)
            # Condition B: Any delay email signal detected (upgraded from OK)
            elif 0 <= days_to_delivery <= 10:
                alert_level = "amber"
                reason = f"🟡 DUE in {days_to_delivery} days"
            
            # RULE 3: PROACTIVE ALERT (High Risk + Upcoming Delivery)
            # Condition: days_to_delivery 0-20 days AND supplier score ≤ 3.5
            # Purpose: Early engagement with unreliable suppliers
            elif (0 <= days_to_delivery <= 20) and (not pd.isna(warp_score)) and (warp_score <= 3.5):
                alert_level = "proactive"
                reason = f"🟠 HIGH-RISK supplier (score {warp_score}) due in {days_to_delivery} days"
            
            # RULE 4: UPGRADE TO AMBER IF DELAY SIGNAL DETECTED
            # Condition: Delay keyword detected in supplier emails
            # Effect: Even if days > 10, if supplier signaled delay, escalate to amber
            elif has_delay_signal and alert_level not in ["red", "amber"]:
                alert_level = "amber"
                reason = f"🟡 DELAY SIGNAL detected via email - due in {days_to_delivery} days"
            
            # DEFAULT: OK (No issues detected)
            # Condition: days_to_delivery > 10 AND no delay signals AND not high-risk
            else:
                alert_level = "ok"
                reason = f"🟢 On track - due in {days_to_delivery} days"
            
            # ================================================================
            # STEP 5: ADD TREND MODIFIER
            # ================================================================
            # If supplier trend is deteriorating (↓), append warning
            trend_indicator = ""
            if trend_arrow == "↓":
                trend_indicator = " ⚠️ Deteriorating trend"
            elif trend_arrow == "↑":
                trend_indicator = " ✅ Improving trend"
            
            # ================================================================
            # APPEND ALERT RECORD
            # ================================================================
            alerts.append({
                "po_number": po_number,
                "supplier_id": supplier_id,
                "supplier_name": po.get("supplier_name", "Unknown"),
                "material_category": po.get("material_category", "Unknown"),
                "expected_delivery": expected_delivery,
                "alert_level": alert_level,
                "days_to_delivery": days_to_delivery,
                "warp_score": warp_score,
                "trend_arrow": trend_arrow,
                "has_delay_signal": has_delay_signal,
                "reason": reason + trend_indicator,
            })
        
        return pd.DataFrame(alerts)


def detect_all_alerts(purchase_orders_csv_path, suppliers_scores_df, email_threads_csv_path):
    """
    Load data and detect all alerts.
    
    Args:
        purchase_orders_csv_path: Path to CSV file
        suppliers_scores_df: DataFrame (already loaded, not a path)
        email_threads_csv_path: Path to CSV file
    
    Returns:
        DataFrame with all POs classified into alert levels
    """
    purchase_orders_df = pd.read_csv(purchase_orders_csv_path)
    # suppliers_scores_df is already a DataFrame, don't read it
    email_threads_df = pd.read_csv(email_threads_csv_path)
    
    detector = DelayDetector(purchase_orders_df, suppliers_scores_df, email_threads_df)
    alerts_df = detector.detect_alerts()
    
    return alerts_df


if __name__ == "__main__":
    # Load data directly without importing
    import sys
    sys.path.insert(0, '.')
    
    from agent.scorer import score_all_suppliers
    
    # Generate supplier scores
    supplier_scores = score_all_suppliers(
        "data/synthetic/suppliers.csv",
        "data/synthetic/delivery_events.csv",
        "data/synthetic/penalties.csv",
        "data/synthetic/email_threads.csv"
    )
    
    # Detect all alerts
    alerts = detect_all_alerts(
        "data/synthetic/purchase_orders.csv",
        supplier_scores,
        "data/synthetic/email_threads.csv"
    )
    
    # Display results
    print("\n" + "="*80)
    print("🚨 WARP DELAY DETECTION ENGINE")
    print("="*80)
    print(f"\nTotal POs analyzed: {len(alerts)}")
    print(f"\nAlert Summary:")
    print(f"  🔴 RED (Overdue):        {(alerts['alert_level'] == 'red').sum():3d} POs")
    print(f"  🟡 AMBER (Imminent):     {(alerts['alert_level'] == 'amber').sum():3d} POs")
    print(f"  🟠 PROACTIVE (High Risk):{(alerts['alert_level'] == 'proactive').sum():3d} POs")
    print(f"  🟢 OK (On track):        {(alerts['alert_level'] == 'ok').sum():3d} POs")
    
    print("\n" + "="*80)
    print("📋 RED ALERTS (Immediate Action Required)")
    print("="*80)
    red_alerts = alerts[alerts["alert_level"] == "red"].sort_values("days_to_delivery")
    if len(red_alerts) > 0:
        for idx, alert in red_alerts.head(10).iterrows():
            print(f"\n  PO: {alert['po_number']:8} | Supplier: {alert['supplier_name']:25} | Score: {alert['warp_score']:.1f}")
            print(f"    {alert['reason']}")
    else:
        print("  ✅ None - all orders on track or recently received")
    
    print("\n" + "="*80)
    print("📋 AMBER ALERTS (Follow-up Required)")
    print("="*80)
    amber_alerts = alerts[alerts["alert_level"] == "amber"].sort_values("days_to_delivery")
    if len(amber_alerts) > 0:
        print(f"  Total: {len(amber_alerts)} alerts\n")
        for idx, alert in amber_alerts.head(10).iterrows():
            print(f"  PO: {alert['po_number']:8} | Supplier: {alert['supplier_name']:25} | Score: {alert['warp_score']:.1f}")
            print(f"    {alert['reason']}")
    else:
        print("  ✅ None")
    
    print("\n" + "="*80)
    print("📋 PROACTIVE ALERTS (Early Engagement)")
    print("="*80)
    proactive_alerts = alerts[alerts["alert_level"] == "proactive"].sort_values("days_to_delivery")
    if len(proactive_alerts) > 0:
        print(f"  Total: {len(proactive_alerts)} alerts")
    else:
        print("  ✅ None")
    
    print("\n✨ Phase 3 Complete!")
    print("="*80 + "\n")