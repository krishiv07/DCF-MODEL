import yfinance as yf

def fetch_financial_data(ticker_symbol, market_risk_premium=0.075):
    stock = yf.Ticker(ticker_symbol)
    
    income_stmt = stock.financials.fillna(0)
    balance_sheet = stock.balance_sheet.fillna(0)
    cash_flow = stock.cashflow.fillna(0)
    info = stock.info
    
    market_price = info.get('currentPrice', info.get('previousClose', 2500))
    shares_out = info.get('sharesOutstanding', 1)
    market_cap = market_price * shares_out
    beta = info.get('beta', 1.0)
    
    try:
        in_10y = yf.Ticker("^IN10YT=RR") 
        risk_free_rate = in_10y.history(period="1d")['Close'].iloc[-1] / 100
    except Exception:
        risk_free_rate = 0.071 
        
    try:
        total_revenue = income_stmt.loc['Total Revenue'].iloc[0]
        ebit = income_stmt.loc['EBIT'].iloc[0]
        tax_provision = income_stmt.loc['Tax Provision'].iloc[0]
        pretax_income = income_stmt.loc['Pretax Income'].iloc[0]
        
        total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else info.get('totalDebt', 0)
        cash_and_equiv = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_sheet.index else info.get('totalCash', 0)
        
        depreciation = cash_flow.loc['Depreciation And Amortization'].iloc[0] if 'Depreciation And Amortization' in cash_flow.index else ebit * 0.1
        capex = abs(cash_flow.loc['Capital Expenditure'].iloc[0]) if 'Capital Expenditure' in cash_flow.index else total_revenue * 0.05
        
        prev_revenue = income_stmt.loc['Total Revenue'].iloc[1]
        historical_growth = (total_revenue / prev_revenue) - 1 if prev_revenue else 0.08

    except Exception as e:
        raise RuntimeError(f"Failed to parse financials: {str(e)}")

    tax_rate = tax_provision / pretax_income if pretax_income > 0 else 0.25
    ebit_margin = ebit / total_revenue if total_revenue > 0 else 0.15
    
    return {
        'market_price': market_price, 'shares_out': shares_out, 'market_cap': market_cap,
        'beta': beta, 'risk_free_rate': risk_free_rate, 'total_revenue': total_revenue,
        'ebit': ebit, 'tax_rate': tax_rate, 'ebit_margin': ebit_margin,
        'total_debt': total_debt, 'cash': cash_and_equiv, 'depreciation': depreciation,
        'capex': capex, 'historical_growth': historical_growth
    }
