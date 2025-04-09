import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
from config import initialize_page
from data_fetching import fetch_logo, display_fund_details, fetch_fund_data, funds
from simulation import perform_simulation
from report_generation import generate_pdf_report, generate_excel_report
from guarantee_calculation import calculate_option_prices, plot_guarantee_vs_cost, plot_sensitivity_volatility, plot_sensitivity_time

def create_summary(simulation_results, paid_in, setup_cost_total, death_benefit_option, guarantee_rate):
    result_summary = []
    for scenario, capital in simulation_results.items():
        final_capital = capital[-1]
        gross_earnings = max(0, final_capital - paid_in)
        tax = gross_earnings * 0.26
        after_tax = final_capital - tax - setup_cost_total

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
    return summary_df

initialize_page()
fetch_logo()

selected_funds = st.sidebar.multiselect("Select funds (up to 5)", list(funds.keys()), max_selections=5)
contribution = st.sidebar.number_input("Monthly Contribution (€)", min_value=10, value=100, step=10)
duration = st.sidebar.number_input("Investment Horizon (Years)", min_value=1, max_value=40, value=20, step=1)

insurance_cost_rate = st.sidebar.slider("Annual Insurance Cost (% of fund value)", 0.0, 3.0, 1.0, step=0.1) / 100
setup_cost_rate = st.sidebar.slider("Initial Setup Cost (% of contributions)", 0.0, 5.0, 2.0, step=0.1) / 100
death_benefit_option = st.sidebar.checkbox("Include Death Benefit Guarantee (Paid-in Capital)", value=True)

guarantee_options = st.sidebar.selectbox("Contribution Guarantee", ["None", "25%", "50%", "75%"])
guarantee_rate = {"None": 0, "25%": 0.25, "50%": 0.50, "75%": 0.75}[guarantee_options]

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

if selected_funds:
    display_fund_details(selected_funds, allocations)

    # Save allocation pie chart to buffer
    buffer_pie = BytesIO()
    fig1, ax1 = plt.subplots(figsize=(4, 4))
    labels = [fund for fund in selected_funds if allocations[fund] > 0]
    sizes = [allocations[fund] for fund in selected_funds if allocations[fund] > 0]
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    fig1.savefig(buffer_pie, format='PNG')
    buffer_pie.seek(0)

if st.sidebar.button("Run Simulation") and total_allocation == 100:
    fund_data = fetch_fund_data(selected_funds)
    simulation_results = perform_simulation(selected_funds, allocations, fund_data, contribution, duration)
    
    paid_in = contribution * duration * 12
    setup_cost_total = paid_in * setup_cost_rate
    summary_df = create_summary(simulation_results, paid_in, setup_cost_total, death_benefit_option, guarantee_rate)

    # Save bar chart to buffer
    buffer_chart = BytesIO()
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.bar(summary_df["Scenario"], summary_df["Guaranteed Payout (EUR)"], color=['green', 'blue', 'red'])
    ax2.set_ylabel("Guaranteed Payout (EUR)")
    ax2.set_title("Scenario Comparison")
    fig2.savefig(buffer_chart, format='PNG')
    buffer_chart.seek(0)

    pdf_buffer = generate_pdf_report(summary_df, advisor_name, client_name, buffer_pie, buffer_chart)
    excel_buffer = generate_excel_report(simulation_results, summary_df)

    st.download_button(
        label="Download PDF Report",
        data=pdf_buffer,
        file_name=f"simulation_report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
    
    st.download_button(
        label="Download results as Excel",
        data=excel_buffer,
        file_name="simulation_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    initial_investment = contribution * duration * 12
    time_horizon = duration
    risk_free_rate = 0.02
    volatility = 0.15
    guarantee_levels = np.linspace(0, 1, 21)  # 0% bis 100% in 5%-Schritten

    option_prices = calculate_option_prices(initial_investment, time_horizon, risk_free_rate, volatility, guarantee_levels)
    plot_guarantee_vs_cost(guarantee_levels, option_prices)
    plot_sensitivity_volatility(initial_investment, time_horizon, risk_free_rate, guarantee_levels)
    plot_sensitivity_time(initial_investment, risk_free_rate, volatility, guarantee_levels)

else:
    st.info("Please complete all inputs in the sidebar and click 'Run Simulation'.")
