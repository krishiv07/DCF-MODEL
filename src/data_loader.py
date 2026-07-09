import yfinance as yf
import pandas as pd

# Master Dictionary of Indian Market Indices
INDIAN_INDICES = {
    "NIFTY 50 (Large Cap)": "^NSEI",
    "BSE SENSEX": "^BSESN",
    "NIFTY NEXT 50": "^NN50.NS",
    "NIFTY MIDCAP 100": "^NIFTYMIDCAP100.NS",
    "NIFTY SMALLCAP 100": "^NIFTYSMLCAP100.NS",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY FMCG": "^CNXFMCG"
}

def fetch_index_performance(index_name="NIFTY 50 (Large Cap)", period="1y"):
    """Fetches live performance data for the selected benchmark index."""
    ticker = INDIAN_INDICES.get(index_name, "^NSEI")
    idx_data = yf.Ticker(ticker)
    hist = idx_data.history(period=period)
    
    if hist.empty:
        return {"current_price": 0, "1y_return": 0}
        
    start_price = hist['Close'].iloc[0]
    end_price = hist['Close'].iloc[-1]
    total_return = (end_price / start_price) - 1
    
    return {
        "index_name": index_name,
        "ticker": ticker,
        "current_price": end_price,
        "1y_return": total_return
    }

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
        # Indian 10-Year Govt Bond Proxy
        in_10y = yf.Ticker("^IN10YT=RR") 
        risk_free_rate = in_10y.history(period="1d")['Close'].iloc[-1] / 100
    except Exception:
        risk_free_rate = 0.071 
        
    try:
        # BULLETPROOF REVENUE PARSING
        if 'Total Revenue' in income_stmt.index:
            total_revenue = income_stmt.loc['Total Revenue'].iloc[0]
        elif 'Operating Revenue' in income_stmt.index:
            total_revenue = income_stmt.loc['Operating Revenue'].iloc[0]
        else:
            total_revenue = info.get('totalRevenue', market_cap * 0.2) 
            
        # BULLETPROOF EBIT PARSING
        if 'EBIT' in income_stmt.index:
            ebit = income_stmt.loc['EBIT'].iloc[0]
        elif 'Operating Income' in income_stmt.index:
            ebit = income_stmt.loc['Operating Income'].iloc[0]
        else:
            ebit = total_revenue * 0.15 
            
        # BULLETPROOF TAX PARSING
        tax_provision = income_stmt.loc['Tax Provision'].iloc[0] if 'Tax Provision' in income_stmt.index else ebit * 0.25
        pretax_income = income_stmt.loc['Pretax Income'].iloc[0] if 'Pretax Income' in income_stmt.index else ebit
        
        # BALANCE SHEET & CASH FLOW
        total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else info.get('totalDebt', 0)
        cash_and_equiv = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_sheet.index else info.get('totalCash', 0)
        
        depreciation = cash_flow.loc['Depreciation And Amortization'].iloc[0] if 'Depreciation And Amortization' in cash_flow.index else ebit * 0.1
        capex = abs(cash_flow.loc['Capital Expenditure'].iloc[0]) if 'Capital Expenditure' in cash_flow.index else total_revenue * 0.05
        
        # BULLETPROOF HISTORICAL GROWTH
        try:
            prev_revenue = income_stmt.loc['Total Revenue'].iloc[1] if 'Total Revenue' in income_stmt.index else income_stmt.loc['Operating Revenue'].iloc[1]
            historical_growth = (total_revenue / prev_revenue) - 1 if prev_revenue else 0.08
        except Exception:
            historical_growth = info.get('revenueGrowth', 0.08)

    except Exception as e:
        raise RuntimeError(f"Data missing from Yahoo Finance for this specific ticker. Details: {str(e)}")

    tax_rate = tax_provision / pretax_income if pretax_income > 0 else 0.25
    ebit_margin = ebit / total_revenue if total_revenue > 0 else 0.15
    
    return {
        'market_price': market_price, 'shares_out': shares_out, 'market_cap': market_cap,
        'beta': beta, 'risk_free_rate': risk_free_rate, 'total_revenue': total_revenue,
        'ebit': ebit, 'tax_rate': tax_rate, 'ebit_margin': ebit_margin,
        'total_debt': total_debt, 'cash': cash_and_equiv, 'depreciation': depreciation,
        'capex': capex, 'historical_growth': historical_growth
    }
