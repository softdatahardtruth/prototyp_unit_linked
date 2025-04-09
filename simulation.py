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
    for fund in selected_funds:
        allocation_pct = allocations[fund] / 100
        data = fund_data[fund]

        if data.empty or allocation_pct == 0:
            continue

        mean_return, volatility = calculate_expected_returns(data)

        fund_capital = 0
        for month in range(months):
            monthly_contribution = contribution * allocation_pct

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

    return total_capital

def perform_simulation(selected_funds, allocations, fund_data, contribution, duration):
    months = duration * 12
    simulation_results = {"Optimistic": [], "Expected": [], "Pessimistic": []}
    
    for scenario in simulation_results.keys():
        simulation_results[scenario] = run_simulation(selected_funds, allocations, fund_data, contribution, months, scenario)

    return simulation_results
