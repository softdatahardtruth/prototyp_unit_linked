import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Dummy fund data (Active4Life)
funds = {
    "Allianz Strategy Select 30": {"return": 0.03, "guarantee": 0.93},
    "Allianz Strategy 4Life Europe 40": {"return": 0.04, "guarantee": 0.92},
    "Allianz Strategy Select 50": {"return": 0.05, "guarantee": 0.90},
    "Allianz Strategy Select 75": {"return": 0.06, "guarantee": 0.85},
}

# Header section
st.title("Allianz Active4Life - Interactive Simulator")
st.subheader("Explore the development of your unit-linked life insurance")
st.markdown("---")

# User Inputs
fund_selection = st.selectbox("Choose your fund", list(funds.keys()))
contribution = st.number_input("Monthly Contribution (€)", min_value=10, value=100, step=10)
duration = st.number_input("Duration (Years)", min_value=1, max_value=40, value=20, step=1)

# Start simulation
if st.button("Start Simulation"):
    # Load parameters
    data = funds[fund_selection]
    return_rate = data["return"]
    guarantee = data["guarantee"]
    months = duration * 12
    capital_development = []
    capital = 0
    paid_in = contribution * months
    
    for month in range(months):
        capital *= (1 + return_rate / 12)
        capital += contribution
        capital_development.append(capital)
    
    final_capital = capital_development[-1]

    # Estimate taxes (26% on earnings)
    earnings = max(0, final_capital - paid_in)
    tax = earnings * 0.26
    after_tax = final_capital - tax

    # Display results
    st.markdown("### Results")
    st.write(f"**Paid-in Capital:** {paid_in:,.2f} €")
    st.write(f"**Capital before Taxes:** {final_capital:,.2f} €")
    st.write(f"**Capital after Taxes:** {after_tax:,.2f} €")
    st.markdown("---")

    # Graph
    st.markdown("### Development over Time")
    fig, ax = plt.subplots()
    ax.plot(range(months), capital_development)
    ax.set_xlabel("Months")
    ax.set_ylabel("Capital (€)")
    ax.set_title("Capital Development")
    st.pyplot(fig)
else:
    st.info("Please enter the parameters and start the simulation.")
