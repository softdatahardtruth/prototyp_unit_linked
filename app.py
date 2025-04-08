import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import requests

# === LOGO-FIX ===
logo_url = "https://raw.githubusercontent.com/softdatahardtruth/prototyp_unit_linked/main/allianz-logo.svg"
response = requests.get(logo_url)
if response.status_code == 200:
    svg_content = response.text
    st.markdown(f'<div style="text-align: center;">{svg_content}</div>', unsafe_allow_html=True)
else:
    st.error("Failed to load the Allianz logo.")

# === STYLING ===
st.title("Allianz VitaVerde - Interaktiver Simulator")
st.subheader("Erkunde die Entwicklung deiner fondsgebundenen Lebensversicherung")
st.markdown("---")

# === FONDSDATEN ===
funds = {
    "Allianz Strategy Select 30": {"return": 0.03, "volatility": 0.01, "guarantee": 0.93},
    "Allianz Strategy 4Life Europe 40": {"return": 0.04, "volatility": 0.015, "guarantee": 0.92},
    "Allianz Strategy Select 50": {"return": 0.05, "volatility": 0.02, "guarantee": 0.90},
    "Allianz Strategy Select 75": {"return": 0.06, "volatility": 0.03, "guarantee": 0.85},
}

# === USER INPUTS ===
selected_funds = st.multiselect("Wähle bis zu fünf Fonds", list(funds.keys()), max_selections=5)
contribution = st.number_input("Monatlicher Beitrag (€)", min_value=10, value=100, step=10)
duration = st.number_input("Laufzeit (Jahre)", min_value=1, max_value=40, value=20, step=1)

allocations = {}
total_allocation = 0

if selected_funds:
    st.markdown("#### Verteile deine Einzahlung auf die Fonds:")
    for fund in selected_funds:
        allocation = st.number_input(f"Allocation für {fund} (%)", min_value=0, max_value=100, value=0, step=1)
        allocations[fund] = allocation
        total_allocation += allocation

# === PRÜFUNG ALLOKATION ===
if total_allocation > 100:
    st.error("Die Gesamtallokation überschreitet 100%. Bitte passe die Verteilung an.")
elif total_allocation < 100 and selected_funds:
    st.warning("Die Gesamtallokation beträgt weniger als 100%. Bitte passe die Verteilung an.")

# === SIMULATION ===
if st.button("Simulation starten") and total_allocation == 100:
    months = duration * 12
    paid_in = contribution * months

    capital_development = {fund: [] for fund in selected_funds}
    total_capital = []

    # Initialisieren Fonds-Kapital
    fund_capitals = {fund: 0 for fund in selected_funds}

    # Simulation über die Monate
    for month in range(months):
        monthly_contributions = {fund: contribution * allocations[fund] / 100 for fund in selected_funds}
        
        month_total = 0
        for fund in selected_funds:
            data = funds[fund]
            expected_return = data["return"] / 12
            volatility = data["volatility"]

            # Simulierter monatlicher zufälliger Return
            random_shock = np.random.normal(loc=expected_return, scale=volatility)

            # Kapitalentwicklung berechnen
            fund_capitals[fund] *= (1 + random_shock)
            fund_capitals[fund] += monthly_contributions[fund]
            capital_development[fund].append(fund_capitals[fund])

            month_total += fund_capitals[fund]

        total_capital.append(month_total)

    final_capital = total_capital[-1]
    earnings = max(0, final_capital - paid_in)
    tax = earnings * 0.26
    after_tax = final_capital - tax

    # === ERGEBNISDARSTELLUNG ===
    st.markdown("### Ergebnisse")
    st.write(f"**Eingezahltes Kapital:** {paid_in:,.2f} €")
    st.write(f"**Kapital vor Steuern:** {final_capital:,.2f} €")
    st.write(f"**Kapital nach Steuern:** {after_tax:,.2f} €")
    st.markdown("---")

    # === GRAFIK ===
    st.markdown("### Entwicklung über die Zeit")
    fig, ax = plt.subplots()
    for fund in selected_funds:
        ax.plot(range(months), capital_development[fund], label=fund)
    ax.plot(range(months), total_capital, label="Gesamt", linewidth=2, linestyle='--', color='black')
    ax.set_xlabel("Monate")
    ax.set_ylabel("Kapital (€)")
    ax.set_title("Kapitalentwicklung")
    ax.legend()
    st.pyplot(fig)

    # === EXPORT ===
    st.markdown("### Exportiere deine Simulation")

    # DataFrame vorbereiten
    df = pd.DataFrame({fund: capital_development[fund] for fund in selected_funds})
    df["Gesamt"] = total_capital
    df.index.name = "Monat"

    # Download Button
    st.download_button(
        label="Ergebnisse als Excel herunterladen",
        data=df.to_excel(index=True, engine='openpyxl'),
        file_name="simulationsergebnisse.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Bitte gib die Parameter ein und starte die Simulation.")