import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import requests
from fpdf import FPDF
from datetime import datetime

# === CONFIG ===
st.set_page_config(page_title="Allianz VitaVerde Simulator", layout="wide")

# === LOGO ===
logo_url = "https://raw.githubusercontent.com/softdatahardtruth/prototyp_unit_linked/main/allianz-logo.svg"
response = requests.get(logo_url)
if response.status_code == 200:
    svg_content = response.text
    st.markdown(f'<div style="text-align: center; margin-bottom: 20px;">{svg_content}</div>', unsafe_allow_html=True)

st.title("Allianz VitaVerde - Insurance & Investment Simulator")

# === FUND DATA ===
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

# === SIDEBAR: INPUT ===
st.sidebar.header("Input Parameters")

selected_funds = st.sidebar.multiselect("Select funds (up to 5)", list(funds.keys()), max_selections=5)
contribution = st.sidebar.number_input("Monthly Contribution (€)", min_value=10, value=100, step=10)
duration = st.sidebar.number_input("Investment Horizon (Years)", min_value=1, max_value=40, value=20, step=1)

insurance_cost_rate = st.sidebar.slider("Annual Insurance Cost (% of fund value)", 0.0, 3.0, 1.0, step=0.1) / 100
setup_cost_rate = st.sidebar.slider("Initial Setup Cost (% of contributions)", 0.0, 5.0, 2.0, step=0.1) / 100
death_benefit_option = st.sidebar.checkbox("Include Death Benefit Guarantee (Paid-in Capital)", value=True)

# Optional: Advisor and Client Name for PDF
advisor_name = st.sidebar.text_input("Advisor Name (optional)", value="Advisor")
client_name = st.sidebar.text_input("Client Name (optional)", value="Client")

allocations = {}
total_allocation = 0

if selected_funds:
    st.sidebar.markdown("### Allocate your contributions:")
    for fund in selected_funds:
        allocation = st.sidebar.number_input(f"{fund} (%)", min_value=0, max_value=100, value=0, step=1)
        allocations[fund] = allocation
        total_allocation += allocation

if total_allocation > 100:
    st.sidebar.error("Total allocation exceeds 100%. Adjust your distribution.")
elif total_allocation < 100 and selected_funds:
    st.sidebar.warning("Total allocation is less than 100%.")

# === MAIN: DISPLAY FUND DETAILS ===
if selected_funds:
    st.subheader("Fund Details")
    cols = st.columns(len(selected_funds))
    for idx, fund in enumerate(selected_funds):
        details = funds[fund]
        with cols[idx]:
            st.markdown(f"**{fund}**")
            st.markdown(f"- **Ticker:** {details['ticker']}")
            st.markdown(f"- **Type:** {details['type']}")
            st.markdown(f"- {details['description']}")

    if total_allocation > 0:
        st.markdown("### Allocation Overview")
        labels = [fund for fund in selected_funds if allocations[fund] > 0]
        sizes = [allocations[fund] for fund in selected_funds if allocations[fund] > 0]

        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

# === SIMULATION ===
if st.sidebar.button("Run Simulation") and total_allocation == 100:
    st.subheader("Simulation Results")

    months = duration * 12
    paid_in = contribution * months
    setup_cost_total = paid_in * setup_cost_rate

    st.markdown("Fetching historical fund data...")
    fund_data = {}
    for fund in selected_funds:
        ticker = funds[fund]["ticker"]
        data = yf.download(ticker, period="5y", interval="1mo").dropna()
        fund_data[fund] = data

    if all(data.empty for data in fund_data.values()):
        st.error("No historical data found for the selected funds.")
    else:
        simulation_results_with = {"Optimistic": [], "Expected": [], "Pessimistic": []}
        simulation_results_without = {"Optimistic": [], "Expected": [], "Pessimistic": []}

        def run_simulation(apply_insurance_cost):
            results = {}
            for scenario in ["Optimistic", "Expected", "Pessimistic"]:
                total_capital = np.zeros(months)

                for fund in selected_funds:
                    allocation_pct = allocations[fund] / 100
                    data = fund_data[fund]

                    if data.empty or allocation_pct == 0:
                        continue

                    price_column = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
                    returns = data[price_column].pct_change().fillna(0).values
                    volatility = np.std(returns)

                    if scenario == "Optimistic":
                        returns = returns + volatility
                    elif scenario == "Pessimistic":
                        returns = returns - volatility

                    fund_capital = 0
                    for month in range(months):
                        monthly_contribution = contribution * allocation_pct
                        fund_capital *= (1 + returns[min(month, len(returns) - 1)])
                        if apply_insurance_cost:
                            fund_capital *= (1 - insurance_cost_rate / 12)
                        fund_capital += monthly_contribution
                        total_capital[month] += fund_capital

                results[scenario] = total_capital
            return results

        simulation_results_with = run_simulation(apply_insurance_cost=True)
        simulation_results_without = run_simulation(apply_insurance_cost=False)

        result_summary_with = []
        result_summary_without = []

        for scenario, capital in simulation_results_with.items():
            final_capital = capital[-1]
            gross_earnings = max(0, final_capital - paid_in)
            tax = gross_earnings * 0.26
            after_tax = final_capital - tax - setup_cost_total
            death_benefit = max(paid_in, after_tax) if death_benefit_option else after_tax

            result_summary_with.append({
                "Scenario": scenario,
                "Paid-in Capital (€)": paid_in,
                "Final Capital (€)": final_capital,
                "Earnings (€)": gross_earnings,
                "Tax (€)": tax,
                "Setup Cost (€)": setup_cost_total,
                "After Tax (€)": after_tax,
                "Death Benefit (€)": death_benefit
            })

        for scenario, capital in simulation_results_without.items():
            final_capital = capital[-1]
            gross_earnings = max(0, final_capital - paid_in)
            tax = gross_earnings * 0.26
            after_tax = final_capital - tax

            result_summary_without.append({
                "Scenario": scenario,
                "Paid-in Capital (€)": paid_in,
                "Final Capital (€)": final_capital,
                "Earnings (€)": gross_earnings,
                "Tax (€)": tax,
                "After Tax (€)": after_tax
            })

        summary_df_with = pd.DataFrame(result_summary_with)
        summary_df_without = pd.DataFrame(result_summary_without)

        st.markdown("### With Insurance Wrapper")
        st.dataframe(summary_df_with.style.format("{:,.2f}"))

        st.markdown("### Without Insurance Wrapper")
        st.dataframe(summary_df_without.style.format("{:,.2f}"))
        
                # === Bar Chart Comparison ===
        st.markdown("### Scenario Comparison: After Tax & Death Benefit")
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.bar(summary_df_with["Scenario"], summary_df_with["Death Benefit (€)"], color=['green', 'blue', 'red'])
        ax2.set_ylabel("Net Outcome (€)")
        ax2.set_title("With Insurance - Scenario Comparison")
        st.pyplot(fig2)

        # Save chart to buffer for PDF
        buffer_chart = BytesIO()
        fig2.savefig(buffer_chart, format='PNG')
        buffer_chart.seek(0)

        # === Capital Development Over Time ===
        st.markdown("### Capital Development Over Time (With Insurance)")
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        for scenario, capital in simulation_results_with.items():
            ax3.plot(range(months), capital, label=scenario)

        ax3.set_xlabel("Months")
        ax3.set_ylabel("Capital (€)")
        ax3.set_title("Growth Over Time")
        ax3.legend()
        st.pyplot(fig3)

        # Save allocation pie chart for PDF
        buffer_pie = BytesIO()
        fig1.savefig(buffer_pie, format='PNG')
        buffer_pie.seek(0)

        # === Excel Export ===
        df_with = pd.DataFrame(simulation_results_with)
        df_without = pd.DataFrame(simulation_results_without)

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_with.to_excel(writer, sheet_name="With Insurance")
            df_without.to_excel(writer, sheet_name="Without Insurance")
            summary_df_with.to_excel(writer, sheet_name="Summary With", index=False)
            summary_df_without.to_excel(writer, sheet_name="Summary Without", index=False)

        excel_buffer.seek(0)

        st.download_button(
            label="Download results as Excel",
            data=excel_buffer,
            file_name="simulation_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # === PDF Export ===
    st.markdown("### Download PDF Report")
    # Helper function for safe formatting
    def value(x):
        return f"€{x:,.2f}" if isinstance(x, (int, float, np.number)) and pd.notnull(x) else "n/a"
    pdf = FPDF()
    pdf.add_page()

    # Title and meta info
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Allianz VitaVerde - Simulation Report", ln=True)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(0, 10, f"Advisor: {advisor_name} | Client: {client_name}", ln=True)

    # Parameters
    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    pdf.cell(0, 10, f"Monthly Contribution: {value(contribution)}", ln=True)
    pdf.cell(0, 10, f"Investment Horizon: {duration} years", ln=True)
    pdf.cell(0, 10, f"Insurance Cost: {insurance_cost_rate * 100:.2f}%", ln=True)
    pdf.cell(0, 10, f"Setup Cost: {setup_cost_rate * 100:.2f}%", ln=True)
    pdf.cell(0, 10, f"Death Benefit Guarantee: {'Yes' if death_benefit_option else 'No'}", ln=True)

    # Pie Chart
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Fund Allocation", ln=True)
    pdf.image(buffer_pie, w=100)

    # Bar Chart

    pdf.ln(10)
    pdf.cell(0, 10, "Scenario Comparison", ln=True)
    pdf.image(buffer_chart, w=150)

    # Summary with insurance

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Summary With Insurance", ln=True)
    pdf.set_font("Arial", "", 10)

    for idx, row in summary_df_with.iterrows():
        pdf.multi_cell(
            0, 8,
            f"{row['Scenario']}: "
            f"Paid-in: {value(row['Paid-in Capital (€)'])} | "
            f"After Tax: {value(row['After Tax (€)'])} | "
            f"Death Benefit: {value(row['Death Benefit (€)'])}"
        )

    # Summary without insurance

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Summary Without Insurance", ln=True)
    pdf.set_font("Arial", "", 10)

    for idx, row in summary_df_without.iterrows():
        pdf.multi_cell(
            0, 8,
            f"{row['Scenario']}: "
            f"Paid-in: {value(row['Paid-in Capital (€)'])} | "
            f"After Tax: {value(row['After Tax (€)'])}"
        )

    # Footer

    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "Generated by Allianz VitaVerde Simulator", 0, 0, 'C')

    # Output PDF

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)

    st.download_button(
        label="Download PDF Report",
        data=pdf_buffer,
        file_name=f"simulation_report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"

    )

else:
    st.info("Please complete all inputs in the sidebar and click 'Run Simulation'.") 
