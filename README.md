# Customer 360 Data Platform

End-to-end Customer Intelligence Platform built using Python, SQL, BigQuery, and Machine Learning to unify customer data from multiple business systems into a single analytics-ready intelligence layer.

---

# Project Overview

Businesses often store customer data across disconnected systems, making it difficult to generate unified customer insights for marketing, retention, and revenue growth.

This project builds a complete **Customer 360 Data Platform** that consolidates:

- CRM customer profiles
- Transactional purchase history
- Web/App behavioral events
- Customer support interactions

into a single source of truth for analytics, segmentation, churn prediction, and executive reporting.

---

# Business Impact

- Unified **292,000+ records** across 4 data sources
- Built **5,000+ customer profiles** with 37 attributes each
- Identified **Champions contributing 42% of total revenue**
- Flagged **1,485 high churn-risk customers**
- Surfaced **320+ cross-sell opportunities**
- Reduced reporting turnaround from **3 days to near real-time**
- Enabled precision-targeted customer segmentation

---

# Tech Stack

## Data Engineering
- Python
- Pandas
- NumPy
- PySpark
- Databricks
- Google BigQuery
- Delta Lake

## Machine Learning & Analytics
- Scikit-learn
- K-Means Clustering
- PCA
- RFM Segmentation

## SQL & Warehousing
- BigQuery SQL
- CTEs
- Window Functions
- Views

## Visualization & BI
- Tableau
- Power BI
- Matplotlib
- Seaborn

## Data Quality & Architecture
- Great Expectations
- Medallion Architecture (Bronze → Silver → Gold)

---

# Architecture

```text
CRM Data
Transactions Data
Web/App Events
Support Tickets
        ↓
Bronze Layer (Raw Ingestion)
        ↓
Silver Layer (Cleaned & Standardized)
        ↓
Gold Layer (Customer 360 Master Table)
        ↓
Feature Engineering
        ↓
RFM Segmentation + Churn Scoring + Clustering
        ↓
Executive Dashboards & Business Insights
```

---

# Key Features

## 1. ETL Pipeline
- Built end-to-end ETL workflows for ingesting and cleaning multi-source customer data
- Handled null values, duplicate records, schema standardization, and data validation
- Generated unified `customer_360_master` table with customer-level metrics

---

## 2. RFM Segmentation
Customers segmented using:
- Recency
- Frequency
- Monetary value

Segments created:
- Champions
- Loyal Customers
- Potential Loyalists
- At Risk
- Lost Customers

---

## 3. Behavioral Clustering
Applied K-Means clustering on behavioral metrics:
- Total spend
- Order frequency
- Average order value
- Return rate
- Category diversity
- Purchase recency

Identified customer personas:
- VIP Spenders
- Engaged Explorers
- Price Sensitive
- Occasional Buyers
- Churned Shoppers

---

## 4. Churn Risk Scoring
Built composite churn scoring model using:
- Purchase inactivity
- Ticket volume
- CSAT score
- Return behavior
- Engagement activity

Generated win-back target lists for retention campaigns.

---

## 5. SQL Analytics Layer
Built production-style SQL views and KPI queries:
- Monthly revenue trends
- MoM growth
- Channel performance
- Customer health metrics
- Cross-sell opportunities
- Churn analysis

---

# Folder Structure

```
customer-360-data-platform/
│
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
│
├── data/
│   ├── raw/
│   │   ├── crm_customers_sample.csv
│   │   ├── transactions_sample.csv
│   │   ├── web_events_sample.csv
│   │   └── support_tickets_sample.csv
│   │
│   └── processed/
│       └── customer_360_master.csv
│
├── scripts/
│   ├── 01_etl_pipeline.py
│   ├── 02_segmentation_analysis.py
│   └── 03_sql_analytics.sql
│
├── dashboards/
│   ├── dashboard_executive.png
│   ├── dashboard_clusters.png
│   └── heatmap_segment_city.png
│
└── outputs/
    ├── cluster_summary.csv
    └── rfm_segment_summary.csv
```

---

# Datasets Used

Synthetic datasets generated to simulate real-world enterprise systems:

- CRM customer database
- E-commerce transactions
- Website/app event tracking
- Customer support ticketing systems

---

# Dashboard & Insights

The platform provides dashboards for:

- Revenue trends
- RFM segment distribution
- Customer personas
- Churn risk monitoring
- City-level revenue analysis

---

# Skills Demonstrated

## Data Engineering
- ETL Design
- Data Cleaning
- Feature Engineering
- Data Validation
- Medallion Architecture

## Analytics
- Customer Segmentation
- Churn Modeling
- CLTV Analysis
- Cohort Thinking
- Behavioral Analytics

## SQL
- Window Functions
- Aggregations
- CTEs
- Analytical Views

## Machine Learning
- K-Means Clustering
- PCA
- StandardScaler

## Visualization
- Executive Dashboards
- Heatmaps
- Cluster Visualizations

---

# How to Run

## Clone Repository

```
git clone https://github.com/Suhana-Saini/customer-360-data-platform.git

cd customer-360-data-platform
```

## Install Dependencies

```
pip install -r requirements.txt
```

## Run ETL Pipeline

```
python scripts/01_etl_pipeline.py
```

## Run Segmentation Analysis

```
python scripts/02_segmentation_analysis.py
```

---

# Future Improvements

- Airflow orchestration
- dbt transformations
- Real-time streaming pipelines
- CI/CD integration
- Dockerization
- Streamlit dashboard deployment

---

# Resume Highlights

- Built end-to-end Customer 360 platform processing 292K+ records across 4 enterprise data sources
- Designed RFM segmentation identifying high-value customers contributing 42% revenue share
- Developed churn scoring model flagging 1,485 high-risk accounts for proactive retention
- Applied K-Means clustering to define 5 behavioral customer personas
- Built SQL analytics layer and executive dashboards for business decision-making

---

# Author

Suhana Saini

Data Engineering | Analytics | Machine Learning
