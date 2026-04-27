# 20-Year Term Life Insurance Pricing and Profit Testing

## 1. Project Overview

This project prices a 20-year term life insurance policy for a male age 30 with a face amount of $500,000. It calculates net premium, gross premium (including expenses and profit margin), performs profit testing, computes PVFP, determines the break-even year, and stores results in a SQLite database. All mortality assumptions are based on the SOA FAM Standard Ultimate Life Table.

---

## 2. Assumptions and Notation

### 2.1 Mortality Assumptions

| Symbol | Description | Value/Source |
|--------|-------------|---------------|
| \(l_x\) | Number of survivors at age \(x\) | FAM table (ages 30-49) |
| \(q_x\) | Probability of death between age \(x\) and \(x+1\) | FAM table (ages 30-49) |

### 2.2 Financial Assumptions

| Symbol | Description | Value |
|--------|-------------|-------|
| \(F\) | Face amount / benefit | 500,000 |
| \(i\) | Pricing interest rate | 0.045 (4.5%) |
| \(v\) | Discount factor | \(1 / (1 + i)\) |
| \(n\) | Policy term (years) | 20 |
| \(x\) | Issue age | 30 |
| \(r\) | Risk discount rate (for PVFP) | 0.10 (10%) |

### 2.3 Expense Assumptions

| Symbol | Description | Value | Timing |
|--------|-------------|-------|--------|
| \(E_1\) | First-year expense | 800 | Beginning of year 1 |
| \(E_r\) | Renewal expense (years 2 to \(n\)) | 80 | Beginning of each year |

### 2.4 Profit Assumptions

| Symbol | Description | Value |
|--------|-------------|-------|
| \(\pi\) | Profit margin (% of gross premium) | 0.15 (15%) |

### 2.5 Discounting Conventions

| Item | Convention |
|------|------------|
| Premiums and benefits | Discrete (year-end for benefits, beginning-of-year for premiums) |
| Profits (for PVFP) | Mid-year discounting \((t + 0.5)\) |

---

## 3. Actuarial Formulas

### 3.1 Normalization

\[
l_x^{\text{norm}} = \frac{l_x}{l_{30}}, \quad d_x = l_x^{\text{norm}} \cdot q_x
\]

Note: \(d_x\) is the unconditional probability of death at age \(x\) from issue age 30.

### 3.2 Present Value of Benefits

**Original formula**:
\[
A_{x:\overline{n}|}^1 = \sum_{t=0}^{n-1} v^{t+1} \cdot {}_tp_x \cdot q_{x+t}
\]

**Derivation**:
- \({}_tp_x\) = probability a life age \(x\) survives to age \(x+t\)
- \(q_{x+t}\) = probability a life age \(x+t\) dies within one year
- Their product \({}_tp_x \cdot q_{x+t}\) is the unconditional probability of dying at age \(x+t\)
- Multiply by \(v^{t+1}\) (discount from end of year \(t+1\))

**In this project**:
\[
A = \sum_{t=0}^{n-1} v^{t+1} \cdot d_{x+t}
\]
where \(d_{x+t} = l_{x+t}^{\text{norm}} \cdot q_{x+t}\) represents \({}_tp_x \cdot q_{x+t}\).

**Note**: \(A\) in the code corresponds to \(A_{30:\overline{20}|}^1\) (term life annuity factor).

### 3.3 Present Value of Premiums

**Original formula**:
\[
\ddot{a}_{x:\overline{n}|} = \sum_{t=0}^{n-1} v^t \cdot {}_tp_x
\]

**Derivation**:
- Premiums are paid at the **beginning** of each year if the insured is alive
- \({}_tp_x\) = probability of surviving to age \(x+t\) to pay the premium
- Multiply by \(v^t\) (discount from beginning of year \(t\))

**In this project**:
\[
\ddot{a} = \sum_{t=0}^{n-1} v^t \cdot l_{x+t}^{\text{norm}}
\]
where \(l_{x+t}^{\text{norm}} = {}_tp_x\).

**Note**: \(\ddot{a}\) in the code corresponds to \(\ddot{a}_{30:\overline{20}|}\).

### 3.4 Net Premium (Equivalence Principle)

\[
P_{\text{net}} = \frac{F \cdot A}{\ddot{a}}
\]

### 3.5 Gross Premium (with Expenses and Profit)

**Original equation**:
\[
P_{\text{gross}} \cdot \ddot{a} = F \cdot A + E_1 + E_r \cdot (\ddot{a} - 1) + \pi \cdot P_{\text{gross}} \cdot \ddot{a}
\]

**Derivation of each term**:
- Left side: present value of gross premium income
- Right side:
  - \(F \cdot A\) = present value of death benefits
  - \(E_1\) = present value of first-year expense (paid at time 0)
  - \(E_r \cdot (\ddot{a} - 1)\) = present value of renewal expenses (paid at beginnings of years 2 to \(n\))
  - \(\pi \cdot P_{\text{gross}} \cdot \ddot{a}\) = present value of profit (profit margin × premium income PV)

**Solving**:
\[
P_{\text{gross}} \cdot \ddot{a} - \pi \cdot P_{\text{gross}} \cdot \ddot{a} = F \cdot A + E_1 + E_r \cdot (\ddot{a} - 1)
\]
\[
P_{\text{gross}} \cdot \ddot{a} \cdot (1 - \pi) = F \cdot A + E_1 + E_r \cdot (\ddot{a} - 1)
\]
\[
P_{\text{gross}} = \frac{F \cdot A + E_1 + E_r \cdot (\ddot{a} - 1)}{\ddot{a} \cdot (1 - \pi)}
\]

### 3.6 Reserve Calculation (Recursive)

**Original formula**:
\[
(V_t + P_{\text{net}}) \cdot (1 + i) = q_{x+t} \cdot F + p_{x+t} \cdot V_{t+1}
\]

**Derivation**:
- Start of year \(t\): company has reserve \(V_t\) and receives premium \(P_{\text{net}}\)
- Total funds = \(V_t + P_{\text{net}}\)
- After one year at interest rate \(i\): \((V_t + P_{\text{net}}) \cdot (1 + i)\)
- From this, pay death benefits to those who die: \(q_{x+t} \cdot F\)
- Remaining funds belong to survivors, who need reserve \(V_{t+1}\) each
- Divide by survival probability \(p_{x+t}\) to get reserve **per survivor**

**Solving for \(V_{t+1}\)**:
\[
V_{t+1} = \frac{(V_t + P_{\text{net}}) \cdot (1 + i) - q_{x+t} \cdot F}{p_{x+t}}
\]

**In this project**:
- \(q_{x+t} = \dfrac{d_{x+t}}{l_{x+t}^{\text{norm}}}\)
- \(p_{x+t} = 1 - q_{x+t}\)
- \(V_{t+1} \geq 0\) (reserve cannot be negative)

### 3.7 Annual Profit

**Formula**:
\[
\text{Profit}_t = P_{\text{gross}} - \text{Expense}_t - \text{Claims}_t - (V_{t+1} - V_t)
\]

**Explanation of terms**:
- \(P_{\text{gross}}\): gross premium received at beginning of year
- \(\text{Expense}_t\): expenses paid at beginning of year (\(E_1\) in year 1, \(E_r\) in years 2+)
- \(\text{Claims}_t\): expected death benefits paid at end of year = \(d_{x+t} \cdot F\)
  - This is NOT a fee for processing claims. It is the actual benefit amount paid to beneficiaries when the insured dies.
- \(V_{t+1} - V_t\): change in reserve (increase = cost, decrease = release of funds)

**Note**: The negative sign before \((V_{t+1} - V_t)\) means:
- If reserve increases (\(V_{t+1} > V_t\)), profit decreases (money is locked away)
- If reserve decreases (\(V_{t+1} < V_t\)), profit increases (money is released)

### 3.8 Discounted Profit and PVFP

Let \(v_{\text{risk}} = 1 / (1 + r)\). Using mid-year discounting:

\[
\text{PV}(\text{Profit}_t) = \text{Profit}_t \cdot v_{\text{risk}}^{\,t + 0.5}
\]

\[
\text{PVFP} = \sum_{t=0}^{n-1} \text{PV}(\text{Profit}_t)
\]

### 3.9 Break-even Year

The smallest \(t\) such that cumulative \(\text{PV}(\text{Profit}) > 0\).

---

## 4. File Structure and Execution Steps

### 4.1 Required Files

```
project/
├── fam_tables_2024.pdf              # Original FAM table (reference only)
├── parse_SULT.py                    # Step 1: Parse table to Excel
├── premium_from_vlookup.py          # Step 3: Premium calculation
├── profit_with_sqlite.py            # Step 4: Profit testing + SQLite
└── README.md                        # This document
```

### 4.2 Step 1: Parse FAM Table

**File**: `parse_SULT.py`

**Background**:
The original FAM mortality table was manually copied from `fam_tables_2024.pdf` (pages 20-21) into a text string inside `parse_SULT.py`. Python's `pandas` library then converted this text string into a DataFrame and exported it as an Excel file with the sheet name `SULT`.

### 4.3 Step 2: Create VLOOKUP Sheet (Manual in Excel)

**File**: `fam_SULT_30_to_49.xlsx`

**Action**:
1. Open `fam_SULT_30_to_49.xlsx`
2. Create new sheet named `qx_extracted`
3. Enter headers: A1="age", B1="qx", C1="lx"
4. Enter ages 30-49 in column A (A2:A21)
5. B2 formula: `=VLOOKUP(A2, SULT!$A$2:$M$21, 3, FALSE)` and drag down
6. C2 formula: `=VLOOKUP(A2, SULT!$A$2:$M$21, 2, FALSE)` and drag down
7. Save the file

### 4.4 Step 3: Calculate Premiums

**File**: `premium_from_vlookup.py`

**Action**:
- Reads qx and lx from `qx_extracted` sheet
- Normalizes lx (sets \(l_{30}^{\text{norm}} = 1\))
- Calculates \(A\), \(\ddot{a}\), \(P_{\text{net}}\), \(P_{\text{gross}}\)
- Writes \(l_x^{\text{norm}}\) back to column D

### 4.5 Step 4: Profit Testing and SQLite

**File**: `profit_with_sqlite.py`

**Action**:
- Same premium calculation as Step 3
- Calculates reserves recursively using the formula in Section 3.6
- Computes annual profit, discounted profit (mid-year), and cumulative PV
- Writes results to SQLite database
- Displays table and break-even year

---

## 5. Commands to Run Everything

```bash
# Install dependencies
pip install pandas numpy openpyxl

# Step 1: Parse FAM table to Excel
python parse_SULT.py

# Step 2: Manual Excel VLOOKUP (see Section 4.3)

# Step 3: Calculate premiums
python premium_from_vlookup.py

# Step 4: Profit testing with SQLite
python profit_with_sqlite.py
```

---

## 6. Modifiable Variables

To test different scenarios, modify the following variables at the top of each `.py` file.

### In both `premium_from_vlookup.py` and `profit_with_sqlite.py`

| Variable | Location | Description | Example Changes |
|----------|----------|-------------|-----------------|
| `face` | Product assumptions | Face amount / benefit | 250000, 1000000 |
| `i` | Product assumptions | Interest rate | 0.03, 0.05, 0.06 |
| `term` | Product assumptions | Policy term (max 20) | 10, 15 |
| `exp_first` | Expenses and profit | First-year expense | 500, 1000 |
| `exp_renew` | Expenses and profit | Renewal expense | 50, 100 |
| `profit_rate` | Expenses and profit | Profit margin | 0.10, 0.20 |

### In `profit_with_sqlite.py` only

| Variable | Location | Description | Example Changes |
|----------|----------|-------------|-----------------|
| `risk_discount` | Profit section | Risk discount rate | 0.08, 0.12 |

**Note**: `term` cannot exceed 20 without extending the mortality table (ages 30-49 only).

---

## 7. Key Results

| Metric | Value |
|--------|-------|
| Net premium (\(P_{\text{net}}\)) | $251.34 / year |
| Gross premium (\(P_{\text{gross}}\)) | $452.34 / year |
| PVFP | $101.74 |
| Break-even year | Year 14 |

---

## 8. Dependencies

- Python 3.x
- pandas
- numpy
- openpyxl
- sqlite3 (included in Python standard library)