import pandas as pd
import numpy as np
import sqlite3

# Read from VLOOKUP sheet
df = pd.read_excel("fam_SULT_30_to_49.xlsx", sheet_name="qx_extracted")

# Normalize
lx_30 = df.loc[df['age'] == 30, 'lx'].values[0]
df['lx_norm'] = df['lx'] / lx_30
df['dx'] = df['lx_norm'] * df['qx']

# Product assumptions
face = 500000
i = 0.045
v = 1 / (1 + i)
term = 20

lx = df['lx_norm'].values[:term]
dx = df['dx'].values[:term]

t = np.arange(term)
v_t = v ** t
v_d = v ** (t + 1)

A = np.sum(v_d * dx)
a = np.sum(v_t * lx)

net_premium = face * A / a

# Expenses and profit
exp_first = 800
exp_renew = 80
profit_rate = 0.15

numerator = face * A + exp_first + exp_renew * (a - 1)
denominator = a * (1 - profit_rate)
gross_premium = numerator / denominator

# Calculate reserve
net_premium_reserve = net_premium
reserve = np.zeros(term + 1)
for year in range(term):
    q = dx[year] / lx[year] if lx[year] > 0 else 0
    p = 1 - q
    start = 0 if year == 0 else reserve[year]
    end = ((start + net_premium_reserve) * (1 + i) - q * face) / p
    reserve[year + 1] = max(end, 0)

# Profit
risk_discount = 0.10 # i
df_discount = 1 / (1 + risk_discount) # v = 1/(1+i)
profit = []
pv = [] # empty list to store present value of future premium of every year
cum = 0 # present value of cumulative pvfp
cum_list = [] # 

for year in range(term):
    expense = exp_first if year == 0 else exp_renew
    claims = dx[year] * face
    delta_res = reserve[year + 1] - reserve[year] # change in reserve
    p = gross_premium - expense - claims - delta_res # benefit of that year
    profit.append(p)
    
    pv_year = p * (df_discount ** (year + 0.5)) # profits are assumed to occur mid-year
    pv.append(pv_year)
    cum += pv_year
    cum_list.append(cum)

# Write to SQLite
conn = sqlite3.connect("profit.db")
df_profit = pd.DataFrame({
    'year': range(1, term + 1),
    'profit': profit,
    'pv_profit': pv,
    'cumulative_pv': cum_list
})
df_profit.to_sql("profit_table", conn, if_exists="replace", index=False)

# SQL query: all years with profit, pv_profit, cumulative_pv
query = "SELECT year, profit, pv_profit, cumulative_pv FROM profit_table"
all_years = pd.read_sql(query, conn)
print("\nAll years (profit, discounted profit, cumulative discounted profit):")
print(all_years.to_string(index=False))

# Find break-even year
query2 = "SELECT year, cumulative_pv FROM profit_table WHERE cumulative_pv > 0 ORDER BY year LIMIT 1" # get only the first row to find the first year that cumulative pv > 0
break_even = pd.read_sql(query2, conn)
if not break_even.empty:
    print(f"\nBreak-even year: {break_even['year'].values[0]} (cumulative PV = {break_even['cumulative_pv'].values[0]:.2f})")
else:
    print("\nNo break-even year within policy term")

conn.close()

print(f"\nGross premium: {gross_premium:.2f}")
print(f"Final cumulative PV (PVFP): {cum:.2f}")