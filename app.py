import streamlit as st
from src.data_loader import fetch_financial_data
from src.valuation import calculate_wacc, build_base_forecast
from src.visualization import get_dcf_visuals, get_sensitivity_analysis

st.set_page_config(page_title="Institutional DCF Engine", layout="wide")
st.title("Institutional Fundamental Valuation Platform (Indian Markets)")

# Master Dictionary mapping Company Names to their Yahoo Finance Tickers
INDIAN_STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services (TCS)": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India (SBI)": "SBIN.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "ITC Limited": "ITC.NS",
    "Larsen & Toubro (L&T)": "LT.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Hindustan Unilever (HUL)": "HINDUNILVR.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "Titan Company": "TITAN.NS"
}

st.sidebar.header("Model Inputs")

# The smart dropdown that lets you type the name to search
company_name = st.sidebar.selectbox(
    "Search Company Name",
    options=list(INDIAN_STOCKS.keys()) + ["Enter Custom Ticker..."]
)

# Background logic to handle the ticker cleanly
if company_name == "Enter Custom Ticker...":
    raw_ticker = st.sidebar.text_input("Enter base ticker (e.g., ZOMATO, PAYTM)", value="ZOMATO")
    # Auto-append .NS in the background so the user doesn't have to!
    ticker = raw_ticker.upper()
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = f"{ticker}.NS"
else:
    ticker = INDIAN_STOCKS[company_name]

forecast_years = st.sidebar.slider("Forecast Period (Years)", min_value=3, max_value=10, value=5)
erp = st.sidebar.slider("Equity Risk Premium (India)", min_value=0.05, max_value=0.10, value=0.075, step=0.005)
terminal_growth = st.sidebar.slider("Terminal Perpetuity Growth Rate", min_value=0.01, max_value=0.05, value=0.025, step=0.005)

if st.sidebar.button("Run Valuation Engine"):
    try:
        with st.spinner(f"Processing market data for {ticker}..."):
            fin_data = fetch_financial_data(ticker, market_risk_premium=erp)
            wacc_computed = calculate_wacc(fin_data, market_risk_premium=erp)
            forecast_df, ev, eqv, implied_price, tv = build_base_forecast(
                fin_data, wacc_computed, forecast_years=forecast_years, terminal_growth=terminal_growth
            )
            
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
        st.error(f"Execution Error: {str(e)}")
