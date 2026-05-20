"""
Customer 360 Data Platform - ETL Pipeline
Project: Unified Customer Intelligence Platform
Author: Suhana
Tools: Python, Pandas, Google BigQuery, Cloud Storage
Description: Ingests raw data from CRM, transactions, web events, and
             support tickets; cleans, transforms, and loads to BigQuery.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")
import random
# ─────────────────────────────────────────────
# STEP 1: SIMULATE RAW DATA SOURCES
# (In production: connect to CRM API, DB, S3, etc.)
# ─────────────────────────────────────────────

np.random.seed(42)
n_customers = 5000

print("=" * 60)
print("  CUSTOMER 360 DATA PLATFORM - ETL PIPELINE")
print("=" * 60)

# --- Source 1: CRM Data ---
print("\n[1/5] Loading CRM data...")
customer_ids = [f"CUST_{str(i).zfill(5)}" for i in range(1, n_customers + 1)]
crm_raw = pd.DataFrame({
    "customer_id":    customer_ids,
    "first_name":     np.random.choice(["Aarav", "Priya", "Rahul", "Neha", "Vikram",
                                         "Anjali", "Arjun", "Meera", "Sanjay", "Pooja"], n_customers),
    "last_name":      np.random.choice(["Sharma", "Patel", "Singh", "Kumar", "Gupta",
                                         "Nair", "Reddy", "Mehta", "Joshi", "Shah"], n_customers),
    "email":          [f"user{i}@email.com" for i in range(1, n_customers + 1)],
    #"phone":          [f"+91-{random.randint(7000000000, 9999999999)}" for _ in range(n_customers)],
    "phone": [f"+91-{abs(random.randint(7000000000, 9999999999))}" for _ in range(n_customers)],
    "city":           np.random.choice(["Bengaluru", "Mumbai", "Delhi", "Hyderabad",
                                         "Chennai", "Pune", "Kolkata", "Ahmedabad"], n_customers),
    "signup_date":    pd.date_range("2020-01-01", periods=n_customers, freq="6h"),
    "segment":        np.random.choice(["Premium", "Standard", "Basic", None], n_customers, p=[0.2, 0.4, 0.35, 0.05]),
    "age":            np.random.choice(list(range(18, 70)) + [None], n_customers),
})
print(f"   ✔ CRM records loaded: {len(crm_raw):,}")

# --- Source 2: Transactions ---
print("[2/5] Loading transaction data...")
n_transactions = 80000
txn_raw = pd.DataFrame({
    "txn_id":         [f"TXN_{str(i).zfill(7)}" for i in range(1, n_transactions + 1)],
    "customer_id":    np.random.choice(customer_ids, n_transactions),
    "txn_date":       [datetime(2022, 1, 1) + timedelta(days=np.random.randint(0, 900)) for _ in range(n_transactions)],
    "amount":         np.round(np.random.exponential(scale=2500, size=n_transactions), 2),
    "category":       np.random.choice(["Electronics", "Apparel", "Grocery", "Home",
                                         "Beauty", "Sports", "Books", "Travel"], n_transactions),
    "channel":        np.random.choice(["Mobile App", "Web", "In-Store", "Partner"], n_transactions, p=[0.45, 0.3, 0.2, 0.05]),
    "is_returned":    np.random.choice([0, 1], n_transactions, p=[0.92, 0.08]),
    "payment_method": np.random.choice(["UPI", "Credit Card", "Debit Card", "Net Banking", "COD"], n_transactions),
})
# Introduce missing values for realism
txn_raw.loc[np.random.choice(txn_raw.index, 800), "amount"] = np.nan
print(f"   ✔ Transaction records loaded: {len(txn_raw):,}")

# --- Source 3: Web/App Events ---
print("[3/5] Loading web/app event data...")
n_events = 200000
events_raw = pd.DataFrame({
    "event_id":       range(n_events),
    "customer_id":    np.random.choice(customer_ids, n_events),
    "event_type":     np.random.choice(["page_view", "add_to_cart", "checkout", "search",
                                          "wishlist", "product_click", "app_open"], n_events,
                                         p=[0.35, 0.2, 0.1, 0.15, 0.08, 0.09, 0.03]),
    "event_date":     [datetime(2022, 1, 1) + timedelta(hours=np.random.randint(0, 21600)) for _ in range(n_events)],
    "device":         np.random.choice(["Android", "iOS", "Desktop", "Tablet"], n_events, p=[0.4, 0.3, 0.25, 0.05]),
    "session_minutes": np.round(np.abs(np.random.normal(8, 5, n_events)), 1),
})
print(f"   ✔ Web/app event records loaded: {len(events_raw):,}")

# --- Source 4: Support Tickets ---
print("[4/5] Loading support ticket data...")
n_tickets = 12000
tickets_raw = pd.DataFrame({
    "ticket_id":      [f"TKT_{str(i).zfill(6)}" for i in range(1, n_tickets + 1)],
    "customer_id":    np.random.choice(customer_ids, n_tickets),
    "created_date":   [datetime(2022, 1, 1) + timedelta(days=np.random.randint(0, 900)) for _ in range(n_tickets)],
    "category":       np.random.choice(["Delivery", "Payment", "Return", "Product Quality",
                                          "App Issue", "Account", "Other"], n_tickets),
    "priority":       np.random.choice(["High", "Medium", "Low"], n_tickets, p=[0.2, 0.5, 0.3]),
    "resolution_days": np.random.choice([1, 2, 3, 5, 7, 10, None], n_tickets, p=[0.2, 0.25, 0.2, 0.15, 0.1, 0.05, 0.05]),
    "csat_score":     np.random.choice([1, 2, 3, 4, 5, None], n_tickets, p=[0.05, 0.08, 0.17, 0.35, 0.3, 0.05]),
})
print(f"   ✔ Support ticket records loaded: {len(tickets_raw):,}")

# ─────────────────────────────────────────────
# STEP 2: DATA CLEANING & TRANSFORMATION
# ─────────────────────────────────────────────

print("\n" + "─" * 60)
print("TRANSFORMING & CLEANING DATA")
print("─" * 60)

# --- Clean CRM ---
crm = crm_raw.copy()
crm["segment"] = crm["segment"].fillna("Standard")
crm["age"] = crm["age"].fillna(crm["age"].median())
crm["full_name"] = crm["first_name"] + " " + crm["last_name"]
crm["days_since_signup"] = (datetime.today() - pd.to_datetime(crm["signup_date"])).dt.days
crm = crm.drop_duplicates(subset=["customer_id"])
print(f"\n✔ CRM cleaned — {crm['segment'].isna().sum()} nulls fixed, {len(crm):,} unique customers")

# --- Clean Transactions ---
txn = txn_raw.copy()
before = len(txn)
txn["amount"] = txn["amount"].fillna(txn["amount"].median())
txn["net_amount"] = np.where(txn["is_returned"] == 1, 0, txn["amount"])
txn["txn_year_month"] = pd.to_datetime(txn["txn_date"]).dt.to_period("M")
print(f"✔ Transactions cleaned — {before - txn['amount'].isna().sum()} null amounts imputed")

# --- Customer Aggregations from Transactions ---
txn_agg = txn.groupby("customer_id").agg(
    total_orders       = ("txn_id", "count"),
    total_spend        = ("net_amount", "sum"),
    avg_order_value    = ("net_amount", "mean"),
    return_rate        = ("is_returned", "mean"),
    unique_categories  = ("category", "nunique"),
    last_purchase_date = ("txn_date", "max"),
    first_purchase_date= ("txn_date", "min"),
    preferred_channel  = ("channel", lambda x: x.mode()[0] if not x.empty else "Unknown"),
).reset_index()
txn_agg["days_since_last_purchase"] = (datetime.today() - pd.to_datetime(txn_agg["last_purchase_date"])).dt.days
txn_agg["customer_lifetime_days"]   = (pd.to_datetime(txn_agg["last_purchase_date"]) - pd.to_datetime(txn_agg["first_purchase_date"])).dt.days
print(f"✔ Transaction features engineered for {len(txn_agg):,} customers")

# --- Web/App Engagement ---
events_agg = events_raw.groupby("customer_id").agg(
    total_sessions     = ("event_id", "count"),
    avg_session_mins   = ("session_minutes", "mean"),
    checkout_events    = ("event_type", lambda x: (x == "checkout").sum()),
    cart_events        = ("event_type", lambda x: (x == "add_to_cart").sum()),
    preferred_device   = ("device", lambda x: x.mode()[0] if not x.empty else "Unknown"),
).reset_index()
events_agg["cart_to_checkout_rate"] = np.where(
    events_agg["cart_events"] > 0,
    events_agg["checkout_events"] / events_agg["cart_events"],
    0
)
print(f"✔ Engagement features engineered for {len(events_agg):,} customers")

# --- Support Summary ---
tickets_agg = tickets_raw.groupby("customer_id").agg(
    total_tickets      = ("ticket_id", "count"),
    high_priority_tickets = ("priority", lambda x: (x == "High").sum()),
    avg_csat           = ("csat_score", "mean"),
    avg_resolution_days= ("resolution_days", "mean"),
).reset_index()
#tickets_agg["avg_csat"] = tickets_agg["avg_csat"].round(2)
tickets_agg["avg_csat"] = pd.to_numeric(tickets_agg["avg_csat"], errors="coerce").round(2)
print(f"✔ Support features engineered for {len(tickets_agg):,} customers")

# ─────────────────────────────────────────────
# STEP 3: BUILD UNIFIED CUSTOMER 360 TABLE
# ─────────────────────────────────────────────

print("\n" + "─" * 60)
print("BUILDING CUSTOMER 360 UNIFIED TABLE")
print("─" * 60)

customer360 = crm.merge(txn_agg,    on="customer_id", how="left")
customer360 = customer360.merge(events_agg, on="customer_id", how="left")
customer360 = customer360.merge(tickets_agg, on="customer_id", how="left")

# Fill numeric nulls for customers with no transactions/events/tickets
num_cols = ["total_orders", "total_spend", "avg_order_value", "return_rate",
            "unique_categories", "total_sessions", "avg_session_mins",
            "checkout_events", "cart_events", "cart_to_checkout_rate",
            "total_tickets", "high_priority_tickets", "avg_csat", "avg_resolution_days"]
customer360[num_cols] = customer360[num_cols].fillna(0)

# ─────────────────────────────────────────────
# STEP 4: RFM SCORING
# ─────────────────────────────────────────────

print("\n[RFM Scoring]")
active = customer360[customer360["total_orders"] > 0].copy()

active["R_score"] = pd.qcut(active["days_since_last_purchase"].rank(method="first"), 5, labels=[5,4,3,2,1]).astype(int)
active["F_score"] = pd.qcut(active["total_orders"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
active["M_score"] = pd.qcut(active["total_spend"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
active["RFM_score"] = active["R_score"] + active["F_score"] + active["M_score"]

def rfm_segment(score):
    if score >= 13: return "Champions"
    elif score >= 10: return "Loyal Customers"
    elif score >= 7:  return "Potential Loyalists"
    elif score >= 5:  return "At Risk"
    else:             return "Lost / Inactive"

active["rfm_segment"] = active["RFM_score"].apply(rfm_segment)
customer360 = customer360.merge(active[["customer_id", "R_score", "F_score", "M_score", "RFM_score", "rfm_segment"]], on="customer_id", how="left")
customer360["rfm_segment"] = customer360["rfm_segment"].fillna("No Purchase History")

print(f"✔ RFM segments assigned:")
print(customer360["rfm_segment"].value_counts().to_string())

# ─────────────────────────────────────────────
# STEP 5: CHURN RISK FLAG
# ─────────────────────────────────────────────

def churn_risk(row):
    score = 0
    if row["days_since_last_purchase"] > 180: score += 3
    elif row["days_since_last_purchase"] > 90: score += 1
    if row["total_tickets"] > 3: score += 2
    if row["avg_csat"] > 0 and row["avg_csat"] < 3: score += 2
    if row["return_rate"] > 0.3: score += 1
    if row["total_sessions"] < 5: score += 1
    if score >= 5: return "High"
    elif score >= 3: return "Medium"
    return "Low"

customer360["churn_risk"] = customer360.apply(churn_risk, axis=1)

# ─────────────────────────────────────────────
# STEP 6: EXPORT
# ─────────────────────────────────────────────

print("\n" + "─" * 60)
print("EXPORTING OUTPUTS")
print("─" * 60)

#customer360.to_csv("/home/claude/customer360/customer_360_master.csv", index=False)
customer360.to_csv(r"D:\Customer 360 data platform\customer_360_master.csv", index=False)
print(f"✔ Master customer 360 table saved: {len(customer360):,} rows × {len(customer360.columns)} columns")


# ─────────────────────────────────────────────
# EXPORT INDIVIDUAL SOURCE TABLES (for BigQuery SQL layer)
# ─────────────────────────────────────────────

crm.to_csv(r"D:\Customer 360 data platform\crm_customers.csv", index=False)
txn.to_csv(r"D:\Customer 360 data platform\transactions.csv", index=False)
events_raw.to_csv(r"D:\Customer 360 data platform\web_events.csv", index=False)
tickets_raw.to_csv(r"D:\Customer 360 data platform\support_tickets.csv", index=False)

print("✔ Source tables exported for BigQuery (CRM, Transactions, Events, Tickets)")

# Summary stats
print("\n━━━ PIPELINE SUMMARY ━━━")
print(f"  Total Customers:          {len(customer360):,}")
print(f"  Total Transactions:       {len(txn):,}")
print(f"  Total Web Events:         {len(events_raw):,}")
print(f"  Total Support Tickets:    {len(tickets_raw):,}")
print(f"  Avg Customer Spend:       ₹{customer360['total_spend'].mean():,.0f}")
print(f"  Churn Risk - High:        {(customer360['churn_risk']=='High').sum():,}")
print(f"  Churn Risk - Medium:      {(customer360['churn_risk']=='Medium').sum():,}")
print(f"  Champions (RFM):          {(customer360['rfm_segment']=='Champions').sum():,}")
print(f"\n✅ ETL Pipeline Complete — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
