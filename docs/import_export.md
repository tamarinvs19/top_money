# Import/Export Table Format

## Overview

Transaction data can be imported from Excel (.xlsx) or CSV (.csv) files, and exported to Excel format.

---

## Column Format

| Column       | Required | Format                      | Description                              |
| ------------ | :------: | --------------------------- | ---------------------------------------- |
| Date         | Yes      | `YYYY-MM-DD HH:MM`         | Transaction date and time                |
| Type         | Yes      | Text                        | Refill, Waste, or Transfer               |
| Category     | No       | Text                        | Transaction category                     |
| Amount       | Yes      | Decimal                     | Transaction amount                       |
| Currency     | No       | Text (default: RUB)         | ISO currency code (RUB, USD, EUR, etc.) |
| From Asset   | No       | Text                        | Source asset name (e.g., "DEBIT_CARD: Sberbank") |
| To Asset     | No       | Text                        | Destination asset name                   |
| Description  | No       | Text                        | Optional description                     |

---

## Supported Transaction Types

| Type         | Description                       |
| ------------ | --------------------------------- |
| Refill       | Money coming in (income, deposit) |
| Waste        | Money going out (expense)         |
| Transfer     | Money between assets             |

---

## Asset Name Format

When specifying assets in import files, use the format:

```
TYPE: AssetName
```

Examples:
- `DEBIT_CARD: Sberbank`
- `CASH: Wallet`
- `CREDIT_CARD: Tinkoff All`

---

## Category Values

### Waste Categories
- PRODUCTS
- CAFE_AND_RESTAURANTS
- TRANSPORT
- HCS
- HOUSEHOLD
- PERSONAL
- LEISURE
- ENTERTAINMENT
- CLOTHING_AND_SHOES
- SPORT
- HEALTH_AND_BEAUTY
- SUBSCRIPTIONS
- TAXES_AND_PENALTIES
- LEARNING
- GIFTS
- TECHNIQUE
- TRAVELING
- REALTY
- OTHER_WASTE

### Refill Categories
- SALARY
- BONUS
- CASHBACK
- INTEREST
- SALE
- INVESTMENT
- OTHER_REFILL

---

## Example CSV

```csv
Date,Type,Category,Amount,Currency,From Asset,To Asset,Description
2024-01-15 10:30,WASTE,PRODUCTS,2500.00,RUB,DEBIT_CARD: Sberbank,,Grocery shopping
2024-01-16 14:00,REFILL,SALARY,50000.00,RUB,,DEBIT_CARD: Sberbank,Monthly salary
2024-01-17 09:15,WASTE,CAFE_AND_RESTAURANTS,1500.00,RUB,DEBIT_CARD: Sberbank,,Lunch with colleagues
2024-01-18 12:00,TRANSFER,,10000.00,RUB,DEBIT_CARD: Sberbank,DEBIT_CARD: Tinkoff,Transfer to investment
```

---

## Import Instructions

1. Go to **Profile** → **Load Transactions**
2. Select an Excel (.xlsx) or CSV (.csv) file
3. Click **Load**
4. Review the success message with imported count

---

## Export Instructions

1. Go to **Profile** → **Download Transactions**
2. A .xlsx file will be downloaded with all your transactions
