import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def get_dcf_visuals(forecast, data, tv, wacc, forecast_years, equity_value):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    sns.set_theme(style="whitegrid")
    
    axes[0].bar(forecast.index, forecast['FCFF'] / 1e9, color='#2c3e50', label='FCFF')
    axes[0].plot(forecast.index, forecast['Revenue'] / 1e9, color='#e74c3c', marker='o', label='Revenue')
    axes[0].set_title('Revenue and FCFF Forecast (in Billions)')
    axes[0].set_xlabel('Year')
    axes[0].set_ylabel('INR (Billions)')
    axes[0].legend()
    
    components = ['PV of Explicit FCFF', 'PV of Terminal Value', 'Plus: Cash', 'Less: Debt', 'Equity Value']
    pv_fcff_sum = forecast['PV_FCFF'].sum()
    pv_tv = tv / ((1 + wacc) ** forecast_years)
    values = [pv_fcff_sum / 1e9, pv_tv / 1e9, data['cash'] / 1e9, -data['total_debt'] / 1e9, equity_value / 1e9]
    
    axes[1].bar(components, values, color=['#3498db', '#2980b9', '#27ae60', '#c0392b', '#8e44ad'])
    axes[1].set_title('Enterprise Value to Equity Value Bridge (in Billions)')
    axes[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def get_sensitivity_analysis(data, base_wacc, forecast_years, from_valuation_func):
    wacc_range = np.linspace(base_wacc - 0.02, base_wacc + 0.02, 7)
    tg_range = np.linspace(0.01, 0.04, 7)
    sensitivity_matrix = np.zeros((len(wacc_range), len(tg_range)))
    
    for i, w in enumerate(wacc_range):
        for j, tg in enumerate(tg_range):
            _, _, _, price, _ = from_valuation_func(data, w, forecast_years=forecast_years, terminal_growth=tg)
            sensitivity_matrix[i, j] = price
            
    fig = plt.figure(figsize=(10, 6))
    sns.heatmap(sensitivity_matrix, 
                xticklabels=[f"{x:.1%}" for x in tg_range], 
                yticklabels=[f"{x:.1%}" for x in wacc_range],
                annot=True, fmt=".2f", cmap="RdYlGn", center=data['market_price'])
    plt.title('Implied Share Price Sensitivity: WACC vs Terminal Growth')
    plt.xlabel('Terminal Growth Rate')
    plt.ylabel('WACC')
    return fig
