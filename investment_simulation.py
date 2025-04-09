import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def calculate_expected_returns(data):
    monthly_returns = data['Close'].pct_change().dropna()
    mean_return = monthly_returns.mean()
    volatility = monthly_returns.std()
    return mean_return, volatility

def simulate_investment(start_date, end_date, monthly_contribution, selected_funds, allocations, fund_data, rebalancing_cost=0.00003):
    # Initialisiere das Kapital und die Zeitreihe
    current_date = start_date
    total_capital = 0
    time_series = []

    while current_date <= end_date:
        # Füge monatlichen Beitrag hinzu
        monthly_contributions = {fund: monthly_contribution * allocations[fund] / 100 for fund in selected_funds}

        # Berechne Renditen und aktualisiere Kapital
        for fund, contribution in monthly_contributions.items():
            data = fund_data.get(fund)
            if data is None or data.empty:
                continue

            mean_return, volatility = calculate_expected_returns(data)

            # Aktualisiere Kapital mit Rendite und ziehe Kosten ab
            total_capital += contribution * (1 + mean_return - rebalancing_cost)

        # Füge Kapitalstand zur Zeitreihe hinzu
        time_series.append((current_date, total_capital))

        # Aktualisiere das Datum für den nächsten Monat
        current_date += timedelta(days=30)  # Ungefähre Monatsdauer

    # Erstelle DataFrame für die Zeitreihe
    df_time_series = pd.DataFrame(time_series, columns=['Date', 'Capital'])

    return df_time_series
