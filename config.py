import streamlit as st

def initialize_page():
    st.set_page_config(page_title="Allianz VitaVerde Simulator", layout="wide")
    st.title("Allianz VitaVerde - Insurance & Investment Simulator")

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
