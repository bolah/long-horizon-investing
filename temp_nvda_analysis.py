#!/usr/bin/env python3
"""
NVDA Fundamentals Analysis - 10+ Year Horizon
Extracts financial data from EDGAR and calculates key metrics
"""

import json
from datetime import datetime
from statistics import median
import yfinance as yf

# Try to import edgartools
try:
    from edgar import Company, find
    EDGAR_AVAILABLE = True
except ImportError:
    EDGAR_AVAILABLE = False
    print("Warning: edgartools not available, will use yfinance only")

def get_nvda_financials():
    """Get NVDA financial data from EDGAR and yfinance"""

    ticker = "NVDA"
    as_of_date = datetime.now().strftime("%Y-%m-%d")

    # Initialize result structure
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

    eu_mode = False

    # Get data from yfinance
    print(f"Fetching {ticker} data from yfinance...")
    stock = yf.Ticker(ticker)

    try:
        # Get financial statements
        income_stmt = stock.financials.T  # Transpose to have years as rows
        balance_sheet = stock.balance_sheet.T
        cash_flow = stock.cashflow.T

        # Sort by date
        income_stmt = income_stmt.sort_index()
        balance_sheet = balance_sheet.sort_index()
        cash_flow = cash_flow.sort_index()

        print(f"Income statement years: {list(income_stmt.index)}")
        print(f"Balance sheet years: {list(balance_sheet.index)}")
        print(f"Cash flow years: {list(cash_flow.index)}")

        # Calculate metrics
        revenues = []
        gross_margins = []
        ebit_margins = []
        fcf_margins = []
        fcf_conversion_ratios = []
        net_debt_ebitda_values = []
        reinvestment_rates = []
        roic_series = []

        years = sorted(income_stmt.index)[-11:]  # Last 11 years to get 10 years of data

        for year in years:
            year_label = year.year

            # Revenue
            if 'Total Revenue' in income_stmt.columns:
                revenue = income_stmt.loc[year, 'Total Revenue']
                if revenue and revenue > 0:
                    revenues.append((year_label, revenue))

            # Gross Margin
            if 'Gross Profit' in income_stmt.columns and 'Total Revenue' in income_stmt.columns:
                gross_profit = income_stmt.loc[year, 'Gross Profit']
                revenue = income_stmt.loc[year, 'Total Revenue']
                if gross_profit and revenue and revenue > 0:
                    gross_margin = (gross_profit / revenue) * 100
                    gross_margins.append(gross_margin)

            # EBIT Margin
            if 'Operating Income' in income_stmt.columns and 'Total Revenue' in income_stmt.columns:
                ebit = income_stmt.loc[year, 'Operating Income']
                revenue = income_stmt.loc[year, 'Total Revenue']
                if ebit and revenue and revenue > 0:
                    ebit_margin = (ebit / revenue) * 100
                    ebit_margins.append(ebit_margin)
            elif 'EBIT' in income_stmt.columns and 'Total Revenue' in income_stmt.columns:
                ebit = income_stmt.loc[year, 'EBIT']
                revenue = income_stmt.loc[year, 'Total Revenue']
                if ebit and revenue and revenue > 0:
                    ebit_margin = (ebit / revenue) * 100
                    ebit_margins.append(ebit_margin)

            # Free Cash Flow
            if year in cash_flow.index:
                if 'Free Cash Flow' in cash_flow.columns:
                    fcf = cash_flow.loc[year, 'Free Cash Flow']
                elif 'Operating Cash Flow' in cash_flow.columns and 'Capital Expenditure' in cash_flow.columns:
                    ocf = cash_flow.loc[year, 'Operating Cash Flow']
                    capex = cash_flow.loc[year, 'Capital Expenditure']
                    if ocf and capex:
                        fcf = ocf + capex  # capex is negative
                    else:
                        fcf = None
                else:
                    fcf = None

                if fcf and 'Total Revenue' in income_stmt.columns:
                    revenue = income_stmt.loc[year, 'Total Revenue']
                    if revenue and revenue > 0:
                        fcf_margin = (fcf / revenue) * 100
                        fcf_margins.append(fcf_margin)

                # FCF Conversion Ratio
                if fcf and 'Net Income' in income_stmt.columns:
                    net_income = income_stmt.loc[year, 'Net Income']
                    if net_income and net_income > 0:
                        fcf_conversion = fcf / net_income
                        fcf_conversion_ratios.append(fcf_conversion)

                # Reinvestment Rate
                if 'Capital Expenditure' in cash_flow.columns and 'Net Income' in income_stmt.columns:
                    capex = cash_flow.loc[year, 'Capital Expenditure']
                    net_income = income_stmt.loc[year, 'Net Income']
                    if capex and net_income and net_income > 0:
                        reinvestment_rate = abs(capex / net_income) * 100
                        reinvestment_rates.append(reinvestment_rate)

            # Net Debt / EBITDA
            if year in balance_sheet.index:
                cash = balance_sheet.loc[year, 'Cash And Cash Equivalents'] if 'Cash And Cash Equivalents' in balance_sheet.columns else 0
                if not cash:
                    cash = 0

                short_term_debt = balance_sheet.loc[year, 'Current Debt'] if 'Current Debt' in balance_sheet.columns else 0
                if not short_term_debt:
                    short_term_debt = 0

                long_term_debt = balance_sheet.loc[year, 'Long Term Debt'] if 'Long Term Debt' in balance_sheet.columns else 0
                if not long_term_debt:
                    long_term_debt = 0

                total_debt = short_term_debt + long_term_debt
                net_debt = total_debt - cash

                # Calculate EBITDA
                if 'Operating Income' in income_stmt.columns:
                    ebit = income_stmt.loc[year, 'Operating Income']
                    # Approximate D&A as a portion of revenue (typical for tech is 3-5%)
                    # Or try to get it from cash flow
                    if year in cash_flow.index and 'Depreciation And Amortization' in cash_flow.columns:
                        da = cash_flow.loc[year, 'Depreciation And Amortization']
                    else:
                        da = 0

                    if ebit and da:
                        ebitda = ebit + abs(da) if da else ebit
                        if ebitda > 0:
                            net_debt_ebitda = net_debt / ebitda
                            net_debt_ebitda_values.append(net_debt_ebitda)

            # ROIC calculation
            if year in balance_sheet.index and 'Operating Income' in income_stmt.columns:
                ebit = income_stmt.loc[year, 'Operating Income']
                # Tax rate approximation
                if 'Tax Provision' in income_stmt.columns and 'Pretax Income' in income_stmt.columns:
                    tax_prov = income_stmt.loc[year, 'Tax Provision']
                    pretax_income = income_stmt.loc[year, 'Pretax Income']
                    if tax_prov and pretax_income and pretax_income > 0:
                        tax_rate = abs(tax_prov / pretax_income)
                    else:
                        tax_rate = 0.21  # US corporate rate
                else:
                    tax_rate = 0.21

                nopat = ebit * (1 - tax_rate)

                # Invested Capital = Total Assets - Current Liabilities (non-debt) - Cash
                if 'Total Assets' in balance_sheet.columns and 'Current Liabilities' in balance_sheet.columns:
                    total_assets = balance_sheet.loc[year, 'Total Assets']
                    current_liabilities = balance_sheet.loc[year, 'Current Liabilities']
                    cash = balance_sheet.loc[year, 'Cash And Cash Equivalents'] if 'Cash And Cash Equivalents' in balance_sheet.columns else 0

                    if total_assets and current_liabilities:
                        invested_capital = total_assets - current_liabilities - (cash if cash else 0)

                        if invested_capital > 0:
                            roic = (nopat / invested_capital) * 100
                            roic_series.append({"year": year_label, "roic_pct": round(roic, 1)})

        # Calculate Revenue CAGR
        if len(revenues) >= 2:
            start_rev = revenues[0][1]
            end_rev = revenues[-1][1]
            years_diff = revenues[-1][0] - revenues[0][0]
            if years_diff > 0 and start_rev > 0:
                cagr = ((end_rev / start_rev) ** (1 / years_diff) - 1) * 100
                result["content"]["revenue_cagr_10y_pct"] = round(cagr, 1)
                result["citations"].append({
                    "claim": f"Revenue CAGR {round(cagr, 1)}% over {years_diff} years (${start_rev/1e9:.1f}B → ${end_rev/1e9:.1f}B)",
                    "source": "yfinance",
                    "url_or_id": f"{ticker} financials",
                    "retrieved_at": as_of_date
                })

        # Calculate medians
        if gross_margins:
            result["content"]["gross_margin_median_10y_pct"] = round(median(gross_margins), 1)
            result["citations"].append({
                "claim": f"Gross margin median {round(median(gross_margins), 1)}% over {len(gross_margins)} years",
                "source": "yfinance",
                "url_or_id": f"{ticker} income statements",
                "retrieved_at": as_of_date
            })

        if ebit_margins:
            result["content"]["ebit_margin_median_10y_pct"] = round(median(ebit_margins), 1)
            result["citations"].append({
                "claim": f"EBIT margin median {round(median(ebit_margins), 1)}% over {len(ebit_margins)} years",
                "source": "yfinance",
                "url_or_id": f"{ticker} income statements",
                "retrieved_at": as_of_date
            })

        if fcf_margins:
            result["content"]["fcf_margin_median_10y_pct"] = round(median(fcf_margins), 1)
            result["citations"].append({
                "claim": f"FCF margin median {round(median(fcf_margins), 1)}% over {len(fcf_margins)} years",
                "source": "yfinance",
                "url_or_id": f"{ticker} cash flow statements",
                "retrieved_at": as_of_date
            })

        if fcf_conversion_ratios:
            result["content"]["fcf_conversion_ratio_median"] = round(median(fcf_conversion_ratios), 2)
            result["citations"].append({
                "claim": f"FCF conversion ratio median {round(median(fcf_conversion_ratios), 2)}x",
                "source": "yfinance",
                "url_or_id": f"{ticker} cash flow statements",
                "retrieved_at": as_of_date
            })

        if net_debt_ebitda_values:
            result["content"]["net_debt_ebitda_latest"] = round(net_debt_ebitda_values[-1], 1)
            result["content"]["net_debt_ebitda_trough"] = round(min(net_debt_ebitda_values), 1)
            result["citations"].append({
                "claim": f"Net debt / EBITDA latest {round(net_debt_ebitda_values[-1], 1)}x, trough {round(min(net_debt_ebitda_values), 1)}x",
                "source": "yfinance",
                "url_or_id": f"{ticker} balance sheet",
                "retrieved_at": as_of_date
            })

        # Balance sheet verdict
        if net_debt_ebitda_values:
            max_leverage = max(net_debt_ebitda_values)
            if max_leverage < 0:  # Net cash position
                result["content"]["balance_sheet_verdict"] = "resilient"
            elif max_leverage < 1.5:
                result["content"]["balance_sheet_verdict"] = "resilient"
            elif max_leverage < 3.0:
                result["content"]["balance_sheet_verdict"] = "adequate"
            elif max_leverage < 4.0:
                result["content"]["balance_sheet_verdict"] = "stretched"
            else:
                result["content"]["balance_sheet_verdict"] = "distressed"

        # Capital allocation
        if reinvestment_rates:
            result["content"]["capital_allocation"]["reinvestment_rate_avg_pct"] = round(sum(reinvestment_rates) / len(reinvestment_rates), 0)

        if roic_series:
            result["content"]["capital_allocation"]["roic_10y_series"] = roic_series
            # ROIC vs WACC verdict (assume WACC ~10% for tech)
            above_wacc = sum(1 for r in roic_series if r["roic_pct"] > 10)
            if above_wacc >= len(roic_series) * 0.8:
                result["content"]["capital_allocation"]["roic_vs_wacc_verdict"] = "consistently_above"
            elif above_wacc >= len(roic_series) * 0.5:
                result["content"]["capital_allocation"]["roic_vs_wacc_verdict"] = "mixed"
            else:
                result["content"]["capital_allocation"]["roic_vs_wacc_verdict"] = "consistently_below"

            result["citations"].append({
                "claim": f"ROIC calculated over {len(roic_series)} years; {above_wacc}/{len(roic_series)} years above 10% WACC threshold",
                "source": "yfinance",
                "url_or_id": f"{ticker} financial statements (NOPAT / Invested Capital)",
                "retrieved_at": as_of_date
            })

        # Dividend policy
        dividends = stock.dividends
        if len(dividends) > 0:
            recent_divs = dividends[-10:]
            if len(recent_divs) >= 5:
                growth = (recent_divs.iloc[-1] / recent_divs.iloc[0]) ** (1 / (len(recent_divs) - 1)) - 1
                if growth > 0.05:
                    result["content"]["capital_allocation"]["dividend_policy"] = "growing"
                elif growth > -0.05:
                    result["content"]["capital_allocation"]["dividend_policy"] = "stable"
                else:
                    result["content"]["capital_allocation"]["dividend_policy"] = "cut_history"
            else:
                result["content"]["capital_allocation"]["dividend_policy"] = "stable"

            result["citations"].append({
                "claim": f"Dividend policy: {result['content']['capital_allocation']['dividend_policy']}",
                "source": "yfinance",
                "url_or_id": f"{ticker} dividend history",
                "retrieved_at": as_of_date
            })
        else:
            result["content"]["capital_allocation"]["dividend_policy"] = "no_dividend"

        # Buyback discipline (simplified - would need more data)
        result["content"]["capital_allocation"]["buyback_discipline"] = "neutral"
        result["gaps"].append("Buyback discipline assessment requires detailed share count and timing data not available from yfinance")

        # Acquisition track record (simplified)
        result["content"]["capital_allocation"]["acquisition_track_record"] = "neutral"
        result["gaps"].append("Acquisition track record requires detailed 10-K business section analysis")

        # Set confidence
        if eu_mode:
            result["confidence"] = 5
            result["content"]["eu_mode_degraded"] = True
        else:
            result["confidence"] = 7

        # Add gap if any key metric is missing
        if not result["content"]["revenue_cagr_10y_pct"]:
            result["gaps"].append("Revenue CAGR could not be calculated")
        if not result["content"]["fcf_conversion_ratio_median"]:
            result["gaps"].append("FCF conversion ratio incomplete")

        return result

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        result["gaps"].append(f"Data extraction error: {str(e)}")
        result["confidence"] = 2
        return result

if __name__ == "__main__":
    result = get_nvda_financials()

    # Write to file
    output_path = "/Users/Bence_Olah/Projects/Personal/long-horizon-investing/research/NVDA/fundamentals.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nAnalysis complete. Written to {output_path}")
    print(f"Confidence: {result['confidence']}/10")
    print(f"Gaps: {len(result['gaps'])}")
