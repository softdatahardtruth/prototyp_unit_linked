import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from fpdf import FPDF
import requests

# Logo laden
logo_url = "https://raw.githubusercontent.com/softdatahardtruth/prototyp_unit_linked/main/allianz-logo.svg"
response = requests.get(logo_url)
if response.status_code == 200:
    svg_content = response.text
    st.markdown(f'<div style="text-align: center;">{svg_content}</div>', unsafe_allow_html=True)

# Title
st.title("Allianz VitaVerde - Live Fund Simulator")
st.subheader("Real-time Data, Scenario Analysis, and Tax Simulation")
st.markdown("---")

# Fund selection with real tickers
funds = {
    "Allianz Strategy Select 30 (Eur)": {"ticker": "0P0000Q8MA.IR", "type": "Mixed"},
    "Allianz Strategy Select 50 (Eur)": {"ticker": "0P0000Q8MB.IR", "type": "Mixed"},
    "Allianz Strategy Select 75 (Eur)": {"ticker": "0P0000Q8MC.IR", "type": "Equity"},
    "iShares Euro Govt Bond 15-30yr": {"ticker": "IBGL.DE", "type": "Bond"},
    "MSCI World ETF": {"ticker": "URTH", "type": "Equity"},
}

selected_funds = st.multiselect("Select your funds (up to 5)", list(funds.keys()), max_selections=5)
contribution = st.number_input("Monthly Contribution (€)", min_value=10, value=100, step=10)
duration = st.number_input("Investment Horizon (Years)", min_value=1, max_value=40, value=20, step=1)

allocations = {}
total_allocation = 0

if selected_funds:
    st.markdown("#### Allocate your contributions among the selected funds:")
    for fund in selected_funds:
        allocation = st.number_input(f"Allocation for {fund} (%)", min_value=0, max_value=100, value=0, step=1)
        allocations[fund] = allocation
        total_allocation += allocation

# === VALIDATION ===
if total_allocation > 100:
    st.error("The total allocation exceeds 100%. Please adjust your distribution.")
elif total_allocation < 100 and selected_funds:
    st.warning("The total allocation is less than 100%. Please adjust your distribution.")

# === RUN SIMULATION ===
if st.button("Run Simulation") and total_allocation == 100:
    st.markdown("### Fetching historical data...")

    # Fetch data
    fund_data = {}
    for fund in selected_funds:
        ticker = funds[fund]["ticker"]
        data = yf.download(ticker, period="5y", interval="1mo")
        data = data.dropna()
        fund_data[fund] = data

    # Prepare simulation
    months = duration * 12
    initial_month = list(fund_data.values())[0].index[0]

    simulation_results = {
        "Optimistic": [],
        "Expected": [],
        "Pessimistic": [],
    }

    paid_in = contribution * months

    # Run scenarios
    for scenario in simulation_results.keys():
        total_capital = np.zeros(months)

        for fund in selected_funds:
            allocation_pct = allocations[fund] / 100
            data = fund_data[fund]
            returns = data['Adj Close'].pct_change().fillna(0).values

            # Scenario adjustment
            volatility = np.std(returns)
            mean_return = np.mean(returns)

            if scenario == "Optimistic":
                returns = returns + volatility
            elif scenario == "Pessimistic":
                returns = returns - volatility

            fund_capital = 0
            fund_capitals = []

            for month in range(months):
                monthly_contribution = contribution * allocation_pct
                fund_capital *= (1 + returns[min(month, len(returns)-1)])
                fund_capital += monthly_contribution
                fund_capitals.append(fund_capital)

                total_capital[month] += fund_capital

        simulation_results[scenario] = total_capital

    # Display results
    st.markdown("### Simulation Results")

    for scenario, capital in simulation_results.items():
        final = capital[-1]
        earnings = max(0, final - paid_in)

        # Tax calculation based on fund types
        tax_rate = 0.26
        if all(funds[fund]["type"] == "Bond" for fund in selected_funds):
            tax_rate = 0.125  # Favorable tax for bonds

        tax = earnings * tax_rate
        after_tax = final - tax

        st.write(f"**{scenario} Scenario:**")
        st.write(f" - Final Capital before Tax: {final:,.2f} €")
        st.write(f" - After Tax: {after_tax:,.2f} €")

    # Plot
    st.markdown("### Capital Development over Time")
    fig, ax = plt.subplots()

    for scenario, capital in simulation_results.items():
        ax.plot(range(months), capital, label=scenario)

    ax.set_xlabel("Months")
    ax.set_ylabel("Capital (€)")
    ax.set_title("Simulation Scenarios")
    ax.legend()

    st.pyplot(fig)

else:
    st.info("Please enter your parameters and run the simulation.")