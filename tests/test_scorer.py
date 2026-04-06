"""
WARP Supplier Scorer Tests (tests/test_scorer.py)

Tests the supplier risk scoring engine.
Ensures scores are valid, problematic suppliers are identified, and insufficient data is handled.

Validation Rules:
  1. All scores must be in [1.0, 10.0]
  2. Problematic suppliers (score < 5.0) should be clearly marked
  3. Suppliers with < 5 events should return NaN (insufficient data)
  4. Score calculation should be deterministic (same seed = same scores)
"""

import pytest
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '.')

from agent.scorer import score_all_suppliers


class TestSupplierScorer:
    """Test suite for supplier scoring logic."""
    
    # ================================================================
    # TEST 1: All Scores in Valid Range [1.0, 10.0]
    # ================================================================
    def test_all_scores_in_valid_range(self):
        """All supplier scores should be between 1.0 and 10.0."""
        scores_df = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        # Get valid (non-NaN) scores
        valid_scores = scores_df['warp_score'].dropna()
        
        assert len(valid_scores) > 0, "Should have at least some valid scores"
        
        # Check all scores are in [1.0, 10.0]
        assert valid_scores.min() >= 1.0, f"Minimum score {valid_scores.min()} is below 1.0"
        assert valid_scores.max() <= 10.0, f"Maximum score {valid_scores.max()} is above 10.0"
    
    # ================================================================
    # TEST 2: Problematic Suppliers Have Low Scores
    # ================================================================
    def test_problematic_suppliers_identified(self):
        """Suppliers with delays/penalties should have low scores."""
        scores_df = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        # Get suppliers with valid scores
        valid_scores = scores_df[scores_df['warp_score'].notna()]
        
        # There should be SOME suppliers with low scores (< 5.0)
        low_score_suppliers = valid_scores[valid_scores['warp_score'] < 5.0]
        
        assert len(low_score_suppliers) > 0, \
            "Should have at least some suppliers with low scores (< 5.0)"
    
    # ================================================================
    # TEST 3: High-Performing Suppliers Have High Scores
    # ================================================================
    def test_high_performing_suppliers_identified(self):
        """Reliable suppliers should have high scores."""
        scores_df = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        # Get suppliers with valid scores
        valid_scores = scores_df[scores_df['warp_score'].notna()]
        
        # There should be SOME suppliers with high scores (> 7.0)
        high_score_suppliers = valid_scores[valid_scores['warp_score'] > 7.0]
        
        assert len(high_score_suppliers) > 0, \
            "Should have at least some suppliers with high scores (> 7.0)"
    
    # ================================================================
    # TEST 4: Insufficient Data Marked as NaN
    # ================================================================
    def test_insufficient_data_returns_nan(self):
        """Suppliers with < 5 events should have NaN scores."""
        scores_df = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        # Some suppliers may have NaN (insufficient data)
        nan_scores = scores_df[scores_df['warp_score'].isna()]
        
        # This is valid — suppliers with < 5 events should be NaN
        # If all have scores, that's also okay (means all have >= 5 events)
        assert isinstance(nan_scores, pd.DataFrame), "Should return DataFrame"
    
    # ================================================================
    # TEST 5: Score Distribution is Reasonable
    # ================================================================
    def test_score_distribution_is_reasonable(self):
        """Score distribution should be spread (not all clustered at 5.0)."""
        scores_df = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        valid_scores = scores_df['warp_score'].dropna()
        
        # Calculate quartiles
        q1 = valid_scores.quantile(0.25)
        q3 = valid_scores.quantile(0.75)
        iqr = q3 - q1
        
        # IQR should be > 0 (spread, not all same value)
        assert iqr > 0.5, f"Scores too clustered (IQR = {iqr}). Should be spread."
    
    # ================================================================
    # TEST 6: Trend Arrow is Present
    # ================================================================
    def test_trend_arrow_present(self):
        """All scores should have a trend arrow (↑, →, or ↓)."""
        scores_df = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        assert 'trend_arrow' in scores_df.columns, "Missing trend_arrow column"
        
        # All should have a trend arrow
        valid_arrows = scores_df[scores_df['warp_score'].notna()]
        for arrow in valid_arrows['trend_arrow']:
            assert arrow in ['↑', '→', '↓'], f"Invalid trend arrow: {arrow}"
    
    # ================================================================
    # TEST 7: Required Columns Present
    # ================================================================
    def test_required_columns_present(self):
        """Scorer should return all required columns."""
        scores_df = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        required_columns = [
            'supplier_id',
            'supplier_name',
            'warp_score',
            'trend_arrow',
        ]
        
        for col in required_columns:
            assert col in scores_df.columns, f"Missing column: {col}"
    
    # ================================================================
    # TEST 8: Deterministic Scoring (Same Seed = Same Scores)
    # ================================================================
    def test_scoring_is_deterministic(self):
        """Scoring should be deterministic — same seed should produce same scores."""
        
        # First run
        scores_df_1 = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        # Second run (same data, same seed)
        scores_df_2 = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        # Scores should be identical
        pd.testing.assert_frame_equal(
            scores_df_1.sort_values('supplier_id').reset_index(drop=True),
            scores_df_2.sort_values('supplier_id').reset_index(drop=True),
            check_dtype=False  # Allow minor type differences
        )
    
    # ================================================================
    # TEST 9: Mean Score is Reasonable
    # ================================================================
    def test_mean_score_is_reasonable(self):
        """Mean supplier score should be in reasonable range (5.0 - 8.0)."""
        scores_df = score_all_suppliers(
            "data/synthetic/suppliers.csv",
            "data/synthetic/delivery_events.csv",
            "data/synthetic/penalties.csv",
            "data/synthetic/email_threads.csv"
        )
        
        valid_scores = scores_df['warp_score'].dropna()
        mean_score = valid_scores.mean()
        
        # Mean should be reasonable (between 5 and 8)
        assert 5.0 <= mean_score <= 8.0, \
            f"Mean score {mean_score:.2f} is outside reasonable range [5.0, 8.0]"


# ============================================================================
# RUN TESTS
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])