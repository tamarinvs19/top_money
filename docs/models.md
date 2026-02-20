# Finance Manager - Data Models

## Overview

A web application for managing personal finances with support for multiple asset types and transaction categories.

---

## User Model

| Field      | Type        | Description                |
| ---------- | ----------- | -------------------------- |
| id         | UUID        | Primary key                |
| username   | String(150) | Unique username            |
| email      | EmailField  | User email                 |
| password   | Char(128)   | Hashed password            |
| first_name | String(30)  | First name                 |
| last_name  | String(150) | Last name                  |
| created_at | DateTime    | Account creation timestamp |
| updated_at | DateTime    | Last update timestamp      |

**Relationships:**

- One-to-Many: User → Asset (cascade delete)
- One-to-Many: User → Transaction (cascade delete)

---

## Asset Model

Represents any financial account or container for money.

| Field      | Type             | Description                        |
| ---------- | ---------------- | ---------------------------------- |
| id         | UUID             | Primary key                        |
| user       | ForeignKey(User) | Owner                              |
| name       | Char(100)        | Asset name (e.g., "Sberbank Card") |
| type       | Enum             | Asset type                         |
| currency   | Char(3)          | ISO currency code (RUB, USD, EUR)  |
| balance    | Decimal(15,2)    | Current balance                    |
| is_active  | Boolean          | Whether asset is active            |
| created_at | DateTime         | Creation timestamp                 |
| updated_at | DateTime         | Last update timestamp              |

### Asset Types

| Type        | Description                           |
| ----------- | ------------------------------------- |
| CASH        | Physical cash (case/wallet)           |
| DEBIT_CARD  | Debit card (bank account)              |
| DEPOSIT     | Bank deposit account                  |
| CREDIT_CARD | Credit card (negative balance = debt) |
| BROKERAGE   | Investment/brokerage account          |

### Asset-Specific Fields

---

#### 1. CASH (Physical Cash)

Physical money in wallet, safe, or other location.

| Field    | Type      | Description                           |
| -------- | --------- | ------------------------------------- |
| location | Char(100) | Where cash is stored (e.g., "Wallet") |

**Example:** "Cash in Wallet", "Emergency Fund Safe"

---

### CardAsset (Abstract Base Class)

Base class for card-based assets (debit and credit cards).

| Field         | Type      | Description                      |
| ------------- | --------- | -------------------------------- |
| bank_name     | Char(100) | Bank name (e.g., "Sberbank")     |
| last_4_digits | Char(4)   | Last 4 digits of card (optional) |

---

#### 2. DEBIT_CARD (Debit Card)

Debit card linked to a bank account. Inherits fields from CardAsset.

**No additional fields.**

**Example:** "Sberbank Debit Card", "Tinkoff Black"

---

#### 3. DEPOSIT (Bank Deposit)

Time deposit with interest accrual.

| Field          | Type         | Description                       |
| -------------- | ------------ | --------------------------------- |
| interest_rate  | Decimal(5,2) | Annual interest rate (e.g., 4.5)  |
| term_months    | Integer      | Deposit term in months            |
| renewal_date   | Date         | Auto-renewal date (optional)      |
| is_capitalized | Boolean      | Interest capitalized to principal |

**Example:** "Sberbank Savings Account", "Fixed Deposit 12 months"

---

#### 4. CREDIT_CARD (Credit Card)

Credit card with spending limit and grace period. Inherits fields from CardAsset.

| Field             | Type          | Description                                 |
| ----------------- | ------------- | ------------------------------------------- |
| credit_limit      | Decimal(15,2) | Maximum credit limit                        |
| grace_period_days | Integer       | Days to pay without interest (e.g., 25)     |
| billing_day       | Integer       | Day of month when billing cycle ends (1-31) |

**Example:** "Tinkoff All Credit", "Sberbank Gold"

---

#### 5. BROKERAGE (Brokerage Account)

Investment account for stocks, bonds, funds.

| Field          | Type      | Description                          |
| -------------- | --------- | ------------------------------------ |
| broker_name    | Char(100) | Broker name (e.g., "Tinkoff Invest") |
| account_number | Char(50)  | Broker account number (optional)     |
| account_type   | Enum      | Type: BROKERAGE, IIS, IRA            |

**Example:** "Tinkoff Invest", "Yandex Money Brokerage"

---

### Assets Fields Summary Table

| Field / Type   | CASH | CardAsset | DEBIT_CARD | DEPOSIT | CREDIT_CARD | BROKERAGE |
| -------------- | :--: | :-------: | :--------: | :-----: | :----------: | :-------: |
| name           |  ✓   |     ✓     |     ✓      |    ✓    |      ✓       |     ✓     |
| currency       |  ✓   |     ✓     |     ✓      |    ✓    |      ✓       |     ✓     |
| balance        |  ✓   |     ✓     |     ✓      |    ✓    |      ✓       |     ✓     |
| is_active      |  ✓   |     ✓     |     ✓      |    ✓    |      ✓       |     ✓     |
| location       |  ✓   |     -     |     -      |    -    |      -       |     -     |
| bank_name      |  -   |     ✓     |     ✓      |    ✓    |      ✓       |     -     |
| last_4_digits  |  -   |     ✓     |     ✓      |    -    |      ✓       |     -     |
| interest_rate  |  -   |     -     |     -      |    ✓    |      -       |     -     |
| term_months    |  -   |     -     |     -      |    ✓    |      -       |     -     |
| renewal_date   |  -   |     -     |     -      |    ✓    |      -       |     -     |
| credit_limit   |  -   |     -     |     -      |    -    |      ✓       |     -     |
| grace_period   |  -   |     -     |     -      |    -    |      ✓       |     -     |
| broker_name    |  -   |     -     |     -      |    -    |      -       |     ✓     |
| account_number |  -   |     -     |     -      |    -    |      -       |     ✓     |

---

## Transaction Model

Represents any movement of money between assets or external sources.

| Field       | Type              | Description                       |
| ----------- | ----------------- | --------------------------------- |
| id          | UUID              | Primary key                       |
| user        | ForeignKey(User)  | Owner                             |
| type        | Enum              | Transaction type                  |
| amount      | Decimal(15,2)     | Transaction amount                |
| currency    | Char(3)           | ISO currency code                 |
| from_asset  | ForeignKey(Asset) | Source asset (nullable)           |
| to_asset    | ForeignKey(Asset) | Destination asset (nullable)      |
| category    | Char(50)          | Category (e.g., "Food", "Salary") |
| description | Text              | Optional description              |
| date        | DateTime          | Transaction date                  |
| created_at  | DateTime          | Creation timestamp                |

### Transaction Types

| Type     | Description                       | Required Fields           |
| -------- | --------------------------------- | ------------------------- |
| REFILL   | Money coming in (income, deposit) | `to_asset`, `-from_asset` |
| WASTE    | Money going out (expense)         | `from_asset`, `-to_asset` |
| TRANSFER | Money between assets              | `from_asset`, `to_asset`  |

### Transaction Rules

- **REFILL**: `from_asset` is NULL, `to_asset` is required
- **WASTE**: `from_asset` is required, `to_asset` is NULL
- **TRANSFER**: Both `from_asset` and `to_asset` are required

---

## Relationships Diagram

```
User (1) ----< (N) Asset
     |
     └----< (N) Transaction
                |
                ├----> Asset (from_asset)
                └----> Asset (to_asset)
```

---

## Example Usage

### Adding Cash to Bank Card (Refill)

```
type: REFILL
from_asset: NULL
to_asset: Bank Card "Sberbank"
amount: 50000.00
category: "Salary"
```

### Paying for Groceries (Waste)

```
type: WASTE
from_asset: Bank Card "Sberbank"
to_asset: NULL
amount: 3500.00
category: "Food"
```

### Transferring Between Cards (Transfer)

```
type: TRANSFER
from_asset: Bank Card "Sberbank"
to_asset: Bank Card "Tinkoff"
amount: 10000.00
category: "Transfer"
```
