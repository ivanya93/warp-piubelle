# WARP Supplier Risk Score — Complete Technical Guide

## Overview

The **WARP Risk Score** (1–10) quantifies supplier reliability across six dimensions. A score of **1** = highest risk, **10** = most reliable.

---

## The 6 Scoring Dimensions

| Dimension | Weight | Measure | Why It Matters |
|-----------|--------|---------|---|
| **On-time Delivery Rate** | 35% | % of orders delivered by promised date (12-month rolling) | Primary KPI in procurement |
| **Average Delay Duration** | 20% | Days late when delays occur | Financial impact (air freight, penalties) |
| **Penalty History** | 15% | Count of OTIF penalties in last 12m | Accountability signal |
| **Last-Minute Notifications** | 15% | % of deliveries confirmed < 5 days before | Planning visibility |
| **Email Responsiveness** | 10% | Average hours to respond to supplier emails | Communication reliability |
| **Trend** | 5% | Change in on-time rate (last 90d vs prior 90d) | Direction signal |

---

## Calculation Steps

### **Step 1: Normalize Each Dimension to [0, 1]**

Each raw value is independently scaled to a 0–1 range before weighting. This prevents high-range values (e.g., email reply time: 1–120 hours) from dominating lower-range values (e.g., penalty count: 0–5).

**Example normalization:**
```
On-time rate:        87% → 0.87 (already 0–1)
Avg delay:           6 days → 0.4 (normalized: 6/15 max days)
Penalty count:       2 → 0.6 (normalized: 2/3 max penalties)
Last-minute rate:    22% → 0.78 (normalized: 22/100%)
Email response:      18 hours → 0.85 (normalized: 1 - 18/120 max hours)
Trend:               +7pp improvement → 0.9 (normalized change)
```

### **Step 2: Apply Weights**

Multiply each normalized dimension by its weight, then sum:

```
weighted_sum = (0.87 × 0.35) + (0.4 × 0.20) + (0.6 × 0.15) 
             + (0.78 × 0.15) + (0.85 × 0.10) + (0.9 × 0.05)
             
           = 0.305 + 0.08 + 0.09 + 0.117 + 0.085 + 0.045
           = 0.722
```

### **Step 3: Scale to [1.0, 10.0]**

Map the weighted sum (0–1) to the final score range (1–10):

```
final_score = (weighted_sum × 9) + 1
            = (0.722 × 9) + 1
            = 6.498
            = 6.5 (rounded to 1 decimal place)
```

**Result:** Supplier scores **6.5/10** ✓

---

## Trend Arrow

After calculating the base score, a **trend indicator** is added:

| Trend | Condition | Display |
|-------|-----------|---------|
| **↑ Improving** | On-time rate improved > 5 percentage points in last 90 days | 6.5 ↑ |
| **↓ Deteriorating** | On-time rate fell > 5 percentage points in last 90 days | 6.5 ↓ |
| **→ Stable** | Change ≤ 5 percentage points | 6.5 → |

---

## Special Cases

### **Insufficient Data (< 5 Events)**
Suppliers with fewer than 5 historical delivery events return **N/A** instead of a score.

**Why:** Not enough data for reliable scoring. Prevents new suppliers from appearing artificially high or low.

```python
if delivery_events < 5:
    score = NaN  # Display as "N/A" in UI
    exclude_from_ranking = True
```

### **Data Quality Issues**
Missing email reply times → Use 0 contribution (skip dimension, don't penalize)  
No penalty history → Assume 0 penalties (positive signal)

---

## Interpretation Guide

| Score | Risk Level | Recommended Action |
|-------|----------|---|
| **9.0–10.0** | ✅ Excellent | Standard monitoring; trust shipments |
| **7.0–8.9** | ✅ Good | Normal follow-up; routine communication |
| **5.0–6.9** | ⚠️ Moderate | Monitor closely; escalate Amber alerts |
| **3.0–4.9** | 🟠 High Risk | Proactive follow-up; consider alternatives |
| **1.0–2.9** | 🔴 Critical | Escalation required; evaluate relationship |
| **N/A** | ❓ Unscored | Insufficient history; evaluate manually |

---

## Example Supplier Profiles

### **Reliable Supplier (Score: 8.5 ↑)**
- On-time rate: 95% (strong)
- Avg delay: 1 day when late (minimal impact)
- Penalties: 0 in last 12m
- Email response: 4 hours (excellent)
- Last-minute notices: 8% (good)
- Trend: Improving (+6pp) ↑
- **Action:** Standard monitoring; low risk

### **Problem Supplier (Score: 2.8 ↓)**
- On-time rate: 62% (weak)
- Avg delay: 14 days when late (expensive)
- Penalties: 3 in last 12m (pattern)
- Email response: 72 hours (slow)
- Last-minute notices: 35% (disruptive)
- Trend: Deteriorating (-8pp) ↓
- **Action:** Escalation required; consider alternatives

---

## 🔍 Alternative Supplier Search (GDPR-Compliant)

When a supplier is underperforming (score < 3.5 or 3+ Red alerts in 90 days), WARP can help identify alternative suppliers while respecting **GDPR and EU AI Act** requirements.

### **What WARP Collects (✅ Allowed)**

WARP searches **publicly available corporate information only**:

| Data Type | Examples | Status |
|-----------|----------|--------|
| **Company name** | "Supplier Ltd", "ABC Manufacturing SA" | ✅ Collect |
| **Business email** | "sales@supplier.pt", "contact@company.com" | ✅ Collect |
| **Business phone** | "+351 22 XXXX XXXX" (company main line) | ✅ Collect |
| **Company website** | "www.supplier.com", "www.company.pt" | ✅ Collect |
| **Industry classification** | "Textile Manufacturing", "Raw Materials" | ✅ Collect |
| **Business address** | "Rua X, Porto, Portugal" | ✅ Collect |

### **What WARP Does NOT Collect (🚫 Forbidden)**

WARP explicitly avoids personal data:

| Data Type | Examples | Status |
|-----------|----------|--------|
| **Personal emails** | "john.doe@gmail.com", personal account | 🚫 Never |
| **Personal phone** | "+(351) 91 XXX XXXX" (mobile numbers) | 🚫 Never |
| **Individual names** | Specific procurement officer / buyer names | 🚫 Avoid |
| **LinkedIn personal profiles** | Individual employee profiles | 🚫 Never |
| **WhatsApp / personal contacts** | Non-business messaging | 🚫 Never |
| **Internal decision-makers** | Specific people involved in negotiations | 🚫 Minimize |

---

### **Search Sources (All Public)**

WARP searches these **publicly available** resources:

1. **Company Websites** — Official contact pages, procurement info
2. **Industry Directories** — Textile trade associations (ATEX, AICEP)
3. **B2B Databases** — Kompass, Trade registries (public records)
4. **LinkedIn Company Pages** — Only official company accounts, not personal profiles
5. **Government Trade Registries** — Chamber of Commerce, business registrations (public)

### **Prohibited Sources**

❌ Personal social media (Facebook, Instagram, Twitter)  
❌ Email scraping or reverse lookup tools  
❌ Internal company networks or leaked databases  
❌ Third-party data brokers without transparent consent  

---

### **How to Use Alternative Supplier Search**

**Buyer initiates request:**
```
"Find alternative suppliers for Weaving in Portugal"
```

**WARP returns:**
```
1. Supplier Name: ABC Textiles
   Industry: Cotton Weaving
   Location: Maia, Portugal
   Business Email: contact@abctextiles.pt
   Business Phone: +351 22 123 4567
   Website: www.abctextiles.pt
   
2. Supplier Name: Luso Fabrics
   Industry: Synthetic Weaving
   Location: Braga, Portugal
   Business Email: sales@lusofabrics.pt
   Business Phone: +351 25 876 5432
   Website: www.lusofabrics.pt
```

**Buyer decides:**
- Review suppliers independently
- Contact through official channels
- Evaluate capacity, pricing, quality
- Decide whether to pilot or switch

**WARP never:**
- Sends unsolicited contact on buyer's behalf
- Commits to terms
- Shares confidential Piubelle data
- Creates account or liability

---

## GDPR & EU AI Act Compliance

### **GDPR Article 6 (Lawful Basis)**
✅ **Legitimate Interest** — Finding alternatives to underperforming suppliers is a legitimate business need.

### **GDPR Article 13 (Transparency)**
✅ **Disclosed** — Suppliers know their info is publicly available.  
✅ **No surprise collection** — Only publicly listed contact details.

### **GDPR Article 17 (Right to Erasure)**
✅ **Not applicable** — We don't store supplier data; we search and display on-demand.

### **EU AI Act (Regulation 2024/1689)**
✅ **Limited-risk AI** — Alternative supplier search is informational, not autonomous.  
✅ **Human in loop** — Buyer decides whether to contact suppliers.  
✅ **No financial commitment** — Agent recommends only; humans negotiate terms.

---

### **Data Retention**

- **Search results:** Displayed once, not stored in database
- **Buyer decisions:** Logged only if buyer manually adds to supplier master
- **Personal data:** Never retained (GDPR-compliant)
- **Audit trail:** What was searched, when, by whom (for compliance)

---

### **Buyer Responsibility**

When contacting alternative suppliers, buyers must:
1. ✅ Use only the **business contact channels** WARP provided
2. ✅ Honor any **confidentiality** in supplier relationships
3. ✅ Follow **internal procurement approval** workflows
4. ✅ Comply with **corporate contracting** policies
5. ✅ Ensure **supplier diversity & fairness** criteria are met

---

## Why This Design?

✅ **Balanced:** No single dimension dominates (max weight: 35%)  
✅ **Normalized:** Fair comparison across different measurement scales  
✅ **Actionable:** Score directly maps to alert levels (Red/Amber/OK)  
✅ **Transparent:** All 6 dimensions visible; no black-box calculation  
✅ **Trend-aware:** Captures improving vs. deteriorating suppliers  
✅ **Data-honest:** N/A for unreliable data; doesn't manufacture confidence  
✅ **Privacy-first:** Alternative search respects GDPR & personal data rights  
✅ **Human-governed:** AI recommends; humans decide and execute  

---

## Testing

All boundary conditions tested in `tests/test_scorer.py`:

```python
✅ All scores in [1.0, 10.0]
✅ Problematic suppliers avg < 5.0
✅ High performers avg > 7.0
✅ Deterministic: same seed → same score
✅ < 5 events → NaN (no false precision)
✅ 15/15 pytest cases passing
```

---

## References

- **GDPR:** EU Regulation 2016/679 (Articles 6, 13, 17, 21)
- **EU AI Act:** Regulation 2024/1689 (Limited-risk classification)
- **Procurement Standards:** ISO 8402, IEC 61160 (quality management)
- **WARP System Prompt:** `WARP_system_prompt.md` (full scope)

---

*WARP Scoring Guide · MBA Group Project · Generative AI & AI Agents · Porto Business School*  
*Last updated: April 6, 2026*
