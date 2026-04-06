"""
WARP Delay Detector Tests (tests/test_delay_detector.py)

Tests boundary conditions for the delay detection engine.
These tests ensure that POs are classified correctly: Red / Amber / Proactive / OK

Boundary Cases to Test:
  1. PO due today → should be AMBER
  2. PO due in 10 days → should be AMBER
  3. PO due in 11 days, score > 3.5 → should be OK
  4. PO 1 day overdue → should be RED
  5. PO with delay email signal → should upgrade to AMBER
"""

import pytest
import pandas as pd
from datetime import date, timedelta
import sys
sys.path.insert(0, '.')

from agent.delay_detector import DelayDetector


class TestDelayDetector:
    """Test suite for delay detection logic."""
    
    @pytest.fixture
    def sample_data(self):
        """Create minimal sample data for testing."""
        
        # Minimal suppliers
        suppliers_df = pd.DataFrame({
            'supplier_id': [1, 2, 3, 4, 5],
            'supplier_name': ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D', 'Supplier E'],
            'material_category': ['Raw Materials'] * 5,
        })
        
        # Minimal POs with different delivery dates
        pos_df = pd.DataFrame({
            'po_number': ['PO001', 'PO002', 'PO003', 'PO004', 'PO005'],
            'supplier_id': [1, 2, 3, 4, 5],
            'expected_delivery': [
                date.today(),                    # PO001: Due today
                date.today() + timedelta(days=10),  # PO002: Due in 10 days
                date.today() + timedelta(days=11),  # PO003: Due in 11 days
                date.today() - timedelta(days=1),   # PO004: 1 day overdue
                date.today() + timedelta(days=5),   # PO005: Due in 5 days (for email signal test)
            ],
            'status': ['on_track'] * 5,
        })
        
        # Minimal scores (all high quality)
        scores_df = pd.DataFrame({
            'supplier_id': [1, 2, 3, 4, 5],
            'supplier_name': ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D', 'Supplier E'],
            'warp_score': [8.0, 8.5, 9.0, 7.5, 8.2],  # All > 3.5
            'trend_arrow': ['→', '→', '→', '→', '→'],
            'material_category': ['Raw Materials'] * 5,
        })
        
        # Minimal emails (no delay signals)
        emails_df = pd.DataFrame({
            'po_number': ['PO001', 'PO002', 'PO003', 'PO004', 'PO005'],
            'supplier_id': [1, 2, 3, 4, 5],
            'has_delay_signal': [False, False, False, False, False],
        })
        
        return suppliers_df, pos_df, scores_df, emails_df
    
    # ================================================================
    # TEST 1: PO Due Today → AMBER
    # ================================================================
    def test_po_due_today_is_amber(self, sample_data):
        """PO due today (0 days until delivery) should be AMBER."""
        suppliers_df, pos_df, scores_df, emails_df = sample_data
        
        detector = DelayDetector(pos_df, scores_df, emails_df)
        alerts_df = detector.detect_alerts()
        
        po001_alert = alerts_df[alerts_df['po_number'] == 'PO001']
        
        assert len(po001_alert) == 1, "PO001 should have an alert"
        assert po001_alert.iloc[0]['alert_level'] == 'amber', \
            f"PO due today should be AMBER, got {po001_alert.iloc[0]['alert_level']}"
    
    # ================================================================
    # TEST 2: PO Due in 10 Days → AMBER
    # ================================================================
    def test_po_due_in_10_days_is_amber(self, sample_data):
        """PO due in 10 days should be AMBER."""
        suppliers_df, pos_df, scores_df, emails_df = sample_data
        
        detector = DelayDetector(pos_df, scores_df, emails_df)
        alerts_df = detector.detect_alerts()
        
        po002_alert = alerts_df[alerts_df['po_number'] == 'PO002']
        
        assert len(po002_alert) == 1, "PO002 should have an alert"
        assert po002_alert.iloc[0]['alert_level'] == 'amber', \
            f"PO due in 10 days should be AMBER, got {po002_alert.iloc[0]['alert_level']}"
    
    # ================================================================
    # TEST 3: PO Due in 11 Days, High Score → OK
    # ================================================================
    def test_po_due_in_11_days_high_score_is_ok(self, sample_data):
        """PO due in 11 days with high score (>3.5) should be OK."""
        suppliers_df, pos_df, scores_df, emails_df = sample_data
        
        detector = DelayDetector(pos_df, scores_df, emails_df)
        alerts_df = detector.detect_alerts()
        
        po003_alert = alerts_df[alerts_df['po_number'] == 'PO003']
        
        # Should still be in alerts (to show all POs)
        # but status should be OK
        if len(po003_alert) > 0:
            assert po003_alert.iloc[0]['alert_level'] == 'ok', \
                f"PO due in 11 days with high score should be OK, got {po003_alert.iloc[0]['alert_level']}"
    
    # ================================================================
    # TEST 4: PO Overdue (1 day past) → RED
    # ================================================================
    def test_po_overdue_is_red(self, sample_data):
        """PO 1 day overdue should be RED."""
        suppliers_df, pos_df, scores_df, emails_df = sample_data
        
        detector = DelayDetector(pos_df, scores_df, emails_df)
        alerts_df = detector.detect_alerts()
        
        po004_alert = alerts_df[alerts_df['po_number'] == 'PO004']
        
        assert len(po004_alert) == 1, "PO004 (overdue) should have an alert"
        assert po004_alert.iloc[0]['alert_level'] == 'red', \
            f"Overdue PO should be RED, got {po004_alert.iloc[0]['alert_level']}"
    
    # ================================================================
    # TEST 5: PO with Delay Email Signal → AMBER or Higher
    # ================================================================
    def test_delay_email_signal_upgrades_to_amber(self, sample_data):
        """PO with delay email signal should be upgraded to AMBER or higher."""
        suppliers_df, pos_df, scores_df, emails_df = sample_data
        
        # Modify PO005 to have a delay email signal
        emails_df.loc[emails_df['po_number'] == 'PO005', 'has_delay_signal'] = True
        
        detector = DelayDetector(pos_df, scores_df, emails_df)
        alerts_df = detector.detect_alerts()
        
        po005_alert = alerts_df[alerts_df['po_number'] == 'PO005']
        
        assert len(po005_alert) == 1, "PO005 should have an alert"
        alert_level = po005_alert.iloc[0]['alert_level']
        
        # Should be at least AMBER (or higher like RED)
        assert alert_level in ['red', 'amber'], \
            f"PO with delay signal should be RED or AMBER, got {alert_level}"
    
    # ================================================================
    # TEST 6: All Alerts Have Required Fields
    # ================================================================
    def test_alerts_have_required_fields(self, sample_data):
        """All alerts should have required fields."""
        suppliers_df, pos_df, scores_df, emails_df = sample_data
        
        detector = DelayDetector(pos_df, scores_df, emails_df)
        alerts_df = detector.detect_alerts()
        
        required_fields = ['po_number', 'supplier_id', 'alert_level', 'days_to_delivery', 'reason']
        
        for field in required_fields:
            assert field in alerts_df.columns, f"Missing required field: {field}"
        
        # All alerts should have non-null values in required fields
        for field in required_fields:
            assert alerts_df[field].notna().all(), f"Field {field} has null values"


# ============================================================================
# RUN TESTS
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])