import streamlit as st
import urllib.request
import urllib.parse
import json
from src.data_loader import fetch_financial_data
from src.valuation import calculate_wacc, build_base_forecast
from src.visualization import get_dcf_visuals, get_sensitivity_analysis

st.set_page_config(page_title="Institutional DCF Engine", layout="wide")
st.title("Institutional Fundamental Valuation Platform (Indian Markets)")

def search_indian_ticker(query):
    """Hits the live Yahoo Finance API to translate a company name into an NSE/BSE ticker."""
    safe_query = urllib.parse.quote(query)
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={safe_query}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            quotes = data.get('quotes', [])
            
            # Filter specifically for Indian Exchanges (NSE = NSI, BSE = BSE)
            indian_quotes = [q for q in quotes if q.get('exchange') in ['NSI', 'BSE']]
            if indian_quotes:
                symbol = indian_quotes[0]['symbol']
                name = indian_quotes[0].get('longname', indian_quotes[0].get('shortname', query))
                return symbol, name
    except Exception:
        pass
    
    # Smart Fallback: If search fails, assume they typed the raw ticker (e.g., ZOMATO) and append .NS
    raw_ticker = query.upper().strip()
    if not raw_ticker.endswith(".NS") and not raw_ticker.endswith(".BO"):
        raw_ticker += ".NS"
    return raw_ticker, query.upper()

st.sidebar.header("Model Inputs")

# Free-text search bar replaces the static dropdown!
search_query = st.sidebar.text_input("Search Company Name or Ticker", value="Reliance Industries", 
                                     help="Type any Indian company name (e.g., 'Tata Motors', 'Zomato') or NSE ticker.")

forecast_years = st.sidebar.slider("Forecast Period (Years)", min_value=3, max_value=10, value=5)
erp = st.sidebar.slider("Equity Risk Premium (India)", min_value=0.05, max_value=0.10, value=0.075, step=0.005)
terminal_growth = st.sidebar.slider("Terminal Perpetuity Growth Rate", min_value=0.01, max_value=0.05, value=0.025, step=0.005)

if st.sidebar.button("Run Valuation Engine"):
    try:
        with st.spinner("Locating company ticker and fetching live market data..."):
            # Step 1: Translate name to ticker dynamically
            ticker, company_name = search_indian_ticker(search_query)
            st.sidebar.success(f"Located: {company_name} ({ticker})")
            
            # Step 2: Run the engine
            fin_data = fetch_financial_data(ticker, market_risk_premium=erp)
            wacc_computed = calculate_wacc(fin_data, market_risk_premium=erp)
            forecast_df, ev, eqv, implied_price, tv = build_base_forecast(
                fin_data, wacc_computed, forecast_years=forecast_years, terminal_growth=terminal_growth
            )
            
        st.subheader(f"Valuation Results: {company_name} ({ticker})")    
        
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Current Market Price", value=f"₹{fin_data['market_price']:.2f}")
        col2.metric(label="Implied Intrinsic Price", value=f"₹{implied_price:.2f}")
        col3.metric(label="Calculated Model WACC", value=f"{wacc_computed:.2%}")
        
        st.subheader("Financial Performance & Structural Bridge")
        fig_charts = get_dcf_visuals(forecast_df, fin_data, tv, wacc_computed, forecast_years, eqv)
        st.pyplot(fig_charts)
        
        st.subheader("Assumption Sensitivity Analysis")
        fig_heat = get_sensitivity_analysis(fin_data, wacc_computed, forecast_years, build_base_forecast)
        st.pyplot(fig_heat)
        
        st.subheader("Explicit Projection Period Financial Statements")
        st.dataframe(forecast_df.style.format("₹{:,.2f}"))
        
    except Exception as e:
        st.error(f"Execution Error: Could not process valuation for this company. Details: {str(e)}")
