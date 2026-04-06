"""
WARP Synthetic Data Generator
Generates 6 CSV files for Piubelle procurement simulation:
- suppliers.csv (200 suppliers)
- purchase_orders.csv (400 POs with delivery dates and status)
- delivery_events.csv (18 months of delivery history ~4800 events)
- email_threads.csv (supplier communication threads ~120)
- penalties.csv (OTIF penalty history ~25)
- airfreight_incidents.csv (air freight cost incidents ~15)

Run: python data/generate_data.py
Output: data/synthetic/*.csv
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os

# Set seed for reproducibility across all team members
random.seed(42)
np.random.seed(42)
Faker.seed(42)
fake = Faker()

# Configuration
NUM_SUPPLIERS = 200
NUM_POS = 400
SYNTHETIC_DIR = "data/synthetic"

# Material categories (4 buyers)
MATERIAL_CATEGORIES = ["Raw Materials", "Weaving", "Cutting", "Sewing", "Finishing"]
BUYER_NAMES = ["Ana Silva", "João Santos", "Maria Costa", "Pedro Oliveira"]

# Supplier countries
COUNTRIES = ["Portugal", "Spain", "Italy", "Turkey", "India", "China", "Vietnam"]

# ============================================================================
# 1. GENERATE SUPPLIERS.CSV
# ============================================================================
def generate_suppliers(n=NUM_SUPPLIERS):
    """Generate supplier master data"""
    suppliers = []
    for i in range(n):
        supplier = {
            "supplier_id": f"SUP{i+1:04d}",
            "supplier_name": fake.company(),
            "country": random.choice(COUNTRIES),
            "material_category": random.choice(MATERIAL_CATEGORIES),
            "contact_email": fake.email(),
            "contact_phone": fake.phone_number(),
            "onboarded_date": (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime("%Y-%m-%d"),
            "risk_score_initial": round(random.uniform(1.0, 10.0), 1),
        }
        suppliers.append(supplier)
    
    df = pd.DataFrame(suppliers)
    df.to_csv(f"{SYNTHETIC_DIR}/suppliers.csv", index=False)
    print(f"✓ Generated suppliers.csv ({len(df)} rows)")
    return df

# ============================================================================
# 2. GENERATE PURCHASE_ORDERS.CSV
# ============================================================================
def generate_purchase_orders(suppliers_df, n=NUM_POS):
    """Generate open POs with delivery dates and status"""
    pos = []
    today = datetime.now().date()
    
    for i in range(n):
        supplier_id = suppliers_df.sample(1)["supplier_id"].values[0]
        supplier_name = suppliers_df[suppliers_df["supplier_id"] == supplier_id]["supplier_name"].values[0]
        
        # PO date in the past (last 180 days)
        po_date = today - timedelta(days=random.randint(1, 180))
        
        # Expected delivery in near future or past
        days_to_delivery = random.randint(-30, 60)  # -30 (overdue) to +60 (future)
        expected_delivery = today + timedelta(days=days_to_delivery)
        
        # Determine alert status based on days to delivery and randomness
        if days_to_delivery < 0:
            status = "red"  # Overdue
        elif 0 <= days_to_delivery <= 10:
            status = random.choice(["amber", "amber", "on_track"])  # Bias towards amber
        elif 11 <= days_to_delivery <= 20:
            status = random.choice(["amber", "on_track", "on_track"])
        else:
            status = "on_track"
        
        po = {
            "po_number": f"PO{i+1:05d}",
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "material_category": suppliers_df[suppliers_df["supplier_id"] == supplier_id]["material_category"].values[0],
            "po_date": po_date.strftime("%Y-%m-%d"),
            "expected_delivery": expected_delivery.strftime("%Y-%m-%d"),
            "item_code": f"ITEM{random.randint(1000, 9999)}",
            "quantity": random.randint(100, 5000),
            "status": status,
            "goods_receipt_date": None,  # No receipt yet (open POs)
        }
        pos.append(po)
    
    df = pd.DataFrame(pos)
    df.to_csv(f"{SYNTHETIC_DIR}/purchase_orders.csv", index=False)
    print(f"✓ Generated purchase_orders.csv ({len(df)} rows)")
    print(f"  Status distribution: {df['status'].value_counts().to_dict()}")
    return df

# ============================================================================
# 3. GENERATE DELIVERY_EVENTS.CSV
# ============================================================================
def generate_delivery_events(suppliers_df, pos_df):
    """Generate 18 months of delivery history for scoring"""
    events = []
    today = datetime.now().date()
    
    # Generate ~24 events per supplier on average (18 months)
    for supplier in suppliers_df.itertuples():
        num_events = random.randint(5, 50)
        
        for _ in range(num_events):
            # Event date in the past 18 months
            event_date = today - timedelta(days=random.randint(1, 540))
            
            # Expected delivery was typically 30-60 days before event
            expected_delivery = event_date - timedelta(days=random.randint(30, 60))
            
            # Delay days (mostly 0, occasionally positive)
            if random.random() < 0.75:  # 75% on-time
                delay_days = 0
            else:  # 25% late
                delay_days = random.randint(1, 30)
            
            event = {
                "supplier_id": supplier.supplier_id,
                "supplier_name": supplier.supplier_name,
                "event_date": event_date.strftime("%Y-%m-%d"),
                "expected_delivery": expected_delivery.strftime("%Y-%m-%d"),
                "actual_delivery": (event_date + timedelta(days=delay_days)).strftime("%Y-%m-%d"),
                "delay_days": delay_days,
                "quantity_delivered": random.randint(80, 100),  # % of ordered
                "material_category": supplier.material_category,
            }
            events.append(event)
    
    df = pd.DataFrame(events)
    df.to_csv(f"{SYNTHETIC_DIR}/delivery_events.csv", index=False)
    print(f"✓ Generated delivery_events.csv ({len(df)} rows)")
    return df

# ============================================================================
# 4. GENERATE EMAIL_THREADS.CSV
# ============================================================================
def generate_email_threads(suppliers_df, pos_df):
    """Generate supplier email communication threads"""
    threads = []
    today = datetime.now().date()
    
    # ~120 email threads
    num_threads = min(120, len(pos_df))
    sample_pos = pos_df.sample(n=num_threads, random_state=42)
    
    delay_keywords = [
        "delay", "atraso", "postpone", "problema", "issue", "unable to deliver by",
        "unexpected", "rescheduled", "later than", "cannot guarantee", "difficult",
    ]
    
    for idx, po in sample_pos.iterrows():
        # Email date recent (last 30 days)
        email_date = today - timedelta(days=random.randint(1, 30))
        
        # Decide if this email signals a delay
        is_delay_signal = random.random() < 0.4  # 40% of emails signal delay
        
        if is_delay_signal:
            subject = f"UPDATE: {po['po_number']} - {random.choice(delay_keywords)}"
            body = f"Supplier {po['supplier_name']} has indicated a potential {random.choice(delay_keywords)} on {po['po_number']}"
        else:
            subject = f"RE: {po['po_number']} - Status Update"
            body = f"On schedule for delivery of {po['po_number']} as planned."
        
        thread = {
            "po_number": po["po_number"],
            "supplier_id": po["supplier_id"],
            "supplier_name": po["supplier_name"],
            "email_date": email_date.strftime("%Y-%m-%d"),
            "subject": subject,
            "body": body,
            "sender": "supplier",
            "has_delay_signal": is_delay_signal,
        }
        threads.append(thread)
    
    df = pd.DataFrame(threads)
    df.to_csv(f"{SYNTHETIC_DIR}/email_threads.csv", index=False)
    print(f"✓ Generated email_threads.csv ({len(df)} rows)")
    return df

# ============================================================================
# 5. GENERATE PENALTIES.CSV
# ============================================================================
def generate_penalties():
    """Generate OTIF penalty history"""
    penalties = []
    today = datetime.now().date()
    
    # ~25 penalties
    for i in range(25):
        penalty_date = today - timedelta(days=random.randint(30, 365))
        
        penalty = {
            "penalty_id": f"PEN{i+1:03d}",
            "po_number": f"PO{random.randint(1, 400):05d}",
            "penalty_date": penalty_date.strftime("%Y-%m-%d"),
            "penalty_reason": random.choice(["Late delivery", "Incomplete shipment", "Quality issue", "Wrong item"]),
            "penalty_amount_eur": round(random.uniform(500, 5000), 2),
            "customer": random.choice(["US Retailer A", "EU Distributor B", "UK Importer C", "Wholesaler D"]),
        }
        penalties.append(penalty)
    
    df = pd.DataFrame(penalties)
    df.to_csv(f"{SYNTHETIC_DIR}/penalties.csv", index=False)
    print(f"✓ Generated penalties.csv ({len(df)} rows)")
    return df

# ============================================================================
# 6. GENERATE AIRFREIGHT_INCIDENTS.CSV
# ============================================================================
def generate_airfreight_incidents():
    """Generate air freight cost incidents"""
    incidents = []
    today = datetime.now().date()
    
    # ~15 air freight incidents
    for i in range(15):
        incident_date = today - timedelta(days=random.randint(30, 365))
        
        incident = {
            "incident_id": f"AIR{i+1:03d}",
            "po_number": f"PO{random.randint(1, 400):05d}",
            "incident_date": incident_date.strftime("%Y-%m-%d"),
            "reason": random.choice(["Delayed sea shipment", "Urgent order", "Lost container", "Port strike"]),
            "airfreight_cost_eur": round(random.uniform(2000, 15000), 2),
            "original_delivery_date": (incident_date - timedelta(days=random.randint(5, 30))).strftime("%Y-%m-%d"),
            "actual_delivery_date": incident_date.strftime("%Y-%m-%d"),
        }
        incidents.append(incident)
    
    df = pd.DataFrame(incidents)
    df.to_csv(f"{SYNTHETIC_DIR}/airfreight_incidents.csv", index=False)
    print(f"✓ Generated airfreight_incidents.csv ({len(df)} rows)")
    return df

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    # Create synthetic directory if it doesn't exist
    os.makedirs(SYNTHETIC_DIR, exist_ok=True)
    
    print("\n" + "="*70)
    print("🚀 WARP SYNTHETIC DATA GENERATOR")
    print("="*70)
    print(f"Generating Piubelle procurement data...")
    print(f"Seed: 42 (reproducible across all machines)\n")
    
    # Generate all files
    suppliers_df = generate_suppliers(NUM_SUPPLIERS)
    pos_df = generate_purchase_orders(suppliers_df, NUM_POS)
    delivery_events_df = generate_delivery_events(suppliers_df, pos_df)
    email_threads_df = generate_email_threads(suppliers_df, pos_df)
    penalties_df = generate_penalties()
    airfreight_df = generate_airfreight_incidents()
    
    print("\n" + "="*70)
    print("✅ DONE. Files in data/synthetic/")
    print("="*70)
    print(f"  Suppliers:          {len(suppliers_df)} rows")
    print(f"  Purchase Orders:    {len(pos_df)} rows")
    print(f"  Delivery Events:    {len(delivery_events_df)} rows")
    print(f"  Email Threads:      {len(email_threads_df)} rows")
    print(f"  Penalties:          {len(penalties_df)} rows")
    print(f"  Air Freight:        {len(airfreight_df)} rows")
    print("="*70)
    
    # Spot-check: Alert distribution
    print("\n📊 ALERT DISTRIBUTION CHECK:")
    print(f"  Red alerts:    {(pos_df['status'] == 'red').sum()} (target: >= 5)")
    print(f"  Amber alerts:  {(pos_df['status'] == 'amber').sum()} (target: >= 10)")
    print(f"  On-track:      {(pos_df['status'] == 'on_track').sum()}")
    
    # Spot-check: Score range
    print("\n📈 DELIVERY PERFORMANCE CHECK:")
    on_time_rate = (delivery_events_df['delay_days'] == 0).sum() / len(delivery_events_df)
    print(f"  Overall on-time rate: {on_time_rate*100:.1f}% (target: ~75%)")
    print(f"  Total penalties: €{penalties_df['penalty_amount_eur'].sum():,.2f}")
    print(f"  Total air freight: €{airfreight_df['airfreight_cost_eur'].sum():,.2f}")
    
    print("\n✨ Ready for Phase 2: Supplier Scoring Engine")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
    
  
""" suppliers = pd.read_csv("data/synthetic/suppliers.csv")
print("Suppliers by Category:")
print(suppliers["category"].value_counts())

# Should show ~25 suppliers per category (200 / 8 categories)

emails = pd.read_csv("data/synthetic/email_threads.csv")
print(f"Total email threads: {len(emails)}")
print(f"With delay keyword: {emails['has_delay_keyword'].sum()}")
# Should show ~40–50 threads with delay signals """