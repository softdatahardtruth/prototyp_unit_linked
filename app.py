import streamlit as st
import numpy as np
from config import initialize_page
from data_fetching import fetch_logo, display_fund_details, fetch_fund_data
from simulation import perform_simulation
from report_generation import generate_pdf_report, generate_excel_report
from guarantee_calculation import calculate_option_prices, plot_guarantee_vs_cost, plot_sensitivity_volatility, plot_sensitivity_time

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

if st.sidebar.button("Run Simulation") and total_allocation == 100:
    fund_data = fetch_fund_data(selected_funds)
    simulation_results = perform_simulation(selected_funds, allocations, fund_data, contribution, duration)
    
    # Generate and display reports...
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

    # Guarantee calculations
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
