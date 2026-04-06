"""
WARP Supplier Scoring Engine - WITH COMPREHENSIVE COMMENTS
Computes WARP Risk Score (1–10) for each supplier based on delivery history.

SCORING METHODOLOGY:
The WARP Risk Score combines 6 weighted dimensions into a single 1-10 score.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SupplierScorer:
    """Compute WARP Risk Score for suppliers"""
    
    def __init__(self, delivery_events_df, penalties_df, email_threads_df):
        self.delivery_events = delivery_events_df
        self.penalties = penalties_df
        self.email_threads = email_threads_df
        
    def compute_scores(self, suppliers_df):
        """Compute WARP Risk Score for all suppliers."""
        scores = []
        
        for supplier_id, supplier_name in zip(suppliers_df["supplier_id"], suppliers_df["supplier_name"]):
            # Get all delivery events for this supplier
            supplier_events = self.delivery_events[self.delivery_events["supplier_id"] == supplier_id]
            
            # Check if we have enough data (≥5 events required)
            if len(supplier_events) < 5:
                scores.append({
                    "supplier_id": supplier_id,
                    "supplier_name": supplier_name,
                    "warp_score": np.nan,
                    "trend_arrow": "N/A",
                    "sufficient_data": False,
                    "num_events": len(supplier_events)
                })
                continue
            
            # ====== DIMENSION 1: On-time Delivery Rate (35% weight) ======
            # What: Percentage of orders delivered exactly on time
            # How: Count orders where delay_days = 0, divide by total
            # Example: 180 on-time out of 200 orders = 90% = score 0.9
            on_time_count = (supplier_events["delay_days"] == 0).sum()
            total_count = len(supplier_events)
            on_time_rate = on_time_count / total_count
            dim1_normalized = on_time_rate  # Already [0, 1]
            
            # ====== DIMENSION 2: Average Delay Severity (20% weight) ======
            # What: How many days late when delays occur
            # How: Average delay_days for only the late orders
            # Example: Late orders were 3, 5, 2, 7 days late → avg = 4.25 days
            # Normalized: 1 - (4.25/30) = 0.858 (higher is better)
            late_events = supplier_events[supplier_events["delay_days"] > 0]
            if len(late_events) > 0:
                avg_delay_days = late_events["delay_days"].mean()
                # Normalize: assume 30 days is maximum acceptable delay
                # 0 days → 1.0 (best), 30 days → 0.0 (worst)
                dim2_normalized = 1 - min(avg_delay_days / 30, 1.0)
            else:
                dim2_normalized = 1.0  # Perfect score if never late
            
            # ====== DIMENSION 3: Penalty History (15% weight) ======
            # What: Count of OTIF penalties this supplier triggered
            # How: Match supplier's POs in penalty history
            # Example: 3 penalties → 1 - (3/10) = 0.7 normalized score
            supplier_po_numbers = self.delivery_events[
                self.delivery_events["supplier_id"] == supplier_id
            ]["event_date"].unique()
            supplier_penalties = self.penalties[self.penalties["po_number"].isin(supplier_po_numbers)]
            penalty_count = len(supplier_penalties)
            # Normalize: assume 10 penalties is worst case
            dim3_normalized = 1 - min(penalty_count / 10, 1.0)
            
            # ====== DIMENSION 4: Last-Minute Notification Rate (15% weight) ======
            # What: How often supplier notifies us of delays with short notice
            # How: Count emails with delay_signal = True, divide by total emails
            # Example: 8 out of 20 emails signal delay → 40% = 1 - 0.4 = 0.6 score
            supplier_emails = self.email_threads[self.email_threads["supplier_id"] == supplier_id]
            if len(supplier_emails) > 0:
                delay_signal_count = supplier_emails["has_delay_signal"].sum()
                last_minute_rate = delay_signal_count / len(supplier_emails)
                # Inverse: more delays = lower score
                dim4_normalized = 1 - last_minute_rate
            else:
                dim4_normalized = 1.0  # No emails = assume good
            
            # ====== DIMENSION 5: Email Responsiveness (10% weight) ======
            # What: How frequently the supplier communicates
            # How: Use email count as proxy (more = more engaged)
            # Example: 15 emails → min(15/10, 1.0) = 1.0 score
            if len(supplier_emails) > 0:
                email_count = len(supplier_emails)
                # Normalize: 10+ emails = excellent communication
                dim5_normalized = min(email_count / 10, 1.0)
            else:
                dim5_normalized = 0.5  # Uncertain
            
            # ====== DIMENSION 6: Trend Arrow (5% weight) ======
            # What: Is supplier improving (↑), stable (→), or declining (↓)?
            # How: Compare last 90-day on-time rate vs prior 90-day rate
            # Example: Last 90d = 95%, Prior 90d = 85% → +10pp = improving (↑)
            today = datetime.now().date()
            last_90_events = supplier_events[
                pd.to_datetime(supplier_events["event_date"]).dt.date >= (today - timedelta(days=90))
            ]
            prior_90_events = supplier_events[
                (pd.to_datetime(supplier_events["event_date"]).dt.date >= (today - timedelta(days=180)))
                & (pd.to_datetime(supplier_events["event_date"]).dt.date < (today - timedelta(days=90)))
            ]
            
            if len(last_90_events) > 0 and len(prior_90_events) > 0:
                last_90_on_time = (last_90_events["delay_days"] == 0).sum() / len(last_90_events)
                prior_90_on_time = (prior_90_events["delay_days"] == 0).sum() / len(prior_90_events)
                trend_delta = last_90_on_time - prior_90_on_time
                
                if trend_delta > 0.05:  # Improved >5pp
                    trend_arrow = "↑"
                    dim6_normalized = 1.0
                elif trend_delta < -0.05:  # Deteriorated >5pp
                    trend_arrow = "↓"
                    dim6_normalized = 0.0
                else:  # Stable
                    trend_arrow = "→"
                    dim6_normalized = 0.5
            else:
                trend_arrow = "→"
                dim6_normalized = 0.5
            
            # ====== WEIGHTED SUM ======
            # Multiply each normalized dimension [0, 1] by its weight
            # All weights sum to 1.0 (100%)
            weights = {
                "on_time_rate": 0.35,
                "avg_delay": 0.20,
                "penalties": 0.15,
                "last_minute": 0.15,
                "email_reply": 0.10,
                "trend": 0.05,
            }
            
            weighted_sum = (
                dim1_normalized * weights["on_time_rate"] +
                dim2_normalized * weights["avg_delay"] +
                dim3_normalized * weights["penalties"] +
                dim4_normalized * weights["last_minute"] +
                dim5_normalized * weights["email_reply"] +
                dim6_normalized * weights["trend"]
            )
            
            # ====== FINAL SCORE SCALING ======
            # Convert weighted_sum from [0, 1] to [1.0, 10.0]
            # Formula: (weighted_sum * 9 + 1)
            # 0.0 → 1.0 (worst), 0.5 → 5.5 (medium), 1.0 → 10.0 (best)
            warp_score = round((weighted_sum * 9 + 1), 1)
            
            scores.append({
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "warp_score": warp_score,
                "trend_arrow": trend_arrow,
                "sufficient_data": True,
                "num_events": len(supplier_events),
            })
        
        return pd.DataFrame(scores)


def score_all_suppliers(suppliers_csv_path, delivery_events_csv_path, 
                        penalties_csv_path, email_threads_csv_path):
    """Load data and compute scores for all suppliers."""
    suppliers_df = pd.read_csv(suppliers_csv_path)
    delivery_events_df = pd.read_csv(delivery_events_csv_path)
    penalties_df = pd.read_csv(penalties_csv_path)
    email_threads_df = pd.read_csv(email_threads_csv_path)
    
    scorer = SupplierScorer(delivery_events_df, penalties_df, email_threads_df)
    scores_df = scorer.compute_scores(suppliers_df)
    
    return scores_df


if __name__ == "__main__":
    scores = score_all_suppliers(
        "data/synthetic/suppliers.csv",
        "data/synthetic/delivery_events.csv",
        "data/synthetic/penalties.csv",
        "data/synthetic/email_threads.csv"
    )
    
    print("\n" + "="*70)
    print("📊 WARP SUPPLIER SCORING ENGINE")
    print("="*70)
    print(f"\nTotal suppliers scored: {len(scores)}")
    print(f"With sufficient data (≥5 events): {scores['sufficient_data'].sum()}")
    print(f"With insufficient data (N/A): {(~scores['sufficient_data']).sum()}")
    
    print("\n🔴 HIGH RISK (Score < 3.0):")
    high_risk = scores[scores["warp_score"] < 3.0].sort_values("warp_score")
    if len(high_risk) > 0:
        for idx, row in high_risk.iterrows():
            print(f"  {row['supplier_name']:30} | Score: {row['warp_score']}/10 {row['trend_arrow']}")
    else:
        print("  None")
    
    print("\n🟡 MEDIUM RISK (Score 3.0 – 6.0):")
    medium_risk = scores[(scores["warp_score"] >= 3.0) & (scores["warp_score"] <= 6.0)].sort_values("warp_score")
    if len(medium_risk) > 0:
        print(f"  {len(medium_risk)} suppliers in this range")
    else:
        print("  None")
    
    print("\n🟢 LOW RISK (Score > 6.0):")
    low_risk = scores[scores["warp_score"] > 6.0].sort_values("warp_score", ascending=False)
    if len(low_risk) > 0:
        print(f"  {len(low_risk)} suppliers in this range")
    else:
        print("  None")
    
    print("\n📈 SCORE STATISTICS:")
    valid_scores = scores[scores["sufficient_data"]]["warp_score"]
    print(f"  Mean score: {valid_scores.mean():.1f}")
    print(f"  Min score: {valid_scores.min():.1f}")
    print(f"  Max score: {valid_scores.max():.1f}")
    print(f"  Median score: {valid_scores.median():.1f}")
    
    print("\n✨ Phase 2 Complete!")
    print("="*70 + "\n")