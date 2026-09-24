# 🛍️ Shopify Sales Data Analytics

> A full-stack analytics project: data cleaning, EDA, star schema modelling, DAX measures, and a 3-page interactive Streamlit dashboard.

---

## 📁 Project Structure

```
shopify_analytics/
├── data/
│   ├── raw/                        # Original Shopify Sales.xlsx
│   ├── cleaned/                    # shopify_sales_cleaned.csv
│   └── star_schema/                # FactSales.csv, Dim*.csv
├── notebooks/
│   └── shopify_analytics.ipynb     # Complete EDA + cleaning + schema
├── dashboard/
│   ├── app.py                      # Streamlit dashboard (3 pages)
│   └── data/                       # Data files for the app
├── requirements.txt
├── README.md
├── DAX_Measures.md
└── Project_Report.docx
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Jupyter Notebook (Data Cleaning + EDA)

```bash
cd shopify_analytics/notebooks
jupyter notebook shopify_analytics.ipynb
```

> This will generate `data/cleaned/shopify_sales_cleaned.csv` and all star schema CSVs.

### 3. Launch the Streamlit Dashboard

```bash
cd shopify_analytics/dashboard
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📊 Dataset Overview

| Attribute | Value |
|-----------|-------|
| Source | Shopify Orders Export |
| Sheet | `shopify_sales` |
| Raw Rows | 7,431 |
| Columns | 19 |
| Date Range | March 18–24, 2025 |
| Geography | United States (49 states, 453 cities) |
| Currency | USD |
| Revenue | ~$4.6M |

### Columns

| Column | Description |
|--------|-------------|
| Admin Graphql Api Id | Unique line-item identifier |
| Order Number | Shopify order number |
| Billing Address Country | Customer country |
| Billing Address First/Last Name | Customer name |
| Billing Address Province | US state |
| Billing Address Zip | ZIP code |
| CITY | City in upper case |
| Currency | Always USD |
| Customer Id | Unique customer identifier |
| Invoice Date | Order timestamp (YYYY-MM-DD HH:MM) |
| Gateway | Payment method |
| Product Id | Shopify product ID |
| Product Type | Product category |
| Variant Id | Product variant ID |
| Quantity | Items ordered |
| Subtotal Price | Pre-tax price |
| Total Price Usd | Final price including tax |
| Total Tax | Tax amount |

---

## 🧹 Data Cleaning Summary

| Issue | Action |
|-------|--------|
| Missing `product_id` (11 rows) | Filled with `"UNKNOWN"` |
| Missing `variant_id` (4 rows) | Filled with `"UNKNOWN"` |
| Full duplicate rows | Removed |
| `Invoice Date` as string | Parsed to `datetime64` |
| City names inconsistent | Standardised to UPPER CASE |
| Province names inconsistent | Title-cased |
| Gateway names (snake_case) | Mapped to display labels |
| `"Boy's"` product type | Normalised to `"Boy's Shoes"` |
| Invalid quantities (< 1 or > 20) | Removed |
| Zero/negative prices | Removed |

---

## ⭐ Star Schema

### FactSales (Grain: one row = one line item on an order)

| Column | Type | Description |
|--------|------|-------------|
| line_item_id | STRING (PK) | Unique line item |
| order_number | STRING | Shopify order number |
| date_key | INT (FK) | → DimDate |
| product_key | INT (FK) | → DimProduct |
| customer_key | INT (FK) | → DimCustomer |
| location_key | INT (FK) | → DimLocation |
| payment_key | INT (FK) | → DimPayment |
| quantity | INT | Units ordered |
| unit_price | DECIMAL | Price per unit |
| subtotal_price | DECIMAL | Pre-tax total |
| total_price_usd | DECIMAL | Final total |
| total_tax | DECIMAL | Tax collected |
| tax_rate | DECIMAL | Effective tax rate % |

### Dimension Tables

| Table | PK | Key Attributes |
|-------|----|----------------|
| DimDate | date_key | year, month, quarter, week, day_name, is_weekend |
| DimProduct | product_key | product_id, product_type, variant_id, product_category |
| DimCustomer | customer_key | customer_id, first_name, last_name, full_name |
| DimLocation | location_key | city, province, country, zip_code, region |
| DimPayment | payment_key | gateway, payment_type, is_online |

---

## 📈 Dashboard Pages

### Page 1 — Executive Overview
- Total Revenue, Orders, Customers, Items Sold, AOV, Avg Unit Price, Tax, Repeat Rate
- Daily revenue area chart
- Day-of-week revenue bar
- Revenue by product type
- Revenue by payment gateway (donut)
- Regional breakdown
- Hourly sales trend
- Summary table with CSV download

### Page 2 — Product & Sales
- Product KPIs (unique types, variants, revenue, AOV)
- Revenue treemap
- Units sold by product
- Unit price boxplot by product
- Quantity distribution
- Stacked daily area by product
- Price vs Volume scatter (bubble)
- Product performance table with CSV download

### Page 3 — Customer, Geography & Payment
- Customer count, city/state coverage, orders/customer, revenue/customer
- US choropleth map (revenue by state)
- Top states bar chart
- Top cities bar chart
- Region × product stacked bar
- Top 15 customers bar
- Orders-per-customer histogram
- Payment gateway donut, bar, and stacked bar
- State summary table with CSV download

---

## 🔑 Key Findings

1. **Tennis Shoes** generates the highest revenue, followed by Walking Shoes and Running Shoes.
2. **Shopify Payments** is the dominant payment method (~60% of revenue).
3. **Texas, California, and Florida** are the top 3 states by revenue.
4. **Wednesday and Thursday** are the highest-revenue days of the week.
5. **Peak sales hours** are 10 AM–2 PM and 7 PM–9 PM.
6. Average order value is ~**$620 USD**.
7. Most orders contain **1 unit** (84%+ single-item orders).
8. The **South** region leads all four US regions in revenue.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Data Extraction | office_read / pandas + openpyxl |
| Data Cleaning | pandas, numpy |
| EDA | plotly, matplotlib, seaborn |
| Star Schema | pandas (CSV output) |
| Dashboard | Streamlit, Plotly Express |
| BI Measures | DAX (Power BI compatible) |
| Report | Microsoft Word (.docx) |

---

## 👤 Author

Shopify Sales Analytics Project  
Generated: 2025 | Data Period: March 18–24, 2025
