# 📐 DAX Measures — Shopify Sales Analytics

> All measures are written for Power BI using the Star Schema model:  
> `FactSales`, `DimDate`, `DimProduct`, `DimCustomer`, `DimLocation`, `DimPayment`

---

## 1. Core Revenue Measures

### Total Revenue
```dax
Total Revenue =
SUM ( FactSales[total_price_usd] )
```

### Total Subtotal
```dax
Total Subtotal =
SUM ( FactSales[subtotal_price] )
```

### Total Tax Collected
```dax
Total Tax =
SUM ( FactSales[total_tax] )
```

### Total Units Sold
```dax
Total Units Sold =
SUM ( FactSales[quantity] )
```

---

## 2. Order Measures

### Total Orders
```dax
Total Orders =
DISTINCTCOUNT ( FactSales[order_number] )
```

### Total Line Items
```dax
Total Line Items =
COUNTROWS ( FactSales )
```

### Average Order Value (AOV)
```dax
AOV =
DIVIDE (
    [Total Revenue],
    [Total Orders],
    0
)
```

### Average Items per Order
```dax
Avg Items per Order =
DIVIDE (
    [Total Units Sold],
    [Total Orders],
    0
)
```

---

## 3. Customer Measures

### Total Customers
```dax
Total Customers =
DISTINCTCOUNT ( FactSales[customer_key] )
```

### Revenue per Customer
```dax
Revenue per Customer =
DIVIDE (
    [Total Revenue],
    [Total Customers],
    0
)
```

### Repeat Customers
```dax
Repeat Customers =
COUNTROWS (
    FILTER (
        SUMMARIZE (
            FactSales,
            FactSales[customer_key],
            "OrderCount", DISTINCTCOUNT ( FactSales[order_number] )
        ),
        [OrderCount] > 1
    )
)
```

### Repeat Customer Rate %
```dax
Repeat Customer Rate % =
DIVIDE (
    [Repeat Customers],
    [Total Customers],
    0
) * 100
```

### Customer Lifetime Value (CLV)
```dax
Customer LTV =
DIVIDE (
    [Total Revenue],
    [Total Customers],
    0
)
```

---

## 4. Product Measures

### Unique Product Types
```dax
Unique Product Types =
DISTINCTCOUNT ( DimProduct[product_type] )
```

### Avg Unit Price
```dax
Avg Unit Price =
DIVIDE (
    SUM ( FactSales[subtotal_price] ),
    SUM ( FactSales[quantity] ),
    0
)
```

### Revenue by Product Type
```dax
Revenue by Product =
CALCULATE (
    [Total Revenue],
    ALLEXCEPT ( DimProduct, DimProduct[product_type] )
)
```

### Product Revenue Share %
```dax
Product Revenue Share % =
DIVIDE (
    [Total Revenue],
    CALCULATE ( [Total Revenue], ALL ( DimProduct ) ),
    0
) * 100
```

### Top Product by Revenue
```dax
Top Product =
CALCULATE (
    SELECTEDVALUE ( DimProduct[product_type] ),
    TOPN ( 1,
        SUMMARIZE ( FactSales, DimProduct[product_type], "Rev", [Total Revenue] ),
        [Rev], DESC
    )
)
```

---

## 5. Date / Time Intelligence Measures

### Revenue MTD
```dax
Revenue MTD =
TOTALMTD ( [Total Revenue], DimDate[full_date] )
```

### Revenue WTD
```dax
Revenue WTD =
TOTALWTD ( [Total Revenue], DimDate[full_date] )
```

### Revenue YTD
```dax
Revenue YTD =
TOTALYTD ( [Total Revenue], DimDate[full_date] )
```

### Daily Avg Revenue
```dax
Daily Avg Revenue =
AVERAGEX (
    VALUES ( DimDate[full_date] ),
    [Total Revenue]
)
```

### Peak Revenue Day
```dax
Peak Revenue Day =
CALCULATE (
    FORMAT ( MAX ( DimDate[full_date] ), "YYYY-MM-DD" ),
    TOPN ( 1,
        SUMMARIZE ( FactSales, DimDate[full_date], "DailyRev", [Total Revenue] ),
        [DailyRev], DESC
    )
)
```

---

## 6. Tax Measures

### Effective Tax Rate %
```dax
Effective Tax Rate % =
DIVIDE (
    [Total Tax],
    [Total Subtotal],
    0
) * 100
```

### Avg Tax per Order
```dax
Avg Tax per Order =
DIVIDE (
    [Total Tax],
    [Total Orders],
    0
)
```

---

## 7. Geographic Measures

### Unique States
```dax
Unique States =
DISTINCTCOUNT ( DimLocation[province] )
```

### Unique Cities
```dax
Unique Cities =
DISTINCTCOUNT ( DimLocation[city] )
```

### Revenue per State
```dax
Revenue per State =
DIVIDE (
    [Total Revenue],
    [Unique States],
    0
)
```

### Top State by Revenue
```dax
Top State =
CALCULATE (
    SELECTEDVALUE ( DimLocation[province] ),
    TOPN ( 1,
        SUMMARIZE ( FactSales, DimLocation[province], "Rev", [Total Revenue] ),
        [Rev], DESC
    )
)
```

---

## 8. Payment Measures

### Revenue — Shopify Payments
```dax
Revenue Shopify Payments =
CALCULATE (
    [Total Revenue],
    DimPayment[gateway] = "Shopify Payments"
)
```

### Revenue — PayPal
```dax
Revenue PayPal =
CALCULATE (
    [Total Revenue],
    DimPayment[gateway] = "PayPal"
)
```

### Online Payment Rate %
```dax
Online Payment Rate % =
DIVIDE (
    CALCULATE ( [Total Revenue], DimPayment[is_online] = 1 ),
    [Total Revenue],
    0
) * 100
```

### Gateway Revenue Share %
```dax
Gateway Revenue Share % =
DIVIDE (
    [Total Revenue],
    CALCULATE ( [Total Revenue], ALL ( DimPayment ) ),
    0
) * 100
```

---

## 9. Ranking Measures

### Revenue Rank (Product)
```dax
Product Revenue Rank =
RANKX (
    ALL ( DimProduct[product_type] ),
    [Total Revenue],
    ,
    DESC,
    Dense
)
```

### Revenue Rank (State)
```dax
State Revenue Rank =
RANKX (
    ALL ( DimLocation[province] ),
    [Total Revenue],
    ,
    DESC,
    Dense
)
```

### Customer Revenue Rank
```dax
Customer Revenue Rank =
RANKX (
    ALL ( DimCustomer[customer_id] ),
    [Total Revenue],
    ,
    DESC,
    Dense
)
```

---

## 10. Advanced Measures

### Running Total Revenue
```dax
Running Total Revenue =
CALCULATE (
    [Total Revenue],
    FILTER (
        ALLSELECTED ( DimDate[full_date] ),
        DimDate[full_date] <= MAX ( DimDate[full_date] )
    )
)
```

### Revenue % of Total
```dax
Revenue % of Total =
DIVIDE (
    [Total Revenue],
    CALCULATE ( [Total Revenue], ALL ( FactSales ) ),
    0
) * 100
```

### Orders with Multi-Item
```dax
Multi-Item Orders =
COUNTROWS (
    FILTER (
        SUMMARIZE (
            FactSales,
            FactSales[order_number],
            "TotalQty", SUM ( FactSales[quantity] )
        ),
        [TotalQty] > 1
    )
)
```

### Conversion Rate Proxy (Orders / Customers)
```dax
Orders per Customer =
DIVIDE (
    [Total Orders],
    [Total Customers],
    0
)
```

---

## 📌 Notes

- All measures reference tables in the star schema model: `FactSales`, `DimDate`, `DimProduct`, `DimCustomer`, `DimLocation`, `DimPayment`.
- Use `CALCULATE` with `ALLEXCEPT`/`ALL` to remove unwanted filter contexts.
- Time intelligence functions (`TOTALMTD`, `TOTALYTD`) require `DimDate[full_date]` to be marked as a **Date Table** in Power BI.
- For Python/Pandas equivalents of these KPIs, see the Jupyter Notebook `shopify_analytics.ipynb`.
