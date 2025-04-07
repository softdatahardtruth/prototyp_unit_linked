import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

# Dummy fund data (Active4Life)
funds = {
    "Allianz Strategy Select 30": {"return": 0.03, "guarantee": 0.93},
    "Allianz Strategy 4Life Europe 40": {"return": 0.04, "guarantee": 0.92},
    "Allianz Strategy Select 50": {"return": 0.05, "guarantee": 0.90},
    "Allianz Strategy Select 75": {"return": 0.06, "guarantee": 0.85},
}

# URL to the raw SVG file in your GitHub repository
logo_url = "https://github.com/softdatahardtruth/prototyp_unit_linked/blob/main/allianz-logo.svg"

# Fetch and display the Allianz logo
response = requests.get(logo_url)
if response.status_code == 200:
    st.image(response.content, format="svg")
else:
    st.error("Failed to load the Allianz logo.")

# Header section
st.title("Allianz VitaVerde - Interactive Simulator")
st.subheader("Explore the development of your unit-linked life insurance")
st.markdown("---")

# User Inputs
selected_funds = st.multiselect("Choose up to five funds", list(funds.keys()), max_selections=5)
contribution = st.number_input("Monthly Contribution (€)", min_value=10, value=100, step=10)
duration = st.number_input("Duration (Years)", min_value=1, max_value=40, value=20, step=1)

# Allocation inputs
allocations = {}
total_allocation = 0

if selected_funds:
    st.markdown("#### Allocate your contribution among the selected funds:")
    for fund in selected_funds:
        allocation = st.number_input(f"Allocation for {fund} (%)", min_value=0, max_value=100, value=0, step=1)
        allocations[fund] = allocation
        total_allocation += allocation

# Check allocation validity
if total_allocation > 100:
    st.error("The total allocation exceeds 100%. Please adjust your allocations.")
elif total_allocation < 100:
    st.warning("The total allocation is less than 100%. Please adjust your allocations.")

# Start simulation
if st.button("Start Simulation") and total_allocation == 100:
    months = duration * 12
    capital_development = {fund: [] for fund in selected_funds}
    total_capital = 0
    paid_in = contribution * months

    for month in range(months):
        monthly_contributions = {fund: contribution * allocations[fund] / 100 for fund in selected_funds}
        for fund in selected_funds:
            data = funds[fund]
            fund_return = data["return"]
            capital_development[fund].append(monthly_contributions[fund] * ((1 + fund_return / 12) ** month))
            total_capital += capital_development[fund][-1]

    final_capital = sum([capital_development[fund][-1] for fund in selected_funds])

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
    for fund in selected_funds:
        ax.plot(range(months), capital_development[fund], label=fund)
    ax.set_xlabel("Months")
    ax.set_ylabel("Capital (€)")
    ax.set_title("Capital Development")
    ax.legend()
    st.pyplot(fig)
else:
    st.info("Please enter the parameters and start the simulation.")
