"""
Data pipeline: cleans the raw Shopify Sales xlsx and generates
all star schema CSV files into the correct project folders.
"""
import pandas as pd
import numpy as np
import os

BASE = os.path.dirname(os.path.abspath(__file__))
RAW   = os.path.join(BASE, 'data', 'raw', 'Shopify Sales.xlsx')
CLEAN = os.path.join(BASE, 'data', 'cleaned')
STAR  = os.path.join(BASE, 'data', 'star_schema')
os.makedirs(CLEAN, exist_ok=True)
os.makedirs(STAR,  exist_ok=True)

print("Loading raw data...")
df_raw = pd.read_excel(RAW, sheet_name='shopify_sales')
print(f"Raw shape: {df_raw.shape}")

df = df_raw.copy()

# Rename columns
df.columns = [
    'line_item_id','order_number','country','first_name','last_name',
    'province','zip_code','city','currency','customer_id',
    'invoice_date','gateway','product_id','product_type',
    'variant_id','quantity','subtotal_price','total_price_usd','total_tax'
]

# Deduplication
before = len(df)
df.drop_duplicates(inplace=True)
print(f"Duplicates removed: {before - len(df)}")

# Types
df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce')
for col in ['quantity','subtotal_price','total_price_usd','total_tax']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df['customer_id'] = df['customer_id'].astype(str)
df['product_id']  = df['product_id'].astype(str)
df['variant_id']  = df['variant_id'].astype(str)
df['order_number']= df['order_number'].astype(str)

# Missing values
df['product_id'] = df['product_id'].fillna('UNKNOWN')
df['variant_id'] = df['variant_id'].fillna('UNKNOWN')
before = len(df)
df.dropna(subset=['subtotal_price','total_price_usd','total_tax','invoice_date'], inplace=True)
print(f"Null financials removed: {before - len(df)}")

# Standardise strings
df['city']         = df['city'].str.strip().str.upper()
df['province']     = df['province'].str.strip().str.title()
df['country']      = df['country'].str.strip().str.title()
df['gateway']      = df['gateway'].str.strip().str.lower()
df['product_type'] = df['product_type'].str.strip().str.title()
df['currency']     = df['currency'].str.strip().str.upper()
df['product_type'] = df['product_type'].replace({"Boy'S":"Boy's Shoes","Boy's":"Boy's Shoes"})
gateway_map = {
    'shopify_payments':'Shopify Payments','paypal':'PayPal',
    'amazon_payments':'Amazon Pay','gift_card':'Gift Card','manual':'Manual'
}
df['gateway'] = df['gateway'].map(gateway_map).fillna(df['gateway'])

# Remove invalid rows
before = len(df)
df = df[(df['quantity']>=1)&(df['quantity']<=20)]
df = df[(df['total_price_usd']>0)&(df['subtotal_price']>0)]
print(f"Invalid rows removed: {before - len(df)}")

# Feature engineering
df['order_date']     = df['invoice_date'].dt.date
df['order_year']     = df['invoice_date'].dt.year
df['order_month']    = df['invoice_date'].dt.month
df['order_month_name']= df['invoice_date'].dt.strftime('%B')
df['order_week']     = df['invoice_date'].dt.isocalendar().week.astype(int)
df['order_day']      = df['invoice_date'].dt.day
df['day_of_week']    = df['invoice_date'].dt.day_name()
df['hour']           = df['invoice_date'].dt.hour
df['unit_price']     = (df['subtotal_price'] / df['quantity']).round(2)
df['tax_rate']       = (df['total_tax'] / df['subtotal_price'] * 100).round(2)
df['customer_full_name'] = df['first_name'] + ' ' + df['last_name']
region_map = {
    'California':'West','Oregon':'West','Washington':'West','Nevada':'West',
    'Arizona':'West','Utah':'West','Colorado':'West','Montana':'West',
    'Idaho':'West','Wyoming':'West','Alaska':'West','Hawaii':'West','New Mexico':'West',
    'Texas':'South','Florida':'South','Georgia':'South','North Carolina':'South',
    'South Carolina':'South','Virginia':'South','Tennessee':'South','Alabama':'South',
    'Mississippi':'South','Arkansas':'South','Louisiana':'South','Oklahoma':'South',
    'Kentucky':'South','West Virginia':'South','Maryland':'South',
    'District Of Columbia':'South','Delaware':'South',
    'New York':'Northeast','Pennsylvania':'Northeast','New Jersey':'Northeast',
    'Massachusetts':'Northeast','Connecticut':'Northeast','Rhode Island':'Northeast',
    'New Hampshire':'Northeast','Vermont':'Northeast','Maine':'Northeast',
    'Illinois':'Midwest','Ohio':'Midwest','Michigan':'Midwest','Indiana':'Midwest',
    'Wisconsin':'Midwest','Minnesota':'Midwest','Iowa':'Midwest','Missouri':'Midwest',
    'North Dakota':'Midwest','South Dakota':'Midwest','Nebraska':'Midwest','Kansas':'Midwest',
}
df['region'] = df['province'].map(region_map).fillna('Other')

# Save cleaned
df.to_csv(os.path.join(CLEAN, 'shopify_sales_cleaned.csv'), index=False)
print(f"Cleaned CSV saved: {len(df)} rows")

# ── DimDate ──────────────────────────────────────────────────────────────────
date_range = pd.date_range(start=df['invoice_date'].min().date(),
                           end=df['invoice_date'].max().date(), freq='D')
dim_date = pd.DataFrame({'full_date': date_range})
dim_date['date_key']       = dim_date['full_date'].dt.strftime('%Y%m%d').astype(int)
dim_date['year']           = dim_date['full_date'].dt.year
dim_date['month']          = dim_date['full_date'].dt.month
dim_date['month_name']     = dim_date['full_date'].dt.strftime('%B')
dim_date['quarter']        = dim_date['full_date'].dt.quarter
dim_date['quarter_name']   = 'Q' + dim_date['quarter'].astype(str)
dim_date['week']           = dim_date['full_date'].dt.isocalendar().week.astype(int)
dim_date['day']            = dim_date['full_date'].dt.day
dim_date['day_of_week_num']= dim_date['full_date'].dt.dayofweek
dim_date['day_name']       = dim_date['full_date'].dt.day_name()
dim_date['is_weekend']     = dim_date['day_of_week_num'].isin([5,6]).astype(int)
dim_date.to_csv(os.path.join(STAR,'DimDate.csv'), index=False)
print(f"DimDate: {dim_date.shape}")

# ── DimProduct ───────────────────────────────────────────────────────────────
dim_product = df[['product_id','product_type','variant_id']].drop_duplicates(subset=['product_id','variant_id']).reset_index(drop=True)
dim_product.insert(0,'product_key', range(1, len(dim_product)+1))
dim_product['product_category'] = dim_product['product_type'].apply(
    lambda x: 'Footwear' if any(w in x for w in ['Shoe','Boot','Sandal','Flip','Clog','Water']) else
             ('Apparel' if x=='Jackets' else ('Gift' if x=='Gift Card' else 'Other'))
)
dim_product.to_csv(os.path.join(STAR,'DimProduct.csv'), index=False)
print(f"DimProduct: {dim_product.shape}")

# ── DimCustomer ──────────────────────────────────────────────────────────────
dim_customer = df[['customer_id','first_name','last_name','customer_full_name']].drop_duplicates(subset=['customer_id']).reset_index(drop=True)
dim_customer.insert(0,'customer_key', range(1, len(dim_customer)+1))
dim_customer.to_csv(os.path.join(STAR,'DimCustomer.csv'), index=False)
print(f"DimCustomer: {dim_customer.shape}")

# ── DimLocation ───────────────────────────────────────────────────────────────
dim_location = df[['city','province','country','zip_code']].drop_duplicates(subset=['city','province']).reset_index(drop=True)
dim_location.insert(0,'location_key', range(1, len(dim_location)+1))
dim_location['region'] = dim_location['province'].map(region_map).fillna('Other')
dim_location.to_csv(os.path.join(STAR,'DimLocation.csv'), index=False)
print(f"DimLocation: {dim_location.shape}")

# ── DimPayment ────────────────────────────────────────────────────────────────
dim_payment = df[['gateway']].drop_duplicates().reset_index(drop=True)
dim_payment.insert(0,'payment_key', range(1, len(dim_payment)+1))
payment_type_map = {
    'Shopify Payments':'Digital Wallet','PayPal':'Digital Wallet',
    'Amazon Pay':'Digital Wallet','Gift Card':'Store Credit','Manual':'Manual'
}
dim_payment['payment_type'] = dim_payment['gateway'].map(payment_type_map).fillna('Other')
dim_payment['is_online'] = (dim_payment['gateway'] != 'Manual').astype(int)
dim_payment.to_csv(os.path.join(STAR,'DimPayment.csv'), index=False)
print(f"DimPayment: {dim_payment.shape}")

# ── FactSales ─────────────────────────────────────────────────────────────────
df['date_key'] = df['invoice_date'].dt.strftime('%Y%m%d').astype(int)
fact = df.merge(dim_product[['product_key','product_id','variant_id']], on=['product_id','variant_id'], how='left')
fact = fact.merge(dim_customer[['customer_key','customer_id']], on='customer_id', how='left')
fact = fact.merge(dim_location[['location_key','city','province']], on=['city','province'], how='left')
fact = fact.merge(dim_payment[['payment_key','gateway']], on='gateway', how='left')
fact_sales = fact[[
    'line_item_id','order_number','date_key',
    'product_key','customer_key','location_key','payment_key',
    'quantity','unit_price','subtotal_price','total_price_usd','total_tax','tax_rate'
]].copy()
fact_sales.to_csv(os.path.join(STAR,'FactSales.csv'), index=False)
print(f"FactSales: {fact_sales.shape}")

# Also copy cleaned CSV to dashboard folder
import shutil
dash_clean = os.path.join(BASE,'dashboard','data','cleaned','shopify_sales_cleaned.csv')
os.makedirs(os.path.dirname(dash_clean), exist_ok=True)
shutil.copy(os.path.join(CLEAN,'shopify_sales_cleaned.csv'), dash_clean)
print("Copied cleaned CSV to dashboard/data/cleaned/")
print("\n=== PIPELINE COMPLETE ===")
