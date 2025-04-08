import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import requests

# === CONFIG ===
st.set_page_config(page_title="Allianz VitaVerde Simulator", layout="wide")

# === LOGO ===
logo_url = "https://raw.githubusercontent.com/softdatahardtruth/prototyp_unit_linked/main/allianz-logo.svg"
response = requests.get(logo_url)
if response.status_code == 200:
    svg_content = response.text
    st.markdown(f'<div style="text-align: center;">{svg_content}</div>', unsafe_allow_html=True)

# === TITLE ===
st.title("Allianz VitaVerde - Interactive Fund Simulator")
st.subheader("Real-time Data, Scenario Analysis, Tax Overview, and Allocation Insights")
st.markdown("---")

# === FUND DATA (Stable public tickers + descriptions) ===
funds = {
    "iShares MSCI World ETF": {
        "ticker": "URTH",
        "type": "Equity",
        "description": "Global developed markets equity exposure."
    },
    "SPDR S&P 500 ETF Trust": {
        "ticker": "SPY",
        "type": "Equity",
        "description": "Large-cap US equity exposure."
    },
    "iShares Euro Govt Bond 10-25yr UCITS ETF": {
        "ticker": "IEGA.DE",
        "type": "Bond",
        "description": "Eurozone government bonds with 10-25 years maturity."
    },
    "Vanguard FTSE All-World UCITS ETF": {
        "ticker": "VWRD.L",
        "type": "Equity",
        "description": "Global diversified equity exposure."
    },
    "Xtrackers MSCI Emerging Markets UCITS ETF": {
        "ticker": "XMME.DE",
        "type": "Equity",
        "description": "Emerging markets equity exposure."
    },
}

# === USER INPUTS ===
selected_funds = st.multiselect("Select your funds (up to 5)", list(funds.keys()), max_selections=5)
contribution = st.number_input("Monthly Contribution (€)", min_value=10, value=100, step=10)
duration = st.number_input("Investment Horizon (Years)", min_value=1, max_value=40, value=20, step=1)

allocations = {}
total_allocation = 0

if selected_funds:
    # Elegant fund details display in expander
    with st.expander("Fund Details", expanded=True):
        for fund in selected_funds:
            details = funds[fund]
            st.markdown(f"**{fund}**")
            st.markdown(f"- **Ticker:** {details['ticker']}")
            st.markdown(f"- **Type:** {details['type']}")
            st.markdown(f"- **Description:** {details['description']}")
            st.markdown("---")

    st.markdown("#### Allocate your contributions among the selected funds:")
    for fund in selected_funds:
        allocation = st.number_input(f"Allocation for {fund} (%)", min_value=0, max_value=100, value=0, step=1)
        allocations[fund] = allocation
        total_allocation += allocation

    # === ALLOCATION PIE CHART ===
    if total_allocation > 0:
        st.markdown("### Allocation Overview")
        labels = []
        sizes = []

        for fund in selected_funds:
            if allocations[fund] > 0:
                labels.append(fund)
                sizes.append(allocations[fund])

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

# === VALIDATION ===
if total_allocation > 100:
    st.error("The total allocation exceeds 100%. Please adjust your distribution.")
elif total_allocation < 100 and selected_funds:
    st.warning("The total allocation is less than 100%. Please adjust your distribution.")

# === RUN SIMULATION ===
if st.button("Run Simulation") and total_allocation == 100:
    st.markdown("### Fetching historical data...")

    # Fetch historical data
    fund_data = {}
    for fund in selected_funds:
        ticker = funds[fund]["ticker"]
        data = yf.download(ticker, period="5y", interval="1mo")
        data = data.dropna()
        fund_data[fund] = data

    # Safety check: At least one fund has data
    if all(data.empty for data in fund_data.values()):
        st.error("No historical data found for the selected funds. Please select different funds.")
    else:
        months = duration * 12
        paid_in = contribution * months

        simulation_results = {
            "Optimistic": [],
            "Expected": [],
            "Pessimistic": [],
        }

        # Run scenarios
        for scenario in simulation_results.keys():
            total_capital = np.zeros(months)

            for fund in selected_funds:
                allocation_pct = allocations[fund] / 100
                data = fund_data[fund]

                if data.empty:
                    st.warning(f"No data found for {fund}. Skipping this fund.")
                    continue

                price_column = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
                if price_column not in data.columns:
                    st.warning(f"No price data for {fund}. Skipping this fund.")
                    continue

                returns = data[price_column].pct_change().fillna(0).values
                if len(returns) == 0:
                    st.warning(f"Insufficient return data for {fund}. Skipping this fund.")
                    continue

                volatility = np.std(returns)
                mean_return = np.mean(returns)

                if scenario == "Optimistic":
                    returns = returns + volatility
                elif scenario == "Pessimistic":
                    returns = returns - volatility

                fund_capital = 0
                for month in range(months):
                    monthly_contribution = contribution * allocation_pct
                    fund_capital *= (1 + returns[min(month, len(returns) - 1)])
                    fund_capital += monthly_contribution
                    total_capital[month] += fund_capital

            simulation_results[scenario] = total_capital

        # === RESULTS OVERVIEW ===
        st.markdown("### Simulation Results")

        result_summary = []
        for scenario, capital in simulation_results.items():
            final = capital[-1]
            earnings = max(0, final - paid_in)

            if all(funds[fund]["type"] == "Bond" for fund in selected_funds):
                tax_rate = 0.125
            else:
                tax_rate = 0.26

            tax = earnings * tax_rate
            after_tax = final - tax

            result_summary.append({"Scenario": scenario, "Final Capital (€)": final, "Tax (€)": tax, "After Tax (€)": after_tax})

            st.write(f"**{scenario} Scenario:**")
            st.write(f" - Final Capital before Tax: {final:,.2f} €")
            st.write(f" - Tax: {tax:,.2f} €")
            st.write(f" - Final Capital after Tax: {after_tax:,.2f} €")

        # Summary DataFrame for export and plots
        summary_df = pd.DataFrame(result_summary)

        # === BAR CHART: Scenario Comparison ===
        st.markdown("### Scenario Comparison")
        fig2, ax2 = plt.subplots()
        ax2.bar(summary_df["Scenario"], summary_df["After Tax (€)"], color=['green', 'blue', 'red'])
        ax2.set_ylabel("After Tax Capital (€)")
        ax2.set_title("Scenario Comparison: After Tax Results")
        st.pyplot(fig2)

        # === CAPITAL DEVELOPMENT CHART ===
        st.markdown("### Capital Development Over Time")
        fig3, ax3 = plt.subplots()

        for scenario, capital in simulation_results.items():
            ax3.plot(range(months), capital, label=scenario)

        ax3.set_xlabel("Months")
        ax3.set_ylabel("Capital (€)")
        ax3.set_title("Simulation Scenarios Over Time")
        ax3.legend()

        st.pyplot(fig3)

        # === EXCEL EXPORT ===
        df = pd.DataFrame(simulation_results)
        df.index.name = "Month"

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Capital Development")
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

        excel_buffer.seek(0)

        st.download_button(
            label="Download results as Excel",
            data=excel_buffer,
            file_name="simulation_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Please enter your parameters and run the simulation.")