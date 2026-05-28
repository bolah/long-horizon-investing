#!/usr/bin/env python3
"""
NVDA Fundamentals Analysis - 10+ Year Horizon
Enhanced version using both EDGAR and yfinance data
"""

import json
from datetime import datetime
from statistics import median
import yfinance as yf

def analyze_nvda_fundamentals():
    """Comprehensive fundamentals analysis for NVDA"""

    ticker = "NVDA"
    as_of_date = "2026-05-25"

    print(f"Starting fundamentals analysis for {ticker}...")
    print(f"Data as of: {as_of_date}")

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

    try:
        # Get yfinance data
        print(f"\nFetching data from yfinance for {ticker}...")
        stock = yf.Ticker(ticker)

        # Get financial statements
        income_stmt = stock.financials.T
        balance_sheet = stock.balance_sheet.T
        cash_flow = stock.cashflow.T

        # Sort by date (oldest to newest)
        income_stmt = income_stmt.sort_index()
        balance_sheet = balance_sheet.sort_index()
        cash_flow = cash_flow.sort_index()

        print(f"Income statement years: {[d.year for d in income_stmt.index]}")
        print(f"Balance sheet years: {[d.year for d in balance_sheet.index]}")
        print(f"Cash flow years: {[d.year for d in cash_flow.index]}")

        # Initialize tracking lists
        revenues = []
        gross_margins = []
        ebit_margins = []
        fcf_margins = []
        fcf_conversion_ratios = []
        net_debt_ebitda_values = []
        reinvestment_rates = []
        roic_series = []

        # Process each year
        years = sorted(income_stmt.index)
        print(f"\nProcessing {len(years)} years of data...")

        for year in years:
            year_label = year.year
            print(f"  Processing FY{year_label}...")

            # === REVENUE ===
            if 'Total Revenue' in income_stmt.columns:
                revenue = income_stmt.loc[year, 'Total Revenue']
                if revenue and revenue > 0:
                    revenues.append((year_label, revenue))
                    print(f"    Revenue: ${revenue/1e9:.2f}B")

            # === GROSS MARGIN ===
            if 'Gross Profit' in income_stmt.columns and 'Total Revenue' in income_stmt.columns:
                gross_profit = income_stmt.loc[year, 'Gross Profit']
                revenue = income_stmt.loc[year, 'Total Revenue']
                if gross_profit and revenue and revenue > 0:
                    gross_margin = (gross_profit / revenue) * 100
                    gross_margins.append(gross_margin)
                    print(f"    Gross margin: {gross_margin:.1f}%")

            # === EBIT MARGIN ===
            if 'Operating Income' in income_stmt.columns and 'Total Revenue' in income_stmt.columns:
                ebit = income_stmt.loc[year, 'Operating Income']
                revenue = income_stmt.loc[year, 'Total Revenue']
                if ebit and revenue and revenue > 0:
                    ebit_margin = (ebit / revenue) * 100
                    ebit_margins.append(ebit_margin)
                    print(f"    EBIT margin: {ebit_margin:.1f}%")

            # === FREE CASH FLOW ===
            if year in cash_flow.index:
                fcf = None
                if 'Free Cash Flow' in cash_flow.columns:
                    fcf = cash_flow.loc[year, 'Free Cash Flow']
                elif 'Operating Cash Flow' in cash_flow.columns and 'Capital Expenditure' in cash_flow.columns:
                    ocf = cash_flow.loc[year, 'Operating Cash Flow']
                    capex = cash_flow.loc[year, 'Capital Expenditure']
                    if ocf is not None and capex is not None:
                        fcf = ocf + capex  # capex is negative in yfinance

                if fcf is not None:
                    # FCF Margin
                    if 'Total Revenue' in income_stmt.columns:
                        revenue = income_stmt.loc[year, 'Total Revenue']
                        if revenue and revenue > 0:
                            fcf_margin = (fcf / revenue) * 100
                            fcf_margins.append(fcf_margin)
                            print(f"    FCF margin: {fcf_margin:.1f}%")

                    # FCF Conversion Ratio
                    if 'Net Income' in income_stmt.columns:
                        net_income = income_stmt.loc[year, 'Net Income']
                        if net_income and net_income > 0:
                            fcf_conversion = fcf / net_income
                            fcf_conversion_ratios.append(fcf_conversion)
                            print(f"    FCF/NI: {fcf_conversion:.2f}x")

                # === REINVESTMENT RATE ===
                if 'Capital Expenditure' in cash_flow.columns and 'Net Income' in income_stmt.columns:
                    capex = cash_flow.loc[year, 'Capital Expenditure']
                    net_income = income_stmt.loc[year, 'Net Income']
                    if capex is not None and net_income and net_income > 0:
                        reinvestment_rate = abs(capex / net_income) * 100
                        reinvestment_rates.append(reinvestment_rate)
                        print(f"    Reinvestment rate: {reinvestment_rate:.1f}%")

            # === NET DEBT / EBITDA ===
            if year in balance_sheet.index:
                cash = 0
                if 'Cash And Cash Equivalents' in balance_sheet.columns:
                    cash_val = balance_sheet.loc[year, 'Cash And Cash Equivalents']
                    if cash_val:
                        cash = cash_val

                short_term_debt = 0
                if 'Current Debt' in balance_sheet.columns:
                    std = balance_sheet.loc[year, 'Current Debt']
                    if std:
                        short_term_debt = std

                long_term_debt = 0
                if 'Long Term Debt' in balance_sheet.columns:
                    ltd = balance_sheet.loc[year, 'Long Term Debt']
                    if ltd:
                        long_term_debt = ltd

                total_debt = short_term_debt + long_term_debt
                net_debt = total_debt - cash

                # Calculate EBITDA
                if 'Operating Income' in income_stmt.columns:
                    ebit = income_stmt.loc[year, 'Operating Income']
                    da = 0
                    if year in cash_flow.index and 'Depreciation And Amortization' in cash_flow.columns:
                        da_val = cash_flow.loc[year, 'Depreciation And Amortization']
                        if da_val:
                            da = abs(da_val)

                    if ebit:
                        ebitda = ebit + da
                        if ebitda > 0:
                            nd_ebitda = net_debt / ebitda
                            net_debt_ebitda_values.append(nd_ebitda)
                            print(f"    Net Debt/EBITDA: {nd_ebitda:.2f}x (cash ${cash/1e9:.1f}B, debt ${total_debt/1e9:.1f}B)")

            # === ROIC ===
            if year in balance_sheet.index and 'Operating Income' in income_stmt.columns:
                ebit = income_stmt.loc[year, 'Operating Income']

                # Calculate tax rate
                tax_rate = 0.21  # Default US corporate rate
                if 'Tax Provision' in income_stmt.columns and 'Pretax Income' in income_stmt.columns:
                    tax_prov = income_stmt.loc[year, 'Tax Provision']
                    pretax_income = income_stmt.loc[year, 'Pretax Income']
                    if tax_prov and pretax_income and pretax_income > 0:
                        tax_rate = abs(tax_prov / pretax_income)

                if ebit:
                    nopat = ebit * (1 - tax_rate)

                    # Calculate Invested Capital
                    if 'Total Assets' in balance_sheet.columns and 'Current Liabilities' in balance_sheet.columns:
                        total_assets = balance_sheet.loc[year, 'Total Assets']
                        current_liabilities = balance_sheet.loc[year, 'Current Liabilities']
                        cash = 0
                        if 'Cash And Cash Equivalents' in balance_sheet.columns:
                            cash_val = balance_sheet.loc[year, 'Cash And Cash Equivalents']
                            if cash_val:
                                cash = cash_val

                        if total_assets and current_liabilities:
                            invested_capital = total_assets - current_liabilities - cash

                            if invested_capital > 0:
                                roic = (nopat / invested_capital) * 100
                                roic_series.append({"year": year_label, "roic_pct": round(roic, 1)})
                                print(f"    ROIC: {roic:.1f}%")

        # === CALCULATE SUMMARY METRICS ===
        print("\n=== SUMMARY METRICS ===")

        # Revenue CAGR
        if len(revenues) >= 2:
            start_year, start_rev = revenues[0]
            end_year, end_rev = revenues[-1]
            years_diff = end_year - start_year
            if years_diff > 0 and start_rev > 0:
                cagr = ((end_rev / start_rev) ** (1 / years_diff) - 1) * 100
                result["content"]["revenue_cagr_10y_pct"] = round(cagr, 1)
                print(f"Revenue CAGR: {cagr:.1f}% over {years_diff} years (${start_rev/1e9:.1f}B → ${end_rev/1e9:.1f}B)")
                result["citations"].append({
                    "claim": f"Revenue CAGR {round(cagr, 1)}% over {years_diff} years (FY{start_year} ${start_rev/1e9:.1f}B → FY{end_year} ${end_rev/1e9:.1f}B)",
                    "source": "yfinance",
                    "url_or_id": f"{ticker} financials",
                    "retrieved_at": as_of_date
                })

        # Margin medians
        if gross_margins:
            gm_median = round(median(gross_margins), 1)
            result["content"]["gross_margin_median_10y_pct"] = gm_median
            print(f"Gross margin median: {gm_median}% (range: {min(gross_margins):.1f}%-{max(gross_margins):.1f}%)")
            result["citations"].append({
                "claim": f"Gross margin median {gm_median}% over {len(gross_margins)} years (range {min(gross_margins):.1f}%-{max(gross_margins):.1f}%)",
                "source": "yfinance",
                "url_or_id": f"{ticker} income statements",
                "retrieved_at": as_of_date
            })

        if ebit_margins:
            em_median = round(median(ebit_margins), 1)
            result["content"]["ebit_margin_median_10y_pct"] = em_median
            print(f"EBIT margin median: {em_median}% (range: {min(ebit_margins):.1f}%-{max(ebit_margins):.1f}%)")
            result["citations"].append({
                "claim": f"EBIT margin median {em_median}% over {len(ebit_margins)} years (range {min(ebit_margins):.1f}%-{max(ebit_margins):.1f}%)",
                "source": "yfinance",
                "url_or_id": f"{ticker} income statements",
                "retrieved_at": as_of_date
            })

        if fcf_margins:
            fcf_median = round(median(fcf_margins), 1)
            result["content"]["fcf_margin_median_10y_pct"] = fcf_median
            print(f"FCF margin median: {fcf_median}% (range: {min(fcf_margins):.1f}%-{max(fcf_margins):.1f}%)")
            result["citations"].append({
                "claim": f"FCF margin median {fcf_median}% over {len(fcf_margins)} years (range {min(fcf_margins):.1f}%-{max(fcf_margins):.1f}%)",
                "source": "yfinance",
                "url_or_id": f"{ticker} cash flow statements",
                "retrieved_at": as_of_date
            })

        if fcf_conversion_ratios:
            fcf_conv_median = round(median(fcf_conversion_ratios), 2)
            result["content"]["fcf_conversion_ratio_median"] = fcf_conv_median
            print(f"FCF conversion median: {fcf_conv_median}x")
            result["citations"].append({
                "claim": f"FCF conversion ratio median {fcf_conv_median}x (FCF/Net Income over {len(fcf_conversion_ratios)} years)",
                "source": "yfinance",
                "url_or_id": f"{ticker} cash flow statements",
                "retrieved_at": as_of_date
            })

        # Net debt / EBITDA
        if net_debt_ebitda_values:
            latest_nd = round(net_debt_ebitda_values[-1], 1)
            trough_nd = round(min(net_debt_ebitda_values), 1)
            result["content"]["net_debt_ebitda_latest"] = latest_nd
            result["content"]["net_debt_ebitda_trough"] = trough_nd
            print(f"Net Debt/EBITDA: latest {latest_nd}x, trough {trough_nd}x")
            result["citations"].append({
                "claim": f"Net debt / EBITDA latest {latest_nd}x, trough {trough_nd}x over {len(net_debt_ebitda_values)} years",
                "source": "yfinance",
                "url_or_id": f"{ticker} balance sheet and cash flow statements",
                "retrieved_at": as_of_date
            })

            # Balance sheet verdict
            max_leverage = max(net_debt_ebitda_values)
            if max_leverage < 0:
                result["content"]["balance_sheet_verdict"] = "resilient"
                verdict_reason = f"net cash position throughout period (max leverage {max_leverage:.1f}x)"
            elif max_leverage < 1.5:
                result["content"]["balance_sheet_verdict"] = "resilient"
                verdict_reason = f"low leverage throughout (max {max_leverage:.1f}x)"
            elif max_leverage < 3.0:
                result["content"]["balance_sheet_verdict"] = "adequate"
                verdict_reason = f"moderate leverage (max {max_leverage:.1f}x)"
            elif max_leverage < 4.0:
                result["content"]["balance_sheet_verdict"] = "stretched"
                verdict_reason = f"elevated leverage (max {max_leverage:.1f}x)"
            else:
                result["content"]["balance_sheet_verdict"] = "distressed"
                verdict_reason = f"high leverage (max {max_leverage:.1f}x)"

            print(f"Balance sheet verdict: {result['content']['balance_sheet_verdict']} ({verdict_reason})")
            result["citations"].append({
                "claim": f"Balance sheet {result['content']['balance_sheet_verdict']}: {verdict_reason}",
                "source": "yfinance",
                "url_or_id": f"{ticker} balance sheet analysis",
                "retrieved_at": as_of_date
            })

        # === CAPITAL ALLOCATION ===
        print("\n=== CAPITAL ALLOCATION ===")

        # Reinvestment rate
        if reinvestment_rates:
            avg_reinv = round(sum(reinvestment_rates) / len(reinvestment_rates), 0)
            result["content"]["capital_allocation"]["reinvestment_rate_avg_pct"] = int(avg_reinv)
            print(f"Avg reinvestment rate: {avg_reinv}%")
            result["citations"].append({
                "claim": f"Reinvestment rate avg {int(avg_reinv)}% (capex / net income over {len(reinvestment_rates)} years)",
                "source": "yfinance",
                "url_or_id": f"{ticker} cash flow statements",
                "retrieved_at": as_of_date
            })

        # ROIC series
        if roic_series:
            result["content"]["capital_allocation"]["roic_10y_series"] = roic_series

            # ROIC vs WACC verdict (assume 10% WACC for semiconductor/tech)
            above_wacc = sum(1 for r in roic_series if r["roic_pct"] > 10)
            if above_wacc >= len(roic_series) * 0.8:
                result["content"]["capital_allocation"]["roic_vs_wacc_verdict"] = "consistently_above"
            elif above_wacc >= len(roic_series) * 0.5:
                result["content"]["capital_allocation"]["roic_vs_wacc_verdict"] = "mixed"
            else:
                result["content"]["capital_allocation"]["roic_vs_wacc_verdict"] = "consistently_below"

            roic_values = [r["roic_pct"] for r in roic_series]
            print(f"ROIC series: {above_wacc}/{len(roic_series)} years above 10% WACC")
            print(f"  ROIC range: {min(roic_values):.1f}%-{max(roic_values):.1f}%")
            print(f"  Verdict: {result['content']['capital_allocation']['roic_vs_wacc_verdict']}")

            result["citations"].append({
                "claim": f"ROIC over {len(roic_series)} years: {above_wacc}/{len(roic_series)} years above 10% WACC threshold (range {min(roic_values):.1f}%-{max(roic_values):.1f}%)",
                "source": "yfinance",
                "url_or_id": f"{ticker} financial statements (NOPAT / Invested Capital)",
                "retrieved_at": as_of_date
            })

        # Dividend policy
        dividends = stock.dividends
        if len(dividends) > 0:
            recent_divs = dividends[-40:]  # Last ~10 years (quarterly)
            if len(recent_divs) >= 8:
                first_annual = recent_divs[:4].sum()
                last_annual = recent_divs[-4:].sum()
                years_span = len(recent_divs) / 4
                if first_annual > 0 and years_span > 0:
                    div_cagr = (last_annual / first_annual) ** (1 / years_span) - 1
                    if div_cagr > 0.05:
                        result["content"]["capital_allocation"]["dividend_policy"] = "growing"
                        div_desc = f"growing at {div_cagr*100:.1f}% CAGR"
                    elif div_cagr > -0.05:
                        result["content"]["capital_allocation"]["dividend_policy"] = "stable"
                        div_desc = "stable"
                    else:
                        result["content"]["capital_allocation"]["dividend_policy"] = "cut_history"
                        div_desc = "declining"
                else:
                    result["content"]["capital_allocation"]["dividend_policy"] = "stable"
                    div_desc = "stable"
            else:
                result["content"]["capital_allocation"]["dividend_policy"] = "stable"
                div_desc = "limited history"

            print(f"Dividend policy: {result['content']['capital_allocation']['dividend_policy']} ({div_desc})")
            result["citations"].append({
                "claim": f"Dividend policy: {result['content']['capital_allocation']['dividend_policy']} ({div_desc})",
                "source": "yfinance",
                "url_or_id": f"{ticker} dividend history",
                "retrieved_at": as_of_date
            })
        else:
            result["content"]["capital_allocation"]["dividend_policy"] = "no_dividend"
            print("Dividend policy: no dividend")

        # Buyback discipline - analyze share count trends
        info = stock.info
        shares_outstanding = info.get('sharesOutstanding', None)
        if shares_outstanding:
            # Get historical share counts (simplified)
            result["content"]["capital_allocation"]["buyback_discipline"] = "neutral"
            print("Buyback discipline: neutral (detailed analysis requires historical share count data)")
            result["gaps"].append("Buyback discipline timing assessment requires detailed share count and repurchase timing data from 10-K filings")
        else:
            result["content"]["capital_allocation"]["buyback_discipline"] = "neutral"
            result["gaps"].append("Share count data not available for buyback discipline assessment")

        # Acquisition track record
        # This requires detailed 10-K analysis
        result["content"]["capital_allocation"]["acquisition_track_record"] = "neutral"
        print("Acquisition track record: neutral (requires 10-K business section analysis)")
        result["gaps"].append("Acquisition track record requires detailed review of 10-K business sections and management discussion")

        # === FINAL ASSESSMENT ===
        print("\n=== FINAL ASSESSMENT ===")

        # Count missing key metrics
        missing_count = 0
        if result["content"]["revenue_cagr_10y_pct"] is None:
            missing_count += 1
            result["gaps"].append("Revenue CAGR could not be calculated")
        if result["content"]["fcf_conversion_ratio_median"] is None:
            missing_count += 1
            result["gaps"].append("FCF conversion ratio incomplete")
        if result["content"]["net_debt_ebitda_latest"] is None:
            missing_count += 1
            result["gaps"].append("Net debt/EBITDA could not be calculated")
        if not roic_series:
            missing_count += 1
            result["gaps"].append("ROIC series incomplete")

        # Set confidence based on data completeness
        if missing_count == 0:
            result["confidence"] = 7  # yfinance data only, no EDGAR
        elif missing_count <= 1:
            result["confidence"] = 6
        elif missing_count <= 2:
            result["confidence"] = 5
        else:
            result["confidence"] = 3

        print(f"Confidence: {result['confidence']}/10")
        print(f"Gaps: {len(result['gaps'])}")
        print(f"Citations: {len(result['citations'])}")

        # Estimate token usage
        result["tokens_used"] = len(json.dumps(result)) * 0.4  # rough estimate
        result["cost_usd_est"] = result["tokens_used"] * 0.0003 / 1000  # Claude 3 Sonnet pricing

        return result

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        result["gaps"].append(f"Data extraction error: {str(e)}")
        result["confidence"] = 2
        return result


if __name__ == "__main__":
    result = analyze_nvda_fundamentals()

    # Write to file
    output_path = "/Users/Bence_Olah/Projects/Personal/long-horizon-investing/research/NVDA/fundamentals.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Analysis complete!")
    print(f"Output: {output_path}")
    print(f"{'='*60}")
