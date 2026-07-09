import numpy as np
import pandas as pd

def calculate_wacc(data, market_risk_premium=0.075):
    cost_of_equity = data['risk_free_rate'] + (data['beta'] * market_risk_premium)
    cost_of_debt = data['risk_free_rate'] + 0.015 
    
    total_capital = data['market_cap'] + data['total_debt']
    weight_equity = data['market_cap'] / total_capital
    weight_debt = data['total_debt'] / total_capital
    
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - data['tax_rate']))
    return wacc

def build_base_forecast(data, wacc, forecast_years=5, terminal_growth=0.025):
    years = np.arange(1, forecast_years + 1)
    rev_growth = np.linspace(data['historical_growth'], terminal_growth, forecast_years)
    margins = np.linspace(data['ebit_margin'], data['ebit_margin'] * 0.95, forecast_years)
    
    capex_pct = data['capex'] / data['total_revenue']
    da_pct = data['depreciation'] / data['total_revenue']
    nwc_pct = 0.03 
    
    forecast = pd.DataFrame(index=years)
    
    revenues = [data['total_revenue'] * (1 + rev_growth[0])]
    for i in range(1, forecast_years):
        revenues.append(revenues[-1] * (1 + rev_growth[i]))
        
    forecast['Revenue'] = revenues
    forecast['EBIT'] = forecast['Revenue'] * margins
    forecast['NOPAT'] = forecast['EBIT'] * (1 - data['tax_rate'])
    forecast['D&A'] = forecast['Revenue'] * da_pct
    forecast['CapEx'] = forecast['Revenue'] * capex_pct
    forecast['Change_NWC'] = forecast['Revenue'] * nwc_pct
    
    forecast['FCFF'] = forecast['NOPAT'] + forecast['D&A'] - forecast['CapEx'] - forecast['Change_NWC']
    forecast['Discount_Factor'] = (1 + wacc) ** forecast.index
    forecast['PV_FCFF'] = forecast['FCFF'] / forecast['Discount_Factor']
    
    terminal_value = (forecast['FCFF'].iloc[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / ((1 + wacc) ** forecast_years)
    
    enterprise_value = forecast['PV_FCFF'].sum() + pv_terminal_value
    equity_value = enterprise_value - data['total_debt'] + data['cash']
    implied_share_price = equity_value / data['shares_out']
    
    return forecast, enterprise_value, equity_value, implied_share_price, terminal_value
