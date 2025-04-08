import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
from io import BytesIO
import tempfile
import requests

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Allianz VitaVerde - Simulation Report", 0, 1, "C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Generated by Allianz VitaVerde Simulator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, "C")

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

# Beitragsgarantie Optionen
guarantee_options = st.sidebar.selectbox("Contribution Guarantee", ["None", "25%", "50%", "75%"])
guarantee_rate = {"None": 0, "25%": 0.25, "50%": 0.50, "75%": 0.75}[guarantee_options]

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
        simulation_results = {"Optimistic": [], "Expected": [], "Pessimistic": []}

        def calculate_expected_returns(data):
            price_column = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
            monthly_returns = data[price_column].pct_change().dropna()
            mean_return = monthly_returns.mean()
            volatility = monthly_returns.std()
            return mean_return, volatility

        def run_simulation(mean_return, volatility, scenario):
            total_capital = np.zeros(months)
            for fund in selected_funds:
                allocation_pct = allocations[fund] / 100
                data = fund_data[fund]

                if data.empty or allocation_pct == 0:
                    continue

                price_column = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
                monthly_returns = data[price_column].pct_change().fillna(0).values
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

        for scenario in simulation_results.keys():
            mean_returns = []
            volatilities = []
            for fund in selected_funds:
                data = fund_data[fund]
                mean_return, volatility = calculate_expected_returns(data)
                mean_returns.append(mean_return)
                volatilities.append(volatility)

            simulation_results[scenario] = run_simulation(np.mean(mean_returns), np.mean(volatilities), scenario)

        result_summary = []

        for scenario, capital in simulation_results.items():
            final_capital = capital[-1]
            gross_earnings = max(0, final_capital - paid_in)
            tax = gross_earnings * 0.26
            after_tax = final_capital - tax - setup_cost_total

            # Anwendung der Todesfalloption und Beitragsgarantie
            death_benefit = max(paid_in, after_tax) if death_benefit_option else after_tax
            contribution_guarantee = paid_in * guarantee_rate
            guaranteed_payout = max(death_benefit, contribution_guarantee)

            result_summary.append({
                "Scenario": scenario,
                "Paid-in Capital (EUR)": paid_in,
                "Final Capital (EUR)": final_capital,
                "Earnings (EUR)": gross_earnings,
                "Tax (EUR)": tax,
                "Setup Cost (EUR)": setup_cost_total,
                "After Tax (EUR)": after_tax,
                "Death Benefit (EUR)": death_benefit,
                "Guaranteed Payout (EUR)": guaranteed_payout
            })

        summary_df = pd.DataFrame(result_summary)

        # Helper function for safe formatting
        def safe_format(value):
            if isinstance(value, (int, float, np.number)) and pd.notnull(value):
                return "{:,.2f}".format(value)
            else:
                return "n/a"

        # Formatieren Sie die DataFrame vor der Anzeige
        summary_df_formatted = summary_df.copy()
        for col in summary_df_formatted.columns:
            if summary_df_formatted[col].dtype in [np.float64, np.int64]:
                summary_df_formatted[col] = summary_df_formatted[col].apply(safe_format)

        st.markdown("### Simulation Results")
        st.dataframe(summary_df_formatted)

        # === Bar Chart Comparison ===
        st.markdown("### Scenario Comparison: Guaranteed Payout")
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.bar(summary_df["Scenario"], summary_df["Guaranteed Payout (EUR)"], color=['green', 'blue', 'red'])
        ax2.set_ylabel("Guaranteed Payout (EUR)")
        ax2.set_title("Scenario Comparison")
        st.pyplot(fig2)

        # Save chart to buffer for PDF
        buffer_chart = BytesIO()
        fig2.savefig(buffer_chart, format='PNG')
        buffer_chart.seek(0)

        # === Capital Development Over Time ===
        st.markdown("### Capital Development Over Time")
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        for scenario, capital in simulation_results.items():
            ax3.plot(range(months), capital, label=scenario)

        ax3.set_xlabel("Months")
        ax3.set_ylabel("Capital (EUR)")
        ax3.set_title("Growth Over Time")
        ax3.legend()
        st.pyplot(fig3)

        # Save allocation pie chart for PDF
        buffer_pie = BytesIO()
        fig1.savefig(buffer_pie, format='PNG')
        buffer_pie.seek(0)

        # === Excel Export ===
        df_results = pd.DataFrame(simulation_results)

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_results.to_excel(writer, sheet_name="Simulation Results")
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

        excel_buffer.seek(0)

        st.download_button(
            label="Download results as Excel",
            data=excel_buffer,
            file_name="simulation_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # === PDF Export ===
    st.markdown("### Download PDF Report")

    pdf = PDF()
    pdf.add_page()

    # Verwendung der Standard-Schriftart Arial
    pdf.set_font("Arial", "", 12)

    # Title and meta info
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Allianz VitaVerde - Simulation Report", ln=True)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(0, 10, f"Advisor: {advisor_name} | Client: {client_name}", ln=True)

    # Parameters
    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    pdf.cell(0, 10, f"Monthly Contribution: {safe_format(contribution)}", ln=True)
    pdf.cell(0, 10, f"Investment Horizon: {duration} years", ln=True)
    pdf.cell(0, 10, f"Insurance Cost: {insurance_cost_rate * 100:.2f}%", ln=True)
    pdf.cell(0, 10, f"Setup Cost: {setup_cost_rate * 100:.2f}%", ln=True)
    pdf.cell(0, 10, f"Death Benefit Guarantee: {'Yes' if death_benefit_option else 'No'}", ln=True)
    pdf.cell(0, 10, f"Contribution Guarantee: {guarantee_options}", ln=True)

    # Pie Chart
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Fund Allocation", ln=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        tmpfile.write(buffer_pie.getvalue())
        pdf.image(tmpfile.name, w=100)

    # Bar Chart
    pdf.ln(10)
    pdf.cell(0, 10, "Scenario Comparison", ln=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        tmpfile.write(buffer_chart.getvalue())
        pdf.image(tmpfile.name, w=150)

    # Summary
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Simulation Summary", ln=True)
    pdf.set_font("Arial", "", 10)

    for idx, row in summary_df.iterrows():
        pdf.multi_cell(
            0, 8,
            f"{row['Scenario']}: "
            f"Paid-in: {safe_format(row['Paid-in Capital (EUR)'])} | "
            f"After Tax: {safe_format(row['After Tax (EUR)'])} | "
            f"Guaranteed Payout: {safe_format(row['Guaranteed Payout (EUR)'])}"
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
