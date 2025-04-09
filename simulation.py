import numpy as np
import pandas as pd
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
