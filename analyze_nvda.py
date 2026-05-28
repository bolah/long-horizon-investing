#!/usr/bin/env python3
"""
NVDA Fundamentals Analysis
Comprehensive 10-year financial analysis
"""

import json
from datetime import datetime
from statistics import median
import pandas as pd

def main():
    print("="*70)
    print("NVIDIA (NVDA) Fundamentals Analysis - 10-Year Horizon")
    print("="*70)

    # Import yfinance
    try:
        import yfinance as yf
        print("\n[INFO] yfinance imported successfully")
    except ImportError:
        print("\n[ERROR] yfinance not available. Install with: pip install yfinance")
        return

    ticker = "NVDA"
    as_of_date = "2026-05-25"

    # Fetch data
    print(f"\n[INFO] Fetching {ticker} data from yfinance...")
    stock = yf.Ticker(ticker)

    # Get financials
    try:
        income_stmt = stock.financials.T.sort_index()
        balance_sheet = stock.balance_sheet.T.sort_index()
        cash_flow = stock.cashflow.T.sort_index()

        print(f"[SUCCESS] Financial data retrieved")
        print(f"  - Income statements: {len(income_stmt)} years")
        print(f"  - Balance sheets: {len(balance_sheet)} years")
        print(f"  - Cash flows: {len(cash_flow)} years")

        # Print available years
        years = [d.year for d in income_stmt.index]
        print(f"  - Years covered: {min(years)} - {max(years)}")

    except Exception as e:
        print(f"[ERROR] Failed to retrieve financial data: {e}")
        return

    # Initialize result
    result = {
        "role": "fundamentals",
        "ticker": ticker,
        "as_of_date": as_of_date,
        "horizon_years": 10,
        "content": {
            "revenue_cagr_10y_pct": None,
            "gross_margin_median_10y_pct": None,
            "ebit_margin_median_10y_pct": None,
            "fcf_margin_median_10y_pct": None,
            "fcf_conversion_ratio_median": None,
            "net_debt_ebitda_latest": None,
            "net_debt_ebitda_trough": None,
            "balance_sheet_verdict": None,
            "capital_allocation": {
                "reinvestment_rate_avg_pct": None,
                "roic_10y_series": [],
                "roic_vs_wacc_verdict": None,
                "buyback_discipline": None,
                "dividend_policy": None,
                "acquisition_track_record": None
            },
            "eu_mode_degraded": False
        },
        "citations": [],
        "confidence": 1,
        "gaps": [],
        "tokens_used": 0,
        "cost_usd_est": 0.0
    }

    # Tracking lists
    revenues = []
    gross_margins = []
    ebit_margins = []
    fcf_margins = []
    fcf_conversion_ratios = []
    net_debt_ebitda_vals = []
    reinvestment_rates = []
    roic_series = []

    print("\n" + "="*70)
    print("Processing Annual Data")
    print("="*70)

    # Process each year
    for year in income_stmt.index:
        year_label = year.year
        print(f"\n--- FY{year_label} ---")

        # Revenue
        try:
            revenue = income_stmt.loc[year, 'Total Revenue']
            if pd.notna(revenue) and revenue > 0:
                revenues.append((year_label, revenue))
                print(f"  Revenue: ${revenue/1e9:.2f}B")
        except:
            pass

        # Gross Margin
        try:
            gross_profit = income_stmt.loc[year, 'Gross Profit']
            revenue = income_stmt.loc[year, 'Total Revenue']
            if pd.notna(gross_profit) and pd.notna(revenue) and revenue > 0:
                gm = (gross_profit / revenue) * 100
                gross_margins.append(gm)
                print(f"  Gross Margin: {gm:.1f}%")
        except:
            pass

        # EBIT Margin
        try:
            op_income = income_stmt.loc[year, 'Operating Income']
            revenue = income_stmt.loc[year, 'Total Revenue']
            if pd.notna(op_income) and pd.notna(revenue) and revenue > 0:
                em = (op_income / revenue) * 100
                ebit_margins.append(em)
                print(f"  EBIT Margin: {em:.1f}%")
        except:
            pass

        # FCF
        if year in cash_flow.index:
            try:
                fcf = None
                if 'Free Cash Flow' in cash_flow.columns:
                    fcf = cash_flow.loc[year, 'Free Cash Flow']
                else:
                    ocf = cash_flow.loc[year, 'Operating Cash Flow']
                    capex = cash_flow.loc[year, 'Capital Expenditure']
                    if pd.notna(ocf) and pd.notna(capex):
                        fcf = ocf + capex  # capex is negative

                if pd.notna(fcf):
                    # FCF Margin
                    revenue = income_stmt.loc[year, 'Total Revenue']
                    if pd.notna(revenue) and revenue > 0:
                        fcf_margin = (fcf / revenue) * 100
                        fcf_margins.append(fcf_margin)
                        print(f"  FCF Margin: {fcf_margin:.1f}%")

                    # FCF Conversion
                    net_income = income_stmt.loc[year, 'Net Income']
                    if pd.notna(net_income) and net_income > 0:
                        fcf_conv = fcf / net_income
                        fcf_conversion_ratios.append(fcf_conv)
                        print(f"  FCF/NI: {fcf_conv:.2f}x")

                    # Reinvestment Rate
                    if 'Capital Expenditure' in cash_flow.columns:
                        capex = cash_flow.loc[year, 'Capital Expenditure']
                        if pd.notna(capex) and pd.notna(net_income) and net_income > 0:
                            reinv = abs(capex / net_income) * 100
                            reinvestment_rates.append(reinv)
                            print(f"  Reinvestment Rate: {reinv:.1f}%")
            except Exception as e:
                print(f"  [Warning] FCF calculation issue: {e}")

        # Net Debt / EBITDA
        if year in balance_sheet.index:
            try:
                cash = balance_sheet.loc[year, 'Cash And Cash Equivalents']
                if pd.isna(cash):
                    cash = 0

                st_debt = balance_sheet.loc[year, 'Current Debt'] if 'Current Debt' in balance_sheet.columns else 0
                if pd.isna(st_debt):
                    st_debt = 0

                lt_debt = balance_sheet.loc[year, 'Long Term Debt'] if 'Long Term Debt' in balance_sheet.columns else 0
                if pd.isna(lt_debt):
                    lt_debt = 0

                total_debt = st_debt + lt_debt
                net_debt = total_debt - cash

                # EBITDA
                op_income = income_stmt.loc[year, 'Operating Income']
                if year in cash_flow.index and 'Depreciation And Amortization' in cash_flow.columns:
                    da = cash_flow.loc[year, 'Depreciation And Amortization']
                else:
                    da = 0

                if pd.notna(op_income):
                    ebitda = op_income + abs(da) if pd.notna(da) and da != 0 else op_income
                    if ebitda > 0:
                        nd_ebitda = net_debt / ebitda
                        net_debt_ebitda_vals.append(nd_ebitda)
                        print(f"  Net Debt/EBITDA: {nd_ebitda:.2f}x")
                        print(f"    (Cash: ${cash/1e9:.1f}B, Debt: ${total_debt/1e9:.1f}B)")
            except Exception as e:
                print(f"  [Warning] Leverage calculation issue: {e}")

        # ROIC
        if year in balance_sheet.index:
            try:
                op_income = income_stmt.loc[year, 'Operating Income']

                # Tax rate
                tax_rate = 0.21
                if 'Tax Provision' in income_stmt.columns and 'Pretax Income' in income_stmt.columns:
                    tax_prov = income_stmt.loc[year, 'Tax Provision']
                    pretax = income_stmt.loc[year, 'Pretax Income']
                    if pd.notna(tax_prov) and pd.notna(pretax) and pretax > 0:
                        tax_rate = abs(tax_prov / pretax)

                if pd.notna(op_income):
                    nopat = op_income * (1 - tax_rate)

                    # Invested Capital
                    total_assets = balance_sheet.loc[year, 'Total Assets']
                    curr_liab = balance_sheet.loc[year, 'Current Liabilities']
                    cash = balance_sheet.loc[year, 'Cash And Cash Equivalents']
                    if pd.isna(cash):
                        cash = 0

                    if pd.notna(total_assets) and pd.notna(curr_liab):
                        invested_capital = total_assets - curr_liab - cash

                        if invested_capital > 0:
                            roic = (nopat / invested_capital) * 100
                            roic_series.append({"year": year_label, "roic_pct": round(roic, 1)})
                            print(f"  ROIC: {roic:.1f}%")
            except Exception as e:
                print(f"  [Warning] ROIC calculation issue: {e}")

    # ========== SUMMARY METRICS ==========
    print("\n" + "="*70)
    print("SUMMARY METRICS")
    print("="*70)

    # Revenue CAGR
    if len(revenues) >= 2:
        start_yr, start_rev = revenues[0]
        end_yr, end_rev = revenues[-1]
        years_diff = end_yr - start_yr
        if years_diff > 0 and start_rev > 0:
            cagr = ((end_rev / start_rev) ** (1 / years_diff) - 1) * 100
            result["content"]["revenue_cagr_10y_pct"] = round(cagr, 1)
            print(f"\nRevenue CAGR: {cagr:.1f}% ({years_diff} years)")
            print(f"  FY{start_yr}: ${start_rev/1e9:.1f}B → FY{end_yr}: ${end_rev/1e9:.1f}B")
            result["citations"].append({
                "claim": f"Revenue CAGR {round(cagr, 1)}% over {years_diff} years (FY{start_yr} ${start_rev/1e9:.1f}B → FY{end_yr} ${end_rev/1e9:.1f}B)",
                "source": "yfinance",
                "url_or_id": f"{ticker} financials",
                "retrieved_at": as_of_date
            })

    # Gross Margin
    if gross_margins:
        gm_med = round(median(gross_margins), 1)
        result["content"]["gross_margin_median_10y_pct"] = gm_med
        print(f"\nGross Margin Median: {gm_med}%")
        print(f"  Range: {min(gross_margins):.1f}% - {max(gross_margins):.1f}%")
        result["citations"].append({
            "claim": f"Gross margin median {gm_med}% over {len(gross_margins)} years (range {min(gross_margins):.1f}%-{max(gross_margins):.1f}%)",
            "source": "yfinance",
            "url_or_id": f"{ticker} income statements",
            "retrieved_at": as_of_date
        })

    # EBIT Margin
    if ebit_margins:
        em_med = round(median(ebit_margins), 1)
        result["content"]["ebit_margin_median_10y_pct"] = em_med
        print(f"\nEBIT Margin Median: {em_med}%")
        print(f"  Range: {min(ebit_margins):.1f}% - {max(ebit_margins):.1f}%")
        result["citations"].append({
            "claim": f"EBIT margin median {em_med}% over {len(ebit_margins)} years (range {min(ebit_margins):.1f}%-{max(ebit_margins):.1f}%)",
            "source": "yfinance",
            "url_or_id": f"{ticker} income statements",
            "retrieved_at": as_of_date
        })

    # FCF Margin
    if fcf_margins:
        fcf_med = round(median(fcf_margins), 1)
        result["content"]["fcf_margin_median_10y_pct"] = fcf_med
        print(f"\nFCF Margin Median: {fcf_med}%")
        print(f"  Range: {min(fcf_margins):.1f}% - {max(fcf_margins):.1f}%")
        result["citations"].append({
            "claim": f"FCF margin median {fcf_med}% over {len(fcf_margins)} years (range {min(fcf_margins):.1f}%-{max(fcf_margins):.1f}%)",
            "source": "yfinance",
            "url_or_id": f"{ticker} cash flow statements",
            "retrieved_at": as_of_date
        })

    # FCF Conversion
    if fcf_conversion_ratios:
        fcf_conv_med = round(median(fcf_conversion_ratios), 2)
        result["content"]["fcf_conversion_ratio_median"] = fcf_conv_med
        print(f"\nFCF Conversion Median: {fcf_conv_med}x")
        result["citations"].append({
            "claim": f"FCF conversion ratio median {fcf_conv_med}x over {len(fcf_conversion_ratios)} years",
            "source": "yfinance",
            "url_or_id": f"{ticker} cash flow statements",
            "retrieved_at": as_of_date
        })

    # Net Debt / EBITDA
    if net_debt_ebitda_vals:
        latest_nd = round(net_debt_ebitda_vals[-1], 1)
        trough_nd = round(min(net_debt_ebitda_vals), 1)
        result["content"]["net_debt_ebitda_latest"] = latest_nd
        result["content"]["net_debt_ebitda_trough"] = trough_nd
        print(f"\nNet Debt / EBITDA:")
        print(f"  Latest: {latest_nd}x")
        print(f"  Trough: {trough_nd}x")
        result["citations"].append({
            "claim": f"Net debt / EBITDA latest {latest_nd}x, trough {trough_nd}x over {len(net_debt_ebitda_vals)} years",
            "source": "yfinance",
            "url_or_id": f"{ticker} balance sheet",
            "retrieved_at": as_of_date
        })

        # Balance Sheet Verdict
        max_lev = max(net_debt_ebitda_vals)
        if max_lev < 0:
            verdict = "resilient"
            reason = f"net cash throughout (max {max_lev:.1f}x)"
        elif max_lev < 1.5:
            verdict = "resilient"
            reason = f"low leverage (max {max_lev:.1f}x)"
        elif max_lev < 3.0:
            verdict = "adequate"
            reason = f"moderate leverage (max {max_lev:.1f}x)"
        elif max_lev < 4.0:
            verdict = "stretched"
            reason = f"elevated leverage (max {max_lev:.1f}x)"
        else:
            verdict = "distressed"
            reason = f"high leverage (max {max_lev:.1f}x)"

        result["content"]["balance_sheet_verdict"] = verdict
        print(f"\nBalance Sheet: {verdict.upper()} ({reason})")
        result["citations"].append({
            "claim": f"Balance sheet {verdict}: {reason}",
            "source": "yfinance",
            "url_or_id": f"{ticker} balance sheet analysis",
            "retrieved_at": as_of_date
        })

    # ========== CAPITAL ALLOCATION ==========
    print("\n" + "="*70)
    print("CAPITAL ALLOCATION")
    print("="*70)

    # Reinvestment Rate
    if reinvestment_rates:
        avg_reinv = round(sum(reinvestment_rates) / len(reinvestment_rates), 0)
        result["content"]["capital_allocation"]["reinvestment_rate_avg_pct"] = int(avg_reinv)
        print(f"\nReinvestment Rate Avg: {int(avg_reinv)}%")
        result["citations"].append({
            "claim": f"Reinvestment rate avg {int(avg_reinv)}% (capex / net income) over {len(reinvestment_rates)} years",
            "source": "yfinance",
            "url_or_id": f"{ticker} cash flow statements",
            "retrieved_at": as_of_date
        })

    # ROIC
    if roic_series:
        result["content"]["capital_allocation"]["roic_10y_series"] = roic_series
        roic_vals = [r["roic_pct"] for r in roic_series]
        above_wacc = sum(1 for r in roic_series if r["roic_pct"] > 10)

        if above_wacc >= len(roic_series) * 0.8:
            roic_verdict = "consistently_above"
        elif above_wacc >= len(roic_series) * 0.5:
            roic_verdict = "mixed"
        else:
            roic_verdict = "consistently_below"

        result["content"]["capital_allocation"]["roic_vs_wacc_verdict"] = roic_verdict
        print(f"\nROIC vs WACC (10% threshold):")
        print(f"  {above_wacc}/{len(roic_series)} years above")
        print(f"  Range: {min(roic_vals):.1f}% - {max(roic_vals):.1f}%")
        print(f"  Verdict: {roic_verdict}")
        result["citations"].append({
            "claim": f"ROIC {above_wacc}/{len(roic_series)} years above 10% WACC (range {min(roic_vals):.1f}%-{max(roic_vals):.1f}%)",
            "source": "yfinance",
            "url_or_id": f"{ticker} calculated from financial statements",
            "retrieved_at": as_of_date
        })

    # Dividend Policy
    try:
        dividends = stock.dividends
        if len(dividends) > 0:
            recent = dividends[-40:]  # ~10 years quarterly
            if len(recent) >= 8:
                first_annual = recent[:4].sum()
                last_annual = recent[-4:].sum()
                yrs = len(recent) / 4
                if first_annual > 0 and yrs > 0:
                    div_cagr = (last_annual / first_annual) ** (1 / yrs) - 1
                    if div_cagr > 0.05:
                        div_policy = "growing"
                        div_desc = f"growing at {div_cagr*100:.1f}% CAGR"
                    elif div_cagr > -0.05:
                        div_policy = "stable"
                        div_desc = "stable"
                    else:
                        div_policy = "cut_history"
                        div_desc = "declining"
                else:
                    div_policy = "stable"
                    div_desc = "stable"
            else:
                div_policy = "stable"
                div_desc = "limited history"

            result["content"]["capital_allocation"]["dividend_policy"] = div_policy
            print(f"\nDividend Policy: {div_policy} ({div_desc})")
            result["citations"].append({
                "claim": f"Dividend policy: {div_policy} ({div_desc})",
                "source": "yfinance",
                "url_or_id": f"{ticker} dividend history",
                "retrieved_at": as_of_date
            })
        else:
            result["content"]["capital_allocation"]["dividend_policy"] = "no_dividend"
            print("\nDividend Policy: no dividend")
    except:
        result["content"]["capital_allocation"]["dividend_policy"] = "no_dividend"
        result["gaps"].append("Dividend history not available")

    # Buyback & Acquisition (placeholders)
    result["content"]["capital_allocation"]["buyback_discipline"] = "neutral"
    result["gaps"].append("Buyback discipline requires detailed share count timing analysis from 10-K")

    result["content"]["capital_allocation"]["acquisition_track_record"] = "neutral"
    result["gaps"].append("Acquisition track record requires 10-K business section review (e.g., Mellanox 2020)")

    print("\nBuyback Discipline: neutral (requires 10-K data)")
    print("Acquisition Track Record: neutral (requires 10-K review)")

    # ========== CONFIDENCE ASSESSMENT ==========
    missing = 0
    if result["content"]["revenue_cagr_10y_pct"] is None:
        missing += 1
        result["gaps"].append("Revenue CAGR not calculated")
    if result["content"]["fcf_conversion_ratio_median"] is None:
        missing += 1
        result["gaps"].append("FCF conversion incomplete")
    if result["content"]["net_debt_ebitda_latest"] is None:
        missing += 1
        result["gaps"].append("Net debt/EBITDA not calculated")
    if not roic_series:
        missing += 1
        result["gaps"].append("ROIC series incomplete")

    if missing == 0:
        result["confidence"] = 7  # yfinance only, no EDGAR
    elif missing <= 1:
        result["confidence"] = 6
    elif missing <= 2:
        result["confidence"] = 5
    else:
        result["confidence"] = 3

    # Token estimate
    result["tokens_used"] = len(json.dumps(result)) * 0.4
    result["cost_usd_est"] = round(result["tokens_used"] * 0.0003 / 1000, 3)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"Confidence: {result['confidence']}/10")
    print(f"Citations: {len(result['citations'])}")
    print(f"Gaps: {len(result['gaps'])}")

    # Write output
    output_path = "/Users/Bence_Olah/Projects/Personal/long-horizon-investing/research/NVDA/fundamentals.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nWritten to: {output_path}")
    print("="*70)

if __name__ == "__main__":
    main()
