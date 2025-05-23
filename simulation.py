import streamlit as st
import numpy as np
import pandas as pd
from utils import calculate_tax

def calculate_weighted_average_return(selected_funds, allocations, fund_data, rebalancing_cost=0.00003):
    total_weighted_return = 0
    total_allocation = sum(allocations.values())
    
    #st.write(f"Total Allocation: {total_allocation}")

    for fund in selected_funds:
        allocation_pct = allocations[fund] / total_allocation
        data = fund_data[fund]
        
        if data.empty:
            continue
        
        mean_return, _ = calculate_expected_returns(data)
        
        # Adjust for rebalancing cost
        adjusted_mean_return = mean_return - rebalancing_cost
        
        # Debugging-Ausgabe für mean_return und allocation_pct
        #st.write(f"Fund: {fund}, Mean Return: {mean_return}, Adjusted Mean Return: {adjusted_mean_return}, Allocation Percentage: {allocation_pct}")

        weighted_return_contribution = adjusted_mean_return * allocation_pct
        #st.write(f"Weighted Return Contribution: {weighted_return_contribution}")

        total_weighted_return += weighted_return_contribution
    
    #st.write(f"Total Weighted Return: {total_weighted_return}")
    return total_weighted_return

def run_simulation(selected_funds, allocations, fund_data, contribution, months, scenario, weighted_average_return):
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
                adjusted_return = weighted_average_return + volatility
            elif scenario == "Pessimistic":
                adjusted_return = weighted_average_return - volatility
            else:
                adjusted_return = weighted_average_return

            # Apply rebalancing cost
            adjusted_return -= 0.00003

            # Debugging-Ausgabe für adjusted_return in Streamlit
            t.write(f"Month: {month}, Adjusted Return: {adjusted_return}")

            fund_capital *= (1 + adjusted_return)
            fund_capital += monthly_contribution

            # Debugging-Ausgabe für fund_capital vor der Addition in Streamlit
            #st.write(f"Month: {month}, Fund Capital before addition: {fund_capital}")

            # Sicherstellen, dass fund_capital ein skalarer Wert ist
            if isinstance(fund_capital, pd.Series):
                fund_capital = fund_capital.iloc[0]

            total_capital[month] += fund_capital

            # Debugging-Ausgabe in Streamlit
            #st.write(f"Month: {month}, Fund: {fund}, Fund Capital: {fund_capital}, Total Capital: {total_capital[month]}")

    return total_capital, total_contributions



def perform_simulation(selected_funds, allocations, fund_data, contribution, duration, tax_rate):
    months = duration * 12
    simulation_results = {"Optimistic": {}, "Expected": {}, "Pessimistic": {}}
    
    weighted_average_return = calculate_weighted_average_return(selected_funds, allocations, fund_data)
    
    for scenario in simulation_results.keys():
        total_capital, total_contributions = run_simulation(selected_funds, allocations, fund_data, contribution, months, scenario, weighted_average_return)
        
        end_capital = total_capital[-1]
        total_contribution = total_contributions.sum()
        profit = end_capital - total_contribution
        tax = calculate_tax(profit, tax_rate)

        simulation_results[scenario] = {
            "Final Capital": end_capital,
            "Earnings": profit,
            "Tax": tax
        }

    return simulation_results

