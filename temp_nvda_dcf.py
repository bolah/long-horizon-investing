"""
NVIDIA (NVDA) Long-Horizon DCF Valuation
Terminal-value-driven model using normalized earnings power (FY2026 baseline)
"""

# Financial data
ticker = "NVDA"
current_price = 215.33  # as of May 22, 2026
current_date = "2026-05-25"

# Normalized FCF per share (FY2026 basis)
fcf_fy2026 = 96.7e9  # Operating CF $102.7B - Capex $6.0B
shares_outstanding = 24.3e9  # in billions
fcf_per_share = fcf_fy2026 / shares_outstanding  # $3.98/share

# WACC inputs
risk_free_rate = 0.0457  # 10Y Treasury yield (May 23, 2026)
equity_risk_premium = 0.055  # Damodaran 2024 ERP estimate
beta = 2.244  # 5-year monthly beta from yfinance

cost_of_equity = risk_free_rate + beta * equity_risk_premium
print(f"Cost of Equity: {cost_of_equity:.4f} ({cost_of_equity*100:.2f}%)")

# Cost of debt
interest_expense = 259e6  # FY2026
total_debt = 11_040e6  # FY2026 total debt
tax_rate = 0.151  # FY2026 effective tax rate

cost_of_debt_pretax = interest_expense / total_debt
cost_of_debt_aftertax = cost_of_debt_pretax * (1 - tax_rate)
print(f"Cost of Debt (pre-tax): {cost_of_debt_pretax:.4f} ({cost_of_debt_pretax*100:.2f}%)")
print(f"Cost of Debt (after-tax): {cost_of_debt_aftertax:.4f} ({cost_of_debt_aftertax*100:.2f}%)")

# Capital structure
equity_value = 157_300e6  # FY2026 stockholders' equity
debt_value = 11_040e6    # FY2026 total debt
total_cap = equity_value + debt_value

e_v_ratio = equity_value / total_cap
d_v_ratio = debt_value / total_cap

# WACC
wacc = (cost_of_equity * e_v_ratio) + (cost_of_debt_aftertax * d_v_ratio)
print(f"\nWACC: {wacc:.4f} ({wacc*100:.2f}%)")
print(f"  Equity weight: {e_v_ratio:.1%}")
print(f"  Debt weight: {d_v_ratio:.1%}")

# Terminal growth scenarios
# US nominal GDP long-term growth ~2.5% (from 10Y CAGR trends)
gdp_growth = 0.025
terminal_g_bear = gdp_growth - 0.01   # 1.5%
terminal_g_base = gdp_growth          # 2.5%
terminal_g_bull = gdp_growth + 0.015  # 4.0%

print(f"\nTerminal Growth Scenarios:")
print(f"  Bear: {terminal_g_bear:.1%} (GDP - 1%)")
print(f"  Base: {terminal_g_base:.1%} (GDP)")
print(f"  Bull: {terminal_g_bull:.1%} (GDP + 1.5% sector premium)")

# Intrinsic value calculations
def terminal_value_iv(fcf_ps, g, wacc):
    """Terminal value DCF: IV = FCF × (1+g) / (WACC - g)"""
    if g >= wacc:
        return None
    return (fcf_ps * (1 + g)) / (wacc - g)

iv_bear = terminal_value_iv(fcf_per_share, terminal_g_bear, wacc)
iv_base = terminal_value_iv(fcf_per_share, terminal_g_base, wacc)
iv_bull = terminal_value_iv(fcf_per_share, terminal_g_bull, wacc)

print(f"\nIntrinsic Value per Share:")
print(f"  Bear: ${iv_bear:.2f}")
print(f"  Base: ${iv_base:.2f}")
print(f"  Bull: ${iv_bull:.2f}")

# Margin of safety (base case)
mos_base = (iv_base - current_price) / current_price

print(f"\nMargin of Safety (Base Case):")
print(f"  IV (base): ${iv_base:.2f}")
print(f"  Current price: ${current_price:.2f}")
print(f"  MoS: {mos_base:.1%}")

if mos_base > 0.30:
    verdict = "significant_undervalue"
elif mos_base > 0.10:
    verdict = "modest_undervalue"
elif mos_base > -0.10:
    verdict = "fair_value"
else:
    verdict = "overvalued"

print(f"  Verdict: {verdict.replace('_', ' ').title()}")

# Normalized metrics
revenue_fy2026 = 215.938e9
ebit_fy2026 = 141.709e9
ebitda_fy2026 = 144.552e9
da_fy2026 = 2.843e9

# Average of FY2025-2026 for through-cycle margin
ebitda_fy2025 = 86.137e9
ebitda_avg = (ebitda_fy2026 + ebitda_fy2025) / 2

# Normalized operating income (use stable margins from recent years)
# Operating margin FY2026: 65.6%, FY2025: 64.6% → use 65%
normalized_op_margin = 0.65
normalized_ebit = revenue_fy2026 * normalized_op_margin
normalized_nopat = normalized_ebit * (1 - tax_rate)
normalized_eps = normalized_nopat / shares_outstanding
pe_normalized = current_price / normalized_eps

# EV/EBITDA
market_cap = current_price * shares_outstanding
cash = 62_556e6  # FY2026 cash & equivalents
net_debt = debt_value - cash
enterprise_value = market_cap + net_debt if net_debt > 0 else market_cap - abs(net_debt)
ev_ebitda = enterprise_value / ebitda_fy2026

print(f"\nNormalized Metrics:")
print(f"  Normalized operating margin: {normalized_op_margin:.1%}")
print(f"  Normalized EPS: ${normalized_eps:.2f}")
print(f"  P/E (normalized): {pe_normalized:.1f}x")
print(f"  EV/EBITDA (FY2026): {ev_ebitda:.1f}x")

# Historical data years used
data_years = 4  # FY2023-2026 from yfinance

# JSON output
import json

dcf_output = {
    "normalized_fcf_per_share": round(fcf_per_share, 2),
    "wacc_pct": round(wacc * 100, 2),
    "risk_free_rate_pct": round(risk_free_rate * 100, 2),
    "terminal_g_bear_pct": round(terminal_g_bear * 100, 1),
    "terminal_g_base_pct": round(terminal_g_base * 100, 1),
    "terminal_g_bull_pct": round(terminal_g_bull * 100, 1),
    "iv_per_share_bear": round(iv_bear, 2),
    "iv_per_share_base": round(iv_base, 2),
    "iv_per_share_bull": round(iv_bull, 2),
    "current_price": current_price,
    "margin_of_safety_base_pct": round(mos_base * 100, 1),
    "valuation_verdict": verdict,
    "pe_normalized": round(pe_normalized, 1),
    "ev_ebitda_normalized": round(ev_ebitda, 1),
    "data_years_used": data_years
}

print("\n" + "="*60)
print("DCF VALUATION OUTPUT")
print("="*60)
print(json.dumps(dcf_output, indent=2))
