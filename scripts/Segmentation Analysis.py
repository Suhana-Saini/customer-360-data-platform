"""
Customer 360 Data Platform - Segmentation & Analysis
Project: Unified Customer Intelligence Platform
Tools: Python (Pandas, Scikit-learn, Matplotlib, Seaborn)
Description: Performs RFM analysis, behavioral clustering, churn risk
             scoring, and generates charts ready for Tableau/Power BI.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# SETUP: RECREATE CUSTOMER 360 DATA
# ─────────────────────────────────────────────

from datetime import datetime, timedelta
np.random.seed(42)
n = 5000
customer_ids = [f"CUST_{str(i).zfill(5)}" for i in range(1, n + 1)]

n_transactions = 80000
txn = pd.DataFrame({
    "customer_id": np.random.choice(customer_ids, n_transactions),
    "txn_id": range(n_transactions),
    "txn_date": [datetime(2022,1,1) + timedelta(days=np.random.randint(0,900)) for _ in range(n_transactions)],
    "amount": np.round(np.abs(np.random.exponential(2500, n_transactions)), 2),
    "category": np.random.choice(["Electronics","Apparel","Grocery","Home","Beauty","Sports","Books","Travel"], n_transactions),
    "channel": np.random.choice(["Mobile App","Web","In-Store","Partner"], n_transactions, p=[0.45,0.3,0.2,0.05]),
    "is_returned": np.random.choice([0,1], n_transactions, p=[0.92,0.08]),
})

txn_agg = txn.groupby("customer_id").agg(
    total_orders=("txn_id","count"),
    total_spend=("amount","sum"),
    avg_order_value=("amount","mean"),
    return_rate=("is_returned","mean"),
    unique_categories=("category","nunique"),
    last_purchase_date=("txn_date","max"),
).reset_index()
txn_agg["days_since_last_purchase"] = (datetime.today() - pd.to_datetime(txn_agg["last_purchase_date"])).dt.days

# RFM
df = txn_agg.copy()
df["R"] = pd.qcut(df["days_since_last_purchase"].rank(method="first"), 5, labels=[5,4,3,2,1]).astype(int)
df["F"] = pd.qcut(df["total_orders"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
df["M"] = pd.qcut(df["total_spend"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
df["RFM"] = df["R"] + df["F"] + df["M"]
def seg(s):
    if s>=13: return "Champions"
    elif s>=10: return "Loyal Customers"
    elif s>=7: return "Potential Loyalists"
    elif s>=5: return "At Risk"
    return "Lost / Inactive"
df["rfm_segment"] = df["RFM"].apply(seg)
df["city"] = np.random.choice(["Bengaluru","Mumbai","Delhi","Hyderabad","Chennai","Pune"], n, p=[0.25,0.2,0.2,0.15,0.1,0.1])
df["segment"] = np.random.choice(["Premium","Standard","Basic"], n, p=[0.2,0.45,0.35])

# ─────────────────────────────────────────────
# SECTION 1: K-MEANS CLUSTERING
# ─────────────────────────────────────────────

print("Running K-Means Customer Clustering...")
features = ["total_orders", "total_spend", "avg_order_value", "return_rate",
            "unique_categories", "days_since_last_purchase"]
X = df[features].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Elbow method
inertias = [KMeans(n_clusters=k, random_state=42, n_init=10).fit(X_scaled).inertia_ for k in range(2, 9)]

# Fit final model (k=5)
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X_scaled)
cluster_labels = {0:"Price-Sensitive", 1:"VIP Spenders", 2:"Occasional Buyers",
                  3:"Engaged Explorers", 4:"Churned Shoppers"}
df["cluster_name"] = df["cluster"].map(cluster_labels)

# PCA for 2D visualization
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
df["pca_x"], df["pca_y"] = X_pca[:,0], X_pca[:,1]
print(f"✔ Clustering complete. Explained variance: {pca.explained_variance_ratio_.sum()*100:.1f}%")

# ─────────────────────────────────────────────
# SECTION 2: CHARTS & VISUALIZATIONS
# ─────────────────────────────────────────────

palette_rfm  = {"Champions":"#1a6e3c","Loyal Customers":"#2ca85c","Potential Loyalists":"#f5a623",
                "At Risk":"#e8641b","Lost / Inactive":"#c0392b"}
palette_clus = {"VIP Spenders":"#1a3c6e","Engaged Explorers":"#2980b9","Occasional Buyers":"#27ae60",
                "Price-Sensitive":"#f39c12","Churned Shoppers":"#e74c3c"}
bg = "#f8f9fb"

# ── FIGURE 1: Executive Dashboard (4-panel) ──
fig = plt.figure(figsize=(18, 12), facecolor=bg)
fig.suptitle("Customer 360 Intelligence Dashboard", fontsize=20, fontweight="bold", y=0.98, color="#1a1a2e")
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

# Panel 1: RFM Segment Distribution
ax1 = fig.add_subplot(gs[0, 0])
rfm_counts = df["rfm_segment"].value_counts()
colors = [palette_rfm[s] for s in rfm_counts.index]
wedges, texts, autotexts = ax1.pie(rfm_counts.values, labels=rfm_counts.index,
    autopct="%1.1f%%", colors=colors, startangle=140, pctdistance=0.78,
    textprops={"fontsize":8}, wedgeprops={"edgecolor":"white","linewidth":1.5})
for at in autotexts: at.set_fontsize(7); at.set_color("white"); at.set_fontweight("bold")
ax1.set_title("RFM Customer Segments", fontweight="bold", fontsize=12, pad=10)

# Panel 2: Revenue by Segment
ax2 = fig.add_subplot(gs[0, 1])
rev_seg = df.groupby("rfm_segment")["total_spend"].sum().sort_values(ascending=True) / 1e6
bar_colors = [palette_rfm[s] for s in rev_seg.index]
bars = ax2.barh(rev_seg.index, rev_seg.values, color=bar_colors, edgecolor="white", height=0.65)
for bar, val in zip(bars, rev_seg.values):
    ax2.text(val + 0.3, bar.get_y() + bar.get_height()/2, f"₹{val:.1f}M",
             va="center", ha="left", fontsize=8, fontweight="bold", color="#333")
ax2.set_xlabel("Revenue (₹ Millions)", fontsize=9)
ax2.set_title("Revenue by RFM Segment", fontweight="bold", fontsize=12)
ax2.set_facecolor(bg); ax2.spines[["top","right"]].set_visible(False)

# Panel 3: K-Means PCA Clusters
ax3 = fig.add_subplot(gs[0, 2])
sample = df.sample(1500, random_state=42)
for cname, cdf in sample.groupby("cluster_name"):
    ax3.scatter(cdf["pca_x"], cdf["pca_y"], label=cname, alpha=0.55,
                s=18, color=palette_clus[cname], edgecolors="none")
ax3.set_title("Behavioral Clusters (PCA)", fontweight="bold", fontsize=12)
ax3.set_xlabel("PC1", fontsize=9); ax3.set_ylabel("PC2", fontsize=9)
ax3.legend(fontsize=7, markerscale=1.5, framealpha=0.7)
ax3.set_facecolor(bg); ax3.spines[["top","right"]].set_visible(False)

# Panel 4: Monthly Revenue Trend
ax4 = fig.add_subplot(gs[1, 0:2])
txn["month"] = pd.to_datetime(txn["txn_date"]).dt.to_period("M")
monthly = txn.groupby("month")["amount"].sum().reset_index()
monthly["month_dt"] = monthly["month"].dt.to_timestamp()
monthly_roll = monthly["amount"].rolling(3).mean()
ax4.fill_between(monthly["month_dt"], monthly["amount"]/1e6, alpha=0.2, color="#2980b9")
ax4.plot(monthly["month_dt"], monthly["amount"]/1e6, color="#2980b9", linewidth=2, label="Monthly Revenue")
ax4.plot(monthly["month_dt"], monthly_roll/1e6, color="#e74c3c", linewidth=2, linestyle="--", label="3M Rolling Avg")
ax4.set_title("Monthly Revenue Trend (2022-2024)", fontweight="bold", fontsize=12)
ax4.set_ylabel("Revenue (₹ Millions)", fontsize=9)
ax4.legend(fontsize=9); ax4.set_facecolor(bg)
ax4.spines[["top","right"]].set_visible(False)
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=8)

# Panel 5: City-wise Revenue
ax5 = fig.add_subplot(gs[1, 2])
city_rev = df.groupby("city")["total_spend"].sum().sort_values(ascending=False) / 1e6
ax5.bar(city_rev.index, city_rev.values, color=["#1a3c6e","#2980b9","#27ae60","#f39c12","#e74c3c","#8e44ad"],
        edgecolor="white", width=0.65)
ax5.set_title("Revenue by City", fontweight="bold", fontsize=12)
ax5.set_ylabel("Revenue (₹ Millions)", fontsize=9)
ax5.set_facecolor(bg); ax5.spines[["top","right"]].set_visible(False)
plt.setp(ax5.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=8)

plt.savefig("D:\Customer 360 data platform\Dashboard executive", dpi=150, bbox_inches="tight", facecolor=bg)
print("✔ Executive dashboard saved")

# ── FIGURE 2: Cluster Deep-Dive ──
fig2, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor=bg)
fig2.suptitle("Customer Cluster Deep-Dive Analysis", fontsize=16, fontweight="bold", color="#1a1a2e")

metrics = ["total_spend","total_orders","avg_order_value"]
titles  = ["Avg Total Spend (₹)","Avg Total Orders","Avg Order Value (₹)"]
for ax, metric, title in zip(axes, metrics, titles):
    cluster_avg = df.groupby("cluster_name")[metric].mean().sort_values(ascending=False)
    colors = [palette_clus[c] for c in cluster_avg.index]
    bars = ax.bar(cluster_avg.index, cluster_avg.values, color=colors, edgecolor="white", width=0.65)
    for bar in bars:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.01,
                f"{bar.get_height():,.0f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.set_title(title, fontweight="bold", fontsize=12)
    ax.set_facecolor(bg); ax.spines[["top","right"]].set_visible(False)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=15, ha="right", fontsize=8)

plt.tight_layout()
plt.savefig("D:\Customer 360 data platform\Dashboard Clusters", dpi=150, bbox_inches="tight", facecolor=bg)
print("✔ Cluster analysis chart saved")

# ── FIGURE 3: Churn Risk Heatmap ──
fig3, ax = plt.subplots(figsize=(10, 6), facecolor=bg)
pivot = df.groupby(["rfm_segment","city"])["total_spend"].sum().unstack(fill_value=0) / 1e6
sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd", linewidths=0.5,
            linecolor="white", ax=ax, cbar_kws={"label":"Revenue (₹M)"})
ax.set_title("Revenue Heatmap: Segment × City (₹M)", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel(""); ax.set_ylabel("")
plt.tight_layout()
plt.savefig("D:\Customer 360 data platform\Heatmap segment city", dpi=150, bbox_inches="tight")
print("✔ Segment×City heatmap saved")

# ─────────────────────────────────────────────
# SECTION 3: EXPORT ANALYSIS TABLES
# ─────────────────────────────────────────────

segment_summary = df.groupby("rfm_segment").agg(
    customers=("customer_id","count"),
    avg_spend=("total_spend","mean"),
    total_revenue=("total_spend","sum"),
    avg_orders=("total_orders","mean"),
    avg_recency_days=("days_since_last_purchase","mean"),
).reset_index().round(2)
segment_summary["revenue_share_%"] = (segment_summary["total_revenue"] / segment_summary["total_revenue"].sum() * 100).round(1)
segment_summary.to_csv("D:\Customer 360 data platform\Rfm segment summary.csv", index=False)

cluster_summary = df.groupby("cluster_name").agg(
    customers=("customer_id","count"),
    avg_spend=("total_spend","mean"),
    avg_orders=("total_orders","mean"),
    avg_aov=("avg_order_value","mean"),
    avg_return_rate=("return_rate","mean"),
).reset_index().round(2)
cluster_summary.to_csv("D:\Customer 360 data platform\cluster_summary.csv", index=False)

print("\n✅ All analysis outputs saved successfully!")
print("\n📊 RFM Segment Summary:")
print(segment_summary[["rfm_segment","customers","avg_spend","revenue_share_%"]].to_string(index=False))
print("\n🔵 Cluster Summary:")
print(cluster_summary[["cluster_name","customers","avg_spend","avg_orders"]].to_string(index=False))