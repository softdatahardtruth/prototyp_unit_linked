import numpy as np
import pandas as pd

def calculate_expected_returns(data):
    price_column = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
    monthly_returns = data[price_column].pct_change().dropna()
    mean_return = monthly_returns.mean()
    volatility = monthly_returns.std()
    return mean_return, volatility

def run_simulation(selected_funds, allocations, fund_data, contribution, months, scenario):
    total_capital = np.zeros(months)
    total_contributions = np.zeros(months)

    for fund in selected_funds:
        allocation_pct = allocations[fund] / 100
        data = fund_data[fund]

        if data.empty or allocation_pct == 0:
            continue

        mean_return, volatility = calculate_expected_returns(data)

        fund_capital = 0
        for month in range(months):
            monthly_contribution = contribution * allocation_pct
            total_contributions[month] += monthly_contribution

            # Adjust monthly return based on scenario
            if scenario == "Optimistic":
                adjusted_return = mean_return + volatility
            elif scenario == "Pessimistic":
                adjusted_return = mean_return - volatility
            else:
                adjusted_return = mean_return

            fund_capital *= (1 + adjusted_return)
            fund_capital += monthly_contribution
            total_capital[month] += fund_capital

    return total_capital, total_contributions

def perform_simulation(selected_funds, allocations, fund_data, contribution, duration, tax_rate):
    months = duration * 12
    simulation_results = {"Optimistic": {}, "Expected": {}, "Pessimistic": {}}
    
    for scenario in simulation_results.keys():
        total_capital, total_contributions = run_simulation(selected_funds, allocations, fund_data, contribution, months, scenario)
        
        end_capital = total_capital[-1]
        total_contribution = total_contributions.sum()
        profit = end_capital - total_contribution
        tax = profit * tax_rate
        
        simulation_results[scenario] = {
            "Endkapital": end_capital,
            "Gewinn": profit,
            "Steuer": tax
        }

    return simulation_results
